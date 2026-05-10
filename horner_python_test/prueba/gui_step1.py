import sys
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QMessageBox,
    QLineEdit,
)
from PySide6.QtCore import QTimer

from modbus_service import (
    HornerModbusService,
    COIL_T1,
    COIL_Q10,
    REGISTER_R1,
)


class HornerWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Horner XL4 - GUI Paso 3 (QTimer)")
        self.resize(360, 320)

        self.service = HornerModbusService()
        self.connected = False

        # Estado de Q10
        self.label_q10 = QLabel("Estado Q10: desconocido")

        # Botones T1
        self.button_t1_on = QPushButton("T1 ON")
        self.button_t1_off = QPushButton("T1 OFF")

        # Estado de R1
        self.label_r1 = QLabel("Valor R1: desconocido")
        self.input_r1 = QLineEdit()
        self.input_r1.setPlaceholderText("Escribe un entero para R1")

        self.button_write_r1 = QPushButton("Escribir R1")
        self.button_read_r1 = QPushButton("Leer R1")

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.label_q10)
        layout.addWidget(self.button_t1_on)
        layout.addWidget(self.button_t1_off)
        layout.addWidget(self.label_r1)
        layout.addWidget(self.input_r1)
        layout.addWidget(self.button_write_r1)
        layout.addWidget(self.button_read_r1)

        self.setLayout(layout)

        # Conexiones de botones
        self.button_t1_on.clicked.connect(self.turn_t1_on)
        self.button_t1_off.clicked.connect(self.turn_t1_off)
        self.button_write_r1.clicked.connect(self.write_r1)
        self.button_read_r1.clicked.connect(self.refresh_r1)

        self.connect_to_plc()

        # Timer para refresco automático
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_all_status)
        self.timer.start(500)  # cada 500 ms

    def connect_to_plc(self):
        self.connected = self.service.connect()

        if not self.connected:
            QMessageBox.critical(self, "Error", "No se pudo conectar al PLC.")
            self.label_q10.setText("Estado Q10: sin conexion")
            self.label_r1.setText("Valor R1: sin conexion")

            self.button_t1_on.setEnabled(False)
            self.button_t1_off.setEnabled(False)
            self.button_write_r1.setEnabled(False)
            self.button_read_r1.setEnabled(False)
            self.input_r1.setEnabled(False)
            return

        self.refresh_all_status()

    def refresh_all_status(self):
        if not self.connected:
            return

        try:
            q10_value = self.service.read_coil(COIL_Q10)
            self.label_q10.setText(f"Estado Q10: {q10_value}")
        except Exception as e:
            self.label_q10.setText(f"Estado Q10: error")
            print(f"Error leyendo Q10: {e}")

        try:
            r1_value = self.service.read_register(REGISTER_R1)
            self.label_r1.setText(f"Valor R1: {r1_value}")
        except Exception as e:
            self.label_r1.setText("Valor R1: error")
            print(f"Error leyendo R1: {e}")

    def turn_t1_on(self):
        try:
            self.service.write_coil(COIL_T1, True)
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def turn_t1_off(self):
        try:
            self.service.write_coil(COIL_T1, False)
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def write_r1(self):
        try:
            text_value = self.input_r1.text().strip()

            if text_value == "":
                QMessageBox.warning(self, "Aviso", "Escribe un valor entero para R1.")
                return

            value = int(text_value)
            self.service.write_register(REGISTER_R1, value)
            self.refresh_r1()
        except ValueError:
            QMessageBox.warning(self, "Aviso", "R1 debe ser un numero entero.")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def refresh_r1(self):
        if not self.connected:
            return

        try:
            r1_value = self.service.read_register(REGISTER_R1)
            self.label_r1.setText(f"Valor R1: {r1_value}")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def closeEvent(self, event):
        self.timer.stop()
        self.service.close()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = HornerWindow()
    window.show()
    sys.exit(app.exec())