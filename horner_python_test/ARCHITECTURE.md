"""
ARQUITECTURA DEL SISTEMA MULTICONTROLADOR
==========================================

Este documento explica la arquitectura implementada en la carpeta 'system/'
y cómo facilita el control de múltiples PLCs simultáneamente.

"""

# ============================================================================
# 1. OVERVIEW DE LA ARQUITECTURA
# ============================================================================

"""
ANTES (Código Original)
=======================
main.py / cli.py → HornerModbusService (1 PLC hardcodeado) → Modbus TCP

Limitaciones:
- Un solo PLC por aplicación
- IP y puerto hardcodeados en modbus_service.py
- Difícil de extender o reutilizar
- Sin sistema de eventos

DESPUÉS (Con system/)
====================
                    ┌─────────────────────────┐
                    │   CLI / GUI / Scripts   │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │   PLCManager            │  ← Gestor Central
                    │   (Coordinador)         │
                    └────────────┬────────────┘
                                 │
                ┌────────────────┼────────────────┬──────────────┐
                │                │                │              │
        ┌───────▼────────┐ ┌─────▼────────┐ ┌────▼──────────┐  ...
        │  PLCDevice-1   │ │ PLCDevice-2  │ │ PLCDevice-3  │
        │ (HORNER_1)     │ │ (HORNER_2)   │ │ (HORNER_3)   │
        └───────┬────────┘ └─────┬────────┘ └────┬─────────┘
                │                │               │
        ┌───────▼────────┐ ┌─────▼────────┐ ┌────▼──────────┐
        │  Modbus TCP    │ │  Modbus TCP  │ │  Modbus TCP   │
        │ 192.168.3.12   │ │ 192.168.3.13 │ │ 192.168.3.14  │
        └────────────────┘ └──────────────┘ └───────────────┘
            PLC1               PLC2             PLC3

Ventajas:
✓ N PLCs sin cambiar código
✓ Configuración centralizada (config.py)
✓ Sistema de eventos para real-time monitoring
✓ Fácil de testear y extender
✓ Reutilizable en cualquier script
"""


# ============================================================================
# 2. COMPONENTES PRINCIPALES
# ============================================================================

"""
A. CONSTANTS.PY
================
Define constantes compartidas:
  - Direcciones Modbus: COIL_T1, COIL_Q10, REGISTER_R1
  - Parámetros de conexión por defecto
  
Por qué:
  - Un único lugar para cambiar direcciones
  - Evita números mágicos en el código
  - Facilita documentación

Uso:
  from system.constants import COIL_T1, REGISTER_R1
  manager.read_coil("HORNER_1", COIL_T1)


B. CONFIG.PY
=============
Gestiona la configuración de PLCs:
  - PLCConfig: dataclass con IP, puerto, timeout, nombre
  - PLCConfigManager: Almacena y accede a configuraciones
  - create_default_config(): Configuración inicial

Por qué:
  - Centraliza la información de conectividad
  - Fácil de exportar a YAML/JSON en futuro
  - Cada PLC tiene su propio ID único
  - Permite agregar/remover PLCs sin tocar código

Ejemplo:
  config = create_default_config()
  config.register_plc(PLCConfig(
      id="HORNER_2",
      host="192.168.3.13",
      name="PLC Producción"
  ))


C. EVENTS.PY
=============
Sistema Pub-Sub de eventos:
  - EventEmitter: Clase base para emitir eventos
  - EventType: Enum con tipos de eventos predefinidos
  - Callbacks se ejecutan cuando ocurren eventos

Eventos disponibles:
  - PLC_CONNECTED, PLC_DISCONNECTED, PLC_ERROR
  - COIL_READ, COIL_WRITTEN
  - REGISTER_READ, REGISTER_WRITTEN

Por qué:
  - Desacoplamiento entre componentes
  - Múltiples suscriptores a los mismos eventos
  - Facilita logging, monitoring, GUI updates
  - Pattern Observer bien conocido

Ejemplo:
  manager.on("coil_written", lambda plc_id, address, value:
      print(f"{plc_id}: Coil {address} = {value}")
  )


D. PLC_DEVICE.PY
==================
Abstracción de un PLC individual:
  - Encapsula una conexión ModbusTcpClient
  - Métodos: connect(), disconnect(), read_coil(), write_register(), etc.
  - Emite eventos automáticamente
  - Mantiene caché local de valores leídos

Por qué:
  - Cada PLC es independiente
  - Fácil de reemplazar PyModbus con otra librería
  - Caché reduce consultas innecesarias
  - Eventos notifican cambios sin polling

Ejemplo:
  device = PLCDevice("HORNER_1", "192.168.3.12")
  device.connect()
  device.write_coil(6000, True)  # Emite evento COIL_WRITTEN


E. PLC_MANAGER.PY
===================
Gestor central que coordina múltiples PLCs:
  - Mantiene dict de PLCDevice
  - Interfaz unificada para operaciones
  - Operaciones sincronizadas en múltiples PLCs
  - Re-emite eventos de todos los dispositivos

Métodos principales:
  - initialize() → Conecta todos los PLCs
  - shutdown() → Desconecta todos
  - read_coil(plc_id, address) → Lee en un PLC
  - read_coil_from_all(address) → Lee en todos
  - write_coil_multiple(operations) → Escribe en múltiples

Por qué:
  - Un único punto de entrada al sistema
  - Simplifica la lógica de la aplicación
  - Facilita operaciones sincronizadas
  - La GUI se suscribe aquí, no a devices individuales

Ejemplo:
  manager = PLCManager()
  manager.initialize()
  
  # Leer de un PLC
  value = manager.read_coil("HORNER_1", 6000)
  
  # Leer de TODOS los PLCs
  values = manager.read_coil_from_all(6000)
  # Resultado: {"HORNER_1": True, "HORNER_2": False, ...}
  
  manager.shutdown()
"""


