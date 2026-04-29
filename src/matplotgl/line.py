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
        fmt=None,
        color=None,
        ls=None,
        lw=None,
        ms=None,
        marker=None,
        zorder=None,
        xscale=None,
        yscale=None,
        linestyle=None,
        linewidth=None,
        markersize=None,
        alpha=None,
        visible=None,
        **ignored,
    ):
        self._color = mplc.to_hex(color or "C0")
        self._linewidth = linewidth or (lw or 2)
        self._linestyle = linestyle or (ls or "solid")
        self._markersize = markersize or (ms or 5)
        self._marker = marker or (
            "o" if marker is None and fmt and "o" in fmt else None
        )
        self._zorder = zorder or 0
        self._xscale = xscale or "linear"
        self._yscale = yscale or "linear"
        self._alpha = alpha or 1.0
        visible = visible if visible is not None else True

        self.axes = None
        # self._xscale = xscale
        # self._yscale = yscale
        self._x = np.asarray(x)
        self._y = np.asarray(y)
        pos = self._make_positions()
        self._line_geometry = p3.LineGeometry(positions=pos)

        # self._linewidth = linewidth or (lw or 2)
        # self._linestyle = linestyle or (ls or "solid")

        # self._color = mplc.to_hex(color)
        self._line = None
        self._vertices = None

        if self._linestyle not in (None, 'none'):
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
                geometry=self._line_geometry,
                material=self._line_material,
                visible=visible,
            )

        if self._marker not in (None, 'none'):
            self._vertices_geometry = p3.BufferGeometry(
                attributes={
                    "position": p3.BufferAttribute(array=pos),
                }
            )
            self._vertices_material = p3.PointsMaterial(
                color=self._color,
                size=self._markersize,
                opacity=self._alpha,
                transparent=self._alpha < 1.0,
            )
            self._vertices = p3.Points(
                geometry=self._vertices_geometry,
                material=self._vertices_material,
                visible=visible,
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
        if self._line is not None:
            self._line_material.color = self._color
        if self._vertices is not None:
            self._vertices_material.color = self._color

    def get_marker(self):
        return self._marker

    def get_markersize(self):
        return self._markersize

    # def set_marker(self, marker):

    def get_linestyle(self):
        return self._linestyle

    def get_linewidth(self):
        return self._linewidth

    def set(self, **kwargs):
        for key, value in kwargs.items():
            getattr(self, f"set_{key}")(value)
