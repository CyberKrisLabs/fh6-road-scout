"""Windows API helpers — find game window bounds."""

import ctypes
import ctypes.wintypes
import logging

log = logging.getLogger(__name__)

_user32 = ctypes.windll.user32
_WNDENUMPROC = ctypes.WINFUNCTYPE(
    ctypes.c_bool,
    ctypes.wintypes.HWND,
    ctypes.wintypes.LPARAM,
)


def find_window_region(title_contains: str) -> tuple[int, int, int, int] | None:
    """
    Return the client-area bounding box (x, y, w, h) in screen coordinates
    of the first visible window whose title contains `title_contains` (case-insensitive).
    Returns None if no matching window is found.
    """
    found: list[ctypes.wintypes.HWND] = []

    def _cb(hwnd: ctypes.wintypes.HWND, _: ctypes.wintypes.LPARAM) -> bool:
        if not _user32.IsWindowVisible(hwnd):
            return True
        length = _user32.GetWindowTextLengthW(hwnd)
        if length == 0:
            return True
        buf = ctypes.create_unicode_buffer(length + 1)
        _user32.GetWindowTextW(hwnd, buf, length + 1)
        if title_contains.lower() in buf.value.lower():
            found.append(hwnd)
        return True

    _user32.EnumWindows(_WNDENUMPROC(_cb), 0)

    if not found:
        log.debug("find_window_region: no window containing %r found", title_contains)
        return None

    hwnd = found[0]
    # GetWindowRect gives absolute screen coords including title bar/border
    rect = ctypes.wintypes.RECT()
    _user32.GetWindowRect(hwnd, ctypes.byref(rect))
    x, y = rect.left, rect.top
    w, h = rect.right - rect.left, rect.bottom - rect.top
    if w <= 0 or h <= 0 or x < -500 or y < -500:
        # Window is minimised or off-screen
        log.debug("find_window_region: window %r is minimised or off-screen (%d,%d %dx%d)",
                  title_contains, x, y, w, h)
        return None
    # Inset by a few pixels to skip the window border/resize-handle area
    pad = 12
    region = (x + pad, y + pad, w - pad * 2, h - pad * 2)
    log.info("Game window found: %r → region %s (pad=%d)", title_contains, region, pad)
    return region
