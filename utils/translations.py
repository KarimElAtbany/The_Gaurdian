"""
Guardian Platform — Bilingual Translation Module (English / Arabic)
Scientific index names (MSAVI, NDRE, NDWI, CIre, NDVI, Sentinel-2,
STAC, GeoJSON, GeoTIFF, YOLO) are intentionally kept in English
inside Arabic strings.
"""

_T = {
    # ─────────────────────────────────────────────────────────────────────────
    # SHARED / GLOBAL
    # ─────────────────────────────────────────────────────────────────────────
    "en": {
        "app_name":             "The Guardian",
        "eco_badge":            "Eco Team",
        "header_sub_home":      "El Wadi El Gedid · Palm & Vegetation Monitor",
        "header_sub_data":      "Data Acquisition",
        "header_sub_ai":        "AI Analysis",
        "header_sub_dash":      "Dashboard & Insights",
        "header_sub_ts":        "Time Series Analysis",
        "sidebar_nav_hint":     "Use the menu above to navigate between pages.",

        # ── Home page ────────────────────────────────────────────────────────
        "welcome_title":        "Welcome to The Guardian",
        "welcome_desc":         ("A satellite-powered platform for monitoring the health "
                                 "of date palm plantations in El Wadi El Gedid, Egypt — "
                                 "no technical knowledge required."),
        "step1_num":            "Step 1",
        "step1_title":          "Get Satellite Data",
        "step1_body":           ("Draw your farm area on the map and download the latest "
                                 "Sentinel-2 satellite images automatically — no sign-up needed."),
        "step2_num":            "Step 2",
        "step2_title":          "Run AI Analysis",
        "step2_body":           ("Our AI checks vegetation health across 4 scientific indicators "
                                 "and counts individual palm trees using computer vision."),
        "step3_num":            "Step 3",
        "step3_title":          "See Results & Export",
        "step3_body":           ("View your farm's health score, maps, and actionable recommendations. "
                                 "Export a PDF report or raw data in one click."),
        "banner_title":         "Powered by Sentinel-2 Satellite Imagery",
        "banner_sub":           ("Uses 4 scientific health indicators: Vegetation Density (MSAVI), "
                                 "Leaf Health (NDRE), Water Stress (NDWI), and Nutrient Status (CIre) "
                                 "— imagery updated every 5 days."),
        "footer_text":          "The Guardian · Built by Eco Team · El Wadi El Gedid Palm & Vegetation Monitor",

        # ── Home — Added Value & Sensor Integration ───────────────────────────
        "home_added_value_title": "Why The Guardian?",
        "home_av_bullet1":      "Detect vegetation stress weeks before it becomes visible crop damage — act early, save cost.",
        "home_av_bullet2":      "Monitor water stress (NDWI) across the entire farm to optimize irrigation in arid farmland.",
        "home_av_bullet3":      "Correlate satellite stress hotspots with date palm Red Weevil risk zones for early pest intervention.",
        "home_av_bullet4":      "No field visits needed — Sentinel-2 satellite imagery refreshed automatically every 5 days.",
        "home_sensor_title":    "Future: IoT Sensor Integration",
        "home_sensor_body":     ("The Guardian is designed to integrate with IoT soil moisture sensors, temperature probes, "
                                 "and Red Palm Weevil acoustic traps. Field sensor data will overlay on satellite maps "
                                 "to create a unified precision-agriculture dashboard — bridging remote sensing with ground-truth."),

        # ── Data Acquisition ─────────────────────────────────────────────────
        "section_data":         "Data Acquisition",
        "quick_locations":      "Quick Locations",
        "location_search":      "Location Search",
        "coord_input":          "Coordinates (e.g., 25.65N, 28.95E)",
        "go_to_location":       "Go to Location",
        "invalid_coords":       "Invalid coordinates format",
        "date_range":           "Date Range",
        "date_from":            "From",
        "date_to":              "To",
        "filters":              "Filters",
        "max_cloud":            "Max Cloud Cover %",
        # "collection" removed — hardcoded to sentinel-2-l2a
        "max_results":          "Max Results",
        "draw_aoi":             "Draw Area of Interest",
        "search_products":      "Search Products",
        "search_stac_btn":      "Search STAC Catalog",
        "searching_stac":       "Searching STAC catalog...",
        "no_products":          "No products found. Try adjusting filters.",
        "available_products":   "Available Products",
        "cached":               "Cached",
        "load_from_cache":      "Load from Cache",
        "download_bands_btn":   "Download Bands",
        "downloading_bands":    "Downloading 8 spectral bands…",
        "download_complete":    "Download complete",
        "download_incomplete":  "Download incomplete",
        "downloaded_products":  "Downloaded Products",
        "date_label":           "Date",
        "cloud_label":          "Cloud",

        # ── Time Series ──────────────────────────────────────────────────────
        "select_for_analysis":  "Select for Analysis",
        "ts_add_btn":           "Add to Time Series",
        "ts_added":             "Added to time series queue ✓",
        "ts_already_added":     "Already in time series queue",
        "ts_queue_title":       "Time Series — Product Queue",
        "ts_queue_empty_title": "No products queued yet",
        "ts_queue_empty_body":  ("Go to Data Acquisition, search for products across different dates, "
                                 "download or load each one, then click \"Add to Time Series\". "
                                 "Add at least 2 dates to enable comparison."),
        "ts_run_btn":           "Run Time Series Analysis",
        "ts_min_products":      "Add at least 2 products (different dates) to enable comparison.",
        "ts_processing":        "Processing product",
        "ts_of":                "of",
        "ts_results_title":     "Time Series Results",
        "ts_health_trend":      "Health Score Over Time",
        "ts_veg_distribution":  "Vegetation Class Distribution",
        "ts_expansion_title":   "Expansion Summary",
        "ts_change_title":      "Change Detection  —  First vs Latest",
        "ts_improved":          "Improved",
        "ts_degraded":          "Degraded",
        "ts_stable":            "Stable",
        "ts_net_change":        "Net Healthy Area Change",
        "ts_trend_expanding":   "Expanding",
        "ts_trend_stable":      "Stable",
        "ts_trend_degrading":   "Degrading",
        "ts_table_title":       "Summary Table",
        "ts_date_col":          "Date",
        "ts_score_col":         "Health Score",
        "ts_healthy_col":       "Healthy km²",
        "ts_moderate_col":      "Moderate km²",
        "ts_severe_col":        "Severe km²",
        "ts_bare_col":          "Bare km²",
        "ts_clear_queue":       "Clear Queue",
        "ts_clear_results":     "Clear Results",
        "ts_remove":            "Remove",
        "ts_no_aoi":            "No AOI defined. Draw an area on the Data Acquisition map first.",
        "ts_one_product":       "Only 1 product processed — add at least 2 to see comparison charts.",

        # ── AI Analysis — shared ─────────────────────────────────────────────
        "section_ai":           "AI Analysis",
        "tab_ndvi":             "NDVI Vegetation Health",
        "tab_detection":        "Tree Detection",
        "tab_iot":              "🔒 Well Consumption (IoT)",
        "iot_analysis_title":   "Analysis: The platform uses this data to:",
        "iot_bullet1":          "Calculate Water Production: Total volume extracted over time.",
        "iot_bullet2":          "Identify Water Loss: Detecting leaks or unmetered discharge.",
        "iot_bullet3":          "Monitor Extraction Rates: Ensuring the well does not exceed sustainable groundwater recharge limits.",
        "iot_irr_title":        "Irrigation Intelligence:",
        "iot_irr_body":         (
            "Requirement Calculation: One of the most advanced features is the ability to calculate "
            "the \"water required for complete irrigation.\" This suggests the platform may be integrating "
            "soil moisture data or evapotranspiration (ET) models to tell the farmer exactly when to stop "
            "pumping, preventing over-watering and aquifer depletion."
        ),
        "no_downloaded":        ("&#9432; No downloaded products. "
                                 "Please go to <strong>Data Acquisition</strong> first."),

        # ── AI Analysis — NDVI sidebar ───────────────────────────────────────
        "sidebar_satellite":    "🛰 Satellite Product",
        "select_image":         "Select image",
        "sidebar_farm_area":    "📐 Farm Area",
        "use_drawn_area":       "Use area drawn on map",
        "paste_geojson":        "Paste GeoJSON polygon",
        "area_from_map":        "Area selected from map ✓",
        "no_area_drawn":        "No area drawn. Go to Data Acquisition first.",
        "advanced_settings":    "⚙️ Advanced Settings",
        "sensitivity_thresh":   "Sensitivity thresholds",
        "no_veg_threshold":     "No vegetation threshold",
        "critical_threshold":   "Critical stress threshold",
        "moderate_threshold":   "Moderate stress threshold",
        "indicator_weights":    "Indicator weights",
        "weight_msavi":         "Vegetation Density",
        "weight_ndre":          "Leaf Health",
        "weight_ndwi":          "Water Stress",
        "weight_cire":          "Nutrient Level",
        "run_analysis_btn":     "Run Health Analysis",
        "computing_analysis":   "Computing multi-index health analysis…",
        "provide_aoi":          "Please provide an AOI",
        "analysis_complete":    "Health Analysis complete",

        # ── AI Analysis — NDVI results ───────────────────────────────────────
        "overall_veg_health":   "Overall Vegetation Health",
        "based_on_4":           "Based on 4 scientific health indicators across your selected area",
        "status_good":          "Good",
        "status_fair":          "Fair",
        "status_poor":          "Poor",
        "veg_cover_lbl":        "Vegetation Cover",
        "veg_cover_desc":       "of your total selected area has some plant cover",
        "healthy_area_lbl":     "Healthy Area",
        "stressed_area_lbl":    "Stressed Area",
        "stressed_area_desc":   "needs attention",
        "no_veg_lbl":           "No Vegetation",
        "no_veg_desc":          "bare or inactive land",
        "health_map_title":     "Health Map",
        "what_measured":        "What We Measured",
        "index_msavi_name":     "Vegetation Density",
        "index_msavi_desc":     "How green and dense the plant cover is, adjusted for desert soil",
        "index_ndre_name":      "Leaf Health",
        "index_ndre_desc":      "Chlorophyll level — catches stress 2–4 weeks before it's visible",
        "index_ndwi_name":      "Water Stress",
        "index_ndwi_desc":      "How much water the plants contain — detects drought early",
        "index_cire_name":      "Nutrient Level",
        "index_cire_desc":      "Plant nutrient status — flags deficiencies in nitrogen & magnesium",

        # ── AI Analysis — Recommendations ────────────────────────────────────
        "section_recs":         "Recommendations",
        "rec_bare_title":       "High bare/dead area detected.",
        "rec_severe_title":     "Severe stress zones need urgent attention.",
        "rec_moderate_title":   "Moderate stress — act before it worsens.",
        "rec_healthy_title":    "Vegetation is mostly healthy.",
        "rec_declining_title":  "Health is acceptable but declining areas need monitoring.",
        "rec_declining_body":   "Run Tree Detection to correlate vegetation stress with individual palm health.",
        "rec_poor_title":       "Overall vegetation health is poor.",
        "rec_poor_body":        "Immediate ground-truth survey is strongly recommended.",
        "rec_detect_title":     "Run Tree Detection for full cross-analysis.",
        "rec_detect_body":      "Combine these vegetation results with palm tree counting for an economic outlook.",

        # ── AI Analysis — Tree Detection ─────────────────────────────────────
        "detection_settings":   "🌴 Detection Settings",
        "model_ready":          "AI model ready ✓",
        "no_model":             "No AI model found in models/ folder",
        "conf_thresh_lbl":      "Detection Confidence Threshold",
        "conf_thresh_help":     ("Minimum confidence score for a detection to be counted. "
                                 "Lower values detect more trees but may include false positives."),
        "section_palm_census":  "Palm Census & Health Classification",
        "highres_title":        "High-Resolution Imaging Mode",
        "highres_body":         ("Acquires Google Maps satellite imagery at ~0.3 m/pixel resolution "
                                 "for precise individual palm detection — significantly sharper than "
                                 "the 10 m/pixel Sentinel-2 product. No additional downloads required; "
                                 "the image is captured automatically from your drawn area of interest."),
        "no_area_selected":     ("&#9432; No area selected. Go to <strong>Data Acquisition</strong> "
                                 "and draw your farm boundary first."),
        "no_model_error":       "AI model not found. Place a .pt model file inside the models/ folder.",
        "acquire_btn":          "🛰️  Acquire High-Resolution Image & Run Detection",
        "capturing_spinner":    "Capturing high-resolution satellite image from Google Maps…",
        "running_detection":    "Running AI detection on high-resolution image…",
        "caption_aoi":          "📍 Area of Interest — Google Maps Satellite",
        "caption_detections":   "🌴 Palm Tree Detection Results",
        "section_census":       "Census Results",
        "total_palms_lbl":      "Total Palms Detected",
        "total_palms_desc":     "within the area of interest",
        "healthy_lbl":          "Healthy",
        "early_stress_lbl":     "Early Stress",
        "early_stress_desc":    "monitor closely",
        "critical_lbl":         "Critical Condition",
        "critical_desc":        "urgent intervention",

        # ── Dashboard ────────────────────────────────────────────────────────
        "overall_health_lbl":   "Your Farm's Overall Health",
        "palms_counted_lbl":    "Palms Counted",
        "palms_counted_desc":   "trees detected by AI in your area",
        "healthy_area_desc_d":  "in good condition",
        "economic_outlook_lbl": "Economic Outlook",
        "economic_outlook_desc":"based on tree and vegetation health",
        "status_no_data":       "No Data",
        "no_analysis_title":    "No analysis run yet",
        "no_analysis_body":     ("Go to <strong>AI Analysis</strong> to run vegetation health "
                                 "analysis and tree detection, then come back here to see your "
                                 "full dashboard."),
        "maps_title":           "Maps &amp; Visual Results",
        "veg_map_caption":      "Vegetation Health Map",
        "run_veg_health":       "Run <strong>Vegetation Health</strong> in AI Analysis",
        "run_tree_detect":      "Run <strong>Tree Detection</strong> in AI Analysis",
        "veg_breakdown_title":  "Vegetation Health Breakdown",
        "bar_healthy":          "Healthy",
        "bar_moderate":         "Moderate Stress",
        "bar_critical":         "Critical Stress",
        "bar_no_veg":           "No Vegetation",
        "tree_health_title":    "Tree Health Summary",
        "healthy_trees_lbl":    "Healthy Trees 🟢",
        "early_stress_lbl_d":   "Early Stress 🟡",
        "critical_lbl_d":       "Critical Condition 🔴",
        "of_detected_palms":    "% of detected palms",
        "monitor_closely":      "% — monitor closely",
        "urgent_intervention":  "% — urgent intervention",
        "econ_positive":        "Economic Outlook: Positive",
        "econ_positive_body":   ("Over 70% of your palms are healthy. "
                                 "The plantation is in good productive condition."),
        "econ_moderate":        "Economic Outlook: Moderate",
        "econ_moderate_body":   ("About half your palms are healthy. "
                                 "Monitor stressed trees closely to prevent further decline."),
        "econ_at_risk":         "Economic Outlook: At Risk",
        "econ_at_risk_body":    ("Less than half your palms are healthy. "
                                 "Immediate intervention is recommended."),
        "section_recs_d":       "Recommendations",
        "rec_d2":               "Apply targeted irrigation in stressed areas — water stress is the most common issue in this region.",
        "rec_d4":               "Schedule a follow-up satellite scan in 30 days to track whether conditions are improving.",
        "rec_d5":               "Download the PDF report below to share these findings with your agronomist or investor.",
        "hint_tree_detect":     "💡 Run **Tree Detection** in AI Analysis to unlock the full cross-reference insights and economic outlook.",
        "hint_veg_health":      "💡 Run **Vegetation Health** in AI Analysis to unlock the full cross-reference insights.",
        "section_export":       "Export Your Report",
        "pdf_lbl":              "PDF Report",
        "pdf_desc":             ("A professional report with your health maps, statistics, and economic "
                                 "outlook — ready to share with your team or investors."),
        "generate_pdf_btn":     "Generate PDF Report",
        "building_report":      "Building your report…",
        "run_analysis_first":   "Run at least one analysis before generating a report.",
        "report_ready":         "Report ready!",
        "download_pdf_btn":     "⬇️ Download PDF Report",
        "zip_lbl":              "Full Data Export",
        "zip_desc":             ("A ZIP archive with all raw data: health statistics as CSV, "
                                 "the GeoTIFF map file, and a metadata summary."),
        "export_all_btn":       "Export All Data",
        "packaging_data":       "Packaging your data…",
        "no_data_export":       "No data to export yet.",
        "export_ready":         "Export ready!",
        "download_zip_btn":     "⬇️ Download ZIP",
        # ── PDF Report strings ────────────────────────────────────────────────
        "rpt_title":            "Environmental Monitoring Report",
        "rpt_date_label":       "Report Date",
        "rpt_product":          "Satellite Product",
        "rpt_aoi":              "Area of Interest",
        "rpt_source":           "Data Source",
        "rpt_model":            "Detection Model",
        "rpt_platform":         "Platform",
        "rpt_not_specified":    "Not specified",
        "rpt_source_val":       "Sentinel-2 L2A (ESA Copernicus Programme)",
        "rpt_model_val":        "YOLOv8 — fine-tuned on aerial palm imagery",
        "rpt_platform_val":     "The Guardian Monitoring Platform  ·  Eco Team",
        "rpt_disclaimer":       (
            "This report was generated automatically by The Guardian platform using satellite imagery "
            "from the ESA Copernicus Sentinel-2 mission and an AI-based palm tree detection model. "
            "Results are provided for research, advisory, and investment purposes. "
            "Field verification is recommended before any operational decision is made."
        ),
        "rpt_s1_title":         "1.  Vegetation Health Analysis — Multi-Index Assessment",
        "rpt_overview":         "Overview",
        "rpt_s1_overview":      (
            "A multi-index vegetation health assessment was performed over a total valid area of "
            "<b>{area:.2f} km²</b>, using four complementary spectral indicators derived "
            "from Sentinel-2 imagery: Vegetation Density (MSAVI), Leaf Health (NDRE), "
            "Water Stress (NDWI), and Nutrient Status (CIre). "
            "Each pixel was classified into one of four health categories based on a weighted composite score."
        ),
        "rpt_health_stats":     "Health Classification Statistics",
        "rpt_col_class":        "Health Class",
        "rpt_col_area":         "Area (km²)",
        "rpt_col_coverage":     "Coverage (%)",
        "rpt_col_pixels":       "Pixel Count",
        "rpt_viz":              "Analysis Visualizations",
        "rpt_s2_title":         "2.  Palm Tree Census — AI Detection Results",
        "rpt_s2_overview":      (
            "A total of <b>{total:,} palm trees</b> were identified within the area of interest "
            "using a fine-tuned YOLOv8 deep learning model. High-resolution satellite imagery "
            "(~0.3 m/pixel from Google Maps) was used to ensure individual crown-level detection accuracy. "
            "Each detected tree was classified into one of three condition categories."
        ),
        "rpt_detect_summary":   "Detection Summary by Condition",
        "rpt_crit_condition":   "Critical Condition",
        "rpt_healthy":          "Healthy",
        "rpt_early_stress":     "Early Stress",
        "rpt_col_condition":    "Condition",
        "rpt_col_count":        "Count",
        "rpt_col_proportion":   "Proportion (%)",
        "rpt_total":            "TOTAL",
        "rpt_annot_map":        "Annotated Detection Map",
        "rpt_legend":           "(Green = Healthy · Orange = Early Stress · Red = Critical)",
        "rpt_s3_title":         "3.  Cross-Reference Analysis &amp; Economic Outlook",
        "rpt_key_findings":     "Key Findings",
        "rpt_finding1":         "Vegetation analysis indicates <b>{pct:.1f}%</b> of the monitored area supports healthy plant cover.",
        "rpt_finding2":         "<b>{count:,}</b> palms classified as healthy, correlating spatially with high-NDVI vegetation zones.",
        "rpt_finding3":         "<b>{count:,}</b> trees in critical condition correspond with <b>{pct:.1f}%</b> severe-stress vegetation.",
        "rpt_finding4":         "<b>{count:,}</b> early-stress trees detected within <b>{pct:.1f}%</b> moderate-stress zones — intervention is advised.",
        "rpt_econ_outlook":     "Economic Outlook",
        "rpt_positive":         "POSITIVE",
        "rpt_moderate_outlook": "MODERATE",
        "rpt_at_risk":          "AT RISK",
        "rpt_positive_body":    (
            "With {pct:.1f}% of palms in healthy condition, the plantation demonstrates strong "
            "productive capacity. Yield levels are expected to be at or above seasonal averages. "
            "Investment risk is assessed as LOW."
        ),
        "rpt_moderate_body":    (
            "With {pct:.1f}% healthy palms, overall productivity is acceptable. However, intervention "
            "in stressed and critical zones is recommended to prevent further decline. "
            "Investment risk is assessed as MEDIUM."
        ),
        "rpt_at_risk_body":     (
            "Only {pct:.1f}% of detected palms are healthy. Significant agronomic intervention is "
            "required. A measurable reduction in seasonal yield is anticipated if conditions persist. "
            "Investment risk is assessed as HIGH."
        ),
        "rpt_econ_label":       "Economic Outlook:",
        "rpt_recommendations":  "Actionable Recommendations",
        "rpt_rec1":             "Conduct a ground-truth field survey in all areas classified as Severe Stress or Critical Condition.",
        "rpt_rec2":             "Apply targeted irrigation to zones with NDWI values below threshold — water stress is the primary driver in this region.",
        "rpt_rec3":             "Inspect all Early Stress trees for early-stage pest or disease to enable cost-effective intervention.",
        "rpt_rec4":             "Apply foliar nutrient supplementation in areas where CIre index indicates nitrogen or magnesium deficiency.",
        "rpt_rec5":             "Schedule a repeat satellite acquisition in 30 days to track temporal change and measure intervention effectiveness.",
        "rpt_footer":           "The Guardian  ·  El Wadi El Gedid Palm & Vegetation Monitor  ·  Eco Team  ·  Confidential",
        "rpt_page":             "Page",
        "rpt_class0":           "No Vegetation",
        "rpt_class1":           "Critical Stress",
        "rpt_class2":           "Moderate Stress",
        "rpt_class3":           "Healthy",
    },

    # ─────────────────────────────────────────────────────────────────────────
    # ARABIC
    # ─────────────────────────────────────────────────────────────────────────
    "ar": {
        "app_name":             "The Guardian",
        "eco_badge":            "فريق إيكو",
        "header_sub_home":      "الوادي الجديد · مراقبة النخيل والغطاء النباتي",
        "header_sub_data":      "استحواذ البيانات",
        "header_sub_ai":        "تحليل الذكاء الاصطناعي",
        "header_sub_dash":      "لوحة التحكم والرؤى",
        "header_sub_ts":        "تحليل السلاسل الزمنية",
        "sidebar_nav_hint":     "استخدم القائمة أعلاه للتنقل بين الصفحات.",

        # ── Home page ────────────────────────────────────────────────────────
        "welcome_title":        "مرحباً بك في The Guardian",
        "welcome_desc":         ("منصة تعتمد على الأقمار الاصطناعية لمراقبة صحة مزارع النخيل "
                                 "في الوادي الجديد، مصر — لا تحتاج إلى خبرة تقنية."),
        "step1_num":            "الخطوة الأولى",
        "step1_title":          "احصل على بيانات الأقمار الاصطناعية",
        "step1_body":           ("ارسم حدود مزرعتك على الخريطة وحمّل أحدث صور "
                                 "Sentinel-2 تلقائياً — دون الحاجة إلى تسجيل."),
        "step2_num":            "الخطوة الثانية",
        "step2_title":          "شغّل تحليل الذكاء الاصطناعي",
        "step2_body":           ("يفحص الذكاء الاصطناعي صحة الغطاء النباتي عبر 4 مؤشرات علمية "
                                 "ويحصر أشجار النخيل بشكل فردي باستخدام رؤية الحاسوب."),
        "step3_num":            "الخطوة الثالثة",
        "step3_title":          "اعرض النتائج وصدّرها",
        "step3_body":           ("اطّلع على درجة صحة مزرعتك والخرائط والتوصيات القابلة للتنفيذ. "
                                 "صدّر تقرير PDF أو البيانات الخام بنقرة واحدة."),
        "banner_title":         "مدعوم بصور Sentinel-2 الاصطناعية",
        "banner_sub":           ("يستخدم 4 مؤشرات صحية علمية: كثافة النبات (MSAVI)، "
                                 "صحة الأوراق (NDRE)، إجهاد المياه (NDWI)، "
                                 "والمغذيات (CIre) — تتجدد الصور كل 5 أيام."),
        "footer_text":          "The Guardian · من تطوير فريق إيكو · مراقبة النخيل والنبات — الوادي الجديد",

        # ── Home — القيمة المضافة وتكامل المستشعرات ───────────────────────────
        "home_added_value_title": "لماذا The Guardian؟",
        "home_av_bullet1":      "اكتشف إجهاد النبات قبل أسابيع من ظهور الأضرار المرئية — تصرّف مبكرًا ووفّر التكاليف.",
        "home_av_bullet2":      "راقب إجهاد المياه عبر المزرعة بأكملها لتحسين الري في الأراضي الجافة.",
        "home_av_bullet3":      "اربط مناطق الإجهاد بالأقمار الصناعية بمناطق خطر سوسة النخيل الحمراء للتدخل المبكر.",
        "home_av_bullet4":      "لا حاجة لزيارات ميدانية — تتجدد صور Sentinel-2 تلقائيًا كل 5 أيام.",
        "home_sensor_title":    "الرؤية المستقبلية: تكامل مستشعرات إنترنت الأشياء",
        "home_sensor_body":     ("يعد مشروع ذا جارديان مشروع مستقل بذاته، لكن يمكن ربطه بمستشعرات رطوبة التربة ومجسّات الحرارة، وأفخاخ سوسة النخيل الصوتية عبر إنترنت الأشياء في المستقبل  و الحصول على نظام كامل يجمع بين الذكاء الاصطناعي و انترنت الأشياء ستتداخل بيانات المستشعرات الميدانية مع خرائط الأقمار الصناعية لإنشاء لوحة تحكم زراعة دقيقة موحّدة."),

        # ── Data Acquisition ─────────────────────────────────────────────────
        "section_data":         "استحواذ البيانات",
        "quick_locations":      "مواقع سريعة",
        "location_search":      "البحث بالإحداثيات",
        "coord_input":          "الإحداثيات (مثال: 25.65N, 28.95E)",
        "go_to_location":       "انتقل إلى الموقع",
        "invalid_coords":       "صيغة إحداثيات غير صحيحة",
        "date_range":           "النطاق الزمني",
        "date_from":            "من",
        "date_to":              "إلى",
        "filters":              "المرشّحات",
        "max_cloud":            "الحد الأقصى لنسبة الغيوم %",
        # "collection" removed — hardcoded to sentinel-2-l2a
        "max_results":          "الحد الأقصى للنتائج",
        "draw_aoi":             "ارسم منطقة الاهتمام",
        "search_products":      "البحث عن المنتجات",
        "search_stac_btn":      "البحث في كتالوج STAC",
        "searching_stac":       "جارٍ البحث في كتالوج STAC...",
        "no_products":          "لم يُعثر على منتجات. حاول تعديل المرشّحات.",
        "available_products":   "المنتجات المتاحة",
        "cached":               "محفوظ في الذاكرة",
        "load_from_cache":      "تحميل من الذاكرة",
        "download_bands_btn":   "تحميل النطاقات",
        "downloading_bands":    "جارٍ تحميل 8 نطاقات طيفية…",
        "download_complete":    "اكتمل التحميل",
        "download_incomplete":  "التحميل غير مكتمل",
        "downloaded_products":  "المنتجات المحمّلة",
        "date_label":           "التاريخ",
        "cloud_label":          "الغيوم",

        # ── Time Series ──────────────────────────────────────────────────────
        "select_for_analysis":  "اختر للتحليل",
        "ts_add_btn":           "إضافة إلى السلاسل الزمنية",
        "ts_added":             "تمت الإضافة إلى قائمة الانتظار ✓",
        "ts_already_added":     "موجود بالفعل في قائمة الانتظار",
        "ts_queue_title":       "السلاسل الزمنية — قائمة المنتجات",
        "ts_queue_empty_title": "لا توجد منتجات في قائمة الانتظار",
        "ts_queue_empty_body":  ("انتقل إلى استحواذ البيانات، ابحث عن منتجات بتواريخ مختلفة، "
                                 "حمّل كل منتج أو حمّله من الذاكرة، ثم اضغط \"إضافة إلى السلاسل الزمنية\". "
                                 "أضف تاريخَين على الأقل لتفعيل المقارنة."),
        "ts_run_btn":           "تشغيل تحليل السلاسل الزمنية",
        "ts_min_products":      "أضف منتجَين على الأقل (تواريخ مختلفة) لتفعيل المقارنة.",
        "ts_processing":        "جارٍ معالجة المنتج",
        "ts_of":                "من",
        "ts_results_title":     "نتائج السلاسل الزمنية",
        "ts_health_trend":      "درجة الصحة عبر الزمن",
        "ts_veg_distribution":  "توزيع فئات الغطاء النباتي",
        "ts_expansion_title":   "ملخص التوسع",
        "ts_change_title":      "كشف التغيير  —  الأول مقابل الأخير",
        "ts_improved":          "تحسّن",
        "ts_degraded":          "تراجع",
        "ts_stable":            "مستقر",
        "ts_net_change":        "صافي تغير المساحة الصحية",
        "ts_trend_expanding":   "في توسع",
        "ts_trend_stable":      "مستقر",
        "ts_trend_degrading":   "في تراجع",
        "ts_table_title":       "جدول الملخص",
        "ts_date_col":          "التاريخ",
        "ts_score_col":         "درجة الصحة",
        "ts_healthy_col":       "سليم كم²",
        "ts_moderate_col":      "متوسط كم²",
        "ts_severe_col":        "حرج كم²",
        "ts_bare_col":          "جرداء كم²",
        "ts_clear_queue":       "مسح القائمة",
        "ts_clear_results":     "مسح النتائج",
        "ts_remove":            "حذف",
        "ts_no_aoi":            "لم يتم تحديد منطقة. ارسم منطقة على خريطة استحواذ البيانات أولاً.",
        "ts_one_product":       "تمت معالجة منتج واحد فقط — أضف اثنين على الأقل لرؤية مخططات المقارنة.",

        # ── AI Analysis — shared ─────────────────────────────────────────────
        "section_ai":           "تحليل الذكاء الاصطناعي",
        "tab_ndvi":             "صحة النبات — NDVI",
        "tab_detection":        "كشف الأشجار",
        "tab_iot":              "🔒 استهلاك الابار (IoT)",
        "iot_analysis_title":   "التحليل: تستخدم المنصة هذه البيانات من أجل:",
        "iot_bullet1":          "حساب إنتاج المياه: إجمالي حجم المياه المستخرجة على مدار الوقت.",
        "iot_bullet2":          "تحديد فقدان المياه: الكشف عن التسريبات أو التصريف غير المقاس.",
        "iot_bullet3":          "مراقبة معدلات الاستخراج: ضمان عدم تجاوز البئر لحدود التغذية المستدامة للمياه الجوفية.",
        "iot_irr_title":        "ذكاء الري:",
        "iot_irr_body":         (
            "حساب الاحتياجات: من أبرز الميزات المتقدمة التي ذكرتموها القدرة على حساب "
            "\"كمية المياه اللازمة للري الكامل\". يشير هذا إلى أن المنصة قد تدمج بيانات "
            "رطوبة التربة أو نماذج التبخر النتحي (ET) لتحديد الوقت الأمثل لتوقف الضخ للمزارع، "
            "مما يمنع الإفراط في الري واستنزاف المياه الجوفية."
        ),
        "no_downloaded":        ("&#9432; لا توجد منتجات محمّلة. "
                                 "يرجى الانتقال إلى <strong>استحواذ البيانات</strong> أولاً."),

        # ── AI Analysis — NDVI sidebar ───────────────────────────────────────
        "sidebar_satellite":    "🛰 صورة القمر الاصطناعي",
        "select_image":         "اختر صورة",
        "sidebar_farm_area":    "📐 منطقة المزرعة",
        "use_drawn_area":       "استخدام المنطقة المرسومة على الخريطة",
        "paste_geojson":        "الصق مضلع GeoJSON",
        "area_from_map":        "تم تحديد المنطقة من الخريطة ✓",
        "no_area_drawn":        "لم تُرسم منطقة. انتقل إلى استحواذ البيانات أولاً.",
        "advanced_settings":    "⚙️ الإعدادات المتقدمة",
        "sensitivity_thresh":   "حدود الحساسية",
        "no_veg_threshold":     "حد عدم وجود نبات",
        "critical_threshold":   "حد الإجهاد الحرج",
        "moderate_threshold":   "حد الإجهاد المتوسط",
        "indicator_weights":    "أوزان المؤشرات",
        "weight_msavi":         "كثافة النبات",
        "weight_ndre":          "صحة الأوراق",
        "weight_ndwi":          "إجهاد المياه",
        "weight_cire":          "مستوى المغذيات",
        "run_analysis_btn":     "تشغيل تحليل الصحة",
        "computing_analysis":   "جارٍ حساب تحليل الصحة متعدد المؤشرات…",
        "provide_aoi":          "يرجى تحديد منطقة الاهتمام",
        "analysis_complete":    "اكتمل تحليل الصحة",

        # ── AI Analysis — NDVI results ───────────────────────────────────────
        "overall_veg_health":   "الصحة الإجمالية للغطاء النباتي",
        "based_on_4":           "استناداً إلى 4 مؤشرات صحية علمية على المنطقة المحددة",
        "status_good":          "جيد",
        "status_fair":          "مقبول",
        "status_poor":          "ضعيف",
        "veg_cover_lbl":        "الغطاء النباتي",
        "veg_cover_desc":       "من إجمالي المنطقة المحددة يحمل غطاءً نباتياً",
        "healthy_area_lbl":     "المساحة الصحية",
        "stressed_area_lbl":    "المساحة المجهدة",
        "stressed_area_desc":   "تحتاج إلى اهتمام",
        "no_veg_lbl":           "لا يوجد نبات",
        "no_veg_desc":          "أرض جرداء أو غير نشطة",
        "health_map_title":     "خريطة الصحة",
        "what_measured":        "ما الذي قسناه",
        "index_msavi_name":     "كثافة النبات",
        "index_msavi_desc":     "مدى خضرة وكثافة الغطاء النباتي مع تعديل لأثر التربة الصحراوية",
        "index_ndre_name":      "صحة الأوراق",
        "index_ndre_desc":      "مستوى الكلوروفيل — يكتشف الإجهاد قبل 2-4 أسابيع من ظهوره",
        "index_ndwi_name":      "إجهاد المياه",
        "index_ndwi_desc":      "كمية المياه في النباتات — يكتشف الجفاف مبكراً",
        "index_cire_name":      "مستوى المغذيات",
        "index_cire_desc":      "الحالة الغذائية للنبات — يرصد نقص النيتروجين والمغنيسيوم",

        # ── AI Analysis — Recommendations ────────────────────────────────────
        "section_recs":         "التوصيات",
        "rec_bare_title":       "رصد مساحة عارية أو ميتة كبيرة.",
        "rec_severe_title":     "مناطق إجهاد حاد تحتاج إلى تدخل عاجل.",
        "rec_moderate_title":   "إجهاد متوسط — تصرّف قبل تفاقم الوضع.",
        "rec_healthy_title":    "الغطاء النباتي في حالة صحية جيدة في معظمه.",
        "rec_declining_title":  "الصحة مقبولة لكن المناطق المتراجعة تحتاج متابعة.",
        "rec_declining_body":   "شغّل كشف الأشجار لربط إجهاد النبات بصحة النخيل الفردية.",
        "rec_poor_title":       "الصحة الإجمالية للغطاء النباتي ضعيفة.",
        "rec_poor_body":        "يُنصح بشدة بإجراء مسح ميداني فوري.",
        "rec_detect_title":     "شغّل كشف الأشجار للتحليل المتقاطع الكامل.",
        "rec_detect_body":      "ادمج نتائج النبات مع إحصاء النخيل للحصول على التوقعات الاقتصادية.",

        # ── AI Analysis — Tree Detection ─────────────────────────────────────
        "detection_settings":   "🌴 إعدادات الكشف",
        "model_ready":          "نموذج الذكاء الاصطناعي جاهز ✓",
        "no_model":             "لم يُعثر على نموذج ذكاء اصطناعي في مجلد models/",
        "conf_thresh_lbl":      "حد ثقة الكشف",
        "conf_thresh_help":     ("الحد الأدنى لدرجة الثقة لاحتساب الكشف. "
                                 "القيم المنخفضة تكشف أشجاراً أكثر لكنها قد تتضمن نتائج خاطئة."),
        "section_palm_census":  "إحصاء النخيل وتصنيف الصحة",
        "highres_title":        "وضع التصوير عالي الدقة",
        "highres_body":         ("يحصل على صور Sentinel-2 الاصطناعية بدقة ~0.3 م/بكسل "
                                 "لكشف دقيق للنخيل الفردي — أكثر حدةً بكثير من "
                                 "منتج Sentinel-2 بدقة 10 م/بكسل. لا حاجة لتحميلات إضافية؛ "
                                 "يتم التقاط الصورة تلقائياً من منطقة الاهتمام المرسومة."),
        "no_area_selected":     ("&#9432; لم يتم تحديد منطقة. انتقل إلى "
                                 "<strong>استحواذ البيانات</strong> وارسم حدود مزرعتك أولاً."),
        "no_model_error":       "لم يُعثر على النموذج. ضع ملف .pt داخل مجلد models/.",
        "acquire_btn":          "🛰️  التقاط صورة عالية الدقة وتشغيل الكشف",
        "capturing_spinner":    "جارٍ التقاط صورة الأقمار الاصطناعية عالية الدقة…",
        "running_detection":    "جارٍ تشغيل كشف الذكاء الاصطناعي على الصورة عالية الدقة…",
        "caption_aoi":          "📍 منطقة الاهتمام — صور Google Maps الاصطناعية",
        "caption_detections":   "🌴 نتائج كشف النخيل",
        "section_census":       "نتائج الإحصاء",
        "total_palms_lbl":      "إجمالي النخيل المكتشف",
        "total_palms_desc":     "داخل منطقة الاهتمام",
        "healthy_lbl":          "سليم",
        "early_stress_lbl":     "إجهاد مبكر",
        "early_stress_desc":    "يحتاج متابعة",
        "critical_lbl":         "حالة حرجة",
        "critical_desc":        "تدخل عاجل",

        # ── Dashboard ────────────────────────────────────────────────────────
        "overall_health_lbl":   "الصحة الإجمالية لمزرعتك",
        "palms_counted_lbl":    "النخيل المحصى",
        "palms_counted_desc":   "شجرة رصدها الذكاء الاصطناعي في منطقتك",
        "healthy_area_desc_d":  "في حالة جيدة",
        "economic_outlook_lbl": "التوقعات الاقتصادية",
        "economic_outlook_desc":"استناداً إلى صحة الأشجار والنبات",
        "status_no_data":       "لا توجد بيانات",
        "no_analysis_title":    "لم يُجرَ أي تحليل بعد",
        "no_analysis_body":     ("انتقل إلى <strong>تحليل الذكاء الاصطناعي</strong> لتشغيل تحليل "
                                 "صحة النبات وكشف الأشجار، ثم ارجع هنا لعرض لوحة التحكم الكاملة."),
        "maps_title":           "الخرائط والنتائج المرئية",
        "veg_map_caption":      "خريطة صحة الغطاء النباتي",
        "run_veg_health":       "شغّل <strong>تحليل صحة النبات</strong> في تحليل الذكاء الاصطناعي",
        "run_tree_detect":      "شغّل <strong>كشف الأشجار</strong> في تحليل الذكاء الاصطناعي",
        "veg_breakdown_title":  "تفصيل صحة الغطاء النباتي",
        "bar_healthy":          "سليم",
        "bar_moderate":         "إجهاد متوسط",
        "bar_critical":         "إجهاد حرج",
        "bar_no_veg":           "لا يوجد نبات",
        "tree_health_title":    "ملخص صحة الأشجار",
        "healthy_trees_lbl":    "أشجار سليمة 🟢",
        "early_stress_lbl_d":   "إجهاد مبكر 🟡",
        "critical_lbl_d":       "حالة حرجة 🔴",
        "of_detected_palms":    "% من النخيل المكتشف",
        "monitor_closely":      "% — يحتاج متابعة",
        "urgent_intervention":  "% — تدخل عاجل",
        "econ_positive":        "التوقعات الاقتصادية: إيجابية",
        "econ_positive_body":   ("أكثر من 70% من النخيل في حالة صحية. "
                                 "المزرعة في حالة إنتاجية جيدة."),
        "econ_moderate":        "التوقعات الاقتصادية: متوسطة",
        "econ_moderate_body":   ("نحو نصف النخيل في حالة صحية. "
                                 "راقب الأشجار المجهدة عن كثب لمنع المزيد من التراجع."),
        "econ_at_risk":         "التوقعات الاقتصادية: في خطر",
        "econ_at_risk_body":    ("أقل من نصف النخيل في حالة صحية. "
                                 "التدخل الزراعي الفوري ضروري."),
        "section_recs_d":       "التوصيات",
        "rec_d2":               "طبّق ريّاً موجّهاً في المناطق المجهدة — إجهاد المياه هو السبب الأكثر شيوعاً في هذه المنطقة.",
        "rec_d4":               "جدوِل مسحاً لاحقاً بالقمر الاصطناعي بعد 30 يوماً لتتبع تطور الأوضاع.",
        "rec_d5":               "حمّل تقرير PDF أدناه لمشاركة هذه النتائج مع المهندس الزراعي أو المستثمر.",
        "hint_tree_detect":     "💡 شغّل **كشف الأشجار** في تحليل الذكاء الاصطناعي لفتح التحليل المتقاطع الكامل والتوقعات الاقتصادية.",
        "hint_veg_health":      "💡 شغّل **تحليل صحة النبات** في تحليل الذكاء الاصطناعي لفتح التحليل المتقاطع الكامل.",
        "section_export":       "تصدير تقريرك",
        "pdf_lbl":              "تقرير PDF",
        "pdf_desc":             ("تقرير احترافي يتضمن خرائط الصحة والإحصاءات والتوقعات الاقتصادية "
                                 "— جاهز للمشاركة مع فريقك أو مستثمريك."),
        "generate_pdf_btn":     "إنشاء تقرير PDF",
        "building_report":      "جارٍ إنشاء تقريرك…",
        "run_analysis_first":   "شغّل تحليلاً واحداً على الأقل قبل إنشاء التقرير.",
        "report_ready":         "التقرير جاهز!",
        "download_pdf_btn":     "⬇️ تحميل تقرير PDF",
        "zip_lbl":              "تصدير البيانات الكاملة",
        "zip_desc":             ("أرشيف ZIP يحتوي على جميع البيانات الخام: إحصاءات الصحة كـ CSV، "
                                 "ملف خريطة GeoTIFF، وملخص البيانات الوصفية."),
        "export_all_btn":       "تصدير كل البيانات",
        "packaging_data":       "جارٍ تجهيز بياناتك…",
        "no_data_export":       "لا توجد بيانات للتصدير بعد.",
        "export_ready":         "التصدير جاهز!",
        "download_zip_btn":     "⬇️ تحميل ZIP",
        # ── PDF Report strings ────────────────────────────────────────────────
        "rpt_title":            "تقرير الرصد البيئي",
        "rpt_date_label":       "تاريخ التقرير",
        "rpt_product":          "المنتج الفضائي",
        "rpt_aoi":              "منطقة الاهتمام",
        "rpt_source":           "مصدر البيانات",
        "rpt_model":            "نموذج الكشف",
        "rpt_platform":         "المنصة",
        "rpt_not_specified":    "غير محدد",
        "rpt_source_val":       "Sentinel-2 L2A (برنامج ESA كوبرنيكوس)",
        "rpt_model_val":        "YOLOv8 — مدرَّب على صور النخيل الجوية",
        "rpt_platform_val":     "منصة الحارس للرصد · فريق إيكو",
        "rpt_disclaimer":       (
            "تم إنشاء هذا التقرير تلقائيًا بواسطة منصة الحارس باستخدام صور الأقمار الصناعية "
            "من مهمة ESA Copernicus Sentinel-2 ونموذج الذكاء الاصطناعي للكشف عن أشجار النخيل. "
            "تُقدَّم النتائج لأغراض البحث والاستشارة والاستثمار. "
            "يُوصى بالتحقق الميداني قبل اتخاذ أي قرار تشغيلي."
        ),
        "rpt_s1_title":         "١.  تحليل صحة الغطاء النباتي — تقييم متعدد المؤشرات",
        "rpt_overview":         "نظرة عامة",
        "rpt_s1_overview":      (
            "تم إجراء تقييم صحة الغطاء النباتي متعدد المؤشرات على مساحة إجمالية صالحة "
            "تبلغ {area:.2f} كم²، باستخدام أربعة مؤشرات طيفية تكميلية مشتقة "
            "من صور Sentinel-2: كثافة النبات (MSAVI)، وصحة الأوراق (NDRE)، "
            "وإجهاد المياه (NDWI)، والحالة الغذائية (CIre). "
            "تم تصنيف كل بكسل في إحدى فئات الصحة الأربع بناءً على درجة مركبة موزونة."
        ),
        "rpt_health_stats":     "إحصاءات تصنيف الصحة",
        "rpt_col_class":        "الفئة الصحية",
        "rpt_col_area":         "المساحة (كم²)",
        "rpt_col_coverage":     "التغطية (%)",
        "rpt_col_pixels":       "عدد البكسل",
        "rpt_viz":              "مرئيات التحليل",
        "rpt_s2_title":         "٢.  إحصاء أشجار النخيل — نتائج الكشف بالذكاء الاصطناعي",
        "rpt_s2_overview":      (
            "تم تحديد {total:,} شجرة نخيل داخل منطقة الاهتمام "
            "باستخدام نموذج التعلم العميق YOLOv8 المدرَّب. تم استخدام صور الأقمار الصناعية "
            "عالية الدقة (~0.3 متر/بكسل) لضمان دقة الكشف على مستوى التاج الفردي. "
            "تم تصنيف كل شجرة مكتشفة في إحدى فئات الحالة الثلاث."
        ),
        "rpt_detect_summary":   "ملخص الكشف حسب الحالة",
        "rpt_crit_condition":   "حالة حرجة",
        "rpt_healthy":          "سليم",
        "rpt_early_stress":     "إجهاد مبكر",
        "rpt_col_condition":    "الحالة",
        "rpt_col_count":        "العدد",
        "rpt_col_proportion":   "النسبة (%)",
        "rpt_total":            "الإجمالي",
        "rpt_annot_map":        "خريطة الكشف المشروحة",
        "rpt_legend":           "(أخضر = سليم · برتقالي = إجهاد مبكر · أحمر = حرج)",
        "rpt_s3_title":         "٣.  تحليل التقاطع والتوقعات الاقتصادية",
        "rpt_key_findings":     "النتائج الرئيسية",
        "rpt_finding1":         "يشير تحليل النبات إلى أن {pct:.1f}% من المنطقة المراقبة تدعم غطاءً نباتيًا صحيًا.",
        "rpt_finding2":         "{count:,} نخلة مصنفة على أنها سليمة، مرتبطة مكانيًا بمناطق الغطاء النباتي عالي NDVI.",
        "rpt_finding3":         "{count:,} شجرة في حالة حرجة تتوافق مع {pct:.1f}% من مناطق الإجهاد الشديد.",
        "rpt_finding4":         "{count:,} شجرة ذات إجهاد مبكر رُصدت ضمن {pct:.1f}% من مناطق الإجهاد المتوسط — يُنصح بالتدخل.",
        "rpt_econ_outlook":     "التوقعات الاقتصادية",
        "rpt_positive":         "إيجابي",
        "rpt_moderate":         "متوسط",
        "rpt_at_risk":          "في خطر",
        "rpt_positive_body":    (
            "مع وجود {pct:.1f}% من النخيل في حالة سليمة، تُظهر المزرعة طاقة إنتاجية قوية. "
            "من المتوقع أن تكون مستويات الإنتاج عند المتوسطات الموسمية أو تتجاوزها. "
            "يُقدَّر خطر الاستثمار بأنه منخفض."
        ),
        "rpt_moderate_body":    (
            "مع وجود {pct:.1f}% من النخيل السليم، تكون الإنتاجية الإجمالية مقبولة. "
            "ومع ذلك، يُوصى بالتدخل في مناطق الإجهاد والحالات الحرجة لمنع المزيد من التدهور. "
            "يُقدَّر خطر الاستثمار بأنه متوسط."
        ),
        "rpt_at_risk_body":     (
            "{pct:.1f}% فقط من النخيل المكتشف سليم. يستلزم الأمر تدخلًا زراعيًا كبيرًا. "
            "يُتوقع انخفاض ملحوظ في الإنتاج الموسمي إذا استمرت الأوضاع. "
            "يُقدَّر خطر الاستثمار بأنه مرتفع."
        ),
        "rpt_econ_label":       "التوقعات الاقتصادية:",
        "rpt_recommendations":  "توصيات قابلة للتنفيذ",
        "rpt_rec1":             "إجراء مسح ميداني للتحقق في جميع المناطق المصنفة على أنها إجهاد شديد أو حالة حرجة.",
        "rpt_rec2":             "تطبيق الري المستهدف في المناطق التي تنخفض فيها قيم NDWI عن الحد الأدنى — إجهاد المياه هو المحرك الرئيسي في هذه المنطقة.",
        "rpt_rec3":             "فحص جميع أشجار الإجهاد المبكر بحثًا عن الآفات أو الأمراض في مرحلة مبكرة لتمكين التدخل الفعّال من حيث التكلفة.",
        "rpt_rec4":             "تطبيق التغذية الورقية بالمغذيات في المناطق التي يشير فيها مؤشر CIre إلى نقص النيتروجين أو المغنيسيوم.",
        "rpt_rec5":             "جدولة التقاط صور أقمار صناعية متكررة خلال 30 يومًا لتتبع التغيرات الزمنية وقياس فعالية التدخل.",
        "rpt_footer":           "الحارس · مراقب نخيل وادي الجديد والغطاء النباتي · فريق إيكو · سري",
        "rpt_page":             "صفحة",
        "rpt_class0":           "لا نبات",
        "rpt_class1":           "إجهاد حرج",
        "rpt_class2":           "إجهاد متوسط",
        "rpt_class3":           "نبات سليم",
    },
}


