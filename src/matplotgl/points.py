# SPDX-License-Identifier: BSD-3-Clause

import warnings

import matplotlib as mpl
import matplotlib.colors as cm
import numpy as np
import pythreejs as p3

from .norm import Normalizer
from .utils import find_limits, fix_empty_range

SHADER_LIBRARY = {
    "o": """
varying vec3 vColor;

void main() {
    // Calculate distance from center of point sprite
    vec2 center = gl_PointCoord - vec2(0.5, 0.5);
    float dist = length(center);

    // Discard fragments outside the circle
    if (dist > 0.5) {
        discard;
    }

    // Optional: add anti-aliasing at the edge
    float alpha = 1.0 - smoothstep(0.45, 0.5, dist);

    gl_FragColor = vec4(vColor, alpha);
}
""",
    "s": """
varying vec3 vColor;

void main() {
    gl_FragColor = vec4(vColor, 1.0);
    }
""",
    "^": """
varying vec3 vColor;

void main() {
    vec2 center = gl_PointCoord - vec2(0.5, 0.5);
    if (center.y < abs(center.x) * 1.73205080757) {
        discard;
    }
    gl_FragColor = vec4(vColor, 1.0);
}
""",
}


class Points:
    def __init__(
        self,
        x,
        y,
        c="C0",
        s=3,
        marker="s",
        zorder=0,
        cmap="viridis",
        norm: str = "linear",
    ) -> None:
        self.axes = None
        self._x = np.asarray(x)
        self._y = np.asarray(y)
        self._xscale = "linear"
        self._yscale = "linear"
        self._zorder = zorder

        if not isinstance(c, str) or not np.isscalar(s) or marker != "s":
            if isinstance(c, str):
                self._c = np.ones_like(self._x)
                self._norm = Normalizer(vmin=1, vmax=1)
                self._cmap = cm.LinearSegmentedColormap.from_list("tmp", [c, c])
                # (
                #     np.ones_like(self._x)
                # )
            else:
                self._c = np.asarray(c)
                self._norm = Normalizer(
                    vmin=np.min(self._c), vmax=np.max(self._c), norm=norm
                )
                self._cmap = mpl.colormaps[cmap].copy()
                # rgba = self.cmap(self.norm(self._c))

            colors = self._make_colors()

            if np.isscalar(s):
                sizes = np.full_like(self._x, s, dtype=np.float32)
            else:
                sizes = np.asarray(s, dtype=np.float32)

            # Custom vertex shader for variable size and color
            vertex_shader = """
attribute float size;
attribute vec3 customColor;
varying vec3 vColor;

void main() {
    vColor = customColor;
    vec4 mvPosition = modelViewMatrix * vec4(position, 1.0);
    gl_PointSize = size;
    gl_Position = projectionMatrix * mvPosition;
}
"""

            self._geometry = p3.BufferGeometry(
                attributes={
                    "position": p3.BufferAttribute(
                        array=np.array(
                            [self._x, self._y, np.full_like(self._x, self._zorder)],
                            dtype="float32",
                        ).T
                    ),
                    "customColor": p3.BufferAttribute(array=colors),
                    "size": p3.BufferAttribute(array=sizes),
                }
            )
            # Create ShaderMaterial with custom shaders
            self._material = p3.ShaderMaterial(
                vertexShader=vertex_shader,
                fragmentShader=SHADER_LIBRARY[marker],
                transparent=True,
            )
        else:
            self._geometry = p3.BufferGeometry(
                attributes={
                    "position": p3.BufferAttribute(
                        array=np.array(
                            [self._x, self._y, np.full_like(self._x, self._zorder)],
                            dtype="float32",
                        ).T
                    ),
                }
            )

            self._material = p3.PointsMaterial(color=cm.to_hex(c), size=s)

        self._points = p3.Points(geometry=self._geometry, material=self._material)

    def _make_colors(self) -> np.ndarray:
        return self._cmap(self.norm(self._c))[..., :3].astype("float32")

    def _update_colors(self) -> None:
        self._geometry.attributes["customColor"].array = self._make_colors()

    def get_bbox(self):
        pad = 0.03
        left, right = fix_empty_range(find_limits(self._x, scale=self._xscale, pad=pad))
        bottom, top = fix_empty_range(find_limits(self._y, scale=self._yscale, pad=pad))
        return {"left": left, "right": right, "bottom": bottom, "top": top}

    def _update(self):
        with warnings.catch_warnings(category=RuntimeWarning, action="ignore"):
            xx = self._x if self._xscale == "linear" else np.log10(self._x)
            yy = self._y if self._yscale == "linear" else np.log10(self._y)
        self._geometry.attributes["position"].array = np.array(
            [xx, yy, np.full_like(xx, self._zorder)], dtype="float32"
        ).T

    def get(self):
        return self._points

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

    def set_data(self, xy):
        self._x = np.asarray(xy[:, 0])
        self._y = np.asarray(xy[:, 1])
        self._update()

    def _set_xscale(self, scale):
        self._xscale = scale
        self._update()

    def _set_yscale(self, scale):
        self._yscale = scale
        self._update()

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
