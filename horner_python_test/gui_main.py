"""
GUI principal del sistema SCADA para bandas automatizadas.
Controla 3 PLCs Horner XL4 via Modbus TCP.
"""

import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QPushButton, QLabel, QTabWidget, QGroupBox,
    QGridLayout, QLineEdit, QTextEdit, QMessageBox
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont

from system import PLCManager
from system.constants import *


class LedIndicator(QLabel):
    """Widget de LED virtual reutilizable."""

    def __init__(self, text="OFF", parent=None):
        super().__init__(text, parent)
        self.setAlignment(Qt.AlignCenter)
        self.setFixedSize(70, 30)
        self.setFont(QFont("Arial", 10, QFont.Bold))
        self.set_off()

    def set_on(self, text="ON"):
        self.setText(text)
        self.setStyleSheet(
            "background-color: #4CAF50; color: white; "
            "border-radius: 8px;"
        )

    def set_off(self, text="OFF"):
        self.setText(text)
        self.setStyleSheet(
            "background-color: #F44336; color: white; "
            "border-radius: 8px;"
        )

    def set_warning(self, text="---"):
        self.setText(text)
        self.setStyleSheet(
            "background-color: #FF9800; color: white; "
            "border-radius: 8px;"
        )

    def set_inactive(self, text="N/C"):
        self.setText(text)
        self.setStyleSheet(
            "background-color: #9E9E9E; color: white; "
            "border-radius: 8px;"
        )

    def update_state(self, state: bool):
        if state:
            self.set_on()
        else:
            self.set_off()


