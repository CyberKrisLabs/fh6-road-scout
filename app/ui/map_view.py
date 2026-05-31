"""Zoomable, pannable map canvas with scan-point and calibration overlays."""

import logging

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import (
    QBrush,
    QColor,
    QMouseEvent,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QWheelEvent,
)
from PySide6.QtWidgets import QSizePolicy, QWidget

from app.models.scan_result import DiscoveryState, RoadType, ScanPoint

log = logging.getLogger(__name__)

_DOT_R = 4

# Colors when a point has been scanned
_DISCOVERED_COLOR = QColor(80, 220, 100, 200)
_UNDISCOVERED_COLOR = QColor(255, 80, 50, 220)

# Colors when a point is still UNKNOWN — show by road type (matches in-game overlay)
_ROAD_TYPE_COLOR: dict[RoadType, QColor] = {
    RoadType.ASPHALT: QColor(240, 240, 255, 170),  # white
    RoadType.TUNNEL: QColor(180, 185, 200, 140),  # grey-white (subtle dots in-game)
    RoadType.DIRT: QColor(255, 150, 30, 190),  # orange solid
    RoadType.OFFROAD: QColor(255, 175, 70, 160),  # orange dashed (lighter)
    RoadType.ALLEYWAY: QColor(80, 220, 220, 170),  # cyan dashed
}

_CALIB_COLOR = QColor(255, 200, 0, 255)


