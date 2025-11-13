# SPDX-License-Identifier: BSD-3-Clause

import numpy as np

import matplotgl.pyplot as plt


def test_pcolormesh_z_only():
    _, ax = plt.subplots()

    m = ax.pcolormesh(np.random.random((20, 30)))

    assert len(ax.collections) == 1
    assert m._c.shape == (20, 30)


def test_pcolormesh_with_colorbar():
    fig, ax = plt.subplots()

    m = ax.pcolormesh(np.random.random((20, 30)))
    cb = fig.colorbar(m)

    assert cb._mappable is m


def test_pcolormesh_1d_coords_edges():
    _, ax = plt.subplots()

    M, N = 80, 100
    xx = np.linspace(1.0, 5.0, N + 1)
    yy = np.linspace(1.0, 5.0, M + 1)
    x, y = np.meshgrid(xx[:-1], yy[:-1])
    z = 1.0 - (np.sin(x) ** 10 + np.cos(10 + y * x) * np.cos(x))

    m = ax.pcolormesh(xx, yy, z)

    assert len(ax.collections) == 1
    assert m._c.shape == (M, N)


def test_pcolormesh_1d_coords_square():
    _, ax = plt.subplots()

    N = 100
    xx = np.linspace(1.0, 5.0, N)
    yy = np.linspace(1.0, 5.0, N)
    x, y = np.meshgrid(xx, yy)
    z = 1.0 - (np.sin(x) ** 10 + np.cos(10 + y * x) * np.cos(x))

    m = ax.pcolormesh(xx, yy, z)

    assert len(ax.collections) == 1
    assert m._c.shape == (N, N)


def test_pcolormesh_1d_coords_midpoints():
    _, ax = plt.subplots()

    M, N = 80, 100
    xx = np.linspace(1.0, 5.0, N)
    yy = np.linspace(1.0, 5.0, M)
    x, y = np.meshgrid(xx, yy)
    z = 1.0 - (np.sin(x) ** 10 + np.cos(10 + y * x) * np.cos(x))

    m = ax.pcolormesh(xx, yy, z)

    assert len(ax.collections) == 1
    assert m._c.shape == (M, N)


def test_pcolormesh_2d_coords_edges():
    _, ax = plt.subplots()

    M, N = 80, 100
    xx = np.linspace(1.0, 5.0, N + 1)
    yy = np.linspace(1.0, 5.0, M + 1)
    x, y = np.meshgrid(xx, yy)
    z = 1.0 - (
        np.sin(x[:-1, :-1]) ** 10
        + np.cos(10 + y[:-1, :-1] * x[:-1, :-1]) * np.cos(x[:-1, :-1])
    )

    m = ax.pcolormesh(x, y, z)

    assert len(ax.collections) == 1
    assert m._c.shape == (M, N)


def test_pcolormesh_2d_coords_midpoints():
    _, ax = plt.subplots()

    M, N = 80, 100
    xx = np.linspace(1.0, 5.0, N)
    yy = np.linspace(1.0, 5.0, M)
    x, y = np.meshgrid(xx, yy)
    z = 1.0 - (np.sin(x) ** 10 + np.cos(10 + y * x) * np.cos(x))

    m = ax.pcolormesh(x, y, z)

    assert len(ax.collections) == 1
    assert m._c.shape == (M, N)
