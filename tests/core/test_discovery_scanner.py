"""Tests for DiscoveryScanner — scan road points and mark discovered/undiscovered."""

from unittest.mock import patch

import cv2
import numpy as np
from pytestqt.qtbot import QtBot

from app.core.discovery_scanner import DiscoveryScanner
from app.core.fast_travel_detector import FastTravelDetector
from app.models.scan_result import DiscoveryState, ScanPoint

_MOVE = "app.core.discovery_scanner.pyautogui.moveTo"
_TEMPLATE = "assets/ft_samples/ft_button_template.png"


def _blank() -> np.ndarray:
    return np.full((600, 800, 3), (40, 80, 40), dtype=np.uint8)


def _with_ft(ft_detector: FastTravelDetector) -> np.ndarray:
    """Screenshot with the FT indicator embedded at a known position."""
    canvas = _blank()
    template_img = cv2.imread("assets/ft_samples/ft_indicator_01_light_grey.png")
    if template_img is not None:
        h, w = template_img.shape[:2]
        canvas[10: 10 + h, 10: 10 + w] = template_img
    return canvas


def _make_points(n: int = 3) -> list[ScanPoint]:
    return [ScanPoint(ref_x=i * 100, ref_y=50) for i in range(n)]


class TestDiscoveryScannerBasic:
    def test_emits_point_scanned_for_each_point(self, qtbot: QtBot) -> None:
        ft = FastTravelDetector()
        ft.load_template(_TEMPLATE)
        scanner = DiscoveryScanner(_make_points(3), ft, dwell_ms=0)
        scanned: list[ScanPoint] = []
        scanner.point_scanned.connect(scanned.append)
        with patch(_MOVE), patch.object(scanner, "_capture", return_value=_blank()):
            scanner.run()
        assert len(scanned) == 3

    def test_marks_undiscovered_when_ft_absent(self, qtbot: QtBot) -> None:
        ft = FastTravelDetector()
        ft.load_template(_TEMPLATE)
        scanner = DiscoveryScanner(_make_points(2), ft, dwell_ms=0)
        scanned: list[ScanPoint] = []
        scanner.point_scanned.connect(scanned.append)
        # Blank screenshot → no FT indicator
        with patch(_MOVE), patch.object(scanner, "_capture", return_value=_blank()):
            scanner.run()
        assert all(p.state == DiscoveryState.UNDISCOVERED for p in scanned)

    def test_marks_discovered_when_ft_present(self, qtbot: QtBot) -> None:
        ft = FastTravelDetector()
        ft.load_template(_TEMPLATE)
        canvas = _with_ft(ft)
        scanner = DiscoveryScanner(_make_points(1), ft, dwell_ms=0)
        scanned: list[ScanPoint] = []
        scanner.point_scanned.connect(scanned.append)
        with patch(_MOVE), patch.object(scanner, "_capture", return_value=canvas):
            scanner.run()
        assert scanned[0].state == DiscoveryState.DISCOVERED

    def test_progress_signal_fires_for_each_point(self, qtbot: QtBot) -> None:
        ft = FastTravelDetector()
        scanner = DiscoveryScanner(_make_points(4), ft, dwell_ms=0)
        progress: list[tuple[int, int]] = []
        scanner.progress.connect(lambda c, t: progress.append((c, t)))
        with patch(_MOVE), patch.object(scanner, "_capture", return_value=_blank()):
            scanner.run()
        assert len(progress) == 4
        assert [c for c, _ in progress] == [1, 2, 3, 4]
        assert all(t == 4 for _, t in progress)

    def test_finished_emitted_after_all_points(self, qtbot: QtBot) -> None:
        ft = FastTravelDetector()
        scanner = DiscoveryScanner(_make_points(2), ft, dwell_ms=0)
        done: list[bool] = []
        scanner.finished.connect(lambda: done.append(True))
        with patch(_MOVE), patch.object(scanner, "_capture", return_value=_blank()):
            scanner.run()
        assert done == [True]

    def test_empty_point_list_emits_finished(self, qtbot: QtBot) -> None:
        ft = FastTravelDetector()
        scanner = DiscoveryScanner([], ft, dwell_ms=0)
        done: list[bool] = []
        scanner.finished.connect(lambda: done.append(True))
        with patch(_MOVE), patch.object(scanner, "_capture", return_value=_blank()):
            scanner.run()
        assert done == [True]


class TestDiscoveryScannerStopResume:
    def test_stop_before_run_emits_finished_immediately(self, qtbot: QtBot) -> None:
        ft = FastTravelDetector()
        scanner = DiscoveryScanner(_make_points(10), ft, dwell_ms=0)
        scanner.stop()
        with patch(_MOVE), patch.object(scanner, "_capture", return_value=_blank()), qtbot.waitSignal(scanner.finished, timeout=1000):
            scanner.run()

    def test_skips_already_scanned_points(self, qtbot: QtBot) -> None:
        pts = _make_points(3)
        pts[0].state = DiscoveryState.DISCOVERED  # already scanned
        ft = FastTravelDetector()
        scanner = DiscoveryScanner(pts, ft, dwell_ms=0)
        scanned: list[ScanPoint] = []
        scanner.point_scanned.connect(scanned.append)
        with patch(_MOVE), patch.object(scanner, "_capture", return_value=_blank()):
            scanner.run()
        # Only unscanned (UNKNOWN) points should be re-scanned
        assert len(scanned) == 2
