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
CENTRAL_MODO_PRUEBA = 6051          # T51 - ir a modo prueba (enclavable)
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
CENTRAL_ROTADOR_HORARIO = 6054     # T54 - girar rotador sentido horario
CENTRAL_ROTADOR_STOP = 6056        # T56 - detener giro del rotador

# --- Modo prueba: control de banda ---
CENTRAL_BANDA_ADELANTE = 6057      # T57 - avance banda hacia adelante
CENTRAL_BANDA_ATRAS = 6058         # T58 - avance banda hacia atrás
CENTRAL_BANDA_STOP = 6059          # T59 - detener banda

# --- Modo prueba: torreta ---
CENTRAL_TORRETA_VERDE = 6060       # T60 - torreta piloto verde
CENTRAL_TORRETA_AMARILLO = 6061    # T61 - torreta piloto amarillo
CENTRAL_TORRETA_ROJO = 6055        # T55 - torreta piloto rojo

# --- Modo prueba: pilotos de diagnóstico (lectura) ---
CENTRAL_PILOTO_SENSOR_SALIDA = 6064   # T64 - sensor de salida
CENTRAL_PILOTO_SENSOR_ENTRADA = 6065  # T65 - sensor de entrada
CENTRAL_PILOTO_SENSOR_GIRO = 6066     # T66 - sensor de fin de giro
CENTRAL_PILOTO_BOTON_VERDE = 6067     # T67 - botón verde
CENTRAL_PILOTO_BOTON_ROJO = 6068      # T68 - botón rojo
CENTRAL_PILOTO_BOTON_PARO = 6069      # T69 - botón de paro


# =============================================================================
# PLC ENTRADA (HORNER_2 - 192.168.3.132)
# Banda de entrada
# IMPORTANTE: Estas constantes SOLO aplican para HORNER_2.
# Usar exclusivamente con: manager.write_coil("HORNER_2", ENTRADA_XXX, value)
#                      o:  manager.read_input("HORNER_2", ENTRADA_XXX)
# =============================================================================

# --- Navegación HMI (solo cambian pantalla, no afectan actuadores) ---
# ENTRADA_SCREEN_2 = (navegación interna HMI)
# ENTRADA_SCREEN_1 = (navegación interna HMI)
# ENTRADA_SCREEN_3 = (navegación interna HMI)

# --- Control general (modo integración) ---
ENTRADA_STOP = 6030                    # T30 - STOP, frena todo el sistema
ENTRADA_INICIO = 6099                  # T99 - señal que inicia el proceso

# --- Control general (modo individual) ---
ENTRADA_STOP_INDIVIDUAL = 6033         # T33 - STOP en modo individual
ENTRADA_INICIO_INDIVIDUAL = 6999       # T999 - señal que inicia proceso en modo individual

# --- Pilotos de lámparas (lectura) ---
ENTRADA_LAMPARA_VERDE = 6009           # T9 - lámpara verde
ENTRADA_LAMPARA_AMARILLA = 6088        # T88 - lámpara amarilla, indica paso de caja
ENTRADA_LAMPARA_ROJA = 6077            # T77 - lámpara roja, indica paro

# --- Modo prueba: control de plumas ---
ENTRADA_PLUMA_INICIO_SUBE = 6005       # T5 - levanta la pluma de inicio
ENTRADA_PLUMA_INICIO_BAJA = 6006       # T6 - baja la pluma de inicio
ENTRADA_PLUMA_FIN = 6007               # T7 - levanta/baja la pluma de fin

# --- Modo prueba: control de banda ---
ENTRADA_BANDA_DERECHA = 6045           # T45 - arranca banda a la derecha
ENTRADA_BANDA_IZQUIERDA = 6044         # T44 - arranca banda a la izquierda
ENTRADA_BANDA_STOP = 6046              # T46 - detiene la banda

# --- Modo prueba: torreta manual ---
ENTRADA_TORRETA_VERDE = 6345           # T345 - enciende lámpara verde
ENTRADA_TORRETA_AMARILLA = 6346        # T346 - enciende lámpara amarilla
ENTRADA_TORRETA_ROJA = 6347            # T347 - enciende lámpara roja

# --- Modo individual: pilotos de estado UR3/banda (lectura) ---
ENTRADA_SEB_LISTO = 6995              # T995 - banda media en posición de recibir caja
ENTRADA_SEB_CAJA = 6998               # T998 - caja ya está en banda media
ENTRADA_UR1 = 6997                    # T997 - UR3 ya puso caja en banda inicial
ENTRADA_UR2 = 6996                    # T996 - UR3 ya puede poner otra caja

