# SPDX-License-Identifier: BSD-3-Clause

import anywidget
import traitlets
from ipywidgets import HBox, VBox, Widget


class Bar:
    """
    A simple mixin to provide add and remove helper methods for HBox/VBox containers.
    """

    def __getitem__(self, ind):
        return self.children[ind]

    def add(self, obj: Widget):
        """
        Append a widget to the list of children.
        """
        self.children = [*list(self.children), obj]

    def remove(self, obj: Widget):
        """
        Remove a widget from the list of children.
        """
        children = list(self.children)
        children.remove(obj)
        self.children = children


class VBar(VBox, Bar):
    """
    Vertical bar container.
    """

    def __getitem__(self, ind):
        if isinstance(ind, int):
            return self.children[ind]
        elif isinstance(ind, slice):
            return VBar(self.children[ind])


class HBar(HBox, Bar):
    """
    Horizontal bar container.
    """

    def __getitem__(self, ind):
        if isinstance(ind, int):
            return self.children[ind]
        elif isinstance(ind, slice):
            return HBar(self.children[ind])


class Box(VBar):
    """
    Container widget that accepts a list of items. For each item in the list, if the
    item is itself a list, it will be made into a horizontal row of the underlying
    items, if not, the item will span then entire row.
    Finally, all the rows will be placed inside a vertical box container.

    Parameters
    ----------

    widgets:
        List of widgets to place in the box.
    """

    def __init__(self, widgets):
        super().__init__(
            [HBar(view) if isinstance(view, list | tuple) else view for view in widgets]
        )


class ClickableHTML(anywidget.AnyWidget):
    _esm = """
    export function render({ model, el }) {
      let div = document.createElement("div");
      div.innerHTML = model.get("value");
      div.style.cursor = "pointer";
      div.style.lineHeight = "0";  // Remove line-height spacing

      // Make sure SVGs don't have extra spacing
      const svgs = div.querySelectorAll("svg");
      svgs.forEach(svg => {
        svg.style.display = "block";
      });

      // Set tooltip if provided
      const tooltip_text = model.get("tooltip_text");
      if (tooltip_text) {
        div.title = tooltip_text;
      }


      div.ondblclick = () => {
        model.set("_dblclick_trigger", model.get("_dblclick_trigger") + 1);
        model.save_changes();
      };
      el.appendChild(div);

      model.on("change:value", () => {
        div.innerHTML = model.get("value");
        // Re-apply block display to any new SVGs
        const svgs = div.querySelectorAll("svg");
        svgs.forEach(svg => {
          svg.style.display = "block";
        });
      });

      model.on("change:tooltip_text", () => {
        div.title = model.get("tooltip_text");
      });
    }
    """

    value = traitlets.Unicode("").tag(sync=True)
    tooltip_text = traitlets.Unicode("").tag(sync=True)
    _dblclick_trigger = traitlets.Int(0).tag(sync=True)

    def __init__(self, value="", tooltip="", **kwargs):
        super().__init__(value=value, tooltip_text=tooltip, **kwargs)

    def on_dblclick(self, on_dblclick):
        self.observe(lambda change: on_dblclick(self), "_dblclick_trigger")
