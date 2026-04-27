"""
Configuración centralizada de PLCs.
Define todos los PLCs disponibles en el sistema.
"""

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class PLCConfig:
    """Configuración de un PLC individual."""
    
    id: str
    host: str
    port: int = 502
    timeout: int = 3
    name: str = ""
    
    def __post_init__(self):
        if not self.name:
            self.name = self.id


class PLCConfigManager:
    """Gestor de configuraciones de PLCs."""
    
    def __init__(self):
        self.plcs: Dict[str, PLCConfig] = {}
    
    def register_plc(self, plc_config: PLCConfig) -> None:
        """Registra un nuevo PLC."""
        self.plcs[plc_config.id] = plc_config
    
    def get_plc(self, plc_id: str) -> PLCConfig:
        """Obtiene la configuración de un PLC por ID."""
        if plc_id not in self.plcs:
            raise ValueError(f"PLC '{plc_id}' no encontrado en la configuración")
        return self.plcs[plc_id]
    
    def get_all_plcs(self) -> List[PLCConfig]:
        """Retorna todas las configuraciones de PLCs."""
        return list(self.plcs.values())
    
    def list_plcs(self) -> Dict[str, str]:
        """Retorna un dict con ID -> nombre de cada PLC."""
        return {plc.id: plc.name for plc in self.plcs.values()}


# ============================================================================
# Configuración por defecto del sistema
# ============================================================================

def create_default_config() -> PLCConfigManager:
    """
    Crea la configuración por defecto.
    Actualmente solo tiene el PLC de la escuela.
    """
    config = PLCConfigManager()
    
    # PLC actual de desarrollo
    config.register_plc(PLCConfig(
        id="HORNER_1",
        host="192.168.3.12",
        port=502,
        timeout=3,
        name="Horner XL4 - Escuela"
    ))
    
    # Aquí se pueden agregar más PLCs en el futuro:
    # config.register_plc(PLCConfig(
    #     id="HORNER_2",
    #     host="192.168.3.13",
    #     port=502,
    #     name="Horner XL4 - Producción"
    # ))
    
    return config
