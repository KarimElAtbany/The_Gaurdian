import streamlit as st
from pathlib import Path
import sys
import base64
sys.path.append(str(Path(__file__).parent.parent))

from utils.aws_downloader import STACDownloader
from utils.cache_manager import CacheManager
from utils.map_utils import create_base_map, parse_coordinates, bbox_from_drawing, bbox_zoom
from utils.translations import t, inject_rtl, lang_toggle, render_nav
from streamlit_folium import st_folium
from datetime import datetime, timedelta

st.set_page_config(page_title="Data Acquisition — The Guardian", layout="wide")

def _load_styles():
    base = Path(__file__).parent.parent
    for _css in [base / "assets/style.css", base / "assets/icons/tabler-local.css"]:
        if _css.exists():
            st.markdown(f"<style>{_css.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

_load_styles()

def _svg_logo(height=52, invert=True):
    svg_path = Path(__file__).parent.parent / "graphic" / "logo.svg"
    if svg_path.exists():
        svg = svg_path.read_text(encoding='utf-8')
        b64 = base64.b64encode(svg.encode()).decode()
        filt = "filter:brightness(0) invert(1);" if invert else ""
        return f'<img src="data:image/svg+xml;base64,{b64}" style="height:{height}px;width:auto;{filt}">'
    return '<span style="font-size:2rem;">🌿</span>'

def _png_img(name, height=48):
    p = Path(__file__).parent.parent / "graphic" / name
    if p.exists():
        b64 = base64.b64encode(p.read_bytes()).decode()
        return f'<img src="data:image/png;base64,{b64}" style="height:{height}px;width:auto;vertical-align:middle;">'
    return ''

# ── Sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.markdown(f"""
<div class="sidebar-logo">{_svg_logo(44)}</div>
<div class="sidebar-eco">Eco Team</div>
""", unsafe_allow_html=True)

lang = lang_toggle("data")
render_nav(lang)
inject_rtl(lang)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="guardian-header">
    {_svg_logo(52)}
    <div class="guardian-header-text">
        <div class="title">The Guardian</div>
        <div class="subtitle">{t("header_sub_data", lang)}</div>
        <div class="eco-badge">{t("eco_badge", lang)}</div>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown(f'<div class="g-section-title">{_png_img("data.png", 22)} {t("section_data", lang)}</div>',
            unsafe_allow_html=True)

# ── Session state init ────────────────────────────────────────────────────────
if 'bbox' not in st.session_state:
    st.session_state.bbox = None
if 'downloaded_bands' not in st.session_state:
    st.session_state.downloaded_bands = {}
if 'stac_items' not in st.session_state:
    st.session_state.stac_items = []
if 'map_center' not in st.session_state:
    st.session_state.map_center = [25.65, 28.95]
if 'selected_products' not in st.session_state:
    st.session_state.selected_products = []
if 'selected_products_meta' not in st.session_state:
    st.session_state.selected_products_meta = {}

cache_manager = CacheManager("data/cache")
downloader = STACDownloader()

# ── Preset AOI definitions ────────────────────────────────────────────────────
_LOCATIONS = [
        (
        "Dakhla", "الداخلة",
        25.549117, 29.269004,  # updated center
        [29.266886, 25.547824, 29.269134, 25.550074],  # bbox
        [
            [29.266886,25.547824],
            [29.266886,25.550074],
            [29.269134,25.550074],
            [29.269134,25.547824],
            [29.266886,25.547824]
        ],
    ),
    (
        "Sharq El Owainat", "شرق العوينات",
        22.559879, 28.675666,  # updated center
        [28.6754, 22.556804, 28.678512, 22.562372],
        [
            [28.6754,22.556804],
            [28.6754,22.562372],
            [28.678512,22.562372],
            [28.678512,22.556804],
            [28.6754,22.556804]
        ],
    ),
(
        "Kharga", "الخارجة",
        25.373725, 30.578701,  # updated center
        [30.576390568063232, 25.373116115631035, 30.57820289503394, 25.374097813976903],
        [
            [30.57820289503394,25.374097813976903],
            [30.576390568063232,25.374097813976903],
            [30.576390568063232,25.373116115631035],
            [30.57820289503394,25.373116115631035],
            [30.57820289503394,25.374097813976903]
        ],
    ),]

# ── Sidebar controls ──────────────────────────────────────────────────────────
with st.sidebar:
    st.subheader(t("quick_locations", lang))
    for en_name, ar_name, clat, clon, bbox_preset, ring in _LOCATIONS:
        label = en_name if lang == "en" else ar_name
        if st.button(label, key=f"loc_{en_name}", use_container_width=True):
            st.session_state.map_center     = [clat, clon]
            st.session_state.bbox           = bbox_preset
            st.session_state.preset_polygon = ring
            st.session_state.map_zoom       = bbox_zoom(
                bbox_preset[0], bbox_preset[1], bbox_preset[2], bbox_preset[3]
            )
            st.rerun()

    st.divider()
    st.subheader(t("location_search", lang))
    coord_search = st.text_input(t("coord_input", lang))
    if coord_search and st.button(t("go_to_location", lang)):
        coords = parse_coordinates(coord_search)
        if coords:
            st.session_state.map_center = coords
            st.success(f"Centered at {coords}")
        else:
            st.error(t("invalid_coords", lang))

    st.divider()
    st.subheader(t("date_range", lang))
    date_from = st.date_input(t("date_from", lang), datetime.now() - timedelta(days=30))
    date_to   = st.date_input(t("date_to",   lang), datetime.now())

    st.subheader(t("filters", lang))
    cloud_cover = st.slider(t("max_cloud", lang), 0, 100, 30)
    collection  = "sentinel-2-l2a"   # always L2A (surface reflectance)
    limit       = st.number_input(t("max_results", lang), 1, 20, 10)

# ── Map ───────────────────────────────────────────────────────────────────────
st.subheader(t("draw_aoi", lang))

if st.session_state.bbox:
    bbox = st.session_state.bbox
    st.success(f"AOI: {bbox[0]:.4f}, {bbox[1]:.4f}  —  {bbox[2]:.4f}, {bbox[3]:.4f}")

center = st.session_state.map_center
zoom   = st.session_state.get("map_zoom", 12)
m = create_base_map(center=center, zoom=zoom)

# Draw preset polygon on the map if one was loaded from a quick-location button
if st.session_state.get('preset_polygon'):
    import folium
    ring = st.session_state.preset_polygon
    geojson_layer = {
        "type": "FeatureCollection",
        "features": [{
            "type": "Feature",
            "properties": {},
            "geometry": {"type": "Polygon", "coordinates": [ring]}
        }]
    }
    folium.GeoJson(
        geojson_layer,
        style_function=lambda _: {
            "fillColor": "#219EBC",
            "color": "#219EBC",
            "weight": 2,
            "fillOpacity": 0.15,
        }
    ).add_to(m)
st.markdown("""
<style>
.element-container:has(iframe) {
    border: 2px solid #84A59D;
    border-radius: 10px;
    overflow: hidden;
}
</style>
""", unsafe_allow_html=True)
map_data = st_folium(m, use_container_width=True, height=640, returned_objects=["last_active_drawing"])

if map_data and map_data.get('last_active_drawing'):
    bbox = bbox_from_drawing(map_data['last_active_drawing'])
    if bbox:
        st.session_state.bbox           = bbox
        st.session_state.preset_polygon = None   # user drew a custom area — discard preset
        st.session_state.pop("map_zoom", None)   # reset zoom to default
        st.success(f"AOI: {bbox[0]:.4f}, {bbox[1]:.4f}  —  {bbox[2]:.4f}, {bbox[3]:.4f}")

# ── Search products ───────────────────────────────────────────────────────────
st.divider()
st.subheader(t("search_products", lang))

if st.button(t("search_stac_btn", lang), type="primary", disabled=not st.session_state.bbox):
    bbox = st.session_state.bbox
    polygon = {
        "type": "Polygon",
        "coordinates": [[
            [bbox[0], bbox[1]], [bbox[0], bbox[3]],
            [bbox[2], bbox[3]], [bbox[2], bbox[1]],
            [bbox[0], bbox[1]]
        ]]
    }
    start_date = date_from.strftime('%Y-%m-%dT00:00:00Z')
    end_date   = date_to.strftime('%Y-%m-%dT23:59:59Z')

    try:
        with st.spinner(t("searching_stac", lang)):
            items = downloader.search_items(
                polygon, start_date, end_date,
                collection=collection, limit=limit, max_cloud=cloud_cover
            )
        if items:
            st.session_state.stac_items    = items
            st.session_state.search_polygon = polygon
            n = len(items)
            found_msg = f"Found {n} products" if lang == "en" else f"تم العثور على {n} منتج"
            st.success(found_msg)
        else:
            st.warning(t("no_products", lang))
    except Exception as e:
        st.error(f"Search error: {e}")

if st.session_state.stac_items:
    st.subheader(t("available_products", lang))

    for idx, item in enumerate(st.session_state.stac_items):
        product_id = item['id']
        props  = item.get('properties', {})
        cloud  = props.get('eo:cloud_cover', 'N/A')
        date   = props.get('datetime', 'N/A')[:10]

        with st.expander(f"{product_id[:30]}...  |  {t('cloud_label', lang)}: {cloud}%"):
            st.write(f"**{t('date_label', lang)}:** {date}")
            st.write(f"**{t('cloud_label', lang)}:** {cloud}%")

            cached = cache_manager.get_all_bands(product_id)

            if cached:
                st.success(t("cached", lang))
                _is_sel = product_id in st.session_state.selected_products
                if _is_sel:
                    _desel_lbl = ("✓ Selected — click to deselect"
                                  if lang == "en" else "✓ مختار — اضغط للإلغاء")
                    if st.button(_desel_lbl, key=f"desel_{idx}",
                                 use_container_width=True, type="primary"):
                        st.session_state.selected_products.remove(product_id)
                        st.session_state.selected_products_meta.pop(product_id, None)
                        st.rerun()
                else:
                    if st.button(t("select_for_analysis", lang), key=f"sel_{idx}",
                                 use_container_width=True):
                        st.session_state.downloaded_bands[product_id] = cached
                        st.session_state.current_product = product_id
                        st.session_state.selected_products.append(product_id)
                        st.session_state.selected_products_meta[product_id] = {
                            "date": date, "cloud": cloud
                        }
                        st.rerun()
            else:
                if st.button(t("download_bands_btn", lang), key=f"dl_{idx}"):
                    output_dir = Path("data/downloads") / product_id
                    output_dir.mkdir(parents=True, exist_ok=True)

                    _dl_label = "Downloading spectral bands…" if lang == "en" else "جارٍ تنزيل النطاقات الطيفية…"
                    progress_bar  = st.progress(0.0, text=_dl_label)
                    status_text   = st.empty()

                    def _on_band_progress(fraction, band_display, index, total):
                        # Bands fill 0–90 %; caching fills 90–100 %
                        bar_val = fraction * 0.90
                        if lang == "en":
                            msg = f"Band {index} / {total} — {band_display}"
                        else:
                            msg = f"نطاق {index} / {total} — {band_display}"
                        progress_bar.progress(bar_val, text=msg)
                        status_text.caption(f"⬇ {band_display}")

                    try:
                        bands = downloader.download_bands(
                            item, output_dir,
                            bands=['blue', 'green', 'red', 'rededge1',
                                   'rededge3', 'nir', 'nir08', 'swir16'],
                            progress_callback=_on_band_progress,
                        )

                        if len(bands) >= 4:
                            cache_msg = "Caching bands…" if lang == "en" else "جارٍ حفظ النطاقات في الذاكرة…"
                            progress_bar.progress(0.90, text=cache_msg)
                            status_text.empty()

                            n_cached = len(bands)
                            for ci, (band_name, path) in enumerate(list(bands.items()), 1):
                                cached_path = cache_manager.cache_band(product_id, band_name, path)
                                bands[band_name] = cached_path
                                progress_bar.progress(0.90 + 0.10 * ci / n_cached,
                                                      text=cache_msg)

                            st.session_state.downloaded_bands[product_id] = bands
                            st.session_state.current_product = product_id
                            st.session_state.current_item    = item
                            # Auto-select the freshly downloaded product
                            if product_id not in st.session_state.selected_products:
                                st.session_state.selected_products.append(product_id)
                            st.session_state.selected_products_meta[product_id] = {
                                "date": date, "cloud": cloud
                            }

                            done_msg = t("download_complete", lang)
                            progress_bar.progress(1.0, text=done_msg)
                            st.success(done_msg)
                            st.rerun()
                        else:
                            st.error(t("download_incomplete", lang))
                    except Exception as e:
                        st.error(f"Download error: {e}")

_sel = st.session_state.selected_products
_meta = st.session_state.selected_products_meta
if _sel:
    st.divider()
    n_sel = len(_sel)
    if n_sel == 1:
        _badge = ("1 product selected for analysis"
                  if lang == "en" else "منتج واحد مختار للتحليل")
        _hint  = ("Go to AI Analysis to run vegetation health and tree detection."
                  if lang == "en" else
                  "انتقل إلى تحليل الذكاء الاصطناعي لتشغيل تحليل الصحة النباتية وكشف الأشجار.")
    else:
        _badge = (f"{n_sel} products selected for time series comparison"
                  if lang == "en" else f"{n_sel} منتجات مختارة لمقارنة السلاسل الزمنية")
        _hint  = ("Run AI Analysis on at least one product, then open the Dashboard to run "
                  "the full time series comparison across all selected products."
                  if lang == "en" else
                  "شغّل تحليل الذكاء الاصطناعي على منتج واحد على الأقل، ثم افتح لوحة التحكم "
                  "لتشغيل مقارنة السلاسل الزمنية الكاملة لجميع المنتجات المختارة.")

    st.markdown(f"""
    <div style="background:#EAF4F7;border-radius:12px;padding:16px 20px;margin-bottom:12px;">
        <div style="font-size:13px;font-weight:700;color:#219EBC;margin-bottom:10px;">
            🔵 {_badge}
        </div>
        {''.join(
            f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:6px;">'
            f'<span style="background:#219EBC;color:white;border-radius:50%;width:22px;height:22px;'
            f'display:inline-flex;align-items:center;justify-content:center;font-size:11px;'
            f'font-weight:700;flex-shrink:0;">{i+1}</span>'
            f'<span style="font-size:12px;color:#4A5759;">'
            f'{pid[:40]}{"…" if len(pid)>40 else ""} '
            f'<span style="color:#84A59D;">· {_meta.get(pid, {}).get("date", "")}</span>'            f'</div>'
            for i, pid in enumerate(_sel)
        )}
        <div style="font-size:12px;color:#84A59D;margin-top:10px;">{_hint}</div>
    </div>
    """, unsafe_allow_html=True)
