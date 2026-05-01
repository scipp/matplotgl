# SPDX-License-Identifier: BSD-3-Clause
from typing import Literal

import matplotlib as mpl
import matplotlib.colors as cm
import numpy as np
import pythreejs as p3

from .norm import Normalizer


class Image:
    def __init__(
        self,
        array: np.ndarray,
        extent: list[float] | None = None,
        cmap: str | None = None,
        norm: str | Normalizer | None = None,
        zorder: float | None = None,
        origin: Literal["upper", "lower"] | None = None,
    ):

        cmap = cmap or "viridis"
        norm = norm or "linear"
        zorder = zorder or 0
        self._origin = origin or "upper"

        self.axes = None
        self._colorbar = None
        self._array = np.asarray(array)
        if self._origin == "upper":
            self._array = np.flip(self._array, axis=0)
        self._extent = extent or [0, array.shape[1], 0, array.shape[0]]
        self._zorder = zorder
        self._norm = (
            Normalizer(vmin=np.min(self._array), vmax=np.max(self._array), norm=norm)
            if isinstance(norm, str)
            else norm
        )
        self._cmap = mpl.colormaps[cmap].copy()
        self._texture = p3.DataTexture(
            data=self._make_colors(), format="RGBFormat", type="FloatType"
        )

        self._geometry = p3.PlaneGeometry(
            width=self._extent[1] - self._extent[0],
            height=self._extent[3] - self._extent[2],
            widthSegments=1,
            heightSegments=1,
        )

        self._image = p3.Mesh(
            geometry=self._geometry,
            material=p3.MeshBasicMaterial(map=self._texture),
            position=[
                0.5 * (self._extent[0] + self._extent[1]),
                0.5 * (self._extent[2] + self._extent[3]),
                self._zorder,
            ],
        )

    def _make_colors(self) -> np.ndarray:
        if self._array.ndim == 3 and self._array.shape[2] in (3, 4):
            if self._array.dtype == np.uint8:
                return self._array.astype("float32") / 255
            return self._array.astype("float32")
        return self._cmap(self.norm(self._array))[..., :3].astype("float32")

    def set_axes(self, axes):
        self.axes = axes
        if self._origin == "upper":
            self.axes.y_inverted = True

    def get_bbox(self) -> dict[str, float]:
        return {
            "left": self._extent[0],
            "right": self._extent[1],
            "bottom": self._extent[2],
            "top": self._extent[3],
        }

    def _update_colors(self) -> None:
        self._texture.data = self._make_colors()

    def _as_object3d(self) -> p3.Object3D:
        return self._image

    def _set_xscale(self, scale: str) -> None:
        if scale == "log":
            raise NotImplementedError("Log scale for images is not implemented yet.")

    def _set_yscale(self, scale: str) -> None:
        if scale == "log":
            raise NotImplementedError("Log scale for images is not implemented yet.")

    def get_array(self) -> np.ndarray:
        return self._array

    def set_array(self, array: np.ndarray) -> None:
        self._array = np.asarray(array)
        self._update_colors()

    def get_extent(self) -> list[float]:
        return self._extent

    def set_extent(self, extent: list[float]) -> None:
        self._extent = extent
        self._geometry = p3.PlaneGeometry(
            width=self._extent[1] - self._extent[0],
            height=self._extent[3] - self._extent[2],
            widthSegments=1,
            heightSegments=1,
        )
        self._image.geometry = self._geometry
        self._image.position = [
            0.5 * (self._extent[0] + self._extent[1]),
            0.5 * (self._extent[2] + self._extent[3]),
            self._zorder,
        ]

    def set_cmap(self, cmap: str) -> None:
        self._cmap = mpl.colormaps[cmap].copy()
        self._update_colors()
        if self._colorbar is not None:
            self._colorbar.update()

    @property
    def cmap(self) -> cm.Colormap:
        return self._cmap

    @cmap.setter
    def cmap(self, cmap: str) -> None:
        self.set_cmap(cmap)

    @property
    def norm(self) -> Normalizer:
        return self._norm

    @norm.setter
    def norm(self, norm: Normalizer | str) -> None:
        if isinstance(norm, str):
            self._norm = Normalizer(
                vmin=np.min(self._array), vmax=np.max(self._array), norm=norm
            )
        else:
            self._norm = norm
        self._update_colors()
        if self._colorbar is not None:
            self._colorbar.update()
