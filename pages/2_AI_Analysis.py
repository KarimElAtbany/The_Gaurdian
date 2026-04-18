import streamlit as st
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))

from utils.ndvi_pipeline import NDVIPipeline
from utils.yolo_pipeline import YOLOPipeline
from utils.translations import t, inject_rtl, lang_toggle, render_nav
import json
import cv2
import numpy as np


def find_model():
    models_dir = Path(__file__).parent.parent / "models"
    pts = list(models_dir.glob("*.pt"))
    return pts[0] if pts else None


import base64 as _b64

def _png_img(name, height=48):
    p = Path(__file__).parent.parent / "graphic" / name
    if p.exists():
        b64 = _b64.b64encode(p.read_bytes()).decode()
        return f'<img src="data:image/png;base64,{b64}" style="height:{height}px;width:auto;vertical-align:middle;">'
    return ''

st.set_page_config(page_title="AI Analysis — The Guardian", layout="wide")

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
        b64 = _b64.b64encode(svg.encode()).decode()
        filt = "filter:brightness(0) invert(1);" if invert else ""
        return f'<img src="data:image/svg+xml;base64,{b64}" style="height:{height}px;width:auto;{filt}">'
    return '<span style="font-size:2rem;">🌿</span>'

# ── Sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.markdown(f"""
<div class="sidebar-logo">{_svg_logo(44)}</div>
<div class="sidebar-eco">Eco Team</div>
""", unsafe_allow_html=True)

lang = lang_toggle("ai")
render_nav(lang)
inject_rtl(lang)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="guardian-header">
    {_svg_logo(52)}
    <div class="guardian-header-text">
        <div class="title">The Guardian</div>
        <div class="subtitle">{t("header_sub_ai", lang)}</div>
        <div class="eco-badge">{t("eco_badge", lang)}</div>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown(f'<div class="g-section-title">{_png_img("ai.png", 22)} {t("section_ai", lang)}</div>',
            unsafe_allow_html=True)

ndvi_tab, detection_tab, iot_tab = st.tabs([
    t("tab_ndvi", lang), t("tab_detection", lang), t("tab_iot", lang)
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — NDVI Vegetation Health
# ══════════════════════════════════════════════════════════════════════════════
with ndvi_tab:
    _dir   = "rtl" if lang == "ar" else "ltr"
    _align = "right" if lang == "ar" else "left"
    if not st.session_state.get('downloaded_bands'):
        st.markdown(
            f'<div style="background:#e8f4f8;color:#0c5460;border:1px solid #bee5eb;'
            f'border-radius:8px;padding:14px 18px;font-size:14px;'
            f'direction:{_dir};text-align:{_align};">'
            f'{t("no_downloaded", lang)}</div>',
            unsafe_allow_html=True
        )
    else:
        with st.sidebar:
            st.subheader(t("sidebar_satellite", lang))
            ndvi_product_id = st.selectbox(
                t("select_image", lang),
                list(st.session_state.downloaded_bands.keys()),
                key="ndvi_product"
            )
            st.divider()
            st.subheader(t("sidebar_farm_area", lang))
            use_bbox = st.checkbox(t("use_drawn_area", lang), value=True)
            if not use_bbox:
                geojson_text = st.text_area(t("paste_geojson", lang), height=120)
            else:
                if st.session_state.get('bbox'):
                    st.success(t("area_from_map", lang))
                else:
                    st.warning(t("no_area_drawn", lang))

            with st.expander(t("advanced_settings", lang)):
                st.caption(t("sensitivity_thresh", lang))
                t1 = st.slider(t("no_veg_threshold",   lang), 0.0, 0.5, 0.20, 0.01)
                t2 = st.slider(t("critical_threshold",  lang), 0.0, 0.7, 0.40, 0.01)
                t3 = st.slider(t("moderate_threshold",  lang), 0.0, 0.9, 0.50, 0.01)
                st.caption(t("indicator_weights", lang))
                w_msavi = st.slider(t("weight_msavi", lang), 0.0, 1.0, 0.20, 0.05, key="w_msavi")
                w_ndre  = st.slider(t("weight_ndre",  lang), 0.0, 1.0, 0.35, 0.05, key="w_ndre")
                w_ndwi  = st.slider(t("weight_ndwi",  lang), 0.0, 1.0, 0.30, 0.05, key="w_ndwi")
                w_cire  = st.slider(t("weight_cire",  lang), 0.0, 1.0, 0.15, 0.05, key="w_cire")

        if st.button(t("run_analysis_btn", lang), type="primary"):
            bands = st.session_state.downloaded_bands[ndvi_product_id]

            if use_bbox and st.session_state.get('bbox'):
                bbox = st.session_state.bbox
                geojson = {
                    "type": "Polygon",
                    "coordinates": [[
                        [bbox[0], bbox[1]], [bbox[0], bbox[3]],
                        [bbox[2], bbox[3]], [bbox[2], bbox[1]],
                        [bbox[0], bbox[1]]
                    ]]
                }
            elif not use_bbox and geojson_text:
                geojson = json.loads(geojson_text)
            else:
                st.error(t("provide_aoi", lang))
                st.stop()

            with st.spinner(t("computing_analysis", lang)):
                pipeline = NDVIPipeline(thresholds=(t1, t2, t3))
                pipeline.INDEX_WEIGHTS = {
                    "MSAVI": w_msavi, "NDRE": w_ndre,
                    "NDWI":  w_ndwi,  "CIre": w_cire,
                }

                bands_paths = {k: bands.get(k) for k in ['B04', 'B05', 'B07', 'B08', 'B8A', 'B11']}
                bands_paths = {k: v for k, v in bands_paths.items() if v is not None}

                loaded_bands, transform, profile, pixel_size_m = pipeline.crop_and_load_bands(
                    bands_paths, geojson
                )

                indices    = pipeline.compute_indices(loaded_bands)
                composite  = pipeline.compute_composite(indices)
                health_map = pipeline.classify_health(composite)
                pixel_area_km2 = (pixel_size_m / 1000) ** 2
                stats, total_area, composite_mean = pipeline.compute_statistics(
                    health_map, composite, pixel_area_km2
                )

                true_color_rgb = None
                if all(b in bands for b in ['B02', 'B03', 'B04']):
                    try:
                        true_color_rgb = pipeline.crop_rgb_to_aoi(
                            bands['B02'], bands['B03'], bands['B04'], geojson
                        )
                    except Exception:
                        true_color_rgb = None

                fig = pipeline.create_visualization(
                    health_map, indices, stats, total_area,
                    true_color_rgb=true_color_rgb, composite=composite
                )

                st.session_state.ndvi_results = {
                    'health_map':     health_map,
                    'indices':        indices,
                    'composite':      composite,
                    'composite_mean': composite_mean,
                    'stats':          stats,
                    'total_area':     total_area,
                    'transform':      transform,
                }
                st.session_state.health_plot       = fig
                st.session_state.true_color_rgb    = true_color_rgb
                st.session_state.vegetation_cover  = sum(stats[i]['pct'] for i in [1, 2, 3])
                st.session_state.composite_health  = round(composite_mean * 100, 1)
                st.session_state.ndvi_product_id   = ndvi_product_id

                st.success(t("analysis_complete", lang))

        if 'ndvi_results' in st.session_state:
            st.divider()

            results   = st.session_state.ndvi_results
            stats     = results['stats']
            indices   = results.get('indices', {})
            score     = results['composite_mean']
            score_pct = int(score * 100)

            if score_pct >= 60:
                status_cls, status_lbl, status_emoji = "g-status-healthy",  t("status_good", lang), "✅"
            elif score_pct >= 40:
                status_cls, status_lbl, status_emoji = "g-status-moderate", t("status_fair", lang), "⚠️"
            else:
                status_cls, status_lbl, status_emoji = "g-status-critical", t("status_poor", lang), "🚨"

            st.markdown(f"""
            <div style="text-align:center;padding:20px 0 8px;">
                <div style="font-size:13px;font-weight:600;color:#8fb8a0;text-transform:uppercase;
                            letter-spacing:0.8px;margin-bottom:10px;">{t("overall_veg_health", lang)}</div>
                <div style="font-size:64px;font-weight:800;color:#4dcc6e;line-height:1;">{score_pct}%</div>
                <div style="margin-top:10px;">
                    <span class="g-status {status_cls}">{status_emoji} {status_lbl}</span>
                </div>
                <div style="font-size:12px;color:#6a9e7f;margin-top:8px;">
                    {t("based_on_4", lang)}
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.divider()

            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.markdown(f"""<div class="g-card">
                    <div class="g-card-icon">{_png_img("vegetation.png", 32)}</div>
                    <div class="g-card-value">{st.session_state.get('vegetation_cover', 0):.0f}%</div>
                    <div class="g-card-label">{t("veg_cover_lbl", lang)}</div>
                    <div class="g-card-desc">{t("veg_cover_desc", lang)}</div>
                </div>""", unsafe_allow_html=True)
            with c2:
                st.markdown(f"""<div class="g-card">
                    <div class="g-card-icon">{_png_img("healthy.png", 32)}</div>
                    <div class="g-card-value">{stats[3]['pct']:.0f}%</div>
                    <div class="g-card-label">{t("healthy_area_lbl", lang)}</div>
                    <div class="g-card-desc">{stats[3]['area_km2']:.2f} km²</div>
                </div>""", unsafe_allow_html=True)
            with c3:
                stressed      = stats[1]['pct'] + stats[2]['pct']
                stressed_area = stats[1]['area_km2'] + stats[2]['area_km2']
                st.markdown(f"""<div class="g-card">
                    <div class="g-card-icon">{_png_img("result.png", 32)}</div>
                    <div class="g-card-value">{stressed:.0f}%</div>
                    <div class="g-card-label">{t("stressed_area_lbl", lang)}</div>
                    <div class="g-card-desc">{stressed_area:.2f} km² — {t("stressed_area_desc", lang)}</div>
                </div>""", unsafe_allow_html=True)
            with c4:
                st.markdown(f"""<div class="g-card">
                    <div class="g-card-icon">{_png_img("nodata.png", 32)}</div>
                    <div class="g-card-value">{stats[0]['pct']:.0f}%</div>
                    <div class="g-card-label">{t("no_veg_lbl", lang)}</div>
                    <div class="g-card-desc">{stats[0]['area_km2']:.2f} km² — {t("no_veg_desc", lang)}</div>
                </div>""", unsafe_allow_html=True)

            st.divider()

            col_left, col_right = st.columns([3, 2])

            with col_left:
                st.markdown(f'<div class="g-section-title">{_png_img("map.png", 20)} {t("health_map_title", lang)}</div>',
                            unsafe_allow_html=True)
                st.pyplot(st.session_state.health_plot)

            with col_right:
                st.markdown(f'<div class="g-section-title">{_png_img("ai.png", 20)} {t("what_measured", lang)}</div>',
                            unsafe_allow_html=True)

                index_info = {
                    "MSAVI": ('<i class="ti ti-plant-2"></i>',    t("index_msavi_name", lang), t("index_msavi_desc", lang)),
                    "NDRE":  ('<i class="ti ti-leaf"></i>',        t("index_ndre_name",  lang), t("index_ndre_desc",  lang)),
                    "NDWI":  ('<i class="ti ti-droplet"></i>',     t("index_ndwi_name",  lang), t("index_ndwi_desc",  lang)),
                    "CIre":  ('<i class="ti ti-test-pipe-2"></i>', t("index_cire_name",  lang), t("index_cire_desc",  lang)),
                }
                scale_ranges = {"MSAVI": (-0.1, 0.6), "NDRE": (-0.1, 0.5), "NDWI": (-0.3, 0.5), "CIre": (0, 1)}

                for name, arr in indices.items():
                    if arr is None:
                        continue
                    icon, friendly, desc = index_info.get(name, ("📊", name, ""))
                    raw_val = float(np.nanmean(arr))
                    vmin, vmax = scale_ranges.get(name, (-1, 1))
                    pct = int(max(0, min(100, (raw_val - vmin) / (vmax - vmin) * 100)))
                    bar_cls = "g-bar-healthy" if pct >= 60 else ("g-bar-moderate" if pct >= 35 else "g-bar-stress")
                    st.markdown(f"""
                    <div class="g-index-row">
                        <div class="g-index-icon">{icon}</div>
                        <div style="flex:1;min-width:0;">
                            <div class="g-index-name">{friendly}</div>
                            <div class="g-index-desc">{desc}</div>
                            <div class="g-bar-wrap" style="margin-top:6px;">
                                <div class="g-bar-fill {bar_cls}" style="width:{pct}%;"></div>
                            </div>
                        </div>
                        <div class="g-index-val">{pct}%</div>
                    </div>
                    """, unsafe_allow_html=True)

            # ── Recommendations ──────────────────────────────────────────────
            st.divider()
            st.markdown(f'<div class="g-section-title">{_png_img("result.png", 20)} {t("section_recs", lang)}</div>',
                        unsafe_allow_html=True)

            _recs = []
            if stats[0]['pct'] > 30:
                body = (f"{stats[0]['pct']:.0f}% " +
                        ("of the zone has no vegetation. Consider soil remediation or replanting."
                         if lang == "en" else
                         "من المنطقة لا يحتوي على نبات. يُنصح بإصلاح التربة أو إعادة الزراعة."))
                _recs.append(("🔴", t("rec_bare_title", lang), body))
            if stats[1]['pct'] > 20:
                body = (f"{stats[1]['pct']:.0f}% " +
                        ("of the area is critically stressed. Apply targeted irrigation and inspect for disease immediately."
                         if lang == "en" else
                         "من المنطقة تعاني إجهاداً حاداً. طبّق ريّاً موجّهاً وافحص علامات الأمراض فوراً."))
                _recs.append(("🚨", t("rec_severe_title", lang), body))
            if stats[2]['pct'] > 25:
                body = (f"{stats[2]['pct']:.0f}% " +
                        ("shows moderate stress. Review irrigation schedules and check nutrient levels."
                         if lang == "en" else
                         "تظهر إجهاداً متوسطاً. راجع جداول الري وافحص مستويات المغذيات."))
                _recs.append(("⚠️", t("rec_moderate_title", lang), body))
            if stats[3]['pct'] >= 60:
                body = (f"{stats[3]['pct']:.0f}% " +
                        ("of the area is in good condition. Maintain current practices and schedule a 30-day follow-up scan."
                         if lang == "en" else
                         "من المنطقة في حالة جيدة. حافظ على الممارسات الحالية وجدوِل مسحاً متابعاً بعد 30 يوماً."))
                _recs.append(("✅", t("rec_healthy_title", lang), body))
            elif stats[3]['pct'] >= 40:
                _recs.append(("⚠️", t("rec_declining_title", lang), t("rec_declining_body", lang)))
            else:
                _recs.append(("🚨", t("rec_poor_title", lang), t("rec_poor_body", lang)))

            _recs.append(("📋", t("rec_detect_title", lang), t("rec_detect_body", lang)))

            for _emoji, _title, _body in _recs:
                st.markdown(f"""
                <div class="g-rec" style="margin-bottom:10px;">
                    <div class="g-rec-icon" style="font-size:20px;">{_emoji}</div>
                    <div><strong style="color:#4A5759;">{_title}</strong><br>
                    <span style="font-size:13px;color:#84A59D;">{_body}</span></div>
                </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — Well Consumption (IoT)  — must come before detection_tab (which has st.stop())
# ══════════════════════════════════════════════════════════════════════════════
with iot_tab:
    _dir    = "rtl" if lang == "ar" else "ltr"
    _align  = "right" if lang == "ar" else "left"
    _ul_pad = "padding-right:20px;padding-left:0;" if lang == "ar" else "padding-left:20px;padding-right:0;"

    iot_dir  = Path(__file__).parent.parent / "iot"
    img_name = "ar_blr.png" if lang == "ar" else "en_blr.png"
    img_path = iot_dir / img_name

    if img_path.exists():
        st.image(str(img_path), width="stretch")
    else:
        st.warning(f"Image not found: iot/{img_name}")

    st.markdown("<br>", unsafe_allow_html=True)

    iot_analysis_title = t("iot_analysis_title", lang)
    iot_b1 = t("iot_bullet1", lang)
    iot_b2 = t("iot_bullet2", lang)
    iot_b3 = t("iot_bullet3", lang)
    st.markdown(
        f'<div style="background:#EAF4F7;border-left:4px solid #219EBC;border-radius:8px;'
        f'padding:18px 20px;margin-bottom:16px;direction:{_dir};text-align:{_align};">'
        f'<div style="font-weight:700;font-size:15px;color:#219EBC;margin-bottom:10px;'
        f'direction:{_dir};text-align:{_align};">{iot_analysis_title}</div>'
        f'<ul style="margin:0;{_ul_pad}color:#2C3A3C;font-size:14px;line-height:1.8;">'
        f'<li style="direction:{_dir};text-align:{_align};">{iot_b1}</li>'
        f'<li style="direction:{_dir};text-align:{_align};">{iot_b2}</li>'
        f'<li style="direction:{_dir};text-align:{_align};">{iot_b3}</li>'
        f'</ul></div>',
        unsafe_allow_html=True
    )

    iot_irr_title = t("iot_irr_title", lang)
    iot_irr_body  = t("iot_irr_body", lang)
    st.markdown(
        f'<div style="background:#F0FDF4;border-left:4px solid #1a9850;border-radius:8px;'
        f'padding:18px 20px;margin-bottom:16px;direction:{_dir};text-align:{_align};">'
        f'<div style="font-weight:700;font-size:15px;color:#1a9850;margin-bottom:8px;'
        f'direction:{_dir};text-align:{_align};">{iot_irr_title}</div>'
        f'<div style="color:#2C3A3C;font-size:14px;line-height:1.8;'
        f'direction:{_dir};text-align:{_align};">{iot_irr_body}</div>'
        f'</div>',
        unsafe_allow_html=True
    )

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — Tree Detection
# ══════════════════════════════════════════════════════════════════════════════
with detection_tab:
    with st.sidebar:
        st.subheader(t("detection_settings", lang))
        model_file = find_model()
        if model_file:
            st.success(t("model_ready", lang))
        else:
            st.error(t("no_model", lang))

        conf_threshold = st.slider(
            t("conf_thresh_lbl", lang), 0.0, 1.0, 0.1, 0.05, key="conf_thresh",
            help=t("conf_thresh_help", lang)
        )

    st.markdown(
        f'<div class="g-section-title">{_png_img("palm.png", 22)} {t("section_palm_census", lang)}</div>',
        unsafe_allow_html=True
    )
    _dir   = "rtl" if lang == "ar" else "ltr"
    _align = "right" if lang == "ar" else "left"
    st.markdown(f"""
    <div style="background:#EAF4F7;border:1px solid #bee5eb;border-radius:8px;
                padding:12px 16px;font-size:13px;color:#0c5460;margin-bottom:14px;
                direction:{_dir};text-align:{_align};">
        🛰️ <strong>{t("highres_title", lang)}</strong> — {t("highres_body", lang)}
    </div>""", unsafe_allow_html=True)

    # ── IMPORTANT zoom note ──────────────────────────────────────────────────
    _zoom_en = (
        "For best palm tree detection results, draw the smallest possible area around "
        "your target palms on the map — the smaller the AOI, the higher the zoom level "
        "the camera will use, and the clearer the individual tree crowns will appear in "
        "the captured image. A very large AOI will result in low zoom and poor detection accuracy."
    )
    _zoom_ar = (
        "للحصول على أفضل نتائج كشف النخيل، ارسم أصغر منطقة ممكنة حول النخيل المستهدف على الخريطة — "
        "كلما صغرت المنطقة، ارتفع مستوى التكبير وظهرت تيجان الأشجار الفردية بوضوح أكبر في الصورة الملتقطة. "
        "المنطقة الكبيرة جداً تؤدي إلى تكبير منخفض ودقة كشف ضعيفة."
    )
    st.markdown(f"""
    <div style="background:#fff8e1;border:2px solid #f59e0b;border-radius:10px;
                padding:14px 18px;font-size:13px;color:#78350f;margin-bottom:16px;
                direction:{_dir};text-align:{_align};">
        <strong style="font-size:14px;">
            {"⚠️ Important — Draw a small AOI for maximum zoom" if lang == "en" else "⚠️ مهم — ارسم منطقة صغيرة للحصول على أقصى تكبير"}
        </strong><br><br>
        {_zoom_en if lang == "en" else _zoom_ar}
    </div>""", unsafe_allow_html=True)

    if not st.session_state.get('bbox'):
        st.markdown(
            f'<div style="background:#e8f4f8;color:#0c5460;border:1px solid #bee5eb;'
            f'border-radius:8px;padding:14px 18px;font-size:14px;'
            f'direction:{_dir};text-align:{_align};">'
            f'{t("no_area_selected", lang)}</div>',
            unsafe_allow_html=True
        )
        st.stop()

    if not model_file:
        st.error(t("no_model_error", lang))
        st.stop()

    bbox = st.session_state.bbox
    st.info(f"AOI: {bbox[0]:.4f}°, {bbox[1]:.4f}° → {bbox[2]:.4f}°, {bbox[3]:.4f}°")

    if st.button(t("acquire_btn", lang), type="primary"):
        from utils.google_maps_capture import bbox_to_dims, capture_google_maps

        processed_dir = Path("data/processed")
        processed_dir.mkdir(parents=True, exist_ok=True)

        center_lat, center_lon, width_km, height_km = bbox_to_dims(bbox)

        with st.spinner(t("capturing_spinner", lang)):
            try:
                capture_path = processed_dir / "gmaps_capture.png"
                capture_path, zoom = capture_google_maps(
                    center_lat, center_lon, width_km, height_km,
                    output_path=capture_path
                )
                st.success(
                    f"{'Satellite image acquired at zoom level' if lang == 'en' else 'تم التقاط الصورة عند مستوى التكبير'} "
                    f"{zoom}  ·  {'Coverage' if lang == 'en' else 'التغطية'}: "
                    f"{width_km:.2f} km × {height_km:.2f} km"
                )
            except (ImportError, RuntimeError) as e:
                st.error(str(e))
                st.stop()
            except Exception as e:
                st.error(f"Capture failed: {e}")
                st.stop()

        from PIL import Image as PILImage
        pil_img  = PILImage.open(capture_path).convert("RGB")
        img_rgb  = np.array(pil_img)
        img_bgr  = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
        cropped_path = processed_dir / "gmaps_capture.jpg"
        cv2.imwrite(str(cropped_path), img_bgr)

        # ── Logo watermark helper ─────────────────────────────────────────────
        def _stamp_logo(img_array_rgb):
            """Stamp the Guardian logo at the bottom-left of an RGB numpy array."""
            from PIL import Image as _PIL
            logo_p = Path(__file__).parent.parent / "graphic" / "logo.png"
            if not logo_p.exists():
                return img_array_rgb
            base = _PIL.fromarray(img_array_rgb).convert("RGBA")
            W, H = base.size
            logo_size = max(40, int(min(W, H) * 0.10))
            logo = _PIL.open(str(logo_p)).convert("RGBA").resize(
                (logo_size, logo_size), _PIL.LANCZOS
            )
            pad = int(logo_size * 0.15)
            pos = (pad, H - logo_size - pad)
            layer = _PIL.new("RGBA", base.size, (0, 0, 0, 0))
            layer.paste(logo, pos, logo)
            out = _PIL.alpha_composite(base, layer)
            return np.array(out.convert("RGB"))

        col_prev1, col_prev2 = st.columns(2)
        with col_prev1:
            st.caption(t("caption_aoi", lang))
            st.image(_stamp_logo(img_rgb), width="stretch")

        # ── Choose detection mode based on captured image size ────────────────
        from utils.yolo_pipeline import TILE_THRESH
        W_img, H_img = pil_img.size
        use_tiling   = max(W_img, H_img) > TILE_THRESH

        if use_tiling:
            spin_msg = (f"Large AOI detected — running tiled detection ({W_img}×{H_img}px)…"
                        if lang == "en" else
                        f"منطقة كبيرة — تشغيل الكشف المقسَّم ({W_img}×{H_img}px)…")
        else:
            spin_msg = t("running_detection", lang)

        with st.spinner(spin_msg):
            try:
                pipeline = YOLOPipeline(str(model_file))
                if use_tiling:
                    merged_boxes = pipeline.detect_tiled(cropped_path, conf_threshold)
                    annotated    = pipeline.annotate_tiled(cropped_path, merged_boxes)
                    class_counts = {}
                    for box in merged_boxes:
                        cls = int(box[4])
                        class_counts[cls] = class_counts.get(cls, 0) + 1
                    n = len(merged_boxes)
                else:
                    results      = pipeline.detect(cropped_path, conf_threshold)
                    annotated    = pipeline.annotate_image(cropped_path, results)
                    class_counts = {}
                    for box in results.boxes:
                        cls = int(box.cls[0])
                        class_counts[cls] = class_counts.get(cls, 0) + 1
                    n = len(results.boxes)
            except Exception as e:
                st.error(f"Detection failed: {e}")
                st.stop()

        with col_prev2:
            st.caption(t("caption_detections", lang))
            st.image(_stamp_logo(cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)), width="stretch")

        if use_tiling:
            from utils.yolo_pipeline import TILE_SIZE, TILE_OVERLAP
            n_tiles_w = max(1, (W_img - TILE_SIZE) // int(TILE_SIZE * (1 - TILE_OVERLAP)) + 1)
            n_tiles_h = max(1, (H_img - TILE_SIZE) // int(TILE_SIZE * (1 - TILE_OVERLAP)) + 1)
            tile_info = (
                f"ℹ️ Tiled detection — image split into {n_tiles_w}×{n_tiles_h} "
                f"overlapping {TILE_SIZE}px tiles with {int(TILE_OVERLAP*100)}% overlap. "
                f"Duplicate detections removed via NMS."
                if lang == "en" else
                f"ℹ️ كشف مقسَّم — تم تقسيم الصورة إلى {n_tiles_w}×{n_tiles_h} "
                f"مقاطع متداخلة بحجم {TILE_SIZE}px مع تداخل {int(TILE_OVERLAP*100)}٪. "
                f"تمت إزالة التكرارات عبر NMS."
            )
            st.info(tile_info)

        st.session_state.class_counts   = class_counts
        st.session_state.palm_census    = sum(class_counts.values())
        st.session_state.yolo_annotated = annotated

        msg = (f"✅ {n:,} palm trees identified within the area of interest"
               if lang == "en" else
               f"✅ تم تحديد {n:,} نخلة داخل منطقة الاهتمام")
        st.success(msg)

    if 'class_counts' in st.session_state:
        st.divider()
        counts = st.session_state.class_counts
        total  = sum(counts.values())

        st.markdown(
            f'<div class="g-section-title">{_png_img("palm.png", 20)} {t("section_census", lang)}</div>',
            unsafe_allow_html=True
        )

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f"""<div class="g-card" style="text-align:center;">
                <div class="g-card-icon">{_png_img("palm.png", 32)}</div>
                <div class="g-card-value">{total:,}</div>
                <div class="g-card-label">{t("total_palms_lbl", lang)}</div>
                <div class="g-card-desc">{t("total_palms_desc", lang)}</div>
            </div>""", unsafe_allow_html=True)
        with col2:
            pct_h = counts.get(1, 0) / total * 100 if total else 0
            st.markdown(f"""<div class="g-card" style="text-align:center;">
                <div class="g-card-icon">{_png_img("healthy.png", 32)}</div>
                <div class="g-card-value" style="color:#16a34a;">{counts.get(1, 0):,}</div>
                <div class="g-card-label">{t("healthy_lbl", lang)}</div>
                <div class="g-card-desc">{pct_h:.0f}% {t("of_detected_palms", lang).lstrip('%').strip()}</div>
            </div>""", unsafe_allow_html=True)
        with col3:
            pct_s = counts.get(2, 0) / total * 100 if total else 0
            st.markdown(f"""<div class="g-card" style="text-align:center;">
                <div class="g-card-icon">{_png_img("result.png", 32)}</div>
                <div class="g-card-value" style="color:#d97706;">{counts.get(2, 0):,}</div>
                <div class="g-card-label">{t("early_stress_lbl", lang)}</div>
                <div class="g-card-desc">{pct_s:.0f}% — {t("early_stress_desc", lang)}</div>
            </div>""", unsafe_allow_html=True)
        with col4:
            pct_u = counts.get(0, 0) / total * 100 if total else 0
            st.markdown(f"""<div class="g-card" style="text-align:center;">
                <div class="g-card-icon">{_png_img("nodata.png", 32)}</div>
                <div class="g-card-value" style="color:#dc2626;">{counts.get(0, 0):,}</div>
                <div class="g-card-label">{t("critical_lbl", lang)}</div>
                <div class="g-card-desc">{pct_u:.0f}% — {t("critical_desc", lang)}</div>
            </div>""", unsafe_allow_html=True)
