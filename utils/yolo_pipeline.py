from ultralytics import YOLO
import cv2
import numpy as np
from pathlib import Path

# Tile size used for both single-image resize and tiled detection
TILE_SIZE    = 480
TILE_OVERLAP = 0.30   # 20 % — prevents missing detections near tile edges
TILE_THRESH  = 960    # pixels — images larger than this in any dimension use tiling


class YOLOPipeline:
    # BGR colors — converted to RGB before display in Streamlit
    # Class 0 = Critical Condition  → Red
    # Class 1 = Healthy             → Green
    # Class 2 = Early Stress        → Orange
    CLASS_COLORS_BGR = {
        0: (0, 0, 220),    # Red
        1: (0, 180, 0),    # Green
        2: (0, 130, 255),  # Orange
    }

    def __init__(self, model_path):
        self.model = YOLO(model_path)

    # ──────────────────────────────────────────────────────────────────────────
    # Single-image detection (small AOI — resize to TILE_SIZE × TILE_SIZE)
    # ──────────────────────────────────────────────────────────────────────────

    def detect(self, image_path, conf_threshold=0.2):
        from PIL import Image as PILImage
        img = PILImage.open(image_path).resize((TILE_SIZE, TILE_SIZE), PILImage.LANCZOS)
        results = self.model(img, conf=conf_threshold)[0]
        return results

    def annotate_image(self, image_path, results):
        """Draw colored bounding boxes on a TILE_SIZE×TILE_SIZE image — no labels, no scores."""
        img = cv2.imread(str(image_path))
        img = cv2.resize(img, (TILE_SIZE, TILE_SIZE))
        for box in results.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cls   = int(box.cls[0])
            color = self.CLASS_COLORS_BGR.get(cls, (200, 200, 200))
            cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
        return img

    # ──────────────────────────────────────────────────────────────────────────
    # Tiled detection (large AOI — slide a TILE_SIZE window with overlap)
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _iou(a, b):
        """Intersection-over-Union for two boxes [x1, y1, x2, y2, ...]."""
        ix1 = max(a[0], b[0]);  iy1 = max(a[1], b[1])
        ix2 = min(a[2], b[2]);  iy2 = min(a[3], b[3])
        inter = max(0.0, ix2 - ix1) * max(0.0, iy2 - iy1)
        area_a = (a[2] - a[0]) * (a[3] - a[1])
        area_b = (b[2] - b[0]) * (b[3] - b[1])
        union  = area_a + area_b - inter
        return inter / union if union > 0 else 0.0

    @staticmethod
    def _nms(boxes, iou_threshold=0.40):
        """
        Non-maximum suppression.
        boxes: list of [x1, y1, x2, y2, cls, conf]
        Returns deduplicated list (per-class IoU filtering).
        """
        if not boxes:
            return []
        boxes = sorted(boxes, key=lambda b: b[5], reverse=True)
        kept  = []
        while boxes:
            best  = boxes.pop(0)
            kept.append(best)
            boxes = [
                b for b in boxes
                if int(b[4]) != int(best[4]) or YOLOPipeline._iou(best, b) < iou_threshold
            ]
        return kept

    def detect_tiled(self, image_path, conf_threshold=0.2):
        """
        Divide the image into overlapping TILE_SIZE×TILE_SIZE tiles, run the
        model on each tile, remap box coordinates to full-image space, then
        apply NMS to remove cross-tile duplicates.

        Returns a list of [x1, y1, x2, y2, cls, conf] in full-image pixels.
        """
        from PIL import Image as PILImage
        img_pil = PILImage.open(image_path).convert("RGB")
        W, H    = img_pil.size

        stride   = int(TILE_SIZE * (1.0 - TILE_OVERLAP))
        all_boxes = []

        # Build tile origin grid (ensure we always cover the far edge)
        def _starts(dim):
            pts = list(range(0, dim - TILE_SIZE, stride))
            pts.append(dim - TILE_SIZE)
            return sorted(set(max(0, p) for p in pts))

        for y0 in _starts(H):
            for x0 in _starts(W):
                x1c = min(x0 + TILE_SIZE, W)
                y1c = min(y0 + TILE_SIZE, H)

                tile = img_pil.crop((x0, y0, x1c, y1c))

                # Pad edge tiles so the model always sees TILE_SIZE × TILE_SIZE
                if tile.size != (TILE_SIZE, TILE_SIZE):
                    padded = PILImage.new("RGB", (TILE_SIZE, TILE_SIZE), (0, 0, 0))
                    padded.paste(tile, (0, 0))
                    tile = padded

                results = self.model(tile, conf=conf_threshold)[0]

                # Scale factor: boxes are in padded-tile space → actual crop space
                sx = (x1c - x0) / TILE_SIZE
                sy = (y1c - y0) / TILE_SIZE

                for box in results.boxes:
                    bx1, by1, bx2, by2 = box.xyxy[0].tolist()
                    cls  = int(box.cls[0])
                    conf = float(box.conf[0])
                    # Map from padded-tile → full-image coordinates
                    all_boxes.append([
                        bx1 * sx + x0,
                        by1 * sy + y0,
                        bx2 * sx + x0,
                        by2 * sy + y0,
                        cls,
                        conf,
                    ])

        return YOLOPipeline._nms(all_boxes)

    def annotate_tiled(self, image_path, boxes):
        """Draw merged detection boxes on the full-size source image."""
        img = cv2.imread(str(image_path))
        for box in boxes:
            x1, y1, x2, y2, cls, _ = box
            color = self.CLASS_COLORS_BGR.get(int(cls), (200, 200, 200))
            cv2.rectangle(img, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
        return img
    
    def process_batch(self, image_paths, conf_threshold=0.5):
        detections = {}
        class_counts = {0: 0, 1: 0, 2: 0}
        
        for img_path in image_paths:
            results = self.detect(img_path, conf_threshold)
            annotated = self.annotate_image(img_path, results)
            
            for box in results.boxes:
                cls = int(box.cls[0])
                class_counts[cls] = class_counts.get(cls, 0) + 1
            
            detections[img_path] = {
                'results': results,
                'annotated': annotated,
                'count': len(results.boxes)
            }
        
        return detections, class_counts
    
    def create_rgb_from_bands(self, b02, b03, b04, output_path):
        import rasterio
        
        with rasterio.open(b04) as src:
            red = src.read(1)
        with rasterio.open(b03) as src:
            green = src.read(1)
        with rasterio.open(b02) as src:
            blue = src.read(1)
        
        if red.max() > 255:
            red = ((red / red.max()) * 255).astype(np.uint8)
            green = ((green / green.max()) * 255).astype(np.uint8)
            blue = ((blue / blue.max()) * 255).astype(np.uint8)
        
        rgb = np.dstack([red, green, blue])
        cv2.imwrite(str(output_path), cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))
        return output_path
