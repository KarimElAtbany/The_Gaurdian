import math
import time
from pathlib import Path
from PIL import Image, ImageFilter


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


def _calc_zoom(lat, bbox_km, screen_px=1280):
    lat_rad = math.radians(lat)
    z = math.log2((screen_px * 40075.0 * math.cos(lat_rad)) / (256.0 * bbox_km))
    return round(z)


def capture_google_maps(center_lat, center_lon, width_km, height_km,
                        output_path, screen_w=1280, screen_h=900, wait=6):
    """
    Open Google Maps satellite view in headless Chrome, strip all UI elements
    using JavaScript to expose only the map canvas, take a screenshot, then
    crop the result to the exact AOI rectangle (width_km x height_km).

    Returns (Path, zoom_level).
    Raises ImportError if selenium is not installed.
    Raises RuntimeError on Chrome/driver failure.
    """
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
    except ImportError:
        raise ImportError(
            "selenium is required for high-res capture. "
            "Install it with:  pip install selenium"
        )

    # Zoom to fit the larger AOI dimension across screen_w pixels
    bbox_km = max(width_km, height_km)
    zoom    = _calc_zoom(center_lat, bbox_km, screen_w)

    url = (
        f"https://www.google.com/maps/@{center_lat},{center_lon},{zoom}z"
        "/data=!3m1!1e3"
    )

    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument(f"--window-size={screen_w},{screen_h}")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--log-level=3")

    try:
        driver = webdriver.Chrome(options=chrome_options)
    except Exception as exc:
        raise RuntimeError(
            f"Chrome/ChromeDriver not found or failed to start: {exc}\n"
            "Make sure Google Chrome and ChromeDriver are installed."
        )

    driver.set_window_size(screen_w, screen_h)
    driver.get(url)

    # Wait for map tiles to fully load
    time.sleep(wait)

    # Hide all Google Maps UI overlays via CSS — does NOT touch the canvas/WebGL context
    driver.execute_script("""
        var s = document.createElement('style');
        s.textContent = [
            'button { opacity: 0 !important; pointer-events: none !important; }',
            'a { opacity: 0 !important; pointer-events: none !important; }',
            '[role="menubar"]            { display: none !important; }',
            '[role="dialog"]             { display: none !important; }',
            '[role="main"]               { display: none !important; }',
            '.app-viewcard-strip         { display: none !important; }',
            '.scene-footer-default       { display: none !important; }',
            '.widget-scene-titlecard     { display: none !important; }',
            '.omnibox-container          { display: none !important; }',
            '.searchbox                  { display: none !important; }',
            '#searchbox                  { display: none !important; }',
            '.id-searchbox               { display: none !important; }',
            '.widget-scene-canvas .app-bottom-content-anchor { display: none !important; }',
            '[jsrenderer="PlacePage"]    { display: none !important; }',
            '[jsrenderer="PlaceReview"]  { display: none !important; }',
            '.ml-promotion-panel         { display: none !important; }',
            '.ml-promotion-container     { display: none !important; }',
            '.watermark                  { display: none !important; }',
            'body { margin: 0 !important; overflow: hidden !important; }'
        ].join('');
        document.head.appendChild(s);

        // Also hide by position: any fixed/absolute element in the top-right quadrant
        Array.from(document.querySelectorAll('*')).forEach(function(el) {
            var r = el.getBoundingClientRect();
            var p = window.getComputedStyle(el).position;
            if ((p === 'fixed' || p === 'absolute') &&
                r.left > window.innerWidth * 0.50 &&
                r.top  < window.innerHeight * 0.25 &&
                r.width > 50) {
                el.style.display = 'none';
            }
        });
    """)

    time.sleep(2)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save raw full-window screenshot
    raw_path = output_path.with_stem(output_path.stem + "_raw")
    driver.save_screenshot(str(raw_path))
    driver.quit()

    # ── Post-process raw screenshot ───────────────────────────────────────────
    img = Image.open(raw_path)
    w, h = img.size

    # Blur bottom strip (Google Maps watermark + copyright)
    btm_h = 38
    btm_region = img.crop((0, h - btm_h, w, h))
    img.paste(btm_region.filter(ImageFilter.GaussianBlur(radius=14)),
              (0, h - btm_h))

    img.save(str(raw_path))   # overwrite raw with processed version

    # ── Rectangular crop to exact AOI dimensions ──────────────────────────────
    img = Image.open(raw_path)
    w, h = img.size

    # km per pixel: the larger dimension fills screen_w pixels
    km_per_px = bbox_km / w

    crop_w = min(w, max(1, int(round(width_km  / km_per_px))))
    crop_h = min(h, max(1, int(round(height_km / km_per_px))))

    left = (w - crop_w) // 2
    top  = (h - crop_h) // 2

    img = img.crop((left, top, left + crop_w, top + crop_h))
    img.save(str(output_path))

    try:
        raw_path.unlink()
    except OSError:
        pass

    return output_path, zoom