class EntradaTab(QWidget):
    """Tab para el PLC de Entrada (HORNER_2 - 192.168.3.132)."""

    PLC_ID = "HORNER_2"

    def __init__(self, manager: PLCManager, log_callback):
        super().__init__()
        self.manager = manager
        self.log = log_callback
        self.connected = False
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # --- Fila superior: Control + Lámparas ---
        top_row = QHBoxLayout()

        # Control general
        grp_control = QGroupBox("Control")
        ctrl_layout = QHBoxLayout(grp_control)

        self.btn_inicio = QPushButton("▶ INICIO")
        self.btn_inicio.setStyleSheet(self._btn_style("#4CAF50"))
        self.btn_inicio.clicked.connect(self.on_inicio)

        self.btn_stop = QPushButton("⏹ STOP")
        self.btn_stop.setStyleSheet(self._btn_style("#F44336"))
        self.btn_stop.clicked.connect(self.on_stop)

        ctrl_layout.addWidget(self.btn_inicio)
        ctrl_layout.addWidget(self.btn_stop)
        top_row.addWidget(grp_control)

        # Lámparas
        grp_lamparas = QGroupBox("Lámparas")
        lamp_layout = QHBoxLayout(grp_lamparas)

        lamp_layout.addWidget(QLabel("Verde:"))
        self.led_verde = LedIndicator()
        lamp_layout.addWidget(self.led_verde)

        lamp_layout.addWidget(QLabel("Amarilla:"))
        self.led_amarilla = LedIndicator()
        lamp_layout.addWidget(self.led_amarilla)

        lamp_layout.addWidget(QLabel("Roja:"))
        self.led_roja = LedIndicator()
        lamp_layout.addWidget(self.led_roja)

        top_row.addWidget(grp_lamparas)
        layout.addLayout(top_row)

        # --- Fila media: Banda + Plumas ---
        mid_row = QHBoxLayout()

        # Banda
        grp_banda = QGroupBox("Banda")
        banda_layout = QVBoxLayout(grp_banda)

        banda_btns = QHBoxLayout()
        self.btn_banda_izq = QPushButton("◀ Izq")
        self.btn_banda_izq.setStyleSheet(self._btn_style("#2196F3"))
        self.btn_banda_izq.clicked.connect(self.on_banda_izq)

        self.btn_banda_stop = QPushButton("⏹ Stop")
        self.btn_banda_stop.setStyleSheet(self._btn_style("#607D8B"))
        self.btn_banda_stop.clicked.connect(self.on_banda_stop)

        self.btn_banda_der = QPushButton("▶ Der")
        self.btn_banda_der.setStyleSheet(self._btn_style("#2196F3"))
        self.btn_banda_der.clicked.connect(self.on_banda_der)

        banda_btns.addWidget(self.btn_banda_izq)
        banda_btns.addWidget(self.btn_banda_stop)
        banda_btns.addWidget(self.btn_banda_der)
        banda_layout.addLayout(banda_btns)

        # VFD
        vfd_row = QHBoxLayout()
        vfd_row.addWidget(QLabel("VFD Hz:"))
        self.input_vfd = QLineEdit()
        self.input_vfd.setPlaceholderText("Frecuencia")
        self.input_vfd.setFixedWidth(80)
        vfd_row.addWidget(self.input_vfd)

        self.btn_vfd_escribir = QPushButton("Escribir")
        self.btn_vfd_escribir.clicked.connect(self.on_vfd_escribir)
        vfd_row.addWidget(self.btn_vfd_escribir)

        vfd_row.addWidget(QLabel("Actual:"))
        self.lbl_vfd_actual = QLabel("--- Hz")
        self.lbl_vfd_actual.setFont(QFont("Arial", 10, QFont.Bold))
        vfd_row.addWidget(self.lbl_vfd_actual)
        vfd_row.addStretch()

        banda_layout.addLayout(vfd_row)
        mid_row.addWidget(grp_banda)

        # Plumas
        grp_plumas = QGroupBox("Plumas")
        plumas_layout = QGridLayout(grp_plumas)

        plumas_layout.addWidget(QLabel("Inicio:"), 0, 0)
        self.btn_pluma_ini_sube = QPushButton("↑ Sube")
        self.btn_pluma_ini_sube.clicked.connect(self.on_pluma_ini_sube)
        plumas_layout.addWidget(self.btn_pluma_ini_sube, 0, 1)

        self.btn_pluma_ini_baja = QPushButton("↓ Baja")
        self.btn_pluma_ini_baja.clicked.connect(self.on_pluma_ini_baja)
        plumas_layout.addWidget(self.btn_pluma_ini_baja, 0, 2)

        plumas_layout.addWidget(QLabel("Fin:"), 1, 0)
        self.btn_pluma_fin = QPushButton("↕ Toggle")
        self.btn_pluma_fin.clicked.connect(self.on_pluma_fin)
        plumas_layout.addWidget(self.btn_pluma_fin, 1, 1)

        mid_row.addWidget(grp_plumas)
        layout.addLayout(mid_row)

        # --- Fila inferior: Torreta + Sensores ---
        bot_row = QHBoxLayout()

        # Torreta
        grp_torreta = QGroupBox("Torreta Manual")
        torreta_layout = QHBoxLayout(grp_torreta)

        self.btn_torr_verde = QPushButton("🟢")
        self.btn_torr_verde.setStyleSheet(self._btn_style("#4CAF50"))
        self.btn_torr_verde.clicked.connect(self.on_torreta_verde)
        torreta_layout.addWidget(self.btn_torr_verde)

        self.btn_torr_amarilla = QPushButton("🟡")
        self.btn_torr_amarilla.setStyleSheet(self._btn_style("#FFC107"))
        self.btn_torr_amarilla.clicked.connect(self.on_torreta_amarilla)
        torreta_layout.addWidget(self.btn_torr_amarilla)

        self.btn_torr_roja = QPushButton("🔴")
        self.btn_torr_roja.setStyleSheet(self._btn_style("#F44336"))
        self.btn_torr_roja.clicked.connect(self.on_torreta_roja)
        torreta_layout.addWidget(self.btn_torr_roja)

        bot_row.addWidget(grp_torreta)

        # Sensores
        grp_sensores = QGroupBox("Sensores / Estado")
        sensores_layout = QGridLayout(grp_sensores)

        sensores_layout.addWidget(QLabel("I4 Entrada:"), 0, 0)
        self.led_sensor_entrada = LedIndicator()
        sensores_layout.addWidget(self.led_sensor_entrada, 0, 1)

        sensores_layout.addWidget(QLabel("I5 Salida:"), 0, 2)
        self.led_sensor_salida = LedIndicator()
        sensores_layout.addWidget(self.led_sensor_salida, 0, 3)

        sensores_layout.addWidget(QLabel("Pluma ini↑:"), 1, 0)
        self.led_pluma_ini_arriba = LedIndicator()
        sensores_layout.addWidget(self.led_pluma_ini_arriba, 1, 1)

        sensores_layout.addWidget(QLabel("Pluma ini↓:"), 1, 2)
        self.led_pluma_ini_abajo = LedIndicator()
        sensores_layout.addWidget(self.led_pluma_ini_abajo, 1, 3)

        sensores_layout.addWidget(QLabel("Pluma fin↑:"), 2, 0)
        self.led_pluma_fin_arriba = LedIndicator()
        sensores_layout.addWidget(self.led_pluma_fin_arriba, 2, 1)

        sensores_layout.addWidget(QLabel("Pluma fin↓:"), 2, 2)
        self.led_pluma_fin_abajo = LedIndicator()
        sensores_layout.addWidget(self.led_pluma_fin_abajo, 2, 3)

        bot_row.addWidget(grp_sensores)
        layout.addLayout(bot_row)

        # --- UR3 / Integración ---
        grp_ur3 = QGroupBox("Estado Integración / UR3")
        ur3_layout = QHBoxLayout(grp_ur3)

        ur3_layout.addWidget(QLabel("sebListo:"))
        self.led_seb_listo = LedIndicator()
        ur3_layout.addWidget(self.led_seb_listo)

        ur3_layout.addWidget(QLabel("sebCaja:"))
        self.led_seb_caja = LedIndicator()
        ur3_layout.addWidget(self.led_seb_caja)

        ur3_layout.addWidget(QLabel("UR1:"))
        self.led_ur1 = LedIndicator()
        ur3_layout.addWidget(self.led_ur1)

        ur3_layout.addWidget(QLabel("UR2:"))
        self.led_ur2 = LedIndicator()
        ur3_layout.addWidget(self.led_ur2)

        layout.addWidget(grp_ur3)

    # --- Acciones de botones ---

    def on_inicio(self):
        self._write_coil(ENTRADA_INICIO, True, "INICIO activado")

    def on_stop(self):
        self._write_coil(ENTRADA_STOP, True, "STOP activado")

    def on_banda_izq(self):
        self._write_coil(ENTRADA_BANDA_IZQUIERDA, True, "Banda ← izquierda")

    def on_banda_der(self):
        self._write_coil(ENTRADA_BANDA_DERECHA, True, "Banda → derecha")

    def on_banda_stop(self):
        self._write_coil(ENTRADA_BANDA_STOP, True, "Banda detenida")

    def on_pluma_ini_sube(self):
        self._write_coil(ENTRADA_PLUMA_INICIO_SUBE, True, "Pluma inicio ↑")

    def on_pluma_ini_baja(self):
        self._write_coil(ENTRADA_PLUMA_INICIO_BAJA, True, "Pluma inicio ↓")

    def on_pluma_fin(self):
        self._write_coil(ENTRADA_PLUMA_FIN, True, "Pluma fin toggle")

    def on_torreta_verde(self):
        self._write_coil(ENTRADA_TORRETA_VERDE, True, "Torreta verde ON")

    def on_torreta_amarilla(self):
        self._write_coil(ENTRADA_TORRETA_AMARILLA, True, "Torreta amarilla ON")

    def on_torreta_roja(self):
        self._write_coil(ENTRADA_TORRETA_ROJA, True, "Torreta roja ON")

    def on_vfd_escribir(self):
        text = self.input_vfd.text().strip()
        if not text:
            return
        try:
            value = int(text)
            self.manager.write_register(self.PLC_ID, ENTRADA_VFD_ESCRIBIR, value)
            self.log(f"[ENTRADA] VFD frecuencia escrita: {value}")
        except ValueError:
            self.log("[ENTRADA] Error: frecuencia debe ser un número entero")
        except Exception as e:
            self.log(f"[ENTRADA] Error escribiendo VFD: {e}")

    # --- Polling de estado ---

    def refresh(self):
        """Llamado por el timer para actualizar indicadores."""
        if not self.connected:
            return

        try:
            self.led_verde.update_state(
                self.manager.read_coil(self.PLC_ID, ENTRADA_LAMPARA_VERDE))
            self.led_amarilla.update_state(
                self.manager.read_coil(self.PLC_ID, ENTRADA_LAMPARA_AMARILLA))
            self.led_roja.update_state(
                self.manager.read_coil(self.PLC_ID, ENTRADA_LAMPARA_ROJA))

            self.led_sensor_entrada.update_state(
                self.manager.read_input(self.PLC_ID, ENTRADA_INPUT_SENSOR_ENTRADA))
            self.led_sensor_salida.update_state(
                self.manager.read_input(self.PLC_ID, ENTRADA_INPUT_SENSOR_SALIDA))

            self.led_pluma_ini_arriba.update_state(
                self.manager.read_coil(self.PLC_ID, ENTRADA_PLUMA_INICIO_ARRIBA))
            self.led_pluma_ini_abajo.update_state(
                self.manager.read_coil(self.PLC_ID, ENTRADA_PLUMA_INICIO_ABAJO))
            self.led_pluma_fin_arriba.update_state(
                self.manager.read_coil(self.PLC_ID, ENTRADA_PLUMA_FIN_ARRIBA))
            self.led_pluma_fin_abajo.update_state(
                self.manager.read_coil(self.PLC_ID, ENTRADA_PLUMA_FIN_ABAJO))

            self.led_seb_listo.update_state(
                self.manager.read_coil(self.PLC_ID, ENTRADA_SEB_LISTO))
            self.led_seb_caja.update_state(
                self.manager.read_coil(self.PLC_ID, ENTRADA_SEB_CAJA))
            self.led_ur1.update_state(
                self.manager.read_coil(self.PLC_ID, ENTRADA_UR1))
            self.led_ur2.update_state(
                self.manager.read_coil(self.PLC_ID, ENTRADA_UR2))

            vfd_value = self.manager.read_register(self.PLC_ID, ENTRADA_VFD_LEER)
            self.lbl_vfd_actual.setText(f"{vfd_value} Hz")

        except Exception as e:
            self.log(f"[ENTRADA] Error en refresh: {e}")

    # --- Helpers ---

    def _write_coil(self, address, value, msg):
        try:
            self.manager.write_coil(self.PLC_ID, address, value)
            self.log(f"[ENTRADA] {msg}")
        except Exception as e:
            self.log(f"[ENTRADA] Error: {e}")

    def _btn_style(self, color):
        return (
            f"background-color: {color}; color: white; "
            f"font-size: 12px; padding: 8px 12px; border-radius: 4px;"
        )


