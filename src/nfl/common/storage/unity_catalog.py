"""Shared Unity Catalog persistence adapters.

Provides write utilities for persisting Polars DataFrames to:
- Unity Catalog Delta tables (via PySpark)
- Unity Catalog Volumes (as Parquet/CSV/NDJSON files)
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

import polars as pl

WriteMode = Literal["append", "overwrite", "merge"]
VolumeFileFormat = Literal["parquet", "csv", "ndjson"]


@dataclass(frozen=True, slots=True)
class UCTableConfig:
    """Configuration for writing to Unity Catalog Delta tables."""

    catalog: str = "nfl"
    schema: str = "default"
    write_mode: WriteMode = "overwrite"
    merge_keys: tuple[str, ...] = ()
    table_prefix: str = ""
    table_properties: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class UCVolumeConfig:
    """Configuration for writing files to Unity Catalog Volumes."""

    catalog: str = "nfl"
    schema: str = "default"
    volume: str = "pipeline_output"
    file_format: VolumeFileFormat = "parquet"
    subdirectory: str = ""

    @property
    def base_path(self) -> str:
        parts = f"/Volumes/{self.catalog}/{self.schema}/{self.volume}"
        if self.subdirectory:
            parts = f"{parts}/{self.subdirectory.strip('/')}"
        return parts


@dataclass(frozen=True, slots=True)
class UCWriteResult:
    """Result of a single UC write operation."""

    entity: str
    target: str
    mode: str
    source_rows: int
    written_rows: int
    target_type: Literal["table", "volume"]


def _get_spark() -> Any:
    """Retrieve the active SparkSession (Databricks runtime)."""
    try:
        from pyspark.sql import SparkSession

        spark = SparkSession.getActiveSession()
        if spark is None:
            spark = SparkSession.builder.getOrCreate()
        return spark
    except ImportError as exc:
        raise RuntimeError(
            "PySpark is not available. Unity Catalog table writes require "
            "a Databricks runtime or a PySpark environment."
        ) from exc


def _polars_to_spark(frame: pl.DataFrame, spark: Any) -> Any:
    """Convert a Polars DataFrame to a PySpark DataFrame via Arrow.

    TODO(Phase 5): Replace .to_pandas() intermediate with direct Arrow path.
    Spark 3.5+ supports createDataFrame(arrow_table) via PyArrow, which
    avoids the pandas memory copy. Blocked on verifying Databricks Runtime
    version compatibility. See: spark.conf('spark.sql.execution.arrow.pyspark.enabled').
    """
    arrow_table = frame.to_arrow()
    return spark.createDataFrame(arrow_table.to_pandas())


def _fully_qualified_table(config: UCTableConfig, entity: str) -> str:
    """Build fully qualified table name: catalog.schema.table."""
    table_name = f"{config.table_prefix}{entity}" if config.table_prefix else entity
    return f"{config.catalog}.{config.schema}.{table_name}"


def persist_to_uc_tables(
    frames: Mapping[str, pl.DataFrame],
    config: UCTableConfig | None = None,
    dry_run: bool = False,
) -> list[UCWriteResult]:
    """Write Polars DataFrames as Unity Catalog Delta tables.

    Parameters
    ----------
    frames : Mapping[str, pl.DataFrame]
        Entity name to DataFrame mapping.
    config : UCTableConfig | None
        UC table write configuration. Defaults to catalog='nfl', schema='default'.
    dry_run : bool
        If True, reports what would be written without executing writes.

    Returns
    -------
    list[UCWriteResult]
        Write results for each entity.
    """
    cfg = config or UCTableConfig()
    results: list[UCWriteResult] = []
    spark = None if dry_run else _get_spark()

    for entity, frame in frames.items():
        if frame.is_empty():
            results.append(
                UCWriteResult(
                    entity=entity,
                    target=_fully_qualified_table(cfg, entity),
                    mode=cfg.write_mode,
                    source_rows=0,
                    written_rows=0,
                    target_type="table",
                )
            )
            continue

        fq_table = _fully_qualified_table(cfg, entity)
        source_rows = frame.height

        if dry_run:
            results.append(
                UCWriteResult(
                    entity=entity,
                    target=fq_table,
                    mode=cfg.write_mode,
                    source_rows=source_rows,
                    written_rows=source_rows,
                    target_type="table",
                )
            )
            continue

        spark_df = _polars_to_spark(frame, spark)

        if cfg.write_mode == "merge" and cfg.merge_keys:
            _merge_into_table(spark, spark_df, fq_table, cfg.merge_keys)
        elif cfg.write_mode == "append":
            spark_df.write.format("delta").mode("append").saveAsTable(fq_table)
        else:
            spark_df.write.format("delta").mode("overwrite").option(
                "overwriteSchema", "true"
            ).saveAsTable(fq_table)

        results.append(
            UCWriteResult(
                entity=entity,
                target=fq_table,
                mode=cfg.write_mode,
                source_rows=source_rows,
                written_rows=source_rows,
                target_type="table",
            )
        )

    return results


def _merge_into_table(
    spark: Any,
    source_df: Any,
    target_table: str,
    merge_keys: tuple[str, ...],
) -> None:
    """MERGE INTO target using source DataFrame on merge_keys."""
    from pyspark.sql.utils import AnalysisException

    temp_view = f"_uc_merge_source_{target_table.replace('.', '_')}"
    source_df.createOrReplaceTempView(temp_view)

    merge_condition = " AND ".join(
        f"target.`{key}` = source.`{key}`" for key in merge_keys
    )

    try:
        spark.sql(f"""
            MERGE INTO {target_table} AS target
            USING {temp_view} AS source
            ON {merge_condition}
            WHEN MATCHED THEN UPDATE SET *
            WHEN NOT MATCHED THEN INSERT *
        """)
    except AnalysisException:
        # Table does not exist yet; fall back to creating it.
        source_df.write.format("delta").mode("overwrite").option(
            "overwriteSchema", "true"
        ).saveAsTable(target_table)
    finally:
        spark.catalog.dropTempView(temp_view)


def load_uc_table(
    table_identifier: str,
    *,
    spark: Any | None = None,
) -> pl.DataFrame:
    """Load a Unity Catalog Delta table as a Polars DataFrame.

    Reads the Spark DataFrame and converts it to Polars via Pandas.

    Parameters
    ----------
    table_identifier:
        Fully qualified table name, e.g. ``"nfl.yh.player"``.
    spark:
        An existing ``SparkSession`` to use.  If ``None`` the active session
        is retrieved automatically.

    Returns
    -------
    pl.DataFrame
        Contents of the UC table as a Polars DataFrame.

    Examples
    --------
    .. code-block:: python

        from nfl.common.storage import load_uc_table

        player_df = load_uc_table("nfl.yh.player")
    """
    active_spark = spark or _get_spark()
    spark_df = active_spark.table(table_identifier)
    return pl.from_pandas(spark_df.toPandas())


def persist_to_uc_volume(
    frames: Mapping[str, pl.DataFrame],
    config: UCVolumeConfig | None = None,
    dry_run: bool = False,
) -> list[UCWriteResult]:
    """Write Polars DataFrames as files to a Unity Catalog Volume.

    Parameters
    ----------
    frames : Mapping[str, pl.DataFrame]
        Entity name to DataFrame mapping.
    config : UCVolumeConfig | None
        Volume write configuration.
    dry_run : bool
        If True, reports what would be written without executing writes.

    Returns
    -------
    list[UCWriteResult]
        Write results for each entity.
    """
    cfg = config or UCVolumeConfig()
    results: list[UCWriteResult] = []

    for entity, frame in frames.items():
        file_name = f"{entity}.{cfg.file_format}"
        target_path = f"{cfg.base_path}/{file_name}"
        source_rows = frame.height

        if dry_run or frame.is_empty():
            results.append(
                UCWriteResult(
                    entity=entity,
                    target=target_path,
                    mode="overwrite",
                    source_rows=source_rows,
                    written_rows=source_rows if not frame.is_empty() else 0,
                    target_type="volume",
                )
            )
            continue

        # Ensure subdirectory exists
        volume_dir = Path(cfg.base_path)
        volume_dir.mkdir(parents=True, exist_ok=True)

        output_path = Path(target_path)
        if cfg.file_format == "parquet":
            frame.write_parquet(output_path)
        elif cfg.file_format == "csv":
            frame.write_csv(output_path)
        elif cfg.file_format == "ndjson":
            frame.write_ndjson(output_path)

        results.append(
            UCWriteResult(
                entity=entity,
                target=target_path,
                mode="overwrite",
                source_rows=source_rows,
                written_rows=source_rows,
                target_type="volume",
            )
        )

    return results
