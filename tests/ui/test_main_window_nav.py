"""Tests for MainWindow Next Gap navigation."""

import pytest
from pytestqt.qtbot import QtBot

from app.models.scan_result import DiscoveryState, ScanPoint, ScanSession
from app.ui.main_window import MainWindow


@pytest.fixture
def window(qtbot: QtBot) -> MainWindow:
    win = MainWindow()
    qtbot.addWidget(win)
    win.show()
    return win


def _session_with_gaps(n_undiscovered: int = 3) -> ScanSession:
    pts = []
    for i in range(n_undiscovered):
        pts.append(ScanPoint(ref_x=i * 50, ref_y=50, state=DiscoveryState.UNDISCOVERED))
    pts.append(ScanPoint(ref_x=200, ref_y=200, state=DiscoveryState.DISCOVERED))
    return ScanSession(points=pts)


class TestNextGapNavigation:
    def test_jump_visits_first_undiscovered_point(self, window: MainWindow) -> None:
        window._session = _session_with_gaps(3)
        jumped: list[ScanPoint] = []
        window._map_view.jump_to_point = lambda pt: jumped.append(pt)  # type: ignore[method-assign]
        window._on_jump_next()
        assert len(jumped) == 1
        assert jumped[0].state == DiscoveryState.UNDISCOVERED

    def test_jump_cycles_through_all_undiscovered(self, window: MainWindow) -> None:
        window._session = _session_with_gaps(3)
        visited: list[ScanPoint] = []
        window._map_view.jump_to_point = lambda pt: visited.append(pt)  # type: ignore[method-assign]
        for _ in range(3):
            window._on_jump_next()
        coords = [(p.ref_x, p.ref_y) for p in visited]
        assert len(set(coords)) == 3  # all 3 different points visited

    def test_jump_wraps_around_after_last(self, window: MainWindow) -> None:
        window._session = _session_with_gaps(2)
        visited: list[ScanPoint] = []
        window._map_view.jump_to_point = lambda pt: visited.append(pt)  # type: ignore[method-assign]
        window._on_jump_next()
        window._on_jump_next()
        window._on_jump_next()  # wrap-around
        assert visited[0].ref_x == visited[2].ref_x

    def test_jump_does_nothing_when_no_undiscovered(self, window: MainWindow) -> None:
        window._session = ScanSession(
            points=[
                ScanPoint(ref_x=10, ref_y=10, state=DiscoveryState.DISCOVERED),
            ]
        )
        jumped: list[ScanPoint] = []
        window._map_view.jump_to_point = lambda pt: jumped.append(pt)  # type: ignore[method-assign]
        window._on_jump_next()
        assert len(jumped) == 0

    def test_jump_does_nothing_with_empty_session(self, window: MainWindow) -> None:
        window._session = ScanSession()
        jumped: list[ScanPoint] = []
        window._map_view.jump_to_point = lambda pt: jumped.append(pt)  # type: ignore[method-assign]
        window._on_jump_next()
        assert len(jumped) == 0

    def test_new_undiscovered_points_included_in_cycle(self, window: MainWindow) -> None:
        window._session = _session_with_gaps(1)
        visited: list[ScanPoint] = []
        window._map_view.jump_to_point = lambda pt: visited.append(pt)  # type: ignore[method-assign]
        window._on_jump_next()
        # Add a second undiscovered point mid-cycle
        window._session.points.append(
            ScanPoint(ref_x=999, ref_y=999, state=DiscoveryState.UNDISCOVERED)
        )
        window._on_jump_next()
        coords = [p.ref_x for p in visited]
        assert 999 in coords
