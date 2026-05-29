"""MainWindow: wires ScanPanel and MapView, owns the session and scanner thread."""

import logging
import os

from PySide6.QtCore import Qt, QThread
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QWidget,
)

from app.core.road_sampler import RoadSampler
from app.models.scan_result import ScanSession
from app.ui.map_view import MapView
from app.ui.scan_panel import ScanPanel

log = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Horizon Scout")
        self.resize(1280, 820)

        self._session = ScanSession()
        self._scanner: object | None = None
        self._scan_thread: QThread | None = None
        self._ref_map_path: str = ""

        self._build_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._panel = ScanPanel()
        self._map_view = MapView()

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self._panel)
        splitter.addWidget(self._map_view)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([210, 1070])
        layout.addWidget(splitter)

        self._panel.load_map_requested.connect(self._on_load_map)
        self._panel.calibrate_requested.connect(self._on_calibrate)
        self._panel.scan_start_requested.connect(self._on_scan_start)
        self._panel.scan_pause_requested.connect(self._on_scan_pause)
        self._panel.scan_stop_requested.connect(self._on_scan_stop)
        self._panel.jump_next_requested.connect(self._on_jump_next)
        self._panel.export_requested.connect(self._on_export)
        self._panel.save_requested.connect(self._on_save)
        self._panel.load_session_requested.connect(self._on_load_session)

    # ------------------------------------------------------------------
    # Public helper (also used by tests to bypass the file dialog)
    # ------------------------------------------------------------------

    def _load_map(self, path: str) -> None:
        if not self._map_view.load_image(path):
            QMessageBox.critical(self, "Error", "Could not load the image.")
            return
        self._ref_map_path = path
        self._panel.set_status(f"Sampling: {os.path.basename(path)}")

        sampler = RoadSampler()
        points = sampler.sample(path)
        self._session = ScanSession(points=points, reference_map_path=path)
        self._map_view.set_points(points)
        self._panel.set_map_loaded(True)
        self._panel.update_progress(0, len(points), 0, 0)
        self._panel.set_status(f"Ready — {len(points)} road points sampled.")
        log.info("Loaded map: %s (%d points)", path, len(points))

    # ------------------------------------------------------------------
    # Slot handlers
    # ------------------------------------------------------------------

    def _on_load_map(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Load Reference Map", "", "Images (*.png *.jpg *.jpeg *.bmp)"
        )
        if path:
            self._load_map(path)

    def _on_calibrate(self) -> None:
        pass  # implemented in P3

    def _on_scan_start(self) -> None:
        pass  # implemented in P4

    def _on_scan_pause(self) -> None:
        pass  # implemented in P4

    def _on_scan_stop(self) -> None:
        pass  # implemented in P4

    def _on_jump_next(self) -> None:
        pass  # implemented in P5

    def _on_export(self) -> None:
        pass  # implemented in P5

    def _on_save(self) -> None:
        pass  # implemented in P5

    def _on_load_session(self) -> None:
        pass  # implemented in P5

    # ------------------------------------------------------------------

    def closeEvent(self, event: QCloseEvent) -> None:
        if self._scanner is not None and hasattr(self._scanner, "stop"):
            self._scanner.stop()
        if self._scan_thread and self._scan_thread.isRunning():
            self._scan_thread.quit()
            self._scan_thread.wait(2000)
        super().closeEvent(event)
