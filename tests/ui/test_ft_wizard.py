"""Tests for the Fast Travel template capture wizard."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
from pytestqt.qtbot import QtBot

from app.ui.ft_wizard import FTWizard


def _fake_capture() -> np.ndarray:
    return np.full((100, 300, 3), (180, 180, 180), dtype=np.uint8)


class TestFTWizard:
    def test_opens_without_error(self, qtbot: QtBot) -> None:
        dlg = FTWizard()
        qtbot.addWidget(dlg)
        dlg.show()

    def test_ok_button_disabled_before_capture(self, qtbot: QtBot) -> None:
        dlg = FTWizard()
        qtbot.addWidget(dlg)
        assert not dlg._ok_btn.isEnabled()

    def test_ok_enabled_after_capture(self, qtbot: QtBot) -> None:
        dlg = FTWizard()
        qtbot.addWidget(dlg)
        with patch("app.ui.ft_wizard.pyautogui.position", return_value=(400, 300)), \
             patch("app.ui.ft_wizard.mss.mss") as mock_mss:
            mock_sct = MagicMock()
            mock_shot = MagicMock()
            # Return a valid BGRA numpy array via __array__
            bgra = np.full((100, 300, 4), 180, dtype=np.uint8)
            mock_shot.__array__ = MagicMock(return_value=bgra)
            mock_sct.grab.return_value = mock_shot
            mock_mss.return_value.__enter__ = MagicMock(return_value=mock_sct)
            mock_mss.return_value.__exit__ = MagicMock(return_value=False)
            dlg._capture()
        assert dlg._ok_btn.isEnabled()

    def test_confirm_writes_file(self, qtbot: QtBot, tmp_path: Path) -> None:
        dlg = FTWizard()
        qtbot.addWidget(dlg)
        dlg._captured_img = _fake_capture()
        out = str(tmp_path / "ft.png")
        dlg._out_path = out
        with patch.object(dlg, "accept"):
            dlg._on_confirm()
        assert Path(out).exists()

    def test_confirm_without_capture_does_nothing(self, qtbot: QtBot) -> None:
        dlg = FTWizard()
        qtbot.addWidget(dlg)
        assert dlg._captured_img is None
        with patch.object(dlg, "accept") as mock_accept:
            dlg._on_confirm()
            mock_accept.assert_not_called()
