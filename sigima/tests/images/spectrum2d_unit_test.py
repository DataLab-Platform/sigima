# Copyright (c) DataLab Platform Developers, BSD 3-Clause license, see LICENSE file.

"""
Image spectrum unit test.
"""

# pylint: disable=invalid-name  # Allows short reference names like x, y, ...
# pylint: disable=duplicate-code

import pytest

import sigima.tools.image as alg
from sigima.tests.data import get_test_image


@pytest.mark.gui
def test_image_spectrum_interactive():
    """Interactive test of the magnitude/phase/power spectrum of an image."""
    # pylint: disable=import-outside-toplevel
    from guidata.qthelpers import qt_app_context

    from sigima.tests.vistools import view_images_side_by_side

    with qt_app_context():
        obj = get_test_image("NF 180338201.scor-data")
        data = obj.data
        ms = alg.magnitude_spectrum(data, log_scale=True)
        ps = alg.phase_spectrum(data)
        psd = alg.psd(data, log_scale=True)
        images = [data, ms, ps, psd]
        titles = [
            "Original",
            "Magnitude spectrum",
            "Phase spectrum",
            "Power spectral density",
        ]
        view_images_side_by_side(images, titles, rows=2, title="Image spectrum")


if __name__ == "__main__":
    test_image_spectrum_interactive()
