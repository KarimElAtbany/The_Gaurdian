import io
from datetime import datetime
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, Image as RLImage, KeepTogether
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from utils.translations import t

# ── Guardian Brand Palette ────────────────────────────────────────────────────
DARK_SLATE   = colors.HexColor("#4A5759")   # primary dark
MID_BLUE     = colors.HexColor("#219EBC")   # accent blue
LIGHT_TEAL   = colors.HexColor("#EAF4F7")   # light card background
MUTED_TEAL   = colors.HexColor("#84A59D")   # secondary text / subtle accents
GREY_DARK    = colors.HexColor("#2C3A3C")
GREY_MID     = colors.HexColor("#6B7B7D")
GREY_LIGHT   = colors.HexColor("#F7F7F7")
WHITE        = colors.white

PAGE_W, PAGE_H = A4
CONTENT_W = PAGE_W - 4 * cm

# ── Arabic font registration ──────────────────────────────────────────────────
_AMIRI_FONT  = "Amiri"
_AMIRI_PATH  = Path(__file__).parent.parent / "assets" / "Amiri-Regular.ttf"
_AMIRI_REGISTERED = False

def _ensure_arabic_font():
    global _AMIRI_REGISTERED
    if not _AMIRI_REGISTERED and _AMIRI_PATH.exists():
        pdfmetrics.registerFont(TTFont(_AMIRI_FONT, str(_AMIRI_PATH)))
        _AMIRI_REGISTERED = True
    return _AMIRI_REGISTERED


def _ensure_arabic_deps():
    """Install arabic-reshaper and python-bidi into the running Python if missing."""
    try:
        import arabic_reshaper  # noqa: F401
        from bidi.algorithm import get_display  # noqa: F401
    except ImportError:
        import subprocess, sys
        subprocess.run(
            [sys.executable, "-m", "pip", "install",
             "arabic-reshaper", "python-bidi", "--quiet"],
            check=False
        )


def _ar(text: str) -> str:
    """Reshape + bidi — use for single-line text (headings, labels, table cells)."""
    _ensure_arabic_deps()
    try:
        import arabic_reshaper
        from bidi.algorithm import get_display
        # base_dir='R' forces RTL base direction — critical for text that starts
        # with numbers or Latin words (e.g. "77.9% من..." or "NDVI عالي")
        # Without it, get_display auto-detects as LTR and scrambles the output.
        return get_display(arabic_reshaper.reshape(text), base_dir='R')
    except Exception:
        return text


def _txt(text: str, lang: str) -> str:
    """Apply Arabic shaping when lang=='ar', otherwise return as-is."""
    if lang == "ar":
        return _ar(text)
    return text


def _ar_paragraphs(text: str, style, _unused=None) -> list:
    """
    Render an Arabic paragraph as a list of ReportLab Paragraphs — one per
    visual line.

    WHY NOT PIL images:
      arabic_reshaper produces Presentation-Form codepoints (U+FE70–U+FEFF).
      PIL/FreeType renders these per-glyph without OpenType GSUB, so on some
      platforms (e.g. Railway's python:3.12-slim) the characters appear
      disconnected.  ReportLab uses the same FreeType path BUT the Amiri font
      has already been registered at startup with its full glyph table, and
      the section/sub headings (which use this path) render correctly.

    APPROACH:
      1. Measure word widths with PIL/FreeType (measurement only, not rendering).
      2. Split into lines that fit the content column.
      3. Apply _ar() (reshape + bidi with base_dir='R') to each line.
      4. Return one ReportLab Paragraph per line — rendered by ReportLab with
         the registered Amiri font, giving the same quality as headings.
    """
    _ensure_arabic_deps()
    from PIL import Image as PILImage, ImageDraw, ImageFont
    import arabic_reshaper
    from bidi.algorithm import get_display

    # ── Measure word widths with PIL (measurement only) ───────────────────────
    DPI        = 150
    PT_TO_PX   = DPI / 72.0
    font_px    = max(10, int(style.fontSize * PT_TO_PX))
    content_px = int(CONTENT_W * PT_TO_PX)
    pad_x      = int(font_px * 0.4)

    try:
        mfont = ImageFont.truetype(str(_AMIRI_PATH), font_px)
    except Exception:
        mfont = None

    def _measure(s: str) -> int:
        """Return pixel width of reshaped+bidi string."""
        bidi_s = get_display(arabic_reshaper.reshape(s), base_dir='R')
        if mfont is None:
            return len(s) * font_px  # rough fallback
        tmp = PILImage.new("RGB", (1, 1))
        bb  = ImageDraw.Draw(tmp).textbbox((0, 0), bidi_s, font=mfont)
        return bb[2] - bb[0]

    # ── Word-wrap ──────────────────────────────────────────────────────────────
    words   = text.split()
    lines   = []
    current = []
    max_px  = content_px - 2 * pad_x

    for word in words:
        candidate = " ".join(current + [word])
        if current and _measure(candidate) > max_px:
            lines.append(" ".join(current))
            current = [word]
        else:
            current.append(word)
    if current:
        lines.append(" ".join(current))

    # ── Render each line as a ReportLab Paragraph (same path as headings) ─────
    result = []
    for line in lines:
        shaped = _ar(line)            # reshape + bidi with base_dir='R'
        result.append(Paragraph(shaped, style))
    return result if result else [Paragraph(_ar(text), style)]


