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
        cache_path = self.cache_dir / f"{product_id}_{band}.jp2"
        
        if Path(file_path).exists():
            Path(file_path).rename(cache_path)
        
        self.index[key] = {
            'product_id': product_id,
            'band': band,
            'path': str(cache_path),
            'cached_at': datetime.now().isoformat()
        }
        self._save_index()
        return cache_path
    
    def get_all_bands(self, product_id):
        bands = {}
        for band in ['B02', 'B03', 'B04', 'B08']:
            cached = self.get_cached_band(product_id, band)
            if cached:
                bands[band] = cached
        return bands if len(bands) == 4 else None
    
    def clear_cache(self):
        for key, data in self.index.items():
            path = Path(data['path'])
            if path.exists():
                path.unlink()
        self.index = {}
        self._save_index()
