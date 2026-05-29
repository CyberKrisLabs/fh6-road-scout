"""Persist and restore scan sessions as JSON files."""

import json
import logging
from pathlib import Path
from typing import Any

from app.models.scan_result import DiscoveryState, ScanPoint, ScanSession

log = logging.getLogger(__name__)


class SessionStore:
    @staticmethod
    def save(session: ScanSession, path: str) -> None:
        """Serialise a ScanSession to a JSON file."""
        data: dict[str, Any] = {
            "reference_map_path": session.reference_map_path,
            "calibration": session.calibration_data,
            "points": [
                {
                    "x": p.ref_x,
                    "y": p.ref_y,
                    "state": p.state.value,
                    "conf": p.confidence,
                }
                for p in session.points
            ],
        }
        Path(path).write_text(json.dumps(data, indent=2), encoding="utf-8")
        log.info("Session saved to %s (%d points)", path, len(session.points))

    @staticmethod
    def load(path: str) -> ScanSession:
        """Deserialise a ScanSession from a JSON file."""
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Session file not found: {path}")
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid session JSON in {path}: {e}") from e

        points = [
            ScanPoint(
                ref_x=pt["x"],
                ref_y=pt["y"],
                state=DiscoveryState(pt["state"]),
                confidence=pt.get("conf", 0.0),
            )
            for pt in data.get("points", [])
        ]
        session = ScanSession(
            points=points,
            reference_map_path=data.get("reference_map_path", ""),
            calibration_data=data.get("calibration", {}),
        )
        log.info("Session loaded from %s (%d points)", path, len(points))
        return session
