"""
Constantes compartidas del sistema Horner.
Define direcciones Modbus para coils y registros.

Convención de direcciones:
  - Marcas T en Horner empiezan en dirección 6000
  - Ejemplo: T49 = 6049, T76 = 6076
  - Salidas Q empiezan en 0 (Q1=0, Q2=1, ..., Q10=9)
  - Entradas I empiezan en 0 (I1=0, I2=1, ...)
  - Registros R empiezan en 3000 (R1=3000, R2=3001, ...)
"""

# =============================================================================
# CONSTANTES DE CONEXIÓN
# =============================================================================

DEFAULT_TIMEOUT = 3  # segundos
DEFAULT_PORT = 502   # Puerto estándar Modbus TCP

# =============================================================================
# PLC CENTRAL (HORNER_3 - 192.168.3.133)
# Banda rotatoria
# IMPORTANTE: Estas constantes SOLO aplican para HORNER_3.
# Usar exclusivamente con: manager.write_coil("HORNER_3", CENTRAL_XXX, value)
# =============================================================================

# --- Navegación HMI (solo cambian pantalla, no afectan actuadores) ---
# CENTRAL_MODO_PROCESO = 6076       # T76 - ir a pestaña proceso + señal init
# CENTRAL_MODO_INTEGRACION = 6070   # T70 - ir a modo integración + señal init
# CENTRAL_MODO_PRUEBA = 6051        # T51 - ir a modo prueba (individual)
# CENTRAL_MENU = 6053               # T53 - regresar al menú principal

# --- Control general ---
CENTRAL_STOP = 6049                 # T49 - STOP, frena todo el sistema

# --- Señales de proceso / integración ---
CENTRAL_LLEGO_CAJA = 6024          # T24 - señal de banda 1: está por mandar caja
CENTRAL_RECIBIO_BANDA3 = 6028      # T28 - señal de banda 3: recibió la caja (gira antihorario)
CENTRAL_UR3_FIN = 6079             # T79 - señal del UR3 en integración (gira horario después)

# --- Pilotos de estado (lectura) ---
CENTRAL_PILOTO_RECIBIDO = 6026     # T26 - piloto: recibió caja / sensor entrada da 1
CENTRAL_PILOTO_LISTO = 6034        # T34 - piloto: sistema listo para nueva caja

# --- Modo prueba: control de rotador ---
CENTRAL_ROTADOR_ANTIHORARIO = 6063  # T63 - girar rotador sentido antihorario
CENTRAL_ROTADOR_HORARIO = 6055     # T55 - girar rotador sentido horario
CENTRAL_ROTADOR_STOP = 6056        # T56 - detener giro del rotador

# --- Modo prueba: control de banda ---
CENTRAL_BANDA_ADELANTE = 6057      # T57 - avance banda hacia adelante
CENTRAL_BANDA_ATRAS = 6058         # T58 - avance banda hacia atrás
CENTRAL_BANDA_STOP = 6059          # T59 - detener banda

# --- Modo prueba: torreta ---
CENTRAL_TORRETA_VERDE = 6060       # T60 - torreta piloto verde
CENTRAL_TORRETA_AMARILLO = 6061    # T61 - torreta piloto amarillo
CENTRAL_TORRETA_ROJO = 6054        # T54 - torreta piloto rojo

# --- Modo prueba: pilotos de diagnóstico (lectura) ---
CENTRAL_PILOTO_SENSOR_SALIDA = 6064   # T64 - sensor de salida
CENTRAL_PILOTO_SENSOR_ENTRADA = 6065  # T65 - sensor de entrada
CENTRAL_PILOTO_SENSOR_GIRO = 6066     # T66 - sensor de fin de giro
CENTRAL_PILOTO_BOTON_VERDE = 6067     # T67 - botón verde
CENTRAL_PILOTO_BOTON_ROJO = 6068      # T68 - botón rojo
CENTRAL_PILOTO_BOTON_PARO = 6069      # T69 - botón de paro
