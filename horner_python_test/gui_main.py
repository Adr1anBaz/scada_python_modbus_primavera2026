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
from PySide6.QtGui import QFont, QPalette, QColor

from system import PLCManager
import system.constants as constants


# =============================================================================
# TEMA CLARO MINIMALISTA
# =============================================================================

STYLESHEET = """
QMainWindow, QWidget {
    background-color: #f8f9fa;
    color: #212529;
    font-family: 'Segoe UI', 'Helvetica Neue', sans-serif;
    font-size: 12px;
}

QTabWidget::pane {
    border: 1px solid #dee2e6;
    background-color: #ffffff;
    border-radius: 6px;
}

QTabBar::tab {
    background-color: #e9ecef;
    color: #6c757d;
    padding: 8px 24px;
    margin-right: 2px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    font-weight: bold;
}

QTabBar::tab:selected {
    background-color: #ffffff;
    color: #212529;
    border-bottom: 2px solid #4263eb;
}

QTabBar::tab:hover {
    color: #212529;
    background-color: #f1f3f5;
}

QGroupBox {
    border: 1px solid #dee2e6;
    border-radius: 8px;
    margin-top: 14px;
    padding: 12px 8px 8px 8px;
    background-color: #ffffff;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: #4263eb;
    font-weight: bold;
}

QPushButton {
    background-color: #e9ecef;
    color: #212529;
    border: 1px solid #ced4da;
    border-radius: 6px;
    padding: 8px 18px;
    font-weight: bold;
    min-width: 60px;
    min-height: 30px;
}

QPushButton:hover {
    background-color: #dee2e6;
    border-color: #4263eb;
}

QPushButton:pressed {
    background-color: #4263eb;
    color: #ffffff;
}

QLineEdit {
    background-color: #ffffff;
    border: 1px solid #ced4da;
    border-radius: 6px;
    padding: 6px 8px;
    color: #212529;
}

QLineEdit:focus {
    border-color: #4263eb;
}

QTextEdit {
    background-color: #f1f3f5;
    border: 1px solid #dee2e6;
    border-radius: 6px;
    color: #495057;
    font-family: 'JetBrains Mono', 'Courier New', monospace;
    font-size: 10px;
    padding: 4px;
}

QLabel {
    color: #495057;
    background-color: transparent;
}
"""


def styled_btn(color, text_color="#ffffff"):
    return (
        f"background-color: {color}; color: {text_color}; "
        f"border: none; border-radius: 6px; padding: 8px 18px; "
        f"font-size: 12px; font-weight: bold; min-width: 60px; min-height: 30px;"
    )


def styled_btn_sm(color, text_color="#ffffff"):
    return (
        f"background-color: {color}; color: {text_color}; "
        f"border: none; border-radius: 4px; padding: 4px 10px; "
        f"font-size: 10px; font-weight: bold; min-width: 36px; min-height: 22px;"
    )


def coil_label(address: int) -> str:
    if 6000 <= address < 7000:
        return f"T{address - 6000} ({address})"
    return f"COIL ({address})"


def register_label(address: int) -> str:
    if address >= 3000:
        return f"R{address - 2999} ({address})"
    return f"REG ({address})"


def register_bit_label(address: int, bit: int) -> str:
    if address >= 3000:
        return f"R{address - 2999}.{bit} ({address}.{bit})"
    return f"REG.{bit} ({address}.{bit})"


from system.constants import *


