import streamlit as st
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))

import cv2
import numpy as np

st.set_page_config(page_title="Tree Detection", page_icon="🎯", layout="wide")

with open(Path(__file__).parent.parent / "assets/style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.title("🎯 YOLO Palm Tree Detection")

with st.sidebar:
    st.subheader("⚙️ Model Settings")
    model_path = st.text_input("Model Path", value="models/finetune_yolov8n_best_map50.pt")
    conf_threshold = st.slider("Confidence Threshold", 0.0, 1.0, 0.50, 0.05)
    st.divider()
    detection_source = st.radio("Detection Source", ["Drone Images", "Sentinel-2 RGB"])

if detection_source == "Drone Images":
    st.subheader("📁 Upload Drone Images")
    uploaded_files = st.file_uploader(
        "Choose images (JPG / PNG)",
        type=['jpg', 'jpeg', 'png'],
        accept_multiple_files=True
    )

    if uploaded_files and st.button("🚀 Run Detection", type="primary"):
        model_file = Path(model_path)
        if not model_file.exists():
            st.error(f"Model not found: {model_path}")
            st.stop()

        from utils.yolo_pipeline import YOLOPipeline
        pipeline = YOLOPipeline(model_path)

        temp_dir = Path("data/temp_uploads")
        temp_dir.mkdir(parents=True, exist_ok=True)

        image_paths = []
        for uploaded_file in uploaded_files:
            file_path = temp_dir / uploaded_file.name
            with open(file_path, 'wb') as f:
                f.write(uploaded_file.getbuffer())
            image_paths.append(file_path)

        with st.spinner(f"Detecting trees in {len(image_paths)} image(s)…"):
            detections, class_counts = pipeline.process_batch(image_paths, conf_threshold)

        st.session_state.yolo_results   = detections
        st.session_state.class_counts   = class_counts
        st.session_state.palm_census    = sum(class_counts.values())
        st.success(f"✅ Detected {sum(class_counts.values())} trees across {len(image_paths)} image(s)")

else:
    st.subheader("📡 Sentinel-2 RGB Detection")

    if not st.session_state.get('downloaded_bands'):
        st.warning("No downloaded bands found — go to Data Acquisition first.")
        st.stop()

    product_id = st.selectbox("Select Product", list(st.session_state.downloaded_bands.keys()))

    if st.button("🚀 Create RGB & Detect", type="primary"):
        model_file = Path(model_path)
        if not model_file.exists():
            st.error(f"Model not found: {model_path}")
            st.stop()

        bands = st.session_state.downloaded_bands[product_id]
        if not all(b in bands for b in ['B02', 'B03', 'B04']):
            st.error("Missing RGB bands (B02, B03, B04). Please download them first.")
            st.stop()

        from utils.yolo_pipeline import YOLOPipeline
        pipeline = YOLOPipeline(model_path)

        rgb_output = Path("data/processed") / f"{product_id}_rgb.jpg"
        rgb_output.parent.mkdir(parents=True, exist_ok=True)

        with st.spinner("Building RGB composite…"):
            rgb_path = pipeline.create_rgb_from_bands(
                bands['B02'], bands['B03'], bands['B04'], rgb_output
            )

        st.image(str(rgb_path), caption="Sentinel-2 True Colour Composite", use_column_width=True)

        with st.spinner("Running YOLO detection…"):
            results   = pipeline.detect(rgb_path, conf_threshold)
            annotated = pipeline.annotate_image(rgb_path, results)

        st.warning("⚠️ Sentinel-2 at 10 m/px — detection is most reliable at 25–30 cm drone resolution.")

        st.image(
            cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB),
            caption=f"{len(results.boxes)} detections",
            use_column_width=True
        )

        class_counts = {0: 0, 1: 0, 2: 0}
        for box in results.boxes:
            cls = int(box.cls[0])
            class_counts[cls] = class_counts.get(cls, 0) + 1

        st.session_state.class_counts = class_counts
        st.session_state.palm_census  = sum(class_counts.values())
        st.success(f"Detected {len(results.boxes)} objects")

if 'yolo_results' in st.session_state or 'class_counts' in st.session_state:
    st.divider()
    st.subheader("📊 Detection Summary")

    counts = st.session_state.get('class_counts', {})
    total  = sum(counts.values())

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("🌴 Total Trees",   total)
    with c2:
        st.metric("🔴 Unhealthy",     counts.get(0, 0))
    with c3:
        st.metric("🟢 Healthy",       counts.get(1, 0))
    with c4:
        st.metric("🟡 Yellow",        counts.get(2, 0))

    if total > 0:
        st.divider()
        st.subheader("📈 Health Distribution")
        labels = ["Unhealthy", "Healthy", "Yellow"]
        colors = ["#d73027", "#1a9850", "#fdae61"]
        for i, (label, color) in enumerate(zip(labels, colors)):
            count = counts.get(i, 0)
            pct   = count / total * 100 if total > 0 else 0
            bar   = (
                f"<div style='background:{color};width:{max(pct,0.5):.1f}%;"
                f"height:10px;border-radius:5px;margin-bottom:4px'></div>"
            )
            st.markdown(bar, unsafe_allow_html=True)
            st.caption(f"{label}: {count} trees ({pct:.1f}%)")

    if 'yolo_results' in st.session_state:
        st.divider()
        st.subheader("🖼️ Annotated Images")
        cols = st.columns(min(3, len(st.session_state.yolo_results)))
        for idx, (img_key, data) in enumerate(st.session_state.yolo_results.items()):
            with cols[idx % 3]:
                annotated = data['annotated']
                if len(annotated.shape) == 3 and annotated.shape[2] == 3:
                    display = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)
                else:
                    display = annotated
                st.image(display, caption=f"{Path(img_key).name} — {data['count']} trees")
