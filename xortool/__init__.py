from importlib.metadata import version
from importlib.metadata import PackageNotFoundError

try:
    __version__ = version(__package__)
except PackageNotFoundError:
    __version__ = "0.0.0"  # or "unknown", "dev", etc.
