# SPDX-License-Identifier: BSD-3-Clause

import numpy as np
import pytest

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


def test_set_xscale_log():
    _, ax = plt.subplots()
    x = np.arange(50.0)
    y = np.sin(0.2 * x)

    ax.plot(x, y, lw=2)
    ax.set_xscale('log')

    assert ax.get_xscale() == 'log'


def test_set_yscale_log():
    _, ax = plt.subplots()
    x = np.arange(50.0)
    y = np.sin(0.2 * x)

    ax.plot(x, y, lw=2)
    ax.set_yscale('log')

    assert ax.get_yscale() == 'log'


def test_set_xscale_invalid():
    _, ax = plt.subplots()
    with pytest.raises(ValueError, match="Scale must be 'linear' or 'log'"):
        ax.set_xscale('invalid_scale')


def test_set_yscale_invalid():
    _, ax = plt.subplots()
    with pytest.raises(ValueError, match="Scale must be 'linear' or 'log'"):
        ax.set_yscale('invalid_scale')


def test_set_xscale_log_before_plot():
    _, ax = plt.subplots()
    x = np.arange(50.0)
    y = np.sin(0.2 * x)

    ax.set_xscale('log')
    ax.plot(x, y, lw=2)

    assert ax.get_xscale() == 'log'


def test_set_yscale_log_before_plot():
    _, ax = plt.subplots()
    x = np.arange(50.0)
    y = np.sin(0.2 * x)

    ax.set_yscale('log')
    ax.plot(x, y, lw=2)

    assert ax.get_yscale() == 'log'


def test_semilogx():
    _, ax = plt.subplots()
    x = np.arange(1.0, 50.0)
    y = np.sin(0.2 * x)

    ax.semilogx(x, y, lw=2)

    assert ax.get_xscale() == 'log'


def test_semilogy():
    _, ax = plt.subplots()
    x = np.arange(50.0)
    y = np.exp(0.1 * x)

    ax.semilogy(x, y, lw=2)

    assert ax.get_yscale() == 'log'


def test_loglog():
    _, ax = plt.subplots()
    x = np.arange(1.0, 50.0)
    y = np.exp(0.1 * x)

    ax.loglog(x, y, lw=2)

    assert ax.get_xscale() == 'log'
    assert ax.get_yscale() == 'log'
