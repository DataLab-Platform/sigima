# Copyright (c) DataLab Platform Developers, BSD 3-Clause license, see LICENSE file.

"""
Filtering computation module
----------------------------

This module provides spatial and frequency-based filtering operations for images.

Main features include:
- Gaussian, median, moving average, Wiener, and Butterworth filters
- Noise reduction and image smoothing

Filtering functions are essential for enhancing image quality
and removing noise prior to further analysis.
"""

# pylint: disable=invalid-name  # Allows short reference names like x, y, ...

# Note:
# ----
# - All `guidata.dataset.DataSet` parameter classes must also be imported
#   in the `sigima.params` module.
# - All functions decorated by `computation_function` must be imported in the upper
#   level `sigima.proc.image` module.

from __future__ import annotations

import guidata.dataset as gds
import scipy.ndimage as spi
import scipy.signal as sps
from skimage import filters

from sigima.config import _
from sigima.objects.image import ImageObj
from sigima.proc import computation_function
from sigima.proc.base import (
    GaussianParam,
    MovingAverageParam,
    MovingMedianParam,
    dst_1_to_1,
)
from sigima.proc.image.base import Wrap1to1Func, restore_data_outside_roi
from sigima.tools.image import freq_fft_filter


@computation_function()
def gaussian_filter(src: ImageObj, p: GaussianParam) -> ImageObj:
    """Compute gaussian filter with :py:func:`scipy.ndimage.gaussian_filter`

    Args:
        src: input image object
        p: parameters

    Returns:
        Output image object
    """
    return Wrap1to1Func(spi.gaussian_filter, sigma=p.sigma)(src)


@computation_function()
def moving_average(src: ImageObj, p: MovingAverageParam) -> ImageObj:
    """Compute moving average with :py:func:`scipy.ndimage.uniform_filter`

    Args:
        src: input image object
        p: parameters

    Returns:
        Output image object
    """
    return Wrap1to1Func(spi.uniform_filter, size=p.n, mode=p.mode)(src)


@computation_function()
def moving_median(src: ImageObj, p: MovingMedianParam) -> ImageObj:
    """Compute moving median with :py:func:`scipy.ndimage.median_filter`

    Args:
        src: input image object
        p: parameters

    Returns:
        Output image object
    """
    return Wrap1to1Func(spi.median_filter, size=p.n, mode=p.mode)(src)


@computation_function()
def wiener(src: ImageObj) -> ImageObj:
    """Compute Wiener filter with :py:func:`scipy.signal.wiener`

    Args:
        src: input image object

    Returns:
        Output image object
    """
    return Wrap1to1Func(sps.wiener)(src)


class ButterworthParam(gds.DataSet):
    """Butterworth filter parameters"""

    cut_off = gds.FloatItem(
        _("Cut-off frequency ratio"),
        default=0.005,
        min=0.0,
        max=0.5,
        help=_("Cut-off frequency ratio"),
    )
    high_pass = gds.BoolItem(
        _("High-pass filter"),
        default=False,
        help=_("If True, apply high-pass filter instead of low-pass"),
    )
    order = gds.IntItem(
        _("Order"),
        default=2,
        min=1,
        help=_("Order of the Butterworth filter"),
    )


@computation_function()
def butterworth(src: ImageObj, p: ButterworthParam) -> ImageObj:
    """Compute Butterworth filter with :py:func:`skimage.filters.butterworth`

    Args:
        src: input image object
        p: parameters

    Returns:
        Output image object
    """
    dst = dst_1_to_1(
        src,
        "butterworth",
        f"cut_off={p.cut_off:.3f}, order={p.order}, high_pass={p.high_pass}",
    )
    dst.data = filters.butterworth(src.data, p.cut_off, p.high_pass, p.order)
    restore_data_outside_roi(dst, src)
    return dst


class FreqFFTParam(gds.DataSet):
    """2D Gaussian bandpass FFT filter parameters"""

    f0 = gds.FloatItem(
        _("Center frequency"),
        default=1,
        unit="pixels⁻¹",
        min=0.0,
        help=_("Center frequency of the Gaussian filter"),
    )
    sigma = gds.FloatItem(
        _("σ"),
        default=0.5,
        unit="pixels⁻¹",
        min=0.0,
        help=_("Standard deviation of the Gaussian filter"),
    )
    ifft_result_type = gds.ChoiceItem(
        _("IFFT result type"),
        (("real", _("Real part")), ("abs", _("Absolute value"))),
        default="real",
        help=_("How to return the inverse FFT result"),
    )


@computation_function()
def freq_fft(src: ImageObj, p: FreqFFTParam) -> ImageObj:
    """Apply a 2D Gaussian bandpass filter in the frequency domain to an image.

    Args:
        src: input image object
        p: parameters

    Returns:
        Output image object
    """
    dst = dst_1_to_1(
        src,
        "freq_fft",
        f"f0={p.f0:.3f}, sigma={p.sigma:.3f}, type={p.ifft_result_type}",
    )
    dst.data = freq_fft_filter(src.data, p.f0, p.sigma, p.ifft_result_type)
    restore_data_outside_roi(dst, src)
    return dst
