from matplotlib.colorbar import ColorbarBase
from matplotlib.pyplot import Figure


def fig_to_bytes(fig) -> bytes:
    """
    Convert a Matplotlib figure to svg bytes.

    Parameters
    ----------
    fig:
        The figure to be converted.
    """
    from io import BytesIO

    buf = BytesIO()
    fig.savefig(buf, format="svg", bbox_inches="tight")
    buf.seek(0)
    return buf.getvalue()


# def make_colorbar(mappable, height_inches: float) -> str:
#     fig = Figure(figsize=(height_inches * 0.2, height_inches))
#     cax = fig.add_axes([0.05, 0.02, 0.2, 0.98])
#     ColorbarBase(cax, cmap=mappable.cmap)  # , norm=self.normalizer)
#     return fig_to_bytes(fig).decode()


class Colorbar:
    def __init__(self, widget, mappable, height_inches: float):
        self._mappable = mappable
        self._height_inches = height_inches
        self._widget = widget

    def update(self):
        self._mappable._update_colors()
        fig = Figure(figsize=(self._height_inches * 0.2, self._height_inches))
        cax = fig.add_axes([0.05, 0.02, 0.2, 0.98])
        ColorbarBase(cax, cmap=self._mappable.cmap, norm=self._mappable.norm._norm)
        self._widget.value = fig_to_bytes(fig).decode()
