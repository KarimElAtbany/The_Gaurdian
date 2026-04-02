import streamlit as st
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))

st.set_page_config(page_title="Dashboard Overview", page_icon="📊", layout="wide")

with open(Path(__file__).parent.parent / "assets/style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.title("📊 Dashboard Overview")

col1, col2, col3, col4 = st.columns(4)

with col1:
    palm_count = st.session_state.get('palm_census', 0)
    st.metric("🌴 Palm Census", f"{palm_count:,}", "+1.2%")

with col2:
    veg_cover = st.session_state.get('vegetation_cover', 0)
    st.metric("🌿 Vegetation Cover", f"{veg_cover:.1f}%", "of Total Area")

with col3:
    composite = st.session_state.get('composite_health', 0)
    st.metric("📈 Composite Health Score", f"{composite:.1f} / 100", "Multi-Index")

with col4:
    yield_est = st.session_state.get('economic_yield', 'N/A')
    st.metric("💰 Economic Yield", yield_est, "Forecast")

st.divider()

if 'ndvi_results' in st.session_state:
    results = st.session_state.ndvi_results
    stats   = results.get('stats', {})
    indices = results.get('indices', {})

    st.subheader("🌡️ Index Breakdown")

    import numpy as np
    index_info = {
        "MSAVI": {"label": "MSAVI", "desc": "Soil-Adj. Greenness",   "color": "#4dac26", "range": (-0.1, 0.6)},
        "NDRE":  {"label": "NDRE",  "desc": "Chlorophyll / Stress",  "color": "#b8e186", "range": (-0.1, 0.5)},
        "NDWI":  {"label": "NDWI",  "desc": "Water / Drought",       "color": "#4393c3", "range": (-0.3, 0.5)},
        "CIre":  {"label": "CIre",  "desc": "Nutrient Status",       "color": "#f4a582", "range": (0.0,  1.0)},
    }

    idx_cols = st.columns(4)
    for col, (name, info) in zip(idx_cols, index_info.items()):
        arr = indices.get(name)
        if arr is not None:
            mean_val = float(np.nanmean(arr))
            vmin, vmax = info["range"]
            pct = int(np.clip((mean_val - vmin) / (vmax - vmin + 1e-10), 0, 1) * 100)
            with col:
                st.metric(f"{info['label']} — {info['desc']}", f"{mean_val:.4f}")
                st.progress(pct)
        else:
            with col:
                st.metric(f"{info['label']} — {info['desc']}", "N/A")
                st.caption("Band not downloaded")

    st.divider()
    st.subheader("🗺️ Analysis Results")

    col_map, col_det = st.columns(2)

    with col_map:
        st.write("**Composite Health Map**")
        if 'health_plot' in st.session_state:
            st.pyplot(st.session_state.health_plot)

    with col_det:
        st.write("**Detection Results**")
        if 'yolo_results' in st.session_state:
            for img_name, data in st.session_state.yolo_results.items():
                st.image(data['annotated'], caption=f"{data['count']} trees detected")
                break

        st.write("**Health Class Summary**")
        colors = ["#d73027", "#fdae61", "#ffffbf", "#1a9850"]
        for cid, data in stats.items():
            bar_html = (
                f"<div style='background:{colors[cid]};width:{max(data['pct'],1):.0f}%;"
                f"height:8px;border-radius:4px;margin-bottom:4px'></div>"
            )
            st.markdown(bar_html, unsafe_allow_html=True)
            st.caption(f"{data['label']}: {data['area_km2']:.3f} km²  ({data['pct']:.1f}%)")

else:
    st.info("Run Vegetation Health Analysis or Tree Detection to see results here.")

if 'class_counts' in st.session_state:
    st.divider()
    st.subheader("🎯 Tree Detection Summary")

    counts = st.session_state.class_counts
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Unhealthy 🔴", counts.get(0, 0), delta_color="inverse")
    with col2:
        st.metric("Healthy 🟢",   counts.get(1, 0))
    with col3:
        st.metric("Yellow 🟡",    counts.get(2, 0))