def _logo_path():
    base = Path(__file__).parent.parent / "graphic"
    for name in ("logo.png", "logo.svg"):
        p = base / name
        if p.exists():
            return p
    return None


def _make_styles(lang: str = "en"):
    base     = getSampleStyleSheet()
    is_ar    = lang == "ar"
    has_font = _ensure_arabic_font() if is_ar else False
    body_font = _AMIRI_FONT if (is_ar and has_font) else "Helvetica"
    bold_font = _AMIRI_FONT if (is_ar and has_font) else "Helvetica-Bold"
    align_body   = TA_RIGHT if is_ar else TA_LEFT
    align_center = TA_CENTER

    return dict(
        cover_title=ParagraphStyle(
            "CoverTitle", parent=base["Title"],
            fontSize=26, textColor=WHITE, alignment=align_center,
            spaceAfter=4, leading=32, fontName=bold_font
        ),
        cover_sub=ParagraphStyle(
            "CoverSub", parent=base["Normal"],
            fontSize=11, textColor=colors.HexColor("#B8D4DC"),
            alignment=align_center, spaceAfter=4, fontName=body_font
        ),
        section_heading=ParagraphStyle(
            "SectionHeading", parent=base["Heading1"],
            fontSize=13, textColor=WHITE, backColor=MID_BLUE,
            spaceBefore=14, spaceAfter=8, leading=20,
            fontName=bold_font, borderPad=7, alignment=align_body
        ),
        sub_heading=ParagraphStyle(
            "SubHeading", parent=base["Heading2"],
            fontSize=10, textColor=DARK_SLATE,
            spaceBefore=8, spaceAfter=4, fontName=bold_font,
            alignment=align_body
        ),
        body=ParagraphStyle(
            "Body", parent=base["Normal"],
            fontSize=9, textColor=GREY_DARK,
            spaceAfter=4, leading=14, fontName=body_font,
            alignment=align_body
        ),
        highlight=ParagraphStyle(
            "Highlight", parent=base["Normal"],
            fontSize=10, textColor=DARK_SLATE, fontName=bold_font,
            backColor=LIGHT_TEAL, borderPad=7, spaceAfter=6, leading=16,
            alignment=align_body
        ),
        label=ParagraphStyle(
            "Label", parent=base["Normal"],
            fontSize=8, textColor=MUTED_TEAL, fontName=body_font,
            spaceAfter=2, leading=12, alignment=align_body
        ),
    )


def _fig_to_rl_image(fig, width_cm=17):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    buf.seek(0)
    w = width_cm * cm
    return RLImage(buf, width=w, height=w * 0.6)


def _ndarray_to_rl_image(arr_rgb, width_cm=12):
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.imshow(arr_rgb)
    ax.axis("off")
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=120, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    w = width_cm * cm
    return RLImage(buf, width=w, height=w)


