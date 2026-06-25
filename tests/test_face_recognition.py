import unittest
import sys
import os
import shutil
from unittest.mock import MagicMock, patch

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

# Mock face_recognition before importing FaceRecognizer
# This is necessary because the environment might not have face_recognition installed
sys.modules['face_recognition'] = MagicMock()
# Mock cv2 if not present
sys.modules['cv2'] = MagicMock()
# Set cv2 constants
sys.modules['cv2'].COLOR_BGR2RGB = 4

from recognition.face_recognizer import FaceRecognizer

class TestFaceRecognizer(unittest.TestCase):
    def setUp(self):
        self.faces_dir = "tests/data/faces"
        self.encodings_file = "tests/data/faces/encodings.pkl"
        os.makedirs(self.faces_dir, exist_ok=True)
        # Clean up
        if os.path.exists(self.encodings_file):
            os.remove(self.encodings_file)

    def tearDown(self):
        if os.path.exists("tests/data"):
            shutil.rmtree("tests/data")

    def test_load_known_faces(self):
        # We need to mock the face_recognition module used INSIDE FaceRecognizer
        # Since we mocked sys.modules['face_recognition'], the imported module is the mock.
        import face_recognition
        
        face_recognition.load_image_file.return_value = "dummy_image"
        face_recognition.face_encodings.return_value = [[0.1, 0.2, 0.3]]
        
        # Create dummy face file
        person_dir = os.path.join(self.faces_dir, "TestPerson")
        os.makedirs(person_dir, exist_ok=True)
        with open(os.path.join(person_dir, "face.jpg"), "w") as f:
            f.write("dummy")

        recognizer = FaceRecognizer(faces_dir=self.faces_dir, encodings_file=self.encodings_file)
        
        self.assertEqual(len(recognizer.known_face_names), 1)
        self.assertEqual(recognizer.known_face_names[0], "TestPerson")
        self.assertTrue(os.path.exists(self.encodings_file))

    def test_recognize_face(self):
        import face_recognition
        import numpy as np
        
        recognizer = FaceRecognizer(faces_dir=self.faces_dir, encodings_file=self.encodings_file)
        recognizer.known_face_encodings = [[0.1, 0.2, 0.3]]
        recognizer.known_face_names = ["TestPerson"]

        # Mock frame
        frame = np.zeros((100, 100, 3), dtype=np.uint8)

        # Case 1: Match
        face_recognition.face_locations.return_value = [(10, 10, 50, 50)]
        face_recognition.face_encodings.return_value = [[0.1, 0.2, 0.3]]
        face_recognition.compare_faces.return_value = [True]
        face_recognition.face_distance.return_value = [0.0]

        name = recognizer.recognize_face(frame)
        self.assertEqual(name, "TestPerson")

        # Case 2: No Match
        face_recognition.compare_faces.return_value = [False]
        name = recognizer.recognize_face(frame)
        self.assertEqual(name, "Unknown")

if __name__ == '__main__':
    unittest.main()
