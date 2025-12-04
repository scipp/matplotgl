# SPDX-License-Identifier: BSD-3-Clause

import warnings

import matplotlib as mpl
import matplotlib.colors as cm
import numpy as np
import pythreejs as p3

from .norm import Normalizer
from .utils import find_limits, fix_empty_range


def _maybe_centers_to_edges(coord: np.ndarray, M: int, N: int, axis: str) -> np.ndarray:
    """
    Convert cell centers to cell edges if necessary.

    Parameters:
    - coord: coordinate array (1D or 2D)
    - M: number of rows of cells
    - N: number of columns of cells
    - axis: 'x' or 'y' to indicate which axis this coordinate represents

    For 1D arrays:
    - x-axis: If length is N, assume centers and convert to edges (N+1)
    - y-axis: If length is M, assume centers and convert to edges (M+1)
    - If already N+1 or M+1, assume edges and return as is

    For 2D arrays:
    - If shape is (M, N), assume centers and convert to edges (M+1, N+1)
    - If shape is (M+1, N+1), assume already edges and return as is
    """
    if coord.ndim not in (1, 2):
        raise ValueError(f"Coordinate array must be 1D or 2D, got {coord.ndim}D")

    if coord.ndim == 1:
        expected_centers = N if axis == 'x' else M
        expected_edges = expected_centers + 1

        if len(coord) == expected_edges:
            return coord

        if len(coord) == expected_centers:
            edges = np.zeros(expected_edges, dtype=coord.dtype)
            # Midpoints between centers, with extrapolation at ends
            edges[1:-1] = 0.5 * (coord[:-1] + coord[1:])
            edges[0] = coord[0] - (coord[1] - coord[0]) / 2
            edges[-1] = coord[-1] + (coord[-1] - coord[-2]) / 2
            return edges

        raise ValueError(
            f"1D {axis}-coordinate array has incompatible length "
            f"{len(coord)}. Expected {expected_centers} (centers) "
            f"or {expected_edges} (edges)."
        )
    elif coord.ndim == 2:
        m, n = coord.shape
        if (m, n) == (M + 1, N + 1):
            return coord

        if (m, n) == (M, N):
            # Strategy: First pad the coordinate array by extrapolating one
            # layer of "ghost" cells around the perimeter, then compute all
            # edges as average of 4 surrounding padded centers

            # Create padded array with shape (M+2, N+2)
            padded = np.zeros((M + 2, N + 2), dtype=coord.dtype)
            # Copy original centers to interior
            padded[1:-1, 1:-1] = coord

            # Extrapolate edges (sides)
            # Left edge
            padded[1:-1, 0] = coord[:, 0] - (coord[:, 1] - coord[:, 0])
            # Right edge
            padded[1:-1, -1] = coord[:, -1] + (coord[:, -1] - coord[:, -2])
            # Bottom edge
            padded[0, 1:-1] = coord[0, :] - (coord[1, :] - coord[0, :])
            # Top edge
            padded[-1, 1:-1] = coord[-1, :] + (coord[-1, :] - coord[-2, :])

            # Extrapolate corners
            # Bottom-left
            padded[0, 0] = (
                coord[0, 0] - (coord[1, 0] - coord[0, 0]) - (coord[0, 1] - coord[0, 0])
            )
            # Bottom-right
            padded[0, -1] = (
                coord[0, -1]
                - (coord[1, -1] - coord[0, -1])
                + (coord[0, -1] - coord[0, -2])
            )
            # Top-left
            padded[-1, 0] = (
                coord[-1, 0]
                + (coord[-1, 0] - coord[-2, 0])
                - (coord[-1, 1] - coord[-1, 0])
            )
            # Top-right
            padded[-1, -1] = (
                coord[-1, -1]
                + (coord[-1, -1] - coord[-2, -1])
                + (coord[-1, -1] - coord[-1, -2])
            )

            # Now compute all edges as average of 4 surrounding padded centers
            edges = 0.25 * (
                padded[:-1, :-1] + padded[1:, :-1] + padded[:-1, 1:] + padded[1:, 1:]
            )
            return edges

        raise ValueError(
            f"2D {axis}-coordinate array has incompatible shape "
            f"{coord.shape}. Expected ({M}, {N}) for centers or "
            f"({M + 1}, {N + 1}) for edges."
        )


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

        # Convert centers to edges if necessary
        self._x = _maybe_centers_to_edges(self._x, M, N, axis='x')
        self._y = _maybe_centers_to_edges(self._y, M, N, axis='y')

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
        if x.ndim == 1:
            x_left = x[i_flat]
            x_right = x[i_flat + 1]
        else:
            # x is 2D: shape (M+1, N+1) for cell corners
            x_left = x[j_flat, i_flat]
            x_right = x[j_flat, i_flat + 1]

        if y.ndim == 1:
            y_bottom = y[j_flat]
            y_top = y[j_flat + 1]
        else:
            # y is 2D: shape (M+1, N+1) for cell corners
            y_bottom = y[j_flat, i_flat]
            y_top = y[j_flat + 1, i_flat]

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
        M, N = self._c.shape
        self._x = _maybe_centers_to_edges(np.asarray(x), M, N, axis='x')
        self._update_positions()

    def get_ydata(self) -> np.ndarray:
        return self._y

    def set_ydata(self, y: np.ndarray):
        M, N = self._c.shape
        self._y = _maybe_centers_to_edges(np.asarray(y), M, N, axis='y')
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

    def _on_axes_limits_changed(self, _) -> None:
        pass
