"""
Guardian — Time Series Analysis
Compare vegetation health across multiple dates for the same AOI.
"""
import streamlit as st
from pathlib import Path
import sys
import base64
import numpy as np
import cv2
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

sys.path.append(str(Path(__file__).parent.parent))

from utils.translations import t, inject_rtl, lang_toggle, render_nav
from utils.ndvi_pipeline import NDVIPipeline

st.set_page_config(page_title="Time Series — The Guardian", layout="wide")


# ── Helpers ───────────────────────────────────────────────────────────────────
def _load_styles():
    base = Path(__file__).parent.parent
    for _css in [base / "assets/style.css", base / "assets/icons/tabler-local.css"]:
        if _css.exists():
            st.markdown(f"<style>{_css.read_text(encoding='utf-8')}</style>",
                        unsafe_allow_html=True)


def _svg_logo(height=52, invert=True):
    svg_path = Path(__file__).parent.parent / "graphic" / "logo.svg"
    if svg_path.exists():
        svg = svg_path.read_text(encoding="utf-8")
        b64 = base64.b64encode(svg.encode()).decode()
        filt = "filter:brightness(0) invert(1);" if invert else ""
        return f'<img src="data:image/svg+xml;base64,{b64}" style="height:{height}px;width:auto;{filt}">'
    return '<span style="font-size:2rem;">🌿</span>'


def _png_img(name, height=36):
    p = Path(__file__).parent.parent / "graphic" / name
    if p.exists():
        b64 = base64.b64encode(p.read_bytes()).decode()
        return f'<img src="data:image/png;base64,{b64}" style="height:{height}px;width:auto;">'
    return ""


def _colorize_health_map(hmap):
    """Convert a uint8 class map (0-3, 255=nodata) to an RGB numpy array."""
    palette = {
        0:   [214,  39,  40],   # Bare / Dead  → red
        1:   [253, 174,  97],   # Severe       → orange
        2:   [255, 255, 191],   # Moderate     → yellow
        3:   [ 26, 152,  80],   # Healthy      → green
        255: [235, 235, 235],   # NoData       → light grey
    }
    out = np.zeros((*hmap.shape, 3), dtype=np.uint8)
    for cid, col in palette.items():
        out[hmap == cid] = col
    return out


_load_styles()

# ── Sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.markdown(f"""
<div class="sidebar-logo">{_svg_logo(44)}</div>
<div class="sidebar-eco">Eco Team</div>
""", unsafe_allow_html=True)

lang = lang_toggle("ts")
render_nav(lang)
inject_rtl(lang)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="guardian-header">
    {_svg_logo(52)}
    <div class="guardian-header-text">
        <div class="title">The Guardian</div>
        <div class="subtitle">{t("header_sub_ts", lang)}</div>
        <div class="eco-badge">{t("eco_badge", lang)}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── State ─────────────────────────────────────────────────────────────────────
if "ts_queue" not in st.session_state:
    st.session_state.ts_queue = []
if "ts_results" not in st.session_state:
    st.session_state.ts_results = {}

ts_queue   = st.session_state.ts_queue
ts_results = st.session_state.ts_results

# ── Queue Panel ───────────────────────────────────────────────────────────────
st.markdown(
    f'<div class="g-section-title"><i class="ti ti-timeline"></i> {t("ts_queue_title", lang)}</div>',
    unsafe_allow_html=True,
)

if not ts_queue:
    st.markdown(f"""
    <div style="text-align:center;padding:44px 20px;background:#EAF4F7;
                border-radius:14px;margin:16px 0;">
        <div style="font-size:44px;margin-bottom:14px;">🛰</div>
        <div style="font-size:18px;font-weight:700;color:#4A5759;margin-bottom:10px;">
            {t("ts_queue_empty_title", lang)}
        </div>
        <div style="font-size:14px;color:#84A59D;max-width:480px;margin:0 auto;line-height:1.6;">
            {t("ts_queue_empty_body", lang)}
        </div>
    </div>
    """, unsafe_allow_html=True)
else:
    # ── Queue table ───────────────────────────────────────────────────────────
    h_id, h_date, h_cloud, h_rm = st.columns([3, 1.8, 1.4, 0.8])
    h_id.markdown(f"**{'Product ID' if lang=='en' else 'معرّف المنتج'}**")
    h_date.markdown(f"**{'Date' if lang=='en' else 'التاريخ'}**")
    h_cloud.markdown(f"**{'Cloud %' if lang=='en' else 'الغيوم %'}**")
    h_rm.markdown(f"**{'Remove' if lang=='en' else 'حذف'}**")
    st.markdown("<hr style='margin:4px 0 10px;border-color:#DDE8E5;'>", unsafe_allow_html=True)

    to_remove = None
    for i, entry in enumerate(ts_queue):
        pid_disp = (entry["id"][:32] + "…") if len(entry["id"]) > 32 else entry["id"]
        already_done = entry["id"] in ts_results

        c1, c2, c3, c4 = st.columns([3, 1.8, 1.4, 0.8])
        done_badge = " ✅" if already_done else ""
        c1.markdown(f"`{pid_disp}`{done_badge}")
        c2.markdown(entry["date"])
        c3.markdown(str(entry.get("cloud", "—")))
        if c4.button("✕", key=f"ts_rm_{i}", help="Remove from queue"):
            to_remove = i

    if to_remove is not None:
        st.session_state.ts_queue.pop(to_remove)
        st.rerun()

    # ── Controls ──────────────────────────────────────────────────────────────
    st.markdown("")
    run_col, _, clear_col = st.columns([2, 3, 1.5])

    with clear_col:
        if st.button(t("ts_clear_queue", lang), use_container_width=True):
            st.session_state.ts_queue = []
            st.session_state.ts_results = {}
            st.rerun()

    if len(ts_queue) < 2:
        st.info(t("ts_min_products", lang))
    else:
        with run_col:
            run_clicked = st.button(t("ts_run_btn", lang), type="primary",
                                    use_container_width=True)

        if run_clicked:
            bbox = st.session_state.get("bbox")
            if not bbox:
                st.error(t("ts_no_aoi", lang))
                st.stop()

            geojson = {
                "type": "Polygon",
                "coordinates": [[
                    [bbox[0], bbox[1]], [bbox[0], bbox[3]],
                    [bbox[2], bbox[3]], [bbox[2], bbox[1]],
                    [bbox[0], bbox[1]],
                ]],
            }

            results_acc   = {}
            overall_prog  = st.progress(0.0)
            status_ph     = st.empty()
            total_prods   = len(ts_queue)

            for pi, entry in enumerate(ts_queue):
                pid   = entry["id"]
                pdate = entry["date"]
                step_label = (
                    f"{t('ts_processing', lang)} {pi+1} {t('ts_of', lang)} "
                    f"{total_prods}  —  {pdate}"
                )
                status_ph.info(step_label)
                overall_prog.progress(pi / total_prods)

                bands = st.session_state.get("downloaded_bands", {}).get(pid)
                if not bands:
                    status_ph.warning(
                        f"No bands available for {pid} — skipping."
                        if lang == "en" else
                        f"لا توجد نطاقات لـ {pid} — يتم التخطي."
                    )
                    continue

                try:
                    pipeline    = NDVIPipeline()
                    bands_paths = {
                        k: bands.get(k)
                        for k in ["B04", "B05", "B07", "B08", "B8A", "B11"]
                        if bands.get(k)
                    }
                    loaded, transform, profile, pixel_size_m = pipeline.crop_and_load_bands(
                        bands_paths, geojson
                    )
                    indices    = pipeline.compute_indices(loaded)
                    composite  = pipeline.compute_composite(indices)
                    health_map = pipeline.classify_health(composite)
                    pxkm2      = (pixel_size_m / 1000) ** 2
                    stats, total_area, comp_mean = pipeline.compute_statistics(
                        health_map, composite, pxkm2
                    )
                    results_acc[pid] = {
                        "date":           pdate,
                        "stats":          stats,
                        "composite_mean": comp_mean,
                        "health_map":     health_map,
                        "total_area":     total_area,
                    }
                except Exception as exc:
                    status_ph.error(f"Failed for {pid}: {exc}")

                overall_prog.progress((pi + 1) / total_prods)

            overall_prog.progress(1.0)
            n_ok = len(results_acc)
            status_ph.success(
                f"Done — {n_ok} / {total_prods} products processed."
                if lang == "en" else
                f"تم — {n_ok} / {total_prods} منتج تمت معالجته."
            )
            st.session_state.ts_results = results_acc
            ts_results = results_acc


# ── Results ───────────────────────────────────────────────────────────────────
if len(ts_results) < 2:
    if len(ts_results) == 1:
        st.info(t("ts_one_product", lang))
    st.stop()

st.divider()
st.markdown(
    f'<div class="g-section-title"><i class="ti ti-chart-line"></i> '
    f'{t("ts_results_title", lang)}</div>',
    unsafe_allow_html=True,
)

# Sort chronologically
sorted_items  = sorted(ts_results.items(), key=lambda x: x[1]["date"])
dates         = [v["date"]                        for _, v in sorted_items]
scores        = [v["composite_mean"] * 100        for _, v in sorted_items]
healthy_kms   = [v["stats"][3]["area_km2"]        for _, v in sorted_items]
moderate_kms  = [v["stats"][2]["area_km2"]        for _, v in sorted_items]
severe_kms    = [v["stats"][1]["area_km2"]        for _, v in sorted_items]
bare_kms      = [v["stats"][0]["area_km2"]        for _, v in sorted_items]
healthy_pcts  = [v["stats"][3]["pct"]             for _, v in sorted_items]
moderate_pcts = [v["stats"][2]["pct"]             for _, v in sorted_items]
severe_pcts   = [v["stats"][1]["pct"]             for _, v in sorted_items]
bare_pcts     = [v["stats"][0]["pct"]             for _, v in sorted_items]

PALETTE = {
    "bg":      "#F7F9FA",
    "accent":  "#219EBC",
    "text":    "#4A5759",
    "sub":     "#84A59D",
    "grid":    "#DDE8E5",
    "healthy": "#16a34a",
    "moderate":"#b45309",
    "severe":  "#dc2626",
    "bare":    "#94a3b8",
}

# ── Chart 1 — Health Score Line ───────────────────────────────────────────────
chart_l, chart_r = st.columns(2)

with chart_l:
    st.markdown(f"**{t('ts_health_trend', lang)}**")
    fig1, ax1 = plt.subplots(figsize=(6, 3.6))
    fig1.patch.set_facecolor(PALETTE["bg"])
    ax1.set_facecolor(PALETTE["bg"])

    ax1.plot(dates, scores, color=PALETTE["accent"], linewidth=2.5,
             marker="o", markersize=9,
             markerfacecolor="white", markeredgecolor=PALETTE["accent"],
             markeredgewidth=2.5, zorder=3)

    for d, s in zip(dates, scores):
        ax1.annotate(f"{s:.0f}%", (d, s),
                     textcoords="offset points", xytext=(0, 11),
                     ha="center", fontsize=9,
                     color=PALETTE["accent"], fontweight="bold")

    ax1.fill_between(dates, scores, alpha=0.10, color=PALETTE["accent"])
    ax1.set_ylim(0, 108)
    ax1.set_ylabel("Health Score (%)", color=PALETTE["text"], fontsize=10)
    ax1.tick_params(axis="x", rotation=30, labelsize=8, colors=PALETTE["text"])
    ax1.tick_params(axis="y", labelsize=9,  colors=PALETTE["text"])
    ax1.grid(axis="y", alpha=0.35, color=PALETTE["grid"])
    for spine in ax1.spines.values():
        spine.set_edgecolor(PALETTE["grid"])
    ax1.spines["top"].set_visible(False)
    ax1.spines["right"].set_visible(False)
    fig1.tight_layout()
    st.pyplot(fig1)
    plt.close(fig1)

# ── Chart 2 — Stacked Bar ─────────────────────────────────────────────────────
with chart_r:
    st.markdown(f"**{t('ts_veg_distribution', lang)}**")
    fig2, ax2 = plt.subplots(figsize=(6, 3.6))
    fig2.patch.set_facecolor(PALETTE["bg"])
    ax2.set_facecolor(PALETTE["bg"])

    x = list(range(len(dates)))
    w = 0.55

    b1 = ax2.bar(x, healthy_pcts,  w, color=PALETTE["healthy"],  alpha=0.88,
                 label="Healthy" if lang=="en" else "سليم")
    b2 = ax2.bar(x, moderate_pcts, w, bottom=healthy_pcts,
                 color=PALETTE["moderate"], alpha=0.88,
                 label="Moderate" if lang=="en" else "متوسط")
    bot3 = [a+b for a, b in zip(healthy_pcts, moderate_pcts)]
    b3 = ax2.bar(x, severe_pcts, w, bottom=bot3,
                 color=PALETTE["severe"], alpha=0.88,
                 label="Severe" if lang=="en" else "حرج")
    bot4 = [a+b for a, b in zip(bot3, severe_pcts)]
    b4 = ax2.bar(x, bare_pcts, w, bottom=bot4,
                 color=PALETTE["bare"], alpha=0.88,
                 label="Bare" if lang=="en" else "جرداء")

    ax2.set_xticks(x)
    ax2.set_xticklabels(dates, rotation=30, ha="right",
                        fontsize=8, color=PALETTE["text"])
    ax2.set_ylabel("Coverage (%)", color=PALETTE["text"], fontsize=10)
    ax2.set_ylim(0, 112)
    ax2.tick_params(axis="y", labelsize=9, colors=PALETTE["text"])
    ax2.legend(loc="upper right", fontsize=7, framealpha=0.75,
               edgecolor=PALETTE["grid"])
    for spine in ax2.spines.values():
        spine.set_edgecolor(PALETTE["grid"])
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)
    ax2.grid(axis="y", alpha=0.3, color=PALETTE["grid"])
    fig2.tight_layout()
    st.pyplot(fig2)
    plt.close(fig2)

st.divider()

# ── Expansion Summary Cards ───────────────────────────────────────────────────
st.markdown(
    f'<div class="g-section-title"><i class="ti ti-trending-up"></i> '
    f'{t("ts_expansion_title", lang)}</div>',
    unsafe_allow_html=True,
)

first_healthy  = healthy_kms[0]
last_healthy   = healthy_kms[-1]
net_change     = last_healthy - first_healthy
score_delta    = scores[-1] - scores[0]

if net_change > 0.05:
    trend_lbl, trend_clr, trend_icon = t("ts_trend_expanding", lang), PALETTE["healthy"], "▲"
elif net_change < -0.05:
    trend_lbl, trend_clr, trend_icon = t("ts_trend_degrading", lang), PALETTE["severe"],  "▼"
else:
    trend_lbl, trend_clr, trend_icon = t("ts_trend_stable",    lang), PALETTE["moderate"],"→"

ec1, ec2, ec3, ec4 = st.columns(4)

with ec1:
    st.markdown(f"""<div class="g-card" style="text-align:center;">
        <div style="font-size:24px;font-weight:800;color:{trend_clr};">{trend_icon} {trend_lbl}</div>
        <div class="g-card-label">{'Overall Trend' if lang=='en' else 'الاتجاه العام'}</div>
        <div class="g-card-desc">{dates[0]} → {dates[-1]}</div>
    </div>""", unsafe_allow_html=True)

with ec2:
    chg_str = f"{'+'if net_change>=0 else ''}{net_change:.2f} km²"
    st.markdown(f"""<div class="g-card" style="text-align:center;">
        <div style="font-size:24px;font-weight:800;color:{trend_clr};">{chg_str}</div>
        <div class="g-card-label">{t("ts_net_change", lang)}</div>
        <div class="g-card-desc">{first_healthy:.2f} → {last_healthy:.2f} km²</div>
    </div>""", unsafe_allow_html=True)

with ec3:
    sd_str = f"{'+'if score_delta>=0 else ''}{score_delta:.1f}%"
    sd_clr = trend_clr if abs(score_delta) > 2 else PALETTE["sub"]
    st.markdown(f"""<div class="g-card" style="text-align:center;">
        <div style="font-size:24px;font-weight:800;color:{sd_clr};">{sd_str}</div>
        <div class="g-card-label">{'Score Change' if lang=='en' else 'تغير الدرجة'}</div>
        <div class="g-card-desc">{scores[0]:.0f}% → {scores[-1]:.0f}%</div>
    </div>""", unsafe_allow_html=True)

with ec4:
    n_pts = len(dates)
    st.markdown(f"""<div class="g-card" style="text-align:center;">
        <div style="font-size:24px;font-weight:800;color:{PALETTE['accent']};">{n_pts}</div>
        <div class="g-card-label">{'Time Points' if lang=='en' else 'نقاط زمنية'}</div>
        <div class="g-card-desc">{n_pts-1} {'periods compared' if lang=='en' else 'فترة مقارنة'}</div>
    </div>""", unsafe_allow_html=True)

st.divider()

# ── Change Detection Map ──────────────────────────────────────────────────────
st.markdown(
    f'<div class="g-section-title"><i class="ti ti-map-2"></i> '
    f'{t("ts_change_title", lang)}</div>',
    unsafe_allow_html=True,
)

_, first_data = sorted_items[0]
_, last_data  = sorted_items[-1]

hmap_first = first_data["health_map"].copy().astype(np.int16)
hmap_last  = last_data["health_map"].copy().astype(np.int16)

# Align spatial extents (nearest-neighbour keeps class IDs intact)
if hmap_first.shape != hmap_last.shape:
    th, tw = hmap_first.shape
    hmap_last = cv2.resize(
        hmap_last.astype(np.uint8), (tw, th),
        interpolation=cv2.INTER_NEAREST,
    ).astype(np.int16)

nodata_mask = (hmap_first == 255) | (hmap_last == 255)
delta       = np.where(nodata_mask, 0, hmap_last - hmap_first)

# Build RGB change map
change_rgb = np.full((*delta.shape, 3), 230, dtype=np.uint8)
change_rgb[delta  > 0] = [22, 163,  74]   # improved  → green
change_rgb[delta  < 0] = [220,  38,  38]   # degraded  → red
change_rgb[delta == 0] = [148, 163, 184]   # stable    → grey
change_rgb[nodata_mask] = [235, 235, 235]  # nodata    → very light grey

valid_px     = (~nodata_mask).sum()
improved_pct = (delta > 0).sum() / max(1, valid_px) * 100
degraded_pct = (delta < 0).sum() / max(1, valid_px) * 100
stable_pct   = 100 - improved_pct - degraded_pct

col_f, col_c, col_l = st.columns(3)

with col_f:
    score_f = first_data["composite_mean"] * 100
    st.caption(f"📅 {first_data['date']}  —  {score_f:.0f}%")
    fig_f, ax_f = plt.subplots(figsize=(4.2, 4.2))
    fig_f.patch.set_facecolor(PALETTE["bg"])
    ax_f.imshow(_colorize_health_map(first_data["health_map"]))
    ax_f.set_title(first_data["date"], fontsize=9, color=PALETTE["text"], pad=4)
    ax_f.axis("off")
    fig_f.tight_layout(pad=0.2)
    st.pyplot(fig_f)
    plt.close(fig_f)

    # Class legend
    _leg_items = [
        ("#16a34a", "Healthy" if lang=="en" else "سليم"),
        ("#b45309", "Moderate" if lang=="en" else "متوسط"),
        ("#dc2626", "Severe" if lang=="en" else "حرج"),
        ("#94a3b8", "Bare" if lang=="en" else "جرداء"),
    ]
    st.markdown(
        "".join(
            f'<span style="background:{c};padding:2px 9px;border-radius:4px;'
            f'color:white;font-size:11px;margin-right:5px;">{lbl}</span>'
            for c, lbl in _leg_items
        ),
        unsafe_allow_html=True,
    )

with col_c:
    st.caption(
        f"{'Change Map' if lang=='en' else 'خريطة التغيير'}  —  "
        f"{t('ts_improved', lang)}: {improved_pct:.0f}%  "
        f"{t('ts_degraded', lang)}: {degraded_pct:.0f}%"
    )
    fig_c, ax_c = plt.subplots(figsize=(4.2, 4.2))
    fig_c.patch.set_facecolor(PALETTE["bg"])
    ax_c.imshow(change_rgb)
    ax_c.set_title(
        f"{first_data['date']} → {last_data['date']}",
        fontsize=9, color=PALETTE["text"], pad=4,
    )
    ax_c.axis("off")
    legend_handles = [
        mpatches.Patch(color=[c/255 for c in [22,163,74]],
                       label=f"{t('ts_improved', lang)} ({improved_pct:.0f}%)"),
        mpatches.Patch(color=[c/255 for c in [220,38,38]],
                       label=f"{t('ts_degraded', lang)} ({degraded_pct:.0f}%)"),
        mpatches.Patch(color=[c/255 for c in [148,163,184]],
                       label=f"{t('ts_stable', lang)} ({stable_pct:.0f}%)"),
    ]
    ax_c.legend(handles=legend_handles, loc="lower left",
                fontsize=7, framealpha=0.85, edgecolor=PALETTE["grid"])
    fig_c.tight_layout(pad=0.2)
    st.pyplot(fig_c)
    plt.close(fig_c)

with col_l:
    score_l = last_data["composite_mean"] * 100
    st.caption(f"📅 {last_data['date']}  —  {score_l:.0f}%")
    fig_l, ax_l = plt.subplots(figsize=(4.2, 4.2))
    fig_l.patch.set_facecolor(PALETTE["bg"])
    ax_l.imshow(_colorize_health_map(last_data["health_map"]))
    ax_l.set_title(last_data["date"], fontsize=9, color=PALETTE["text"], pad=4)
    ax_l.axis("off")
    fig_l.tight_layout(pad=0.2)
    st.pyplot(fig_l)
    plt.close(fig_l)

st.divider()

# ── Summary Data Table ────────────────────────────────────────────────────────
st.markdown(
    f'<div class="g-section-title"><i class="ti ti-table"></i> '
    f'{t("ts_table_title", lang)}</div>',
    unsafe_allow_html=True,
)

prev_score = None
rows = ""
for _, v in sorted_items:
    sc = v["composite_mean"] * 100
    if prev_score is None:
        arrow, a_clr = "—", PALETTE["sub"]
    elif sc > prev_score + 1.0:
        arrow, a_clr = "▲", PALETTE["healthy"]
    elif sc < prev_score - 1.0:
        arrow, a_clr = "▼", PALETTE["severe"]
    else:
        arrow, a_clr = "→", PALETTE["moderate"]
    prev_score = sc

    rows += f"""
    <tr style="border-bottom:1px solid #EAF4F7;">
      <td style="padding:10px 14px;">{v['date']}</td>
      <td style="padding:10px 14px;font-weight:700;">
          {sc:.1f}% <span style="color:{a_clr}">{arrow}</span>
      </td>
      <td style="padding:10px 14px;color:{PALETTE['healthy']};">{v['stats'][3]['area_km2']:.2f}</td>
      <td style="padding:10px 14px;color:{PALETTE['moderate']};">{v['stats'][2]['area_km2']:.2f}</td>
      <td style="padding:10px 14px;color:{PALETTE['severe']};">{v['stats'][1]['area_km2']:.2f}</td>
      <td style="padding:10px 14px;color:{PALETTE['bare']};">{v['stats'][0]['area_km2']:.2f}</td>
    </tr>"""

st.markdown(f"""
<div style="overflow-x:auto;border-radius:10px;border:1px solid #DDE8E5;">
<table style="width:100%;border-collapse:collapse;font-size:13px;color:{PALETTE['text']};">
  <thead>
    <tr style="background:#219EBC;color:white;">
      <th style="padding:11px 14px;text-align:left;">{t('ts_date_col',     lang)}</th>
      <th style="padding:11px 14px;text-align:left;">{t('ts_score_col',    lang)}</th>
      <th style="padding:11px 14px;text-align:left;">{t('ts_healthy_col',  lang)}</th>
      <th style="padding:11px 14px;text-align:left;">{t('ts_moderate_col', lang)}</th>
      <th style="padding:11px 14px;text-align:left;">{t('ts_severe_col',   lang)}</th>
      <th style="padding:11px 14px;text-align:left;">{t('ts_bare_col',     lang)}</th>
    </tr>
  </thead>
  <tbody>{rows}</tbody>
</table>
</div>
""", unsafe_allow_html=True)

st.markdown("")
if st.button(t("ts_clear_results", lang)):
    st.session_state.ts_results = {}
    st.rerun()
