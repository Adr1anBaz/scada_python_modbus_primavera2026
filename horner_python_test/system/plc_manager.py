"""
Gestor centralizado de múltiples PLCs.
Coordina todas las conexiones y operaciones.
"""

from typing import Dict, List, Optional, Tuple
from .plc_device import PLCDevice
from .config import PLCConfig, PLCConfigManager, create_default_config
from .events import EventEmitter


class PLCManager(EventEmitter):
    """
    Gestor central que coordina múltiples PLCs.
    
    Características:
    - Gestiona múltiples conexiones PLC simultáneamente
    - Proporciona interfaz unificada para operaciones
    - Emite eventos globales del sistema
    - Facilita operaciones sincronizadas en múltiples PLCs
    """
    
    def __init__(self, config: Optional[PLCConfigManager] = None):
        """
        Inicializa el gestor de PLCs.
        
        Args:
            config: Configuración de PLCs (si es None, usa la configuración por defecto)
        """
        super().__init__()
        
        self.config = config or create_default_config()
        self.devices: Dict[str, PLCDevice] = {}
    
    def initialize(self) -> Dict[str, bool]:
        """
        Inicializa todos los PLCs definidos en la configuración.
        
        Returns:
            Dict con plc_id -> estado de conexión (True/False)
        """
        results = {}
        
        for plc_config in self.config.get_all_plcs():
            device = PLCDevice(
                plc_id=plc_config.id,
                host=plc_config.host,
                port=plc_config.port,
                timeout=plc_config.timeout
            )
            
            # Reemitir eventos del dispositivo
            device.on("plc_connected", 
                     lambda plc_id=plc_config.id: self.emit("plc_connected", plc_id=plc_id))
            device.on("plc_disconnected",
                     lambda plc_id=plc_config.id: self.emit("plc_disconnected", plc_id=plc_id))
            device.on("plc_error",
                     lambda error, plc_id=plc_config.id: self.emit("plc_error", plc_id=plc_id, error=error))
            device.on("coil_read",
                     lambda address, value, plc_id=plc_config.id: self.emit("coil_read", plc_id=plc_id, address=address, value=value))
            device.on("coil_written",
                     lambda address, value, plc_id=plc_config.id: self.emit("coil_written", plc_id=plc_id, address=address, value=value))
            device.on("input_read",
                     lambda address, value, plc_id=plc_config.id: self.emit("input_read", plc_id=plc_id, address=address, value=value))
            device.on("register_read",
                     lambda address, value, plc_id=plc_config.id: self.emit("register_read", plc_id=plc_id, address=address, value=value))
            device.on("register_written",
                     lambda address, value, plc_id=plc_config.id: self.emit("register_written", plc_id=plc_id, address=address, value=value))
            
            self.devices[plc_config.id] = device
            results[plc_config.id] = device.connect()
        
        return results
    
    def shutdown(self) -> None:
        """Desconecta todos los PLCs."""
        for device in self.devices.values():
            device.disconnect()
        self.devices.clear()
    
    # =========================================================================
    # ACCESO A DISPOSITIVOS
    # =========================================================================
    
    def get_device(self, plc_id: str) -> PLCDevice:
        """
        Obtiene un dispositivo PLC por su ID.
        
        Args:
            plc_id: Identificador del PLC
            
        Returns:
            PLCDevice correspondiente
            
        Raises:
            ValueError: Si el PLC_id no existe
        """
        if plc_id not in self.devices:
            raise ValueError(f"PLC '{plc_id}' no encontrado")
        return self.devices[plc_id]
    
    def list_devices(self) -> Dict[str, str]:
        """Retorna dict con plc_id -> nombre de todos los PLCs."""
        return {
            plc_id: self.config.get_plc(plc_id).name
            for plc_id in self.devices.keys()
        }
    
    def is_connected(self, plc_id: str) -> bool:
        """Verifica si un PLC específico está conectado."""
        return self.get_device(plc_id).is_connected()
    
    # =========================================================================
    # OPERACIONES CON COILS (acceso directo desde el manager)
    # =========================================================================
    
    def read_coil(self, plc_id: str, address: int) -> bool:
        """Lee una coil en un PLC específico."""
        return self.get_device(plc_id).read_coil(address)
    
    def write_coil(self, plc_id: str, address: int, value: bool) -> None:
        """Escribe una coil en un PLC específico."""
        self.get_device(plc_id).write_coil(address, value)
    
    def write_coil_multiple(self, operations: List[Tuple[str, int, bool]]) -> Dict[str, bool]:
        """
        Escribe múltiples coils en diferentes PLCs.
        
        Args:
            operations: Lista de tuplas (plc_id, address, value)
            
        Returns:
            Dict con (plc_id, address) -> éxito
        """
        results = {}
        
        for plc_id, address, value in operations:
            try:
                self.write_coil(plc_id, address, value)
                results[(plc_id, address)] = True
            except Exception as e:
                print(f"Error en {plc_id} coil {address}: {e}")
                results[(plc_id, address)] = False
        
        return results
    
    # =========================================================================
    # OPERACIONES CON DISCRETE INPUTS (entradas físicas, solo lectura)
    # =========================================================================

    def read_input(self, plc_id: str, address: int) -> bool:
        """Lee una entrada discreta en un PLC específico."""
        return self.get_device(plc_id).read_input(address)

    def read_input_from_all(self, address: int) -> Dict[str, bool]:
        """
        Lee la misma entrada discreta en todos los PLCs.

        Args:
            address: Dirección del input

        Returns:
            Dict con plc_id -> valor
        """
        results = {}

        for plc_id, device in self.devices.items():
            try:
                results[plc_id] = device.read_input(address)
            except Exception as e:
                print(f"Error leyendo input {address} en {plc_id}: {e}")
                results[plc_id] = None

        return results

    # =========================================================================
    # OPERACIONES CON REGISTROS (acceso directo desde el manager)
    # =========================================================================

    def read_register(self, plc_id: str, address: int) -> int:
        """Lee un registro en un PLC específico."""
        return self.get_device(plc_id).read_register(address)

    def write_register(self, plc_id: str, address: int, value: int) -> None:
        """Escribe un registro en un PLC específico."""
        self.get_device(plc_id).write_register(address, value)

    def read_register_bit(self, plc_id: str, address: int, bit: int) -> bool:
        """Lee un bit específico de un registro en un PLC."""
        return self.get_device(plc_id).read_register_bit(address, bit)

    def write_register_bit(self, plc_id: str, address: int, bit: int, state: bool) -> None:
        """Escribe un bit específico de un registro en un PLC sin afectar los demás."""
        self.get_device(plc_id).write_register_bit(address, bit, state)
    
    def write_register_multiple(self, operations: List[Tuple[str, int, int]]) -> Dict[str, bool]:
        """
        Escribe múltiples registros en diferentes PLCs.
        
        Args:
            operations: Lista de tuplas (plc_id, address, value)
            
        Returns:
            Dict con (plc_id, address) -> éxito
        """
        results = {}
        
        for plc_id, address, value in operations:
            try:
                self.write_register(plc_id, address, value)
                results[(plc_id, address)] = True
            except Exception as e:
                print(f"Error en {plc_id} registro {address}: {e}")
                results[(plc_id, address)] = False
        
        return results
    
    # =========================================================================
    # OPERACIONES SINCRONIZADAS (lectura en múltiples PLCs)
    # =========================================================================
    
    def read_coil_from_all(self, address: int) -> Dict[str, bool]:
        """
        Lee la misma coil en todos los PLCs.
        
        Args:
            address: Dirección de la coil
            
        Returns:
            Dict con plc_id -> valor
        """
        results = {}
        
        for plc_id, device in self.devices.items():
            try:
                results[plc_id] = device.read_coil(address)
            except Exception as e:
                print(f"Error leyendo coil {address} en {plc_id}: {e}")
                results[plc_id] = None
        
        return results
    
    def read_register_from_all(self, address: int) -> Dict[str, int]:
        """
        Lee el mismo registro en todos los PLCs.
        
        Args:
            address: Dirección del registro
            
        Returns:
            Dict con plc_id -> valor
        """
        results = {}
        
        for plc_id, device in self.devices.items():
            try:
                results[plc_id] = device.read_register(address)
            except Exception as e:
                print(f"Error leyendo registro {address} en {plc_id}: {e}")
                results[plc_id] = None
        
        return results
    
    def __repr__(self) -> str:
        connected_count = sum(1 for d in self.devices.values() if d.is_connected())
        return f"<PLCManager: {connected_count}/{len(self.devices)} PLCs conectados>"
