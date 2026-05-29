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

from app.core.calibrator import Calibrator, load_calibration, save_calibration
from app.core.road_sampler import RoadSampler
from app.core.scanner import Scanner
from app.core.session_store import SessionStore
from app.models.scan_result import DiscoveryState, ScanPoint, ScanSession
from app.ui.map_view import MapView
from app.ui.scan_panel import ScanPanel
from app.utils.paths import asset

log = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Horizon Scout")
        self.resize(1280, 820)

        self._session = ScanSession()
        self._calibrator = Calibrator()
        self._scanner: Scanner | None = None
        self._scan_thread: QThread | None = None
        self._ref_map_path: str = ""
        self._next_gap_index: int = -1

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
        if not self._calibrator.is_fitted:
            QMessageBox.warning(
                self,
                "Not Calibrated",
                "Please calibrate before scanning.",
            )
            return

        ft_path = str(asset("ft_indicator.png")) if asset("ft_indicator.png").exists() else ""
        self._scanner = Scanner(
            points=self._session.points,
            calibrator=self._calibrator,
            ft_template_path=ft_path,
        )
        self._scan_thread = QThread()
        self._scanner.moveToThread(self._scan_thread)
        self._scanner.point_scanned.connect(self._on_point_scanned)
        self._scanner.progress.connect(self._on_scan_progress)
        self._scanner.finished.connect(self._on_scan_finished)
        self._scan_thread.started.connect(self._scanner.run)
        self._panel.set_scan_running(True)
        self._panel.set_status("Scanning...")
        self._scan_thread.start()
        log.info("Scan started with %d points", len(self._session.points))

    def _on_scan_pause(self) -> None:
        if self._scanner:
            self._scanner.pause()
            self._panel.set_status("Paused.")
            self._panel.set_scan_running(False, paused=True)

    def _on_scan_stop(self) -> None:
        if self._scanner:
            self._scanner.stop()
        self._panel.set_status("Stopped.")

    def _on_point_scanned(self, point: ScanPoint) -> None:
        self._map_view.update_point(point)

    def _on_scan_progress(self, scanned: int) -> None:
        s = self._session
        self._panel.update_progress(scanned, s.total, s.discovered, s.undiscovered)

    def _on_scan_finished(self) -> None:
        if self._scan_thread:
            self._scan_thread.quit()
            self._scan_thread.wait()
        self._panel.set_scan_running(False)
        s = self._session
        self._panel.set_status(f"Done - {s.undiscovered} undiscovered road(s) found.")
        self._panel.update_progress(s.scanned, s.total, s.discovered, s.undiscovered)
        log.info("Scan finished")

    def _on_jump_next(self) -> None:
        gaps = [p for p in self._session.points if p.state == DiscoveryState.UNDISCOVERED]
        if not gaps:
            return
        self._next_gap_index = (self._next_gap_index + 1) % len(gaps)
        self._map_view.jump_to_point(gaps[self._next_gap_index])

    def _on_export(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Highlighted Map", "result.png", "PNG (*.png)"
        )
        if not path:
            return
        from app.core.exporter import export_overlay

        try:
            export_overlay(self._ref_map_path, self._session.points, path)
            self._panel.set_status(f"Exported to {os.path.basename(path)}")
        except FileNotFoundError:
            QMessageBox.critical(self, "Export Error", "Reference map not loaded.")

    def _on_save(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Save Session", "session.json", "JSON (*.json)")
        if not path:
            return
        try:
            self._session.calibration_data = self._calibrator.to_dict()
            SessionStore.save(self._session, path)
            save_calibration(self._calibrator)
            self._panel.set_status(f"Session saved to {os.path.basename(path)}")
        except Exception as e:
            QMessageBox.critical(self, "Save Error", str(e))

    def _on_load_session(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Load Session", "", "JSON (*.json)")
        if not path:
            return
        try:
            self._session = SessionStore.load(path)
            load_calibration(self._calibrator)
            if self._session.reference_map_path and os.path.exists(
                self._session.reference_map_path
            ):
                self._map_view.load_image(self._session.reference_map_path)
                self._ref_map_path = self._session.reference_map_path
            self._map_view.set_points(self._session.points)
            self._panel.set_map_loaded(True)
            s = self._session
            self._panel.update_progress(s.scanned, s.total, s.discovered, s.undiscovered)
            self._panel.set_status("Session loaded.")
        except (FileNotFoundError, ValueError) as e:
            QMessageBox.critical(self, "Load Error", str(e))

    # ------------------------------------------------------------------

    def closeEvent(self, event: QCloseEvent) -> None:
        if self._scanner is not None:
            self._scanner.stop()
        if self._scan_thread and self._scan_thread.isRunning():
            self._scan_thread.quit()
            self._scan_thread.wait(2000)
        super().closeEvent(event)
