import streamlit as st
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))

from utils.ndvi_pipeline import VegetationHealthPipeline
import json

st.set_page_config(page_title="Vegetation Health Analysis", page_icon="🌿", layout="wide")

with open(Path(__file__).parent.parent / "assets/style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.title("🌿 Multi-Index Vegetation Health Analysis")
st.caption("MSAVI · NDRE · NDWI · CIre → Composite Health Score")

if not st.session_state.get('downloaded_bands'):
    st.warning("⚠️ No downloaded products. Please go to Data Acquisition first.")
    st.stop()

with st.sidebar:
    st.subheader("🎯 Composite Score Thresholds")
    st.caption("Thresholds applied to the weighted composite score (0 → 1)")
    t1 = st.slider("Dead / Bare  (t1)",       0.0, 0.5, 0.20, 0.01)
    t2 = st.slider("Severe Stress  (t2)",      0.0, 0.7, 0.40, 0.01)
    t3 = st.slider("Moderate Stress  (t3)",    0.0, 0.9, 0.60, 0.01)

    st.divider()

    st.subheader("⚖️ Index Weights")
    st.caption("Relative contribution of each index to the composite score")
    w_msavi = st.slider("MSAVI weight",  0.0, 1.0, 0.20, 0.05)
    w_ndre  = st.slider("NDRE weight",   0.0, 1.0, 0.35, 0.05)
    w_ndwi  = st.slider("NDWI weight",   0.0, 1.0, 0.30, 0.05)
    w_cire  = st.slider("CIre weight",   0.0, 1.0, 0.15, 0.05)

    st.divider()

    product_id = st.selectbox(
        "Select Product",
        list(st.session_state.downloaded_bands.keys())
    )

    st.divider()

    st.subheader("📐 Area of Interest")
    use_bbox = st.checkbox("Use drawn AOI", value=True)

    if not use_bbox:
        st.write("Manual GeoJSON")
        geojson_text = st.text_area("Paste GeoJSON polygon", height=150)
    else:
        if st.session_state.get('bbox'):
            st.success("Using AOI from map")
        else:
            st.warning("No AOI drawn. Go to Data Acquisition.")

with st.expander("ℹ️ About the indices used", expanded=False):
    col_a, col_b, col_c, col_d = st.columns(4)
    with col_a:
        st.markdown("**MSAVI**")
        st.markdown("Modified Soil-Adjusted VI. Corrects for bright desert soil background — more reliable than NDVI in arid regions like El Wadi El Gedid.")
    with col_b:
        st.markdown("**NDRE**")
        st.markdown("Normalized Difference Red-Edge. Uses Sentinel-2 B05 (705 nm). Detects chlorophyll stress 2–4 weeks earlier than NDVI.")
    with col_c:
        st.markdown("**NDWI**")
        st.markdown("Normalized Difference Water Index. Uses B8A + B11 (SWIR). Directly measures canopy water content and drought stress.")
    with col_d:
        st.markdown("**CIre**")
        st.markdown("Red-Edge Chlorophyll Index. Uses B07/B05. Sensitive to nutrient (N, Mg) deficiency before visible symptoms appear.")

if st.button("🚀 Run Health Analysis", type="primary"):
    bands_available = st.session_state.downloaded_bands[product_id]

    if use_bbox and st.session_state.get('bbox'):
        bbox = st.session_state.bbox
        geojson = {
            "type": "Polygon",
            "coordinates": [[
                [bbox[0], bbox[1]],
                [bbox[0], bbox[3]],
                [bbox[2], bbox[3]],
                [bbox[2], bbox[1]],
                [bbox[0], bbox[1]]
            ]]
        }
    elif not use_bbox and geojson_text:
        geojson = json.loads(geojson_text)
    else:
        st.error("Please provide an AOI")
        st.stop()

    with st.spinner("Computing multi-index health analysis…"):
        pipeline = VegetationHealthPipeline(thresholds=(t1, t2, t3))

        pipeline.INDEX_WEIGHTS = {
            "MSAVI": w_msavi,
            "NDRE":  w_ndre,
            "NDWI":  w_ndwi,
            "CIre":  w_cire,
        }

        bands_paths = {
            'B04': bands_available.get('B04'),
            'B05': bands_available.get('B05'),
            'B07': bands_available.get('B07'),
            'B08': bands_available.get('B08'),
            'B8A': bands_available.get('B8A'),
            'B11': bands_available.get('B11'),
        }

        bands_paths = {k: v for k, v in bands_paths.items() if v is not None}

        loaded_bands, transform, profile, pixel_size_m = pipeline.crop_and_load_bands(
            bands_paths, geojson
        )

        indices   = pipeline.compute_indices(loaded_bands)
        composite = pipeline.compute_composite(indices)
        health_map = pipeline.classify_health(composite)

        pixel_area_km2 = (pixel_size_m / 1000) ** 2
        stats, total_area, composite_mean = pipeline.compute_statistics(
            health_map, composite, pixel_area_km2
        )

        output_tif = Path("data/processed") / f"{product_id}_health.tif"
        output_tif.parent.mkdir(parents=True, exist_ok=True)
        pipeline.save_geotiff(health_map, profile, transform, output_tif)

        fig = pipeline.create_visualization(health_map, indices, composite, stats, total_area)

        st.session_state.ndvi_results = {
            'health_map':     health_map,
            'indices':        indices,
            'composite':      composite,
            'composite_mean': composite_mean,
            'stats':          stats,
            'total_area':     total_area,
            'transform':      transform,
        }
        st.session_state.health_plot     = fig
        st.session_state.vegetation_cover = sum(stats[i]['pct'] for i in [1, 2, 3])
        st.session_state.composite_health = round(composite_mean * 100, 1)

        st.success("✅ Analysis complete!")

if 'ndvi_results' in st.session_state:
    st.divider()
    st.subheader("📊 Results")

    results = st.session_state.ndvi_results
    stats   = results['stats']
    indices = results['indices']

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("🌿 Vegetation Cover",   f"{st.session_state.get('vegetation_cover', 0):.1f}%")
    with m2:
        st.metric("📈 Composite Score",    f"{results['composite_mean']:.3f}")
    with m3:
        healthy_pct = stats[3]['pct']
        st.metric("✅ Healthy Area",        f"{healthy_pct:.1f}%")
    with m4:
        stressed_pct = stats[1]['pct'] + stats[2]['pct']
        st.metric("⚠️ Stressed Area",       f"{stressed_pct:.1f}%")

    st.divider()

    st.pyplot(st.session_state.health_plot)

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📈 Class Statistics")
        colors = ["#d73027", "#fdae61", "#ffffbf", "#1a9850"]
        for cid, data in stats.items():
            bar_html = (
                f"<div style='background:{colors[cid]};width:{max(data['pct'],1):.0f}%;height:6px;"
                f"border-radius:3px;margin-bottom:2px'></div>"
            )
            st.markdown(bar_html, unsafe_allow_html=True)
            st.metric(data['label'], f"{data['area_km2']:.3f} km²", f"{data['pct']:.1f}%")

    with col2:
        st.subheader("🔬 Index Means")
        index_labels = {
            "MSAVI": "MSAVI — Soil-Adj. Greenness",
            "NDRE":  "NDRE — Chlorophyll / Early Stress",
            "NDWI":  "NDWI — Water / Drought Stress",
            "CIre":  "CIre — Nutrient Status",
        }
        import numpy as np
        for name, arr in indices.items():
            if arr is not None:
                mean_val = float(np.nanmean(arr))
                st.metric(index_labels.get(name, name), f"{mean_val:.4f}")

        st.divider()
        st.subheader("💾 Download")
        output_tif = Path("data/processed") / f"{product_id}_health.tif"
        if output_tif.exists():
            with open(output_tif, 'rb') as f:
                st.download_button(
                    "⬇️ Download Health GeoTIFF",
                    f,
                    file_name=f"{product_id}_health.tif",
                    mime="image/tiff"
                )
