import logging
from typing import Tuple

import click
import geopandas as gpd
from shapely.geometry import Polygon

from .shared.rasterio_utils import compute_raster_mosaic, crop_raster

Bbox = Tuple[float, float, float, float]


def update_bbox_bounds(
    bbox: Bbox,
    bbox_delta: Bbox,
) -> Bbox:
    """Adapt the bbox bounds values by the chosen delta values."""
    return (
        bbox[0] + bbox_delta[0],
        bbox[1] + bbox_delta[1],
        bbox[2] + bbox_delta[2],
        bbox[3] + bbox_delta[3],
    )


def get_mask_shape(dpt_geojson_path: str, mask_on: str) -> Polygon:
    """Get the shape that will be used to mask the rasters.

    Two choices are available:
    - mask is based on the admin boundary feature.
    - mask is based on the bounding box of the admin boundary feature (rectangle polygon).
    """
    gdf_dpt = gpd.read_file(dpt_geojson_path)
    dpt_polygon = gdf_dpt["geometry"].values[0]
    if mask_on == "admin":
        return dpt_polygon
    elif mask_on == "bbox":
        # Define bounding box of the area of interest based on the bounds of the admin feature.
        bbox = update_bbox_bounds(dpt_polygon.bounds, (-0.23, -0.1, 0.1, 0.1))
        return Polygon(
            [
                [bbox[0], bbox[1]],
                [bbox[2], bbox[1]],
                [bbox[2], bbox[3]],
                [bbox[0], bbox[3]],
                [bbox[0], bbox[1]],
            ]
        )
    else:
        raise ValueError("mask_on value is not recognized! choose between: bbox or admin")


def process_rasters(folder: str, nodata: float, mask_shape: Polygon) -> None:
    compute_raster_mosaic(
        glob_pattern=f"../data/{folder}/raw/*.tif",
        nodata=nodata,
        output_path=f"../data/{folder}/mosaic.tif",
    )
    crop_raster(
        file_path=f"../data/{folder}/mosaic.tif",
        shape=mask_shape,
        output_path=f"../data/{folder}/ardeche_{folder}.tif",
    )


def prepare_input_data(dpt_geojson_path: str, mask_on: str = "bbox") -> None:
    logging.info("The input data preparation is starting ...")

    mask_shape = get_mask_shape(dpt_geojson_path, mask_on)
    logging.info("The polygon used to mask the rasters has been computed ...")

    # Process flow direction data
    process_rasters(folder="fdir", nodata=247, mask_shape=mask_shape)
    logging.info("The flow direction raster has been prepared ...")

    # Process elevation data
    process_rasters(folder="elv", nodata=-9999, mask_shape=mask_shape)
    logging.info("The elevation raster (DEM) has been prepared ...")


@click.command()
@click.option("--dpt_geojson_path", help="path to the geojson file containing the admin boundary")
@click.option("--mask_on", help="choose the object used to mask the rasters (bbox or admin)")
def run(dpt_geojson_path: str, mask_on: str) -> None:
    """Run the input data preparation script."""
    prepare_input_data(dpt_geojson_path=dpt_geojson_path, mask_on=mask_on)


if __name__ == "__main__":
    run()
