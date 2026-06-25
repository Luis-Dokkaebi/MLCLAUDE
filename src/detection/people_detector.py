import cv2
import os
import sys
import json
from ultralytics import YOLO

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

try:
    from config.config import ZONAS_FILE as _DEFAULT_ZONAS, MODEL_PATH as _DEFAULT_MODEL
except ImportError:
    _DEFAULT_ZONAS = "data/zonas/zonas.json"
    _DEFAULT_MODEL = "yolov8n.pt"

class PeopleDetector:
    def __init__(self, source=0, zonas_path=None, model_path=None):
        if zonas_path is None:
            zonas_path = _DEFAULT_ZONAS
        if model_path is None:
            model_path = _DEFAULT_MODEL
        self.source = source  # 0 para webcam, o URL de cámara IP
        self.model = YOLO(model_path)
        self.zonas = self.load_zonas(zonas_path)

    def load_zonas(self, path):
        full_path = os.path.abspath(path)
        if not os.path.exists(full_path):
            print("❌ Archivo de zonas no encontrado:", full_path)
            return {}
        with open(full_path, 'r') as f:
            data = json.load(f)
        print("✅ Zonas cargadas:", list(data.keys()))
        return data

    def point_in_polygon(self, point, polygon):
        # Algoritmo de ray casting
        x, y = point
        inside = False
        n = len(polygon)
        for i in range(n):
            xi, yi = polygon[i]
            xj, yj = polygon[(i + 1) % n]
            if ((yi > y) != (yj > y)) and \
               (x < (xj - xi) * (y - yi) / ((yj - yi) + 1e-9) + xi):
                inside = not inside
        return inside

    def run(self):
        cap = cv2.VideoCapture(self.source)

        if not cap.isOpened():
            print("❌ No se pudo abrir la cámara o fuente de video.")
            return

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            results = self.model(frame)[0]

            for result in results.boxes.data:
                x1, y1, x2, y2, conf, cls = result.tolist()
                if int(cls) != 0:  # Solo clase 0 = persona
                    continue

                cx, cy = int((x1 + x2) / 2), int((y1 + y2) / 2)
                estado = "Fuera de zona"

                for zona_nombre, puntos in self.zonas.items():
                    if self.point_in_polygon((cx, cy), puntos):
                        estado = f"En zona: {zona_nombre}"
                        break

                color = (0, 255, 0) if "En zona" in estado else (0, 0, 255)
                cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
                cv2.circle(frame, (cx, cy), 4, color, -1)
                cv2.putText(frame, estado, (int(x1), int(y1) - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

            cv2.imshow("Detección de personas", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()
