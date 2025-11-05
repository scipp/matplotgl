# SPDX-License-Identifier: BSD-3-Clause

from .colorbar import Colorbar
from .toolbar import Toolbar
from .widgets import HBar


class Figure(HBar):
    def __init__(self, *, figsize=(5.0, 3.5), dpi=96, nrows=1, ncols=1) -> None:
        self.axes = []
        self._dpi = dpi
        self._figsize = figsize
        self._nrows = nrows
        self._ncols = ncols
        self.width = self._figsize[0] * self._dpi
        self.height = self._figsize[1] * self._dpi

        self.toolbar = Toolbar()
        self.toolbar._home.on_click(self.home)
        self.toolbar._zoom.observe(self.toggle_zoom, names="value")
        self.toolbar._pan.observe(self.toggle_pan, names="value")

        super().__init__([self.toolbar])

    def home(self, *args):
        for ax in self.axes:
            ax.autoscale()
            # ax.reset()

    def toggle_zoom(self, change):
        for ax in self.axes:
            if change["new"]:
                ax._zoom_down_picker.observe(ax.on_mouse_down, names=["point"])
                ax._zoom_up_picker.observe(ax.on_mouse_up, names=["point"])
                ax._zoom_move_picker.observe(ax.on_mouse_move, names=["point"])
                ax.renderer.controls = [
                    *ax._base_controls,
                    ax._zoom_down_picker,
                    ax._zoom_up_picker,
                    ax._zoom_move_picker,
                ]
                if self.toolbar._pan.value:
                    self.toolbar._pan.value = False
                ax._active_tool = "zoom"
            else:
                ax._zoom_down_picker.unobserve_all()
                ax._zoom_up_picker.unobserve_all()
                ax._zoom_move_picker.unobserve_all()
                ax.renderer.controls = ax._base_controls
                ax._active_tool = None

    def toggle_pan(self, change):
        for ax in self.axes:
            ax.controls.enablePan = change["new"]
            if change["new"]:
                if self.toolbar._zoom.value:
                    self.toolbar._zoom.value = False
                ax._active_tool = "pan"
            else:
                ax._active_tool = None

    # def toggle_pickers(self, change):
    #     for ax in self.axes:
    #         if change["new"]:
    #             ax._zoom_down_picker.observe(ax.on_mouse_down, names=["point"])
    #             ax._zoom_up_picker.observe(ax.on_mouse_up, names=["point"])
    #             ax._zoom_move_picker.observe(ax.on_mouse_move, names=["point"])
    #             ax.renderer.controls = [
    #                 ax.controls,
    #                 ax._zoom_down_picker,
    #                 ax._zoom_up_picker,
    #                 ax._zoom_move_picker,
    #             ]
    #         else:
    #             ax._zoom_down_picker.unobserve_all()
    #             ax._zoom_up_picker.unobserve_all()
    #             ax._zoom_move_picker.unobserve_all()
    #             ax.renderer.controls = [ax.controls]

    # def toggle_pan(self, change):
    #     for ax in self.axes:
    #         ax.toggle_pan(change["new"])

    def add_axes(self, ax):
        self.axes.append(ax)
        ax.set_figure(self)
        self.add(ax)

    def get_size_inches(self):
        return self._figsize

    def set_size_inches(self, w, h=None):
        if h is None:
            h = w[1]
            w = w[0]
        self._figsize = (w, h)
        self.width = self._figsize[0] * self._dpi
        self.height = self._figsize[1] * self._dpi
        for ax in self.axes:
            ax.width = self.width // self._ncols
            ax.height = self.height // self._nrows

    def colorbar(self, mappable, ax=None):
        if ax is None:
            ax = mappable.axes
        cb = Colorbar(
            widget=ax._margins["colorbar"],
            mappable=mappable,
            height=ax.height,
        )
        cb.update()
        mappable._colorbar = cb
        mappable._norm._colorbar = cb
        return cb
