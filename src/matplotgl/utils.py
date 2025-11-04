import re
from typing import Literal

import numpy as np
import pythreejs as p3


def value_to_string(val, precision: int = 3) -> str:
    """
    Convert a number to a human readable string.

    Parameters
    ----------
    val:
        The input number.
    precision:
        The number of decimal places to use for the string output.
    """
    if not isinstance(val, float):
        text = str(val)
    elif val == 0:
        text = "{val:.{prec}f}".format(val=val, prec=precision)
    elif (abs(val) >= 1.0e4) or (abs(val) <= 1.0e-4):
        text = "{val:.{prec}e}".format(val=val, prec=precision)
    else:
        text = str(val)
        if len(text) > precision + 2 + (text[0] == "-"):
            text = "{val:.{prec}f}".format(val=val, prec=precision)
    return text


def make_sprite(
    string: str,
    position: tuple[float, float, float],
    color: str = "black",
    size: float = 1.0,
) -> p3.Sprite:
    """
    Make a text-based sprite for axis tick.
    """
    sm = p3.SpriteMaterial(
        map=p3.TextTexture(string=string, color=color, size=60, squareTexture=False),
        transparent=True,
    )
    return p3.Sprite(material=sm, position=position, scale=[size, size, size])


def find_limits(
    x: np.ndarray,
    scale: Literal["linear", "log"] = "linear",
    pad: bool | float = False,
) -> tuple[float, float]:
    """
    Find sensible limits, depending on linear or log scale.
    If there are no finite values in the array, raise an error.
    If there are no positive values in the array, and the scale is log, fall back to
    some sensible default values.

    Parameters
    ----------
    x:
        The data for which to find the limits.
    scale:
        The scale to use for the limits.
    pad:
        Whether to pad the limits.
    """
    # is_dt = is_datetime(x)
    # Computing limits for string arrays is not supported, so we convert them to
    # dummy numerical arrays.
    if x.dtype == str:
        x = np.arange(float(len(x)))
    # v = x.values
    finite_inds = np.isfinite(x)
    if np.sum(finite_inds) == 0:
        raise ValueError("No finite values were found in array. Cannot compute limits.")
    finite_vals = x[finite_inds]
    finite_max = None
    if scale == "log":
        positives = finite_vals > 0
        if np.sum(positives) == 0:
            finite_min = 0.1
            finite_max = 1.0
        else:
            initial = (np.finfo if x.dtype.kind == "f" else np.iinfo)(x.dtype).max
            finite_min = np.amin(finite_vals, initial=initial, where=finite_vals > 0)
    else:
        finite_min = np.amin(finite_vals)
    if finite_max is None:
        finite_max = np.amax(finite_vals)
    if pad:
        delta = 0.05 if isinstance(pad, bool) else pad
        if scale == "log":
            p = (finite_max / finite_min) ** delta
            finite_min /= p
            finite_max *= p
        if scale == "linear":
            p = (finite_max - finite_min) * delta
            finite_min -= p
            finite_max += p
    return finite_min, finite_max


def fix_empty_range(
    lims: tuple[float, float],
) -> tuple[float, float]:
    """
    Range correction in case xmin == xmax
    """
    if lims[0] != lims[1]:
        return lims
    if lims[0] == 0.0:
        dx = 0.5
    else:
        dx = 0.5 * abs(lims[0])
    return lims[0] - dx, lims[1] + dx


def latex_to_html(latex_str: str) -> str:
    """Convert simple matplotlib-style LaTeX tick labels to HTML.

    Examples handled:
      - $\\mathdefault{10^{-8}}$ -> 10<sup>-8</sup>
      - $2.5 \\times 10^{3}$ -> 2.5 &times; 10<sup>3</sup>
      - x_{0}^{2} -> x<sub>0</sub><sup>2</sup>
      - $\\alpha + \\beta$ -> &alpha; + &beta;
    """
    # Remove $\mathdefault{...}$ wrapper
    s = re.sub(r"^\$\\mathdefault\{(.*)\}\$$", r"\1", latex_str)
    # Also handle plain $...$ if no mathdefault
    s = re.sub(r"^\$(.*)\$$", r"\1", s)

    # Handle nested/braced superscripts first (iteratively)
    while re.search(r"\^{([^{}]+)}", s):
        s = re.sub(r"\^{([^{}]+)}", r"<sup>\1</sup>", s)
    s = re.sub(r"\^(\S)", r"<sup>\1</sup>", s)

    # Handle nested/braced subscripts
    while re.search(r"_{([^{}]+)}", s):
        s = re.sub(r"_{([^{}]+)}", r"<sub>\1</sub>", s)
    s = re.sub(r"_(\S)", r"<sub>\1</sub>", s)

    # Generic replacement: \symbolname -> &symbolname;
    # This catches most Greek letters and common HTML entities
    s = re.sub(r"\\([a-zA-Z]+)", r"&\1;", s)

    # Special cases that don't follow the pattern (optional overrides)
    special_replacements = {
        "&cdot;": "&middot;",
    }

    for entity, replacement in special_replacements.items():
        s = s.replace(entity, replacement)

    return s


def html_to_svg(text: str, baseline: str) -> str:
    """Convert HTML text to SVG-compatible text using tspan for subscripts/superscripts.

    Parameters
    ----------
    text:
        The input HTML text.
    baseline:
        The dominant baseline alignment for the text ('hanging', 'middle', 'baseline').

    Returns
    -------
    str
        The SVG-compatible text.
    """
    replacements = {
        "hanging": {
            "<sup>": '<tspan dy="-7%" font-size="70%">',
            "</sup>": "</tspan>",
            "<sub>": '<tspan dy="7%" font-size="70%">',
            "</sub>": "</tspan>",
        },
        "middle": {
            "<sup>": '<tspan dy="-2%" font-size="70%">',
            "</sup>": "</tspan>",
            "<sub>": '<tspan dy="2%" font-size="70%">',
            "</sub>": "</tspan>",
        },
    }

    for entity, replacement in replacements[baseline].items():
        text = text.replace(entity, replacement)

    return text
