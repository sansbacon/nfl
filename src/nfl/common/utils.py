"""General-purpose utilities shared across the nfl library."""

from __future__ import annotations

from pathlib import Path


def find_project_root(start: Path | None = None) -> Path:
    """Walk up from *start* until a ``pyproject.toml`` is found.

    Returns the first ancestor directory that contains a ``pyproject.toml``
    file.  This mirrors the bootstrap pattern duplicated across example
    notebooks and scripts.

    Parameters
    ----------
    start:
        Starting directory for the search.  Defaults to ``Path.cwd()`` when
        not provided.

    Returns
    -------
    Path
        The resolved project root directory.

    Raises
    ------
    RuntimeError
        If no ``pyproject.toml`` is found before reaching the filesystem root.

    Examples
    --------
    >>> from nfl.common.utils import find_project_root
    >>> root = find_project_root()
    >>> (root / "pyproject.toml").exists()
    True
    """
    current = (start or Path.cwd()).resolve()
    while current != current.parent:
        if (current / "pyproject.toml").exists():
            return current
        current = current.parent
    raise RuntimeError(
        "Cannot locate project root: no pyproject.toml found in any ancestor "
        f"of {(start or Path.cwd())!r}."
    )
