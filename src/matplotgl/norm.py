import numpy as np
from matplotlib import colors as cm


class Normalizer:
    def __init__(self, vmin: float, vmax: float, norm: str = "linear") -> None:
        self._colorbar = None
        self._artists = []
        if norm == "log":
            self._norm = cm.LogNorm(vmin=vmin, vmax=vmax)
        else:
            self._norm = cm.Normalize(vmin=vmin, vmax=vmax)

    def __call__(self, value: float | np.ndarray) -> float | np.ndarray:
        return self._norm(value)

    @property
    def vmin(self) -> float:
        return self._norm.vmin

    @vmin.setter
    def vmin(self, vmin: float) -> None:
        self._norm.vmin = vmin
        if self._colorbar is not None:
            self._colorbar.update()

    @property
    def vmax(self) -> float:
        return self._norm.vmax

    @vmax.setter
    def vmax(self, vmax: float) -> None:
        self._norm.vmax = vmax
        if self._colorbar is not None:
            self._colorbar.update()
