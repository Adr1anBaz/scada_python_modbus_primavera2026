"""
Abstracción de un PLC individual.
Encapsula la lógica Modbus para un solo dispositivo.
"""

from pymodbus.client import ModbusTcpClient
from typing import Optional
from .events import EventEmitter, EventType


class PLCDevice(EventEmitter):
    """
    Representa un PLC individual con su propia conexión Modbus.
    
    Características:
    - Gestión independiente de conexión
    - Caché local del estado
    - Emisión de eventos para cambios
    - Reintentos automáticos de conexión
    """
    
    def __init__(self, plc_id: str, host: str, port: int = 502, timeout: int = 3):
        """
        Inicializa un dispositivo PLC.
        
        Args:
            plc_id: Identificador único del PLC
            host: Dirección IP del PLC
            port: Puerto Modbus TCP (default 502)
            timeout: Timeout en segundos (default 3)
        """
        super().__init__()
        
        self.plc_id = plc_id
        self.host = host
        self.port = port
        self.timeout = timeout
        
        self.client = ModbusTcpClient(
            host=host,
            port=port,
            timeout=timeout
        )
        
        self.connected = False
        self._coil_cache = {}
        self._input_cache = {}
        self._register_cache = {}
    
    def connect(self) -> bool:
        """
        Conecta al PLC.
        
        Returns:
            True si la conexión fue exitosa, False en caso contrario
        """
        try:
            self.connected = self.client.connect()
            
            if self.connected:
                self.emit(EventType.PLC_CONNECTED, plc_id=self.plc_id)
            else:
                self.emit(
                    EventType.PLC_ERROR,
                    plc_id=self.plc_id,
                    error=f"No se pudo conectar a {self.host}:{self.port}"
                )
            
            return self.connected
        
        except Exception as e:
            self.connected = False
            self.emit(
                EventType.PLC_ERROR,
                plc_id=self.plc_id,
                error=str(e)
            )
            return False
    
    def disconnect(self) -> None:
        """Desconecta del PLC."""
        if self.connected:
            self.client.close()
            self.connected = False
            self.emit(EventType.PLC_DISCONNECTED, plc_id=self.plc_id)
    
    def is_connected(self) -> bool:
        """Retorna el estado de conexión."""
        return self.connected
    
    # =========================================================================
    # OPERACIONES CON COILS (Entradas/Salidas Binarias)
    # =========================================================================
    
    def read_coil(self, address: int) -> bool:
        """
        Lee una coil (entrada/salida binaria).
        
        Args:
            address: Dirección Modbus de la coil
            
        Returns:
            Valor booleano leído
            
        Raises:
            RuntimeError: Si hay error en la lectura
        """
        if not self.connected:
            raise RuntimeError(f"PLC {self.plc_id} no está conectado")
        
        try:
            result = self.client.read_coils(address, count=1)
            
            if result is None or result.isError():
                raise RuntimeError(f"Error al leer coil {address}: {result}")
            
            value = bool(result.bits[0])
            self._coil_cache[address] = value
            
            self.emit(
                EventType.COIL_READ,
                plc_id=self.plc_id,
                address=address,
                value=value
            )
            
            return value
        
        except Exception as e:
            self.emit(
                EventType.PLC_ERROR,
                plc_id=self.plc_id,
                error=str(e)
            )
            raise RuntimeError(f"Error leyendo coil {address} en {self.plc_id}: {e}")
    
    def write_coil(self, address: int, value: bool) -> None:
        """
        Escribe una coil (entrada/salida binaria).
        
        Args:
            address: Dirección Modbus de la coil
            value: Valor booleano a escribir
            
        Raises:
            RuntimeError: Si hay error en la escritura
        """
        if not self.connected:
            raise RuntimeError(f"PLC {self.plc_id} no está conectado")
        
        try:
            result = self.client.write_coil(address, value)
            
            if result is None or result.isError():
                raise RuntimeError(f"Error al escribir coil {address}: {result}")
            
            self._coil_cache[address] = value
            
            self.emit(
                EventType.COIL_WRITTEN,
                plc_id=self.plc_id,
                address=address,
                value=value
            )
        
        except Exception as e:
            self.emit(
                EventType.PLC_ERROR,
                plc_id=self.plc_id,
                error=str(e)
            )
            raise RuntimeError(f"Error escribiendo coil {address} en {self.plc_id}: {e}")
    
    # =========================================================================
    # OPERACIONES CON DISCRETE INPUTS (Entradas físicas - solo lectura)
    # =========================================================================

    def read_input(self, address: int) -> bool:
        """
        Lee una entrada discreta (input físico del PLC).
        Usa read_discrete_inputs de Modbus (función 02).

        Args:
            address: Dirección Modbus de la entrada (I1=0, I2=1, ...)

        Returns:
            Valor booleano leído

        Raises:
            RuntimeError: Si hay error en la lectura
        """
        if not self.connected:
            raise RuntimeError(f"PLC {self.plc_id} no está conectado")

        try:
            result = self.client.read_discrete_inputs(address, count=1)

            if result is None or result.isError():
                raise RuntimeError(f"Error al leer input {address}: {result}")

            value = bool(result.bits[0])
            self._input_cache[address] = value

            self.emit(
                EventType.INPUT_READ,
                plc_id=self.plc_id,
                address=address,
                value=value
            )

            return value

        except Exception as e:
            self.emit(
                EventType.PLC_ERROR,
                plc_id=self.plc_id,
                error=str(e)
            )
            raise RuntimeError(f"Error leyendo input {address} en {self.plc_id}: {e}")

    # =========================================================================
    # OPERACIONES CON REGISTROS (Valores de 16 bits)
    # =========================================================================
    
    def read_register(self, address: int) -> int:
        """
        Lee un registro (valor de 16 bits).
        
        Args:
            address: Dirección Modbus del registro
            
        Returns:
            Valor entero leído
            
        Raises:
            RuntimeError: Si hay error en la lectura
        """
        if not self.connected:
            raise RuntimeError(f"PLC {self.plc_id} no está conectado")
        
        try:
            result = self.client.read_holding_registers(address=address, count=1)
            
            if result is None or result.isError():
                raise RuntimeError(f"Error al leer registro {address}: {result}")
            
            value = int(result.registers[0])
            self._register_cache[address] = value
            
            self.emit(
                EventType.REGISTER_READ,
                plc_id=self.plc_id,
                address=address,
                value=value
            )
            
            return value
        
        except Exception as e:
            self.emit(
                EventType.PLC_ERROR,
                plc_id=self.plc_id,
                error=str(e)
            )
            raise RuntimeError(f"Error leyendo registro {address} en {self.plc_id}: {e}")
    
    def write_register(self, address: int, value: int) -> None:
        """
        Escribe un registro (valor de 16 bits).
        
        Args:
            address: Dirección Modbus del registro
            value: Valor entero a escribir
            
        Raises:
            RuntimeError: Si hay error en la escritura
        """
        if not self.connected:
            raise RuntimeError(f"PLC {self.plc_id} no está conectado")
        
        try:
            result = self.client.write_register(address=address, value=value)
            
            if result is None or result.isError():
                raise RuntimeError(f"Error al escribir registro {address}: {result}")
            
            self._register_cache[address] = value
            
            self.emit(
                EventType.REGISTER_WRITTEN,
                plc_id=self.plc_id,
                address=address,
                value=value
            )
        
        except Exception as e:
            self.emit(
                EventType.PLC_ERROR,
                plc_id=self.plc_id,
                error=str(e)
            )
            raise RuntimeError(f"Error escribiendo registro {address} en {self.plc_id}: {e}")
    
    # =========================================================================
    # OPERACIONES CON BITS DE REGISTRO
    # Útil cuando múltiples señales (M) están mapeadas como bits de un registro.
    # Ejemplo: R170.4 = bit 4 del registro en dirección 3169
    # =========================================================================

    def read_register_bit(self, address: int, bit: int) -> bool:
        """
        Lee un bit específico de un registro.

        Args:
            address: Dirección Modbus del registro
            bit: Número de bit (0-15)

        Returns:
            True si el bit está en 1, False si está en 0
        """
        value = self.read_register(address)
        return bool(value & (1 << bit))

    def write_register_bit(self, address: int, bit: int, state: bool) -> None:
        """
        Escribe un bit específico de un registro sin afectar los demás.
        Lee el registro actual, modifica el bit, y lo escribe de vuelta.

        Args:
            address: Dirección Modbus del registro
            bit: Número de bit (0-15)
            state: True para setear (1), False para limpiar (0)
        """
        current = self.read_register(address)

        if state:
            new_value = current | (1 << bit)
        else:
            new_value = current & ~(1 << bit)

        self.write_register(address, new_value)

    # =========================================================================
    # CACHÉ Y UTILIDADES
    # =========================================================================
    
    def get_cached_coil(self, address: int) -> Optional[bool]:
        """Obtiene el valor cacheado de una coil sin consultar el PLC."""
        return self._coil_cache.get(address)

    def get_cached_input(self, address: int) -> Optional[bool]:
        """Obtiene el valor cacheado de un input sin consultar el PLC."""
        return self._input_cache.get(address)

    def get_cached_register(self, address: int) -> Optional[int]:
        """Obtiene el valor cacheado de un registro sin consultar el PLC."""
        return self._register_cache.get(address)

    def clear_cache(self) -> None:
        """Limpia la caché local."""
        self._coil_cache.clear()
        self._input_cache.clear()
        self._register_cache.clear()
    
    def __repr__(self) -> str:
        status = "conectado" if self.connected else "desconectado"
        return f"<PLCDevice {self.plc_id} ({self.host}:{self.port}) - {status}>"
