"""Left-side control panel: buttons, progress, stats, status bar."""

import logging

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)

log = logging.getLogger(__name__)


class ScanPanel(QWidget):
    """Left-side control panel."""

    calibrate_requested = Signal()
    capture_ft_template_requested = Signal()
    scan_start_requested = Signal()
    scan_pause_requested = Signal()
    scan_stop_requested = Signal()
    jump_next_requested = Signal()
    export_requested = Signal()
    save_requested = Signal()
    load_session_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedWidth(210)
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 14, 10, 14)
        root.setSpacing(8)

        title = QLabel("Horizon Scout")
        title.setProperty("class", "app-title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(title)

        sub = QLabel("FH6 Road Discovery")
        sub.setProperty("class", "app-subtitle")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(sub)

        root.addWidget(_hr())

        root.addWidget(_section_label("MAP"))
        self.btn_calibrate = _btn("Calibrate", primary=True)
        self.btn_calibrate.clicked.connect(self.calibrate_requested)
        root.addWidget(self.btn_calibrate)

        self.btn_capture_ft = _btn("Capture FT Template")
        self.btn_capture_ft.setToolTip("Capture the Fast Travel button from the in-game map")
        self.btn_capture_ft.clicked.connect(self.capture_ft_template_requested)
        root.addWidget(self.btn_capture_ft)

        root.addWidget(_hr())

        root.addWidget(_section_label("SCAN"))
        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)
        self.btn_start = _btn("Start", primary=True)
        self.btn_start.setEnabled(False)
        self.btn_start.clicked.connect(self.scan_start_requested)
        self.btn_pause = _btn("Pause")
        self.btn_pause.setEnabled(False)
        self.btn_pause.clicked.connect(self.scan_pause_requested)
        self.btn_stop = _btn("Stop")
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.scan_stop_requested)
        btn_row.addWidget(self.btn_start)
        btn_row.addWidget(self.btn_pause)
        btn_row.addWidget(self.btn_stop)
        root.addLayout(btn_row)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p%")
        root.addWidget(self.progress_bar)

        self.lbl_progress = QLabel("0 / 0 points")
        self.lbl_progress.setProperty("class", "small-label")
        self.lbl_progress.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(self.lbl_progress)

        root.addWidget(_hr())

        root.addWidget(_section_label("RESULTS"))
        stats_layout = QVBoxLayout()
        stats_layout.setSpacing(6)
        disc_card, self.lbl_discovered = _stat_widget("Discovered")
        undisc_card, self.lbl_undiscovered = _stat_widget("Undiscovered")
        total_card, self.lbl_total = _stat_widget("Total Points")
        stats_layout.addWidget(disc_card)
        stats_layout.addWidget(undisc_card)
        stats_layout.addWidget(total_card)
        root.addLayout(stats_layout)

        root.addWidget(_hr())

        root.addWidget(_section_label("NAVIGATE"))
        self.btn_jump = _btn("Next Gap", accent=True)
        self.btn_jump.setEnabled(False)
        self.btn_jump.clicked.connect(self.jump_next_requested)
        root.addWidget(self.btn_jump)

        root.addWidget(_hr())

        root.addWidget(_section_label("FILE"))
        self.btn_export = _btn("Export PNG")
        self.btn_export.setEnabled(False)
        self.btn_export.clicked.connect(self.export_requested)
        root.addWidget(self.btn_export)

        save_row = QHBoxLayout()
        save_row.setSpacing(6)
        self.btn_save = _btn("Save")
        self.btn_save.setEnabled(False)
        self.btn_save.clicked.connect(self.save_requested)
        self.btn_load_session = _btn("Load")
        self.btn_load_session.clicked.connect(self.load_session_requested)
        save_row.addWidget(self.btn_save)
        save_row.addWidget(self.btn_load_session)
        root.addLayout(save_row)

        root.addSpacerItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        )

        self.lbl_status = QLabel("Ready")
        self.lbl_status.setProperty("class", "status-label")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_status.setWordWrap(True)
        root.addWidget(self.lbl_status)

    # ------------------------------------------------------------------
    # Public update API
    # ------------------------------------------------------------------

    def set_status(self, text: str) -> None:
        self.lbl_status.setText(text)

    def set_road_points_ready(self, count: int) -> None:
        """Called once world_road_points.json is loaded successfully."""
        self.btn_start.setEnabled(True)
        self.set_status(f"Ready — {count:,} road points loaded.")

    def set_scan_running(self, running: bool, paused: bool = False) -> None:
        self.btn_start.setEnabled(not running)
        self.btn_pause.setEnabled(running)
        self.btn_stop.setEnabled(running or paused)
        self.btn_calibrate.setEnabled(not running)

    def update_progress(self, scanned: int, total: int, discovered: int, undiscovered: int) -> None:
        pct = int(scanned / total * 100) if total > 0 else 0
        self.progress_bar.setValue(pct)
        self.lbl_progress.setText(f"{scanned} / {total} points")
        self.lbl_discovered.setText(str(discovered))
        self.lbl_undiscovered.setText(str(undiscovered))
        self.lbl_total.setText(str(total))
        self.btn_jump.setEnabled(undiscovered > 0)
        self.btn_export.setEnabled(scanned > 0)
        self.btn_save.setEnabled(scanned > 0)


# ── helpers ──────────────────────────────────────────────────────────────────


def _section_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setProperty("class", "section-label")
    return lbl


def _stat_widget(title: str) -> tuple[QWidget, QLabel]:
    frame = QFrame()
    frame.setProperty("class", "stat-card")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(8, 6, 8, 6)
    layout.setSpacing(2)
    title_lbl = QLabel(title)
    title_lbl.setProperty("class", "stat-title")
    value_lbl = QLabel("—")
    value_lbl.setProperty("class", "stat-value")
    value_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout.addWidget(title_lbl)
    layout.addWidget(value_lbl)
    return frame, value_lbl


def _btn(text: str, primary: bool = False, accent: bool = False) -> QPushButton:
    b = QPushButton(text)
    if primary:
        b.setProperty("class", "primary-btn")
    elif accent:
        b.setProperty("class", "accent-btn")
    return b


def _hr() -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.Shape.HLine)
    line.setProperty("class", "separator")
    return line
