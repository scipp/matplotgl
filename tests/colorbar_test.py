# SPDX-License-Identifier: BSD-3-Clause

import matplotlib.colors as cm
import numpy as np

import matplotgl.pyplot as plt


def test_colorbar_imshow():
    fig, ax = plt.subplots()

    a = np.random.random((20, 20)) * 5.0
    im = ax.imshow(a)
    cb = fig.colorbar(im)

    assert cb._mappable is im
    assert im._colorbar is not None
    assert isinstance(im.norm._norm, cm.Normalize)
    assert im.norm.vmin == a.min()
    assert im.norm.vmax == a.max()


def test_colorbar_imshow_log():
    fig, ax = plt.subplots()

    a = np.random.random((20, 20)) * 100.0 + 1.0
    im = ax.imshow(a, norm='log')
    cb = fig.colorbar(im)

    assert cb._mappable is im
    assert im._colorbar is not None
    assert isinstance(im.norm._norm, cm.LogNorm)
    assert im.norm.vmin == a.min()
    assert im.norm.vmax == a.max()


def test_imshow_set_cmap():
    fig, ax = plt.subplots()

    a = np.random.random((20, 20)) * 5.0
    im = ax.imshow(a)
    fig.colorbar(im)

    im.set_cmap('plasma')
    im.cmap = 'magma'


def test_imshow_set_norm():
    fig, ax = plt.subplots()

    a = np.random.random((20, 20)) * 100.0 + 1.0
    im = ax.imshow(a, norm='linear')
    fig.colorbar(im)

    im.norm = 'log'
    assert isinstance(im.norm._norm, cm.LogNorm)


def test_colorbar_pcolormesh():
    fig, ax = plt.subplots()

    a = np.random.random((20, 20)) * 5.0
    im = ax.pcolormesh(a)
    cb = fig.colorbar(im)

    assert cb._mappable is im
    assert im._colorbar is not None
    assert isinstance(im.norm._norm, cm.Normalize)
    assert im.norm.vmin == a.min()
    assert im.norm.vmax == a.max()


def test_colorbar_pcolormesh_log():
    fig, ax = plt.subplots()

    a = np.random.random((20, 20)) * 100.0 + 1.0
    im = ax.pcolormesh(a, norm='log')
    cb = fig.colorbar(im)

    assert cb._mappable is im
    assert im._colorbar is not None
    assert isinstance(im.norm._norm, cm.LogNorm)
    assert im.norm.vmin == a.min()
    assert im.norm.vmax == a.max()


def test_pcolormesh_set_cmap():
    fig, ax = plt.subplots()

    a = np.random.random((20, 20)) * 5.0
    im = ax.pcolormesh(a)
    fig.colorbar(im)

    im.set_cmap('plasma')
    im.cmap = 'magma'


def test_pcolormesh_set_norm():
    fig, ax = plt.subplots()

    a = np.random.random((20, 20)) * 100.0 + 1.0
    im = ax.pcolormesh(a, norm='linear')
    fig.colorbar(im)

    im.norm = 'log'
    assert isinstance(im.norm._norm, cm.LogNorm)


def test_colorbar_scatter():
    fig, ax = plt.subplots()

    x = np.random.random(100)
    y = np.random.random(100)
    c = np.random.random(100) * 5.0
    im = ax.scatter(x, y, c=c)
    cb = fig.colorbar(im)

    assert cb._mappable is im
    assert im._colorbar is not None
    assert isinstance(im.norm._norm, cm.Normalize)
    assert im.norm.vmin == c.min()
    assert im.norm.vmax == c.max()


def test_colorbar_scatter_log():
    fig, ax = plt.subplots()

    x = np.random.random(100)
    y = np.random.random(100)
    c = np.random.random(100) * 100.0 + 1.0
    im = ax.scatter(x, y, c=c, norm='log')
    cb = fig.colorbar(im)

    assert cb._mappable is im
    assert im._colorbar is not None
    assert isinstance(im.norm._norm, cm.LogNorm)
    assert im.norm.vmin == c.min()
    assert im.norm.vmax == c.max()


def test_scatter_set_cmap():
    fig, ax = plt.subplots()

    x = np.random.random(100)
    y = np.random.random(100)
    c = np.random.random(100) * 5.0
    im = ax.scatter(x, y, c=c)
    fig.colorbar(im)

    im.set_cmap('plasma')
    im.cmap = 'magma'


def test_scatter_set_norm():
    fig, ax = plt.subplots()

    x = np.random.random(100)
    y = np.random.random(100)
    c = np.random.random(100) * 100.0 + 1.0
    im = ax.scatter(x, y, c=c, norm='linear')
    fig.colorbar(im)

    im.norm = 'log'
    assert isinstance(im.norm._norm, cm.LogNorm)