def _cover_page(story, styles, product_id, bbox, report_date, logo_path, lang):
    is_ar  = lang == "ar"
    align  = TA_RIGHT if is_ar else TA_CENTER

    # ── Brand header bar ─────────────────────────────────────────────────────
    header_data = [[Paragraph(
        '<font color="white"><b>THE GUARDIAN</b></font>',
        ParagraphStyle("hdr_title", alignment=TA_CENTER,
                       fontSize=22, leading=28, fontName="Helvetica-Bold")
    )]]
    hdr_tbl = Table(header_data, colWidths=[CONTENT_W])
    hdr_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), MID_BLUE),
        ("TOPPADDING",    (0, 0), (-1, -1), 18),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 18),
        ("LEFTPADDING",   (0, 0), (-1, -1), 12),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 12),
    ]))
    story.append(hdr_tbl)
    story.append(Spacer(1, 0.5 * cm))

    # sub-header bar
    sub_text = _txt(
        "الوادي الجديد · مراقب النخيل والغطاء النباتي · فريق إيكو" if is_ar
        else "El Wadi El Gedid  ·  Palm & Vegetation Monitor  ·  Eco Team",
        lang
    )
    sub_data = [[Paragraph(
        f'<font color="#B8D4DC">{sub_text}</font>',
        ParagraphStyle("hdr_sub", alignment=TA_CENTER,
                       fontSize=9, leading=14, fontName="Helvetica")
    )]]
    sub_tbl = Table(sub_data, colWidths=[CONTENT_W])
    sub_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), DARK_SLATE),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(sub_tbl)
    story.append(Spacer(1, 0.8 * cm))

    # ── Logo ─────────────────────────────────────────────────────────────────
    if logo_path and logo_path.suffix == ".png":
        logo = RLImage(str(logo_path), width=5.0 * cm, height=2.0 * cm)
        logo.hAlign = "CENTER"
        story.append(logo)
        story.append(Spacer(1, 0.4 * cm))

    # ── Report type label ────────────────────────────────────────────────────
    story.append(Paragraph(
        _txt(t("rpt_title", lang), lang), styles["cover_sub"]
    ))
    story.append(Spacer(1, 0.4 * cm))
    story.append(HRFlowable(width="100%", thickness=1.5, color=MID_BLUE))
    story.append(Spacer(1, 0.8 * cm))

    # ── Metadata table ───────────────────────────────────────────────────────
    if bbox:
        bbox_str = f"{bbox[0]:.4f}°E, {bbox[1]:.4f}°N  →  {bbox[2]:.4f}°E, {bbox[3]:.4f}°N"
    else:
        bbox_str = _txt(t("rpt_not_specified", lang), lang)

    meta_rows = [
        [_txt(t("rpt_date_label", lang), lang),  report_date],
        [_txt(t("rpt_product",    lang), lang),  product_id or _txt(t("rpt_not_specified", lang), lang)],
        [_txt(t("rpt_aoi",        lang), lang),  bbox_str],
        [_txt(t("rpt_source",     lang), lang),  _txt(t("rpt_source_val", lang), lang)],
        [_txt(t("rpt_model",      lang), lang),  _txt(t("rpt_model_val",  lang), lang)],
        [_txt(t("rpt_platform",   lang), lang),  _txt(t("rpt_platform_val", lang), lang)],
    ]

    col_label_w = 5 * cm
    col_val_w   = 11.5 * cm
    if is_ar:
        # swap column order for RTL: value | label
        meta_rows = [[v, k] for k, v in meta_rows]

    tbl = Table(meta_rows, colWidths=[col_label_w, col_val_w])
    tbl.setStyle(TableStyle([
        ("BACKGROUND",     (0, 0), (0, -1), LIGHT_TEAL),
        ("TEXTCOLOR",      (0, 0), (0, -1), DARK_SLATE),
        ("FONTNAME",       (0, 0), (0, -1), styles["body"].fontName),
        ("FONTNAME",       (1, 0), (1, -1), styles["body"].fontName),
        ("FONTSIZE",       (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [WHITE, GREY_LIGHT]),
        ("GRID",           (0, 0), (-1, -1), 0.4, colors.HexColor("#C8D8D5")),
        ("PADDING",        (0, 0), (-1, -1), 7),
        ("VALIGN",         (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN",          (0, 0), (-1, -1), "LEFT"),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 1.2 * cm))

    # ── Disclaimer ───────────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=0.5, color=MUTED_TEAL))
    story.append(Spacer(1, 0.3 * cm))
    if is_ar:
        for p in _ar_paragraphs(t("rpt_disclaimer", lang), styles["body"], CONTENT_W):
            story.append(p)
    else:
        story.append(Paragraph(t("rpt_disclaimer", lang), styles["body"]))
    story.append(PageBreak())


def _ndvi_section(story, styles, ndvi_results, health_plot_fig, lang):
    is_ar = lang == "ar"

    story.append(Paragraph(
        _txt(t("rpt_s1_title", lang), lang),
        styles["section_heading"]
    ))
    story.append(Spacer(1, 0.3 * cm))

    stats      = ndvi_results["stats"]
    total_area = ndvi_results["total_area"]

    story.append(Paragraph(_txt(t("rpt_overview", lang), lang), styles["sub_heading"]))
    overview_text = t("rpt_s1_overview", lang).format(area=total_area)
    if is_ar:
        for p in _ar_paragraphs(overview_text, styles["body"]):
            story.append(p)
    else:
        story.append(Paragraph(overview_text, styles["body"]))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph(_txt(t("rpt_health_stats", lang), lang), styles["sub_heading"]))
    class_colors_hex = ["#6B6B6B", "#fdae61", "#a8d576", "#1a9850"]

    class_labels_map = {
        0: _txt(t("rpt_class0", lang), lang),
        1: _txt(t("rpt_class1", lang), lang),
        2: _txt(t("rpt_class2", lang), lang),
        3: _txt(t("rpt_class3", lang), lang),
    }

    hdr = [
        _txt(t("rpt_col_class",    lang), lang),
        _txt(t("rpt_col_area",     lang), lang),
        _txt(t("rpt_col_coverage", lang), lang),
        _txt(t("rpt_col_pixels",   lang), lang),
    ]
    if is_ar:
        hdr = list(reversed(hdr))

    rows = [hdr]
    for cid, data in stats.items():
        label = class_labels_map.get(cid, data["label"])
        row = [
            label,
            f"{data['area_km2']:.4f}",
            f"{data['pct']:.1f}%",
            f"{data['pixels']:,}"
        ]
        if is_ar:
            row = list(reversed(row))
        rows.append(row)

    tbl = Table(rows, colWidths=[5.5 * cm, 3.5 * cm, 3.5 * cm, 4 * cm])
    ts = TableStyle([
        ("BACKGROUND",     (0, 0), (-1, 0), DARK_SLATE),
        ("TEXTCOLOR",      (0, 0), (-1, 0), WHITE),
        ("FONTNAME",       (0, 0), (-1, -1), styles["body"].fontName),
        ("FONTSIZE",       (0, 0), (-1, -1), 9),
        ("ALIGN",          (1, 0), (-1, -1), "CENTER"),
        ("ALIGN",          (0, 0), (0, -1),  "LEFT"),
        ("GRID",           (0, 0), (-1, -1), 0.4, colors.HexColor("#C8D8D5")),
        ("PADDING",        (0, 0), (-1, -1), 7),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, GREY_LIGHT]),
    ])
    label_col = -1 if is_ar else 0
    for i in range(4):
        ts.add("BACKGROUND", (label_col, i + 1), (label_col, i + 1),
               colors.HexColor(class_colors_hex[i] + "88"))
    tbl.setStyle(ts)
    story.append(tbl)

    if health_plot_fig is not None:
        story.append(Spacer(1, 0.6 * cm))
        story.append(Paragraph(_txt(t("rpt_viz", lang), lang), styles["sub_heading"]))
        story.append(_fig_to_rl_image(health_plot_fig, width_cm=17))

    story.append(PageBreak())


def _detection_section(story, styles, class_counts, lang, yolo_annotated=None):
    is_ar = lang == "ar"
    total = sum(class_counts.values())

    story.append(Paragraph(
        _txt(t("rpt_s2_title", lang), lang),
        styles["section_heading"]
    ))
    story.append(Spacer(1, 0.3 * cm))

    story.append(Paragraph(_txt(t("rpt_overview", lang), lang), styles["sub_heading"]))
    overview_text = t("rpt_s2_overview", lang).format(total=total)
    if is_ar:
        for p in _ar_paragraphs(overview_text, styles["body"]):
            story.append(p)
    else:
        story.append(Paragraph(overview_text, styles["body"]))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph(_txt(t("rpt_detect_summary", lang), lang), styles["sub_heading"]))
    label_map = {
        0: _txt(t("rpt_crit_condition", lang), lang),
        1: _txt(t("rpt_healthy",        lang), lang),
        2: _txt(t("rpt_early_stress",   lang), lang),
    }
    color_map = {0: "#d73027", 1: "#1a9850", 2: "#fdae61"}

    hdr = [
        _txt(t("rpt_col_condition",  lang), lang),
        _txt(t("rpt_col_count",      lang), lang),
        _txt(t("rpt_col_proportion", lang), lang),
    ]
    if is_ar:
        hdr = list(reversed(hdr))

    rows = [hdr]
    for cls, label in label_map.items():
        count = class_counts.get(cls, 0)
        pct   = (count / total * 100) if total > 0 else 0
        row = [label, f"{count:,}", f"{pct:.1f}%"]
        if is_ar:
            row = list(reversed(row))
        rows.append(row)

    total_row = [_txt(t("rpt_total", lang), lang), f"{total:,}", "100.0%"]
    if is_ar:
        total_row = list(reversed(total_row))
    rows.append(total_row)

    tbl = Table(rows, colWidths=[6 * cm, 3.5 * cm, 4 * cm])
    ts = TableStyle([
        ("BACKGROUND",     (0, 0), (-1, 0), DARK_SLATE),
        ("TEXTCOLOR",      (0, 0), (-1, 0), WHITE),
        ("FONTNAME",       (0, 0), (-1, -1), styles["body"].fontName),
        ("BACKGROUND",     (0, -1), (-1, -1), LIGHT_TEAL),
        ("TEXTCOLOR",      (0, -1), (-1, -1), DARK_SLATE),
        ("FONTSIZE",       (0, 0), (-1, -1), 9),
        ("ALIGN",          (1, 0), (-1, -1), "CENTER"),
        ("ALIGN",          (0, 0), (0, -1),  "LEFT"),
        ("GRID",           (0, 0), (-1, -1), 0.4, colors.HexColor("#C8D8D5")),
        ("PADDING",        (0, 0), (-1, -1), 7),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [WHITE, GREY_LIGHT]),
    ])
    label_col = -1 if is_ar else 0
    for i, cls in enumerate(range(3)):
        ts.add("BACKGROUND", (label_col, i + 1), (label_col, i + 1),
               colors.HexColor(color_map[cls] + "88"))
    tbl.setStyle(ts)
    story.append(tbl)

    if yolo_annotated is not None:
        import cv2
        story.append(Spacer(1, 0.6 * cm))
        legend = _txt(t("rpt_legend", lang), lang)
        map_title = _txt(t("rpt_annot_map", lang), lang)
        story.append(Paragraph(
            f"{map_title}  <font size='8' color='#6B7B7D'>{legend}</font>",
            styles["sub_heading"]
        ))
        rgb = cv2.cvtColor(yolo_annotated, cv2.COLOR_BGR2RGB)
        story.append(_ndarray_to_rl_image(rgb, width_cm=14))

    story.append(PageBreak())


def _insights_section(story, styles, ndvi_results, class_counts, economic_yield, lang):
    is_ar = lang == "ar"

    story.append(Paragraph(
        _txt(t("rpt_s3_title", lang), lang),
        styles["section_heading"]
    ))
    story.append(Spacer(1, 0.3 * cm))

    stats           = ndvi_results["stats"]
    total           = sum(class_counts.values())
    healthy_trees   = class_counts.get(1, 0)
    unhealthy_trees = class_counts.get(0, 0)
    stressed_trees  = class_counts.get(2, 0)
    healthy_veg_pct  = stats[3]["pct"]
    moderate_veg_pct = stats[2]["pct"]
    severe_veg_pct   = stats[1]["pct"]

    story.append(Paragraph(_txt(t("rpt_key_findings", lang), lang), styles["sub_heading"]))
    findings = [
        t("rpt_finding1", lang).format(pct=healthy_veg_pct),
        t("rpt_finding2", lang).format(count=healthy_trees),
        t("rpt_finding3", lang).format(count=unhealthy_trees, pct=severe_veg_pct),
        t("rpt_finding4", lang).format(count=stressed_trees, pct=moderate_veg_pct),
    ]
    bullet = "• "
    for finding in findings:
        if is_ar:
            for p in _ar_paragraphs(f"{bullet}{finding}", styles["body"], CONTENT_W):
                story.append(p)
        else:
            story.append(Paragraph(f"{bullet}{finding}", styles["body"]))

    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph(_txt(t("rpt_econ_outlook", lang), lang), styles["sub_heading"]))

    if total > 0:
        health_ratio = healthy_trees / total
        pct = health_ratio * 100
        if health_ratio > 0.7:
            outlook_key = "rpt_positive"
            body_key    = "rpt_positive_body"
            out_color   = "#1a9850"
        elif health_ratio > 0.5:
            outlook_key = "rpt_moderate_outlook"
            body_key    = "rpt_moderate_body"
            out_color   = "#219EBC"
        else:
            outlook_key = "rpt_at_risk"
            body_key    = "rpt_at_risk_body"
            out_color   = "#d73027"

        outlook_label = _txt(t("rpt_econ_label", lang), lang)
        outlook_val   = _txt(t(outlook_key, lang), lang)
        story.append(Paragraph(
            f"{outlook_label} <b><font color='{out_color}'>{outlook_val}</font></b>",
            styles["highlight"]
        ))
        body_text = t(body_key, lang).format(pct=pct)
        if is_ar:
            for p in _ar_paragraphs(body_text, styles["body"]):
                story.append(p)
        else:
            story.append(Paragraph(body_text, styles["body"]))

    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph(_txt(t("rpt_recommendations", lang), lang), styles["sub_heading"]))
    for key in ["rpt_rec1", "rpt_rec2", "rpt_rec3", "rpt_rec4", "rpt_rec5"]:
        rec_text = f"• {t(key, lang)}"
        if is_ar:
            for p in _ar_paragraphs(rec_text, styles["body"]):
                story.append(p)
        else:
            story.append(Paragraph(rec_text, styles["body"]))


