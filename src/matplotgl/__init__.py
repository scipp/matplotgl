# SPDX-License-Identifier: BSD-3-Clause
# ruff: noqa: E402, F401, I

import importlib.metadata

try:
    __version__ = importlib.metadata.version(__package__ or __name__)
except importlib.metadata.PackageNotFoundError:
    __version__ = "0.0.0"


from matplotlib import colormaps, colors

from . import pyplot

__all__ = [
    "colormaps",
    "colors",
    "pyplot",
]

del importlib
