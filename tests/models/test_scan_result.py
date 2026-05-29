"""Tests for ScanPoint, ScanSession, and DiscoveryState data models."""

import pytest

from app.models.scan_result import DiscoveryState, ScanPoint, ScanSession


class TestDiscoveryState:
    def test_has_required_variants(self) -> None:
        assert DiscoveryState.UNKNOWN
        assert DiscoveryState.DISCOVERED
        assert DiscoveryState.UNDISCOVERED

    def test_string_values(self) -> None:
        assert DiscoveryState.UNKNOWN.value == "unknown"
        assert DiscoveryState.DISCOVERED.value == "discovered"
        assert DiscoveryState.UNDISCOVERED.value == "undiscovered"


class TestScanPoint:
    def test_stores_coordinates(self) -> None:
        pt = ScanPoint(ref_x=10, ref_y=20)
        assert pt.ref_x == 10
        assert pt.ref_y == 20

    def test_default_state_is_unknown(self) -> None:
        pt = ScanPoint(ref_x=0, ref_y=0)
        assert pt.state == DiscoveryState.UNKNOWN

    def test_default_confidence_is_zero(self) -> None:
        pt = ScanPoint(ref_x=0, ref_y=0)
        assert pt.confidence == 0.0

    def test_state_can_be_set(self) -> None:
        pt = ScanPoint(ref_x=1, ref_y=2, state=DiscoveryState.DISCOVERED, confidence=0.9)
        assert pt.state == DiscoveryState.DISCOVERED
        assert pt.confidence == 0.9


class TestScanSessionEmpty:
    def test_total_is_zero(self) -> None:
        session = ScanSession()
        assert session.total == 0

    def test_scanned_is_zero(self) -> None:
        assert ScanSession().scanned == 0

    def test_discovered_is_zero(self) -> None:
        assert ScanSession().discovered == 0

    def test_undiscovered_is_zero(self) -> None:
        assert ScanSession().undiscovered == 0


class TestScanSessionProperties:
    @pytest.fixture
    def mixed_session(self) -> ScanSession:
        return ScanSession(
            points=[
                ScanPoint(ref_x=0, ref_y=0, state=DiscoveryState.UNKNOWN),
                ScanPoint(ref_x=1, ref_y=0, state=DiscoveryState.DISCOVERED),
                ScanPoint(ref_x=2, ref_y=0, state=DiscoveryState.DISCOVERED),
                ScanPoint(ref_x=3, ref_y=0, state=DiscoveryState.UNDISCOVERED),
            ]
        )

    def test_total_equals_len(self, mixed_session: ScanSession) -> None:
        assert mixed_session.total == 4

    def test_scanned_excludes_unknown(self, mixed_session: ScanSession) -> None:
        assert mixed_session.scanned == 3

    def test_discovered_count(self, mixed_session: ScanSession) -> None:
        assert mixed_session.discovered == 2

    def test_undiscovered_count(self, mixed_session: ScanSession) -> None:
        assert mixed_session.undiscovered == 1


class TestScanSessionAllSameState:
    def test_all_unknown(self) -> None:
        s = ScanSession(points=[ScanPoint(ref_x=i, ref_y=0) for i in range(5)])
        assert s.total == 5
        assert s.scanned == 0
        assert s.discovered == 0
        assert s.undiscovered == 0

    def test_all_discovered(self) -> None:
        s = ScanSession(
            points=[ScanPoint(ref_x=i, ref_y=0, state=DiscoveryState.DISCOVERED) for i in range(3)]
        )
        assert s.scanned == 3
        assert s.discovered == 3
        assert s.undiscovered == 0

    def test_all_undiscovered(self) -> None:
        s = ScanSession(
            points=[
                ScanPoint(ref_x=i, ref_y=0, state=DiscoveryState.UNDISCOVERED) for i in range(3)
            ]
        )
        assert s.scanned == 3
        assert s.discovered == 0
        assert s.undiscovered == 3


class TestScanSessionDefaults:
    def test_reference_map_path_defaults_empty(self) -> None:
        assert ScanSession().reference_map_path == ""

    def test_calibration_data_defaults_empty_dict(self) -> None:
        assert ScanSession().calibration_data == {}

    def test_points_list_not_shared_between_instances(self) -> None:
        a = ScanSession()
        b = ScanSession()
        a.points.append(ScanPoint(ref_x=0, ref_y=0))
        assert len(b.points) == 0
