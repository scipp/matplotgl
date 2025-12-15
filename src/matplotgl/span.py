# SPDX-License-Identifier: BSD-3-Clause

import matplotlib.colors as cm
import numpy as np
import pythreejs as p3


class Span:
    def __init__(
        self,
        xmin,
        xmax,
        ymin,
        ymax,
        color="C0",
        zorder=0,
        xscale="linear",
        yscale="linear",
        alpha=1.0,
    ):
        self.axes = None
        self._xscale = xscale
        self._yscale = yscale

        self._xmin = xmin
        self._xmax = xmax
        self._ymin = ymin
        self._ymax = ymax
        self._color = color
        self._zorder = zorder
        self._alpha = alpha

        self._geometry = self._make_geometry()

        # Create material with vertex colors
        self._material = p3.MeshBasicMaterial(
            color=cm.to_hex(self._color), opacity=self._alpha, transparent=True
        )

        # Create mesh
        self._mesh = p3.Mesh(
            geometry=self._geometry,
            material=self._material,
            position=[
                0.5 * (self._xmin + self._xmax),
                0.5 * (self._ymin + self._ymax),
                self._zorder,
            ],
        )

    def _make_geometry(self) -> p3.PlaneGeometry:
        return p3.PlaneGeometry(
            width=self._xmax - self._xmin,
            height=self._ymax - self._ymin,
            widthSegments=2,
            heightSegments=2,
        )

    def _update_position(self) -> None:
        self._geometry = self._make_geometry()
        self._mesh.geometry = self._geometry
        self._mesh.position = [
            0.5 * (self._xmin + self._xmax),
            0.5 * (self._ymin + self._ymax),
            self._zorder,
        ]

    def _update_color(self) -> None:
        self._material.color = cm.to_hex(self._color)

    def _as_object3d(self) -> p3.Object3D:
        return self._mesh

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

    @property
    def color(self) -> str:
        return self._color

    @color.setter
    def color(self, value: str):
        self._color = value
        self._update_color()


class HSpan(Span):
    def __init__(self, **kwargs):
        super().__init__(
            xmin=-1e30,
            xmax=1e30,
            **{k: v for k, v in kwargs.items() if k not in ('xmin', 'xmax')},
        )

    def get_bbox(self) -> dict[str, float]:
        return {"left": None, "right": None, "bottom": self._ymin, "top": self._ymax}


class VSpan(Span):
    def __init__(self, **kwargs):
        super().__init__(
            ymin=-1e30,
            ymax=1e30,
            **{k: v for k, v in kwargs.items() if k not in ('ymin', 'ymax')},
        )

    def get_bbox(self) -> dict[str, float]:
        return {"left": self._xmin, "right": self._xmax, "bottom": None, "top": None}
