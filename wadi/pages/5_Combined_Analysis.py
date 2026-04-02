import streamlit as st
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))

import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Combined Analysis", page_icon="🔬", layout="wide")

with open(Path(__file__).parent.parent / "assets/style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.title("🔬 Combined Analysis")
st.caption("Cross-reference vegetation health with tree detection for integrated insights")

has_veg  = 'ndvi_results' in st.session_state
has_yolo = 'class_counts' in st.session_state

if not has_veg:
    st.warning("⚠️ Run **Vegetation Health Analysis** (page 3) first.")
if not has_yolo:
    st.warning("⚠️ Run **Tree Detection** (page 4) first.")

if not (has_veg and has_yolo):
    st.stop()

results      = st.session_state.ndvi_results
stats        = results['stats']
indices      = results['indices']
composite    = results['composite']
total_area   = results['total_area']
counts       = st.session_state.class_counts
total_trees  = sum(counts.values())

st.subheader("📊 Integrated Summary")

c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    st.metric("🌿 Vegetation Cover",      f"{st.session_state.get('vegetation_cover', 0):.1f}%")
with c2:
    st.metric("📈 Health Score",          f"{results['composite_mean'] * 100:.1f} / 100")
with c3:
    st.metric("🌴 Total Trees",           total_trees)
with c4:
    healthy_pct = counts.get(1, 0) / total_trees * 100 if total_trees > 0 else 0
    st.metric("🟢 Healthy Trees",         f"{healthy_pct:.1f}%")
with c5:
    st.metric("📐 Total Area",            f"{total_area:.2f} km²")

st.divider()

col_left, col_right = st.columns(2)

with col_left:
    st.subheader("🌡️ Vegetation Health Breakdown")
    colors = ["#d73027", "#fdae61", "#ffffbf", "#1a9850"]
    for cid, data in stats.items():
        bar = (
            f"<div style='background:{colors[cid]};width:{max(data['pct'], 0.5):.1f}%;"
            f"height:9px;border-radius:4px;margin-bottom:3px'></div>"
        )
        st.markdown(bar, unsafe_allow_html=True)
        st.caption(f"{data['label']}: {data['area_km2']:.3f} km²  ({data['pct']:.1f}%)")

with col_right:
    st.subheader("🎯 Tree Health Breakdown")
    tree_colors  = ["#d73027", "#1a9850", "#fdae61"]
    tree_labels  = ["Unhealthy", "Healthy", "Yellow"]
    for i, (label, color) in enumerate(zip(tree_labels, tree_colors)):
        count = counts.get(i, 0)
        pct   = count / total_trees * 100 if total_trees > 0 else 0
        bar   = (
            f"<div style='background:{color};width:{max(pct, 0.5):.1f}%;"
            f"height:9px;border-radius:4px;margin-bottom:3px'></div>"
        )
        st.markdown(bar, unsafe_allow_html=True)
        st.caption(f"{label}: {count} trees  ({pct:.1f}%)")

st.divider()

st.subheader("🎯 Cross-Reference Findings")

healthy_trees   = counts.get(1, 0)
unhealthy_trees = counts.get(0, 0)
yellow_trees    = counts.get(2, 0)

healthy_veg_pct  = stats[3]['pct']
moderate_veg_pct = stats[2]['pct']
severe_veg_pct   = stats[1]['pct']

findings_col, chart_col = st.columns([3, 2])

with findings_col:
    st.markdown(f"""
    - **{healthy_trees}** healthy trees detected in a zone with **{healthy_veg_pct:.1f}%** healthy satellite-measured vegetation
    - **{unhealthy_trees}** unhealthy trees may correlate with **{severe_veg_pct:.1f}%** severe stress areas
    - **{yellow_trees}** yellowing trees fall within **{moderate_veg_pct:.1f}%** moderate stress zones
    - Composite vegetation score: **{results['composite_mean'] * 100:.1f} / 100**
    """)

    if total_trees > 0:
        health_ratio = healthy_trees / total_trees

        st.divider()
        if health_ratio >= 0.70:
            st.session_state.economic_yield = "Positive"
            st.success("✅ **Economic Outlook: POSITIVE** — High proportion of healthy trees suggests strong yield potential.")
        elif health_ratio >= 0.50:
            st.session_state.economic_yield = "Moderate"
            st.warning("⚠️ **Economic Outlook: MODERATE** — Mixed health signals; targeted interventions recommended.")
        else:
            st.session_state.economic_yield = "At Risk"
            st.error("❌ **Economic Outlook: AT RISK** — Majority of trees show stress or disease; urgent action needed.")

with chart_col:
    fig, axes = plt.subplots(1, 2, figsize=(7, 4))

    veg_sizes  = [stats[i]['pct'] for i in range(4) if stats[i]['pct'] > 0]
    veg_labels = [stats[i]['label'] for i in range(4) if stats[i]['pct'] > 0]
    veg_colors = ["#d73027", "#fdae61", "#ffffbf", "#1a9850"][:len(veg_sizes)]
    axes[0].pie(veg_sizes, labels=veg_labels, colors=veg_colors,
                startangle=90, wedgeprops={'edgecolor': 'white'})
    axes[0].set_title("Vegetation Health", fontsize=9, fontweight='bold')

    tree_sizes  = [counts.get(i, 0) for i in range(3) if counts.get(i, 0) > 0]
    tree_labels_pie = [tree_labels[i] for i in range(3) if counts.get(i, 0) > 0]
    tree_colors_pie = [tree_colors[i] for i in range(3) if counts.get(i, 0) > 0]
    if tree_sizes:
        axes[1].pie(tree_sizes, labels=tree_labels_pie, colors=tree_colors_pie,
                    startangle=90, wedgeprops={'edgecolor': 'white'})
    axes[1].set_title("Tree Detection", fontsize=9, fontweight='bold')

    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

st.divider()

st.subheader("📥 Export")

export_col1, export_col2 = st.columns(2)

with export_col1:
    if st.button("📄 Generate Summary Report"):
        lines = [
            "# The Guardian — Combined Analysis Report",
            "",
            f"**Total Area:** {total_area:.2f} km²",
            f"**Composite Health Score:** {results['composite_mean'] * 100:.1f} / 100",
            f"**Vegetation Cover:** {st.session_state.get('vegetation_cover', 0):.1f}%",
            "",
            "## Vegetation Health Classes",
        ]
        for cid, data in stats.items():
            lines.append(f"- {data['label']}: {data['area_km2']:.3f} km²  ({data['pct']:.1f}%)")

        lines += [
            "",
            "## Tree Detection",
            f"- Total: {total_trees}",
            f"- Healthy: {counts.get(1, 0)}",
            f"- Unhealthy: {counts.get(0, 0)}",
            f"- Yellow: {counts.get(2, 0)}",
            "",
            f"## Economic Outlook",
            f"**{st.session_state.get('economic_yield', 'N/A')}**",
        ]

        report_text = "\n".join(lines)

        st.download_button(
            "⬇️ Download Report (.md)",
            data=report_text,
            file_name="guardian_analysis_report.md",
            mime="text/markdown"
        )

with export_col2:
    if st.button("📊 Export Statistics CSV"):
        import csv
        import io

        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["Category", "Label", "Value", "Unit"])

        writer.writerow(["Vegetation", "Total Area", f"{total_area:.4f}", "km²"])
        writer.writerow(["Vegetation", "Composite Score", f"{results['composite_mean']:.4f}", "0-1"])

        for cid, data in stats.items():
            writer.writerow(["Vegetation", data['label'] + " area",  f"{data['area_km2']:.4f}", "km²"])
            writer.writerow(["Vegetation", data['label'] + " share", f"{data['pct']:.2f}",      "%"])

        writer.writerow(["Trees", "Total", total_trees, "count"])
        for i, label in enumerate(tree_labels):
            writer.writerow(["Trees", label, counts.get(i, 0), "count"])

        for name, arr in indices.items():
            if arr is not None:
                writer.writerow(["Index", name + " mean", f"{float(np.nanmean(arr)):.4f}", ""])

        st.download_button(
            "⬇️ Download CSV",
            data=buf.getvalue(),
            file_name="guardian_statistics.csv",
            mime="text/csv"
        )
