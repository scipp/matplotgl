# SPDX-License-Identifier: BSD-3-Clause

import matplotlib as mpl
import numpy as np
from matplotlib import colors as cm
from matplotlib.pyplot import Figure

from .utils import html_to_svg, latex_to_html

mpl.use("Agg")


class Colorbar:
    def __init__(self, widget, mappable, height: float):
        self._mappable = mappable
        self._height = height
        self._widget = widget

    def update(self):
        self._mappable._update_colors()
        fig = Figure()
        cax = fig.add_subplot(111)
        norm = self._mappable._norm._norm
        cax.set_ylim(norm.vmin, norm.vmax)
        cax.set_yscale('log' if isinstance(norm, cm.LogNorm) else 'linear')

        # Generate colors
        n_colors = 128
        segment_height = self._height / n_colors
        bar_width = 18
        bar_left = 20
        bar_top = 3

        # Build SVG
        svg_parts = [
            f'<svg width="{100}" height="{self._height}">',
        ]

        # Draw color segments
        for i in range(n_colors):
            y = (n_colors - i - 1) * segment_height
            color = cm.to_hex(self._mappable.cmap(i / (n_colors - 1)))
            svg_parts.append(
                f'  <rect x="{bar_left}" y="{y + bar_top}" width="{bar_width}" '
                f'height="{segment_height}" fill="{color}" />'
            )

        # Draw colorbar border
        svg_parts.append(
            f'  <rect x="{bar_left}" y="{bar_top}" width="{bar_width}" '
            f'height="{self._height}" fill="none" stroke="black" stroke-width="1"/>'
        )

        yticks = cax.get_yticks()
        ylabels = cax.get_yticklabels()
        ytexts = [lab.get_text() for lab in ylabels]
        tick_length = 6
        label_offset = 3

        xy = np.vstack((np.zeros_like(yticks), yticks)).T

        inv_trans_axes = cax.transAxes.inverted()
        trans_data = cax.transData
        yticks_axes = inv_trans_axes.transform(trans_data.transform(xy))[:, 1]

        for tick, label in zip(yticks_axes, ytexts, strict=True):
            if tick < 0 or tick > 1.0:
                continue
            y = self._height - (tick * self._height) + bar_top
            svg_parts.append(
                f'<line x1="{bar_left+bar_width}" y1="{y}" '
                f'x2="{bar_left+bar_width+tick_length}" y2="{y}" '
                'style="stroke:black;stroke-width:1" />'
            )

            svg_parts.append(
                f'<text x="{bar_left+bar_width+tick_length+label_offset}" '
                f'y="{y}" text-anchor="start" dominant-baseline="middle">'
                f"{html_to_svg(latex_to_html(label), baseline='middle')}</text>"
            )

        minor_ticks = cax.yaxis.get_minorticklocs()
        if len(minor_ticks) > 0:
            xy = np.vstack((np.zeros_like(minor_ticks), minor_ticks)).T
            yticks_axes = inv_trans_axes.transform(trans_data.transform(xy))[:, 1]

            for tick in yticks_axes:
                if tick < 0 or tick > 1.0:
                    continue
                y = self._height - (tick * self._height) + bar_top
                svg_parts.append(
                    f'<line x1="{bar_left+bar_width}" y1="{y}" '
                    f'x2="{bar_left+bar_width+tick_length * 0.6}" y2="{y}" '
                    'style="stroke:black;stroke-width:0.5" />'
                )

        svg_parts.append('</svg>')

        self._widget.value = '\n'.join(svg_parts)
