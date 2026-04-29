# SPDX-License-Identifier: BSD-3-Clause

import warnings

import numpy as np
import pythreejs as p3
from matplotlib import colors as mplc

from .utils import find_limits, fix_empty_range


class Step:
    def __init__(
        self,
        x,
        y,
        *,
        where=None,
        color=None,
        ls=None,
        lw=None,
        zorder=None,
        xscale=None,
        yscale=None,
        linestyle=None,
        linewidth=None,
        alpha=None,
        **ignored,
    ):
        self.where = (where or "pre").lower()
        self._color = mplc.to_hex(color or "C0")
        self._linewidth = linewidth or (lw or 2)
        self._linestyle = linestyle or (ls or "solid")
        self._zorder = zorder or 0
        self._xscale = xscale or "linear"
        self._yscale = yscale or "linear"
        self._alpha = alpha or 1.0

        self.axes = None
        # self._xscale = xscale
        # self._yscale = yscale
        self._x = np.asarray(x)
        self._y = np.asarray(y)
        self._zorder = zorder
        pos = self._make_positions()
        self._line_geometry = p3.LineGeometry(positions=pos)

        # lw = linewidth or lw
        # ls = linestyle or ls

        # self._color = mplc.to_hex(color)
        self._line = None
        self._vertices = None

        if self._linestyle == "solid":
            self._line_material = p3.LineMaterial(
                color=self._color,
                linewidth=self._linewidth,
                # TODO: it seems opacity in LineMaterial does not work in pythreejs?
                opacity=self._alpha,
                transparent=self._alpha < 1.0,
            )
        elif self._linestyle == "dashed":
            raise NotImplementedError("Dashed lines are not yet implemented")
        self._line = p3.Line2(
            geometry=self._line_geometry, material=self._line_material
        )

    def get_bbox(self):
        pad = 0.03
        left, right = fix_empty_range(find_limits(self._x, scale=self._xscale, pad=pad))
        bottom, top = fix_empty_range(find_limits(self._y, scale=self._yscale, pad=pad))
        return {"left": left, "right": right, "bottom": bottom, "top": top}

    def _as_object3d(self) -> p3.Object3D:
        return self._line

    def _make_positions(self):
        with warnings.catch_warnings(category=RuntimeWarning, action="ignore"):
            xx = self._x if self._xscale == "linear" else np.log10(self._x)
            yy = self._y if self._yscale == "linear" else np.log10(self._y)

        match self.where:
            case "pre":
                xx = np.repeat(xx, 2)[:-1]
                yy = np.repeat(yy, 2)[1:]
            case "post":
                xx = np.repeat(xx, 2)[1:]
                yy = np.repeat(yy, 2)[:-1]
            case "mid":
                x1 = 0.5 * (xx[:-1] + xx[1:])
                xx = np.concatenate(
                    [np.atleast_1d(xx[0]), np.repeat(x1, 2), np.atleast_1d(xx[-1])]
                )
                yy = np.repeat(yy, 2)
            case _:
                raise ValueError(f"Invalid where: {self.where}")

        pos = np.array(
            [xx, yy, np.full_like(xx, self._zorder)],
            dtype="float32",
        ).T
        return pos

    def _update(self):
        self._line_geometry.positions = self._make_positions()

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

    def get_visible(self):
        return self._line.visible if self._line is not None else self._vertices.visible

    def set_visible(self, visible):
        if self._line is not None:
            self._line.visible = visible
        if self._vertices is not None:
            self._vertices.visible = visible

    def get_zorder(self):
        return self._zorder

    def set_zorder(self, zorder):
        self._zorder = zorder
        self._update()

    def get_color(self):
        return self._color

    def set_color(self, color):
        self._color = mplc.to_hex(color)
        self._line_material.color = self._color

    def get_linestyle(self):
        return self._linestyle

    def get_linewidth(self):
        return self._linewidth

    def set(self, **kwargs):
        for key, value in kwargs.items():
            getattr(self, f"set_{key}")(value)
