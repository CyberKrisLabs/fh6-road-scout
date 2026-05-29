"""Tests for the dark theme stylesheet."""

from PySide6.QtWidgets import QApplication

from app.ui.theme import STYLESHEET


class TestStylesheet:
    def test_stylesheet_is_non_empty(self) -> None:
        assert len(STYLESHEET.strip()) > 0

    def test_background_colour_defined(self) -> None:
        assert "#12121A" in STYLESHEET

    def test_accent_colour_defined(self) -> None:
        assert "#FF6B1A" in STYLESHEET

    def test_primary_btn_class_defined(self) -> None:
        assert "primary-btn" in STYLESHEET

    def test_accent_btn_class_defined(self) -> None:
        assert "accent-btn" in STYLESHEET

    def test_stat_card_class_defined(self) -> None:
        assert "stat-card" in STYLESHEET

    def test_section_label_class_defined(self) -> None:
        assert "section-label" in STYLESHEET

    def test_status_label_class_defined(self) -> None:
        assert "status-label" in STYLESHEET

    def test_separator_class_defined(self) -> None:
        assert "separator" in STYLESHEET

    def test_app_title_class_defined(self) -> None:
        assert "app-title" in STYLESHEET

    def test_progress_bar_chunk_defined(self) -> None:
        assert "QProgressBar" in STYLESHEET


class TestStylesheetApplied:
    def test_qapplication_has_stylesheet_after_apply(self, qtbot) -> None:
        app = QApplication.instance()
        assert app is not None
        app.setStyleSheet(STYLESHEET)
        assert len(app.styleSheet()) > 0
