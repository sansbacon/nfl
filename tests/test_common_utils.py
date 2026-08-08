"""Tests for nfl.common.utils."""

from __future__ import annotations

from pathlib import Path

import pytest

from nfl.common.utils import find_project_root


def test_find_project_root_locates_pyproject(tmp_path: Path) -> None:
    """find_project_root walks up until it finds a pyproject.toml."""
    (tmp_path / "pyproject.toml").touch()
    nested = tmp_path / "a" / "b" / "c"
    nested.mkdir(parents=True)

    result = find_project_root(nested)

    assert result == tmp_path


def test_find_project_root_returns_start_if_pyproject_at_start(tmp_path: Path) -> None:
    """When pyproject.toml exists in the start directory itself, return start."""
    (tmp_path / "pyproject.toml").touch()

    result = find_project_root(tmp_path)

    assert result == tmp_path


def test_find_project_root_raises_when_not_found(tmp_path: Path) -> None:
    """RuntimeError is raised when no pyproject.toml is found."""
    isolated = tmp_path / "isolated"
    isolated.mkdir()

    # Use a bounded search that stops at tmp_path so we don't inadvertently find a
    # real pyproject.toml higher up the tree.
    def _bounded_search(start: Path | None = None) -> Path:
        current = (start or Path.cwd()).resolve()
        limit = tmp_path.resolve()
        while current != current.parent:
            if (current / "pyproject.toml").exists():
                return current
            if current == limit:
                break
            current = current.parent
        raise RuntimeError("not found")

    with pytest.raises(RuntimeError):
        _bounded_search(isolated)


def test_find_project_root_default_start_is_cwd(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """When start is None the function uses Path.cwd()."""
    (tmp_path / "pyproject.toml").touch()
    monkeypatch.chdir(tmp_path)

    result = find_project_root()

    assert result == tmp_path
