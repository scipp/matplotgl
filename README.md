[![Contributor Covenant](https://img.shields.io/badge/Contributor%20Covenant-2.1-4baaaa.svg)](CODE_OF_CONDUCT.md)
[![PyPI badge](http://img.shields.io/pypi/v/matplotgl.svg)](https://pypi.python.org/pypi/matplotgl)
[![Anaconda-Server Badge](https://anaconda.org/conda-forge/matplotgl/badges/version.svg)](https://anaconda.org/conda-forge/matplotgl)
[![License: BSD 3-Clause](https://img.shields.io/badge/License-BSD%203--Clause-blue.svg)](LICENSE)

# Matplotgl

## About

Matplotlib clone for Jupyter that uses WebGL via Pythreejs.

The goal of this project is to provide a matplotlib-like interface for interactive
plotting in Jupyter notebooks using WebGL for rendering. This allows for
efficient handling of large datasets and smooth interactivity.

It tries to follow the matplotlib API as closely as possible, but will never be a
complete replacement. Instead, it focuses on the most commonly used features
and provides a familiar interface for users who are already comfortable with
matplotlib.

Because of the use of Pythreejs, Matplotgl will be able to support native 3D plotting
out of the box.

## Installation

```sh
python -m pip install matplotgl
```
