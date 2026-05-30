"""Tests for RasterScanner — grid mouse movement across a screen region."""

from unittest.mock import MagicMock, call, patch

import pytest
from PySide6.QtCore import QThread
from pytestqt.qtbot import QtBot

from app.core.raster_scanner import RasterScanner

# Patch target used throughout
_MOVE = "app.core.raster_scanner.pyautogui.moveTo"


class TestPositionGeneration:
    def test_3x3_grid_emits_nine_positions(self, qtbot: QtBot) -> None:
        scanner = RasterScanner(region=(100, 100, 60, 60), step_px=30, dwell_ms=0)
        positions: list[tuple[int, int]] = []
        scanner.position_ready.connect(lambda x, y: positions.append((x, y)))
        with patch(_MOVE):
            scanner.run()
        assert len(positions) == 9

    def test_correct_column_and_row_values(self, qtbot: QtBot) -> None:
        scanner = RasterScanner(region=(10, 20, 40, 60), step_px=20, dwell_ms=0)
        positions: list[tuple[int, int]] = []
        scanner.position_ready.connect(lambda x, y: positions.append((x, y)))
        with patch(_MOVE):
            scanner.run()
        xs = sorted({p[0] for p in positions})
        ys = sorted({p[1] for p in positions})
        assert xs == [10, 30, 50]   # 10, 10+20, 10+40
        assert ys == [20, 40, 60, 80]  # 20, 20+20, 20+40, 20+60

    def test_total_positions_matches_emitted_count(self, qtbot: QtBot) -> None:
        scanner = RasterScanner(region=(0, 0, 100, 80), step_px=25, dwell_ms=0)
        positions: list[tuple[int, int]] = []
        scanner.position_ready.connect(lambda x, y: positions.append((x, y)))
        with patch(_MOVE):
            scanner.run()
        assert len(positions) == scanner.total_positions

    def test_top_to_bottom_within_each_column(self, qtbot: QtBot) -> None:
        scanner = RasterScanner(region=(0, 0, 20, 60), step_px=20, dwell_ms=0)
        positions: list[tuple[int, int]] = []
        scanner.position_ready.connect(lambda x, y: positions.append((x, y)))
        with patch(_MOVE):
            scanner.run()
        # First column (x=0): should emit y values in ascending order
        col0 = [y for x, y in positions if x == 0]
        assert col0 == sorted(col0)

    def test_moves_mouse_to_each_position(self) -> None:
        scanner = RasterScanner(region=(50, 60, 40, 40), step_px=20, dwell_ms=0)
        mock_move = MagicMock()
        with patch(_MOVE, mock_move):
            scanner.run()
        expected = [call(50, 60), call(50, 80), call(50, 100),
                    call(70, 60), call(70, 80), call(70, 100),
                    call(90, 60), call(90, 80), call(90, 100)]
        mock_move.assert_has_calls(expected, any_order=False)


class TestProgressSignal:
    def test_progress_emits_current_and_total(self, qtbot: QtBot) -> None:
        scanner = RasterScanner(region=(0, 0, 20, 20), step_px=10, dwell_ms=0)
        progress_values: list[tuple[int, int]] = []
        scanner.progress.connect(lambda cur, tot: progress_values.append((cur, tot)))
        with patch(_MOVE):
            scanner.run()
        totals = {t for _, t in progress_values}
        assert totals == {scanner.total_positions}
        currents = [c for c, _ in progress_values]
        assert currents == list(range(1, scanner.total_positions + 1))

    def test_finished_emitted_after_all_positions(self, qtbot: QtBot) -> None:
        scanner = RasterScanner(region=(0, 0, 10, 10), step_px=5, dwell_ms=0)
        order: list[str] = []
        scanner.position_ready.connect(lambda x, y: order.append("pos"))
        scanner.finished.connect(lambda: order.append("done"))
        with patch(_MOVE):
            scanner.run()
        assert order[-1] == "done"
        assert order.count("pos") == scanner.total_positions


class TestTotalPositions:
    def test_1x1_region_gives_one_position(self) -> None:
        s = RasterScanner(region=(0, 0, 0, 0), step_px=10, dwell_ms=0)
        assert s.total_positions == 1

    def test_step_larger_than_region(self) -> None:
        s = RasterScanner(region=(0, 0, 5, 5), step_px=20, dwell_ms=0)
        assert s.total_positions == 1

    def test_exact_multiple_steps(self) -> None:
        s = RasterScanner(region=(0, 0, 40, 60), step_px=20, dwell_ms=0)
        assert s.total_positions == 3 * 4  # (0,20,40) × (0,20,40,60)


class TestStopAndPause:
    def test_stop_before_start_emits_finished_immediately(self, qtbot: QtBot) -> None:
        scanner = RasterScanner(region=(0, 0, 1000, 1000), step_px=5, dwell_ms=0)
        scanner.stop()
        with patch(_MOVE):
            with qtbot.waitSignal(scanner.finished, timeout=1000):
                scanner.run()

    def test_stop_during_scan_halts_early(self, qtbot: QtBot) -> None:
        scanner = RasterScanner(region=(0, 0, 500, 500), step_px=2, dwell_ms=0)
        positions: list[tuple[int, int]] = []

        def on_pos(x: int, y: int) -> None:
            positions.append((x, y))
            if len(positions) >= 10:
                scanner.stop()

        scanner.position_ready.connect(on_pos)
        thread = QThread()
        scanner.moveToThread(thread)
        thread.started.connect(scanner.run)
        with patch(_MOVE):
            with qtbot.waitSignal(scanner.finished, timeout=3000):
                thread.start()
        thread.quit()
        thread.wait(1000)
        assert len(positions) < scanner.total_positions

    def test_pause_then_resume_completes_scan(self, qtbot: QtBot) -> None:
        scanner = RasterScanner(region=(0, 0, 20, 20), step_px=10, dwell_ms=0)
        scanner.pause()
        positions: list[tuple[int, int]] = []
        scanner.position_ready.connect(lambda x, y: positions.append((x, y)))

        thread = QThread()
        scanner.moveToThread(thread)
        thread.started.connect(scanner.run)
        with patch(_MOVE):
            thread.start()
            # Give the thread a moment to reach the pause point
            import time; time.sleep(0.05)
            scanner.resume()
            with qtbot.waitSignal(scanner.finished, timeout=2000):
                pass
        thread.quit()
        thread.wait(1000)
        assert len(positions) == scanner.total_positions
