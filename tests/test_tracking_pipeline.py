"""
CR-04 regression: the shared TrackingPipeline must PERSIST tracking data.

Before CR-04 the GUI worker never wrote to the DB, so reports were always empty.
These tests exercise the pipeline with lightweight fakes (no cv2/torch/supervision)
plus the real DatabaseManager + StateManager to prove rows actually land in SQLite.
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

import pytest
from src.tracking.tracking_pipeline import TrackingPipeline
from src.storage.database_manager import DatabaseManager
from src.analysis.state_manager import StateManager


class FakeTracked:
    def __init__(self, boxes, ids):
        self.xyxy = boxes
        self.tracker_id = ids


class FakeTracker:
    """Returns a fixed tracked detection regardless of input."""
    def __init__(self, boxes, ids):
        self._tracked = FakeTracked(boxes, ids)
    def update(self, person_detections):
        return self._tracked


class FakeZoneChecker:
    def __init__(self, result):
        self._result = result
    def check(self, x, y):
        return dict(self._result)


class FakeFaceRecognizer:
    def __init__(self, name="Alice"):
        self._name = name
    def recognize_face(self, frame, bbox=None):
        return self._name


@pytest.fixture
def db(tmp_path):
    return DatabaseManager(db_path=str(tmp_path / "db" / "local_tracking.db"))


def _make_pipeline(db, zones, face_name=None, **kw):
    tracker = FakeTracker(boxes=[(10, 20, 110, 220)], ids=[1])
    zc = FakeZoneChecker(zones)
    sm = StateManager(db)
    fr = FakeFaceRecognizer(face_name) if face_name else None
    return TrackingPipeline(db=db, zone_checker=zc, tracker=tracker,
                            state_manager=sm, face_recognizer=fr,
                            snapshots_dir=None, **kw)


def test_pipeline_persists_tracking_rows(db):
    """A person inside a configured zone must produce tracking rows in the DB."""
    pipe = _make_pipeline(db, {"ZonaA": True}, face_name="Alice",
                          db_write_interval=1, face_check_interval=1)
    frame = object()  # never touched (snapshots_dir=None, no cv2 path)
    for _ in range(3):
        pipe.process(frame, person_detections=None, phones_data=[])

    rows = db.get_all_records()
    assert len(rows) == 3, f"expected 3 tracking rows, got {len(rows)}"


def test_pipeline_records_attendance_for_recognized_employee(db):
    """StateManager wiring must register attendance for a recognized employee."""
    pipe = _make_pipeline(db, {"ZonaA": True}, face_name="Bob",
                          db_write_interval=1, face_check_interval=1)
    pipe.process(object(), None, [])
    assert "Bob" in db.get_unique_employees()


def test_db_write_throttle(db):
    """With db_write_interval=15, only every 15th frame writes a tracking row."""
    pipe = _make_pipeline(db, {"ZonaA": True}, face_name="Alice",
                          db_write_interval=15, face_check_interval=10)
    for _ in range(30):
        pipe.process(object(), None, [])
    # frames 15 and 30 write → 2 rows
    assert len(db.get_all_records()) == 2


def test_track_data_returned_for_drawing(db):
    pipe = _make_pipeline(db, {"ZonaA": True}, face_name="Alice",
                          db_write_interval=1, face_check_interval=1)
    td = pipe.process(object(), None, [])
    assert len(td) == 1
    assert td[0]['name'] == "Alice"
    assert td[0]['inside'] is True
    assert td[0]['bbox'] == (10, 20, 110, 220)


def test_no_zone_no_crash(db):
    """If no zones are configured, pipeline must not crash (no rows, no error)."""
    pipe = _make_pipeline(db, {}, face_name="Alice",
                          db_write_interval=1, face_check_interval=1)
    td = pipe.process(object(), None, [])
    assert len(td) == 1
    assert db.get_all_records() == []
