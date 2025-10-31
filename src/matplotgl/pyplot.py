# SPDX-License-Identifier: BSD-3-Clause

import matplotlib
import numpy as np
from matplotlib.figure import Figure as MplFigure

from .axes import Axes
from .figure import Figure
from .widgets import VBar

matplotlib.use("Agg")  # Headless backend


def subplots(nrows=1, ncols=1, **kwargs):
    mpl_figure = MplFigure(**kwargs)

    fig = Figure(nrows=nrows, ncols=ncols, **kwargs)
    axs = []
    for j in range(ncols):
        column = []
        for i in range(nrows):
            mplax = mpl_figure.add_subplot(nrows, ncols, j * nrows + i + 1)
            ax = Axes(ax=mplax, figure=fig)
            fig.axes.append(ax)
            column.append(ax)
        axs.append(column)
        fig.add(VBar(column))

    if nrows + ncols == 2:
        out = axs[0][0]
    elif ncols == 1:
        out = np.array(axs[0])
    elif nrows == 1:
        out = np.array([ax[0] for ax in axs])
    else:
        out = np.array(axs)
    return fig, out


__all__ = ["Axes", "Figure", "subplots"]
