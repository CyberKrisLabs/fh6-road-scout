"""Configure application logging once at startup."""

import logging
import logging.handlers
import sys
from pathlib import Path


def setup_logging() -> None:
    """Set up console logging (dev) or rotating file logging (packaged exe)."""
    root = logging.getLogger()

    if getattr(sys, "frozen", False):
        log_dir = Path.home() / "AppData" / "Roaming" / "HorizonScout" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        handler: logging.Handler = logging.handlers.RotatingFileHandler(
            log_dir / "horizon_scout.log",
            maxBytes=1_000_000,
            backupCount=3,
            encoding="utf-8",
        )
        root.setLevel(logging.INFO)
    else:
        handler = logging.StreamHandler(sys.stdout)
        root.setLevel(logging.DEBUG)

    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)-8s %(name)s: %(message)s"))
    root.addHandler(handler)
