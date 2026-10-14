from __future__ import annotations

import math
from PySide6 import QtCore, QtGui, QtWidgets


class SwingWidget(QtWidgets.QWidget):
    thetaChanged = QtCore.Signal(float)
    dragStateChanged = QtCore.Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.theta = 0.0
        self.omega = 0.0
        self.length_px = 220
        self._pivot = QtCore.QPointF(0.0, 0.0)
        self._bob = QtCore.QPointF(0.0, 0.0)
        self._dragging = False
        self.setMinimumSize(420, 420)
        self.setMouseTracking(True)

    def set_state(self, theta: float, omega: float) -> None:
        self.theta = float(theta)
        self.omega = float(omega)
        self.update()

    def _compute_geometry(self) -> None:
        rect = self.rect()
        self._pivot = QtCore.QPointF(rect.center().x(), rect.top() + 60)
        x = self._pivot.x() + self.length_px * math.sin(self.theta)
        y = self._pivot.y() + self.length_px * math.cos(self.theta)
        self._bob = QtCore.QPointF(x, y)

    def paintEvent(self, event) -> None:
        self._compute_geometry()
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.Antialiasing, True)
        p.fillRect(self.rect(), QtGui.QColor(245, 245, 245))

        p.setBrush(QtGui.QBrush(QtGui.QColor(60, 60, 60)))
        p.setPen(QtGui.QPen(QtGui.QColor(60, 60, 60), 2))
        p.drawEllipse(self._pivot, 6, 6)

        p.setPen(QtGui.QPen(QtGui.QColor(30, 30, 30), 3))
        p.drawLine(self._pivot, self._bob)

        bob_color = QtGui.QColor(80, 120, 200) if not self._dragging else QtGui.QColor(200, 120, 80)
        p.setBrush(QtGui.QBrush(bob_color))
        p.setPen(QtGui.QPen(QtGui.QColor(40, 40, 40), 2))
        p.drawEllipse(self._bob, 18, 18)

        p.setPen(QtGui.QPen(QtGui.QColor(20, 20, 20)))
        p.setFont(QtGui.QFont("Arial", 10))
        p.drawText(10, 20, f"theta={self.theta:+.3f} rad   omega={self.omega:+.3f} rad/s")

    def _hit_bob(self, pos: QtCore.QPointF) -> bool:
        self._compute_geometry()
        dx = pos.x() - self._bob.x()
        dy = pos.y() - self._bob.y()
        return (dx*dx + dy*dy) <= (24*24)

    def mousePressEvent(self, e: QtGui.QMouseEvent) -> None:
        if e.button() == QtCore.Qt.LeftButton and self._hit_bob(e.position()):
            self._dragging = True
            self.dragStateChanged.emit(True)
            self._update_theta_from_mouse(e.position())
            self.update()

    def mouseMoveEvent(self, e: QtGui.QMouseEvent) -> None:
        if self._dragging:
            self._update_theta_from_mouse(e.position())
            self.update()

    def mouseReleaseEvent(self, e: QtGui.QMouseEvent) -> None:
        if self._dragging and e.button() == QtCore.Qt.LeftButton:
            self._dragging = False
            self.dragStateChanged.emit(False)
            self.update()

    def _update_theta_from_mouse(self, pos: QtCore.QPointF) -> None:
        self._compute_geometry()
        dx = pos.x() - self._pivot.x()
        dy = pos.y() - self._pivot.y()
        theta = math.atan2(dx, dy)
        self.thetaChanged.emit(float(theta))