class MapView(QWidget):
    """Zoomable, pannable map canvas that overlays scan results."""

    calibration_click = Signal(QPointF)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMouseTracking(True)

        self._pixmap: QPixmap | None = None
        self._display_pixmap: QPixmap | None = None  # reduced-res for fast rendering
        self._display_scale: float = 1.0  # full_px * _display_scale = display_px
        self._points: list[ScanPoint] = []
        self._calib_points: list[QPointF] = []
        self._calib_mode: bool = False

        self._scale: float = 1.0
        self._offset: QPointF = QPointF(0.0, 0.0)
        self._pan_origin: QPointF | None = None
        self._pan_offset_origin: QPointF | None = None

        self.setMinimumSize(400, 400)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    _MAX_DISPLAY_PX = 1920  # max dimension of the display pixmap

    def load_builtin_map(self) -> None:
        """Load the pre-generated road_map.png bundled with the application."""
        from app.utils.paths import asset

        path = asset("road_map.png")
        if not self.load_image(str(path)):
            log.warning("Built-in road_map.png not found at %s", path)

    def load_image(self, path: str) -> bool:
        img = QPixmap(path)
        if img.isNull():
            return False
        self._pixmap = img
        # Build a reduced-res display pixmap so paintEvent scales fewer pixels
        max_dim = max(img.width(), img.height())
        if max_dim > self._MAX_DISPLAY_PX:
            self._display_scale = self._MAX_DISPLAY_PX / max_dim
            self._display_pixmap = img.scaled(
                int(img.width() * self._display_scale),
                int(img.height() * self._display_scale),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        else:
            self._display_pixmap = img
            self._display_scale = 1.0
        self._fit_to_view()
        self.update()
        log.debug("Loaded map image: %s (display scale %.2f)", path, self._display_scale)
        return True

    def set_points(self, points: list[ScanPoint]) -> None:
        self._points = points
        self.update()

    def update_point(self, point: ScanPoint) -> None:
        self.update()

    def set_calibration_mode(self, active: bool) -> None:
        self._calib_mode = active
        cursor = Qt.CursorShape.CrossCursor if active else Qt.CursorShape.ArrowCursor
        self.setCursor(cursor)
        self.update()

    def set_calibration_points(self, points: list[QPointF]) -> None:
        self._calib_points = points
        self.update()

    def jump_to_point(self, point: ScanPoint) -> None:
        if self._pixmap is None:
            return
        center = self._img_to_widget(QPointF(point.ref_x, point.ref_y))
        w_center = QPointF(self.width() / 2.0, self.height() / 2.0)
        self._offset += w_center - center
        self.update()

    # ------------------------------------------------------------------
    # Transform helpers
    # ------------------------------------------------------------------

    def _fit_to_view(self) -> None:
        if self._pixmap is None:
            return
        sw = self.width() / self._pixmap.width()
        sh = self.height() / self._pixmap.height()
        self._scale = min(sw, sh) * 0.95
        self._offset = QPointF(
            (self.width() - self._pixmap.width() * self._scale) / 2.0,
            (self.height() - self._pixmap.height() * self._scale) / 2.0,
        )

    def _img_to_widget(self, pt: QPointF) -> QPointF:
        return QPointF(
            pt.x() * self._scale + self._offset.x(),
            pt.y() * self._scale + self._offset.y(),
        )

    def _widget_to_img(self, pt: QPointF) -> QPointF:
        return QPointF(
            (pt.x() - self._offset.x()) / self._scale,
            (pt.y() - self._offset.y()) / self._scale,
        )

    # ------------------------------------------------------------------
    # Qt events
    # ------------------------------------------------------------------

    def resizeEvent(self, event: object) -> None:
        if self._pixmap and self._scale == 1.0:
            self._fit_to_view()
        super().resizeEvent(event)  # type: ignore[arg-type]

    def wheelEvent(self, event: QWheelEvent) -> None:
        delta = event.angleDelta().y()
        factor = 1.15 if delta > 0 else 1.0 / 1.15
        cursor = QPointF(event.position())
        self._offset = cursor + (self._offset - cursor) * factor
        self._scale *= factor
        self._scale = max(0.05, min(50.0, self._scale))
        self.update()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            if self._calib_mode:
                img_pt = self._widget_to_img(QPointF(event.position()))
                self.calibration_click.emit(img_pt)
            else:
                self._pan_origin = QPointF(event.position())
                self._pan_offset_origin = QPointF(self._offset)
                self.setCursor(Qt.CursorShape.ClosedHandCursor)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._pan_origin is not None and not self._calib_mode:
            delta = QPointF(event.position() - self._pan_origin)
            if self._pan_offset_origin is not None:
                self._offset = self._pan_offset_origin + delta
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton and not self._calib_mode:
            self._pan_origin = None
            self._pan_offset_origin = None
            self.setCursor(Qt.CursorShape.ArrowCursor)

    def paintEvent(self, event: object) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(18, 18, 24))

        if self._pixmap is None:
            painter.setPen(QColor(100, 100, 120))
            painter.drawText(
                self.rect(),
                Qt.AlignmentFlag.AlignCenter,
                "Load a reference map to begin",
            )
            return

        # Render only the visible slice using the reduced-res display pixmap
        disp = self._display_pixmap
        ds = self._display_scale
        visible_img = QRectF(
            -self._offset.x() / self._scale,
            -self._offset.y() / self._scale,
            self.width() / self._scale,
            self.height() / self._scale,
        )
        img_bounds = QRectF(0.0, 0.0, float(self._pixmap.width()), float(self._pixmap.height()))
        src_full = visible_img.intersected(img_bounds)
        if not src_full.isEmpty() and disp is not None:
            tgt = QRectF(
                src_full.x() * self._scale + self._offset.x(),
                src_full.y() * self._scale + self._offset.y(),
                src_full.width() * self._scale,
                src_full.height() * self._scale,
            )
            src_disp = QRectF(
                src_full.x() * ds,
                src_full.y() * ds,
                src_full.width() * ds,
                src_full.height() * ds,
            )
            painter.drawPixmap(tgt, disp, src_disp)

        # Batch scan-point dots by colour to minimise painter state changes.
        # Cull in image space first (cheap) before converting to widget coords.
        r = float(max(2, int(_DOT_R * min(self._scale, 2.0))))
        visible_img_l = -self._offset.x() / self._scale
        visible_img_t = -self._offset.y() / self._scale
        visible_img_r = visible_img_l + self.width() / self._scale
        visible_img_b = visible_img_t + self.height() / self._scale
        # Group dots by colour; QColor isn't hashable so key by rgba() int.
        color_paths: dict[int, tuple[QColor, QPainterPath]] = {}
        for pt in self._points:
            if not (
                visible_img_l <= pt.ref_x <= visible_img_r
                and visible_img_t <= pt.ref_y <= visible_img_b
            ):
                continue
            if pt.state == DiscoveryState.DISCOVERED:
                color = _DISCOVERED_COLOR
            elif pt.state == DiscoveryState.UNDISCOVERED:
                color = _UNDISCOVERED_COLOR
            else:
                color = _ROAD_TYPE_COLOR[pt.road_type]
            w_pt = self._img_to_widget(QPointF(pt.ref_x, pt.ref_y))
            key = color.rgba()
            entry = color_paths.get(key)
            if entry is None:
                entry = (color, QPainterPath())
                color_paths[key] = entry
            entry[1].addEllipse(w_pt, r, r)
        painter.setPen(Qt.PenStyle.NoPen)
        for color, path in color_paths.values():
            painter.setBrush(QBrush(color))
            painter.drawPath(path)

        for i, cp in enumerate(self._calib_points):
            w_pt = self._img_to_widget(cp)
            painter.setPen(QPen(_CALIB_COLOR, 2))
            painter.setBrush(QBrush(_CALIB_COLOR.lighter(150)))
            painter.drawEllipse(w_pt, 7, 7)
            painter.setPen(QPen(QColor(0, 0, 0), 1))
            painter.drawText(
                QRectF(w_pt.x() - 10, w_pt.y() - 10, 20, 20),
                Qt.AlignmentFlag.AlignCenter,
                str(i + 1),
            )
