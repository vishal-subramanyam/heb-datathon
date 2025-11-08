from __future__ import annotations

__all__ = ["__version__", "get_version"]
# Keep this in sync with pyproject.toml [tool.poetry].version
__version__ = "0.1.0"


def get_version() -> str:
    """
    Return the semantic version of the tamu25 package.
    Falls back to the hardcoded __version__ if importlib.metadata is unavailable
    or package metadata is not installed (editable dev mode).
    """
    try:
        from importlib.metadata import PackageNotFoundError, version  # Python 3.11+

        try:
            return version("tamu25")
        except PackageNotFoundError:
            return __version__
    except Exception:
        return __version__
