"""
SkyFi satellite image capture — uses a visible Chrome window.

Based on the confirmed-working approach:
  1. Open SkyFi explore in a real (non-headless) Chrome window
  2. Navigate to coordinates via the search box
  3. Hide large UI panels (area > 15 000 px²) via JavaScript
  4. Screenshot the Mapbox canvas element directly (auto-crops to the map)
  5. Return the saved path + zoom level

Re-exports bbox_to_dims so callers only need one import line.
"""

import math
import time
from pathlib import Path

# ── Re-export helpers so the call site only needs one import ──────────────────
from utils.google_maps_capture import bbox_to_dims, _haversine_km   # noqa: F401


# ─────────────────────────────────────────────────────────────────────────────
_SKYFI_URL = "https://app.skyfi.com/explore/open"


def _calc_zoom(lat: float, bbox_km: float, screen_px: int = 800) -> int:
    lat_rad = math.radians(lat)
    z = math.log2((screen_px * 40075.0 * math.cos(lat_rad)) / (256.0 * bbox_km))
    return round(z)


def _try_find(driver, selectors, by, timeout=10):
    """Poll until a visible element matching one of the selectors is found."""
    from selenium.webdriver.common.by import By
    end_time = time.time() + timeout
    while time.time() < end_time:
        for sel in selectors:
            try:
                elements = driver.find_elements(by, sel)
                visible = [e for e in elements if e.is_displayed()]
                if visible:
                    return visible[0], sel
            except Exception:
                pass
        time.sleep(0.5)
    return None, None


def _search_coordinates(driver, lat: float, lon: float) -> bool:
    """Type lat,lon into SkyFi's search box and press Enter."""
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys

    search_selectors = [
        "input[type='text']",
        "input[placeholder*='Search']",
        "input[placeholder*='search']",
        "input[aria-label*='Search']",
        "input[aria-label*='search']",
    ]
    box, _ = _try_find(driver, search_selectors, By.CSS_SELECTOR, timeout=10)
    if not box:
        return False
    try:
        box.click()
        time.sleep(0.8)
        box.clear()
        box.send_keys(f"{lat}, {lon}")
        time.sleep(0.8)
        box.send_keys(Keys.ENTER)
        time.sleep(6)      # wait for map to pan + tiles to load
        return True
    except Exception:
        return False


def _hide_ui_panels(driver) -> None:
    """
    Hide any DOM element whose bounding-box area exceeds 15 000 px²
    AND that is NOT the map canvas — removes sidebars, panels, dialogs
    without touching the satellite imagery canvas.
    """
    js = """
    const skip = new Set();
    document.querySelectorAll('.mapboxgl-canvas, canvas').forEach(c => {
        var p = c;
        while (p) { skip.add(p); p = p.parentElement; }
    });

    const panelSelectors = [
        'header', 'nav', 'aside',
        '[role="dialog"]',
        '[class*="sidebar"]', '[class*="Sidebar"]',
        '[class*="panel"]',   '[class*="Panel"]',
        '[class*="drawer"]',  '[class*="Drawer"]',
        '[class*="toolbar"]', '[class*="Toolbar"]',
        '[class*="search"]',  '[class*="Search"]',
        '[class*="cookie"]',  '[class*="Cookie"]',
        '[class*="consent"]', '[class*="banner"]'
    ];

    panelSelectors.forEach(sel => {
        document.querySelectorAll(sel).forEach(el => {
            if (skip.has(el)) return;
            try {
                const r = el.getBoundingClientRect();
                if (r.width * r.height > 15000) {
                    el.style.display = 'none';
                }
            } catch(e) {}
        });
    });

    document.body.style.margin   = '0';
    document.body.style.overflow = 'hidden';
    """
    try:
        driver.execute_script(js)
        time.sleep(2)
    except Exception:
        pass


def _click_zoom_in(driver, clicks: int = 2) -> None:
    """Click the Mapbox zoom-in button N times."""
    from selenium.webdriver.common.by import By
    zoom_selectors = [
        "button[aria-label*='Zoom in']",
        "button[title*='Zoom in']",
        "[class*='zoom-in']",
    ]
    btn, _ = _try_find(driver, zoom_selectors, By.CSS_SELECTOR, timeout=5)
    if not btn:
        return
    for _ in range(clicks):
        try:
            btn.click()
            time.sleep(0.8)
        except Exception:
            break


def _find_map_canvas(driver):
    """Return the Mapbox GL canvas element."""
    from selenium.webdriver.common.by import By
    map_selectors = [
        ".mapboxgl-canvas",
        "canvas.mapboxgl-canvas",
        ".leaflet-container",
        "[class*='mapbox'] canvas",
        "[class*='map'] canvas",
        "canvas",
    ]
    element, _ = _try_find(driver, map_selectors, By.CSS_SELECTOR, timeout=12)
    return element


# ─────────────────────────────────────────────────────────────────────────────
def capture_skyfi(
    center_lat:  float,
    center_lon:  float,
    width_km:    float,
    height_km:   float,
    output_path,
    headless:    bool  = False,   # SkyFi blocks headless — keep False
    wait_initial: float = 8.0,
) -> tuple:
    """
    Capture a clean satellite image from SkyFi for the given AOI.

    Parameters
    ----------
    center_lat / center_lon : AOI centre in decimal degrees
    width_km / height_km    : AOI extent (used for zoom calculation)
    output_path             : destination PNG path
    headless                : False (SkyFi blocks headless Chrome)
    wait_initial            : seconds to wait after page first loads

    Returns
    -------
    (Path, zoom_level)
    """
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
    except ImportError:
        raise ImportError(
            "selenium is required for SkyFi capture.\n"
            "Install with:  pip install selenium"
        )

    bbox_km = max(width_km, height_km)
    zoom    = _calc_zoom(center_lat, bbox_km)

    opts = Options()
    opts.add_argument("--window-size=1400,1000")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_argument("--disable-infobars")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    if headless:
        opts.add_argument("--headless=new")

    try:
        driver = webdriver.Chrome(options=opts)
        driver.set_page_load_timeout(60)
    except Exception as exc:
        raise RuntimeError(
            f"Chrome/ChromeDriver not found or failed to start: {exc}\n"
            "Make sure Google Chrome and ChromeDriver are installed."
        )

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # ── 1. Open SkyFi ─────────────────────────────────────────────────────
        driver.get(_SKYFI_URL)
        time.sleep(wait_initial)

        # ── 2. Navigate to AOI via search box ─────────────────────────────────
        moved = _search_coordinates(driver, center_lat, center_lon)
        if not moved:
            # Fallback: give the page a moment and try to continue anyway
            time.sleep(4)

        # ── 3. Extra zoom clicks (computed zoom vs SkyFi default ~14) ─────────
        extra_clicks = max(0, min(8, zoom - 14))
        if extra_clicks > 0:
            _click_zoom_in(driver, clicks=extra_clicks)
            time.sleep(2)

        # ── 4. Hide all large UI panels / sidebars / cookie banners ───────────
        _hide_ui_panels(driver)

        # ── 5. Find the Mapbox canvas element ─────────────────────────────────
        map_canvas = _find_map_canvas(driver)
        if not map_canvas:
            raise RuntimeError(
                "Could not find the SkyFi map canvas.\n"
                "SkyFi may have changed its layout — update selectors in skyfi_capture.py."
            )

        # ── 6. Screenshot directly to the canvas (auto-crops to map area) ─────
        map_canvas.screenshot(str(output_path))

    finally:
        driver.quit()

    return output_path, zoom
