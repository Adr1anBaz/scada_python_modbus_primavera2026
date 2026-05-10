import sys
from PySide6.QtWidgets import QApplication, QWidget, QMessageBox
from PySide6.QtCore import QTimer

from horner_gui_ui import Ui_Form
from modbus_service import (
    HornerModbusService,
    COIL_T1,
    COIL_Q10,
    REGISTER_R1,
)


class HornerDesignerWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.ui = Ui_Form()
        self.ui.setupUi(self)

        self.setWindowTitle("Horner XL4 - Qt Designer")

        self.service = HornerModbusService()
        self.connected = False

        # Conectar eventos
        self.ui.btnT1Momentary.pressed.connect(self.turn_t1_on)
        self.ui.btnT1Momentary.released.connect(self.turn_t1_off)
        self.ui.btnWriteR1.clicked.connect(self.write_r1)
        self.ui.btnReadR1.clicked.connect(self.refresh_r1)

        # Conexión al PLC
        self.connect_to_plc()

        # Timer para refresco automático
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_all_status)
        self.timer.start(500)

    def connect_to_plc(self):
        self.connected = self.service.connect()

        if not self.connected:
            QMessageBox.critical(self, "Error", "No se pudo conectar al PLC.")
            self.ui.ledQ10.setText("SIN CONN")
            self.ui.ledQ10.setStyleSheet(
                "background-color: gray; color: white; font-weight: bold; border-radius: 10px; min-height: 24px;"
            )
            self.ui.lblR1Value.setText("sin conexion")
            self.ui.btnT1Momentary.setEnabled(False)
            self.ui.btnWriteR1.setEnabled(False)
            self.ui.btnReadR1.setEnabled(False)
            self.ui.inputR1.setEnabled(False)
            return

        self.refresh_all_status()

    def refresh_all_status(self):
        if not self.connected:
            return

        try:
            q10_value = self.service.read_coil(COIL_Q10)
            self.update_q10_led(q10_value)
        except Exception as e:
            self.ui.ledQ10.setText("ERROR")
            self.ui.ledQ10.setStyleSheet(
                "background-color: orange; color: black; font-weight: bold; border-radius: 10px; min-height: 24px;"
            )
            print(f"Error leyendo Q10: {e}")

        try:
            r1_value = self.service.read_register(REGISTER_R1)
            self.ui.lblR1Value.setText(str(r1_value))
        except Exception as e:
            self.ui.lblR1Value.setText("error")
            print(f"Error leyendo R1: {e}")

    def update_q10_led(self, is_on: bool):
        if is_on:
            self.ui.ledQ10.setText("ON")
            self.ui.ledQ10.setStyleSheet(
                "background-color: green; color: white; font-weight: bold; border-radius: 10px; min-height: 24px;"
            )
        else:
            self.ui.ledQ10.setText("OFF")
            self.ui.ledQ10.setStyleSheet(
                "background-color: red; color: white; font-weight: bold; border-radius: 10px; min-height: 24px;"
            )

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
            text_value = self.ui.inputR1.text().strip()

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
            self.ui.lblR1Value.setText(str(r1_value))
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def closeEvent(self, event):
        self.timer.stop()
        self.service.close()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = HornerDesignerWindow()
    window.show()
    sys.exit(app.exec())