"""
Satellite imagery capture via Google satellite tile stitching.

Replaces the previous Selenium / headless-Chrome approach which fails on
GPU-less cloud servers (Railway, Docker) because Google Maps uses WebGL and
detects headless browsers, producing a blank white canvas.

This implementation:
  - Fetches Google satellite tiles directly (same imagery as Google Maps)
  - Falls back to ESRI World Imagery if Google tiles fail
  - Makes plain HTTP requests — no browser, no Chrome, no Selenium needed
  - Works identically on localhost and Railway
  - Returns the same (Path, zoom) signature as before
"""

import math
import random
from io import BytesIO
from pathlib import Path

import requests
from PIL import Image, ImageFilter

# ── Constants ─────────────────────────────────────────────────────────────────
TILE_SIZE = 256

# Google satellite tiles — same imagery as Google Maps, no API key required.
# Uses mt0..mt3 servers (load-balanced), lyrs=s = satellite only.
GOOGLE_TILE_URL = (
    "https://mt{s}.google.com/vt/lyrs=s&x={x}&y={y}&z={z}"
)

# ESRI World Imagery — fallback if Google tiles fail
ESRI_TILE_URL = (
    "https://services.arcgisonline.com/ArcGIS/rest/services/"
    "World_Imagery/MapServer/tile/{z}/{y}/{x}"
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.google.com/maps/",
}


# ── Geo helpers ───────────────────────────────────────────────────────────────
def _haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(dlon / 2) ** 2)
    return 2 * R * math.asin(math.sqrt(a))


def bbox_to_dims(bbox):
    """
    Convert [minx, miny, maxx, maxy] (lon/lat) to
    (center_lat, center_lon, width_km, height_km).
    """
    minx, miny, maxx, maxy = bbox
    center_lat = (miny + maxy) / 2
    center_lon = (minx + maxx) / 2
    width_km   = _haversine_km(miny, minx, miny, maxx)
    height_km  = _haversine_km(miny, minx, maxy, minx)
    return center_lat, center_lon, width_km, height_km


def _lat_lon_to_tile(lat, lon, zoom):
    """Web-Mercator lat/lon → tile (x, y) at given zoom."""
    lat_rad = math.radians(lat)
    n = 2 ** zoom
    x = int((lon + 180.0) / 360.0 * n)
    y = int(
        (1.0 - math.log(math.tan(lat_rad) + 1.0 / math.cos(lat_rad)) / math.pi)
        / 2.0 * n
    )
    return x, y


def _tile_to_lon(tx, zoom):
    """Left-edge longitude of tile tx at zoom."""
    return tx / (2 ** zoom) * 360.0 - 180.0


def _tile_to_lat(ty, zoom):
    """Top-edge latitude of tile ty at zoom (Web-Mercator)."""
    n = math.pi - 2.0 * math.pi * ty / (2 ** zoom)
    return math.degrees(math.atan(math.sinh(n)))


def _calc_zoom(lat, bbox_km, screen_px=1280):
    """
    Reproduce the exact zoom formula used by the original Selenium capture.
    This ensures tiles are fetched at the same resolution the YOLO model was
    calibrated on — changing zoom by even 1 level halves/doubles palm pixel
    size and significantly hurts detection accuracy.
    """
    lat_rad = math.radians(lat)
    z = math.log2((screen_px * 40075.0 * math.cos(lat_rad)) / (256.0 * bbox_km))
    return round(z)