class LedIndicator(QLabel):
    """LED virtual como circulo de color."""

    def __init__(self, text="OFF", parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setFixedSize(20, 20)
        self.set_off()

    def set_on(self, text="ON"):
        self.setStyleSheet(
            "background-color: #2ecc71; border-radius: 10px; border: none;"
        )

    def set_off(self, text="OFF"):
        self.setStyleSheet(
            "background-color: #e74c3c; border-radius: 10px; border: none;"
        )

    def set_warning(self, text="---"):
        self.setStyleSheet(
            "background-color: #f39c12; border-radius: 10px; border: none;"
        )

    def set_inactive(self, text="N/C"):
        self.setStyleSheet(
            "background-color: #bdc3c7; border-radius: 10px; border: none;"
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

        # --- Conexión individual ---
        conn_row = QHBoxLayout()
        self.btn_connect = QPushButton("CONECTAR")
        self.btn_connect.setStyleSheet(styled_btn("#4263eb"))
        self.btn_connect.clicked.connect(self.toggle_connection)
        conn_row.addWidget(self.btn_connect)
        self.lbl_status = QLabel("DESCONECTADO")
        self.lbl_status.setFont(QFont("Segoe UI", 9, QFont.Bold))
        self.lbl_status.setStyleSheet("color: #e03131;")
        conn_row.addWidget(self.lbl_status)
        conn_row.addStretch()
        layout.addLayout(conn_row)

        # --- Fila 1: Control + Lamparas + Torreta ---
        top_row = QHBoxLayout()

        grp_control = QGroupBox("Control")
        ctrl_layout = QHBoxLayout(grp_control)
        self.btn_inicio = QPushButton("INICIO")
        self.btn_inicio.setStyleSheet(self._btn_style("#2f9e44"))
        self.btn_inicio.clicked.connect(self.on_inicio)
        self.btn_stop = QPushButton("STOP")
        self.btn_stop.setStyleSheet(self._btn_style("#e03131"))
        self.btn_stop.clicked.connect(self.on_stop)
        ctrl_layout.addWidget(self.btn_inicio)
        ctrl_layout.addWidget(self.btn_stop)
        top_row.addWidget(grp_control)

        grp_lamparas = QGroupBox("Lamparas")
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

        grp_torreta = QGroupBox("Torreta")
        torreta_layout = QGridLayout(grp_torreta)
        torreta_layout.addWidget(QLabel("Verde:"), 0, 0)
        self.btn_torr_verde = QPushButton("ON")
        self.btn_torr_verde.setStyleSheet(styled_btn_sm("#2f9e44"))
        self.btn_torr_verde.clicked.connect(self.on_torreta_verde)
        torreta_layout.addWidget(self.btn_torr_verde, 0, 1)
        self.btn_torr_verde_off = QPushButton("OFF")
        self.btn_torr_verde_off.setStyleSheet(styled_btn_sm("#868e96"))
        self.btn_torr_verde_off.clicked.connect(self.on_torreta_verde_off)
        torreta_layout.addWidget(self.btn_torr_verde_off, 0, 2)

        torreta_layout.addWidget(QLabel("Amarillo:"), 1, 0)
        self.btn_torr_amarilla = QPushButton("ON")
        self.btn_torr_amarilla.setStyleSheet(styled_btn_sm("#f08c00"))
        self.btn_torr_amarilla.clicked.connect(self.on_torreta_amarilla)
        torreta_layout.addWidget(self.btn_torr_amarilla, 1, 1)
        self.btn_torr_amarilla_off = QPushButton("OFF")
        self.btn_torr_amarilla_off.setStyleSheet(styled_btn_sm("#868e96"))
        self.btn_torr_amarilla_off.clicked.connect(self.on_torreta_amarilla_off)
        torreta_layout.addWidget(self.btn_torr_amarilla_off, 1, 2)

        torreta_layout.addWidget(QLabel("Roja:"), 2, 0)
        self.btn_torr_roja = QPushButton("ON")
        self.btn_torr_roja.setStyleSheet(styled_btn_sm("#e03131"))
        self.btn_torr_roja.clicked.connect(self.on_torreta_roja)
        torreta_layout.addWidget(self.btn_torr_roja, 2, 1)
        self.btn_torr_roja_off = QPushButton("OFF")
        self.btn_torr_roja_off.setStyleSheet(styled_btn_sm("#868e96"))
        self.btn_torr_roja_off.clicked.connect(self.on_torreta_roja_off)
        torreta_layout.addWidget(self.btn_torr_roja_off, 2, 2)
        top_row.addWidget(grp_torreta)

        layout.addLayout(top_row)

        # --- Fila 2: Banda + Plumas ---
        mid_row = QHBoxLayout()

        grp_banda = QGroupBox("Banda")
        banda_layout = QVBoxLayout(grp_banda)
        banda_btns = QHBoxLayout()
        self.btn_banda_izq = QPushButton("Izq")
        self.btn_banda_izq.setStyleSheet(self._btn_style("#1c7ed6"))
        self.btn_banda_izq.clicked.connect(self.on_banda_izq)
        self.btn_banda_stop = QPushButton("Stop")
        self.btn_banda_stop.setStyleSheet(self._btn_style("#868e96"))
        self.btn_banda_stop.clicked.connect(self.on_banda_stop)
        self.btn_banda_der = QPushButton("Der")
        self.btn_banda_der.setStyleSheet(self._btn_style("#1c7ed6"))
        self.btn_banda_der.clicked.connect(self.on_banda_der)
        banda_btns.addWidget(self.btn_banda_izq)
        banda_btns.addWidget(self.btn_banda_stop)
        banda_btns.addWidget(self.btn_banda_der)
        banda_layout.addLayout(banda_btns)

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
        self.lbl_vfd_actual.setFont(QFont("Segoe UI", 10, QFont.Bold))
        vfd_row.addWidget(self.lbl_vfd_actual)
        vfd_row.addStretch()
        banda_layout.addLayout(vfd_row)
        mid_row.addWidget(grp_banda)

        grp_plumas = QGroupBox("Plumas")
        plumas_layout = QGridLayout(grp_plumas)
        plumas_layout.addWidget(QLabel("Inicio:"), 0, 0)
        self.btn_pluma_ini_sube = QPushButton("Sube")
        self.btn_pluma_ini_sube.setStyleSheet(self._btn_style("#1c7ed6"))
        self.btn_pluma_ini_sube.clicked.connect(self.on_pluma_ini_sube)
        plumas_layout.addWidget(self.btn_pluma_ini_sube, 0, 1)
        self.btn_pluma_ini_baja = QPushButton("Baja")
        self.btn_pluma_ini_baja.setStyleSheet(self._btn_style("#1c7ed6"))
        self.btn_pluma_ini_baja.clicked.connect(self.on_pluma_ini_baja)
        plumas_layout.addWidget(self.btn_pluma_ini_baja, 0, 2)
        plumas_layout.addWidget(QLabel("Fin:"), 1, 0)
        self.btn_pluma_fin = QPushButton("Toggle")
        self.btn_pluma_fin.setStyleSheet(self._btn_style("#1c7ed6"))
        self.btn_pluma_fin.clicked.connect(self.on_pluma_fin)
        plumas_layout.addWidget(self.btn_pluma_fin, 1, 1)
        mid_row.addWidget(grp_plumas)

        layout.addLayout(mid_row)

        # --- Fila 3: Sensores + UR3 ---
        bot_row = QHBoxLayout()

        grp_sensores = QGroupBox("Sensores")
        sensores_layout = QGridLayout(grp_sensores)
        sensores_layout.addWidget(QLabel("I4 Entrada:"), 0, 0)
        self.led_sensor_entrada = LedIndicator()
        sensores_layout.addWidget(self.led_sensor_entrada, 0, 1)
        sensores_layout.addWidget(QLabel("I5 Salida:"), 0, 2)
        self.led_sensor_salida = LedIndicator()
        sensores_layout.addWidget(self.led_sensor_salida, 0, 3)
        sensores_layout.addWidget(QLabel("Pluma ini arr:"), 1, 0)
        self.led_pluma_ini_arriba = LedIndicator()
        sensores_layout.addWidget(self.led_pluma_ini_arriba, 1, 1)
        sensores_layout.addWidget(QLabel("Pluma ini abj:"), 1, 2)
        self.led_pluma_ini_abajo = LedIndicator()
        sensores_layout.addWidget(self.led_pluma_ini_abajo, 1, 3)
        sensores_layout.addWidget(QLabel("Pluma fin arr:"), 2, 0)
        self.led_pluma_fin_arriba = LedIndicator()
        sensores_layout.addWidget(self.led_pluma_fin_arriba, 2, 1)
        sensores_layout.addWidget(QLabel("Pluma fin abj:"), 2, 2)
        self.led_pluma_fin_abajo = LedIndicator()
        sensores_layout.addWidget(self.led_pluma_fin_abajo, 2, 3)
        bot_row.addWidget(grp_sensores)

        grp_ur3 = QGroupBox("UR3 / Integracion")
        ur3_layout = QGridLayout(grp_ur3)
        ur3_layout.addWidget(QLabel("sebListo:"), 0, 0)
        self.led_seb_listo = LedIndicator()
        ur3_layout.addWidget(self.led_seb_listo, 0, 1)
        ur3_layout.addWidget(QLabel("sebCaja:"), 0, 2)
        self.led_seb_caja = LedIndicator()
        ur3_layout.addWidget(self.led_seb_caja, 0, 3)
        ur3_layout.addWidget(QLabel("UR1:"), 1, 0)
        self.led_ur1 = LedIndicator()
        ur3_layout.addWidget(self.led_ur1, 1, 1)
        ur3_layout.addWidget(QLabel("UR2:"), 1, 2)
        self.led_ur2 = LedIndicator()
        ur3_layout.addWidget(self.led_ur2, 1, 3)
        bot_row.addWidget(grp_ur3)

        layout.addLayout(bot_row)

    # --- Acciones de botones ---

    def on_inicio(self):
        self._pulse_coil(ENTRADA_INICIO, "INICIO activado")

    def on_stop(self):
        self._pulse_coil(ENTRADA_STOP, "STOP activado")

    def on_banda_izq(self):
        self._pulse_coil(ENTRADA_BANDA_IZQUIERDA, "Banda izquierda")

    def on_banda_der(self):
        self._pulse_coil(ENTRADA_BANDA_DERECHA, "Banda derecha")

    def on_banda_stop(self):
        self._pulse_coil(ENTRADA_BANDA_STOP, "Banda detenida")

    def on_pluma_ini_sube(self):
        self._pulse_coil(ENTRADA_PLUMA_INICIO_SUBE, "Pluma inicio sube")

    def on_pluma_ini_baja(self):
        self._pulse_coil(ENTRADA_PLUMA_INICIO_BAJA, "Pluma inicio baja")

    def on_pluma_fin(self):
        self._pulse_coil(ENTRADA_PLUMA_FIN, "Pluma fin toggle")

    def on_torreta_verde(self):
        self._write_coil(ENTRADA_TORRETA_VERDE, True, "Torreta verde ON")

    def on_torreta_verde_off(self):
        self._write_coil(ENTRADA_TORRETA_VERDE, False, "Torreta verde OFF")

    def on_torreta_amarilla(self):
        self._write_coil(ENTRADA_TORRETA_AMARILLA, True, "Torreta amarilla ON")

    def on_torreta_amarilla_off(self):
        self._write_coil(ENTRADA_TORRETA_AMARILLA, False, "Torreta amarilla OFF")

    def on_torreta_roja(self):
        self._write_coil(ENTRADA_TORRETA_ROJA, True, "Torreta roja ON")

    def on_torreta_roja_off(self):
        self._write_coil(ENTRADA_TORRETA_ROJA, False, "Torreta roja OFF")

    def on_vfd_escribir(self):
        text = self.input_vfd.text().strip()
        if not text:
            return
        try:
            value = int(text)
            self.manager.write_register(self.PLC_ID, ENTRADA_VFD_ESCRIBIR, value)
            self.log(
                f"[ENTRADA] VFD frecuencia escrita: {value} | "
                f"{register_label(ENTRADA_VFD_ESCRIBIR)}={value}"
            )
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
            state = "ON" if value else "OFF"
            self.log(f"[ENTRADA] {msg} | {coil_label(address)}={state}")
        except Exception as e:
            self.log(f"[ENTRADA] Error: {e}")

    def _pulse_coil(self, address, msg):
        try:
            self._write_coil(address, True, f"{msg} (pulso)")
            QTimer.singleShot(100, lambda: self._write_coil(address, False, f"{msg} OFF"))
        except Exception as e:
            self.log(f"[ENTRADA] Error: {e}")

    def toggle_connection(self):
        if not self.connected:
            try:
                result = self.manager.connect_device(self.PLC_ID)
                self.connected = result
                if result:
                    self.btn_connect.setText("DESCONECTAR")
                    self.btn_connect.setStyleSheet(styled_btn("#e03131"))
                    self.lbl_status.setText("ONLINE")
                    self.lbl_status.setStyleSheet("color: #2f9e44;")
                    self.log(f"[ENTRADA] Conectado a {self.PLC_ID}")
                else:
                    self.lbl_status.setText("FALLO")
                    self.lbl_status.setStyleSheet("color: #e03131;")
                    self.log(f"[ENTRADA] No se pudo conectar a {self.PLC_ID}")
            except Exception as e:
                self.log(f"[ENTRADA] Error conectando: {e}")
        else:
            self.manager.disconnect_device(self.PLC_ID)
            self.connected = False
            self.btn_connect.setText("CONECTAR")
            self.btn_connect.setStyleSheet(styled_btn("#4263eb"))
            self.lbl_status.setText("DESCONECTADO")
            self.lbl_status.setStyleSheet("color: #e03131;")
            self.log(f"[ENTRADA] Desconectado de {self.PLC_ID}")

    def _btn_style(self, color):
        return styled_btn(color)


class CentralTab(QWidget):
    """Tab para el PLC Central (HORNER_3 - 192.168.3.133). Banda rotatoria."""

    PLC_ID = "HORNER_3"

    def __init__(self, manager: PLCManager, log_callback):
        super().__init__()
        self.manager = manager
        self.log = log_callback
        self.connected = False
        self.setup_ui()

        self.fast_timer = QTimer(self)
        self.fast_timer.timeout.connect(self._poll_mode)
        self.fast_timer.start(80)

    def _poll_mode(self):
        if not self.connected:
            return
        try:
            prueba_active = self.manager.read_coil(self.PLC_ID, CENTRAL_MODO_PRUEBA_ACTIVO)
            if prueba_active != self.btn_t51.isChecked():
                self.btn_t51.blockSignals(True)
                self.btn_t51.setChecked(prueba_active)
                self.btn_t51.blockSignals(False)
                self._set_prueba_enabled(prueba_active)
        except Exception:
            pass

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # --- Conexión individual ---
        conn_row = QHBoxLayout()
        self.btn_connect = QPushButton("CONECTAR")
        self.btn_connect.setStyleSheet(styled_btn("#4263eb"))
        self.btn_connect.clicked.connect(self.toggle_connection)
        conn_row.addWidget(self.btn_connect)
        self.lbl_status = QLabel("DESCONECTADO")
        self.lbl_status.setFont(QFont("Segoe UI", 9, QFont.Bold))
        self.lbl_status.setStyleSheet("color: #e03131;")
        conn_row.addWidget(self.lbl_status)
        conn_row.addStretch()
        layout.addLayout(conn_row)

        # --- Fila superior: Modos + Control + Pilotos ---
        top_row = QHBoxLayout()

        grp_modos = QGroupBox("Navegación")
        modos_layout = QHBoxLayout(grp_modos)

        self.btn_modo_proceso = QPushButton("Proceso")
        self.btn_modo_proceso.setStyleSheet(self._btn_style("#2f9e44"))
        self.btn_modo_proceso.clicked.connect(self.on_modo_proceso)
        modos_layout.addWidget(self.btn_modo_proceso)

        self.btn_modo_integracion = QPushButton("Integración")
        self.btn_modo_integracion.setStyleSheet(self._btn_style("#1c7ed6"))
        self.btn_modo_integracion.clicked.connect(self.on_modo_integracion)
        modos_layout.addWidget(self.btn_modo_integracion)

        self.btn_t51 = QPushButton("Prueba")
        self.btn_t51.setCheckable(True)
        self.btn_t51.setStyleSheet(self._btn_style("#7048e8"))
        self.btn_t51.toggled.connect(self.on_modo_prueba)
        modos_layout.addWidget(self.btn_t51)

        self.btn_menu = QPushButton("Menú")
        self.btn_menu.setStyleSheet(self._btn_style("#868e96"))
        self.btn_menu.clicked.connect(self.on_menu)
        modos_layout.addWidget(self.btn_menu)

        top_row.addWidget(grp_modos)

        grp_control = QGroupBox("Control (Proceso/Integración)")
        ctrl_layout = QHBoxLayout(grp_control)

        self.btn_stop = QPushButton("STOP")
        self.btn_stop.setStyleSheet(self._btn_style("#e03131"))
        self.btn_stop.clicked.connect(self.on_stop)
        ctrl_layout.addWidget(self.btn_stop)

        self.btn_llego_caja = QPushButton("Llegó caja")
        self.btn_llego_caja.setStyleSheet(self._btn_style("#7048e8"))
        self.btn_llego_caja.clicked.connect(self.on_llego_caja)
        ctrl_layout.addWidget(self.btn_llego_caja)

        self.btn_recibio_b3 = QPushButton("Recibió B3")
        self.btn_recibio_b3.setStyleSheet(self._btn_style("#7048e8"))
        self.btn_recibio_b3.clicked.connect(self.on_recibio_b3)
        ctrl_layout.addWidget(self.btn_recibio_b3)

        self.btn_ur3_fin = QPushButton("UR3 Fin")
        self.btn_ur3_fin.setStyleSheet(self._btn_style("#7048e8"))
        self.btn_ur3_fin.clicked.connect(self.on_ur3_fin)
        ctrl_layout.addWidget(self.btn_ur3_fin)

        self.btn_banda3_lista = QPushButton("B3 Lista")
        self.btn_banda3_lista.setStyleSheet(self._btn_style("#7048e8"))
        self.btn_banda3_lista.clicked.connect(self.on_banda3_lista)
        ctrl_layout.addWidget(self.btn_banda3_lista)

        top_row.addWidget(grp_control)

        grp_pilotos = QGroupBox("Pilotos de Estado")
        pilotos_layout = QHBoxLayout(grp_pilotos)

        pilotos_layout.addWidget(QLabel("Recibido:"))
        self.led_recibido = LedIndicator()
        pilotos_layout.addWidget(self.led_recibido)

        pilotos_layout.addWidget(QLabel("Listo para empezar:"))
        self.led_listo = LedIndicator()
        pilotos_layout.addWidget(self.led_listo)

        top_row.addWidget(grp_pilotos)
        layout.addLayout(top_row)

        # --- Fila media: Rotador + Banda (solo modo prueba) ---
        mid_row = QHBoxLayout()

        grp_rotador = QGroupBox("Rotador (Modo Prueba)")
        rot_layout = QHBoxLayout(grp_rotador)

        self.btn_rot_anti = QPushButton("Antihorario")
        self.btn_rot_anti.setStyleSheet(self._btn_style("#1c7ed6"))
        self.btn_rot_anti.clicked.connect(self.on_rotador_anti)
        rot_layout.addWidget(self.btn_rot_anti)

        self.btn_rot_stop = QPushButton("Stop")
        self.btn_rot_stop.setStyleSheet(self._btn_style("#868e96"))
        self.btn_rot_stop.clicked.connect(self.on_rotador_stop)
        rot_layout.addWidget(self.btn_rot_stop)

        self.btn_rot_hora = QPushButton("Horario")
        self.btn_rot_hora.setStyleSheet(self._btn_style("#1c7ed6"))
        self.btn_rot_hora.clicked.connect(self.on_rotador_hora)
        rot_layout.addWidget(self.btn_rot_hora)

        mid_row.addWidget(grp_rotador)

        grp_banda = QGroupBox("Banda (Modo Prueba)")
        banda_layout = QHBoxLayout(grp_banda)

        self.btn_banda_atras = QPushButton("Atras")
        self.btn_banda_atras.setStyleSheet(self._btn_style("#1c7ed6"))
        self.btn_banda_atras.clicked.connect(self.on_banda_atras)
        banda_layout.addWidget(self.btn_banda_atras)

        self.btn_banda_stop = QPushButton("Stop")
        self.btn_banda_stop.setStyleSheet(self._btn_style("#868e96"))
        self.btn_banda_stop.clicked.connect(self.on_banda_stop)
        banda_layout.addWidget(self.btn_banda_stop)

        self.btn_banda_adelante = QPushButton("Adelante")
        self.btn_banda_adelante.setStyleSheet(self._btn_style("#1c7ed6"))
        self.btn_banda_adelante.clicked.connect(self.on_banda_adelante)
        banda_layout.addWidget(self.btn_banda_adelante)

        mid_row.addWidget(grp_banda)
        layout.addLayout(mid_row)

        # --- Fila inferior: Torreta + Diagnóstico ---
        bot_row = QHBoxLayout()

        grp_torreta = QGroupBox("Torreta")
        torreta_layout = QGridLayout(grp_torreta)

        torreta_layout.addWidget(QLabel("Verde:"), 0, 0)
        self.btn_torr_verde = QPushButton("ON")
        self.btn_torr_verde.setStyleSheet(styled_btn_sm("#2f9e44"))
        self.btn_torr_verde.clicked.connect(self.on_torreta_verde)
        torreta_layout.addWidget(self.btn_torr_verde, 0, 1)
        self.btn_torr_verde_off = QPushButton("OFF")
        self.btn_torr_verde_off.setStyleSheet(styled_btn_sm("#868e96"))
        self.btn_torr_verde_off.clicked.connect(self.on_torreta_verde_off)
        torreta_layout.addWidget(self.btn_torr_verde_off, 0, 2)

        torreta_layout.addWidget(QLabel("Amarillo:"), 1, 0)
        self.btn_torr_amarillo = QPushButton("ON")
        self.btn_torr_amarillo.setStyleSheet(styled_btn_sm("#f08c00"))
        self.btn_torr_amarillo.clicked.connect(self.on_torreta_amarillo)
        torreta_layout.addWidget(self.btn_torr_amarillo, 1, 1)
        self.btn_torr_amarillo_off = QPushButton("OFF")
        self.btn_torr_amarillo_off.setStyleSheet(styled_btn_sm("#868e96"))
        self.btn_torr_amarillo_off.clicked.connect(self.on_torreta_amarillo_off)
        torreta_layout.addWidget(self.btn_torr_amarillo_off, 1, 2)

        torreta_layout.addWidget(QLabel("Rojo:"), 2, 0)
        self.btn_torr_rojo = QPushButton("ON")
        self.btn_torr_rojo.setStyleSheet(styled_btn_sm("#e03131"))
        self.btn_torr_rojo.clicked.connect(self.on_torreta_rojo)
        torreta_layout.addWidget(self.btn_torr_rojo, 2, 1)
        self.btn_torr_rojo_off = QPushButton("OFF")
        self.btn_torr_rojo_off.setStyleSheet(styled_btn_sm("#868e96"))
        self.btn_torr_rojo_off.clicked.connect(self.on_torreta_rojo_off)
        torreta_layout.addWidget(self.btn_torr_rojo_off, 2, 2)

        bot_row.addWidget(grp_torreta)

        grp_diag = QGroupBox("Diagnóstico (lectura)")
        diag_layout = QGridLayout(grp_diag)

        diag_layout.addWidget(QLabel("Sen. Entrada:"), 0, 0)
        self.led_diag_entrada = LedIndicator()
        diag_layout.addWidget(self.led_diag_entrada, 0, 1)

        diag_layout.addWidget(QLabel("Sen. Salida:"), 0, 2)
        self.led_diag_salida = LedIndicator()
        diag_layout.addWidget(self.led_diag_salida, 0, 3)

        diag_layout.addWidget(QLabel("Sen. Giro:"), 0, 4)
        self.led_diag_giro = LedIndicator()
        diag_layout.addWidget(self.led_diag_giro, 0, 5)

        diag_layout.addWidget(QLabel("Btn Verde:"), 1, 0)
        self.led_diag_btn_verde = LedIndicator()
        diag_layout.addWidget(self.led_diag_btn_verde, 1, 1)

        diag_layout.addWidget(QLabel("Btn Rojo:"), 1, 2)
        self.led_diag_btn_rojo = LedIndicator()
        diag_layout.addWidget(self.led_diag_btn_rojo, 1, 3)

        diag_layout.addWidget(QLabel("Btn Paro:"), 1, 4)
        self.led_diag_btn_paro = LedIndicator()
        diag_layout.addWidget(self.led_diag_btn_paro, 1, 5)

        bot_row.addWidget(grp_diag)
        layout.addLayout(bot_row)

        # --- Botones de modo prueba empiezan deshabilitados ---
        self._set_prueba_enabled(False)

    def _set_prueba_enabled(self, enabled):
        disabled_style = styled_btn_sm("#bdc3c7", "#6c757d")
        btn_styles = {
            self.btn_rot_anti: self._btn_style("#1c7ed6"),
            self.btn_rot_stop: self._btn_style("#868e96"),
            self.btn_rot_hora: self._btn_style("#1c7ed6"),
            self.btn_banda_atras: self._btn_style("#1c7ed6"),
            self.btn_banda_stop: self._btn_style("#868e96"),
            self.btn_banda_adelante: self._btn_style("#1c7ed6"),
            self.btn_torr_verde: styled_btn_sm("#2f9e44"),
            self.btn_torr_verde_off: styled_btn_sm("#868e96"),
            self.btn_torr_amarillo: styled_btn_sm("#f08c00"),
            self.btn_torr_amarillo_off: styled_btn_sm("#868e96"),
            self.btn_torr_rojo: styled_btn_sm("#e03131"),
            self.btn_torr_rojo_off: styled_btn_sm("#868e96"),
        }
        for btn, active_style in btn_styles.items():
            btn.setEnabled(enabled)
            btn.setStyleSheet(active_style if enabled else disabled_style)

    # --- Acciones de botones ---

    def on_stop(self):
        self._pulse_coil(CENTRAL_STOP, "STOP activado")

    def on_llego_caja(self):
        self._pulse_coil(CENTRAL_LLEGO_CAJA, "Señal: llegó caja")

    def on_recibio_b3(self):
        self._pulse_coil(CENTRAL_RECIBIO_BANDA3, "Señal: recibió banda 3")

    def on_ur3_fin(self):
        self._pulse_coil(CENTRAL_UR3_FIN, "Señal: UR3 fin")

    def on_banda3_lista(self):
        self._pulse_coil(CENTRAL_BANDA3_LISTA, "Señal: Banda 3 lista (T98)")

    def on_modo_proceso(self):
        self._pulse_coil(CENTRAL_MODO_PROCESO, "Modo Proceso (T76)")

    def on_modo_integracion(self):
        self._pulse_coil(CENTRAL_MODO_INTEGRACION, "Modo Integración (T70)")

    def on_modo_prueba(self, checked):
        if checked:
            self._write_coil(CENTRAL_MODO_PRUEBA, True, "T51 ON")
            QTimer.singleShot(50, lambda: self._write_coil(CENTRAL_MODO_PRUEBA, False, "T51 OFF (toggle)"))
        self._set_prueba_enabled(checked)

    def on_menu(self):
        self._write_coil(CENTRAL_MENU, True, "Menú (T53)")
        self._write_coil(CENTRAL_MODO_PROCESO, True, "T76 pulso")
        self._write_coil(CENTRAL_MODO_INTEGRACION, True, "T70 pulso")
        self._write_coil(CENTRAL_MODO_PRUEBA, True, "T51 pulso")
        QTimer.singleShot(50, self._menu_release)
        self.btn_t51.blockSignals(True)
        self.btn_t51.setChecked(False)
        self.btn_t51.blockSignals(False)
        self._set_prueba_enabled(False)

    def _menu_release(self):
        self._write_coil(CENTRAL_MENU, False, "T53 OFF")
        self._write_coil(CENTRAL_MODO_PROCESO, False, "T76 OFF")
        self._write_coil(CENTRAL_MODO_INTEGRACION, False, "T70 OFF")
        self._write_coil(CENTRAL_MODO_PRUEBA, False, "T51 OFF")

    def on_rotador_anti(self):
        self._pulse_coil(CENTRAL_ROTADOR_ANTIHORARIO, "Rotador antihorario")

    def on_rotador_stop(self):
        self._pulse_coil(CENTRAL_ROTADOR_STOP, "Rotador detenido")

    def on_rotador_hora(self):
        self._pulse_coil(CENTRAL_ROTADOR_HORARIO, "Rotador horario")

    def on_banda_atras(self):
        self._pulse_coil(CENTRAL_BANDA_ATRAS, "Banda atras")

    def on_banda_stop(self):
        self._pulse_coil(CENTRAL_BANDA_STOP, "Banda detenida")

    def on_banda_adelante(self):
        self._pulse_coil(CENTRAL_BANDA_ADELANTE, "Banda adelante")

    def on_torreta_verde(self):
        self._write_coil(CENTRAL_TORRETA_VERDE, True, "Torreta verde ON")

    def on_torreta_verde_off(self):
        self._write_coil(CENTRAL_TORRETA_VERDE, False, "Torreta verde OFF")

    def on_torreta_amarillo(self):
        self._write_coil(CENTRAL_TORRETA_AMARILLO, True, "Torreta amarillo ON")

    def on_torreta_amarillo_off(self):
        self._write_coil(CENTRAL_TORRETA_AMARILLO, False, "Torreta amarillo OFF")

    def on_torreta_rojo(self):
        self._write_coil(CENTRAL_TORRETA_ROJO, True, "Torreta rojo ON")

    def on_torreta_rojo_off(self):
        self._write_coil(CENTRAL_TORRETA_ROJO, False, "Torreta rojo OFF")

    # --- Polling de estado ---

    def refresh(self):
        """Llamado por el timer para actualizar indicadores."""
        if not self.connected:
            return

        try:
            self.led_recibido.update_state(
                self.manager.read_coil(self.PLC_ID, CENTRAL_PILOTO_RECIBIDO))
            self.led_listo.update_state(
                self.manager.read_coil(self.PLC_ID, CENTRAL_PILOTO_LISTO))

            self.led_diag_entrada.update_state(
                self.manager.read_coil(self.PLC_ID, CENTRAL_PILOTO_SENSOR_ENTRADA))
            self.led_diag_salida.update_state(
                self.manager.read_coil(self.PLC_ID, CENTRAL_PILOTO_SENSOR_SALIDA))
            self.led_diag_giro.update_state(
                self.manager.read_coil(self.PLC_ID, CENTRAL_PILOTO_SENSOR_GIRO))
            self.led_diag_btn_verde.update_state(
                self.manager.read_coil(self.PLC_ID, CENTRAL_PILOTO_BOTON_VERDE))
            self.led_diag_btn_rojo.update_state(
                self.manager.read_coil(self.PLC_ID, CENTRAL_PILOTO_BOTON_ROJO))
            self.led_diag_btn_paro.update_state(
                self.manager.read_coil(self.PLC_ID, CENTRAL_PILOTO_BOTON_PARO))

        except Exception as e:
            self.log(f"[CENTRAL] Error en refresh: {e}")

    # --- Helpers ---

    def _write_coil(self, address, value, msg):
        try:
            self.manager.write_coil(self.PLC_ID, address, value)
            state = "ON" if value else "OFF"
            self.log(f"[CENTRAL] {msg} | {coil_label(address)}={state}")
        except Exception as e:
            self.log(f"[CENTRAL] Error: {e}")

    def _pulse_coil(self, address, msg):
        try:
            self._write_coil(address, True, f"{msg} (pulso)")
            QTimer.singleShot(100, lambda: self._write_coil(address, False, f"{msg} OFF"))
        except Exception as e:
            self.log(f"[CENTRAL] Error: {e}")

    def toggle_connection(self):
        if not self.connected:
            try:
                result = self.manager.connect_device(self.PLC_ID)
                self.connected = result
                if result:
                    self.btn_connect.setText("DESCONECTAR")
                    self.btn_connect.setStyleSheet(styled_btn("#e03131"))
                    self.lbl_status.setText("ONLINE")
                    self.lbl_status.setStyleSheet("color: #2f9e44;")
                    self.log(f"[CENTRAL] Conectado a {self.PLC_ID}")
                else:
                    self.lbl_status.setText("FALLO")
                    self.lbl_status.setStyleSheet("color: #e03131;")
                    self.log(f"[CENTRAL] No se pudo conectar a {self.PLC_ID}")
            except Exception as e:
                self.log(f"[CENTRAL] Error conectando: {e}")
        else:
            self.manager.disconnect_device(self.PLC_ID)
            self.connected = False
            self.btn_connect.setText("CONECTAR")
            self.btn_connect.setStyleSheet(styled_btn("#4263eb"))
            self.lbl_status.setText("DESCONECTADO")
            self.lbl_status.setStyleSheet("color: #e03131;")
            self.log(f"[CENTRAL] Desconectado de {self.PLC_ID}")

    def _btn_style(self, color):
        return styled_btn(color)


class SalidaTab(QWidget):
    """Tab para el PLC de Salida (HORNER_1 - 192.168.3.131). Banda de salida."""

    PLC_ID = "HORNER_1"

    def __init__(self, manager: PLCManager, log_callback):
        super().__init__()
        self.manager = manager
        self.log = log_callback
        self.connected = False
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # --- Conexión individual ---
        conn_row = QHBoxLayout()
        self.btn_connect = QPushButton("CONECTAR")
        self.btn_connect.setStyleSheet(styled_btn("#4263eb"))
        self.btn_connect.clicked.connect(self.toggle_connection)
        conn_row.addWidget(self.btn_connect)
        self.lbl_status = QLabel("DESCONECTADO")
        self.lbl_status.setFont(QFont("Segoe UI", 9, QFont.Bold))
        self.lbl_status.setStyleSheet("color: #e03131;")
        conn_row.addWidget(self.lbl_status)
        conn_row.addStretch()
        layout.addLayout(conn_row)

        # --- Fila superior: Control + LEDs ---
        top_row = QHBoxLayout()

        grp_control = QGroupBox("Control")
        ctrl_layout = QHBoxLayout(grp_control)

        self.btn_init = QPushButton("Init Proceso")
        self.btn_init.setStyleSheet(self._btn_style("#2f9e44"))
        self.btn_init.clicked.connect(self.on_init_proceso)
        ctrl_layout.addWidget(self.btn_init)

        self.btn_stop = QPushButton("STOP")
        self.btn_stop.setStyleSheet(self._btn_style("#e03131"))
        self.btn_stop.clicked.connect(self.on_stop)
        ctrl_layout.addWidget(self.btn_stop)

        top_row.addWidget(grp_control)

        grp_leds = QGroupBox("LEDs")
        leds_layout = QGridLayout(grp_leds)

        leds_layout.addWidget(QLabel("Verde:"), 0, 0)
        self.btn_led_verde = QPushButton("ON")
        self.btn_led_verde.setStyleSheet(styled_btn_sm("#2f9e44"))
        self.btn_led_verde.clicked.connect(self.on_led_verde)
        leds_layout.addWidget(self.btn_led_verde, 0, 1)
        self.btn_led_verde_off = QPushButton("OFF")
        self.btn_led_verde_off.setStyleSheet(styled_btn_sm("#868e96"))
        self.btn_led_verde_off.clicked.connect(self.on_led_verde_off)
        leds_layout.addWidget(self.btn_led_verde_off, 0, 2)

        leds_layout.addWidget(QLabel("Amarillo:"), 1, 0)
        self.btn_led_amarillo = QPushButton("ON")
        self.btn_led_amarillo.setStyleSheet(styled_btn_sm("#f08c00"))
        self.btn_led_amarillo.clicked.connect(self.on_led_amarillo)
        leds_layout.addWidget(self.btn_led_amarillo, 1, 1)
        self.btn_led_amarillo_off = QPushButton("OFF")
        self.btn_led_amarillo_off.setStyleSheet(styled_btn_sm("#868e96"))
        self.btn_led_amarillo_off.clicked.connect(self.on_led_amarillo_off)
        leds_layout.addWidget(self.btn_led_amarillo_off, 1, 2)

        leds_layout.addWidget(QLabel("Rojo:"), 2, 0)
        self.btn_led_rojo = QPushButton("ON")
        self.btn_led_rojo.setStyleSheet(styled_btn_sm("#e03131"))
        self.btn_led_rojo.clicked.connect(self.on_led_rojo)
        leds_layout.addWidget(self.btn_led_rojo, 2, 1)
        self.btn_led_rojo_off = QPushButton("OFF")
        self.btn_led_rojo_off.setStyleSheet(styled_btn_sm("#868e96"))
        self.btn_led_rojo_off.clicked.connect(self.on_led_rojo_off)
        leds_layout.addWidget(self.btn_led_rojo_off, 2, 2)

        top_row.addWidget(grp_leds)
        layout.addLayout(top_row)

        # --- Fila media: Banda + Plumas ---
        mid_row = QHBoxLayout()

        grp_banda = QGroupBox("Banda")
        banda_layout = QVBoxLayout(grp_banda)

        banda_btns = QHBoxLayout()
        self.btn_banda_izq = QPushButton("Izq")
        self.btn_banda_izq.setStyleSheet(self._btn_style("#1c7ed6"))
        self.btn_banda_izq.clicked.connect(self.on_banda_izq)
        banda_btns.addWidget(self.btn_banda_izq)

        self.btn_banda_off = QPushButton("Off")
        self.btn_banda_off.setStyleSheet(self._btn_style("#868e96"))
        self.btn_banda_off.clicked.connect(self.on_banda_off)
        banda_btns.addWidget(self.btn_banda_off)

        self.btn_banda_der = QPushButton("Der")
        self.btn_banda_der.setStyleSheet(self._btn_style("#1c7ed6"))
        self.btn_banda_der.clicked.connect(self.on_banda_der)
        banda_btns.addWidget(self.btn_banda_der)

        self.btn_banda_t12 = QPushButton("T12")
        self.btn_banda_t12.setCheckable(True)
        self.btn_banda_t12.setStyleSheet(self._btn_style("#7048e8"))
        self.btn_banda_t12.toggled.connect(self.on_banda_salida)
        banda_btns.addWidget(self.btn_banda_t12)

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

        vfd_row.addWidget(QLabel("Estado:"))
        self.lbl_maquina_estados = QLabel("---")
        self.lbl_maquina_estados.setFont(QFont("Arial", 10, QFont.Bold))
        vfd_row.addWidget(self.lbl_maquina_estados)
        vfd_row.addStretch()

        banda_layout.addLayout(vfd_row)
        mid_row.addWidget(grp_banda)

        grp_plumas = QGroupBox("Plumas")
        plumas_layout = QGridLayout(grp_plumas)

        plumas_layout.addWidget(QLabel("Entrada:"), 0, 0)
        self.btn_pluma_ent_abrir = QPushButton("Abrir")
        self.btn_pluma_ent_abrir.setStyleSheet(self._btn_style("#2f9e44"))
        self.btn_pluma_ent_abrir.clicked.connect(self.on_pluma_entrada_abrir)
        plumas_layout.addWidget(self.btn_pluma_ent_abrir, 0, 1)

        self.btn_pluma_ent_cerrar = QPushButton("Cerrar")
        self.btn_pluma_ent_cerrar.setStyleSheet(self._btn_style("#e03131"))
        self.btn_pluma_ent_cerrar.clicked.connect(self.on_pluma_entrada_cerrar)
        plumas_layout.addWidget(self.btn_pluma_ent_cerrar, 0, 2)

        plumas_layout.addWidget(QLabel("Salida:"), 1, 0)
        self.btn_pluma_sal_abrir = QPushButton("Abrir")
        self.btn_pluma_sal_abrir.setStyleSheet(self._btn_style("#2f9e44"))
        self.btn_pluma_sal_abrir.clicked.connect(self.on_pluma_salida_abrir)
        plumas_layout.addWidget(self.btn_pluma_sal_abrir, 1, 1)

        self.btn_pluma_sal_cerrar = QPushButton("Cerrar")
        self.btn_pluma_sal_cerrar.setStyleSheet(self._btn_style("#e03131"))
        self.btn_pluma_sal_cerrar.clicked.connect(self.on_pluma_salida_cerrar)
        plumas_layout.addWidget(self.btn_pluma_sal_cerrar, 1, 2)

        mid_row.addWidget(grp_plumas)
        layout.addLayout(mid_row)

        # --- Fila inferior: Sensores ---
        grp_sensores = QGroupBox("Sensores / Entradas Físicas")
        sensores_layout = QHBoxLayout(grp_sensores)

        sensores_layout.addWidget(QLabel("I1 NA:"))
        self.led_boton_na = LedIndicator()
        sensores_layout.addWidget(self.led_boton_na)

        sensores_layout.addWidget(QLabel("I2 NC:"))
        self.led_boton_nc = LedIndicator()
        sensores_layout.addWidget(self.led_boton_nc)

        sensores_layout.addWidget(QLabel("I3 Emerg:"))
        self.led_emergencia = LedIndicator()
        sensores_layout.addWidget(self.led_emergencia)

        sensores_layout.addWidget(QLabel("I4 Salida:"))
        self.led_sensor_salida = LedIndicator()
        sensores_layout.addWidget(self.led_sensor_salida)

        sensores_layout.addWidget(QLabel("I5 Entrada:"))
        self.led_sensor_entrada = LedIndicator()
        sensores_layout.addWidget(self.led_sensor_entrada)

        layout.addWidget(grp_sensores)

    # --- Acciones de botones ---

    def on_init_proceso(self):
        self._write_bit(SALIDA_BIT_INIT_PROCESO, True, "Init proceso (Estado 0 a 1)")

    def on_stop(self):
        self._write_bit(SALIDA_BIT_STOP, True, "STOP activado")

    def on_led_verde(self):
        self._write_bit(SALIDA_BIT_LED_VERDE, True, "LED verde ON")

    def on_led_verde_off(self):
        self._write_bit(SALIDA_BIT_LED_VERDE, False, "LED verde OFF")

    def on_led_amarillo(self):
        self._write_bit(SALIDA_BIT_LED_AMARILLO, True, "LED amarillo ON")

    def on_led_amarillo_off(self):
        self._write_bit(SALIDA_BIT_LED_AMARILLO, False, "LED amarillo OFF")

    def on_led_rojo(self):
        self._write_bit(SALIDA_BIT_LED_ROJO, True, "LED rojo ON")

    def on_led_rojo_off(self):
        self._write_bit(SALIDA_BIT_LED_ROJO, False, "LED rojo OFF")

    def on_banda_izq(self):
        self._write_register(SALIDA_SWITCH_BANDA, 5376, "Banda izquierda")

    def on_banda_off(self):
        self._write_register(SALIDA_SWITCH_BANDA, 5377, "Banda detenida")

    def on_banda_der(self):
        self._write_register(SALIDA_SWITCH_BANDA, 5378, "Banda derecha")

    def on_banda_salida(self, checked):
        self._write_bit(SALIDA_BIT_BANDA_SALIDA, checked, f"Banda salida {'ON' if checked else 'OFF'}")

    def on_pluma_entrada_abrir(self):
        self._write_bit(SALIDA_BIT_LED_VERDE, True, "Pluma entrada abierta (M41)")

    def on_pluma_entrada_cerrar(self):
        self._write_bit(SALIDA_BIT_PLUMA_ENTRADA_CERRAR, True, "Pluma entrada cerrada")

    def on_pluma_salida_abrir(self):
        self._write_bit(SALIDA_BIT_PLUMA_SALIDA_ABRIR, True, "Pluma salida abierta")

    def on_pluma_salida_cerrar(self):
        self._write_bit(SALIDA_BIT_PLUMA_SALIDA_CERRAR, True, "Pluma salida cerrada")

    def on_vfd_escribir(self):
        text = self.input_vfd.text().strip()
        if not text:
            return
        try:
            value = int(text)
            self.manager.write_register(self.PLC_ID, SALIDA_VFD_ESCRIBIR, value)
            self.log(
                f"[SALIDA] VFD frecuencia escrita: {value} | "
                f"{register_label(SALIDA_VFD_ESCRIBIR)}={value}"
            )
        except ValueError:
            self.log("[SALIDA] Error: frecuencia debe ser un número entero")
        except Exception as e:
            self.log(f"[SALIDA] Error escribiendo VFD: {e}")

    # --- Polling de estado ---

    def refresh(self):
        """Llamado por el timer para actualizar indicadores."""
        if not self.connected:
            return

        try:
            self.led_boton_na.update_state(
                self.manager.read_input(self.PLC_ID, SALIDA_INPUT_BOTON_NA))
            self.led_boton_nc.update_state(
                self.manager.read_input(self.PLC_ID, SALIDA_INPUT_BOTON_NC))
            self.led_emergencia.update_state(
                self.manager.read_input(self.PLC_ID, SALIDA_INPUT_EMERGENCIA))
            self.led_sensor_salida.update_state(
                self.manager.read_input(self.PLC_ID, SALIDA_INPUT_SENSOR_SALIDA))
            self.led_sensor_entrada.update_state(
                self.manager.read_input(self.PLC_ID, SALIDA_INPUT_SENSOR_ENTRADA))

            vfd_value = self.manager.read_register(self.PLC_ID, SALIDA_VFD_LEER)
            self.lbl_vfd_actual.setText(f"{vfd_value} Hz")

            estado = self.manager.read_register(self.PLC_ID, SALIDA_MAQUINA_ESTADOS)
            self.lbl_maquina_estados.setText(str(estado))

        except Exception as e:
            self.log(f"[SALIDA] Error en refresh: {e}")

    # --- Helpers ---

    def _write_bit(self, bit, state, msg):
        try:
            self.manager.write_register_bit(
                self.PLC_ID, SALIDA_REG_CONTROL, bit, state)
            state_text = "ON" if state else "OFF"
            self.log(
                f"[SALIDA] {msg} | "
                f"{register_bit_label(SALIDA_REG_CONTROL, bit)}={state_text}"
            )
        except Exception as e:
            self.log(f"[SALIDA] Error: {e}")

    def _write_register(self, address, value, msg):
        try:
            self.manager.write_register(self.PLC_ID, address, value)
            self.log(f"[SALIDA] {msg} | {register_label(address)}={value}")
        except Exception as e:
            self.log(f"[SALIDA] Error: {e}")

    def toggle_connection(self):
        if not self.connected:
            try:
                result = self.manager.connect_device(self.PLC_ID)
                self.connected = result
                if result:
                    self.btn_connect.setText("DESCONECTAR")
                    self.btn_connect.setStyleSheet(styled_btn("#e03131"))
                    self.lbl_status.setText("ONLINE")
                    self.lbl_status.setStyleSheet("color: #2f9e44;")
                    self.log(f"[SALIDA] Conectado a {self.PLC_ID}")
                else:
                    self.lbl_status.setText("FALLO")
                    self.lbl_status.setStyleSheet("color: #e03131;")
                    self.log(f"[SALIDA] No se pudo conectar a {self.PLC_ID}")
            except Exception as e:
                self.log(f"[SALIDA] Error conectando: {e}")
        else:
            self.manager.disconnect_device(self.PLC_ID)
            self.connected = False
            self.btn_connect.setText("CONECTAR")
            self.btn_connect.setStyleSheet(styled_btn("#4263eb"))
            self.lbl_status.setText("DESCONECTADO")
            self.lbl_status.setStyleSheet("color: #e03131;")
            self.log(f"[SALIDA] Desconectado de {self.PLC_ID}")

    def _btn_style(self, color):
        return styled_btn(color)


class MainWindow(QMainWindow):
    """Ventana principal del SCADA."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("SCADA - Bandas Automatizadas | Horner XL4")
        self.setMinimumSize(900, 700)

        self.manager = PLCManager()

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Header con título
        header = QHBoxLayout()

        title = QLabel("SCADA CONTROL")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title.setStyleSheet("color: #4263eb;")
        header.addWidget(title)

        header.addStretch()

        self.btn_reset = QPushButton("RESET")
        self.btn_reset.setStyleSheet(styled_btn("#f08c00"))
        self.btn_reset.clicked.connect(self.on_reset)
        header.addWidget(self.btn_reset)

        main_layout.addLayout(header)

        # Tabs
        self.tabs = QTabWidget()
        self.tab_entrada = EntradaTab(self.manager, self.log_message)
        self.tab_central = CentralTab(self.manager, self.log_message)
        self.tab_salida = SalidaTab(self.manager, self.log_message)
        self.tabs.addTab(self.tab_entrada, "Entrada (HORNER_2)")
        self.tabs.addTab(self.tab_central, "Central (HORNER_3)")
        self.tabs.addTab(self.tab_salida, "Salida (HORNER_1)")
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
        self.timer.start(500)

        self.log_message("Sistema listo. Conecta cada PLC individualmente.")

    def refresh_all(self):
        self.tab_entrada.refresh()
        self.tab_central.refresh()
        self.tab_salida.refresh()

    def on_reset(self):
        if QMessageBox.question(
            self,
            "Confirmar reset",
            "Esto pondrá en cero todas las T activas y los bits de control del registro R170.\n\n¿Deseas continuar?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        ) != QMessageBox.Yes:
            return

        try:
            coil_operations = self._build_reset_coil_operations()
            coil_results = self.manager.write_coil_multiple(coil_operations)

            bit_results = []
            for bit_name, bit in sorted(
                (
                    (name, value)
                    for name, value in vars(constants).items()
                    if name.startswith("SALIDA_BIT_") and isinstance(value, int)
                ),
                key=lambda item: item[1],
            ):
                try:
                    self.manager.write_register_bit(
                        "HORNER_1", SALIDA_REG_CONTROL, bit, False
                    )
                    bit_results.append((bit_name, True))
                except Exception as e:
                    bit_results.append((bit_name, False))
                    self.log_message(f"[RESET] Error limpiando {bit_name}: {e}")

            ok_coils = sum(1 for value in coil_results.values() if value)
            total_coils = len(coil_results)
            ok_bits = sum(1 for _, ok in bit_results if ok)
            total_bits = len(bit_results)

            self.log_message(
                f"[RESET] T limpiadas: {ok_coils}/{total_coils}. Bits limpiados: {ok_bits}/{total_bits}."
            )
        except Exception as e:
            self.log_message(f"[RESET] Error ejecutando reset: {e}")

    def _build_reset_coil_operations(self):
        operations = []
        seen_addresses = set()

        for name, value in vars(constants).items():
            if not isinstance(value, int):
                continue

            if name.startswith("CENTRAL_") and 6000 <= value < 7000:
                key = ("HORNER_3", value)
            elif name.startswith("ENTRADA_") and 6000 <= value < 7000:
                key = ("HORNER_2", value)
            else:
                continue

            if key in seen_addresses:
                continue

            seen_addresses.add(key)
            operations.append((key[0], key[1], False))

        operations.sort(key=lambda item: (item[0], item[1]))
        return operations

    def log_message(self, msg):
        self.txt_log.append(msg)
        self.txt_log.verticalScrollBar().setValue(
            self.txt_log.verticalScrollBar().maximum()
        )

    def closeEvent(self, event):
        self.timer.stop()
        for tab in (self.tab_entrada, self.tab_central, self.tab_salida):
            if tab.connected:
                self.manager.disconnect_device(tab.PLC_ID)
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
