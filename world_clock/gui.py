from __future__ import annotations

import sys
from dataclasses import dataclass
from datetime import datetime
from typing import List

from PySide6 import QtCore, QtGui, QtWidgets

from .time_utils import get_timezones_for_input, now_in_zone


@dataclass
class ClockItem:
    country: str
    zone: str


class AnalogClockWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(120, 120)
        self._time = datetime.now()

    def setDateTime(self, dt: datetime):
        self._time = dt
        self.update()

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        side = min(self.width(), self.height())
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.translate(self.width() / 2, self.height() / 2)
        painter.scale(side / 200.0, side / 200.0)

        # Draw clock face
        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(QtGui.QColor(240, 240, 240))
        painter.drawEllipse(QtCore.QPoint(0, 0), 98, 98)
        painter.setPen(QtGui.QPen(QtGui.QColor(100, 100, 100)))
        for i in range(60):
            painter.drawLine(88 if i % 5 else 80, 0, 92, 0)
            painter.rotate(6)

        t = self._time
        hour = t.hour % 12 + t.minute / 60.0
        minute = t.minute + t.second / 60.0
        second = t.second

        # Hour hand
        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(QtGui.QColor(50, 50, 50))
        painter.save()
        painter.rotate(30 * hour)
        hour_hand = QtGui.QPolygon([QtCore.QPoint(-6, 0), QtCore.QPoint(0, -50), QtCore.QPoint(6, 0), QtCore.QPoint(0, 10)])
        painter.drawPolygon(hour_hand)
        painter.restore()

        # Minute hand
        painter.setBrush(QtGui.QColor(80, 80, 80))
        painter.save()
        painter.rotate(6 * minute)
        minute_hand = QtGui.QPolygon([QtCore.QPoint(-4, 0), QtCore.QPoint(0, -70), QtCore.QPoint(4, 0), QtCore.QPoint(0, 12)])
        painter.drawPolygon(minute_hand)
        painter.restore()

        # Second hand
        painter.setBrush(QtGui.QColor(200, 0, 0))
        painter.save()
        painter.rotate(6 * second)
        painter.drawRect(-1, -80, 2, 80)
        painter.restore()

        painter.setBrush(QtGui.QColor(0, 0, 0))
        painter.drawEllipse(QtCore.QPoint(0, 0), 4, 4)


class ClockCard(QtWidgets.QWidget):
    def __init__(self, item: ClockItem, digital: bool = True, parent=None):
        super().__init__(parent)
        self.item = item
        self.digital = digital

        self.title = QtWidgets.QLabel(f"{item.country} — {item.zone}")
        self.title.setStyleSheet("font-weight: bold")

        if self.digital:
            self.time_label = QtWidgets.QLabel("--:--:--")
            self.time_label.setAlignment(QtCore.Qt.AlignCenter)
            self.time_label.setStyleSheet("font-size: 24px;")
            self.clock_widget = None
        else:
            self.clock_widget = AnalogClockWidget()
            self.time_label = QtWidgets.QLabel("")

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.title)
        if self.clock_widget:
            layout.addWidget(self.clock_widget)
        layout.addWidget(self.time_label)

    def update_time(self):
        dt = now_in_zone(self.item.zone)
        if self.digital:
            self.time_label.setText(dt.strftime('%Y-%m-%d %H:%M:%S'))
        else:
            self.clock_widget.setDateTime(dt)
            self.time_label.setText(dt.strftime('%Y-%m-%d %H:%M:%S'))


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("World Clock")

        central = QtWidgets.QWidget()
        self.setCentralWidget(central)

        self.input_codes = QtWidgets.QLineEdit()
        self.input_codes.setPlaceholderText("Enter country codes or time zones (e.g., US,IN,GB or CST, America/Chicago)")
        self.btn_apply = QtWidgets.QPushButton("Apply")
        self.toggle_mode = QtWidgets.QComboBox()
        self.toggle_mode.addItems(["Digital", "Analog"])
        self.chk_one_per = QtWidgets.QCheckBox("One zone per country")

        top = QtWidgets.QHBoxLayout()
        top.addWidget(self.input_codes)
        top.addWidget(self.btn_apply)
        top.addWidget(self.toggle_mode)
        top.addWidget(self.chk_one_per)

        self.grid = QtWidgets.QGridLayout()
        self.grid.setSpacing(8)

        layout = QtWidgets.QVBoxLayout(central)
        layout.addLayout(top)
        layout.addLayout(self.grid)

        self._cards: list[ClockCard] = []

        self.btn_apply.clicked.connect(self.rebuild)
        self.toggle_mode.currentIndexChanged.connect(self.rebuild)

        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.on_tick)
        self.timer.start()

    def parse_codes(self) -> list[str]:
        text = self.input_codes.text().strip()
        if not text:
            return []
        parts = [p.strip() for p in text.replace(';', ',').split(',')]
        return [p for p in parts if p]

    def rebuild(self):
        # Clear grid
        for c in self._cards:
            c.setParent(None)
        self._cards.clear()
        # Build new cards
        codes = self.parse_codes()
        digital = self.toggle_mode.currentIndex() == 0
        row = col = 0
        for code in codes:
            zones = get_timezones_for_input(code, include_all=not self.chk_one_per.isChecked())
            if not zones:
                # Show a small warning card
                card = QtWidgets.QLabel(f"{code}: no zones found")
                self.grid.addWidget(card, row, col)
                col += 1
                if col >= 3:
                    col = 0
                    row += 1
                continue
            for z in zones:
                card = ClockCard(ClockItem(code.upper(), z), digital=digital)
                self._cards.append(card)
                self.grid.addWidget(card, row, col)
                col += 1
                if col >= 3:
                    col = 0
                    row += 1

        self.on_tick()

    def on_tick(self):
        for c in self._cards:
            c.update_time()


def run_gui():
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.resize(900, 600)
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    run_gui()
