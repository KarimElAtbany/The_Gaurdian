import folium
import math
from folium.plugins import Draw
import numpy as np


def bbox_zoom(min_lon, min_lat, max_lon, max_lat):
    """Return a folium zoom_start suitable for showing the given bbox."""
    span = max(abs(max_lon - min_lon), abs(max_lat - min_lat))
    # ~0.05° span → zoom 14; halving span adds +1 zoom
    zoom = int(round(14 - math.log2(max(span / 0.05, 1e-9))))
    return max(12, min(19, zoom))


def create_base_map(center=None, zoom=12):
    if center is None:
        center = [25.65, 28.95]
    m = folium.Map(
        location=center,
        zoom_start=zoom,
        tiles='OpenStreetMap'
    )
    Draw(
        export=True,
        draw_options={
            'rectangle': True,
            'polygon': True,
            'circle': False,
            'marker': False,
            'circlemarker': False,
            'polyline': False
        }
    ).add_to(m)
    return m


def parse_coordinates(coord_str):
    parts = (
        coord_str
        .replace('°', '')
        .replace('N', '').replace('S', '-')
        .replace('E', '').replace('W', '-')
        .split(',')
    )
    try:
        lat = float(parts[0].strip())
        lon = float(parts[1].strip())
        return [lat, lon]
    except Exception:
        return None


def bbox_from_drawing(drawing_data):
    if not drawing_data or 'geometry' not in drawing_data:
        return None
    geom = drawing_data['geometry']
    if geom['type'] == 'Polygon':
        coords = geom['coordinates'][0]
        lons = [c[0] for c in coords]
        lats = [c[1] for c in coords]
        return [min(lons), min(lats), max(lons), max(lats)]
    return None


def add_health_zones_overlay(m, health_map, transform, colors):
    from folium.raster_layers import ImageOverlay
    import rasterio.transform
    from PIL import Image
    import io
    import base64

    height, width = health_map.shape
    bounds = rasterio.transform.array_bounds(height, width, transform)
    rgb_array = np.zeros((height, width, 4), dtype=np.uint8)
    color_map = {
        0: [215, 48, 39, 180],
        1: [253, 174, 97, 180],
        2: [255, 255, 191, 180],
        3: [26, 152, 80, 180]
    }
    for class_id, color in color_map.items():
        mask = health_map == class_id
        rgb_array[mask] = color

    img = Image.fromarray(rgb_array, mode='RGBA')
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    img_base64 = base64.b64encode(buffer.getvalue()).decode()

    ImageOverlay(
        image=f"data:image/png;base64,{img_base64}",
        bounds=[[bounds[1], bounds[0]], [bounds[3], bounds[2]]],
        opacity=0.6
    ).add_to(m)
    return m
