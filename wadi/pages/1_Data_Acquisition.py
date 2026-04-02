import streamlit as st
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))

from utils.aws_downloader import STACDownloader
from utils.cache_manager import CacheManager
from utils.map_utils import create_base_map, parse_coordinates, bbox_from_drawing
from streamlit_folium import st_folium
from datetime import datetime, timedelta

st.set_page_config(page_title="Data Acquisition", page_icon="📡", layout="wide")

with open(Path(__file__).parent.parent / "assets/style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.title("📡 Data Acquisition")

REQUIRED_BANDS = ['blue', 'green', 'red', 'rededge1', 'rededge3', 'nir', 'nir08', 'swir16']
BAND_LABELS = {
    'blue':     'B02 — Blue',
    'green':    'B03 — Green',
    'red':      'B04 — Red',
    'rededge1': 'B05 — Red Edge 1  (NDRE)',
    'rededge3': 'B07 — Red Edge 3  (CIre)',
    'nir':      'B08 — NIR',
    'nir08':    'B8A — Narrow NIR  (NDWI)',
    'swir16':   'B11 — SWIR        (NDWI)',
}

if 'bbox' not in st.session_state:
    st.session_state.bbox = None
if 'downloaded_bands' not in st.session_state:
    st.session_state.downloaded_bands = {}
if 'stac_items' not in st.session_state:
    st.session_state.stac_items = []

cache_manager = CacheManager("data/cache")
downloader = STACDownloader()

with st.sidebar:
    st.subheader("📍 Location Search")
    coord_search = st.text_input("Coordinates (e.g., 25.65°N, 28.95°E)")
    if coord_search and st.button("Go to Location"):
        coords = parse_coordinates(coord_search)
        if coords:
            st.session_state.map_center = coords
            st.success(f"Centered at {coords}")
        else:
            st.error("Invalid coordinates format")

    st.divider()

    st.subheader("📅 Date Range")
    date_from = st.date_input("From", datetime.now() - timedelta(days=30))
    date_to   = st.date_input("To",   datetime.now())

    st.subheader("⚙️ Filters")
    cloud_cover = st.slider("Max Cloud Cover %", 0, 100, 30)
    collection  = st.selectbox("Collection", ["sentinel-2-l2a", "sentinel-2-l1c"])
    limit       = st.number_input("Max Results", 1, 20, 10)

    st.divider()
    st.caption("**Bands downloaded per product:**")
    for k, v in BAND_LABELS.items():
        st.caption(f"• {v}")

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("🗺️ Draw Area of Interest")

    center = st.session_state.get('map_center', [25.65, 28.95])
    m = create_base_map(center=center)

    map_data = st_folium(m, width=800, height=600, returned_objects=["last_active_drawing"])

    if map_data and map_data.get('last_active_drawing'):
        bbox = bbox_from_drawing(map_data['last_active_drawing'])
        if bbox:
            st.session_state.bbox = bbox
            st.success(f"AOI: {bbox[0]:.4f}, {bbox[1]:.4f} → {bbox[2]:.4f}, {bbox[3]:.4f}")

with col2:
    st.subheader("🔍 Search Products")

    if st.button("Search STAC Catalog", type="primary", disabled=not st.session_state.bbox):
        bbox = st.session_state.bbox

        polygon = {
            "type": "Polygon",
            "coordinates": [[
                [bbox[0], bbox[1]],
                [bbox[0], bbox[3]],
                [bbox[2], bbox[3]],
                [bbox[2], bbox[1]],
                [bbox[0], bbox[1]]
            ]]
        }

        start_date = date_from.strftime('%Y-%m-%dT00:00:00Z')
        end_date   = date_to.strftime('%Y-%m-%dT23:59:59Z')

        try:
            with st.spinner("Searching STAC catalog..."):
                items = downloader.search_items(
                    polygon,
                    start_date,
                    end_date,
                    collection=collection,
                    limit=limit,
                    max_cloud=cloud_cover
                )

            if items:
                st.session_state.stac_items = items
                st.session_state.search_polygon = polygon
                st.success(f"✅ Found {len(items)} products")
            else:
                st.warning("No products found. Try adjusting filters.")
        except Exception as e:
            st.error(f"Search error: {e}")

    if st.session_state.stac_items:
        st.subheader("📦 Available Products")

        for idx, item in enumerate(st.session_state.stac_items):
            product_id = item['id']
            props      = item.get('properties', {})
            cloud      = props.get('eo:cloud_cover', 'N/A')
            date       = props.get('datetime', 'N/A')[:10]

            with st.expander(f"{product_id[:30]}... | ☁️ {cloud}%"):
                st.write(f"**Date:** {date}")
                st.write(f"**Cloud:** {cloud}%")

                cached = cache_manager.get_all_bands(product_id)

                if cached:
                    st.success("✅ Cached")
                    if st.button("Load from Cache", key=f"load_{idx}"):
                        st.session_state.downloaded_bands[product_id] = cached
                        st.session_state.current_product = product_id
                        st.rerun()
                else:
                    if st.button("⬇️ Download Bands", key=f"dl_{idx}"):
                        output_dir = Path("data/downloads") / product_id
                        output_dir.mkdir(parents=True, exist_ok=True)

                        progress_bar = st.progress(0)

                        try:
                            st.write("Downloading 8 spectral bands…")
                            bands = downloader.download_bands(
                                item,
                                output_dir,
                                bands=REQUIRED_BANDS
                            )
                            progress_bar.progress(0.6)

                            for band_name, path in bands.items():
                                cached_path = cache_manager.cache_band(product_id, band_name, path)
                                bands[band_name] = cached_path

                            st.session_state.downloaded_bands[product_id] = bands
                            st.session_state.current_product = product_id
                            st.session_state.current_item    = item
                            progress_bar.progress(1.0)
                            st.success(f"✅ Downloaded {len(bands)} bands!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Download error: {e}")

if st.session_state.downloaded_bands:
    st.divider()
    st.subheader("✅ Downloaded Products")
    for product_id, bands in st.session_state.downloaded_bands.items():
        st.success(f"📦 {product_id}  —  {len(bands)} bands")
