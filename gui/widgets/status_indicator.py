"""
Status indicator dot widget -- shows online/offline/backing-up state.
"""

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPainter, QColor
from PySide6.QtWidgets import QWidget
from gui.theme import POSITIVE, NEGATIVE, WARNING, TEXT_SECONDARY


STATUS_COLORS = {
    "online":     POSITIVE,
    "offline":    NEGATIVE,
    "backing_up": WARNING,
    "unknown":    TEXT_SECONDARY,
}


class StatusIndicator(QWidget):
    """A small coloured dot indicating client status."""

    def __init__(self, status: str = "unknown", size: int = 12, parent=None):
        super().__init__(parent)
        self._status = status
        self._dot_size = size
        self.setFixedSize(QSize(size, size))

    def set_status(self, status: str):
        self._status = status
        self.update()

    def status(self) -> str:
        return self._status

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        color = QColor(STATUS_COLORS.get(self._status, TEXT_SECONDARY))
        painter.setBrush(color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(0, 0, self._dot_size, self._dot_size)
        painter.end()
