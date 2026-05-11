"""
GUI de prueba - sin conexión a PLCs.
Solo para verificar que PySide6 funciona y ver cómo se ve.
"""

import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QPushButton, QLabel, QTabWidget, QGroupBox
)
from PySide6.QtCore import Qt


class PruebaWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SCADA - Prueba de GUI")
        self.setMinimumSize(500, 300)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        tabs = QTabWidget()
        layout.addWidget(tabs)

        # Tab de prueba
        tab_prueba = QWidget()
        tab_layout = QVBoxLayout(tab_prueba)

        # Grupo de control
        grupo = QGroupBox("Control de prueba")
        grupo_layout = QHBoxLayout(grupo)

        self.btn_toggle = QPushButton("Presióname")
        self.btn_toggle.setStyleSheet(
            "background-color: #4CAF50; color: white; font-size: 14px; "
            "padding: 10px 20px; border-radius: 5px;"
        )
        self.btn_toggle.clicked.connect(self.toggle_led)

        self.led = QLabel("OFF")
        self.led.setAlignment(Qt.AlignCenter)
        self.led.setFixedSize(80, 40)
        self.led.setStyleSheet(
            "background-color: red; color: white; font-weight: bold; "
            "border-radius: 10px; font-size: 14px;"
        )

        grupo_layout.addWidget(self.btn_toggle)
        grupo_layout.addWidget(self.led)

        tab_layout.addWidget(grupo)
        tab_layout.addStretch()

        tabs.addTab(tab_prueba, "Prueba")
        tabs.addTab(QWidget(), "Entrada")
        tabs.addTab(QWidget(), "Central")
        tabs.addTab(QWidget(), "Salida")

        # Status bar
        self.statusBar().showMessage("Sin conexión a PLCs - modo prueba")

        self.led_state = False

    def toggle_led(self):
        self.led_state = not self.led_state

        if self.led_state:
            self.led.setText("ON")
            self.led.setStyleSheet(
                "background-color: green; color: white; font-weight: bold; "
                "border-radius: 10px; font-size: 14px;"
            )
            self.btn_toggle.setText("Apagar")
        else:
            self.led.setText("OFF")
            self.led.setStyleSheet(
                "background-color: red; color: white; font-weight: bold; "
                "border-radius: 10px; font-size: 14px;"
            )
            self.btn_toggle.setText("Presióname")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PruebaWindow()
    window.show()
    sys.exit(app.exec())
