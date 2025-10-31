# SPDX-License-Identifier: BSD-3-Clause

import ipywidgets as ipw


class Toolbar(ipw.VBox):
    def __init__(self) -> None:
        self._home = ipw.Button(
            icon="home", tooltip="autoscale", layout={"width": "36px", "padding": "0"}
        )
        self._zoom = ipw.ToggleButton(
            icon="square-o", tooltip="zoom", layout={"width": "36px", "padding": "0"}
        )
        self._pan = ipw.ToggleButton(
            icon="arrows",
            tooltip="pan (right-click)",
            layout={"width": "36px", "padding": "0"},
        )
        super().__init__([self._home, self._zoom, self._pan])
