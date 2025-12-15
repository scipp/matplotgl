# SPDX-License-Identifier: BSD-3-Clause

import matplotgl.pyplot as plt


def test_vspan():
    _, ax = plt.subplots()
    vs = ax.axvspan(10, 20, color='lime', alpha=0.5)
    ax.set_xlim(0, 50)
    ax.set_ylim(0, 10)

    assert vs.get_bbox() == {'left': 10, 'right': 20, 'bottom': None, 'top': None}


def test_hspan():
    _, ax = plt.subplots()
    hs = ax.axhspan(5, 15, color='orange', alpha=0.5)
    ax.set_xlim(0, 50)
    ax.set_ylim(0, 20)

    assert hs.get_bbox() == {'left': None, 'right': None, 'bottom': 5, 'top': 15}
