# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 Matplotgl contributors (https://github.com/matplotgl)

import ipywidgets as ipw
import numpy as np
import pythreejs as p3
from matplotlib.axes import Axes as MplAxes

from .image import Image
from .line import Line
from .mesh import Mesh
from .points import Points
from .utils import latex_to_html
from .widgets import ClickableHTML


class Axes(ipw.GridBox):
    def __init__(self, *, ax: MplAxes, figure=None) -> None:
        self.background_color = "#ffffff"
        self._xmin = 0.0
        self._xmax = 1.0
        self._ymin = 0.0
        self._ymax = 1.0
        self._fig = None
        self._ax = ax
        self._artists = []
        self.lines = []
        self.collections = []
        self.images = []

        # Make background to enable box zoom
        self._background_geometry = p3.PlaneGeometry(
            width=2, height=2, widthSegments=1, heightSegments=1
        )
        self._background_material = p3.MeshBasicMaterial(color=self.background_color)
        self._background_mesh = p3.Mesh(
            geometry=self._background_geometry,
            material=self._background_material,
            position=(0, 0, -101),
        )

        self._mouse_cursor_picker = p3.Picker(
            controlling=self._background_mesh, event="mousemove"
        )
        self._mouse_cursor_picker.observe(self._update_cursor_position, names=["point"])

        self._zoom_down_picker = p3.Picker(
            controlling=self._background_mesh, event="mousedown"
        )
        self._zoom_up_picker = p3.Picker(
            controlling=self._background_mesh, event="mouseup"
        )
        self._zoom_move_picker = p3.Picker(
            controlling=self._background_mesh, event="mousemove"
        )

        rect_pos = np.zeros((5, 3), dtype="float32")
        rect_pos[:, 2] = 101.0
        self._zoom_rect_geometry = p3.LineGeometry(positions=rect_pos)
        self._zoom_rect_line = p3.Line2(
            geometry=self._zoom_rect_geometry,
            material=p3.LineMaterial(color="black", linewidth=1.5),
            visible=False,
        )

        self.camera = p3.OrthographicCamera(
            -0.001, 1.0, 1.0, -0.001, -1, 300, position=[0, 0, 102]
        )
        self.camera.observe(self._on_camera_position_change, names=["position"])

        self.scene = p3.Scene(
            children=[self.camera, self._background_mesh, self._zoom_rect_line],
            background=self.background_color,
        )

        self.controls = p3.OrbitControls(
            controlling=self.camera,
            enableZoom=False,
            enablePan=False,
            enableRotate=False,
        )
        self._base_controls = [self.controls, self._mouse_cursor_picker]
        self.renderer = p3.Renderer(
            camera=self.camera,
            scene=self.scene,
            controls=self._base_controls,
            width=200,
            height=200,
            layout={"grid_area": "renderer", "padding": "0", "margin": "0"},
            antialias=True,
        )

        self._zoom_mouse_down = False
        self._zoom_mouse_moved = False
        self._zoom_limits = {}

        # Tool state: 'zoom' or 'pan'
        self._active_tool = None

        # Pan state tracking
        self._pan_mouse_down = False
        self._pan_start_x = None
        self._pan_start_y = None
        self._pan_camera_left = None
        self._pan_camera_right = None
        self._pan_camera_bottom = None
        self._pan_camera_top = None

        # self._margin_with_ticks = 50
        self._thin_margin = 3

        self._margins = {
            name: ClickableHTML(
                layout={
                    "grid_area": name,
                    "padding": "0",
                    "margin": "0",
                },
            )
            for name in (
                "leftspine",
                "rightspine",
                "bottomspine",
                "topspine",
                "colorbar",
            )
        }
        self._margins.update(
            {
                name: ipw.HTML(
                    layout={"grid_area": name, "padding": "0", "margin": "0"}
                )
                for name in ("xlabel", "ylabel", "title")
            }
        )
        self._margins["cursor"] = ipw.Label(
            "(0.00, 0.00)",
            layout={"grid_area": "cursor", "padding": "0", "margin": "0"},
        )

        if figure is not None:
            self.set_figure(figure)

        super().__init__(
            children=[
                *self._margins.values(),
                self.renderer,
            ],
            layout=ipw.Layout(
                grid_template_columns="auto" * 5,
                grid_template_rows="auto" * 5,
                grid_template_areas="""
            ". . title . ."
            ". . topspine topspine colorbar"
            "ylabel leftspine renderer rightspine colorbar"
            ". leftspine bottomspine bottomspine colorbar"
            ". . xlabel cursor cursor"
            """,
                padding="0",
                grid_gap="0px 0px",
                margin="0",
            ),
        )

    def _update_cursor_position(self, change):
        x, y, _ = change["new"]
        self._margins["cursor"].value = f"({x:.2f}, {y:.2f})"

    def on_mouse_down(self, change):
        x, y, _ = change["new"]
        if self._active_tool == "zoom":
            self._zoom_mouse_down = True
            new_pos = self._zoom_rect_line.geometry.positions.copy()
            new_pos[:, 0] = x
            new_pos[:, 1] = y
            self._zoom_rect_line.geometry.positions = new_pos
            self._zoom_rect_line.visible = True
        # elif self._active_tool == "pan":
        #     self._pan_mouse_down = True
        #     self._pan_start_x = x
        #     self._pan_start_y = y
        #     self._pan_camera_position = self.camera.position
        #     # self._pan_camera_left = self.camera.left
        #     # self._pan_camera_right = self.camera.right
        #     # self._pan_camera_bottom = self.camera.bottom
        #     # self._pan_camera_top = self.camera.top

    def on_mouse_up(self, *ignored):
        if self._zoom_mouse_down:
            self._zoom_mouse_down = False
            self._zoom_rect_line.visible = False
            if self._zoom_mouse_moved:
                array = self._zoom_rect_line.geometry.positions
                self.zoom(
                    [
                        array[:, 0].min(),
                        array[:, 0].max(),
                        array[:, 1].min(),
                        array[:, 1].max(),
                    ]
                )
                self._zoom_mouse_moved = False
        # elif self._pan_mouse_down:
        #     self._pan_mouse_down = False
        #     self._pan_start_x = None
        #     self._pan_start_y = None
        #     self._pan_camera_position = None

    def on_mouse_move(self, change):
        if self._zoom_mouse_down:
            self._zoom_mouse_moved = True
            x, y, _ = change["new"]
            new_pos = self._zoom_rect_line.geometry.positions.copy()
            new_pos[2:4, 0] = x
            new_pos[1:3, 1] = y
            self._zoom_rect_line.geometry.positions = new_pos
        # elif self._pan_mouse_down:
        #     x, y, _ = change["new"]
        #     dx = x - self._pan_start_x
        #     dy = y - self._pan_start_y
        #     pos = self.camera.position
        #     print("Pan xyz:", x, y)
        #     print("Pan start:", self._pan_start_x, self._pan_start_y)
        #     print(f"Panning by ({dx}, {dy})")
        #     print("Old camera pos:", pos)
        #     self.camera.position = [pos[0] - dx, pos[1] - dy, pos[2]]
        #     print("New camera pos:", self.camera.position)
        #     xlim = (self._xmin - dx, self._xmax - dx)
        #     ylim = (self._ymin - dy, self._ymax - dy)
        #     self._ax.set(xlim=xlim, ylim=ylim)
        #     self._make_xticks()
        #     self._make_yticks()

    def _on_camera_position_change(self, change):
        x, y, _ = change["new"]
        # Update tick labels or other UI elements here
        xlim = (
            self._zoom_limits.get("xmin", self._xmin) + x,
            self._zoom_limits.get("xmax", self._xmax) + x,
        )
        ylim = (
            self._zoom_limits.get("ymin", self._ymin) + y,
            self._zoom_limits.get("ymax", self._ymax) + y,
        )
        self._ax.set(xlim=xlim, ylim=ylim)
        self._make_xticks()
        self._make_yticks()

    @property
    def width(self):
        return self.renderer.width

    @width.setter
    def width(self, w):
        self.renderer.width = w
        self._make_xticks()
        # self.set_xlabel(self.get_xlabel())
        # self._margins["xlabel"].width = w
        # self._margins["title"].width = w
        # self._margins["bottomspine"].width = w + self._margin_with_ticks
        # self._margins["topspine"].width = w + self._margin_with_ticks

    @property
    def height(self):
        return self.renderer.height

    @height.setter
    def height(self, h):
        self.renderer.height = h
        self._make_yticks()
        # self.set_ylabel(self.get_ylabel())
        # self._margins["ylabel"].height = h
        # self._margins["leftspine"].height = h + self._margin_with_ticks
        # self._margins["rightspine"].height = h

    def autoscale(self):
        xmin = np.inf
        xmax = -np.inf
        ymin = np.inf
        ymax = -np.inf
        for artist in self._artists:
            lims = artist.get_bbox()
            xmin = min(lims["left"], xmin)
            xmax = max(lims["right"], xmax)
            ymin = min(lims["bottom"], ymin)
            ymax = max(lims["top"], ymax)
        self._xmin = xmin
        self._xmax = xmax
        self._ymin = ymin
        self._ymax = ymax

        # self._background_mesh.geometry = p3.BoxGeometry(
        #     width=2 * (self._xmax - self._xmin),
        #     height=2 * (self._ymax - self._ymin),
        #     widthSegments=1,
        #     heightSegments=1,
        # )
        self._background_mesh.geometry = p3.PlaneGeometry(
            width=2 * (self._xmax - self._xmin),
            height=2 * (self._ymax - self._ymin),
            widthSegments=1,
            heightSegments=1,
        )
        # self._background_mesh.geometry.width = 2 * (self._xmax - self._xmin)
        # self._background_mesh.geometry.height = 2 * (self._ymax - self._ymin)

        self._background_mesh.position = [
            0.5 * (self._xmin + self._xmax),
            0.5 * (self._ymin + self._ymax),
            self._background_mesh.position[-1],
        ]
        self.reset()

    def add_artist(self, artist):
        self._artists.append(artist)
        self.scene.add(artist.get())

    def get_figure(self):
        return self._fig

    def _make_xticks(self):
        """
        Create tick labels on outline edges
        """
        tick_length = 6
        label_offset = 3

        xticks = self.get_xticks()
        xlabels = [lab.get_text() for lab in self.get_xticklabels()]

        xy = np.vstack((xticks, np.zeros_like(xticks))).T
        xticks_axes = self._ax.transAxes.inverted().transform(
            self._ax.transData.transform(xy)
        )[:, 0]

        bottom_string = (
            f'<svg height="calc(1.2em + {tick_length}px + {label_offset}px)" '
            f'width="{self.width}"><line x1="0" y1="0" x2="{self.width}" y2="0" '
            'style="stroke:black;stroke-width:1" />'
        )

        self._margins["topspine"].value = (
            f'<svg height="{self._thin_margin}px" width="{self.width}">'
            f'<line x1="0" y1="{self._thin_margin}" x2="{self.width}" '
            f'y2="{self._thin_margin}" style="stroke:black;stroke-width:1" />'
        )

        for tick, label in zip(xticks_axes, xlabels, strict=True):
            if tick < 0 or tick > 1.0:
                continue
            x = tick * self.width
            bottom_string += (
                f'<line x1="{x}" y1="0" x2="{x}" y2="{tick_length}" '
                'style="stroke:black;stroke-width:1" />'
            )
            bottom_string += (
                f'<text x="{x}" y="{tick_length + label_offset}" '
                'text-anchor="middle" dominant-baseline="hanging">'
                f"{latex_to_html(label)}</text>"
            )

        bottom_string += "</svg></div>"
        self._margins["bottomspine"].value = bottom_string

    def _make_yticks(self):
        """
        Create tick labels on outline edges
        """

        tick_length = 6
        label_offset = 3

        yticks = self.get_yticks()
        ylabels = self.get_yticklabels()
        ytexts = [lab.get_text() for lab in ylabels]

        xy = np.vstack((np.zeros_like(yticks), yticks)).T
        yticks_axes = self._ax.transAxes.inverted().transform(
            self._ax.transData.transform(xy)
        )[:, 1]

        # Predict width of the left margin based on the longest label
        max_length = max(lab.get_tightbbox().width for lab in ylabels)
        width = f"calc({max_length}px + {tick_length}px + {label_offset}px)"
        width1 = f"calc({max_length}px + {label_offset}px)"
        width2 = f"calc({max_length}px)"

        left_string = (
            f'<svg height="{self.height}" width="{width}">'
            f'<line x1="{width}" y1="0" '
            f'x2="{width}" y2="{self.height}" '
            'style="stroke:black;stroke-width:1" />'
        )

        self._margins["rightspine"].value = (
            f'<svg height="{self.height}" width="{self._thin_margin}">'
            f'<line x1="0" y1="0" x2="0" y2="{self.height}" '
            f'style="stroke:black;stroke-width:1" />'
        )

        for tick, label in zip(yticks_axes, ytexts, strict=True):
            if tick < 0 or tick > 1.0:
                continue
            y = self.height - (tick * self.height)
            left_string += (
                f'<line x1="{width}" y1="{y}" '
                f'x2="{width1}" y2="{y}" '
                'style="stroke:black;stroke-width:1" />'
            )

            left_string += (
                f'<text x="{width2}" '
                f'y="{y}" text-anchor="end" dominant-baseline="middle">'
                f"{latex_to_html(label)}</text>"
            )

        left_string += "</svg></div>"
        self._margins["leftspine"].value = left_string

    def get_xlim(self):
        return self._xmin, self._xmax

    def set_xlim(self, left, right=None):
        self._ax.set_xlim(left, right)
        self._zoom_limits.pop("xmin", None)
        self._zoom_limits.pop("xmax", None)
        if right is None:
            right = left[1]
            left = left[0]
        self._xmin = left
        self._xmax = right
        self.camera.left = left
        self.camera.right = right
        self._make_xticks()

    def get_ylim(self):
        return self._ymin, self._ymax

    def set_ylim(self, bottom, top=None):
        self._ax.set_ylim(bottom, top)
        self._zoom_limits.pop("ymin", None)
        self._zoom_limits.pop("ymax", None)
        if top is None:
            top = bottom[1]
            bottom = bottom[0]
        self._ymin = bottom
        self._ymax = top
        self.camera.bottom = bottom
        self.camera.top = top
        self._make_yticks()

    def get_xticks(self):
        return self._ax.get_xticks()

    def get_xticklabels(self):
        return self._ax.get_xticklabels()

    def get_yticks(self):
        return self._ax.get_yticks()

    def get_yticklabels(self):
        return self._ax.get_yticklabels()

    def get_xscale(self):
        return self._ax.get_xscale()

    def set_xscale(self, scale):
        self._ax.set_xscale(scale)
        for artist in self._artists:
            artist._set_xscale(scale)
        self.autoscale()
        self._make_xticks()

    def get_yscale(self):
        return self._ax.get_yscale()

    def set_yscale(self, scale):
        self._ax.set_yscale(scale)
        for artist in self._artists:
            artist._set_yscale(scale)
        self.autoscale()
        self._make_yticks()

    def zoom(self, box):
        self._zoom_limits = {
            "xmin": box[0],
            "xmax": box[1],
            "ymin": box[2],
            "ymax": box[3],
        }
        with self.camera.hold_trait_notifications():
            self.camera.left = self._zoom_limits["xmin"]
            self.camera.right = self._zoom_limits["xmax"]
            self.camera.bottom = self._zoom_limits["ymin"]
            self.camera.top = self._zoom_limits["ymax"]
        if self.get_xscale() == "log":
            xlim = (
                10.0 ** self._zoom_limits["xmin"],
                10.0 ** self._zoom_limits["xmax"],
            )
        else:
            xlim = (self._zoom_limits["xmin"], self._zoom_limits["xmax"])
        if self.get_yscale() == "log":
            ylim = (
                10.0 ** self._zoom_limits["ymin"],
                10.0 ** self._zoom_limits["ymax"],
            )
        else:
            ylim = (self._zoom_limits["ymin"], self._zoom_limits["ymax"])
        self._ax.set(xlim=xlim, ylim=ylim)
        self._make_xticks()
        self._make_yticks()

    def reset(self):
        self._zoom_limits.clear()
        xop = np.log10 if self.get_xscale() == "log" else float
        left, right = xop(self._xmin), xop(self._xmax)
        yop = np.log10 if self.get_yscale() == "log" else float
        bottom, top = yop(self._ymin), yop(self._ymax)
        with self.camera.hold_trait_notifications():
            self.camera.left = left
            self.camera.right = right
            self.camera.bottom = bottom
            self.camera.top = top
            self.camera.position = [0, 0, self.camera.position[2]]
            self.controls.target = [0, 0, 0]
            # self.camera.position = [0, 0, self.camera.position[2]]
        self._ax.set(xlim=(self._xmin, self._xmax), ylim=(self._ymin, self._ymax))
        self._make_xticks()
        self._make_yticks()

    def set_figure(self, fig):
        self._fig = fig
        # self._dpi = fig._dpi
        self.width = self._fig.width // self._fig._ncols
        self.height = self._fig.height // self._fig._nrows
        self.renderer.layout.height = f"{self.height}px"
        self.renderer.layout.width = f"{self.width}px"
        self._make_xticks()
        self._make_yticks()

    def toggle_pan(self, value):
        self.controls.enablePan = value

    def set_xlabel(self, label, fontsize="1.1em"):
        if label:
            # Height should be 115% of fontsize to account for line height
            # height = "calc(1.15 * {fontsize})"
            self._margins["xlabel"].value = (
                '<div style="position:relative; '
                # f'width: {self.width}px; height: {fontsize};">'
                f'width: {self.width}px; height: calc(1.3 * {fontsize});">'
                '<div style="position:relative; top: 50%;left: 50%; '
                f"transform: translate(-50%, -50%); font-size: {fontsize};"
                f'float:left;">{label.replace(" ", "&nbsp;")}</div></div>'
            )
        else:
            self._margins["xlabel"].value = ""
        self._margins["xlabel"]._raw_string = label

    def get_xlabel(self):
        return self._margins["xlabel"]._raw_string

    def set_ylabel(self, label, fontsize="1.1em"):
        if label:
            self._margins["ylabel"].value = (
                '<div style="position:relative; '
                f'width: calc(1.25 * {fontsize}); height: {self.height}px;">'
                '<div style="position:relative; top: 50%;left: 50%; '
                f"transform: translate(-50%, -50%) rotate(-90deg); "
                f"font-size: {fontsize};"
                f'float:left;">{label.replace(" ", "&nbsp;")}</div></div>'
            )
        else:
            self._margins["ylabel"].value = ""
        self._margins["ylabel"]._raw_string = label

    def get_ylabel(self):
        return self._margins["ylabel"]._raw_string

    def set_title(self, title, fontsize="1.2em"):
        if title:
            self._margins["title"].value = (
                '<div style="position:relative; '
                f'width: {self.width}px; height: calc(1.3 * {fontsize});">'
                '<div style="position:relative; top: 50%;left: 50%; '
                f"transform: translate(-50%, -50%); font-size: {fontsize};"
                f'float:left;">{title.replace(" ", "&nbsp;")}</div></div>'
            )
        else:
            self._margins["title"].value = ""
        self._margins["title"]._raw_string = title

    def get_title(self):
        return self._margins["title"]._raw_string

    def plot(self, *args, color=None, **kwargs):
        if color is None:
            color = f"C{len(self.lines)}"
        line = Line(*args, color=color, **kwargs)
        line.axes = self
        self.lines.append(line)
        self.add_artist(line)
        self.autoscale()
        return line

    def scatter(self, *args, c=None, **kwargs):
        if c is None:
            c = f"C{len(self.collections)}"
        coll = Points(*args, c=c, **kwargs)
        coll.axes = self
        self.collections.append(coll)
        self.add_artist(coll)
        self.autoscale()
        return coll

    def imshow(self, *args, **kwargs):
        image = Image(*args, **kwargs)
        image.axes = self
        self.images.append(image)
        self.add_artist(image)
        self.autoscale()
        return image

    def pcolormesh(self, *args, **kwargs):
        mesh = Mesh(*args, **kwargs)
        mesh.axes = self
        self.collections.append(mesh)
        self.add_artist(mesh)
        self.autoscale()
        return mesh
