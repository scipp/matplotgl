# SPDX-License-Identifier: BSD-3-Clause

import warnings

import matplotlib as mpl
import matplotlib.colors as cm
import numpy as np
import pythreejs as p3

from .norm import Normalizer
from .utils import find_limits, fix_empty_range


class Mesh:
    def __init__(
        self,
        *args,
        cmap: str = "viridis",
        norm: str = "linear",
        xscale="linear",
        yscale="linear",
    ):
        if len(args) not in (1, 3):
            raise ValueError(
                f"Invalid number of arguments: expected 1 or 3. Got {len(args)}"
            )
        if len(args) == 3:
            x, y, c = args
            M, N = c.shape
        elif len(args) == 1:
            c = args[0]
            M, N = c.shape
            x = np.arange(N + 1)
            y = np.arange(M + 1)

        self.axes = None
        self._colorbar = None
        self._xscale = xscale
        self._yscale = yscale

        self._x = np.asarray(x)
        self._y = np.asarray(y)
        self._c = np.asarray(c)

        self._norm = Normalizer(vmin=np.min(self._c), vmax=np.max(self._c), norm=norm)
        self._cmap = mpl.colormaps[cmap].copy()

        self._faces = self._make_faces()

        # Create BufferGeometry
        self._geometry = p3.BufferGeometry(
            attributes={
                "position": p3.BufferAttribute(array=self._make_vertices()),
                "color": p3.BufferAttribute(array=self._make_colors()),
            },
            index=p3.BufferAttribute(array=self._faces),
        )

        # Create material with vertex colors
        self._material = p3.MeshBasicMaterial(
            vertexColors="VertexColors", side="DoubleSide"
        )

        # Create mesh
        self._mesh = p3.Mesh(geometry=self._geometry, material=self._material)

    def _make_colors(self) -> np.ndarray:
        colors_rgba = self._cmap(self._norm(self._c.flatten()))
        colors = colors_rgba[:, :3].astype("float32")
        # Assign colors to vertices (each vertex in a cell gets the same color)
        return np.repeat(colors, 4, axis=0)  # 4 vertices per cell

    def _make_faces(self) -> np.ndarray:
        # Create faces (indices into vertices array)
        # For each cell, create two triangles
        n_cells = self._c.size
        base_indices = np.arange(n_cells) * 4
        faces = np.zeros((n_cells * 2, 3), dtype=np.uint32)
        # First triangle: v0, v1, v2
        faces[0::2, 0] = base_indices
        faces[0::2, 1] = base_indices + 1
        faces[0::2, 2] = base_indices + 2
        # Second triangle: v0, v2, v3
        faces[1::2, 0] = base_indices
        faces[1::2, 1] = base_indices + 2
        faces[1::2, 2] = base_indices + 3
        return faces.flatten()

    def _make_vertices(self) -> np.ndarray:
        M, N = self._c.shape
        with warnings.catch_warnings(category=RuntimeWarning, action="ignore"):
            x = self._x if self._xscale == "linear" else np.log10(self._x)
            y = self._y if self._yscale == "linear" else np.log10(self._y)

        # Create meshgrid for all cell corners
        i_indices = np.arange(N)
        j_indices = np.arange(M)
        j_grid, i_grid = np.meshgrid(j_indices, i_indices, indexing="ij")

        # Flatten to get all cells
        i_flat = i_grid.flatten()
        j_flat = j_grid.flatten()
        n_cells = len(i_flat)

        # Create all four corners for all cells at once
        # Each cell has 4 vertices: bottom-left, bottom-right, top-right, top-left
        x_left = x[i_flat]
        x_right = x[i_flat + 1]
        y_bottom = y[j_flat]
        y_top = y[j_flat + 1]

        # Build vertices array (n_cells * 4 vertices, each with x, y, z coords)
        vertices = np.zeros((n_cells * 4, 3), dtype=np.float32)
        vertices[0::4, 0] = x_left
        vertices[0::4, 1] = y_bottom
        vertices[1::4, 0] = x_right
        vertices[1::4, 1] = y_bottom
        vertices[2::4, 0] = x_right
        vertices[2::4, 1] = y_top
        vertices[3::4, 0] = x_left
        vertices[3::4, 1] = y_top
        return vertices

    def _update_positions(self) -> None:
        self._geometry.attributes["position"].array = self._make_vertices()

    def _update_colors(self) -> None:
        self._geometry.attributes["color"].array = self._make_colors()

    def get_bbox(self) -> dict[str, float]:
        pad = False
        left, right = fix_empty_range(find_limits(self._x, scale=self._xscale, pad=pad))
        bottom, top = fix_empty_range(find_limits(self._y, scale=self._yscale, pad=pad))
        return {"left": left, "right": right, "bottom": bottom, "top": top}

    def _as_object3d(self) -> p3.Object3D:
        return self._mesh

    def get_xdata(self) -> np.ndarray:
        return self._x

    def set_xdata(self, x: np.ndarray):
        self._x = np.asarray(x)
        self._update_positions()

    def get_ydata(self) -> np.ndarray:
        return self._y

    def set_ydata(self, y: np.ndarray):
        self._y = np.asarray(y)
        self._update_positions()

    def set_array(self, c: np.ndarray):
        self._c = np.asarray(c)
        self._update_colors()

    def _set_xscale(self, scale: str) -> None:
        self._xscale = scale
        self._update_positions()

    def _set_yscale(self, scale: str) -> None:
        self._yscale = scale
        self._update_positions()

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
                vmin=np.min(self._c), vmax=np.max(self._c), norm=norm
            )
        else:
            self._norm = norm
        self._update_colors()
        if self._colorbar is not None:
            self._colorbar.update()
