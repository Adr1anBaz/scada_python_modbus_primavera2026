# SCADA - Bandas Automatizadas | Horner XL4

Sistema SCADA en Python para controlar 3 PLCs Horner XL4 via Modbus TCP. Incluye una GUI con PySide6 y una arquitectura modular para gestionar multiples PLCs simultaneamente.

## Requisitos

- Python 3.10+
- Red local con acceso a los PLCs (segmento `192.168.3.x`)

## Instalacion

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Dependencias: `PySide6`, `pymodbus`

## Ejecucion

### GUI principal (con conexion a PLCs)

```bash
python3 gui_main.py
```

Abre una ventana con 3 pestanas (una por PLC). Presiona "CONECTAR" para iniciar la comunicacion Modbus. Si los PLCs no estan en red, el boton reporta el fallo en el log.

### GUI de prueba (sin PLCs)

```bash
python3 gui_prueba.py
```

Solo verifica que PySide6 funcione correctamente. No requiere red ni PLCs.

### CLI del sistema

```bash
python3 system_cli.py connect
python3 system_cli.py status
python3 system_cli.py read-coil HORNER_1 6049
python3 system_cli.py write-coil HORNER_3 6049 true
python3 system_cli.py read-register HORNER_1 3169
python3 system_cli.py --help
```

## Estructura del proyecto

```
horner_python_test/
├── gui_main.py            # GUI principal (3 tabs, conecta a PLCs)
├── gui_prueba.py          # GUI de prueba (sin conexion)
├── system_cli.py          # CLI para operaciones rapidas
├── requirements.txt
├── system/                # Modulo backend
│   ├── __init__.py
│   ├── config.py          # Configuracion de PLCs (IPs, puertos)
│   ├── constants.py       # Direcciones Modbus de cada PLC
│   ├── events.py          # Sistema de eventos pub/sub
│   ├── plc_device.py      # Abstraccion de un PLC individual
│   └── plc_manager.py     # Gestor central de multiples PLCs
└── prueba/                # Archivos de pruebas iniciales (legacy)
```

## PLCs configurados

| ID        | IP              | Nombre               | Funcion          |
|-----------|-----------------|----------------------|------------------|
| HORNER_1  | 192.168.3.131   | Horner XL4 - SALIDA  | Banda de salida  |
| HORNER_2  | 192.168.3.132   | Horner XL4 - ENTRADA | Banda de entrada |
| HORNER_3  | 192.168.3.133   | Horner XL4 - CENTRAL | Banda rotatoria  |

## Protocolo Modbus - Convencion de direcciones

Los PLCs Horner XL4 usan estas convenciones de memoria:

| Tipo          | Funcion Modbus        | Rango ejemplo      | Notas                          |
|---------------|-----------------------|--------------------|--------------------------------|
| T (marcas)    | Read/Write Coils (01/05) | 6000 + offset   | T49 = 6049, T76 = 6076        |
| Q (salidas)   | Read Coils (01)       | 0-9                | Q1=0, Q2=1, ..., Q10=9        |
| I (entradas)  | Read Discrete Inputs (02) | 0-4            | I1=0, I2=1, ..., I5=4         |
| R (registros) | Read/Write Holding Registers (03/06) | 3000 + offset | R1=3000, R170=3169 |

## Operaciones disponibles por PLC

### HORNER_2 (Entrada)

- **Coils (write):** Inicio, Stop, Banda izq/der/stop, Plumas sube/baja, Torreta colores
- **Coils (read):** Lamparas verde/amarilla/roja, estados pluma, UR3
- **Inputs (read):** I4 sensor entrada, I5 sensor salida
- **Registros:** VFD frecuencia (R498 escribir, R508 leer)

### HORNER_3 (Central)

- **Coils (write):** Stop, senales de proceso (llego caja, recibio B3, UR3 fin), rotador, banda, torreta
- **Coils (read):** Pilotos de estado, sensores de diagnostico, botones

### HORNER_1 (Salida)

- **Register bits (write):** Init proceso, Stop, LEDs, plumas (todos via bits de R170)
- **Registros (write):** Switch banda (R100), VFD (R498)
- **Registros (read):** Maquina de estados (R1), VFD actual (R508)
- **Inputs (read):** I1-I5 (botones, emergencia, sensores)

---

## Guia: Agregar nuevos registros

### 1. Definir la constante

En `system/constants.py`, agrega la nueva direccion en la seccion del PLC correspondiente:

```python
# En la seccion del PLC que corresponda:
ENTRADA_MI_NUEVA_VARIABLE = 6100    # T100 - descripcion de que hace
```

