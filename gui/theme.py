"""
Theme and styling constants for the backup orchestrator.
"""

from PySide6.QtGui import QColor, QFont

# -- Colour tokens ---------------------------------------------------------------
NAVY         = "#1F3864"
ACCENT       = "#4E79A7"
ACCENT_LIGHT = "#A0CBE8"
BG_CARD      = "#FFFFFF"
BG_MAIN      = "#F5F6FA"
TEXT_PRIMARY  = "#1A1A2E"
TEXT_SECONDARY= "#6B7280"
POSITIVE     = "#22C55E"  # success / online
NEGATIVE     = "#EF4444"  # failure / offline
WARNING      = "#F59E0B"  # in-progress / backing up
BORDER       = "#E5E7EB"

# -- Fonts -----------------------------------------------------------------------
def font_heading(size: int = 16) -> QFont:
    f = QFont("Segoe UI", size)
    f.setWeight(QFont.Weight.DemiBold)
    return f

def font_body(size: int = 10) -> QFont:
    return QFont("Segoe UI", size)

def font_mono(size: int = 9) -> QFont:
    return QFont("Cascadia Code", size)

# -- Card stylesheet -------------------------------------------------------------
CARD_STYLE = f"""
    QFrame#card {{
        background-color: {BG_CARD};
        color: {TEXT_PRIMARY};
        border: 1px solid {BORDER};
        border-radius: 12px;
    }}
"""

STAT_VALUE_STYLE = f"""
    QLabel {{
        color: {NAVY};
        font-size: 28px;
        font-weight: 600;
        font-family: 'Segoe UI';
    }}
"""

STAT_LABEL_STYLE = f"""
    QLabel {{
        color: {TEXT_SECONDARY};
        font-size: 11px;
        font-family: 'Segoe UI';
    }}
"""

# -- Reusable widget styles -------------------------------------------------------
INPUT_STYLE = f"""
    QLineEdit {{
        border: 1px solid {BORDER};
        border-radius: 6px;
        padding: 6px 10px;
        font-size: 10pt;
        background-color: white;
        color: {TEXT_PRIMARY};
    }}
    QLineEdit:focus {{
        border-color: {NAVY};
    }}
"""

COMBO_STYLE = f"""
    QComboBox {{
        border: 1px solid {BORDER};
        border-radius: 6px;
        padding: 6px 10px;
        font-size: 10pt;
        background-color: white;
        color: {TEXT_PRIMARY};
    }}
    QComboBox:focus {{
        border-color: {NAVY};
    }}
    QComboBox::drop-down {{
        border: none;
        width: 24px;
    }}
    QComboBox QAbstractItemView {{
        background-color: white;
        color: {TEXT_PRIMARY};
        border: 1px solid {BORDER};
        selection-background-color: #E8EDF5;
        selection-color: {NAVY};
        font-size: 10pt;
        padding: 4px;
    }}
"""

TABLE_STYLE = f"""
    QTableView {{
        border: none;
        background-color: white;
        color: {TEXT_PRIMARY};
        alternate-background-color: #F9FAFB;
        selection-background-color: #E8EDF5;
        selection-color: {NAVY};
        font-size: 10pt;
        gridline-color: transparent;
    }}
    QTableView::item {{
        padding: 6px 8px;
        border-bottom: 1px solid #F3F4F6;
        color: {TEXT_PRIMARY};
    }}
    QHeaderView::section {{
        background-color: #F9FAFB;
        color: {NAVY};
        font-weight: 600;
        font-size: 10pt;
        padding: 8px;
        border: none;
        border-bottom: 2px solid {BORDER};
    }}
"""

BUTTON_STYLE = f"""
    QPushButton {{
        background-color: {NAVY};
        color: white;
        border: none;
        border-radius: 6px;
        padding: 6px 16px;
        font-size: 10pt;
        font-weight: 600;
    }}
    QPushButton:hover {{
        background-color: #2B4A8C;
    }}
    QPushButton:disabled {{
        background-color: #9CA3AF;
    }}
"""

BUTTON_SECONDARY_STYLE = f"""
    QPushButton {{
        background-color: {ACCENT};
        color: white;
        border: none;
        border-radius: 6px;
        padding: 6px 16px;
        font-size: 10pt;
        font-weight: 600;
    }}
    QPushButton:hover {{
        background-color: #3A6591;
    }}
    QPushButton:disabled {{
        background-color: #9CA3AF;
    }}
"""

BUTTON_DANGER_STYLE = f"""
    QPushButton {{
        background-color: {NEGATIVE};
        color: white;
        border: none;
        border-radius: 6px;
        padding: 6px 16px;
        font-size: 10pt;
        font-weight: 600;
    }}
    QPushButton:hover {{
        background-color: #DC2626;
    }}
    QPushButton:disabled {{
        background-color: #9CA3AF;
    }}
"""
