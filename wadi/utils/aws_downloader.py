import boto3
import botocore.config
from botocore import UNSIGNED
import requests
import rasterio
from rasterio.mask import mask
from shapely.geometry import shape, box
import geopandas as gpd
from pathlib import Path

class STACDownloader:
    def __init__(self):
        self.stac_api = "https://earth-search.aws.element84.com/v1"
        self.s3 = boto3.client(
            "s3",
            region_name="us-west-2",
            config=botocore.config.Config(signature_version=UNSIGNED)
        )

    def search_items(self, geometry, start_date, end_date, collection="sentinel-2-l2a", limit=10, max_cloud=30):
        query = {
            "collections": [collection],
            "datetime": f"{start_date}/{end_date}",
            "limit": limit,
            "intersects": geometry,
            "query": {"eo:cloud_cover": {"lte": max_cloud}}
        }

        resp = requests.post(
            f"{self.stac_api}/search",
            json=query,
            headers={"Content-Type": "application/json"}
        )
        resp.raise_for_status()
        return resp.json().get("features", [])

    def download_asset(self, item, asset_key, output_path):
        assets = item.get("assets", {})
        if asset_key not in assets:
            raise ValueError(f"Asset {asset_key} not available")

        url = assets[asset_key]["href"]

        if url.startswith("s3://"):
            bucket, key = url.replace("s3://", "").split("/", 1)
            self.s3.download_file(bucket, key, str(output_path))
        else:
            r = requests.get(url, stream=True)
            r.raise_for_status()
            with open(output_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

        return output_path

    def download_bands(self, item, output_dir, bands=None):
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        if bands is None:
            bands = ['blue', 'green', 'red', 'nir', 'rededge1', 'rededge3', 'nir08', 'swir16']

        band_mapping = {
            'blue':      'B02',
            'green':     'B03',
            'red':       'B04',
            'rededge1':  'B05',
            'rededge2':  'B06',
            'rededge3':  'B07',
            'nir':       'B08',
            'nir08':     'B8A',
            'swir16':    'B11',
            'swir22':    'B12',
        }

        downloaded = {}
        for asset_key in bands:
            band_name = band_mapping.get(asset_key, asset_key)
            output_path = output_dir / f"{band_name}.tif"

            try:
                self.download_asset(item, asset_key, output_path)
                downloaded[band_name] = output_path
            except Exception as e:
                print(f"Failed to download {asset_key}: {e}")

        return downloaded

    def download_tci(self, item, output_path):
        try:
            return self.download_asset(item, "visual", output_path)
        except:
            return self.download_asset(item, "true_color", output_path)

    def crop_to_polygon(self, tif_file, output_file, polygon):
        with rasterio.open(tif_file) as src:
            gdf = gpd.GeoDataFrame(geometry=[shape(polygon)], crs="EPSG:4326")
            gdf = gdf.to_crs(src.crs)
            poly_proj = gdf.geometry.values[0]

            raster_bounds = box(*src.bounds)
            if not raster_bounds.intersects(poly_proj):
                return None

            out_image, out_transform = mask(src, gdf.geometry, crop=True)
            out_meta = src.meta.copy()
            out_meta.update({
                "driver": "GTiff",
                "height": out_image.shape[1],
                "width": out_image.shape[2],
                "transform": out_transform,
                "crs": src.crs
            })

            with rasterio.open(output_file, "w", **out_meta) as dest:
                dest.write(out_image)

        return output_file
