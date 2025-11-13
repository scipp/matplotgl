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


def test_pcolormesh_1d_set_xdata():
    _, ax = plt.subplots()

    M, N = 80, 100
    xx = np.linspace(1.0, 5.0, N + 1)
    yy = np.linspace(1.0, 5.0, M + 1)
    x, y = np.meshgrid(xx[:-1], yy[:-1])
    z = 1.0 - (np.sin(x) ** 10 + np.cos(10 + y * x) * np.cos(x))

    m = ax.pcolormesh(xx, yy, z)

    new_xx = np.linspace(2.0, 6.0, N + 1)
    m.set_xdata(new_xx)

    bbox = m.get_bbox()
    assert bbox["left"] == new_xx[0]
    assert bbox["right"] == new_xx[-1]


def test_pcolormesh_1d_set_ydata():
    _, ax = plt.subplots()

    M, N = 80, 100
    xx = np.linspace(1.0, 5.0, N + 1)
    yy = np.linspace(1.0, 5.0, M + 1)
    x, y = np.meshgrid(xx[:-1], yy[:-1])
    z = 1.0 - (np.sin(x) ** 10 + np.cos(10 + y * x) * np.cos(x))

    m = ax.pcolormesh(xx, yy, z)

    new_yy = np.linspace(3.0, 7.0, M + 1)
    m.set_ydata(new_yy)

    bbox = m.get_bbox()
    assert bbox["bottom"] == new_yy[0]
    assert bbox["top"] == new_yy[-1]


def test_pcolormesh_2d_set_xdata():
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

    new_x = x + 3.0
    m.set_xdata(new_x)

    bbox = m.get_bbox()
    assert bbox["left"] == new_x[0, 0]
    assert bbox["right"] == new_x[0, -1]


def test_pcolormesh_2d_set_ydata():
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

    new_y = y + 4.0
    m.set_ydata(new_y)

    bbox = m.get_bbox()
    assert bbox["bottom"] == new_y[0, 0]
    assert bbox["top"] == new_y[-1, 0]
