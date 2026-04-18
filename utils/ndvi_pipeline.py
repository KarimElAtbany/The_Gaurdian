import numpy as np
import rasterio
import rasterio.mask
from shapely.geometry import shape, mapping, Polygon
from pyproj import Transformer
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.gridspec import GridSpec


class NDVIPipeline:
    """
    Multi-index vegetation health pipeline.
    Indices:
      MSAVI  — soil-corrected greenness (arid region safe, replaces raw NDVI)
      NDRE   — red-edge chlorophyll / early stress  (B05, B08)
      NDWI   — canopy water / drought stress        (B8A, B11)
      CIre   — red-edge chlorophyll index           (B07, B05)
    A weighted composite score drives the 4-class health map.
    """

    CLASS_LABELS = ["Dead / Bare", "Severe Stress", "Moderate Stress", "Healthy"]
    # Colors aligned with Sentinel Hub NDVI standard palette
    # Dead/Bare: neutral gray | Severe: orange | Moderate: soft green | Healthy: dark green
    CLASS_COLORS = ["#6B6B6B", "#fdae61", "#a8d576", "#1a9850"]

    INDEX_WEIGHTS = {
        "MSAVI": 0.20,
        "NDRE":  0.35,
        "NDWI":  0.30,
        "CIre":  0.15,
    }

    def __init__(self, thresholds=(0.15, 0.30, 0.55)):
        self.thresholds = thresholds
        self.class_labels = self.CLASS_LABELS
        self.class_colors = self.CLASS_COLORS

    def _reproject_polygon(self, geojson_polygon, target_crs):
        polygon_shape = shape(geojson_polygon)
        transformer = Transformer.from_crs("EPSG:4326", target_crs, always_xy=True)
        coords = list(polygon_shape.exterior.coords)
        reprojected = [transformer.transform(x, y) for x, y in coords]
        return [mapping(Polygon(reprojected))]

    def _read_band(self, path, geojson_masks, target_shape=None):
        with rasterio.open(path) as src:
            data, transform = rasterio.mask.mask(src, geojson_masks, crop=True, nodata=0)
            pixel_size_m = abs(src.transform.a)
            profile = src.profile
        arr = data[0].astype("float32")
        if target_shape is not None and arr.shape != target_shape:
            import cv2
            arr = cv2.resize(arr, (target_shape[1], target_shape[0]), interpolation=cv2.INTER_LINEAR)
        return arr, transform, profile, pixel_size_m

    def _normalise(self, arr):
        if arr.max() > 1.0:
            arr = arr / 10000.0
        return arr

    def crop_to_aoi(self, band4_path, band8_path, geojson_polygon):
        """Legacy entry-point kept for compatibility."""
        with rasterio.open(band8_path) as src:
            geojson_reprojected = self._reproject_polygon(geojson_polygon, src.crs)
            nir_crop, transform = rasterio.mask.mask(src, geojson_reprojected, crop=True, nodata=0)
            profile = src.profile
            nir = nir_crop[0].astype("float32")
            pixel_size_m = abs(src.transform.a)

        with rasterio.open(band4_path) as src:
            red_crop, _ = rasterio.mask.mask(src, geojson_reprojected, crop=True, nodata=0)
            red = red_crop[0].astype("float32")

        return nir, red, transform, profile, pixel_size_m

    def crop_and_load_bands(self, bands_paths, geojson_polygon):
        """
        Load and crop all available bands to the AOI.
        bands_paths: dict with keys like B04, B05, B07, B08, B8A, B11
        """
        ref_path = bands_paths.get('B08') or bands_paths.get('B04')
        with rasterio.open(ref_path) as src:
            raster_crs = src.crs

        geojson_masks = self._reproject_polygon(geojson_polygon, raster_crs)

        loaded = {}
        transform = profile = pixel_size_m = None
        target_shape = None

        ref_key = next((k for k in ['B08', 'B04'] if k in bands_paths), next(iter(bands_paths)))
        ref_arr, transform, profile, pixel_size_m = self._read_band(bands_paths[ref_key], geojson_masks)
        target_shape = ref_arr.shape
        loaded[ref_key] = self._normalise(ref_arr)

        for key, path in bands_paths.items():
            if path is None or key == ref_key:
                continue
            arr, _, _, _ = self._read_band(path, geojson_masks, target_shape=target_shape)
            loaded[key] = self._normalise(arr)

        return loaded, transform, profile, pixel_size_m

    def crop_rgb_to_aoi(self, band2_path, band3_path, band4_path, geojson_polygon):
        """Generate a true-color RGB preview cropped to the AOI."""
        with rasterio.open(band4_path) as src:
            geojson_reprojected = self._reproject_polygon(geojson_polygon, src.crs)
            r_crop, _ = rasterio.mask.mask(src, geojson_reprojected, crop=True, nodata=0)
            red = r_crop[0].astype("float32")

        with rasterio.open(band3_path) as src:
            g_crop, _ = rasterio.mask.mask(src, geojson_reprojected, crop=True, nodata=0)
            green = g_crop[0].astype("float32")

        with rasterio.open(band2_path) as src:
            b_crop, _ = rasterio.mask.mask(src, geojson_reprojected, crop=True, nodata=0)
            blue = b_crop[0].astype("float32")

        def normalize(band):
            valid = band[band > 0]
            if len(valid) == 0:
                return np.zeros_like(band)
            p2, p98 = np.percentile(valid, (2, 98))
            return np.clip((band - p2) / (p98 - p2 + 1e-10), 0, 1)

        rgb = np.dstack([normalize(red), normalize(green), normalize(blue)])
        return (rgb * 255).astype(np.uint8)

    def compute_indices(self, bands):
        """
        Compute MSAVI, NDRE, NDWI, CIre from band arrays.
        bands: dict with keys B04, B05, B07, B08, B8A, B11
        """
        red  = bands.get('B04')
        re1  = bands.get('B05')
        re3  = bands.get('B07')
        nir  = bands.get('B08')
        nir8 = bands.get('B8A')
        swir = bands.get('B11')

        invalid = (nir == 0) & (red == 0) if (nir is not None and red is not None) else None

        msavi = ndre = ndwi = cire = None

        if red is not None and nir is not None:
            val = (2 * nir + 1 - np.sqrt(np.clip((2 * nir + 1) ** 2 - 8 * (nir - red), 0, None))) / 2
            msavi = np.clip(val, -1.0, 1.0)
            if invalid is not None:
                msavi[invalid] = np.nan

        if re1 is not None and nir is not None:
            ndre = np.clip((nir - re1) / (nir + re1 + 1e-10), -1.0, 1.0)
            if invalid is not None:
                ndre[invalid] = np.nan

        nir_ref = nir8 if nir8 is not None else nir
        if nir_ref is not None and swir is not None:
            ndwi = np.clip((nir_ref - swir) / (nir_ref + swir + 1e-10), -1.0, 1.0)
            if invalid is not None:
                ndwi[invalid] = np.nan

        if re1 is not None and re3 is not None:
            cire = np.clip(re3 / (re1 + 1e-10) - 1, 0, 10) / 10.0
            if invalid is not None:
                cire[invalid] = np.nan

        return {"MSAVI": msavi, "NDRE": ndre, "NDWI": ndwi, "CIre": cire}

    def _scale_to_01(self, arr, vmin, vmax):
        return np.clip((arr - vmin) / (vmax - vmin + 1e-10), 0.0, 1.0)

    def compute_composite(self, indices):
        """Weighted composite health score in [0, 1]."""
        scale_ranges = {
            "MSAVI": (-0.1, 0.6),
            "NDRE":  (-0.1, 0.5),
            "NDWI":  (-0.3, 0.5),
            "CIre":  (0.0,  1.0),
        }

        ref = next((v for v in indices.values() if v is not None), None)
        if ref is None:
            return None

        composite  = np.zeros_like(ref)
        weight_sum = 0.0

        for name, weight in self.INDEX_WEIGHTS.items():
            arr = indices.get(name)
            if arr is None:
                continue
            vmin, vmax = scale_ranges[name]
            scaled = self._scale_to_01(arr, vmin, vmax)
            composite = np.where(np.isnan(arr), composite, composite + weight * scaled)
            weight_sum += weight

        if weight_sum > 0:
            composite /= weight_sum

        nan_mask = np.all([np.isnan(v) for v in indices.values() if v is not None], axis=0)
        composite[nan_mask] = np.nan

        return composite

    def classify_health(self, composite, invalid_mask=None):
        t1, t2, t3 = self.thresholds
        health_map = np.full(composite.shape, 255, dtype=np.uint8)
        health_map[~np.isnan(composite) & (composite <= t1)] = 0
        health_map[~np.isnan(composite) & (composite > t1) & (composite <= t2)] = 1
        health_map[~np.isnan(composite) & (composite > t2) & (composite <= t3)] = 2
        health_map[~np.isnan(composite) & (composite > t3)] = 3
        return health_map

    def compute_statistics(self, health_map, invalid_mask_or_composite, pixel_area_km2):
        """
        Accepts either the old (health_map, invalid_mask, pixel_area)
        or new (health_map, composite_array, pixel_area) signature.
        Always returns (stats, total_area_km2, composite_mean).
        """
        if isinstance(invalid_mask_or_composite, np.ndarray) and invalid_mask_or_composite.dtype == bool:
            invalid_mask = invalid_mask_or_composite
            composite_mean = 0.0
            total_valid_px = (~invalid_mask).sum()
        else:
            composite = invalid_mask_or_composite
            valid_composite = composite[~np.isnan(composite)] if composite is not None else np.array([])
            composite_mean = float(np.nanmean(valid_composite)) if valid_composite.size > 0 else 0.0
            total_valid_px = (health_map != 255).sum()

        total_area_km2 = total_valid_px * pixel_area_km2
        stats = {}
        for cid, label in enumerate(self.CLASS_LABELS):
            px = int((health_map == cid).sum())
            area = px * pixel_area_km2
            pct = (px / total_valid_px * 100) if total_valid_px > 0 else 0
            stats[cid] = {"label": label, "pixels": px, "area_km2": area, "pct": pct}

        return stats, total_area_km2, composite_mean

    def save_geotiff(self, health_map, profile, transform, output_path):
        profile.update(
            dtype=rasterio.uint8,
            count=1,
            nodata=255,
            width=health_map.shape[1],
            height=health_map.shape[0],
            transform=transform
        )
        with rasterio.open(output_path, "w", **profile) as dst:
            dst.write(health_map, 1)

    def create_visualization(self, health_map, ndvi_or_indices, stats, total_area_km2,
                              true_color_rgb=None, composite=None):
        PALETTE = {
            "bg":      "#F7F7F7",
            "card":    "#FFFFFF",
            "text":    "#4A5759",
            "sub":     "#84A59D",
            "accent":  "#219EBC",
            "grid":    "#DDE8E5",
            "border":  "#C8D8D5",
        }

        cmap        = ListedColormap(self.CLASS_COLORS)
        norm        = BoundaryNorm([-0.5, 0.5, 1.5, 2.5, 3.5], cmap.N)
        display_map = np.ma.masked_where(health_map == 255, health_map)

        is_multi = isinstance(ndvi_or_indices, dict)
        indices  = ndvi_or_indices if is_multi else {}
        ndvi     = None if is_multi else ndvi_or_indices
        n_idx    = sum(1 for v in indices.values() if v is not None) if is_multi else 1
        n_cols   = max(4, n_idx)

        plt.rcParams.update({
            "figure.facecolor":  PALETTE["bg"],
            "axes.facecolor":    PALETTE["card"],
            "axes.edgecolor":    PALETTE["border"],
            "axes.labelcolor":   PALETTE["text"],
            "xtick.color":       PALETTE["text"],
            "ytick.color":       PALETTE["text"],
            "text.color":        PALETTE["text"],
            "grid.color":        PALETTE["grid"],
            "font.family":       "DejaVu Sans",
            "axes.spines.top":   False,
            "axes.spines.right": False,
        })

        fig = plt.figure(figsize=(24, 22), facecolor=PALETTE["bg"])
        gs  = GridSpec(3, n_cols, figure=fig,
                       height_ratios=[2.2, 1.6, 2.2],
                       hspace=0.48, wspace=0.30)
        fig.patch.set_facecolor(PALETTE["bg"])

        span = n_cols // 2

        # ── Row 0: True Colour | Health Map ─────────────────────────────
        ax_tc = fig.add_subplot(gs[0, :span])
        if true_color_rgb is not None:
            ax_tc.imshow(true_color_rgb, interpolation="bilinear")
            ax_tc.set_title("True Color  ·  Sentinel-2 RGB", fontweight="bold",
                             fontsize=13, color=PALETTE["text"], pad=12)
        else:
            ax_tc.set_facecolor("#EAF3F6")
            ax_tc.text(0.5, 0.5, "True Color\nNot Available",
                       ha="center", va="center", transform=ax_tc.transAxes,
                       fontsize=13, color=PALETTE["sub"])
            ax_tc.set_title("True Color  ·  Sentinel-2 RGB", fontweight="bold",
                             fontsize=13, color=PALETTE["text"], pad=12)
        ax_tc.axis("off")

        ax_hm = fig.add_subplot(gs[0, span:])
        im1 = ax_hm.imshow(display_map, cmap=cmap, norm=norm, interpolation="nearest")
        cb  = plt.colorbar(im1, ax=ax_hm, ticks=[0, 1, 2, 3],
                           shrink=0.72, pad=0.025, fraction=0.032)
        cb.ax.set_yticklabels(self.CLASS_LABELS, fontsize=9, color=PALETTE["text"])
        cb.outline.set_edgecolor(PALETTE["border"])
        cb.ax.tick_params(size=0)
        ax_hm.set_title("Composite Health Map", fontweight="bold",
                          fontsize=13, color=PALETTE["text"], pad=12)
        ax_hm.axis("off")

        # thin border around maps
        for ax in (ax_tc, ax_hm):
            for spine in ax.spines.values():
                spine.set_visible(True)
                spine.set_edgecolor(PALETTE["border"])
                spine.set_linewidth(0.8)

        # ── Row 1: Index maps ────────────────────────────────────────────
        index_cmaps  = {"MSAVI": "RdYlGn", "NDRE": "PiYG",
                        "NDWI":  "Blues",  "CIre": "YlOrRd"}
        index_ranges = {"MSAVI": (-0.1, 0.6), "NDRE": (-0.1, 0.5),
                        "NDWI":  (-0.3, 0.5), "CIre": (0, 1)}
        index_titles = {
            "MSAVI": "MSAVI  ·  Vegetation Density",
            "NDRE":  "NDRE  ·  Leaf Health",
            "NDWI":  "NDWI  ·  Water Stress",
            "CIre":  "CIre  ·  Nutrient Level",
        }

        if is_multi:
            col = 0
            for name, arr in indices.items():
                if arr is None:
                    continue
                ax = fig.add_subplot(gs[1, col])
                vmin, vmax = index_ranges.get(name, (-1, 1))
                disp = np.ma.masked_where(np.isnan(arr), arr)
                im_i = ax.imshow(disp, cmap=index_cmaps.get(name, "RdYlGn"),
                                  vmin=vmin, vmax=vmax, interpolation="nearest")
                cb2 = plt.colorbar(im_i, ax=ax, shrink=0.72, pad=0.02, fraction=0.045)
                cb2.ax.tick_params(labelsize=7, colors=PALETTE["text"], size=0)
                cb2.outline.set_edgecolor(PALETTE["border"])
                ax.set_title(index_titles.get(name, name), fontweight="bold",
                              fontsize=9, color=PALETTE["text"], pad=8)
                ax.axis("off")
                col += 1
        else:
            ax_nd = fig.add_subplot(gs[1, :2])
            nd_disp = np.ma.masked_where(np.isnan(ndvi), ndvi)
            im2 = ax_nd.imshow(nd_disp, cmap="RdYlGn", vmin=-0.2, vmax=0.8,
                                interpolation="nearest")
            cb3 = plt.colorbar(im2, ax=ax_nd, shrink=0.72, pad=0.02,
                                fraction=0.032, label="NDVI")
            cb3.ax.tick_params(colors=PALETTE["text"])
            ax_nd.set_title("NDVI", fontweight="bold", fontsize=11,
                             color=PALETTE["text"])
            ax_nd.axis("off")

        # ── Row 2: Area bar | Index summary bar ──────────────────────────
        ax_bar = fig.add_subplot(gs[2, :span])
        bars = ax_bar.bar(
            self.CLASS_LABELS,
            [stats[i]["area_km2"] for i in range(4)],
            color=self.CLASS_COLORS,
            edgecolor=PALETTE["card"],
            linewidth=1.6,
            width=0.60,
            zorder=3,
        )
        max_area = max((stats[i]["area_km2"] for i in range(4)), default=1)
        for bar_obj, cid in zip(bars, range(4)):
            h = bar_obj.get_height()
            if h > 0:
                ax_bar.text(
                    bar_obj.get_x() + bar_obj.get_width() / 2,
                    h + 0.015 * max_area,
                    f"{stats[cid]['pct']:.0f}%\n{stats[cid]['area_km2']:.2f} km²",
                    ha="center", va="bottom", fontsize=11,
                    fontweight="bold", color=PALETTE["text"]
                )
        ax_bar.set_ylabel("Area (km²)", fontsize=12, color=PALETTE["sub"])
        ax_bar.set_title("Area per Health Class", fontweight="bold",
                          fontsize=13, color=PALETTE["text"], pad=12)
        ax_bar.grid(axis="y", alpha=0.35, color=PALETTE["grid"], zorder=0)
        ax_bar.tick_params(axis="x", labelsize=11, rotation=10)
        ax_bar.tick_params(axis="y", labelsize=10)
        ax_bar.set_facecolor(PALETTE["card"])

        ax_idx = fig.add_subplot(gs[2, span:])
        if is_multi:
            mean_vals, radar_names = [], []
            idx_colors = [PALETTE["accent"], PALETTE["sub"], PALETTE["text"], "#F7A072"]
            for name, arr in indices.items():
                if arr is None:
                    continue
                vmin, vmax = index_ranges.get(name, (-1, 1))
                scaled = np.clip((arr - vmin) / (vmax - vmin + 1e-10), 0, 1)
                mean_vals.append(float(np.nanmean(scaled)))
                radar_names.append(name)
            hbars = ax_idx.barh(
                radar_names, mean_vals,
                color=idx_colors[:len(mean_vals)],
                height=0.55, edgecolor=PALETTE["card"], linewidth=1.4, zorder=3
            )
            ax_idx.set_xlim(0, 1.25)
            ax_idx.set_xlabel("Mean Scaled Value  (0 = poor → 1 = excellent)",
                               fontsize=11, color=PALETTE["sub"])
            ax_idx.set_title("Health Index Summary", fontweight="bold",
                              fontsize=13, color=PALETTE["text"], pad=12)
            ax_idx.grid(axis="x", alpha=0.35, color=PALETTE["grid"], zorder=0)
            ax_idx.set_facecolor(PALETTE["card"])
            ax_idx.tick_params(axis="y", labelsize=11)
            ax_idx.tick_params(axis="x", labelsize=10)
            for hb, val in zip(hbars, mean_vals):
                bar_lbl = "Poor" if val < 0.35 else ("Fair" if val < 0.60 else "Good")
                ax_idx.text(val + 0.03, hb.get_y() + hb.get_height() / 2,
                            f"{val:.2f}  ({bar_lbl})",
                            va="center", fontsize=11, fontweight="bold",
                            color=PALETTE["text"])

        # ── Super-title ──────────────────────────────────────────────────
        fig.suptitle(
            f"Multi-Index Vegetation Health Analysis  ·  Total Area: {total_area_km2:.2f} km²",
            fontsize=14, fontweight="bold", color=PALETTE["text"], y=1.005,
        )

        plt.rcParams.update(plt.rcParamsDefault)
        return fig
