# Copyright (c) DataLab Platform Developers, BSD 3-Clause license, see LICENSE file.

"""
Sigima I/O image formats
"""

from __future__ import annotations

import os.path as osp

import imageio.v3 as iio
import numpy as np
import pandas as pd
import scipy.io as sio
import skimage.io

from sigima.config import _, options
from sigima.io import ftlab
from sigima.io.base import FormatInfo
from sigima.io.common.converters import convert_array_to_standard_type
from sigima.io.image import funcs
from sigima.io.image.base import ImageFormatBase, MultipleImagesFormatBase
from sigima.objects.image import ImageObj
from sigima.worker import CallbackWorkerProtocol


class ClassicsImageFormat(ImageFormatBase):
    """Object representing classic image file types"""

    FORMAT_INFO = FormatInfo(
        name="BMP, JPEG, PNG, TIFF, JPEG2000",
        extensions="*.bmp *.jpg *.jpeg *.png *.tif *.tiff *.jp2",
        readable=True,
        writeable=True,
    )

    @staticmethod
    def read_data(filename: str) -> np.ndarray:
        """Read data and return it

        Args:
            filename: File name

        Returns:
            Image array data
        """
        return skimage.io.imread(filename, as_gray=True)

    @staticmethod
    def write_data(filename: str, data: np.ndarray) -> None:
        """Write data to file

        Args:
            filename: File name
            data: Image array data
        """
        ext = osp.splitext(filename)[1].lower()
        if ext in (".bmp", ".jpg", ".jpeg", ".png"):
            if data.dtype is not np.uint8:
                data = data.astype(np.uint8)
        if ext in (".jp2",):
            if data.dtype not in (np.uint8, np.uint16):
                data = data.astype(np.uint16)
        skimage.io.imsave(filename, data, check_contrast=False)


class NumPyImageFormat(ImageFormatBase):
    """Object representing NumPy image file type"""

    FORMAT_INFO = FormatInfo(
        name="NumPy",
        extensions="*.npy",
        readable=True,
        writeable=True,
    )  # pylint: disable=duplicate-code

    @staticmethod
    def read_data(filename: str) -> np.ndarray:
        """Read data and return it

        Args:
            filename: File name

        Returns:
            Image array data
        """
        return convert_array_to_standard_type(np.load(filename))

    @staticmethod
    def write_data(filename: str, data: np.ndarray) -> None:
        """Write data to file

        Args:
            filename: File name
            data: Image array data
        """
        np.save(filename, data)


class TextImageFormat(ImageFormatBase):
    """Object representing text image file type"""

    FORMAT_INFO = FormatInfo(
        name=_("Text files"),
        extensions="*.txt *.csv *.asc",
        readable=True,
        writeable=True,
    )

    @staticmethod
    def read_data(filename: str) -> np.ndarray:
        """Read data and return it

        Args:
            filename: File name

        Returns:
            Image array data
        """
        for encoding in ("utf-8", "utf-8-sig", "latin-1"):
            for decimal in (".", ","):
                for delimiter in (",", ";", r"\s+"):
                    try:
                        df = pd.read_csv(
                            filename,
                            decimal=decimal,
                            delimiter=delimiter,
                            encoding=encoding,
                            header=None,
                        )
                        # Handle the extra column created with trailing delimiters.
                        df = df.dropna(axis=1, how="all")
                        return df.to_numpy(np.float64)
                    except ValueError:
                        continue
        raise ValueError(f"Could not read image data from file {filename}.")

    @staticmethod
    def write_data(filename: str, data: np.ndarray) -> None:
        """Write data to file.

        Args:
            filename: File name.
            data: Image array data.
        """
        if np.issubdtype(data.dtype, np.integer):
            fmt = "%d"
        elif np.issubdtype(data.dtype, np.floating):
            fmt = "%.18e"
        else:
            raise NotImplementedError(
                f"Writing data of type {data.dtype} to text file is not supported."
            )
        ext = osp.splitext(filename)[1]
        if ext.lower() in (".txt", ".asc", ""):
            np.savetxt(filename, data, fmt=fmt)
        elif ext.lower() == ".csv":
            np.savetxt(filename, data, fmt=fmt, delimiter=",")
        else:
            raise ValueError(f"Unknown text file extension {ext}")