# ── Main capture function ─────────────────────────────────────────────────────
def capture_google_maps(center_lat, center_lon, width_km, height_km,
                        output_path, screen_w=1280, screen_h=900, wait=6):
    """
    Fetch satellite imagery by stitching Google / ESRI tiles.

    Signature is identical to the old Selenium version so no call-sites change.
    Returns (Path, zoom_level).
    Raises RuntimeError on network failure.
    """
    # Use the same zoom formula as the original Selenium approach so palm trees
    # appear at the same pixel scale the detection model was trained on.
    bbox_km = max(width_km, height_km)
    zoom    = _calc_zoom(center_lat, bbox_km, screen_w)

    # Bounding box in degrees from center + km dimensions
    lat_deg_per_km = 1.0 / 111.0
    lon_deg_per_km = 1.0 / (111.0 * math.cos(math.radians(center_lat)))

    min_lat = center_lat - (height_km / 2) * lat_deg_per_km
    max_lat = center_lat + (height_km / 2) * lat_deg_per_km
    min_lon = center_lon - (width_km  / 2) * lon_deg_per_km
    max_lon = center_lon + (width_km  / 2) * lon_deg_per_km

    # Tile range covering the bbox
    x_tl, y_tl = _lat_lon_to_tile(max_lat, min_lon, zoom)   # top-left
    x_br, y_br = _lat_lon_to_tile(min_lat, max_lon, zoom)   # bottom-right

    x_min, x_max = min(x_tl, x_br), max(x_tl, x_br)
    y_min, y_max = min(y_tl, y_br), max(y_tl, y_br)

    cols = x_max - x_min + 1
    rows = y_max - y_min + 1

    # Guard against absurdly large tile grids
    if cols * rows > 400:
        raise RuntimeError(
            f"Tile grid too large ({cols}×{rows}). "
            "Reduce the AOI size or lower the zoom."
        )

    # ── Download and stitch tiles ─────────────────────────────────────────────
    stitched = Image.new("RGB", (cols * TILE_SIZE, rows * TILE_SIZE), (30, 30, 30))
    session  = requests.Session()
    session.headers.update(HEADERS)

    def _fetch_tile(tx, ty, z):
        """Try Google first, fall back to ESRI on failure."""
        # Google: rotate across mt0..mt3 for load balancing
        server = random.randint(0, 3)
        google_url = GOOGLE_TILE_URL.format(s=server, x=tx, y=ty, z=z)
        try:
            resp = session.get(google_url, timeout=15)
            resp.raise_for_status()
            return Image.open(BytesIO(resp.content)).convert("RGB")
        except Exception:
            pass
        # ESRI fallback
        esri_url = ESRI_TILE_URL.format(z=z, y=ty, x=tx)
        try:
            resp = session.get(esri_url, timeout=15)
            resp.raise_for_status()
            return Image.open(BytesIO(resp.content)).convert("RGB")
        except Exception:
            return None  # both failed

    errors = 0
    for row_idx, ty in enumerate(range(y_min, y_max + 1)):
        for col_idx, tx in enumerate(range(x_min, x_max + 1)):
            tile = _fetch_tile(tx, ty, zoom)
            if tile is None:
                errors += 1
                tile = Image.new("RGB", (TILE_SIZE, TILE_SIZE), (60, 60, 60))
            stitched.paste(tile, (col_idx * TILE_SIZE, row_idx * TILE_SIZE))

    if errors == cols * rows:
        raise RuntimeError(
            "All tile downloads failed (both Google and ESRI). "
            "Check your internet connection on Railway."
        )

    # ── Crop stitched image to exact AOI bbox ─────────────────────────────────
    full_lon_left  = _tile_to_lon(x_min,        zoom)
    full_lon_right = _tile_to_lon(x_min + cols, zoom)
    full_lat_top   = _tile_to_lat(y_min,        zoom)
    full_lat_bot   = _tile_to_lat(y_min + rows, zoom)

    full_w_px = cols * TILE_SIZE
    full_h_px = rows * TILE_SIZE

    def _lon_to_px(lon):
        return int((lon - full_lon_left) / (full_lon_right - full_lon_left) * full_w_px)

    def _lat_to_px(lat):
        return int((full_lat_top - lat) / (full_lat_top - full_lat_bot) * full_h_px)

    left   = max(0, _lon_to_px(min_lon))
    right  = min(full_w_px, _lon_to_px(max_lon))
    top    = max(0, _lat_to_px(max_lat))
    bottom = min(full_h_px, _lat_to_px(min_lat))

    if right > left and bottom > top:
        stitched = stitched.crop((left, top, right, bottom))

    # ── Blur the bottom strip (ESRI attribution bar) ──────────────────────────
    w, h = stitched.size
    if h > 40:
        btm_h  = min(30, h // 10)
        region = stitched.crop((0, h - btm_h, w, h))
        stitched.paste(region.filter(ImageFilter.GaussianBlur(radius=10)),
                       (0, h - btm_h))

    # ── Save ──────────────────────────────────────────────────────────────────
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    stitched.save(str(output_path))

    return output_path, zoom
