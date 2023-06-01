import glob
from collections import UserDict
from pathlib import Path
from typing import Tuple

import numpy.typing as npt
import rasterio
from rasterio.enums import Resampling
from rasterio.mask import mask
from rasterio.merge import merge
from shapely.geometry import Polygon


def compute_raster_mosaic(
    glob_pattern: str,
    nodata: float,
    output_path: str,
    resampling: int = Resampling.nearest,
) -> None:
    """Compute a raster mosaic from a list of file names."""

    raster_path_list = glob.glob(glob_pattern)

    raster_mosaic_array, mosaic_transform = merge(
        datasets=raster_path_list,
        nodata=nodata,
        resampling=resampling,
    )

    with rasterio.open(raster_path_list[0], "r") as src:
        profile = src.profile.copy()

    profile.update(
        {
            "height": raster_mosaic_array.shape[1],
            "width": raster_mosaic_array.shape[2],
            "transform": mosaic_transform,
            "tiled": True,
            "nodata": nodata,
        }
    )

    save_geotiff(output_path, raster_mosaic_array[0], profile)


def crop_raster(file_path: str, shape: Polygon, output_path: str) -> None:
    with rasterio.open(file_path, "r") as src:
        profile = src.profile
        cropped_raster_array, cropped_raster_transform = mask(src, shapes=[shape], crop=True)

    profile.update(
        {
            "height": cropped_raster_array.shape[1],
            "width": cropped_raster_array.shape[2],
            "transform": cropped_raster_transform,
        }
    )

    save_geotiff(output_path, cropped_raster_array[0], profile)


def save_geotiff(file_path: str, array: npt.NDArray, profile: UserDict) -> None:
    """Save classic Geotiff"""
    with rasterio.open(file_path, "w", **profile) as dst:
        dst.write(array, 1)


def read_geotiff_with_profile(file_path: str) -> Tuple[npt.NDArray, UserDict]:
    if Path(file_path).exists():
        with rasterio.open(file_path, "r") as src:
            array = src.read(src)
            profile = src.profile
        return array, profile
    else:
        raise ValueError(f"Specified file does not exist at: {file_path}")
