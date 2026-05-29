"""Tests for Scanner: QThread loop, signals, stop, skip pre-scanned."""

from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from PySide6.QtCore import QPointF, QThread
from pytestqt.qtbot import QtBot

from app.core.calibrator import Calibrator
from app.core.scanner import Scanner
from app.models.scan_result import DiscoveryState, ScanPoint

# ── Helpers ───────────────────────────────────────────────────────────────────


def _fitted_calibrator() -> Calibrator:
    c = Calibrator()
    pts = [QPointF(float(i * 100), 0.0) for i in range(3)]
    c.fit(pts, pts)
    return c


def _make_points(n: int) -> list[ScanPoint]:
    return [ScanPoint(ref_x=i * 10, ref_y=0) for i in range(n)]


def _mock_mss_sct(screen_array: np.ndarray) -> MagicMock:
    """Return a mock mss context manager that yields a fake screenshot."""
    raw = MagicMock()
    raw.bgra = screen_array.tobytes()
    raw.height = screen_array.shape[0]
    raw.width = screen_array.shape[1]
    sct = MagicMock()
    sct.__enter__ = MagicMock(return_value=sct)
    sct.__exit__ = MagicMock(return_value=False)
    sct.monitors = [{}, {"width": screen_array.shape[1], "height": screen_array.shape[0]}]
    sct.grab = MagicMock(return_value=raw)
    return sct


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def black_screen() -> np.ndarray:
    """Small fake BGRA screen — no FT indicator."""
    return np.zeros((200, 400, 4), dtype=np.uint8)


@pytest.fixture
def scanner_factory(black_screen: np.ndarray):
    """Return a factory that creates a Scanner with all hardware mocked."""

    def _make(points: list[ScanPoint], hover_delay: float = 0.0) -> Scanner:
        cal = _fitted_calibrator()
        s = Scanner(points=points, calibrator=cal, hover_delay=hover_delay)
        return s

    return _make


# ── Scanner construction ──────────────────────────────────────────────────────


class TestScannerConstruction:
    def test_is_qobject(self, scanner_factory) -> None:
        from PySide6.QtCore import QObject

        s = scanner_factory(_make_points(1))
        assert isinstance(s, QObject)

    def test_has_required_signals(self, scanner_factory) -> None:
        s = scanner_factory(_make_points(1))
        assert hasattr(s, "point_scanned")
        assert hasattr(s, "progress")
        assert hasattr(s, "finished")


# ── Scanner run (fully mocked hardware) ──────────────────────────────────────


class TestScannerRun:
    def _run_scanner(
        self,
        scanner: Scanner,
        black_screen: np.ndarray,
        qtbot: QtBot,
    ) -> None:
        sct_mock = _mock_mss_sct(black_screen)
        with (
            patch("app.core.scanner.mss.mss", return_value=sct_mock),
            patch("app.core.scanner.pyautogui.moveTo"),
            patch("app.core.scanner.pyautogui.FAILSAFE", True),
            patch("app.core.scanner.time.sleep"),
        ):
            thread = QThread()
            scanner.moveToThread(thread)
            thread.started.connect(scanner.run)
            with qtbot.waitSignal(scanner.finished, timeout=5000):
                thread.start()
            thread.quit()
            thread.wait(2000)

    def test_finished_emitted_after_all_points(
        self, scanner_factory, black_screen: np.ndarray, qtbot: QtBot
    ) -> None:
        pts = _make_points(3)
        s = scanner_factory(pts)
        self._run_scanner(s, black_screen, qtbot)

    def test_point_scanned_emitted_for_each_point(
        self, scanner_factory, black_screen: np.ndarray, qtbot: QtBot
    ) -> None:
        pts = _make_points(3)
        s = scanner_factory(pts)
        emitted: list[ScanPoint] = []
        s.point_scanned.connect(emitted.append)
        self._run_scanner(s, black_screen, qtbot)
        assert len(emitted) == 3

    def test_all_points_get_non_unknown_state(
        self, scanner_factory, black_screen: np.ndarray, qtbot: QtBot
    ) -> None:
        pts = _make_points(3)
        s = scanner_factory(pts)
        self._run_scanner(s, black_screen, qtbot)
        assert all(p.state != DiscoveryState.UNKNOWN for p in pts)

    def test_pre_scanned_points_are_skipped(
        self, scanner_factory, black_screen: np.ndarray, qtbot: QtBot
    ) -> None:
        pts = _make_points(3)
        pts[1].state = DiscoveryState.DISCOVERED  # already scanned
        s = scanner_factory(pts)
        emitted: list[ScanPoint] = []
        s.point_scanned.connect(emitted.append)
        self._run_scanner(s, black_screen, qtbot)
        assert len(emitted) == 2  # only the 2 UNKNOWN points


class TestScannerStop:
    def test_stop_halts_before_all_points(
        self, scanner_factory, black_screen: np.ndarray, qtbot: QtBot
    ) -> None:
        pts = _make_points(20)
        s = scanner_factory(pts)
        emitted: list[ScanPoint] = []
        s.point_scanned.connect(emitted.append)

        sct_mock = _mock_mss_sct(black_screen)

        def _stop_after_first(_pt: ScanPoint) -> None:
            s.stop()

        s.point_scanned.connect(_stop_after_first)

        with (
            patch("app.core.scanner.mss.mss", return_value=sct_mock),
            patch("app.core.scanner.pyautogui.moveTo"),
            patch("app.core.scanner.pyautogui.FAILSAFE", True),
            patch("app.core.scanner.time.sleep"),
        ):
            thread = QThread()
            scanner_ref = s
            thread.started.connect(scanner_ref.run)
            scanner_ref.moveToThread(thread)
            with qtbot.waitSignal(scanner_ref.finished, timeout=5000):
                thread.start()
            thread.quit()
            thread.wait(2000)

        assert len(emitted) < 20
