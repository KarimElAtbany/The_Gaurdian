import cv2
import numpy as np
from pathlib import Path


class YOLOPipeline:
    CLASS_INFO = {
        0: {'name': 'unhealthy', 'color': (0, 0, 255)},
        1: {'name': 'healthy',   'color': (0, 255, 0)},
        2: {'name': 'yellow',    'color': (0, 255, 255)},
    }

    def __init__(self, model_path):
        from ultralytics import YOLO
        self.model = YOLO(model_path)

    def detect(self, image_path, conf_threshold=0.5):
        results = self.model(str(image_path), conf=conf_threshold)[0]
        return results

    def annotate_image(self, image_path, results):
        img = cv2.imread(str(image_path))
        if img is None:
            raise FileNotFoundError(f"Cannot read image: {image_path}")

        for box in results.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            conf = float(box.conf[0])
            cls  = int(box.cls[0])
            info = self.CLASS_INFO.get(cls, {'name': f'cls{cls}', 'color': (255, 255, 255)})

            cv2.rectangle(img, (x1, y1), (x2, y2), info['color'], 2)
            label = f"{info['name']} {conf:.2f}"
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(img, (x1, y1 - th - 4), (x1 + tw, y1), info['color'], -1)
            cv2.putText(img, label, (x1, y1 - 4),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)

        return img

    def process_batch(self, image_paths, conf_threshold=0.5):
        detections = {}
        class_counts = {0: 0, 1: 0, 2: 0}

        for img_path in image_paths:
            results   = self.detect(img_path, conf_threshold)
            annotated = self.annotate_image(img_path, results)

            for box in results.boxes:
                cls = int(box.cls[0])
                class_counts[cls] = class_counts.get(cls, 0) + 1

            detections[str(img_path)] = {
                'results':   results,
                'annotated': annotated,
                'count':     len(results.boxes),
            }

        return detections, class_counts

    def create_rgb_from_bands(self, b02_path, b03_path, b04_path, output_path):
        import rasterio

        def _read_norm(path):
            with rasterio.open(path) as src:
                arr = src.read(1).astype('float32')
            p2, p98 = np.percentile(arr[arr > 0], [2, 98]) if arr.max() > 0 else (0, 1)
            normed = np.clip((arr - p2) / (p98 - p2 + 1e-10), 0, 1)
            return (normed * 255).astype(np.uint8)

        red   = _read_norm(b04_path)
        green = _read_norm(b03_path)
        blue  = _read_norm(b02_path)

        rgb = np.dstack([red, green, blue])
        cv2.imwrite(str(output_path), cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))
        return output_path