def generate_report(
    product_id, bbox,
    ndvi_results=None, health_plot_fig=None, true_color_rgb=None,
    class_counts=None, yolo_annotated=None,
    economic_yield=None,
    lang="en"
):
    buf        = io.BytesIO()
    styles     = _make_styles(lang)
    logo_path  = _logo_path()
    is_ar      = lang == "ar"

    if is_ar:
        report_date = datetime.now().strftime("%d/%m/%Y  ·  %H:%M UTC")
    else:
        report_date = datetime.now().strftime("%B %d, %Y  ·  %H:%M UTC")

    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=2 * cm,  bottomMargin=2.5 * cm,
        title="The Guardian — Vegetation Monitoring Report",
        author="The Guardian Platform  ·  Eco Team",
        subject="Palm & Vegetation Health Report  ·  El Wadi El Gedid"
    )

    story = []
    _cover_page(story, styles, product_id, bbox, report_date, logo_path, lang)

    if ndvi_results:
        _ndvi_section(story, styles, ndvi_results, health_plot_fig, lang)

    if class_counts:
        _detection_section(story, styles, class_counts, lang, yolo_annotated)

    if ndvi_results and class_counts:
        _insights_section(story, styles, ndvi_results, class_counts, economic_yield, lang)

    footer_font = _AMIRI_FONT if (is_ar and _AMIRI_REGISTERED) else "Helvetica"

    def _footer(canvas, doc):
        canvas.saveState()
        canvas.setFont(footer_font, 7)
        canvas.setFillColor(GREY_MID)
        footer_txt  = _txt(t("rpt_footer", lang), lang)
        page_label  = _txt(t("rpt_page",   lang), lang)
        if is_ar:
            canvas.drawRightString(
                PAGE_W - 2 * cm, 1.2 * cm, footer_txt
            )
            canvas.drawString(
                2 * cm, 1.2 * cm,
                f"{page_label} {doc.page}  ·  {datetime.now().strftime('%Y-%m-%d')}"
            )
        else:
            canvas.drawString(
                2 * cm, 1.2 * cm, footer_txt
            )
            canvas.drawRightString(
                PAGE_W - 2 * cm, 1.2 * cm,
                f"{page_label} {doc.page}  ·  {datetime.now().strftime('%Y-%m-%d')}"
            )
        canvas.setStrokeColor(MID_BLUE)
        canvas.setLineWidth(0.6)
        canvas.line(2 * cm, 1.5 * cm, PAGE_W - 2 * cm, 1.5 * cm)
        canvas.restoreState()

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    buf.seek(0)
    return buf
