"""Tests for RoadMapper — raster scan + road cursor detection → road_points.json."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import cv2
import numpy as np
import pytest
from pytestqt.qtbot import QtBot

from app.core.road_cursor_detector import RoadCursorDetector
from app.core.road_mapper import RoadMapper
from app.core.raster_scanner import RasterScanner
from app.models.scan_result import RoadType, ScanPoint

_MOVE = "app.core.raster_scanner.pyautogui.moveTo"


def _screenshot_with_cursor(cx: int, cy: int, size: tuple[int, int] = (200, 200)) -> np.ndarray:
    """Synthetic screenshot with the road cursor centred at (cx, cy)."""
    img = np.full((size[1], size[0], 3), (40, 80, 40), dtype=np.uint8)
    cv2.circle(img, (cx, cy), 28, (255, 255, 255), thickness=4)
    cv2.circle(img, (cx, cy), 17, (255, 255, 255), thickness=-1)
    return img


def _blank_screenshot(size: tuple[int, int] = (200, 200)) -> np.ndarray:
    return np.full((size[1], size[0], 3), (40, 80, 40), dtype=np.uint8)


class TestRoadMapperPointCollection:
    def test_emits_point_when_cursor_detected(self, qtbot: QtBot, tmp_path: Path) -> None:
        scanner = RasterScanner(region=(0, 0, 0, 0), step_px=100, dwell_ms=0)
        detector = RoadCursorDetector()
        mapper = RoadMapper(scanner, detector, str(tmp_path / "roads.json"))

        points: list[ScanPoint] = []
        mapper.point_found.connect(points.append)

        screen = _screenshot_with_cursor(100, 100)
        with patch(_MOVE), patch.object(mapper, "_capture", return_value=screen):
            mapper.run()

        assert len(points) == 1

    def test_no_point_when_cursor_not_detected(self, qtbot: QtBot, tmp_path: Path) -> None:
        scanner = RasterScanner(region=(0, 0, 0, 0), step_px=100, dwell_ms=0)
        mapper = RoadMapper(scanner, RoadCursorDetector(), str(tmp_path / "roads.json"))
        points: list[ScanPoint] = []
        mapper.point_found.connect(points.append)

        with patch(_MOVE), patch.object(mapper, "_capture", return_value=_blank_screenshot()):
            mapper.run()

        assert len(points) == 0

    def test_deduplicates_nearby_points(self, qtbot: QtBot, tmp_path: Path) -> None:
        # 3 scanner positions all map to the same road position (road cursor snaps to
        # the same road from slightly different mouse positions) → only 1 point emitted.
        scanner = RasterScanner(region=(0, 0, 0, 20), step_px=10, dwell_ms=0)
        mapper = RoadMapper(scanner, RoadCursorDetector(), str(tmp_path / "roads.json"),
                            dedup_radius=20)

        points: list[ScanPoint] = []
        mapper.point_found.connect(points.append)
        screen = _screenshot_with_cursor(100, 100)

        with patch(_MOVE), \
             patch.object(mapper, "_capture", return_value=screen), \
             patch.object(mapper, "_to_map_coords", return_value=(100, 100)):
            mapper.run()

        assert len(points) == 1  # deduplicated to one

    def test_keeps_distinct_points_far_apart(self, qtbot: QtBot, tmp_path: Path) -> None:
        scanner = RasterScanner(region=(0, 0, 0, 0), step_px=100, dwell_ms=0)
        mapper = RoadMapper(scanner, RoadCursorDetector(), str(tmp_path / "roads.json"),
                            dedup_radius=10)

        points: list[ScanPoint] = []
        mapper.point_found.connect(points.append)

        # Two calls to _capture return cursors far apart
        screens = iter([
            _screenshot_with_cursor(30, 30),
            _screenshot_with_cursor(150, 150),
        ])
        with patch(_MOVE), patch.object(mapper, "_capture", side_effect=screens):
            # Give mapper two positions to scan
            scanner2 = RasterScanner(region=(0, 0, 10, 0), step_px=10, dwell_ms=0)
            mapper2 = RoadMapper(scanner2, RoadCursorDetector(), str(tmp_path / "r2.json"),
                                 dedup_radius=10)
            pts2: list[ScanPoint] = []
            mapper2.point_found.connect(pts2.append)
            screens2 = [_screenshot_with_cursor(30, 30), _screenshot_with_cursor(150, 150)]
            with patch(_MOVE), patch.object(mapper2, "_capture", side_effect=screens2):
                mapper2.run()
        assert len(pts2) == 2


class TestRoadMapperOutput:
    def test_writes_road_points_json_on_finish(self, qtbot: QtBot, tmp_path: Path) -> None:
        scanner = RasterScanner(region=(0, 0, 0, 0), step_px=100, dwell_ms=0)
        out = str(tmp_path / "roads.json")
        mapper = RoadMapper(scanner, RoadCursorDetector(), out)
        screen = _screenshot_with_cursor(100, 100)
        with patch(_MOVE), patch.object(mapper, "_capture", return_value=screen):
            mapper.run()
        assert Path(out).exists()

    def test_json_contains_points_key(self, qtbot: QtBot, tmp_path: Path) -> None:
        scanner = RasterScanner(region=(0, 0, 0, 0), step_px=100, dwell_ms=0)
        out = str(tmp_path / "roads.json")
        mapper = RoadMapper(scanner, RoadCursorDetector(), out)
        screen = _screenshot_with_cursor(100, 100)
        with patch(_MOVE), patch.object(mapper, "_capture", return_value=screen):
            mapper.run()
        data = json.loads(Path(out).read_text())
        assert "points" in data

    def test_json_point_has_correct_state(self, qtbot: QtBot, tmp_path: Path) -> None:
        scanner = RasterScanner(region=(0, 0, 0, 0), step_px=100, dwell_ms=0)
        out = str(tmp_path / "roads.json")
        mapper = RoadMapper(scanner, RoadCursorDetector(), out)
        screen = _screenshot_with_cursor(100, 100)
        with patch(_MOVE), patch.object(mapper, "_capture", return_value=screen):
            mapper.run()
        data = json.loads(Path(out).read_text())
        assert data["points"][0]["state"] == "unknown"

    def test_finished_signal_emits_total_count(self, qtbot: QtBot, tmp_path: Path) -> None:
        scanner = RasterScanner(region=(0, 0, 0, 0), step_px=100, dwell_ms=0)
        mapper = RoadMapper(scanner, RoadCursorDetector(), str(tmp_path / "r.json"))
        counts: list[int] = []
        mapper.finished.connect(counts.append)
        screen = _screenshot_with_cursor(100, 100)
        with patch(_MOVE), patch.object(mapper, "_capture", return_value=screen):
            mapper.run()
        assert counts == [1]


class TestRoadMapperStop:
    def test_stop_before_run_emits_finished(self, qtbot: QtBot, tmp_path: Path) -> None:
        scanner = RasterScanner(region=(0, 0, 500, 500), step_px=5, dwell_ms=0)
        mapper = RoadMapper(scanner, RoadCursorDetector(), str(tmp_path / "r.json"))
        mapper.stop()
        with patch(_MOVE), patch.object(mapper, "_capture", return_value=_blank_screenshot()):
            with qtbot.waitSignal(mapper.finished, timeout=1000):
                mapper.run()
