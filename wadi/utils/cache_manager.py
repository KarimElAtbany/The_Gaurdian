import json
import hashlib
from pathlib import Path
from datetime import datetime


class CacheManager:
    def __init__(self, cache_dir):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.cache_dir / "cache_index.json"
        self.index = self._load_index()

    def _load_index(self):
        if self.index_file.exists():
            with open(self.index_file) as f:
                return json.load(f)
        return {}

    def _save_index(self):
        with open(self.index_file, 'w') as f:
            json.dump(self.index, f, indent=2)

    def _get_cache_key(self, product_id, band):
        return hashlib.md5(f"{product_id}_{band}".encode()).hexdigest()

    def get_cached_band(self, product_id, band):
        key = self._get_cache_key(product_id, band)
        if key in self.index:
            path = Path(self.index[key]['path'])
            if path.exists():
                return path
        return None

    def cache_band(self, product_id, band, file_path):
        key = self._get_cache_key(product_id, band)
        suffix = Path(file_path).suffix or '.tif'
        cache_path = self.cache_dir / f"{product_id}_{band}{suffix}"

        src = Path(file_path)
        if src.exists() and src != cache_path:
            import shutil
            shutil.copy2(src, cache_path)

        self.index[key] = {
            'product_id': product_id,
            'band': band,
            'path': str(cache_path),
            'cached_at': datetime.now().isoformat()
        }
        self._save_index()
        return cache_path

    def get_all_bands(self, product_id):
        required = ['B02', 'B03', 'B04', 'B05', 'B07', 'B08', 'B8A', 'B11']
        bands = {}
        for band in required:
            cached = self.get_cached_band(product_id, band)
            if cached:
                bands[band] = cached
        return bands if bands else None

    def list_products(self):
        products = set()
        for data in self.index.values():
            products.add(data['product_id'])
        return list(products)

    def clear_cache(self):
        for data in self.index.values():
            path = Path(data['path'])
            if path.exists():
                path.unlink()
        self.index = {}
        self._save_index()