class MainWindow(QMainWindow):
    """Ventana principal del SCADA."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("SCADA - Bandas Automatizadas")
        self.setMinimumSize(750, 550)

        self.manager = PLCManager()

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Header con estado de conexión
        header = QHBoxLayout()
        self.lbl_status = QLabel("Desconectado")
        self.lbl_status.setFont(QFont("Arial", 10, QFont.Bold))
        self.lbl_status.setStyleSheet("color: #F44336;")
        header.addStretch()
        header.addWidget(self.lbl_status)

        self.btn_connect = QPushButton("Conectar")
        self.btn_connect.clicked.connect(self.toggle_connection)
        header.addWidget(self.btn_connect)
        main_layout.addLayout(header)

        # Tabs
        self.tabs = QTabWidget()
        self.tab_entrada = EntradaTab(self.manager, self.log_message)
        self.tabs.addTab(self.tab_entrada, "Entrada (HORNER_2)")
        self.tabs.addTab(QWidget(), "Central (HORNER_3)")
        self.tabs.addTab(QWidget(), "Salida (HORNER_1)")
        main_layout.addWidget(self.tabs)

        # Log
        grp_log = QGroupBox("Log")
        log_layout = QVBoxLayout(grp_log)
        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        self.txt_log.setMaximumHeight(100)
        self.txt_log.setFont(QFont("Courier", 9))
        log_layout.addWidget(self.txt_log)
        main_layout.addWidget(grp_log)

        # Timer de polling
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_all)

        self.log_message("Sistema listo. Presiona 'Conectar' para iniciar.")

    def toggle_connection(self):
        if self.btn_connect.text() == "Conectar":
            self.log_message("Conectando a PLCs...")
            try:
                results = self.manager.initialize()
                connected_count = sum(1 for v in results.values() if v)
                total = len(results)

                self.tab_entrada.connected = results.get("HORNER_2", False)

                if connected_count > 0:
                    self.lbl_status.setText(f"Conectado: {connected_count}/{total}")
                    self.lbl_status.setStyleSheet("color: #4CAF50;")
                    self.btn_connect.setText("Desconectar")
                    self.timer.start(500)
                    self.log_message(f"Conexión exitosa: {connected_count}/{total} PLCs")
                else:
                    self.lbl_status.setText("Sin conexión")
                    self.lbl_status.setStyleSheet("color: #F44336;")
                    self.log_message("No se pudo conectar a ningún PLC")

                for plc_id, status in results.items():
                    self.log_message(f"  {plc_id}: {'OK' if status else 'FALLO'}")

            except Exception as e:
                self.log_message(f"Error de conexión: {e}")
        else:
            self.timer.stop()
            self.manager.shutdown()
            self.tab_entrada.connected = False
            self.lbl_status.setText("Desconectado")
            self.lbl_status.setStyleSheet("color: #F44336;")
            self.btn_connect.setText("Conectar")
            self.log_message("Desconectado de todos los PLCs")

    def refresh_all(self):
        self.tab_entrada.refresh()

    def log_message(self, msg):
        self.txt_log.append(msg)
        self.txt_log.verticalScrollBar().setValue(
            self.txt_log.verticalScrollBar().maximum()
        )

    def closeEvent(self, event):
        self.timer.stop()
        self.manager.shutdown()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
