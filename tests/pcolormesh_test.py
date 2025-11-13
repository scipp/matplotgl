# SPDX-License-Identifier: BSD-3-Clause

import numpy as np
import pytest

import matplotgl.pyplot as plt


def test_pcolormesh_z_only():
    fig, ax = plt.subplots()

    m = ax.pcolormesh(np.random.random(20, 30))

    assert len(ax.collections) == 1
    assert m._c.shape == (20, 30)


def test_pcolormesh_1d_coords_edges():
    fig, ax = plt.subplots()

    N = 100
    xx = np.linspace(1.0, 5.0, N + 1)
    yy = np.linspace(1.0, 5.0, N + 1)
    x, y = np.meshgrid(xx[:-1], yy[:-1])
    z = 1.0 - (np.sin(x) ** 10 + np.cos(10 + y * x) * np.cos(x))

    m = ax.pcolormesh(xx, yy, z)
    # m = ax.pcolormesh(z)
    cb = fig.colorbar(m)

    fig


# fig, ax = plt.subplots()

# N = 100
# xx = np.linspace(1.0, 5.0, N)
# yy = np.linspace(1.0, 5.0, N)
# x, y = np.meshgrid(xx, yy)
# z = 1.0 - (np.sin(x) ** 10 + np.cos(10 + y * x) * np.cos(x))

# m = ax.pcolormesh(xx, yy, z)
# # m = ax.pcolormesh(z)
# cb = fig.colorbar(m)

# fig


# fig, ax = plt.subplots()

# N = 100
# xx = np.linspace(1.0, 5.0, N+1)
# yy = np.linspace(1.0, 5.0, N+1)
# x, y = np.meshgrid(xx, yy)
# z = 1.0 - (np.sin(x[:-1, :-1]) ** 10 + np.cos(10 + y[:-1, :-1] * x[:-1, :-1]) * np.cos(x[:-1, :-1]))

# # m = ax.pcolormesh(xx, yy, z)
# m = ax.pcolormesh(x, y, z)
# cb = fig.colorbar(m)

# fig


# fig, ax = plt.subplots()

# N = 100
# xx = np.linspace(1.0, 5.0, N)
# yy = np.linspace(1.0, 5.0, N)
# x, y = np.meshgrid(xx, yy)
# z = 1.0 - (np.sin(x) ** 10 + np.cos(10 + y * x) * np.cos(x))

# # m = ax.pcolormesh(xx, yy, z)
# m = ax.pcolormesh(x, y, z)
# cb = fig.colorbar(m)

# fig
