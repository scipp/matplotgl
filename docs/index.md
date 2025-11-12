:::{image} _static/logo.svg
:class: only-light
:alt: Matplotgl
:width: 60%
:align: center
:::
:::{image} _static/logo-dark.svg
:class: only-dark
:alt: Matplotgl
:width: 60%
:align: center
:::

```{raw} html
   <style>
    .transparent {display: none; visibility: hidden;}
    .transparent + a.headerlink {display: none; visibility: hidden;}
   </style>
```

```{role} transparent
```

# {transparent}`Matplotgl`

<div style="font-size:1.2em;font-style:italic;color:var(--pst-color-text-muted);text-align:center;">
  Matplotlib clone for Jupyter that uses WebGL via Pythreejs
  </br></br>
</div>

The goal of this project is to provide a matplotlib-like interface for interactive plotting in Jupyter notebooks using WebGL for rendering. This allows for efficient handling of large datasets and smooth interactivity.

It tries to follow the matplotlib API as closely as possible, but will never be a complete replacement. Instead, it focuses on the most commonly used features and provides a familiar interface for users who are already comfortable with matplotlib.

Because of the use of Pythreejs, Matplotgl will be able to support native 3D plotting out of the box.

:::{include} user-guide/installation.md
:heading-offset: 1
:::

## Get in touch

- If you have questions that are not answered by these documentation pages, ask on [discussions](https://github.com/scipp/matplotgl/discussions). Please include a self-contained reproducible example if possible.
- Report bugs (including unclear, missing, or wrong documentation!), suggest features or view the source code [on GitHub](https://github.com/scipp/matplotgl).

```{toctree}
---
hidden:
---

user-guide/index
api-reference/index
developer/index
about/index
```
