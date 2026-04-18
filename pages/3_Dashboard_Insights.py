import streamlit as st
from pathlib import Path
import sys
import base64
sys.path.append(str(Path(__file__).parent.parent))

import cv2
import io
import json
import zipfile
import csv
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from datetime import datetime

from utils.translations import t, inject_rtl, lang_toggle, render_nav

st.set_page_config(page_title="Dashboard — The Guardian", layout="wide")

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

def _png_img(name, height=36):
    p = Path(__file__).parent.parent / "graphic" / name
    if p.exists():
        b64 = base64.b64encode(p.read_bytes()).decode()
        return f'<img src="data:image/png;base64,{b64}" style="height:{height}px;width:auto;">'
    return ''

# ── Sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.markdown(f"""
<div class="sidebar-logo">{_svg_logo(44)}</div>
<div class="sidebar-eco">Eco Team</div>
""", unsafe_allow_html=True)

lang = lang_toggle("dash")
render_nav(lang)
inject_rtl(lang)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="guardian-header">
    {_svg_logo(52)}
    <div class="guardian-header-text">
        <div class="title">The Guardian</div>
        <div class="subtitle">{t("header_sub_dash", lang)}</div>
        <div class="eco-badge">{t("eco_badge", lang)}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── State ─────────────────────────────────────────────────────────────────────
has_ndvi      = 'ndvi_results' in st.session_state
has_detection = 'class_counts' in st.session_state

score_pct   = st.session_state.get('composite_health', 0)
veg_cover   = st.session_state.get('vegetation_cover', 0)
palm_census = st.session_state.get('palm_census', 0)
econ_yield  = st.session_state.get('economic_yield', '')

if score_pct >= 60:
    overall_cls, overall_lbl, overall_emoji = "g-status-healthy",  t("status_good",    lang), "✅"
elif score_pct >= 40:
    overall_cls, overall_lbl, overall_emoji = "g-status-moderate", t("status_fair",    lang), "⚠️"
elif score_pct > 0:
    overall_cls, overall_lbl, overall_emoji = "g-status-critical", t("status_poor",    lang), "🚨"
else:
    overall_cls, overall_lbl, overall_emoji = "g-status-unknown",  t("status_no_data", lang), " "

if econ_yield == "Positive":
    econ_cls, econ_emoji = "g-status-healthy",  "✅"
elif econ_yield == "Moderate":
    econ_cls, econ_emoji = "g-status-moderate", "⚠️"
elif econ_yield == "At Risk":
    econ_cls, econ_emoji = "g-status-critical", "🚨"
else:
    econ_cls, econ_emoji = "g-status-unknown",  ""

# Economic label — translate the stored English value
econ_display = {
    "Positive": t("status_good",    lang) if lang == "ar" else "Positive",
    "Moderate": t("status_fair",    lang) if lang == "ar" else "Moderate",
    "At Risk":  t("status_poor",    lang) if lang == "ar" else "At Risk",
}.get(econ_yield, "")

# ── Overall health score ──────────────────────────────────────────────────────
st.markdown(f"""
<div style="text-align:center;padding:28px 0 20px;">
    <div style="font-size:12px;font-weight:700;color:#84A59D;text-transform:uppercase;
                letter-spacing:1px;margin-bottom:12px;">{t("overall_health_lbl", lang)}</div>
    <div style="font-size:72px;font-weight:800;color:#219EBC;line-height:1;">{score_pct:.0f}%</div>
    <div style="margin-top:14px;">
        <span class="g-status {overall_cls}">{overall_emoji} {overall_lbl}</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ── KPI cards ─────────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f"""<div class="g-card">
        <div class="g-card-icon">{_png_img("vegetation.png")}</div>
        <div class="g-card-value">{veg_cover:.0f}%</div>
        <div class="g-card-label">{t("veg_cover_lbl", lang)}</div>
        <div class="g-card-desc">{t("veg_cover_desc", lang)}</div>
    </div>""", unsafe_allow_html=True)

with c2:
    st.markdown(f"""<div class="g-card">
        <div class="g-card-icon">{_png_img("palm.png")}</div>
        <div class="g-card-value">{palm_census:,}</div>
        <div class="g-card-label">{t("palms_counted_lbl", lang)}</div>
        <div class="g-card-desc">{t("palms_counted_desc", lang)}</div>
    </div>""", unsafe_allow_html=True)

with c3:
    healthy_pct  = st.session_state.ndvi_results['stats'][3]['pct'] if has_ndvi else 0
    healthy_area = st.session_state.ndvi_results['stats'][3]['area_km2'] if has_ndvi else 0
    st.markdown(f"""<div class="g-card">
        <div class="g-card-icon">{_png_img("healthy.png")}</div>
        <div class="g-card-value">{healthy_pct:.0f}%</div>
        <div class="g-card-label">{t("healthy_area_lbl", lang)}</div>
        <div class="g-card-desc">{healthy_area:.2f} km² {t("healthy_area_desc_d", lang)}</div>
    </div>""", unsafe_allow_html=True)

with c4:
    econ_val = (econ_emoji + " " + econ_display).strip() or "—"
    st.markdown(f"""<div class="g-card">
        <div class="g-card-icon">{_png_img("economic.png")}</div>
        <div class="g-card-value"><span class="g-status {econ_cls}" style="font-size:14px;">{econ_val}</span></div>
        <div class="g-card-label">{t("economic_outlook_lbl", lang)}</div>
        <div class="g-card-desc">{t("economic_outlook_desc", lang)}</div>
    </div>""", unsafe_allow_html=True)

st.divider()

