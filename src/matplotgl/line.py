# SPDX-License-Identifier: BSD-3-Clause

import warnings

import numpy as np
import pythreejs as p3
from matplotlib import colors as mplc

from .utils import find_limits, fix_empty_range


class Line:
    def __init__(
        self,
        x,
        y,
        fmt="-",
        color="C0",
        ls="solid",
        lw=1,
        ms=5,
        zorder=0,
        xscale="linear",
        yscale="linear",
    ):
        self.axes = None
        self._xscale = xscale
        self._yscale = yscale
        self._x = np.asarray(x)
        self._y = np.asarray(y)
        self._zorder = zorder
        pos = self._make_positions()
        self._line_geometry = p3.LineGeometry(positions=pos)

        self._color = mplc.to_hex(color)
        self._line = None
        self._vertices = None
        if "-" in fmt:
            if ls == "solid":
                self._line_material = p3.LineMaterial(color=self._color, linewidth=lw)
            elif ls == "dashed":
                raise NotImplementedError("Dashed lines are not yet implemented")
            self._line = p3.Line2(
                geometry=self._line_geometry, material=self._line_material
            )

        if "o" in fmt:
            self._vertices_geometry = p3.BufferGeometry(
                attributes={
                    "position": p3.BufferAttribute(array=pos),
                }
            )
            self._vertices_material = p3.PointsMaterial(color=self._color, size=ms)
            self._vertices = p3.Points(
                geometry=self._vertices_geometry, material=self._vertices_material
            )

    def get_bbox(self):
        pad = 0.03
        left, right = fix_empty_range(find_limits(self._x, scale=self._xscale, pad=pad))
        bottom, top = fix_empty_range(find_limits(self._y, scale=self._yscale, pad=pad))
        return {"left": left, "right": right, "bottom": bottom, "top": top}

    def _as_object3d(self) -> p3.Object3D:
        out = []
        if self._line is not None:
            out.append(self._line)
        if self._vertices is not None:
            out.append(self._vertices)
        return p3.Group(children=out) if len(out) > 1 else out[0]

    def _make_positions(self):
        with warnings.catch_warnings(category=RuntimeWarning, action="ignore"):
            xx = self._x if self._xscale == "linear" else np.log10(self._x)
            yy = self._y if self._yscale == "linear" else np.log10(self._y)
        pos = np.array(
            [xx, yy, np.full_like(xx, self._zorder)],
            dtype="float32",
        ).T
        return pos

    def _update(self):
        pos = self._make_positions()
        if self._line is not None:
            self._line_geometry.positions = pos
        if self._vertices is not None:
            self._vertices_geometry.attributes["position"].array = pos

    def get_xdata(self) -> np.ndarray:
        return self._x

    def set_xdata(self, x):
        self._x = np.asarray(x)
        self._update()

    def get_ydata(self) -> np.ndarray:
        return self._y

    def set_ydata(self, y):
        self._y = np.asarray(y)
        self._update()

    def set_data(self, x, y=None):
        if y is None:
            x = np.asarray(x)[:, 0]
            y = np.asarray(x)[:, 1]
        self._x = np.asarray(x)
        self._y = np.asarray(y)
        self._update()

    def _set_xscale(self, scale):
        self._xscale = scale
        self._update()

    def _set_yscale(self, scale):
        self._yscale = scale
        self._update()
