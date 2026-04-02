from sentinelsat import SentinelAPI
from shapely.geometry import box
import pandas as pd

class CopernicusAPI:
    def __init__(self, username, password):
        self.api = SentinelAPI(username, password, 'https://apihub.copernicus.eu/apihub')
        
    def search_products(self, bbox, date_range, cloud_cover=30, product_type='S2MSI2A'):
        lon_min, lat_min, lon_max, lat_max = bbox
        footprint = box(lon_min, lat_min, lon_max, lat_max)
        
        products = self.api.query(
            area=footprint.wkt,
            date=date_range,
            platformname='Sentinel-2',
            producttype=product_type,
            cloudcoverpercentage=(0, cloud_cover)
        )
        
        return self.api.to_dataframe(products)
    
    def download_product(self, product_id, output_dir):
        return self.api.download(product_id, directory_path=output_dir)