# ── No-data state ─────────────────────────────────────────────────────────────
if not has_ndvi and not has_detection:
    st.markdown(f"""
    <div style="text-align:center;padding:40px;color:#6a9e7f;">
        <div style="margin-bottom:16px;">{_png_img("nodata.png", 64)}</div>
        <div style="font-size:18px;font-weight:600;color:#b8d4c4;">{t("no_analysis_title", lang)}</div>
        <div style="font-size:14px;margin-top:8px;">{t("no_analysis_body", lang)}</div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ── Maps ──────────────────────────────────────────────────────────────────────
if has_ndvi or has_detection:
    st.markdown(f'<div class="g-section-title"><i class="ti ti-map"></i> {t("maps_title", lang)}</div>',
                unsafe_allow_html=True)
    map_col, det_col = st.columns(2)

    with map_col:
        if has_ndvi and 'health_plot' in st.session_state:
            st.caption(t("veg_map_caption", lang))
            st.pyplot(st.session_state.health_plot, use_container_width=True)
        else:
            st.markdown(f"""
            <div style="background:rgba(33,158,188,0.04);border:1px dashed rgba(33,158,188,0.2);
                        border-radius:12px;padding:40px;text-align:center;color:#84A59D;">
                <i class="ti ti-plant-2" style="font-size:36px;color:#84A59D;"></i>
                <div style="margin-top:10px;font-size:13px;color:#84A59D;">{t("run_veg_health", lang)}</div>
            </div>
            """, unsafe_allow_html=True)

    with det_col:
        if has_detection and 'yolo_annotated' in st.session_state:
            counts   = st.session_state.class_counts
            annotated = st.session_state.yolo_annotated
            img_rgb  = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)
            total    = sum(counts.values())
            st.caption(f"{'Palm Census' if lang == 'en' else 'إحصاء النخيل'} — {total:,} {'trees identified' if lang == 'en' else 'نخلة تم تحديدها'}")
            st.image(img_rgb, width="stretch")
        else:
            st.markdown(f"""
            <div style="background:rgba(33,158,188,0.04);border:1px dashed rgba(33,158,188,0.2);
                        border-radius:12px;padding:40px;text-align:center;color:#84A59D;">
                <i class="ti ti-trees" style="font-size:36px;color:#84A59D;"></i>
                <div style="margin-top:10px;font-size:13px;color:#84A59D;">{t("run_tree_detect", lang)}</div>
            </div>
            """, unsafe_allow_html=True)

st.divider()

# ── Vegetation breakdown ──────────────────────────────────────────────────────
if has_ndvi:
    stats = st.session_state.ndvi_results['stats']
    st.markdown(f'<div class="g-section-title"><i class="ti ti-chart-bar"></i> {t("veg_breakdown_title", lang)}</div>',
                unsafe_allow_html=True)

    bar_data = [
        (stats[3]['pct'], stats[3]['area_km2'], t("bar_healthy",  lang), "g-bar-healthy",  "#16a34a"),
        (stats[2]['pct'], stats[2]['area_km2'], t("bar_moderate", lang), "g-bar-moderate", "#b45309"),
        (stats[1]['pct'], stats[1]['area_km2'], t("bar_critical", lang), "g-bar-stress",   "#dc2626"),
        (stats[0]['pct'], stats[0]['area_km2'], t("bar_no_veg",   lang), "g-bar-bare",     "#64748b"),
    ]

    for pct, area, label, bar_cls, color in bar_data:
        st.markdown(f"""
        <div style="margin-bottom:14px;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:5px;">
                <div style="font-size:13px;font-weight:600;color:#4A5759;">{label}</div>
                <div style="font-size:13px;color:#84A59D;">{pct:.1f}% &nbsp;·&nbsp; {area:.2f} km²</div>
            </div>
            <div class="g-bar-wrap">
                <div class="g-bar-fill {bar_cls}" style="width:{max(pct,1):.0f}%;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Farm Health Grade ─────────────────────────────────────────────────────
    if score_pct >= 60:
        grade, grade_color, grade_bg, grade_line = (
            "A", "#16a34a", "#dcfce7",
            ("Vegetation is dense and healthy — maintain current practices."
             if lang == "en" else
             "الغطاء النباتي كثيف وصحي — استمر في الممارسات الحالية.")
        )
    elif score_pct >= 40:
        grade, grade_color, grade_bg, grade_line = (
            "B", "#0e7490", "#e0f2fe",
            ("Overall health is good with some areas of moderate stress."
             if lang == "en" else
             "الصحة العامة جيدة مع بعض مناطق الإجهاد المتوسط.")
        )
    elif score_pct >= 20:
        grade, grade_color, grade_bg, grade_line = (
            "C", "#b45309", "#fef3c7",
            ("Significant stress detected — targeted intervention is recommended."
             if lang == "en" else
             "تم اكتشاف إجهاد ملحوظ — يُنصح بالتدخل الموجَّه.")
        )
    else:
        grade, grade_color, grade_bg, grade_line = (
            "D", "#dc2626", "#fee2e2",
            ("Farm is in critical condition — immediate action required."
             if lang == "en" else
             "المزرعة في حالة حرجة — يلزم اتخاذ إجراء فوري.")
        )

    grade_title = "Farm Health Grade" if lang == "en" else "درجة صحة المزرعة"
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:20px;background:{grade_bg};
                border-radius:12px;padding:16px 22px;margin:18px 0 10px;">
        <div style="font-size:52px;font-weight:900;color:{grade_color};line-height:1;
                    min-width:56px;text-align:center;">{grade}</div>
        <div>
            <div style="font-size:11px;font-weight:700;text-transform:uppercase;
                        letter-spacing:1px;color:{grade_color};margin-bottom:4px;">{grade_title}</div>
            <div style="font-size:14px;color:#4A5759;">{grade_line}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Per-Index Interpretation ──────────────────────────────────────────────
    import numpy as np
    indices = st.session_state.ndvi_results.get('indices', {})
    if indices:
        idx_title = "Vegetation Index Breakdown" if lang == "en" else "تفصيل مؤشرات النباتات"
        st.markdown(f'<div class="g-section-title" style="margin-top:18px;"><i class="ti ti-wave-sine"></i> {idx_title}</div>',
                    unsafe_allow_html=True)

        def _idx_interp(name, val):
            if name == "MSAVI":
                if val > 0.5:
                    return ("#16a34a",
                            f"MSAVI {val:.2f} — Dense vegetation cover detected." if lang == "en" else
                            f"MSAVI {val:.2f} — تم اكتشاف غطاء نباتي كثيف.")
                elif val > 0.2:
                    return ("#b45309",
                            f"MSAVI {val:.2f} — Moderate vegetation with some bare soil gaps." if lang == "en" else
                            f"MSAVI {val:.2f} — نباتات متوسطة مع بعض الفجوات في التربة.")
                else:
                    return ("#dc2626",
                            f"MSAVI {val:.2f} — Sparse vegetation — possible bare or degraded soil." if lang == "en" else
                            f"MSAVI {val:.2f} — نباتات متفرقة — تربة جرداء أو متدهورة محتملة.")
            elif name == "NDRE":
                if val > 0.3:
                    return ("#16a34a",
                            f"NDRE {val:.2f} — Strong chlorophyll content, leaf health is good." if lang == "en" else
                            f"NDRE {val:.2f} — محتوى كلوروفيل قوي، صحة الأوراق جيدة.")
                elif val > 0.1:
                    return ("#b45309",
                            f"NDRE {val:.2f} — Moderate chlorophyll — monitor for early nutrient deficiency." if lang == "en" else
                            f"NDRE {val:.2f} — كلوروفيل متوسط — راقب لنقص مبكر في العناصر الغذائية.")
                else:
                    return ("#dc2626",
                            f"NDRE {val:.2f} — Low chlorophyll — likely nutrient stress or disease." if lang == "en" else
                            f"NDRE {val:.2f} — كلوروفيل منخفض — إجهاد غذائي أو مرض محتمل.")
            elif name == "NDWI":
                if val < -0.3:
                    return ("#16a34a",
                            f"NDWI {val:.2f} — Good water content in vegetation." if lang == "en" else
                            f"NDWI {val:.2f} — محتوى ماء جيد في النباتات.")
                elif val < -0.1:
                    return ("#b45309",
                            f"NDWI {val:.2f} — Mild water stress detected — review irrigation schedule." if lang == "en" else
                            f"NDWI {val:.2f} — إجهاد مائي خفيف — راجع جدول الري.")
                else:
                    return ("#dc2626",
                            f"NDWI {val:.2f} — Significant water stress — irrigation adjustment needed." if lang == "en" else
                            f"NDWI {val:.2f} — إجهاد مائي ملحوظ — يلزم تعديل الري.")
            else:  # CIre
                if val > 1.5:
                    return ("#16a34a",
                            f"CIre {val:.2f} — High chlorophyll index, nutrient supply appears adequate." if lang == "en" else
                            f"CIre {val:.2f} — مؤشر كلوروفيل مرتفع، إمداد المغذيات يبدو كافياً.")
                elif val > 0.5:
                    return ("#b45309",
                            f"CIre {val:.2f} — Moderate nutrient availability — consider supplemental fertilization." if lang == "en" else
                            f"CIre {val:.2f} — توافر غذائي متوسط — فكر في التسميد التكميلي.")
                else:
                    return ("#dc2626",
                            f"CIre {val:.2f} — Low chlorophyll index — nutrient deficiency likely." if lang == "en" else
                            f"CIre {val:.2f} — مؤشر كلوروفيل منخفض — نقص في المغذيات على الأرجح.")

        idx_cols = st.columns(4)
        for col, name in zip(idx_cols, ["MSAVI", "NDRE", "NDWI", "CIre"]):
            arr = indices.get(name)
            if arr is not None:
                mean_val = float(np.nanmean(arr))
                dot_color, interp_text = _idx_interp(name, mean_val)
                bar_w = min(100, max(5, int((mean_val + 1) / 2 * 100)))
                with col:
                    st.markdown(f"""
                    <div class="g-card" style="padding:14px 16px;">
                        <div style="font-size:13px;font-weight:700;color:#4A5759;margin-bottom:8px;">{name}</div>
                        <div style="font-size:22px;font-weight:800;color:{dot_color};">{mean_val:.2f}</div>
                        <div style="background:#e2e8f0;border-radius:4px;height:5px;margin:8px 0;">
                            <div style="background:{dot_color};width:{bar_w}%;height:5px;border-radius:4px;"></div>
                        </div>
                        <div style="font-size:11px;color:#6b7280;line-height:1.4;">{interp_text}</div>
                    </div>
                    """, unsafe_allow_html=True)

# ── Tree health + economic outlook ────────────────────────────────────────────
if has_ndvi and has_detection:
    st.divider()
    counts = st.session_state.class_counts
    total  = sum(counts.values())

    st.markdown(f'<div class="g-section-title"><i class="ti ti-trees"></i> {t("tree_health_title", lang)}</div>',
                unsafe_allow_html=True)

    if total == 0:
        st.info("No trees detected yet — run AI Analysis first to see health statistics.")
    else:
        t1c, t2c, t3c = st.columns(3)
        with t1c:
            h = counts.get(1, 0)
            st.markdown(f"""<div class="g-card" style="text-align:center;">
                <div style="font-size:36px;font-weight:800;color:#4dcc6e;">{h}</div>
                <div class="g-card-label">{t("healthy_trees_lbl", lang)}</div>
                <div class="g-card-desc">{h/total*100:.0f}{t("of_detected_palms", lang)}</div>
            </div>""", unsafe_allow_html=True)
        with t2c:
            y = counts.get(2, 0)
            st.markdown(f"""<div class="g-card" style="text-align:center;">
                <div style="font-size:36px;font-weight:800;color:#ffb74d;">{y}</div>
                <div class="g-card-label">{t("early_stress_lbl_d", lang)}</div>
                <div class="g-card-desc">{y/total*100:.0f}{t("monitor_closely", lang)}</div>
            </div>""", unsafe_allow_html=True)
        with t3c:
            u = counts.get(0, 0)
            st.markdown(f"""<div class="g-card" style="text-align:center;">
                <div style="font-size:36px;font-weight:800;color:#ef5350;">{u}</div>
                <div class="g-card-label">{t("critical_lbl_d", lang)}</div>
                <div class="g-card-desc">{u/total*100:.0f}{t("urgent_intervention", lang)}</div>
            </div>""", unsafe_allow_html=True)

    health_ratio = counts.get(1, 0) / total if total > 0 else 0
    if health_ratio > 0.7:
        st.session_state.economic_yield = "Positive"
        st.success(f"**{t('econ_positive', lang)}** — {t('econ_positive_body', lang)}")
    elif health_ratio > 0.5:
        st.session_state.economic_yield = "Moderate"
        st.warning(f"**{t('econ_moderate', lang)}** — {t('econ_moderate_body', lang)}")
    else:
        st.session_state.economic_yield = "At Risk"
        st.error(f"**{t('econ_at_risk', lang)}** — {t('econ_at_risk_body', lang)}")

    # ── Palm Density & Cross-Analysis ─────────────────────────────────────────
    total_area_km2 = st.session_state.ndvi_results.get('total_area_km2', 0)
    if total_area_km2 > 0 and palm_census > 0:
        density = palm_census / total_area_km2
        density_lbl = "Palm Density" if lang == "en" else "كثافة النخيل"
        density_unit = "palms / km²" if lang == "en" else "نخلة / كم²"
        st.markdown(f"""
        <div style="background:#EAF4F7;border-radius:10px;padding:14px 20px;
                    margin:14px 0;display:flex;align-items:center;gap:18px;">
            <div style="font-size:32px;font-weight:800;color:#219EBC;">{density:.0f}</div>
            <div>
                <div style="font-size:12px;font-weight:700;color:#84A59D;text-transform:uppercase;
                            letter-spacing:1px;">{density_lbl}</div>
                <div style="font-size:13px;color:#4A5759;">{density_unit} &nbsp;·&nbsp; {total_area_km2:.2f} km² {("monitored area" if lang=="en" else "مساحة مراقبة")}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Cross-analysis alert
    stats = st.session_state.ndvi_results['stats']
    severe_veg_pct  = stats[1]['pct']
    critical_palm_n = counts.get(0, 0)
    critical_palm_pct = (critical_palm_n / total * 100) if total > 0 else 0
    if severe_veg_pct > 30 and critical_palm_pct > 20:
        alert_title = "High-Risk Alert — Combined Stress Detected" if lang == "en" else "تنبيه خطر مرتفع — إجهاد مزدوج تم اكتشافه"
        alert_body = (
            f"Vegetation analysis shows {severe_veg_pct:.0f}% of the area under severe stress, "
            f"while {critical_palm_pct:.0f}% of detected palms ({critical_palm_n} trees) are in critical condition. "
            f"This combination indicates a systemic problem — immediate field inspection and treatment are strongly advised."
            if lang == "en" else
            f"يُظهر تحليل النباتات أن {severe_veg_pct:.0f}% من المساحة تعاني من إجهاد شديد، "
            f"بينما {critical_palm_pct:.0f}% من النخيل المكتشف ({critical_palm_n} نخلة) في حالة حرجة. "
            f"هذا الجمع يُشير إلى مشكلة منهجية — يُنصح بشدة بالفحص الميداني الفوري والمعالجة."
        )
        st.markdown(f"""
        <div style="background:#fee2e2;border:2px solid #dc2626;border-radius:12px;
                    padding:16px 20px;margin:14px 0;">
            <div style="font-size:14px;font-weight:700;color:#991b1b;margin-bottom:6px;">
                🚨 {alert_title}
            </div>
            <div style="font-size:13px;color:#7f1d1d;line-height:1.6;">{alert_body}</div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()
    rec_title = "Priority Action Plan" if lang == "en" else "خطة العمل ذات الأولوية"
    st.markdown(f'<div class="g-section-title"><i class="ti ti-list-check"></i> {rec_title}</div>',
                unsafe_allow_html=True)

    rec_d1 = (f"Visit the {severe_veg_pct:.0f}% critical stress zones on the ground to confirm the cause."
              if lang == "en" else
              f"قم بزيارة مناطق الإجهاد الحرج ({severe_veg_pct:.0f}%) ميدانياً للتحقق من الأسباب.")
    rec_d3 = (f"Inspect the {counts.get(0,0)} critical-condition and {counts.get(2,0)} early-stress palms for disease or pests."
              if lang == "en" else
              f"افحص {counts.get(0,0)} نخلة حرجة و{counts.get(2,0)} نخلة مجهدة بحثاً عن الأمراض والآفات.")

    # Each entry: (severity 1-3, icon, title, body)
    rec_entries = [
        (3 if severe_veg_pct > 30 else 2,
         "ti-zoom-scan", ("Ground-Truth Field Inspection" if lang == "en" else "الفحص الميداني"), rec_d1),
        (3 if counts.get(0, 0) > 0 else 2,
         "ti-trees", ("Inspect Critical Palms" if lang == "en" else "فحص النخيل الحرج"), rec_d3),
        (2,
         "ti-droplet-half-2", ("Irrigation & Nutrients" if lang == "en" else "الري والتغذية"), t("rec_d2", lang)),
        (1,
         "ti-calendar-event", ("Schedule Preventive Treatments" if lang == "en" else "جدولة العلاجات الوقائية"), t("rec_d4", lang)),
        (1,
         "ti-file-report", ("Document & Report Findings" if lang == "en" else "توثيق النتائج والإبلاغ عنها"), t("rec_d5", lang)),
    ]
    rec_entries.sort(key=lambda x: x[0], reverse=True)

    _priority_meta = {
        3: ("#dc2626", "#fee2e2", ("High Priority" if lang == "en" else "أولوية عالية")),
        2: ("#b45309", "#fef3c7", ("Medium Priority" if lang == "en" else "أولوية متوسطة")),
        1: ("#0e7490", "#e0f2fe", ("Low Priority" if lang == "en" else "أولوية منخفضة")),
    }

    for rank, (sev, icon, title, body) in enumerate(rec_entries, 1):
        p_color, p_bg, p_label = _priority_meta[sev]
        st.markdown(f"""
        <div class="g-rec" style="border-left:4px solid {p_color};background:{p_bg}20;">
            <div class="g-rec-icon"><i class="ti {icon}"></i></div>
            <div style="flex:1;">
                <div style="display:flex;align-items:center;gap:10px;margin-bottom:4px;">
                    <span style="font-weight:700;color:#4A5759;">{rank}. {title}</span>
                    <span style="font-size:10px;font-weight:700;color:{p_color};background:{p_bg};
                                 padding:2px 8px;border-radius:20px;border:1px solid {p_color}40;">
                        {p_label}
                    </span>
                </div>
                <div style="font-size:13px;color:#4A5759;">{body}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

elif has_ndvi and not has_detection:
    st.info(t("hint_tree_detect", lang))

elif has_detection and not has_ndvi:
    st.info(t("hint_veg_health", lang))

# ── Export ────────────────────────────────────────────────────────────────────
st.divider()
st.markdown(f'<div class="g-section-title"><i class="ti ti-download"></i> {t("section_export", lang)}</div>',
            unsafe_allow_html=True)

exp_col, zip_col = st.columns(2)

with exp_col:
    st.markdown(f"""
    <div class="g-card">
        <div class="g-card-icon"><i class="ti ti-file-type-pdf"></i></div>
        <div class="g-card-label">{t("pdf_lbl", lang)}</div>
        <div class="g-card-desc" style="margin-bottom:14px;">{t("pdf_desc", lang)}</div>
    </div>
    """, unsafe_allow_html=True)

    if st.button(t("generate_pdf_btn", lang), type="primary"):
        if not has_ndvi and not has_detection:
            st.error(t("run_analysis_first", lang))
        else:
            with st.spinner(t("building_report", lang)):
                try:
                    from utils.report_generator import generate_report
                    import matplotlib
                    matplotlib.use("Agg")

                    pdf_buf = generate_report(
                        product_id=st.session_state.get('ndvi_product_id') or
                                   st.session_state.get('current_product', 'Unknown'),
                        bbox=st.session_state.get('bbox'),
                        ndvi_results=st.session_state.get('ndvi_results'),
                        health_plot_fig=st.session_state.get('health_plot'),
                        true_color_rgb=st.session_state.get('true_color_rgb'),
                        class_counts=st.session_state.get('class_counts'),
                        yolo_annotated=st.session_state.get('yolo_annotated'),
                        economic_yield=st.session_state.get('economic_yield'),
                        lang=lang
                    )
                    report_name = f"guardian_report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
                    st.download_button(t("download_pdf_btn", lang), data=pdf_buf,
                                       file_name=report_name, mime="application/pdf")
                    st.success(t("report_ready", lang))
                except Exception as e:
                    st.error(f"Report generation failed: {e}")

with zip_col:
    st.markdown(f"""
    <div class="g-card">
        <div class="g-card-icon"><i class="ti ti-package-export"></i></div>
        <div class="g-card-label">{t("zip_lbl", lang)}</div>
        <div class="g-card-desc" style="margin-bottom:14px;">{t("zip_desc", lang)}</div>
    </div>
    """, unsafe_allow_html=True)

    if st.button(t("export_all_btn", lang)):
        if not has_ndvi and not has_detection:
            st.error(t("no_data_export", lang))
        else:
            with st.spinner(t("packaging_data", lang)):
                try:
                    zip_buf = io.BytesIO()
                    with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
                        if has_ndvi:
                            stats    = st.session_state.ndvi_results['stats']
                            ndvi_csv = io.StringIO()
                            writer   = csv.writer(ndvi_csv)
                            writer.writerow(["class_id", "label", "area_km2", "coverage_pct", "pixels"])
                            for cid, data in stats.items():
                                writer.writerow([cid, data['label'],
                                                 f"{data['area_km2']:.6f}",
                                                 f"{data['pct']:.4f}",
                                                 data['pixels']])
                            zf.writestr("health_statistics.csv", ndvi_csv.getvalue())

                            pid      = st.session_state.get('ndvi_product_id', 'unknown')
                            tif_path = Path("data/processed") / f"{pid}_health.tif"
                            if tif_path.exists():
                                zf.write(tif_path, f"{pid}_health.tif")

                        if has_detection:
                            counts  = st.session_state.class_counts
                            total   = sum(counts.values())
                            det_csv = io.StringIO()
                            writer  = csv.writer(det_csv)
                            writer.writerow(["label", "count", "proportion_pct"])
                            for cls, label in {0: "Critical Condition", 1: "Healthy", 2: "Early Stress"}.items():
                                count = counts.get(cls, 0)
                                pct   = (count / total * 100) if total > 0 else 0
                                writer.writerow([label, count, f"{pct:.2f}"])
                            writer.writerow(["TOTAL", total, "100.00"])
                            zf.writestr("tree_detection.csv", det_csv.getvalue())

                        meta = {
                            "generated_at":          datetime.now().isoformat(),
                            "product_id":            st.session_state.get('ndvi_product_id') or
                                                     st.session_state.get('current_product', 'Unknown'),
                            "bbox":                  st.session_state.get('bbox'),
                            "economic_yield":        st.session_state.get('economic_yield', ''),
                            "vegetation_cover_pct":  st.session_state.get('vegetation_cover', 0),
                            "composite_health_score":st.session_state.get('composite_health', 0),
                            "palm_census":           st.session_state.get('palm_census', 0),
                            "platform":              "The Guardian v2.0",
                        }
                        zf.writestr("metadata.json", json.dumps(meta, indent=2))

                    zip_buf.seek(0)
                    export_name = f"guardian_export_{datetime.now().strftime('%Y%m%d_%H%M')}.zip"
                    st.download_button(t("download_zip_btn", lang), data=zip_buf,
                                       file_name=export_name, mime="application/zip")
                    st.success(t("export_ready", lang))
                except Exception as e:
                    st.error(f"Export failed: {e}")

# ══════════════════════════════════════════════════════════════════════════════
# TIME SERIES COMPARISON
# Only visible when 2+ products are selected in Data Acquisition
# ══════════════════════════════════════════════════════════════════════════════
_sel      = st.session_state.get("selected_products", [])
_meta     = st.session_state.get("selected_products_meta", {})
_dloaded  = st.session_state.get("downloaded_bands", {})
_eligible = [pid for pid in _sel if pid in _dloaded]

if len(_eligible) >= 2:
    st.divider()
    _ts_title = "Time Series Comparison" if lang == "en" else "مقارنة السلاسل الزمنية"
    st.markdown(
        f'<div class="g-section-title"><i class="ti ti-timeline"></i> {_ts_title}</div>',
        unsafe_allow_html=True,
    )

    # ── Product queue display ─────────────────────────────────────────────────
    _rows_html = "".join(
        f'<span style="display:inline-flex;align-items:center;gap:6px;background:#EAF4F7;'
        f'border-radius:8px;padding:5px 12px;margin:3px 4px;font-size:12px;color:#4A5759;">'
        f'<b style="color:#219EBC;">{i+1}</b> {pid[:36]}{"…" if len(pid)>36 else ""} '
        f'<span style="color:#84A59D;">· {_meta.get(pid, {{}}).get("date","?")}</span></span>'
        for i, pid in enumerate(_eligible)
    )
    st.markdown(
        f'<div style="margin-bottom:14px;">{_rows_html}</div>',
        unsafe_allow_html=True,
    )

    _run_label = t("ts_run_btn", lang)
    _run_ts    = st.button(_run_label, type="primary", key="dash_run_ts")
    if "ts_results" not in st.session_state:
        st.session_state.ts_results = {}

    # ── Run analysis ──────────────────────────────────────────────────────────
    if _run_ts:
        _bbox = st.session_state.get("bbox")
        if not _bbox:
            st.error(t("ts_no_aoi", lang))
        else:
            from utils.ndvi_pipeline import NDVIPipeline as _NDVIP
            _geojson = {
                "type": "Polygon",
                "coordinates": [[
                    [_bbox[0], _bbox[1]], [_bbox[0], _bbox[3]],
                    [_bbox[2], _bbox[3]], [_bbox[2], _bbox[1]],
                    [_bbox[0], _bbox[1]],
                ]],
            }
            _ts_acc   = {}
            _prog     = st.progress(0.0)
            _stat_ph  = st.empty()
            _n_total  = len(_eligible)

            for _pi, _pid in enumerate(_eligible):
                _pdate = _meta.get(_pid, {}).get("date", "?")
                _stat_ph.info(
                    f"{t('ts_processing', lang)} {_pi+1} {t('ts_of', lang)} "
                    f"{_n_total}  —  {_pdate}"
                )
                _prog.progress(_pi / _n_total)
                _bands = _dloaded.get(_pid, {})
                _bpaths = {k: _bands.get(k) for k in
                           ["B04", "B05", "B07", "B08", "B8A", "B11"]
                           if _bands.get(k)}
                try:
                    _pl = _NDVIP()
                    _loaded, _tr, _pr, _psm = _pl.crop_and_load_bands(_bpaths, _geojson)
                    _idx  = _pl.compute_indices(_loaded)
                    _comp = _pl.compute_composite(_idx)
                    _hmap = _pl.classify_health(_comp)
                    _pkm2 = (_psm / 1000) ** 2
                    _st, _ta, _cm = _pl.compute_statistics(_hmap, _comp, _pkm2)
                    _ts_acc[_pid] = {"date": _pdate, "stats": _st,
                                     "composite_mean": _cm, "health_map": _hmap,
                                     "total_area": _ta}
                except Exception as _exc:
                    _stat_ph.warning(f"Skipped {_pid}: {_exc}")
                _prog.progress((_pi + 1) / _n_total)

            _prog.progress(1.0)
            _stat_ph.success(
                f"Done — {len(_ts_acc)} products processed."
                if lang == "en" else
                f"تم — تمت معالجة {len(_ts_acc)} منتج."
            )
            st.session_state.ts_results = _ts_acc

    # ── Show results ──────────────────────────────────────────────────────────
    _ts_res = st.session_state.get("ts_results", {})

    if len(_ts_res) >= 2:
        _sorted   = sorted(_ts_res.items(), key=lambda x: x[1]["date"])
        _dates    = [v["date"]                   for _, v in _sorted]
        _scores   = [v["composite_mean"] * 100   for _, v in _sorted]
        _hkms     = [v["stats"][3]["area_km2"]   for _, v in _sorted]
        _hpcts    = [v["stats"][3]["pct"]        for _, v in _sorted]
        _mpcts    = [v["stats"][2]["pct"]        for _, v in _sorted]
        _spcts    = [v["stats"][1]["pct"]        for _, v in _sorted]
        _bpcts    = [v["stats"][0]["pct"]        for _, v in _sorted]

        _PAL = {"bg":"#F7F9FA","accent":"#219EBC","text":"#4A5759","grid":"#DDE8E5",
                "H":"#16a34a","M":"#b45309","S":"#dc2626","B":"#94a3b8","sub":"#84A59D"}

        # ── Charts — original 2-column layout, bigger figures ────────────────
        _cc1, _cc2 = st.columns(2)

        with _cc1:
            st.markdown(f"**{t('ts_health_trend', lang)}**")
            _f1, _a1 = plt.subplots(figsize=(9, 5.5))
            _f1.patch.set_facecolor(_PAL["bg"]); _a1.set_facecolor(_PAL["bg"])
            _a1.plot(_dates, _scores, color=_PAL["accent"], linewidth=2.5,
                     marker="o", markersize=9, markerfacecolor="white",
                     markeredgecolor=_PAL["accent"], markeredgewidth=2.5, zorder=3)
            _a1.fill_between(_dates, _scores, alpha=0.10, color=_PAL["accent"])
            for _d, _s in zip(_dates, _scores):
                _a1.annotate(f"{_s:.0f}%", (_d, _s),
                             textcoords="offset points", xytext=(0, 11),
                             ha="center", fontsize=10, color=_PAL["accent"],
                             fontweight="bold")
            _a1.set_ylim(0, 115)
            _a1.set_ylabel("Health Score (%)", color=_PAL["text"], fontsize=11)
            _a1.tick_params(axis="x", rotation=25, labelsize=9, colors=_PAL["text"])
            _a1.tick_params(axis="y", labelsize=10, colors=_PAL["text"])
            _a1.grid(axis="y", alpha=0.35, color=_PAL["grid"])
            for _sp in _a1.spines.values(): _sp.set_edgecolor(_PAL["grid"])
            _a1.spines["top"].set_visible(False); _a1.spines["right"].set_visible(False)
            _f1.tight_layout()
            st.pyplot(_f1, use_container_width=True); plt.close(_f1)

        with _cc2:
            st.markdown(f"**{t('ts_veg_distribution', lang)}**")
            _f2, _a2 = plt.subplots(figsize=(9, 5.5))
            _f2.patch.set_facecolor(_PAL["bg"]); _a2.set_facecolor(_PAL["bg"])
            _x = list(range(len(_dates)))
            _a2.bar(_x, _hpcts, 0.6, color=_PAL["H"], alpha=0.88,
                    label="Healthy" if lang=="en" else "سليم")
            _a2.bar(_x, _mpcts, 0.6, bottom=_hpcts, color=_PAL["M"],
                    alpha=0.88, label="Moderate" if lang=="en" else "متوسط")
            _b3 = [a+b for a,b in zip(_hpcts, _mpcts)]
            _a2.bar(_x, _spcts, 0.6, bottom=_b3, color=_PAL["S"],
                    alpha=0.88, label="Severe" if lang=="en" else "حرج")
            _b4 = [a+b for a,b in zip(_b3, _spcts)]
            _a2.bar(_x, _bpcts, 0.6, bottom=_b4, color=_PAL["B"],
                    alpha=0.88, label="Bare" if lang=="en" else "جرداء")
            _a2.set_xticks(_x); _a2.set_xticklabels(_dates, rotation=25, ha="right",
                                                      fontsize=9, color=_PAL["text"])
            _a2.set_ylabel("Coverage (%)", color=_PAL["text"], fontsize=11)
            _a2.set_ylim(0, 115); _a2.tick_params(axis="y", labelsize=10, colors=_PAL["text"])
            _a2.legend(loc="upper right", fontsize=9, framealpha=0.75)
            for _sp in _a2.spines.values(): _sp.set_edgecolor(_PAL["grid"])
            _a2.spines["top"].set_visible(False); _a2.spines["right"].set_visible(False)
            _a2.grid(axis="y", alpha=0.3, color=_PAL["grid"])
            _f2.tight_layout()
            st.pyplot(_f2, use_container_width=True); plt.close(_f2)

        # ── Expansion cards ───────────────────────────────────────────────────
        _net   = _hkms[-1] - _hkms[0]
        _sdlt  = _scores[-1] - _scores[0]
        _tclr  = _PAL["H"] if _net > 0.05 else (_PAL["S"] if _net < -0.05 else _PAL["M"])
        _ticon = "▲" if _net > 0.05 else ("▼" if _net < -0.05 else "→")
        _tlbl  = (t("ts_trend_expanding",lang) if _net > 0.05 else
                  (t("ts_trend_degrading",lang) if _net < -0.05 else t("ts_trend_stable",lang)))

        _ec1, _ec2, _ec3 = st.columns(3)
        with _ec1:
            st.markdown(f"""<div class="g-card" style="text-align:center;">
                <div style="font-size:22px;font-weight:800;color:{_tclr};">{_ticon} {_tlbl}</div>
                <div class="g-card-label">{"Overall Trend" if lang=="en" else "الاتجاه العام"}</div>
                <div class="g-card-desc">{_dates[0]} → {_dates[-1]}</div>
            </div>""", unsafe_allow_html=True)
        with _ec2:
            _cs = f"{'+'if _net>=0 else ''}{_net:.2f} km²"
            st.markdown(f"""<div class="g-card" style="text-align:center;">
                <div style="font-size:22px;font-weight:800;color:{_tclr};">{_cs}</div>
                <div class="g-card-label">{t("ts_net_change", lang)}</div>
                <div class="g-card-desc">{_hkms[0]:.2f} → {_hkms[-1]:.2f} km²</div>
            </div>""", unsafe_allow_html=True)
        with _ec3:
            _ss = f"{'+'if _sdlt>=0 else ''}{_sdlt:.1f}%"
            _sc = _tclr if abs(_sdlt) > 2 else _PAL["sub"]
            st.markdown(f"""<div class="g-card" style="text-align:center;">
                <div style="font-size:22px;font-weight:800;color:{_sc};">{_ss}</div>
                <div class="g-card-label">{"Score Change" if lang=="en" else "تغير الدرجة"}</div>
                <div class="g-card-desc">{_scores[0]:.0f}% → {_scores[-1]:.0f}%</div>
            </div>""", unsafe_allow_html=True)

        # ── Change detection map ──────────────────────────────────────────────
        st.markdown(
            f'<div class="g-section-title" style="margin-top:18px;">'
            f'<i class="ti ti-map-2"></i> {t("ts_change_title", lang)}</div>',
            unsafe_allow_html=True,
        )

        _hf = _sorted[0][1]["health_map"].copy().astype(np.int16)
        _hl = _sorted[-1][1]["health_map"].copy().astype(np.int16)
        if _hf.shape != _hl.shape:
            _th, _tw = _hf.shape
            _hl = cv2.resize(_hl.astype(np.uint8), (_tw, _th),
                             interpolation=cv2.INTER_NEAREST).astype(np.int16)
        _nd   = (_hf == 255) | (_hl == 255)
        _delt = np.where(_nd, 0, _hl - _hf)
        _crgb = np.full((*_delt.shape, 3), 230, dtype=np.uint8)
        _crgb[_delt  > 0] = [22,163,74];  _crgb[_delt < 0] = [220,38,38]
        _crgb[_delt == 0] = [148,163,184]; _crgb[_nd]      = [235,235,235]

        def _cmap(hm):
            _pal = {0:[214,39,40],1:[253,174,97],2:[255,255,191],3:[26,152,80],255:[235,235,235]}
            _o = np.zeros((*hm.shape, 3), dtype=np.uint8)
            for _cid, _col in _pal.items(): _o[hm == _cid] = _col
            return _o

        _vld = (~_nd).sum()
        _imp = (_delt > 0).sum() / max(1, _vld) * 100
        _deg = (_delt < 0).sum() / max(1, _vld) * 100
        _stb = 100 - _imp - _deg

        _cm1, _cm2, _cm3 = st.columns(3)
        for _col, _hmap_data, _is_change in [
            (_cm1, _sorted[0][1], False),
            (_cm2, None, True),
            (_cm3, _sorted[-1][1], False),
        ]:
            with _col:
                if not _is_change:
                    _sc2 = _hmap_data["composite_mean"] * 100
                    st.caption(f"📅 {_hmap_data['date']}  —  {_sc2:.0f}%")
                    _mf, _ma = plt.subplots(figsize=(7, 7))
                    _mf.patch.set_facecolor(_PAL["bg"])
                    _ma.imshow(_cmap(_hmap_data["health_map"]))
                    _ma.set_title(_hmap_data["date"], fontsize=12, color=_PAL["text"])
                    _ma.axis("off"); _mf.tight_layout(pad=0.3)
                    st.pyplot(_mf, use_container_width=True); plt.close(_mf)
                else:
                    st.caption(
                        f"{'Change Map' if lang=='en' else 'خريطة التغيير'}  —  "
                        f"{t('ts_improved',lang)}: {_imp:.0f}%  "
                        f"{t('ts_degraded',lang)}: {_deg:.0f}%"
                    )
                    _mf2, _ma2 = plt.subplots(figsize=(7, 7))
                    _mf2.patch.set_facecolor(_PAL["bg"])
                    _ma2.imshow(_crgb)
                    _ma2.set_title(
                        f"{_sorted[0][1]['date']} → {_sorted[-1][1]['date']}",
                        fontsize=12, color=_PAL["text"]
                    )
                    _ma2.axis("off")
                    _ma2.legend(handles=[
                        mpatches.Patch(color=[c/255 for c in [22,163,74]],
                                       label=f"{t('ts_improved',lang)} ({_imp:.0f}%)"),
                        mpatches.Patch(color=[c/255 for c in [220,38,38]],
                                       label=f"{t('ts_degraded',lang)} ({_deg:.0f}%)"),
                        mpatches.Patch(color=[c/255 for c in [148,163,184]],
                                       label=f"{t('ts_stable',lang)} ({_stb:.0f}%)"),
                    ], loc="lower left", fontsize=10, framealpha=0.85)
                    _mf2.tight_layout(pad=0.3)
                    st.pyplot(_mf2, use_container_width=True); plt.close(_mf2)

        # ── Summary table ─────────────────────────────────────────────────────
        st.markdown(
            f'<div class="g-section-title" style="margin-top:18px;">'
            f'<i class="ti ti-table"></i> {t("ts_table_title", lang)}</div>',
            unsafe_allow_html=True,
        )
        _prev_sc = None; _trows = ""
        for _, _v in _sorted:
            _sc3 = _v["composite_mean"] * 100
            if _prev_sc is None: _arr, _ac = "—", _PAL["sub"]
            elif _sc3 > _prev_sc + 1: _arr, _ac = "▲", _PAL["H"]
            elif _sc3 < _prev_sc - 1: _arr, _ac = "▼", _PAL["S"]
            else: _arr, _ac = "→", _PAL["M"]
            _prev_sc = _sc3
            _trows += (
                f'<tr style="border-bottom:1px solid #EAF4F7;">'
                f'<td style="padding:9px 14px;">{_v["date"]}</td>'
                f'<td style="padding:9px 14px;font-weight:700;">'
                f'{_sc3:.1f}% <span style="color:{_ac}">{_arr}</span></td>'
                f'<td style="padding:9px 14px;color:{_PAL["H"]}">{_v["stats"][3]["area_km2"]:.2f}</td>'
                f'<td style="padding:9px 14px;color:{_PAL["M"]}">{_v["stats"][2]["area_km2"]:.2f}</td>'
                f'<td style="padding:9px 14px;color:{_PAL["S"]}">{_v["stats"][1]["area_km2"]:.2f}</td>'
                f'<td style="padding:9px 14px;color:{_PAL["B"]}">{_v["stats"][0]["area_km2"]:.2f}</td>'
                f'</tr>'
            )
        st.markdown(f"""
        <div style="overflow-x:auto;border-radius:10px;border:1px solid #DDE8E5;">
        <table style="width:100%;border-collapse:collapse;font-size:13px;color:#4A5759;">
          <thead><tr style="background:#219EBC;color:white;">
            <th style="padding:10px 14px;text-align:left;">{t("ts_date_col",lang)}</th>
            <th style="padding:10px 14px;text-align:left;">{t("ts_score_col",lang)}</th>
            <th style="padding:10px 14px;text-align:left;">{t("ts_healthy_col",lang)}</th>
            <th style="padding:10px 14px;text-align:left;">{t("ts_moderate_col",lang)}</th>
            <th style="padding:10px 14px;text-align:left;">{t("ts_severe_col",lang)}</th>
            <th style="padding:10px 14px;text-align:left;">{t("ts_bare_col",lang)}</th>
          </tr></thead>
          <tbody>{_trows}</tbody>
        </table></div>
        """, unsafe_allow_html=True)

        st.markdown("")
        if st.button(t("ts_clear_results", lang), key="dash_clear_ts"):
            st.session_state.ts_results = {}
            st.rerun()

    elif len(_ts_res) == 1:
        st.info(t("ts_one_product", lang))