### 2. Usar en codigo

Desde cualquier parte que tenga acceso al `PLCManager`:

```python
from system.constants import ENTRADA_MI_NUEVA_VARIABLE

# Escribir coil
manager.write_coil("HORNER_2", ENTRADA_MI_NUEVA_VARIABLE, True)

# Leer coil
value = manager.read_coil("HORNER_2", ENTRADA_MI_NUEVA_VARIABLE)

# Leer entrada fisica
value = manager.read_input("HORNER_2", 3)  # I4

# Leer/escribir registro
value = manager.read_register("HORNER_1", 3169)
manager.write_register("HORNER_1", 3497, 500)

# Leer/escribir bit de un registro (para M remapeadas)
bit_val = manager.read_register_bit("HORNER_1", 3169, 4)    # R170.4
manager.write_register_bit("HORNER_1", 3169, 4, True)       # R170.4 = 1
```

### 3. Agregar a la GUI

En `gui_main.py`, dentro del `setup_ui()` del tab correspondiente:

```python
# Agregar un boton
self.btn_nuevo = QPushButton("Mi Accion")
self.btn_nuevo.setStyleSheet(self._btn_style("#1c7ed6"))
self.btn_nuevo.clicked.connect(self.on_mi_accion)
layout.addWidget(self.btn_nuevo)

# Agregar un LED indicador
self.led_nuevo = LedIndicator()
layout.addWidget(self.led_nuevo)
```

Y el handler:

```python
def on_mi_accion(self):
    self._write_coil(ENTRADA_MI_NUEVA_VARIABLE, True, "Mi accion activada")
```

Para leer estado en el polling, agregar dentro de `refresh()`:

```python
self.led_nuevo.update_state(
    self.manager.read_coil(self.PLC_ID, ENTRADA_MI_NUEVA_VARIABLE))
```

---

## Guia: Agregar un nuevo PLC

### 1. Registrar en la configuracion

En `system/config.py`, dentro de `create_default_config()`:

```python
config.register_plc(PLCConfig(
    id="HORNER_4",
    host="192.168.3.134",
    port=502,
    timeout=3,
    name="Horner XL4 - MI NUEVO PLC"
))
```

### 2. Definir sus constantes

En `system/constants.py`, agregar una nueva seccion:

```python
# =============================================================================
# PLC NUEVO (HORNER_4 - 192.168.3.134)
# Descripcion del subsistema
# IMPORTANTE: Estas constantes SOLO aplican para HORNER_4.
# =============================================================================

NUEVO_STOP = 6049               # T49 - STOP
NUEVO_INICIO = 6050             # T50 - Inicio
# ... mas constantes
```

### 3. Crear su tab en la GUI

En `gui_main.py`, crear una nueva clase de tab siguiendo el patron:

```python
class NuevoTab(QWidget):
    """Tab para el nuevo PLC (HORNER_4)."""

    PLC_ID = "HORNER_4"

    def __init__(self, manager: PLCManager, log_callback):
        super().__init__()
        self.manager = manager
        self.log = log_callback
        self.connected = False
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        # ... definir widgets aqui

    def refresh(self):
        """Polling de estado."""
        if not self.connected:
            return
        try:
            # ... leer estados aqui
            pass
        except Exception as e:
            self.log(f"[NUEVO] Error en refresh: {e}")

    def _write_coil(self, address, value, msg):
        try:
            self.manager.write_coil(self.PLC_ID, address, value)
            self.log(f"[NUEVO] {msg}")
        except Exception as e:
            self.log(f"[NUEVO] Error: {e}")

    def _btn_style(self, color):
        return styled_btn(color)
```

### 4. Registrar el tab en MainWindow

En la clase `MainWindow`, agregar:

```python
self.tab_nuevo = NuevoTab(self.manager, self.log_message)
self.tabs.addTab(self.tab_nuevo, "Nuevo (HORNER_4)")
```

Y en `toggle_connection`:

```python
self.tab_nuevo.connected = results.get("HORNER_4", False)
```

Y en `refresh_all`:

```python
self.tab_nuevo.refresh()
```

---

## Notas tecnicas

- El polling de estado se ejecuta cada 500ms (configurable en `self.timer.start(500)`)
- Cada PLC tiene su propia conexion TCP independiente
- Las operaciones de escritura son inmediatas (un click = un write Modbus)
- El sistema de eventos permite suscribirse a cambios sin polling manual
- El cache local en `PLCDevice` almacena el ultimo valor leido para consultas rapidas sin red
