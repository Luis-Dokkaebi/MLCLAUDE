# src/detection/person_detector.py

from ultralytics import YOLO
import numpy as np
import supervision as sv
import sys, os

# Allow config import from both dev and frozen contexts
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

class PersonDetector:
    def __init__(self, model_path=None, confidence_threshold=0.4):
        if model_path is None:
            try:
                from config.config import MODEL_PATH
                model_path = MODEL_PATH
            except ImportError:
                model_path = "yolov8n.pt"
        self.model = YOLO(model_path)
        self.confidence_threshold = confidence_threshold

    def detect(self, frame):
        # Infer on frame
        results = self.model(frame)[0]
        
        # Convert to supervision detections
        detections = sv.Detections.from_ultralytics(results)
        
        # Filter classes: 0 is person, 67 is cell phone (in COCO)
        mask = np.isin(detections.class_id, [0, 67])
        detections = detections[mask]
        
        # Filter by confidence
        detections = detections[detections.confidence > self.confidence_threshold]

        return detections