# --- Entradas físicas (usar con manager.read_input) ---
ENTRADA_INPUT_SENSOR_ENTRADA = 3      # I4 - sensor de entrada (censado)
ENTRADA_INPUT_SENSOR_SALIDA = 4       # I5 - sensor de salida (censado)

# --- Salidas físicas (lectura con read_coil) ---
ENTRADA_PLUMA_INICIO_ARRIBA = 7       # Q8 - LED pluma inicio arriba
ENTRADA_PLUMA_INICIO_ABAJO = 8        # Q9 - LED pluma inicio abajo
ENTRADA_PLUMA_FIN_ARRIBA = 5          # Q6 - LED pluma fin arriba
ENTRADA_PLUMA_FIN_ABAJO = 6           # Q7 - LED pluma fin abajo

# --- Registros VFD ---
ENTRADA_VFD_ESCRIBIR = 3497           # R498 - escribir frecuencia del VFD
ENTRADA_VFD_LEER = 3507               # R508 - leer frecuencia del VFD


# =============================================================================
# PLC SALIDA (HORNER_1 - 192.168.3.131)
# Banda de salida
# IMPORTANTE: Estas constantes SOLO aplican para HORNER_1.
# Usar exclusivamente con: manager.write_register_bit("HORNER_1", SALIDA_REG_CONTROL, bit, state)
#                      o:  manager.read_register("HORNER_1", SALIDA_XXX)
#                      o:  manager.read_input("HORNER_1", SALIDA_INPUT_XXX)
# =============================================================================

# --- Registro de control de bits (R170 = dirección 3169) ---
# Las M originales fueron remapeadas como bits de este registro.
SALIDA_REG_CONTROL = 3169             # R170 - registro que contiene todas las M como bits

# Bits del registro R170:
SALIDA_BIT_MODO_INT_A_PROC = 0        # M29 (R170.0) - Modo Integración → Modo Proceso
SALIDA_BIT_MODO_PROC_A_INT = 1        # M33 (R170.1) - Modo Proceso → Modo Integración
SALIDA_BIT_INIT_PROCESO = 2           # M32 (R170.2) - initPru, pasa Estado 0 a Estado 1
SALIDA_BIT_MODO_PROC_A_IND = 3        # M36 (R170.3) - Modo Proceso → Modo Individual
SALIDA_BIT_LED_ROJO = 4               # M46 (R170.4) - encender LED rojo
SALIDA_BIT_LED_AMARILLO = 5           # M47 (R170.5) - encender LED amarillo
SALIDA_BIT_STOP = 6                   # M49 (R170.6) - stop/paro
SALIDA_BIT_LED_VERDE = 7              # M41 (R170.7) - encender LED verde / abrir pluma entrada
SALIDA_BIT_PLUMA_ENTRADA_CERRAR = 8   # M42 (R170.8) - cerrar pluma de entrada
SALIDA_BIT_PLUMA_SALIDA_ABRIR = 9     # M43 (R170.9) - abrir pluma de salida
SALIDA_BIT_PLUMA_SALIDA_CERRAR = 10   # M44 (R170.10) - cerrar pluma de salida
SALIDA_BIT_MODO_IND_A_PROC = 11       # M37 (R170.11) - Modo Individual → Modo Proceso
SALIDA_BIT_BANDA_SALIDA = 12          # R170.12 - control enclavable de banda de salida
# SALIDA_BIT_RESET_BANDA = ?          # M45 - reset banda (manda 2 a R506) — no mapeado en notasLeo

# --- Registros directos ---
SALIDA_VFD_ESCRIBIR = 3497            # R498 - escribir frecuencia (x100 → R504)
SALIDA_VFD_LEER = 3507                # R508 - leer frecuencia actual (R502/100)
SALIDA_MAQUINA_ESTADOS = 3000         # R1 - registro de máquina de estados
SALIDA_SWITCH_BANDA = 3099            # R100 - switch 3 posiciones (5376=izq, 5377=off, 5378=der)

# --- Entradas físicas (usar con manager.read_input) ---
SALIDA_INPUT_BOTON_NA = 0             # I1 - botón NA
SALIDA_INPUT_BOTON_NC = 1             # I2 - botón NC
SALIDA_INPUT_EMERGENCIA = 2           # I3 - botón de emergencia NC
SALIDA_INPUT_SENSOR_SALIDA = 3        # I4 - sensor de salida
SALIDA_INPUT_SENSOR_ENTRADA = 4       # I5 - sensor de entrada
