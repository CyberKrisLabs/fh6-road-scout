"""Tests for export_overlay(): annotated PNG output."""

from pathlib import Path

import cv2
import numpy as np
import pytest

from app.core.exporter import export_overlay
from app.models.scan_result import DiscoveryState, ScanPoint


@pytest.fixture
def ref_image_path(tmp_path: Path) -> str:
    """200x200 black reference image."""
    img = np.zeros((200, 200, 3), dtype=np.uint8)
    path = str(tmp_path / "ref.png")
    cv2.imwrite(path, img)
    return path


@pytest.fixture
def output_path(tmp_path: Path) -> str:
    return str(tmp_path / "output.png")


class TestExportOverlay:
    def test_raises_for_missing_reference_image(self, output_path: str) -> None:
        with pytest.raises(FileNotFoundError):
            export_overlay("nonexistent.png", [], output_path)

    def test_output_file_is_created(self, ref_image_path: str, output_path: str) -> None:
        export_overlay(ref_image_path, [], output_path)
        assert Path(output_path).exists()

    def test_output_dimensions_match_input(self, ref_image_path: str, output_path: str) -> None:
        ref = cv2.imread(ref_image_path)
        export_overlay(ref_image_path, [], output_path)
        out = cv2.imread(output_path)
        assert out.shape == ref.shape

    def test_discovered_point_produces_green_pixel(
        self, ref_image_path: str, output_path: str
    ) -> None:
        pts = [ScanPoint(ref_x=100, ref_y=100, state=DiscoveryState.DISCOVERED)]
        export_overlay(ref_image_path, pts, output_path)
        out = cv2.imread(output_path)
        # Sample a few pixels near the dot centre; at least one must be greenish
        region = out[94:107, 94:107]
        has_green = np.any((region[:, :, 1] > 100) & (region[:, :, 1] > region[:, :, 2]))
        assert has_green

    def test_undiscovered_point_produces_red_pixel(
        self, ref_image_path: str, output_path: str
    ) -> None:
        pts = [ScanPoint(ref_x=100, ref_y=100, state=DiscoveryState.UNDISCOVERED)]
        export_overlay(ref_image_path, pts, output_path)
        out = cv2.imread(output_path)
        region = out[94:107, 94:107]
        has_red = np.any((region[:, :, 2] > 100) & (region[:, :, 2] > region[:, :, 1]))
        assert has_red

    def test_unknown_points_not_rendered(self, ref_image_path: str, output_path: str) -> None:
        pts = [ScanPoint(ref_x=100, ref_y=100, state=DiscoveryState.UNKNOWN)]
        export_overlay(ref_image_path, pts, output_path)
        out = cv2.imread(output_path)
        # The pixel at the point location should be near-black (background)
        b, g, r = out[100, 100]
        assert int(b) + int(g) + int(r) < 60

    def test_empty_points_list_produces_output(self, ref_image_path: str, output_path: str) -> None:
        export_overlay(ref_image_path, [], output_path)
        assert Path(output_path).exists()

    def test_multiple_points_all_rendered(self, ref_image_path: str, output_path: str) -> None:
        pts = [
            ScanPoint(ref_x=40, ref_y=40, state=DiscoveryState.DISCOVERED),
            ScanPoint(ref_x=160, ref_y=160, state=DiscoveryState.UNDISCOVERED),
        ]
        export_overlay(ref_image_path, pts, output_path)
        out = cv2.imread(output_path)
        # Green near (40,40)
        r1 = out[34:47, 34:47]
        assert np.any((r1[:, :, 1] > 80) & (r1[:, :, 1] > r1[:, :, 2]))
        # Red near (160,160)
        r2 = out[154:167, 154:167]
        assert np.any((r2[:, :, 2] > 80) & (r2[:, :, 2] > r2[:, :, 1]))
