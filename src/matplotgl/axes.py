# SPDX-License-Identifier: BSD-3-Clause

import math

import ipywidgets as ipw
import numpy as np
import pythreejs as p3
from matplotlib.axes import Axes as MplAxes

from .image import Image
from .line import Line
from .mesh import Mesh
from .points import Points
from .utils import html_to_svg, latex_to_html
from .widgets import ClickableHTML


def _min_with_none(a, b):
    return a if b is None else min(a, b)


def _max_with_none(a, b):
    return a if b is None else max(a, b)


def _em_to_px(em_value):
    """Convert em units to pixels using standard conversion (1em = 16px)."""
    return int(em_value * 16)


def _multiply_font_size(fontsize, multiplier):
    """
    Multiply a font size by a factor.

    Args:
        fontsize: Font size string (e.g., "1.2em", "14px", "10pt")
        multiplier: Factor to multiply by

    Returns:
        String with multiplied font size
    """
    value = float(fontsize[:-2])
    unit = fontsize[-2:]
    result_value = value * multiplier
    return f"{result_value}{unit}"


class Axes(ipw.GridBox):
    def __init__(self, *, ax: MplAxes, figure=None) -> None:
        self.background_color = "#ffffff"
        self._xmin = 0.0
        self._xmax = 1.0
        self._ymin = 0.0
        self._ymax = 1.0
        self._fig = None
        self._spine_linewidth = 1.0
        self._ax = ax
        self._artists = []
        self.lines = []
        self.collections = []
        self.images = []

        # Make background to enable box zoom.
        # Use a size based on limits of the float32 range.
        self._background_geometry = p3.PlaneGeometry(
            width=6e38, height=6e38, widthSegments=1, heightSegments=1
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

        tooltips = {
            "leftspine": "Double-click to toggle y-scale",
            "bottomspine": "Double-click to toggle x-scale",
        }

        self._margins = {
            name: ClickableHTML(
                layout={
                    "grid_area": name,
                    "padding": "0",
                    "margin": "0",
                },
                tooltip=tooltips.get(name, ""),
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
            layout={
                "grid_area": "cursor",
                "padding": "0",
                "margin": "0",
                "width": "6em",
            },
        )

        if figure is not None:
            self.set_figure(figure)

        self._margins['leftspine'].on_dblclick(self._toggle_yscale)
        self._margins['bottomspine'].on_dblclick(self._toggle_xscale)

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
        xmin = None
        xmax = None
        ymin = None
        ymax = None
        for artist in self._artists:
            lims = artist.get_bbox()
            xmin = _min_with_none(lims["left"], xmin)
            xmax = _max_with_none(lims["right"], xmax)
            ymin = _min_with_none(lims["bottom"], ymin)
            ymax = _max_with_none(lims["top"], ymax)
        self._xmin = (
            xmin
            if xmin is not None
            else (0.0 if self.get_xscale() == "linear" else 1.0)
        )
        self._xmax = (
            xmax
            if xmax is not None
            else (1.0 if self.get_xscale() == "linear" else 10.0)
        )
        self._ymin = (
            ymin
            if ymin is not None
            else (0.0 if self.get_yscale() == "linear" else 1.0)
        )
        self._ymax = (
            ymax
            if ymax is not None
            else (1.0 if self.get_yscale() == "linear" else 10.0)
        )

        self.reset()

    def add_artist(self, artist):
        self._artists.append(artist)
        self.scene.add(artist._as_object3d())

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

        inv_trans_axes = self._ax.transAxes.inverted()
        trans_data = self._ax.transData
        xticks_axes = inv_trans_axes.transform(trans_data.transform(xy))[:, 0]

        height_px = _em_to_px(1.2) + tick_length + label_offset
        bottom_string = [
            (
                f'<svg height="{height_px}px" '
                f'width="{self.width}"><line x1="0" y1="0" '
                f'x2="{self.width}" y2="0" '
                f'style="stroke:black;stroke-width:{self._spine_linewidth}" />'
            )
        ]

        self._margins["topspine"].value = (
            f'<svg height="{self._thin_margin}px" width="{self.width}">'
            f'<line x1="0" y1="{self._thin_margin}" x2="{self.width}" '
            f'y2="{self._thin_margin}" style="stroke:black;stroke-width:'
            f'{self._spine_linewidth}" />'
        )

        for tick, label in zip(xticks_axes, xlabels, strict=True):
            if tick < 0 or tick > 1.0:
                continue
            x = tick * self.width
            bottom_string.append(
                f'<line x1="{x}" y1="0" x2="{x}" y2="{tick_length}" '
                'style="stroke:black;stroke-width:1" />'
            )
            bottom_string.append(
                f'<text x="{x}" y="{tick_length + label_offset}" '
                'text-anchor="middle" dominant-baseline="hanging">'
                f"{html_to_svg(latex_to_html(label), baseline='hanging')}</text>"
            )

        minor_ticks = self._ax.xaxis.get_minorticklocs()
        if len(minor_ticks) > 0:
            xy = np.vstack((minor_ticks, np.zeros_like(minor_ticks))).T
            xticks_axes = inv_trans_axes.transform(trans_data.transform(xy))[:, 0]

            for tick in xticks_axes:
                if tick < 0 or tick > 1.0:
                    continue
                x = tick * self.width
                bottom_string.append(
                    f'<line x1="{x}" y1="0" x2="{x}" y2="{tick_length * 0.7}" '
                    'style="stroke:black;stroke-width:0.5" />'
                )

        bottom_string.append("</svg></div>")
        self._margins["bottomspine"].value = "".join(bottom_string)

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

        inv_trans_axes = self._ax.transAxes.inverted()
        trans_data = self._ax.transData
        yticks_axes = inv_trans_axes.transform(trans_data.transform(xy))[:, 1]

        # Predict width of the left margin based on the longest label
        # Need to convert to integer to avoid sub-pixel rendering issues
        max_length = math.ceil(max(lab.get_tightbbox().width for lab in ylabels))
        width_px = max_length + tick_length + label_offset
        width1_px = max_length + label_offset
        width2_px = max_length
        width3_px = max_length + int(tick_length * 0.3) + label_offset

        left_string = [
            (
                f'<svg height="{self.height}" width="{width_px}px">'
                f'<line x1="{width_px}" y1="0" '
                f'x2="{width_px}" y2="{self.height}" '
                f'style="stroke:black;stroke-width:{self._spine_linewidth}" />'
            )
        ]

        self._margins["rightspine"].value = (
            f'<svg height="{self.height}" width="{self._thin_margin}">'
            f'<line x1="0" y1="0" x2="0" y2="{self.height}" '
            f'style="stroke:black;stroke-width:{self._spine_linewidth}" />'
        )

        for tick, label in zip(yticks_axes, ytexts, strict=True):
            if tick < 0 or tick > 1.0:
                continue
            y = self.height - (tick * self.height)
            left_string.append(
                f'<line x1="{width_px}" y1="{y}" '
                f'x2="{width1_px}" y2="{y}" '
                'style="stroke:black;stroke-width:1" />'
            )

            left_string.append(
                f'<text x="{width2_px}" '
                f'y="{y}" text-anchor="end" dominant-baseline="middle">'
                f"{html_to_svg(latex_to_html(label), baseline='middle')}</text>"
            )

        minor_ticks = self._ax.yaxis.get_minorticklocs()
        if len(minor_ticks) > 0:
            xy = np.vstack((np.zeros_like(minor_ticks), minor_ticks)).T
            yticks_axes = inv_trans_axes.transform(trans_data.transform(xy))[:, 1]

            for tick in yticks_axes:
                if tick < 0 or tick > 1.0:
                    continue
                y = self.height - (tick * self.height)
                left_string.append(
                    f'<line x1="{width_px}" y1="{y}" '
                    f'x2="{width3_px}" y2="{y}" '
                    'style="stroke:black;stroke-width:0.5" />'
                )

        left_string.append("</svg></div>")
        self._margins["leftspine"].value = "".join(left_string)

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
        self.camera.left = left - self.camera.position[0]
        self.camera.right = right - self.camera.position[0]
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
        self.camera.bottom = bottom - self.camera.position[1]
        self.camera.top = top - self.camera.position[1]
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
        if scale not in ("linear", "log"):
            raise ValueError("Scale must be 'linear' or 'log'")
        if scale == self.get_xscale():
            return
        self._ax.set_xscale(scale)
        for artist in self._artists:
            artist._set_xscale(scale)
        self.autoscale()
        self._make_xticks()

    def get_yscale(self):
        return self._ax.get_yscale()

    def set_yscale(self, scale):
        if scale not in ("linear", "log"):
            raise ValueError("Scale must be 'linear' or 'log'")
        if scale == self.get_yscale():
            return
        self._ax.set_yscale(scale)
        for artist in self._artists:
            artist._set_yscale(scale)
        self.autoscale()
        self._make_yticks()

    def _toggle_xscale(self, _):
        self.set_xscale("log" if self.get_xscale() == "linear" else "linear")

    def _toggle_yscale(self, _):
        self.set_yscale("log" if self.get_yscale() == "linear" else "linear")

    def zoom(self, box):
        self._zoom_limits = {
            "xmin": box[0],
            "xmax": box[1],
            "ymin": box[2],
            "ymax": box[3],
        }
        with self.camera.hold_trait_notifications():
            self.camera.left = self._zoom_limits["xmin"] - self.camera.position[0]
            self.camera.right = self._zoom_limits["xmax"] - self.camera.position[0]
            self.camera.bottom = self._zoom_limits["ymin"] - self.camera.position[1]
            self.camera.top = self._zoom_limits["ymax"] - self.camera.position[1]
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
            height = _multiply_font_size(fontsize, 1.3)
            self._margins["xlabel"].value = (
                '<div style="position:relative; '
                f'width: {self.width}px; height: {height};">'
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
            width = _multiply_font_size(fontsize, 1.25)
            self._margins["ylabel"].value = (
                '<div style="position:relative; '
                f'width: {width}; height: {self.height}px;">'
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
            height = _multiply_font_size(fontsize, 1.3)
            self._margins["title"].value = (
                '<div style="position:relative; '
                f'width: {self.width}px; height: {height};">'
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
        line = Line(
            *args,
            color=color,
            xscale=self.get_xscale(),
            yscale=self.get_yscale(),
            **kwargs,
        )
        line.axes = self
        self.lines.append(line)
        self.add_artist(line)
        self.autoscale()
        return line

    def semilogx(self, *args, **kwargs):
        out = self.plot(*args, **kwargs)
        self.set_xscale("log")
        return out

    def semilogy(self, *args, **kwargs):
        out = self.plot(*args, **kwargs)
        self.set_yscale("log")
        return out

    def loglog(self, *args, **kwargs):
        out = self.plot(*args, **kwargs)
        self.set_xscale("log")
        self.set_yscale("log")
        return out

    def scatter(self, *args, c=None, **kwargs):
        if c is None:
            c = f"C{len(self.collections)}"
        coll = Points(
            *args, c=c, xscale=self.get_xscale(), yscale=self.get_yscale(), **kwargs
        )
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
        mesh = Mesh(*args, xscale=self.get_xscale(), yscale=self.get_yscale(), **kwargs)
        mesh.axes = self
        self.collections.append(mesh)
        self.add_artist(mesh)
        self.autoscale()
        return mesh
