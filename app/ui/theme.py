"""Dark Forza-inspired theme: near-black background, orange accent."""

STYLESHEET = """
QWidget {
    background-color: #12121A;
    color: #E0E0E8;
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 13px;
}

QLabel[class="app-title"] {
    font-size: 18px;
    font-weight: bold;
    color: #FF6B1A;
    letter-spacing: 1px;
}

QLabel[class="app-subtitle"] {
    font-size: 10px;
    color: #888899;
    letter-spacing: 2px;
}

QLabel[class="section-label"] {
    font-size: 10px;
    font-weight: bold;
    color: #FF6B1A;
    letter-spacing: 2px;
}

QLabel[class="stat-title"] {
    font-size: 10px;
    color: #888899;
    letter-spacing: 1px;
}

QLabel[class="stat-value"] {
    font-size: 22px;
    font-weight: bold;
    color: #E0E0E8;
}

QLabel[class="small-label"] {
    font-size: 11px;
    color: #777788;
}

QLabel[class="status-label"] {
    font-size: 11px;
    color: #AAAACC;
    padding: 4px;
    background-color: #1C1C28;
    border-radius: 4px;
}

QFrame[class="stat-card"] {
    background-color: #1C1C28;
    border: 1px solid #2A2A3A;
    border-radius: 6px;
    padding: 4px;
}

QFrame[class="separator"] {
    background-color: #2A2A3A;
    max-height: 1px;
    border: none;
}

QPushButton {
    background-color: #2A2A3A;
    color: #C0C0D0;
    border: 1px solid #3A3A4E;
    border-radius: 5px;
    padding: 6px 10px;
    font-size: 12px;
}

QPushButton:hover {
    background-color: #34344A;
    color: #E0E0F0;
}

QPushButton:pressed {
    background-color: #202030;
}

QPushButton:disabled {
    color: #444458;
    background-color: #1A1A26;
    border-color: #242434;
}

QPushButton[class="primary-btn"] {
    background-color: #FF6B1A;
    color: #FFFFFF;
    font-weight: bold;
    border: none;
}

QPushButton[class="primary-btn"]:hover {
    background-color: #FF7F35;
}

QPushButton[class="primary-btn"]:pressed {
    background-color: #E05510;
}

QPushButton[class="primary-btn"]:disabled {
    background-color: #5A2A10;
    color: #886655;
}

QPushButton[class="accent-btn"] {
    background-color: #1A6AFF;
    color: #FFFFFF;
    font-weight: bold;
    border: none;
}

QPushButton[class="accent-btn"]:hover {
    background-color: #357FFF;
}

QPushButton[class="accent-btn"]:disabled {
    background-color: #1A2A5A;
    color: #445588;
}

QProgressBar {
    background-color: #1C1C28;
    border: 1px solid #2A2A3A;
    border-radius: 5px;
    text-align: center;
    color: #E0E0E8;
    font-size: 11px;
    height: 18px;
}

QProgressBar::chunk {
    background-color: #FF6B1A;
    border-radius: 4px;
}

QDialog {
    background-color: #16161F;
}

QScrollBar:vertical {
    background: #12121A;
    width: 8px;
}

QScrollBar::handle:vertical {
    background: #3A3A4E;
    border-radius: 4px;
}

QSplitter::handle {
    background: #2A2A3A;
    width: 2px;
}
"""