# ============================================================================
# 3. FLUJOS DE USO
# ============================================================================

"""
FLUJO 1: USO BÁSICO (CLI)
==========================

from system import PLCManager

# 1. Crear manager y conectar
manager = PLCManager()
manager.initialize()

# 2. Operaciones
value = manager.read_coil("HORNER_1", 6000)
manager.write_coil("HORNER_1", 6000, True)

# 3. Desconectar
manager.shutdown()


FLUJO 2: CON EVENTOS (Monitoring)
==================================

from system import PLCManager

manager = PLCManager()

# Suscribirse a eventos ANTES de conectar
def on_coil_written(plc_id, address, value):
    print(f"{plc_id}: Coil {address} changed to {value}")

manager.on("coil_written", on_coil_written)

manager.initialize()
manager.write_coil("HORNER_1", 6000, True)  # Trigger del evento
manager.shutdown()


FLUJO 3: OPERACIONES SINCRONIZADAS
===================================

manager = PLCManager()
manager.initialize()

# Leer la MISMA dirección en TODOS los PLCs
# Útil para verificar que todos estén en el mismo estado
results = manager.read_coil_from_all(6000)
# results = {"HORNER_1": True, "HORNER_2": True, "HORNER_3": False}

# Escribir en MÚLTIPLES PLCs a la vez
operations = [
    ("HORNER_1", 6000, True),
    ("HORNER_2", 6000, True),
    ("HORNER_3", 6000, False),
]
results = manager.write_coil_multiple(operations)

manager.shutdown()


FLUJO 4: EN UNA GUI (Pseudo-código)
====================================

from system import PLCManager
from PySide6.QtWidgets import QWidget, QLabel

class ControlPanel(QWidget):
    def __init__(self):
        self.manager = PLCManager()
        self.label = QLabel()
        
        # Suscribirse a eventos
        self.manager.on("coil_written", self.on_coil_change)
        
        self.manager.initialize()
    
    def on_coil_change(self, plc_id, address, value):
        # Actualizar UI cuando cambie valor en PLC
        self.label.setText(f"{plc_id}: {address} = {value}")
    
    def button_clicked(self):
        # Escribir y automáticamente se actualiza UI vía evento
        self.manager.write_coil("HORNER_1", 6000, True)
    
    def closeEvent(self, event):
        self.manager.shutdown()
        event.accept()
"""


# ============================================================================
# 4. PATRONES DE DISEÑO UTILIZADOS
# ============================================================================

"""
1. SINGLETON (PLCManager)
   - Un único gestor en toda la aplicación
   - Coordina todos los PLCs

2. FACTORY (PLCManager.initialize)
   - Crea múltiples PLCDevice a partir de configuración
   - Encapsula la lógica de creación

3. OBSERVER / PUB-SUB (EventEmitter)
   - Múltiples suscriptores a eventos
   - Desacoplamiento entre emisor y receptor

4. ADAPTER (PLCDevice)
   - Adapta PyModbus al interfaz que necesitamos
   - Fácil de cambiar la librería Modbus

5. CONFIGURATION OBJECT (PLCConfig)
   - Encapsula datos de configuración
   - Evita parámetros sueltos
"""


# ============================================================================
# 5. EXTENSIONES FUTURAS
# ============================================================================

"""
El diseño actual permite fáciles extensiones:

A. CONFIGURACIÓN POR ARCHIVO
    config = PLCConfigManager()
    config.load_yaml("config.yaml")  # ← Método nuevo
    manager = PLCManager(config)

B. LOGGING AUTOMÁTICO
    manager.on("coil_written", lambda **kw: logger.info(kw))
    manager.on("plc_error", lambda **kw: logger.error(kw))

C. PERSISTENCIA DE ESTADO
    # Guardar estado último leído
    state = {plc_id: device.get_cached_coil(addr) 
             for plc_id, device in manager.devices.items()}

D. OTROS TIPOS DE DISPOSITIVOS
    # Agregar SerialDevice, HTTPDevice, etc.
    # Todos heredan de Device base

E. TESTING Y MOCKS
    # Mock para testing sin hardware real
    class MockPLCDevice(PLCDevice):
        def connect(self):
            self.connected = True
            return True
        
        def read_coil(self, address):
            return self._mock_data.get(address, False)

F. DASHBOARD WEB
    # Usar eventos para actualizar WebSocket
    manager.on("coil_written", websocket.send)

G. BASE DE DATOS
    # Historizar todos los eventos
    manager.on("coil_written", db.insert_event)
"""


# ============================================================================
# 6. CONSIDERACIONES DE PERFORMANCE
# ============================================================================

"""
El sistema es eficiente porque:

1. CACHÉ LOCAL
   - PLCDevice almacena valores leídos
   - get_cached_coil() retorna sin consultar PLC
   - clear_cache() para refrescar cuando necesites

2. NO TIENE POLLING POR DEFECTO
   - Los eventos se emiten cuando haces operaciones
   - Si quieres polling, agrégalo tú con Timer/threading

3. CONEXIONES INDEPENDIENTES
   - Cada PLC tiene su propia conexión Modbus
   - No hay cuello de botella centralizado
   - Posibilidad de paralelizar lecturas en futuro

4. LAZY INITIALIZATION
   - PLCDevice no se crea hasta que lo necesites
   - initialize() conecta solo los PLCs configurados
"""


print(__doc__)
