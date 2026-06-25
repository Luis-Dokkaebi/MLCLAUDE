# src/acquisition/video_stream.py

import cv2
from threading import Thread

class VideoStream:
    def __init__(self, source, name="Camera"):
        self.stream = cv2.VideoCapture(source)
        self.name = name
        self.stopped = False
        self.frame = None

    def start(self):
        Thread(target=self.update, args=(), daemon=True).start()
        return self

    def update(self):
        while not self.stopped:
            ret, frame = self.stream.read()
            if not ret:
                self.stop()
            else:
                self.frame = frame

    def read(self):
        return self.frame

    def stop(self):
        self.stopped = True
        self.stream.release()
