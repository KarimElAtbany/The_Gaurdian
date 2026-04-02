import streamlit as st
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent))

from utils.translations import t, inject_rtl, lang_toggle, render_nav

st.set_page_config(
    page_title="The Guardian — Eco Team",
    layout="wide",
    initial_sidebar_state="expanded"
)

def _load_styles():
    base = Path(__file__).parent
    for _css in [base / "assets/style.css", base / "assets/icons/tabler-local.css"]:
        if _css.exists():
            st.markdown(f"<style>{_css.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

_load_styles()

def _svg_logo(height=52, invert=True):
    svg_path = Path(__file__).parent / "graphic" / "logo.svg"
    if svg_path.exists():
        svg = svg_path.read_text(encoding='utf-8')
        import base64
        b64 = base64.b64encode(svg.encode()).decode()
        filt = "filter:brightness(0) invert(1);" if invert else ""
        return f'<img src="data:image/svg+xml;base64,{b64}" style="height:{height}px;width:auto;{filt}">'
    return '<span style="font-size:2rem;">🌿</span>'

def _png_img(name, height=48):
    import base64
    p = Path(__file__).parent / "graphic" / name
    if p.exists():
        b64 = base64.b64encode(p.read_bytes()).decode()
        return f'<img src="data:image/png;base64,{b64}" style="height:{height}px;width:auto;">'
    return ''

# ── Sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.markdown(f"""
<div class="sidebar-logo">{_svg_logo(44)}</div>
<div class="sidebar-eco">Eco Team</div>
""", unsafe_allow_html=True)

lang = lang_toggle("home")
render_nav(lang)
inject_rtl(lang)

st.sidebar.caption(t("sidebar_nav_hint", lang))

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="guardian-header">
    {_svg_logo(52)}
    <div class="guardian-header-text">
        <div class="title">The Guardian</div>
        <div class="subtitle">{t("header_sub_home", lang)}</div>
        <div class="eco-badge">{t("eco_badge", lang)}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Welcome ───────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="text-align:center;padding:36px 0 20px;">
    <div style="font-size:34px;font-weight:800;color:#4A5759;letter-spacing:-0.5px;">
        {t("welcome_title", lang)}
    </div>
    <div style="font-size:15px;color:#84A59D;margin-top:10px;max-width:540px;
                margin-left:auto;margin-right:auto;line-height:1.65;">
        {t("welcome_desc", lang)}
    </div>
</div>
""", unsafe_allow_html=True)

c1, c2, c3 = st.columns(3)

with c1:
    st.markdown(f"""
    <div class="g-step">
        <div class="g-step-num">{t("step1_num", lang)}</div>
        <div class="g-step-icon-wrap">{_png_img("satellite.png")}</div>
        <div class="g-step-title">{t("step1_title", lang)}</div>
        <div class="g-step-body">{t("step1_body", lang)}</div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class="g-step">
        <div class="g-step-num">{t("step2_num", lang)}</div>
        <div class="g-step-icon-wrap">{_png_img("ai.png")}</div>
        <div class="g-step-title">{t("step2_title", lang)}</div>
        <div class="g-step-body">{t("step2_body", lang)}</div>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div class="g-step">
        <div class="g-step-num">{t("step3_num", lang)}</div>
        <div class="g-step-icon-wrap">{_png_img("monitor.png")}</div>
        <div class="g-step-title">{t("step3_title", lang)}</div>
        <div class="g-step-body">{t("step3_body", lang)}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Added Value ───────────────────────────────────────────────────────────────
_dir   = 'rtl' if lang == 'ar' else 'ltr'
_align = 'right' if lang == 'ar' else 'left'
_ul_pad = 'padding-right:20px;padding-left:0;' if lang == 'ar' else 'padding-left:20px;'
st.markdown(f"""
<div style="background:#ffffff;border:1.5px solid #C8DDD9;border-radius:14px;
            padding:24px 28px;margin:0 0 16px;direction:{_dir};text-align:{_align};">
    <div style="font-size:16px;font-weight:700;color:#219EBC;margin-bottom:14px;">
        ✦ {t("home_added_value_title", lang)}
    </div>
    <ul style="margin:0;{_ul_pad}color:#4A5759;font-size:14px;line-height:1.85;
               list-style:none;direction:{_dir};text-align:{_align};">
        <li style="margin-bottom:8px;">🌿 &nbsp;{t("home_av_bullet1", lang)}</li>
        <li style="margin-bottom:8px;">💧 &nbsp;{t("home_av_bullet2", lang)}</li>
        <li style="margin-bottom:8px;">🪲 &nbsp;{t("home_av_bullet3", lang)}</li>
        <li style="margin-bottom:0;">🛰️ &nbsp;{t("home_av_bullet4", lang)}</li>
    </ul>
</div>
<div style="border:2px dashed #84A59D;border-radius:14px;padding:20px 24px;
            margin-bottom:20px;background:#F7FAFB;direction:{_dir};text-align:{_align};">
    <div style="font-size:14px;font-weight:700;color:#4A5759;margin-bottom:8px;">
        🔌 {t("home_sensor_title", lang)}
    </div>
    <div style="font-size:13px;color:#84A59D;line-height:1.7;">
        {t("home_sensor_body", lang)}
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="g-info-banner">
    {_png_img("satellite.png", 36)}
    <div style="direction:{_dir};text-align:{_align};">
        <div class="g-info-banner-title">{t("banner_title", lang)}</div>
        <div class="g-info-banner-sub">{t("banner_sub", lang)}</div>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="g-footer">
    {t("footer_text", lang)}
</div>
""", unsafe_allow_html=True)
