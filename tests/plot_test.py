# SPDX-License-Identifier: BSD-3-Clause

import numpy as np

import matplotgl.pyplot as plt


def test_plot_one_line():
    fig, ax = plt.subplots()
    points_per_line = 100
    x = np.linspace(0, 10, points_per_line)
    y = np.sin(x) * np.exp(-x / 5) + np.random.uniform(-0.1, 0.1, size=points_per_line)
    ax.plot(x, y)

    assert len(fig.axes) == 1
    assert len(ax.lines) == 1
    lines = ax.lines[0]
    assert np.allclose(lines.get_xdata(), x)
    assert np.allclose(lines.get_ydata(), y)


def test_plot_multiple_lines():
    fig, ax = plt.subplots()
    points_per_line = 100
    x = np.linspace(0, 10, points_per_line)
    y = []
    for i in range(4):
        y.append(
            np.sin(x + i) * np.exp(-x / 5)
            + np.random.uniform(-0.1, 0.1, size=points_per_line)
        )
        ax.plot(x, y[i])

    assert len(fig.axes) == 1
    assert len(ax.lines) == 4
    for i, line in enumerate(ax.lines):
        assert np.allclose(line.get_xdata(), x)
        assert np.allclose(line.get_ydata(), y[i])


def test_scatter():
    fig, ax = plt.subplots()
    x, y = np.random.normal(size=(2, 1000))
    ax.scatter(x, y)

    assert len(fig.axes) == 1
    assert len(ax.collections) == 1
    scatter = ax.collections[0]
    assert np.allclose(scatter.get_xdata(), x)
    assert np.allclose(scatter.get_ydata(), y)


def test_imshow():
    fig, ax = plt.subplots()
    data = np.random.rand(200, 300)
    ax.imshow(data, cmap='viridis', extent=[0, 10, 0, 5])

    assert len(fig.axes) == 1
    assert len(ax.images) == 1
    im = ax.images[0]
    assert np.allclose(im._array, data)
    assert im.get_extent() == [0, 10, 0, 5]
