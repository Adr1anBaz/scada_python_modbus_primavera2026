"""
Constantes compartidas del sistema Horner.
Define direcciones Modbus para coils y registros.
"""

# =============================================================================
# COILS (Entradas/Salidas Binarias)
# =============================================================================

# Entradas (inputs)
COIL_T1 = 6000  # Entrada de control T1

# Salidas (outputs)
COIL_Q10 = 9    # Salida Q10 (es el output Q1 en posición 10)

# =============================================================================
# REGISTROS (Valores de 16 bits)
# =============================================================================

# Registros de lectura/escritura
REGISTER_R1 = 3000  # Registro de datos R1

# =============================================================================
# CONSTANTES DE CONEXIÓN
# =============================================================================

DEFAULT_TIMEOUT = 3  # segundos
DEFAULT_PORT = 502   # Puerto estándar Modbus TCP
