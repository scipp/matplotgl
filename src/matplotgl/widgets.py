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


class CanvasOverlay(anywidget.AnyWidget):
    _esm = """
    function render({ model, el }) {
      // Create a container for both renderer and canvas
      const container = document.createElement('div');
      container.style.position = 'relative';
      container.style.width = model.get('width') + 'px';
      container.style.height = model.get('height') + 'px';
      container.style.display = 'inline-block';
      container.style.backgroundColor = '#1a1a1a';

      // Create a slot for the renderer
      const rendererSlot = document.createElement('div');
      rendererSlot.id = 'renderer-slot-' + Math.random().toString(36).substr(2, 9);
      console.log(rendererSlot.id);
      rendererSlot.style.position = 'absolute';
      rendererSlot.style.top = '0';
      rendererSlot.style.left = '0';
      rendererSlot.style.width = '100%';
      rendererSlot.style.height = '100%';
      rendererSlot.style.zIndex = '1';

      // Create canvas element for drawing
      const canvas = document.createElement('canvas');
      canvas.width = model.get('width');
      canvas.height = model.get('height');
      canvas.style.position = 'absolute';
      canvas.style.top = '0';
      canvas.style.left = '0';
      canvas.style.width = '100%';
      canvas.style.height = '100%';
      canvas.style.pointerEvents = 'auto';
      canvas.style.cursor = 'crosshair';
      canvas.style.backgroundColor = 'transparent';
      canvas.style.zIndex = '10';

      container.appendChild(rendererSlot);
      container.appendChild(canvas);
      el.appendChild(container);

      const ctx = canvas.getContext('2d');
      let rendererCanvas = null;

      // Function to create a synthetic mouse event
      function createMouseEvent(type, originalEvent, button) {
        const mouseEvent = new MouseEvent(type, {
          bubbles: true,
          cancelable: true,
          view: window,
          detail: originalEvent.detail,
          screenX: originalEvent.screenX,
          screenY: originalEvent.screenY,
          clientX: originalEvent.clientX,
          clientY: originalEvent.clientY,
          ctrlKey: originalEvent.ctrlKey,
          altKey: originalEvent.altKey,
          shiftKey: originalEvent.shiftKey,
          metaKey:  originalEvent.metaKey,
          button: button,  // Override button
          buttons: button === 2 ? 2 : 1,  // Set buttons bitmask
          relatedTarget:  originalEvent.relatedTarget
        });
        return mouseEvent;
      }

      // Function to find and inject the renderer
      function injectRenderer() {
        const widgetId = model.get('renderer_widget_id');
        if (!widgetId) return;

        // Find the renderer canvas
        setTimeout(() => {
          const allCanvases = document.querySelectorAll('canvas');
          for (let canv of allCanvases) {
            console.log(canv.width, model.get('width'));
            console.log(canv.height, model.get('height'));
            if (canv !== canvas && canv.width === model.get('width') && canv.height === model.get('height')) {
              const parent = canv.parentElement;
              if (parent && !rendererSlot.contains(canv)) {
                const originalContainer = parent.closest('.jupyter-widgets');
                if (originalContainer) {
                  originalContainer.style.display = 'none';
                }
                rendererSlot.appendChild(canv);
                rendererCanvas = canv;
                console.log('Renderer canvas injected');
                break;
              }
            }
          }
        }, 1);
      }

      // Wait for renderer widget ID
      model.on('change:renderer_widget_id', injectRenderer);
      if (model.get('renderer_widget_id')) {
        injectRenderer();
      }

      // Drawing/interaction state
      let isDrawing = false;
      let isPanning = false;
      let startX = 0;
      let startY = 0;
      let currentX = 0;
      let currentY = 0;

      function updateCursor() {
        const mode = model.get('mode');
        if (mode === 'zoom') {
          canvas.style.cursor = 'crosshair';
        } else if (mode === 'pan') {
          canvas.style.cursor = isPanning ? 'grabbing' :  'grab';
        }
      }

      function drawRect() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        if (!isDrawing) return;

        const width = currentX - startX;
        const height = currentY - startY;

        ctx.strokeStyle = model.get('box_color');
        ctx.lineWidth = 2;
        ctx.setLineDash([5, 5]);
        ctx.strokeRect(startX, startY, width, height);

        ctx.fillStyle = model.get('box_color') + '33';
        ctx.fillRect(startX, startY, width, height);
      }

      canvas.addEventListener('mousedown', (e) => {
        if (e.button === 0) {
          const mode = model.get('mode');

          if (mode === 'zoom') {
            isDrawing = true;
            const rect = canvas.getBoundingClientRect();
            startX = e.clientX - rect.left;
            startY = e.clientY - rect.top;
            currentX = startX;
            currentY = startY;

            ctx.clearRect(0, 0, canvas.width, canvas.height);

            model.set('is_drawing', true);
            model.set('start_x', startX);
            model.set('start_y', startY);
            model.save_changes();
          } else if (mode === 'pan') {
            // Forward left-click as right-click to renderer
            if (rendererCanvas) {
              isPanning = true;
              updateCursor();

              const syntheticEvent = createMouseEvent('mousedown', e, 2);
              rendererCanvas.dispatchEvent(syntheticEvent);

              // Prevent default to avoid interference
              e.preventDefault();
              e.stopPropagation();

              model.set('is_panning', true);
              model.save_changes();
            }
          }
        }
      });

      canvas.addEventListener('mousemove', (e) => {
        const mode = model.get('mode');

        if (isDrawing) {
          const rect = canvas.getBoundingClientRect();
          currentX = e.clientX - rect.left;
          currentY = e.clientY - rect.top;

          drawRect();

          model.set('end_x', currentX);
          model.set('end_y', currentY);
          model.save_changes();
        } else if (isPanning && mode === 'pan') {
          // Forward mouse move to renderer
          if (rendererCanvas) {
            const syntheticEvent = createMouseEvent('mousemove', e, 2);
            rendererCanvas.dispatchEvent(syntheticEvent);

            e.preventDefault();
            e.stopPropagation();
          }
        }
      });

      canvas.addEventListener('mouseup', (e) => {
        if (isDrawing) {
          isDrawing = false;

          const rect = canvas.getBoundingClientRect();
          currentX = e.clientX - rect.left;
          currentY = e.clientY - rect.top;

          model.set('is_drawing', false);
          model.set('end_x', currentX);
          model.set('end_y', currentY);
          model.set('box_complete', model.get('box_complete') + 1);
          model.save_changes();

          setTimeout(() => {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
          }, 0);
        } else if (isPanning) {
          // Forward mouse up to renderer
          if (rendererCanvas) {
            const syntheticEvent = createMouseEvent('mouseup', e, 2);
            rendererCanvas.dispatchEvent(syntheticEvent);

            e.preventDefault();
            e.stopPropagation();
          }

          isPanning = false;
          updateCursor();

          model.set('is_panning', false);
          model.set('pan_complete', model.get('pan_complete') + 1);
          model.save_changes();
        }
      });


      // Listen for mode changes
      model.on('change:mode', updateCursor);
      updateCursor();

      model.on('change:clear_overlay', () => {
        if (model.get('clear_overlay')) {
          ctx.clearRect(0, 0, canvas.width, canvas.height);
          model.set('clear_overlay', false);
          model.save_changes();
        }
      });
    }
    export default { render };
    """

    width = traitlets.Int(600).tag(sync=True)
    height = traitlets.Int(400).tag(sync=True)
    box_color = traitlets.Unicode('#ff00ff').tag(sync=True)
    renderer_widget_id = traitlets.Unicode('').tag(sync=True)
    mode = traitlets.Unicode('zoom').tag(sync=True)  # 'zoom' or 'pan'

    # Zoom mode properties
    is_drawing = traitlets.Bool(False).tag(sync=True)
    start_x = traitlets.Float(0.0).tag(sync=True)
    start_y = traitlets.Float(0.0).tag(sync=True)
    end_x = traitlets.Float(0.0).tag(sync=True)
    end_y = traitlets.Float(0.0).tag(sync=True)
    box_complete = traitlets.Int(0).tag(sync=True)

    # Pan mode properties
    is_panning = traitlets.Bool(False).tag(sync=True)
    pan_complete = traitlets.Int(0).tag(sync=True)

    clear_overlay = traitlets.Bool(False).tag(sync=True)

    def __init__(self, renderer=None, width=600, height=400, box_color='#ff00ff'):
        super().__init__()
        self.width = width
        self.height = height
        self.box_color = box_color
        self.renderer = renderer

        if renderer:
            self.renderer_widget_id = renderer.model_id

        self.observe(self._on_box_complete, names=['box_complete'])
        self.observe(self._on_pan_complete, names=['pan_complete'])

    def _on_box_complete(self, change):
        # return
        x1, y1 = min(self.start_x, self.end_x), min(self.start_y, self.end_y)
        x2, y2 = max(self.start_x, self.end_x), max(self.start_y, self.end_y)
        width = x2 - x1
        height = y2 - y1

        print(f"📦 Zoom box: ({x1:.1f}, {y1:.1f}) to ({x2:.1f}, {y2:.1f})")
        print(f"   Size: {width:.1f} x {height:.1f} px")

    def _on_pan_complete(self, change):
        """Called when panning is complete"""
        print(f"🖐️ Pan complete")

    def set_mode(self, mode):
        """Set interaction mode:  'zoom' or 'pan'"""
        if mode in ['zoom', 'pan']:
            self.mode = mode
            print(f"🔧 Mode set to: {mode}")
        else:
            print(f"⚠️ Invalid mode: {mode}. Use 'zoom' or 'pan'")

    def get_box_coords(self):
        x1, y1 = min(self.start_x, self.end_x), min(self.start_y, self.end_y)
        x2, y2 = max(self.start_x, self.end_x), max(self.start_y, self.end_y)
        return (x1, y1, x2, y2)

    def clear(self):
        self.clear_overlay = True
