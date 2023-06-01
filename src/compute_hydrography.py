from collections import UserDict
from typing import List, Tuple

import click
import pyflwdir

from .shared.rasterio_utils import read_geotiff_with_profile, save_geotiff

BASINS_OUTLETS = {
    "Ardeche": (44.26478, 4.64837),
    "Escoutay": (44.48831, 4.68929),
    "Eyrieux": (44.80751, 4.80076),
    "Doux": (45.07328, 4.8271),
    "Ay": (45.19066, 4.80338),
    "Cance": (45.20411, 4.80766),
    "Loire": (45.26081, 4.14248),  # Upstream part only
}


def get_basin_outlet_coordinates() -> Tuple[List[float], List[float]]:
    """Get the basins outlet coordinates (lat/lon).

    This function converts the basins outlet dict to a format that can be read by pyflwdir.
    """
    x = [coord[1] for coord in BASINS_OUTLETS.values()]
    y = [coord[0] for coord in BASINS_OUTLETS.values()]
    return x, y


def compute_and_save_stream_order(
    fdir_object: pyflwdir.FlwdirRaster,
    output_file_path: str,
    profile: UserDict,
) -> None:
    stream_order = fdir_object.stream_order(type="strahler")
    save_geotiff(output_file_path, stream_order, profile)


def compute_and_save_basins(
    fdir_object: pyflwdir.FlwdirRaster, output_file_path: str, profile: UserDict, nodata: int = 247
) -> None:
    x, y = get_basin_outlet_coordinates()

    basins = fdir_object.basins(xy=(x, y))
    basins[basins == 0] = nodata

    save_geotiff(output_file_path, basins, profile)


def compute_hydrography(fdir_raster_path: str) -> None:
    fdir_array, profile = read_geotiff_with_profile(fdir_raster_path)

    fdir_object = pyflwdir.from_array(
        fdir_array, ftype="d8", transform=profile["transform"], latlon=True, cache=True
    )

    compute_and_save_stream_order(fdir_object=fdir_object, output_file_path="", profile=profile)
    compute_and_save_basins(fdir_object=fdir_object, output_file_path="", profile=profile)


@click.command()
@click.option("--fdir_raster_path", help="path to the flow direction raster")
def run(fdir_raster_path: str) -> None:
    """Run the compute hydroagraphy script."""
    compute_hydrography(fdir_raster_path=fdir_raster_path)


if __name__ == "__main__":
    run()