class MatImageFormat(ImageFormatBase):
    """Object representing MAT-File image file type"""

    FORMAT_INFO = FormatInfo(
        name=_("MAT-Files"),
        extensions="*.mat",
        readable=True,
        writeable=True,
    )  # pylint: disable=duplicate-code

    def read(
        self, filename: str, worker: CallbackWorkerProtocol | None = None
    ) -> list[ImageObj]:
        """Read list of image objects from file

        Args:
            filename: File name
            worker: Callback worker object

        Returns:
            List of image objects
        """
        mat = sio.loadmat(filename)
        allimg: list[ImageObj] = []
        for dname, data in mat.items():
            if dname.startswith("__") or not isinstance(data, np.ndarray):
                continue
            if len(data.shape) != 2:
                continue
            obj = self.create_object(filename)
            obj.data = data
            if dname != "img":
                obj.title += f" ({dname})"
            allimg.append(obj)
        return allimg

    @staticmethod
    def read_data(filename: str) -> np.ndarray:
        """Read data and return it

        Args:
            filename: File name

        Returns:
            Image array data
        """
        # This method is not used, as read() is overridden

    @staticmethod
    def write_data(filename: str, data: np.ndarray) -> None:
        """Write data to file

        Args:
            filename: File name
            data: Image array data
        """
        sio.savemat(filename, {"img": data})


class DICOMImageFormat(ImageFormatBase):
    """Object representing DICOM image file type"""

    FORMAT_INFO = FormatInfo(
        name="DICOM",
        extensions="*.dcm *.dicom",
        readable=True,
        writeable=False,
        requires=["pydicom"],
    )

    @staticmethod
    def read_data(filename: str) -> np.ndarray:
        """Read data and return it

        Args:
            filename: File name

        Returns:
            Image array data
        """
        return funcs.imread_dicom(filename)


class AndorSIFImageFormat(MultipleImagesFormatBase):
    """Object representing an Andor SIF image file type"""

    FORMAT_INFO = FormatInfo(
        name="Andor SIF",
        extensions="*.sif",
        readable=True,
        writeable=False,
    )

    @staticmethod
    def read_data(filename: str) -> np.ndarray:
        """Read data and return it

        Args:
            filename: File name

        Returns:
            Image array data
        """
        return funcs.imread_sif(filename)


# Generate classes based on the information above:
def generate_imageio_format_classes(
    imageio_formats: list[list[str, str]]
    | list[tuple[str, str]]
    | tuple[tuple[str, str]]
    | tuple[list[str, str]]
    | None = None,
) -> None:
    """Generate classes based on the information above"""
    if imageio_formats is None:
        imageio_formats = options.imageio_formats.get()

    for extensions, name in imageio_formats:
        class_dict = {
            "FORMAT_INFO": FormatInfo(
                name=name, extensions=extensions, readable=True, writeable=False
            ),
            "read_data": staticmethod(
                lambda filename: iio.imread(filename, index=None)
            ),
        }
        class_name = extensions.split()[0].split(".")[1].upper() + "ImageFormat"
        globals()[class_name] = type(
            class_name, (MultipleImagesFormatBase,), class_dict
        )


generate_imageio_format_classes()


class SpiriconImageFormat(ImageFormatBase):
    """Object representing Spiricon image file type"""

    FORMAT_INFO = FormatInfo(
        name="Spiricon",
        extensions="*.scor-data",
        readable=True,
        writeable=False,
    )

    @staticmethod
    def read_data(filename: str) -> np.ndarray:
        """Read data and return it

        Args:
            filename: File name

        Returns:
            Image array data
        """
        return funcs.imread_scor(filename)


class XYZImageFormat(ImageFormatBase):
    """Object representing Dürr NDT XYZ image file type"""

    FORMAT_INFO = FormatInfo(
        name="Dürr NDT",
        extensions="*.xyz",
        readable=True,
        writeable=False,
    )

    @staticmethod
    def read_data(filename: str) -> np.ndarray:
        """Read data and return it

        Args:
            filename: File name

        Returns:
            Image array data
        """
        with open(filename, "rb") as fdesc:
            cols = int(np.fromfile(fdesc, dtype=np.uint16, count=1)[0])
            rows = int(np.fromfile(fdesc, dtype=np.uint16, count=1)[0])
            arr = np.fromfile(fdesc, dtype=np.uint16, count=cols * rows)
            arr = arr.reshape((rows, cols))
        return np.fliplr(arr)


class FTLabImageFormat(ImageFormatBase):
    """FT-Lab image file."""

    FORMAT_INFO = FormatInfo(
        name="FT-Lab",
        extensions="*.ima",
        readable=True,
        writeable=False,
    )

    @staticmethod
    def read_data(filename: str) -> np.ndarray:
        """Read and return data.

        Args:
            filename: Path to FT-Lab file.

        Returns:
            Image data.
        """
        return ftlab.imread_ftlabima(filename)
