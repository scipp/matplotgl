# SPDX-License-Identifier: BSD-3-Clause

import matplotlib.colors as cm
import numpy as np
import pythreejs as p3

from .utils import FLOAT32_LIMIT


class Span:
    def __init__(
        self,
        xmin,
        xmax,
        ymin,
        ymax,
        color="C0",
        edgecolor=None,
        facecolor=None,
        ec=None,
        fc=None,
        zorder=0,
        xscale="linear",
        yscale="linear",
        alpha=1.0,
        linewidth=1.0,
    ):
        self.axes = None
        self._xscale = xscale
        self._yscale = yscale

        self._xmin = xmin
        self._xmax = xmax
        self._ymin = ymin
        self._ymax = ymax
        edgecolor = cm.to_hex(edgecolor or ec or color)
        facecolor = cm.to_hex(facecolor or fc or color)
        self._zorder = zorder
        self._alpha = alpha

        self._face_geometry, self._edge_geometry = self._make_geometry()
        self._face_material = p3.MeshBasicMaterial(
            color=facecolor, opacity=self._alpha, transparent=True
        )
        self._face = p3.Mesh(
            geometry=self._face_geometry,
            material=self._face_material,
            position=[
                0.5 * (self._xmin + self._xmax),
                0.5 * (self._ymin + self._ymax),
                self._zorder,
            ],
        )

        self._edge_material = p3.LineMaterial(color=edgecolor, linewidth=linewidth)
        self._edge = p3.Line2(
            geometry=self._edge_geometry, material=self._edge_material
        )

    def _make_geometry(self) -> tuple[p3.PlaneGeometry, p3.LineGeometry]:
        plane = p3.PlaneGeometry(
            width=self._xmax - self._xmin,
            height=self._ymax - self._ymin,
            widthSegments=2,
            heightSegments=2,
        )
        x0, x1, x2 = self._xmin, 0.5 * (self._xmin + self._xmax), self._xmax
        y0, y1, y2 = self._ymin, 0.5 * (self._ymin + self._ymax), self._ymax
        edge = p3.LineGeometry(
            positions=[
                [x0, y0, self._zorder],
                [x1, y0, self._zorder],
                [x2, y0, self._zorder],
                [x2, y1, self._zorder],
                [x2, y2, self._zorder],
                [x1, y2, self._zorder],
                [x0, y2, self._zorder],
                [x0, y1, self._zorder],
                [x0, y0, self._zorder],
            ]
        )
        return plane, edge

    def _update_position(self) -> None:
        self._face_geometry, self._edge_geometry = self._make_geometry()
        self._face.geometry = self._face_geometry
        self._face.position = [
            0.5 * (self._xmin + self._xmax),
            0.5 * (self._ymin + self._ymax),
            self._zorder,
        ]
        self._edge.geometry.position = self._edge_geometry.position

    def _update_color(self) -> None:
        self._material.color = cm.to_hex(self._color)

    def _as_object3d(self) -> p3.Object3D:
        return p3.Group(children=[self._face, self._edge])

    @property
    def x(self) -> np.ndarray:
        return self._xmin

    @x.setter
    def x(self, value: float):
        self.xmin = value

    @property
    def y(self) -> np.ndarray:
        return self._ymin

    @y.setter
    def y(self, value: float):
        self.ymin = value

    @property
    def xmin(self) -> float:
        return self._xmin

    @xmin.setter
    def xmin(self, value: float):
        self._xmin = value
        self._update_position()

    @property
    def xmax(self) -> float:
        return self._xmax

    @xmax.setter
    def xmax(self, value: float):
        self._xmax = value
        self._update_position()

    @property
    def ymin(self) -> float:
        return self._ymin

    @ymin.setter
    def ymin(self, value: float):
        self._ymin = value
        self._update_position()

    @property
    def ymax(self) -> float:
        return self._ymax

    @ymax.setter
    def ymax(self, value: float):
        self._ymax = value
        self._update_position()

    @property
    def xy(self) -> tuple[float, float]:
        return self._xmin, self._ymin

    def get_facecolor(self) -> str:
        return self._face_material.color

    def set_facecolor(self, color: str):
        self._face_material.color = cm.to_hex(color)

    def get_edgecolor(self) -> str:
        return self._edge_material.color

    def set_edgecolor(self, color: str):
        self._edge_material.color = cm.to_hex(color)

    def set_color(self, value: str):
        self.set_edgecolor(value)
        self.set_facecolor(value)


class HSpan(Span):
    def __init__(self, **kwargs):
        super().__init__(
            xmin=-FLOAT32_LIMIT,
            xmax=FLOAT32_LIMIT,
            **{k: v for k, v in kwargs.items() if k not in ('xmin', 'xmax')},
        )

    def get_bbox(self) -> dict[str, float]:
        return {"left": None, "right": None, "bottom": self._ymin, "top": self._ymax}


class VSpan(Span):
    def __init__(self, **kwargs):
        super().__init__(
            ymin=-FLOAT32_LIMIT,
            ymax=FLOAT32_LIMIT,
            **{k: v for k, v in kwargs.items() if k not in ('ymin', 'ymax')},
        )

    def get_bbox(self) -> dict[str, float]:
        return {"left": self._xmin, "right": self._xmax, "bottom": None, "top": None}
