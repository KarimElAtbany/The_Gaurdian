import numpy as np
import rasterio
import rasterio.mask
from shapely.geometry import shape, mapping, Polygon
from pyproj import Transformer
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.gridspec import GridSpec


class VegetationHealthPipeline:
    """
    Multi-index vegetation health pipeline using:
      - MSAVI  : soil-corrected greenness (replaces raw NDVI for arid regions)
      - NDRE   : red-edge chlorophyll / early stress detection
      - NDWI   : canopy water / drought stress
      - CIre   : red-edge chlorophyll index (nutrient status)
    A weighted composite score drives the final 4-class health map.
    """

    CLASS_LABELS = ["Dead / Bare", "Severe Stress", "Moderate Stress", "Healthy"]
    CLASS_COLORS = ["#d73027", "#fdae61", "#ffffbf", "#1a9850"]

    INDEX_WEIGHTS = {
        "MSAVI": 0.20,
        "NDRE":  0.35,
        "NDWI":  0.30,
        "CIre":  0.15,
    }

    def __init__(self, thresholds=(0.20, 0.40, 0.60)):
        """
        thresholds: (t1, t2, t3) on the composite score [0-1].
          score <= t1  → Dead/Bare
          t1 < score <= t2 → Severe Stress
          t2 < score <= t3 → Moderate Stress
          score > t3  → Healthy
        """
        self.thresholds = thresholds

    def _reproject_polygon(self, geojson_polygon, src_crs):
        polygon_shape = shape(geojson_polygon)
        transformer = Transformer.from_crs("EPSG:4326", src_crs, always_xy=True)
        coords = list(polygon_shape.exterior.coords)
        reprojected = [transformer.transform(x, y) for x, y in coords]
        return [mapping(Polygon(reprojected))]

    def _read_band(self, path, geojson_masks):
        with rasterio.open(path) as src:
            data, transform = rasterio.mask.mask(src, geojson_masks, crop=True, nodata=0)
            pixel_size_m = abs(src.transform.a)
            profile = src.profile
        arr = data[0].astype("float32")
        return arr, transform, profile, pixel_size_m

    def _normalise(self, arr):
        if arr.max() > 1.0:
            arr = arr / 10000.0
        return arr

    def crop_and_load_bands(self, bands_paths, geojson_polygon):
        """
        Load and crop all required bands to the AOI.

        bands_paths: dict with keys B04, B05, B07, B08, B8A, B11
        Returns dict of numpy arrays + shared metadata.
        """
        ref_path = bands_paths.get('B08') or bands_paths.get('B04')
        with rasterio.open(ref_path) as src:
            raster_crs = src.crs

        geojson_masks = self._reproject_polygon(geojson_polygon, raster_crs)

        loaded = {}
        transform = profile = pixel_size_m = None

        for key, path in bands_paths.items():
            if path is None:
                continue
            arr, t, p, psm = self._read_band(path, geojson_masks)
            loaded[key] = self._normalise(arr)
            if transform is None:
                transform, profile, pixel_size_m = t, p, psm

        return loaded, transform, profile, pixel_size_m

    def compute_indices(self, bands):
        """
        Compute MSAVI, NDRE, NDWI, CIre from band arrays.
        All indices are scaled to [0, 1] for compositing.
        """
        red  = bands.get('B04')
        re1  = bands.get('B05')
        re3  = bands.get('B07')
        nir  = bands.get('B08')
        nir8 = bands.get('B8A')
        swir = bands.get('B11')

        invalid = (nir == 0) & (red == 0)

        msavi = ndre = ndwi = cire = None

        if red is not None and nir is not None:
            val = (2 * nir + 1 - np.sqrt((2 * nir + 1) ** 2 - 8 * (nir - red))) / 2
            msavi = np.clip(val, -1.0, 1.0)
            msavi[invalid] = np.nan

        if re1 is not None and nir is not None:
            ndre = np.clip((nir - re1) / (nir + re1 + 1e-10), -1.0, 1.0)
            ndre[invalid] = np.nan

        nir_ref = nir8 if nir8 is not None else nir
        if nir_ref is not None and swir is not None:
            ndwi = np.clip((nir_ref - swir) / (nir_ref + swir + 1e-10), -1.0, 1.0)
            ndwi[invalid] = np.nan

        if re1 is not None and re3 is not None:
            cire = np.clip(re3 / (re1 + 1e-10) - 1, 0, 10) / 10.0
            cire[invalid] = np.nan

        return {
            "MSAVI": msavi,
            "NDRE":  ndre,
            "NDWI":  ndwi,
            "CIre":  cire,
        }

    def _scale_to_01(self, arr, vmin, vmax):
        scaled = (arr - vmin) / (vmax - vmin + 1e-10)
        return np.clip(scaled, 0.0, 1.0)

    def compute_composite(self, indices):
        """
        Build a weighted composite health score in [0, 1].
        Each index is linearly scaled to [0, 1] before weighting.
        """
        scale_ranges = {
            "MSAVI": (-0.1, 0.6),
            "NDRE":  (-0.1, 0.5),
            "NDWI":  (-0.3, 0.5),
            "CIre":  (0.0,  1.0),
        }

        composite = np.zeros_like(next(v for v in indices.values() if v is not None))
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

        nan_mask = np.all(
            [np.isnan(v) for v in indices.values() if v is not None],
            axis=0
        )
        composite[nan_mask] = np.nan

        return composite

    def classify_health(self, composite):
        t1, t2, t3 = self.thresholds
        health_map = np.full(composite.shape, 255, dtype=np.uint8)
        health_map[~np.isnan(composite) & (composite <= t1)] = 0
        health_map[~np.isnan(composite) & (composite > t1) & (composite <= t2)] = 1
        health_map[~np.isnan(composite) & (composite > t2) & (composite <= t3)] = 2
        health_map[~np.isnan(composite) & (composite > t3)] = 3
        return health_map

    def compute_statistics(self, health_map, composite, pixel_area_km2):
        valid_mask = health_map != 255
        total_valid_px = valid_mask.sum()
        total_area_km2 = total_valid_px * pixel_area_km2

        stats = {}
        for cid, label in enumerate(self.CLASS_LABELS):
            px = int((health_map == cid).sum())
            area = px * pixel_area_km2
            pct = (px / total_valid_px * 100) if total_valid_px > 0 else 0
            stats[cid] = {"label": label, "pixels": px, "area_km2": area, "pct": pct}

        valid_composite = composite[~np.isnan(composite)]
        composite_mean = float(np.nanmean(valid_composite)) if valid_composite.size > 0 else 0.0

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

    def create_visualization(self, health_map, indices, composite, stats, total_area_km2):
        cmap = ListedColormap(self.CLASS_COLORS)
        norm = BoundaryNorm([-0.5, 0.5, 1.5, 2.5, 3.5], cmap.N)
        display_map = np.ma.masked_where(health_map == 255, health_map)

        index_list = [(k, v) for k, v in indices.items() if v is not None]
        n_indices = len(index_list)

        fig = plt.figure(figsize=(22, 14))
        gs = GridSpec(3, max(n_indices, 3), figure=fig, hspace=0.38, wspace=0.32)

        ax_health = fig.add_subplot(gs[0, 0])
        im = ax_health.imshow(display_map, cmap=cmap, norm=norm, interpolation="nearest")
        cb = plt.colorbar(im, ax=ax_health, ticks=[0, 1, 2, 3], shrink=0.8)
        cb.ax.set_yticklabels(self.CLASS_LABELS, fontsize=8)
        ax_health.set_title("Composite Health Map", fontweight="bold")
        ax_health.axis("off")

        ax_comp = fig.add_subplot(gs[0, 1])
        comp_disp = np.ma.masked_where(np.isnan(composite), composite)
        im2 = ax_comp.imshow(comp_disp, cmap="RdYlGn", vmin=0, vmax=1, interpolation="nearest")
        plt.colorbar(im2, ax=ax_comp, shrink=0.8, label="Score")
        ax_comp.set_title("Composite Health Score", fontweight="bold")
        ax_comp.axis("off")

        ax_pie = fig.add_subplot(gs[0, 2])
        sizes  = [stats[i]["pct"] for i in range(4) if stats[i]["pixels"] > 0]
        labels = [f"{stats[i]['label']}\n{stats[i]['pct']:.1f}%" for i in range(4) if stats[i]["pixels"] > 0]
        colors = [self.CLASS_COLORS[i] for i in range(4) if stats[i]["pixels"] > 0]
        ax_pie.pie(sizes, labels=labels, colors=colors, startangle=90, wedgeprops={"edgecolor": "white"})
        ax_pie.set_title("Class Distribution", fontweight="bold")

        index_cmaps = {"MSAVI": "RdYlGn", "NDRE": "PiYG", "NDWI": "Blues", "CIre": "YlOrRd"}
        index_ranges = {"MSAVI": (-0.1, 0.6), "NDRE": (-0.1, 0.5), "NDWI": (-0.3, 0.5), "CIre": (0, 1)}
        index_titles = {
            "MSAVI": "MSAVI — Soil-Adj. Greenness",
            "NDRE":  "NDRE — Chlorophyll / Early Stress",
            "NDWI":  "NDWI — Water / Drought Stress",
            "CIre":  "CIre — Nutrient Status",
        }

        for col, (name, arr) in enumerate(index_list):
            ax = fig.add_subplot(gs[1, col])
            vmin, vmax = index_ranges.get(name, (-1, 1))
            disp = np.ma.masked_where(np.isnan(arr), arr)
            im_idx = ax.imshow(disp, cmap=index_cmaps.get(name, "RdYlGn"), vmin=vmin, vmax=vmax, interpolation="nearest")
            plt.colorbar(im_idx, ax=ax, shrink=0.8)
            ax.set_title(index_titles.get(name, name), fontweight="bold", fontsize=9)
            ax.axis("off")

        ax_bar = fig.add_subplot(gs[2, 0])
        ax_bar.bar(self.CLASS_LABELS, [stats[i]["area_km2"] for i in range(4)],
                   color=self.CLASS_COLORS, edgecolor="black")
        ax_bar.set_ylabel("Area (km²)")
        ax_bar.set_title("Area per Health Class", fontweight="bold")
        ax_bar.grid(axis="y", alpha=0.3)
        plt.setp(ax_bar.get_xticklabels(), fontsize=8, rotation=15)

        ax_hist = fig.add_subplot(gs[2, 1])
        valid_comp = composite[~np.isnan(composite)]
        ax_hist.hist(valid_comp.ravel(), bins=80, color="steelblue", alpha=0.8)
        for t, color in zip(self.thresholds, ["#d73027", "#fdae61", "#1a9850"]):
            ax_hist.axvline(t, color=color, linewidth=1.5, linestyle="--")
        ax_hist.set_xlabel("Composite Score")
        ax_hist.set_ylabel("Pixel Count")
        ax_hist.set_title("Score Distribution", fontweight="bold")
        ax_hist.grid(alpha=0.3)

        if n_indices >= 3:
            ax_radar = fig.add_subplot(gs[2, 2])
            mean_vals = []
            radar_names = []
            for name, arr in index_list:
                vmin, vmax = index_ranges.get(name, (-1, 1))
                scaled = np.clip((arr - vmin) / (vmax - vmin + 1e-10), 0, 1)
                mean_vals.append(float(np.nanmean(scaled)))
                radar_names.append(name)
            bars = ax_radar.barh(radar_names, mean_vals, color=["#4dac26", "#b8e186", "#4393c3", "#f4a582"])
            ax_radar.set_xlim(0, 1)
            ax_radar.set_xlabel("Mean Scaled Value")
            ax_radar.set_title("Index Summary", fontweight="bold")
            ax_radar.grid(axis="x", alpha=0.3)
            for bar, val in zip(bars, mean_vals):
                ax_radar.text(val + 0.02, bar.get_y() + bar.get_height() / 2,
                              f"{val:.2f}", va="center", fontsize=9)

        fig.suptitle(
            f"Multi-Index Vegetation Health Analysis  |  Area: {total_area_km2:.2f} km²",
            fontsize=14, fontweight="bold"
        )

        return fig


NDVIPipeline = VegetationHealthPipeline
