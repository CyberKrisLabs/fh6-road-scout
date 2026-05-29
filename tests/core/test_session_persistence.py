"""Tests for SessionStore: save/load scan session to JSON."""

import json
from pathlib import Path

import pytest

from app.core.session_store import SessionStore
from app.models.scan_result import DiscoveryState, ScanPoint, ScanSession


def _make_session() -> ScanSession:
    pts = [
        ScanPoint(ref_x=10, ref_y=20, state=DiscoveryState.DISCOVERED, confidence=0.9),
        ScanPoint(ref_x=30, ref_y=40, state=DiscoveryState.UNDISCOVERED, confidence=0.2),
        ScanPoint(ref_x=50, ref_y=60, state=DiscoveryState.UNKNOWN),
    ]
    return ScanSession(
        points=pts,
        reference_map_path="/some/map.png",
        calibration_data={"matrix": [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]},
    )


class TestSessionStoreSave:
    def test_creates_file(self, tmp_path: Path) -> None:
        path = str(tmp_path / "session.json")
        SessionStore.save(_make_session(), path)
        assert Path(path).exists()

    def test_saved_json_has_points_key(self, tmp_path: Path) -> None:
        path = str(tmp_path / "session.json")
        SessionStore.save(_make_session(), path)
        data = json.loads(Path(path).read_text())
        assert "points" in data

    def test_saved_json_has_calibration(self, tmp_path: Path) -> None:
        path = str(tmp_path / "session.json")
        SessionStore.save(_make_session(), path)
        data = json.loads(Path(path).read_text())
        assert "calibration" in data

    def test_saved_point_count_matches(self, tmp_path: Path) -> None:
        path = str(tmp_path / "session.json")
        s = _make_session()
        SessionStore.save(s, path)
        data = json.loads(Path(path).read_text())
        assert len(data["points"]) == len(s.points)

    def test_point_state_serialised(self, tmp_path: Path) -> None:
        path = str(tmp_path / "session.json")
        SessionStore.save(_make_session(), path)
        data = json.loads(Path(path).read_text())
        states = [p["state"] for p in data["points"]]
        assert "discovered" in states
        assert "undiscovered" in states


class TestSessionStoreLoad:
    def test_round_trip_point_count(self, tmp_path: Path) -> None:
        path = str(tmp_path / "session.json")
        original = _make_session()
        SessionStore.save(original, path)
        loaded = SessionStore.load(path)
        assert loaded.total == original.total

    def test_round_trip_states(self, tmp_path: Path) -> None:
        path = str(tmp_path / "session.json")
        original = _make_session()
        SessionStore.save(original, path)
        loaded = SessionStore.load(path)
        orig_states = [p.state for p in original.points]
        load_states = [p.state for p in loaded.points]
        assert orig_states == load_states

    def test_round_trip_coordinates(self, tmp_path: Path) -> None:
        path = str(tmp_path / "session.json")
        original = _make_session()
        SessionStore.save(original, path)
        loaded = SessionStore.load(path)
        assert loaded.points[0].ref_x == 10
        assert loaded.points[0].ref_y == 20

    def test_round_trip_confidence(self, tmp_path: Path) -> None:
        path = str(tmp_path / "session.json")
        original = _make_session()
        SessionStore.save(original, path)
        loaded = SessionStore.load(path)
        assert abs(loaded.points[0].confidence - 0.9) < 1e-6

    def test_round_trip_calibration(self, tmp_path: Path) -> None:
        path = str(tmp_path / "session.json")
        original = _make_session()
        SessionStore.save(original, path)
        loaded = SessionStore.load(path)
        assert loaded.calibration_data == original.calibration_data

    def test_missing_reference_image_does_not_crash(self, tmp_path: Path) -> None:
        path = str(tmp_path / "session.json")
        s = _make_session()
        SessionStore.save(s, path)
        loaded = SessionStore.load(path)
        assert loaded.reference_map_path == "/some/map.png"

    def test_corrupt_json_raises_value_error(self, tmp_path: Path) -> None:
        path = str(tmp_path / "bad.json")
        Path(path).write_text("not valid json {{{")
        with pytest.raises(ValueError):
            SessionStore.load(path)

    def test_missing_file_raises_file_not_found(self) -> None:
        with pytest.raises(FileNotFoundError):
            SessionStore.load("nonexistent_session.json")
