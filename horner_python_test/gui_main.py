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


class CentralTab(QWidget):
    """Tab para el PLC Central (HORNER_3 - 192.168.3.133). Banda rotatoria."""

    PLC_ID = "HORNER_3"

    def __init__(self, manager: PLCManager, log_callback):
        super().__init__()
        self.manager = manager
        self.log = log_callback
        self.connected = False
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # --- Fila superior: Control + Pilotos ---
        top_row = QHBoxLayout()

        grp_control = QGroupBox("Control")
        ctrl_layout = QHBoxLayout(grp_control)

        self.btn_stop = QPushButton("⏹ STOP")
        self.btn_stop.setStyleSheet(self._btn_style("#F44336"))
        self.btn_stop.clicked.connect(self.on_stop)
        ctrl_layout.addWidget(self.btn_stop)

        self.btn_llego_caja = QPushButton("Llegó caja")
        self.btn_llego_caja.setStyleSheet(self._btn_style("#795548"))
        self.btn_llego_caja.clicked.connect(self.on_llego_caja)
        ctrl_layout.addWidget(self.btn_llego_caja)

        self.btn_recibio_b3 = QPushButton("Recibió B3")
        self.btn_recibio_b3.setStyleSheet(self._btn_style("#795548"))
        self.btn_recibio_b3.clicked.connect(self.on_recibio_b3)
        ctrl_layout.addWidget(self.btn_recibio_b3)

        self.btn_ur3_fin = QPushButton("UR3 Fin")
        self.btn_ur3_fin.setStyleSheet(self._btn_style("#795548"))
        self.btn_ur3_fin.clicked.connect(self.on_ur3_fin)
        ctrl_layout.addWidget(self.btn_ur3_fin)

        top_row.addWidget(grp_control)

        grp_pilotos = QGroupBox("Pilotos de Estado")
        pilotos_layout = QHBoxLayout(grp_pilotos)

        pilotos_layout.addWidget(QLabel("Recibido:"))
        self.led_recibido = LedIndicator()
        pilotos_layout.addWidget(self.led_recibido)

        pilotos_layout.addWidget(QLabel("Listo:"))
        self.led_listo = LedIndicator()
        pilotos_layout.addWidget(self.led_listo)

        top_row.addWidget(grp_pilotos)
        layout.addLayout(top_row)

        # --- Fila media: Rotador + Banda ---
        mid_row = QHBoxLayout()

        grp_rotador = QGroupBox("Rotador")
        rot_layout = QHBoxLayout(grp_rotador)

        self.btn_rot_anti = QPushButton("↺ Anti")
        self.btn_rot_anti.setStyleSheet(self._btn_style("#2196F3"))
        self.btn_rot_anti.clicked.connect(self.on_rotador_anti)
        rot_layout.addWidget(self.btn_rot_anti)

        self.btn_rot_stop = QPushButton("⏹")
        self.btn_rot_stop.setStyleSheet(self._btn_style("#607D8B"))
        self.btn_rot_stop.clicked.connect(self.on_rotador_stop)
        rot_layout.addWidget(self.btn_rot_stop)

        self.btn_rot_hora = QPushButton("↻ Hora")
        self.btn_rot_hora.setStyleSheet(self._btn_style("#2196F3"))
        self.btn_rot_hora.clicked.connect(self.on_rotador_hora)
        rot_layout.addWidget(self.btn_rot_hora)

        mid_row.addWidget(grp_rotador)

        grp_banda = QGroupBox("Banda")
        banda_layout = QHBoxLayout(grp_banda)

        self.btn_banda_atras = QPushButton("◀ Atrás")
        self.btn_banda_atras.setStyleSheet(self._btn_style("#2196F3"))
        self.btn_banda_atras.clicked.connect(self.on_banda_atras)
        banda_layout.addWidget(self.btn_banda_atras)

        self.btn_banda_stop = QPushButton("⏹")
        self.btn_banda_stop.setStyleSheet(self._btn_style("#607D8B"))
        self.btn_banda_stop.clicked.connect(self.on_banda_stop)
        banda_layout.addWidget(self.btn_banda_stop)

        self.btn_banda_adelante = QPushButton("▶ Adelante")
        self.btn_banda_adelante.setStyleSheet(self._btn_style("#2196F3"))
        self.btn_banda_adelante.clicked.connect(self.on_banda_adelante)
        banda_layout.addWidget(self.btn_banda_adelante)

        mid_row.addWidget(grp_banda)
        layout.addLayout(mid_row)

        # --- Fila inferior: Torreta + Diagnóstico ---
        bot_row = QHBoxLayout()

        grp_torreta = QGroupBox("Torreta")
        torreta_layout = QHBoxLayout(grp_torreta)

        self.btn_torr_verde = QPushButton("🟢")
        self.btn_torr_verde.setStyleSheet(self._btn_style("#4CAF50"))
        self.btn_torr_verde.clicked.connect(self.on_torreta_verde)
        torreta_layout.addWidget(self.btn_torr_verde)

        self.btn_torr_amarillo = QPushButton("🟡")
        self.btn_torr_amarillo.setStyleSheet(self._btn_style("#FFC107"))
        self.btn_torr_amarillo.clicked.connect(self.on_torreta_amarillo)
        torreta_layout.addWidget(self.btn_torr_amarillo)

        self.btn_torr_rojo = QPushButton("🔴")
        self.btn_torr_rojo.setStyleSheet(self._btn_style("#F44336"))
        self.btn_torr_rojo.clicked.connect(self.on_torreta_rojo)
        torreta_layout.addWidget(self.btn_torr_rojo)

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

    # --- Acciones de botones ---

    def on_stop(self):
        self._write_coil(CENTRAL_STOP, True, "STOP activado")

    def on_llego_caja(self):
        self._write_coil(CENTRAL_LLEGO_CAJA, True, "Señal: llegó caja")

    def on_recibio_b3(self):
        self._write_coil(CENTRAL_RECIBIO_BANDA3, True, "Señal: recibió banda 3")

    def on_ur3_fin(self):
        self._write_coil(CENTRAL_UR3_FIN, True, "Señal: UR3 fin")

    def on_rotador_anti(self):
        self._write_coil(CENTRAL_ROTADOR_ANTIHORARIO, True, "Rotador ↺ antihorario")

    def on_rotador_stop(self):
        self._write_coil(CENTRAL_ROTADOR_STOP, True, "Rotador detenido")

    def on_rotador_hora(self):
        self._write_coil(CENTRAL_ROTADOR_HORARIO, True, "Rotador ↻ horario")

    def on_banda_atras(self):
        self._write_coil(CENTRAL_BANDA_ATRAS, True, "Banda ◀ atrás")

    def on_banda_stop(self):
        self._write_coil(CENTRAL_BANDA_STOP, True, "Banda detenida")

    def on_banda_adelante(self):
        self._write_coil(CENTRAL_BANDA_ADELANTE, True, "Banda ▶ adelante")

    def on_torreta_verde(self):
        self._write_coil(CENTRAL_TORRETA_VERDE, True, "Torreta verde ON")

    def on_torreta_amarillo(self):
        self._write_coil(CENTRAL_TORRETA_AMARILLO, True, "Torreta amarillo ON")

    def on_torreta_rojo(self):
        self._write_coil(CENTRAL_TORRETA_ROJO, True, "Torreta rojo ON")

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
            self.log(f"[CENTRAL] {msg}")
        except Exception as e:
            self.log(f"[CENTRAL] Error: {e}")

    def _btn_style(self, color):
        return (
            f"background-color: {color}; color: white; "
            f"font-size: 12px; padding: 8px 12px; border-radius: 4px;"
        )


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

        # --- Fila superior: Control + LEDs ---
        top_row = QHBoxLayout()

        grp_control = QGroupBox("Control")
        ctrl_layout = QHBoxLayout(grp_control)

        self.btn_init = QPushButton("▶ Init Proceso")
        self.btn_init.setStyleSheet(self._btn_style("#4CAF50"))
        self.btn_init.clicked.connect(self.on_init_proceso)
        ctrl_layout.addWidget(self.btn_init)

        self.btn_stop = QPushButton("⏹ STOP")
        self.btn_stop.setStyleSheet(self._btn_style("#F44336"))
        self.btn_stop.clicked.connect(self.on_stop)
        ctrl_layout.addWidget(self.btn_stop)

        top_row.addWidget(grp_control)

        grp_leds = QGroupBox("LEDs")
        leds_layout = QHBoxLayout(grp_leds)

        self.btn_led_verde = QPushButton("🟢 Verde")
        self.btn_led_verde.setStyleSheet(self._btn_style("#4CAF50"))
        self.btn_led_verde.clicked.connect(self.on_led_verde)
        leds_layout.addWidget(self.btn_led_verde)

        self.btn_led_amarillo = QPushButton("🟡 Amarillo")
        self.btn_led_amarillo.setStyleSheet(self._btn_style("#FFC107"))
        self.btn_led_amarillo.clicked.connect(self.on_led_amarillo)
        leds_layout.addWidget(self.btn_led_amarillo)

        self.btn_led_rojo = QPushButton("🔴 Rojo")
        self.btn_led_rojo.setStyleSheet(self._btn_style("#F44336"))
        self.btn_led_rojo.clicked.connect(self.on_led_rojo)
        leds_layout.addWidget(self.btn_led_rojo)

        top_row.addWidget(grp_leds)
        layout.addLayout(top_row)

        # --- Fila media: Banda + Plumas ---
        mid_row = QHBoxLayout()

        grp_banda = QGroupBox("Banda")
        banda_layout = QVBoxLayout(grp_banda)

        banda_btns = QHBoxLayout()
        self.btn_banda_izq = QPushButton("◀ Izq")
        self.btn_banda_izq.setStyleSheet(self._btn_style("#2196F3"))
        self.btn_banda_izq.clicked.connect(self.on_banda_izq)
        banda_btns.addWidget(self.btn_banda_izq)

        self.btn_banda_off = QPushButton("⏹ Off")
        self.btn_banda_off.setStyleSheet(self._btn_style("#607D8B"))
        self.btn_banda_off.clicked.connect(self.on_banda_off)
        banda_btns.addWidget(self.btn_banda_off)

        self.btn_banda_der = QPushButton("▶ Der")
        self.btn_banda_der.setStyleSheet(self._btn_style("#2196F3"))
        self.btn_banda_der.clicked.connect(self.on_banda_der)
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
        self.btn_pluma_ent_abrir.clicked.connect(self.on_pluma_entrada_abrir)
        plumas_layout.addWidget(self.btn_pluma_ent_abrir, 0, 1)

        self.btn_pluma_ent_cerrar = QPushButton("Cerrar")
        self.btn_pluma_ent_cerrar.clicked.connect(self.on_pluma_entrada_cerrar)
        plumas_layout.addWidget(self.btn_pluma_ent_cerrar, 0, 2)

        plumas_layout.addWidget(QLabel("Salida:"), 1, 0)
        self.btn_pluma_sal_abrir = QPushButton("Abrir")
        self.btn_pluma_sal_abrir.clicked.connect(self.on_pluma_salida_abrir)
        plumas_layout.addWidget(self.btn_pluma_sal_abrir, 1, 1)

        self.btn_pluma_sal_cerrar = QPushButton("Cerrar")
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
        self._write_bit(SALIDA_BIT_INIT_PROCESO, True, "Init proceso (Estado 0→1)")

    def on_stop(self):
        self._write_bit(SALIDA_BIT_STOP, True, "STOP activado")

    def on_led_verde(self):
        self._write_bit(SALIDA_BIT_LED_VERDE, True, "LED verde ON")

    def on_led_amarillo(self):
        self._write_bit(SALIDA_BIT_LED_AMARILLO, True, "LED amarillo ON")

    def on_led_rojo(self):
        self._write_bit(SALIDA_BIT_LED_ROJO, True, "LED rojo ON")

    def on_banda_izq(self):
        self._write_register(SALIDA_SWITCH_BANDA, 5376, "Banda ◀ izquierda")

    def on_banda_off(self):
        self._write_register(SALIDA_SWITCH_BANDA, 5377, "Banda detenida")

    def on_banda_der(self):
        self._write_register(SALIDA_SWITCH_BANDA, 5378, "Banda ▶ derecha")

    def on_pluma_entrada_abrir(self):
        self._write_bit(SALIDA_BIT_LED_VERDE, True, "Pluma entrada abierta")

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
            self.log(f"[SALIDA] VFD frecuencia escrita: {value}")
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
            self.log(f"[SALIDA] {msg}")
        except Exception as e:
            self.log(f"[SALIDA] Error: {e}")

    def _write_register(self, address, value, msg):
        try:
            self.manager.write_register(self.PLC_ID, address, value)
            self.log(f"[SALIDA] {msg}")
        except Exception as e:
            self.log(f"[SALIDA] Error: {e}")

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

        self.log_message("Sistema listo. Presiona 'Conectar' para iniciar.")

    def toggle_connection(self):
        if self.btn_connect.text() == "Conectar":
            self.log_message("Conectando a PLCs...")
            try:
                results = self.manager.initialize()
                connected_count = sum(1 for v in results.values() if v)
                total = len(results)

                self.tab_entrada.connected = results.get("HORNER_2", False)
                self.tab_central.connected = results.get("HORNER_3", False)
                self.tab_salida.connected = results.get("HORNER_1", False)

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
            self.tab_central.connected = False
            self.tab_salida.connected = False
            self.lbl_status.setText("Desconectado")
            self.lbl_status.setStyleSheet("color: #F44336;")
            self.btn_connect.setText("Conectar")
            self.log_message("Desconectado de todos los PLCs")

    def refresh_all(self):
        self.tab_entrada.refresh()
        self.tab_central.refresh()
        self.tab_salida.refresh()

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
