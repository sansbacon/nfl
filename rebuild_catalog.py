#!/usr/bin/env python3
"""Rebuild Iceberg catalog with correct absolute paths."""

from pathlib import Path
import sys
import json

# Add src to path
ROOT = Path(__file__).parent.resolve()
sys.path.insert(0, str(ROOT / "src"))

from pyiceberg.catalog import load_catalog

def main():
    warehouse = ROOT / "warehouse"
    catalog_uri = f"sqlite:///{ROOT / 'iceberg_catalog.db'}"
    
    print(f"Rebuilding Iceberg catalog...")
    print(f"  Catalog URI: {catalog_uri}")
    print(f"  Warehouse: {warehouse}")
    
    # This will recreate the catalog and scan the warehouse
    catalog = load_catalog(
        "yahoo",
        type="sql",
        uri=catalog_uri,
        warehouse=str(warehouse),
    )
    
    # List tables to verify
    print("\nCatalog tables:")
    for namespace in ["yahoo_common", "yhnfl"]:
        try:
            tables = catalog.list_tables(namespace)
            print(f"\n{namespace}:")
            for ns, tbl in tables:
                print(f"  - {ns}.{tbl}")
                # Try loading to verify paths work
                try:
                    table = catalog.load_table(f"{ns}.{tbl}")
                    scan_result = table.scan()
                    print(f"    ✓ Successfully loaded (snapshot id: {table.current_snapshot().snapshot_id if table.current_snapshot() else 'N/A'})")
                except Exception as e:
                    print(f"    ✗ Error loading: {e}")
        except Exception as e:
            print(f"{namespace}: {e}")
    
    print("\nCatalog rebuild complete!")

if __name__ == "__main__":
    main()
