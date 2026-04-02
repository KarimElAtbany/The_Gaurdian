import streamlit as st
from pathlib import Path

st.set_page_config(
    page_title="The Guardian — Palm & Vegetation Monitor",
    page_icon="🌴",
    layout="wide",
    initial_sidebar_state="expanded",
)

with open(Path(__file__).parent / "assets/style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.markdown("""
<div class="header">
    <div class="logo">
        <span class="logo-icon">🌴</span>
        <div class="logo-text">
            <div class="logo-title">The Guardian — El Wadi El Gedid Palm & Vegetation Monitor</div>
            <div class="logo-subtitle">Environmental intelligence platform for researchers and investors</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

st.sidebar.title("🌴 Navigation")
st.sidebar.info("Select a page above to get started.")

st.markdown("## Welcome to The Guardian")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    ### 📡 Step 1 — Data Acquisition
    Search the Sentinel-2 STAC catalog, draw your Area of Interest on the map, and download multi-spectral bands directly from AWS.
    """)

with col2:
    st.markdown("""
    ### 🌿 Step 2 — Vegetation Health
    Run the multi-index pipeline (MSAVI · NDRE · NDWI · CIre) to generate a composite health map and per-class area statistics.
    """)

with col3:
    st.markdown("""
    ### 🎯 Step 3 — Tree Detection
    Upload drone imagery or use downloaded Sentinel-2 RGB composites to count and classify palm trees with a fine-tuned YOLOv8 model.
    """)

st.divider()

st.markdown("""
### Quick-start workflow
1. Go to **Data Acquisition** → draw your AOI → search and download bands
2. Go to **Vegetation Health Analysis** → tune thresholds → run analysis
3. Go to **Tree Detection** → upload drone images → run YOLO detection
4. Go to **Combined Analysis** → cross-reference all results and export a report
5. Check **Dashboard Overview** at any time for a live summary
""")
