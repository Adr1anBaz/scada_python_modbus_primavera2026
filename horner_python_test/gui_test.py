import sys
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QMessageBox,
)

from modbus_service import HornerModbusService, COIL_T1, COIL_Q10


class HornerWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Horner XL4 - GUI Paso 1")
        self.resize(320, 220)

        self.service = HornerModbusService()

        self.label_status = QLabel("Estado Q10: desconocido")

        self.button_t1_on = QPushButton("T1 ON")
        self.button_t1_off = QPushButton("T1 OFF")
        self.button_refresh_q10 = QPushButton("Leer Q10")

        layout = QVBoxLayout()
        layout.addWidget(self.label_status)
        layout.addWidget(self.button_t1_on)
        layout.addWidget(self.button_t1_off)
        layout.addWidget(self.button_refresh_q10)

        self.setLayout(layout)

        self.button_t1_on.clicked.connect(self.turn_t1_on)
        self.button_t1_off.clicked.connect(self.turn_t1_off)
        self.button_refresh_q10.clicked.connect(self.refresh_q10)

        self.connect_to_plc()

    def connect_to_plc(self):
        connected = self.service.connect()
        if not connected:
            QMessageBox.critical(self, "Error", "No se pudo conectar al PLC.")
            self.label_status.setText("Estado Q10: sin conexion")
            self.button_t1_on.setEnabled(False)
            self.button_t1_off.setEnabled(False)
            self.button_refresh_q10.setEnabled(False)
        else:
            self.refresh_q10()

    def turn_t1_on(self):
        try:
            self.service.write_coil(COIL_T1, True)
            self.refresh_q10()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def turn_t1_off(self):
        try:
            self.service.write_coil(COIL_T1, False)
            self.refresh_q10()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def refresh_q10(self):
        try:
            q10_value = self.service.read_coil(COIL_Q10)
            self.label_status.setText(f"Estado Q10: {q10_value}")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def closeEvent(self, event):
        self.service.close()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = HornerWindow()
    window.show()
    sys.exit(app.exec())