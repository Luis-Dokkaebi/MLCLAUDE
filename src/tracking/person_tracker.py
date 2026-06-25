# src/tracking/person_tracker.py

import supervision as sv

class PersonTracker:
    def __init__(self):
        self.tracker = sv.ByteTrack()

    def update(self, detections):
        # Recibe detecciones en formato de supervision (ya las adaptaremos desde YOLO)
        tracked_detections = self.tracker.update_with_detections(detections)
        return tracked_detections
