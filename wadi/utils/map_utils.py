import folium
from folium.plugins import Draw
import numpy as np


def create_base_map(center=None, zoom=10):
    if center is None:
        center = [25.65, 28.95]

    m = folium.Map(
        location=center,
        zoom_start=zoom,
        tiles='OpenStreetMap'
    )

    folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
        attr='Google Satellite',
        name='Satellite'
    ).add_to(m)

    Draw(
        export=False,
        draw_options={
            'rectangle': True,
            'polygon': True,
            'circle': False,
            'marker': False,
            'circlemarker': False,
            'polyline': False,
        },
        edit_options={'edit': False}
    ).add_to(m)

    folium.LayerControl().add_to(m)

    return m


def parse_coordinates(coord_str):
    try:
        cleaned = (
            coord_str
            .replace('°', '')
            .replace('N', '')
            .replace('E', '')
            .replace('S', '-')
            .replace('W', '-')
        )
        parts = cleaned.split(',')
        lat = float(parts[0].strip())
        lon = float(parts[1].strip())
        return lat, lon
    except Exception:
        return None


def bbox_from_drawing(drawing_data):
    if not drawing_data or 'geometry' not in drawing_data:
        return None

    geom = drawing_data['geometry']
    gtype = geom.get('type')
    coords = geom.get('coordinates', [])

    if gtype == 'Polygon':
        ring = coords[0]
        lons = [c[0] for c in ring]
        lats = [c[1] for c in ring]
        return [min(lons), min(lats), max(lons), max(lats)]

    if gtype == 'Rectangle':
        ring = coords[0]
        lons = [c[0] for c in ring]
        lats = [c[1] for c in ring]
        return [min(lons), min(lats), max(lons), max(lats)]

    return None


def add_health_overlay(m, health_map, transform):
    from folium.raster_layers import ImageOverlay
    import rasterio.transform
    from PIL import Image
    import io
    import base64

    height, width = health_map.shape
    bounds = rasterio.transform.array_bounds(height, width, transform)

    color_map = {
        0: [215, 48, 39, 180],
        1: [253, 174, 97, 180],
        2: [255, 255, 191, 180],
        3: [26, 152, 80, 180],
    }

    rgba = np.zeros((height, width, 4), dtype=np.uint8)
    for class_id, color in color_map.items():
        mask = health_map == class_id
        rgba[mask] = color

    img = Image.fromarray(rgba, mode='RGBA')
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    img_b64 = base64.b64encode(buf.getvalue()).decode()

    ImageOverlay(
        image=f"data:image/png;base64,{img_b64}",
        bounds=[[bounds[1], bounds[0]], [bounds[3], bounds[2]]],
        opacity=0.65,
        name='Health Map'
    ).add_to(m)

    return m