def t(key: str, lang: str = "en") -> str:
    """Return translated string; falls back to English if key missing in Arabic."""
    return _T.get(lang, _T["en"]).get(key, _T["en"].get(key, key))


RTL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&display=swap');

html, body, [class*="css"], .stApp {
    direction: rtl !important;
    font-family: 'Cairo', 'Inter', sans-serif !important;
}
.guardian-header, .guardian-header-text,
.g-step, .g-card, .g-rec, .g-info-banner,
.g-section-title, .g-index-row, .g-bar-wrap,
.g-footer { direction: rtl; text-align: right; }
.g-info-banner { flex-direction: row-reverse; }
.g-step-num, .g-step-title, .g-step-body { text-align: right; }
/* ── Reversed header colors in Arabic mode ── */
.guardian-header {
    background: linear-gradient(135deg, #219EBC 0%, #2E6B7A 60%, #4A5759 100%) !important;
}
.g-section-title {
    color: #219EBC !important;
    border-bottom-color: rgba(74,87,89,0.3) !important;
}
.g-section-title i { color: #4A5759 !important; }
div[data-testid="column"] { direction: rtl; }
div[data-testid="stSidebar"] { direction: rtl; text-align: right; }
.stButton > button, .stDownloadButton > button {
    font-family: 'Cairo', sans-serif !important;
    direction: rtl;
}
label, .stSelectbox label, .stSlider label,
.stTextInput label, .stNumberInput label,
.stDateInput label, .stCheckbox label {
    direction: rtl !important;
    text-align: right !important;
    font-family: 'Cairo', sans-serif !important;
}
.stTabs [data-baseweb="tab"] { font-family: 'Cairo', sans-serif !important; }
p, div, span, h1, h2, h3, h4, li {
    font-family: 'Cairo', 'Inter', sans-serif !important;
}

/* ── Note/info panel text centering in Arabic ── */
div[style*="background:#EAF4F7"] {
    text-align: center !important;
}
div[style*="background:#EAF4F7"] span {
    direction: rtl !important;
}
/* Alert / success / warning / info / error box — full RTL */
div[data-testid="stAlert"],
div[data-testid="stAlert"] *,
.stAlert, .stAlert * {
    text-align: right !important;
    direction: rtl !important;
}
/* g-info-banner text alignment */
.g-info-banner-title, .g-info-banner-sub {
    text-align: right !important;
    direction: rtl !important;
}
/* Subheader and general markdown paragraphs in data page */
.stSubheader p, h3 {
    text-align: right !important;
}

/* ── Sidebar collapse button — LTR + custom glyph, RTL-safe ── */
[data-testid="stSidebarCollapseButton"],
[data-testid="stSidebarCollapseButton"] button {
    direction: ltr !important;
    position: relative !important;
}
/* Hide ALL nested content (SVG, spans, text) regardless of DOM depth */
[data-testid="stSidebarCollapseButton"] button * {
    visibility: hidden !important;
}
/* Inject a properly rendered arrow glyph */
[data-testid="stSidebarCollapseButton"] button::after {
    visibility: visible !important;
    content: "◀" !important;
    font-size: 16px !important;
    color: #C8DDD9 !important;
    position: absolute !important;
    top: 50% !important;
    left: 50% !important;
    transform: translate(-50%, -50%) !important;
    font-family: sans-serif !important;
}
</style>
"""


def inject_rtl(lang: str) -> None:
    """Call inside each page after _load_styles() when Arabic is active."""
    import streamlit as st
    if lang == "ar":
        st.markdown(RTL_CSS, unsafe_allow_html=True)


def lang_toggle(page_key: str) -> str:
    """
    Render a single toggle button in the sidebar.
    Shows 'AR' when currently in English (click → switch to Arabic).
    Shows 'EN' when currently in Arabic (click → switch to English).
    Returns the current language string ('en' or 'ar').
    """
    import streamlit as st
    lang  = st.session_state.get("lang", "en")
    label = "AR" if lang == "en" else "EN"
    if st.sidebar.button(label, key=f"lang_toggle_{page_key}", use_container_width=True):
        st.session_state["lang"] = "ar" if lang == "en" else "en"
        st.rerun()
    return lang


def render_nav(lang: str) -> None:
    """
    Render translated sidebar navigation links.
    Call after lang_toggle() on every page.
    The auto-generated Streamlit nav is hidden via style.css.
    """
    import streamlit as st
    with st.sidebar:
        st.page_link(
            "app.py",
            label="Home" if lang == "en" else "الرئيسية",
        )
        st.page_link(
            "pages/1_Data_Acquisition.py",
            label="Data Acquisition" if lang == "en" else "استحواذ البيانات",
        )
        st.page_link(
            "pages/2_AI_Analysis.py",
            label="AI Analysis" if lang == "en" else "تحليل الذكاء الاصطناعي",
        )
        st.page_link(
            "pages/3_Dashboard_Insights.py",
            label="Dashboard & Insights" if lang == "en" else "لوحة التحكم والرؤى",
        )
