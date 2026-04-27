"""
Sistema de eventos para notificar cambios en PLCs.
Permite que múltiples componentes se suscriban a eventos sin acoplamiento.
"""

from typing import Callable, Dict, List
from enum import Enum


class EventType(Enum):
    """Tipos de eventos que puede emitir el sistema."""
    
    # Conexión
    PLC_CONNECTED = "plc_connected"
    PLC_DISCONNECTED = "plc_disconnected"
    PLC_ERROR = "plc_error"
    
    # Lectura/Escritura
    COIL_READ = "coil_read"
    COIL_WRITTEN = "coil_written"
    REGISTER_READ = "register_read"
    REGISTER_WRITTEN = "register_written"


class EventEmitter:
    """
    Emisor de eventos. Permite suscripción y publicación de eventos.
    Patrón: Observer/Pub-Sub
    """
    
    def __init__(self):
        self._listeners: Dict[str, List[Callable]] = {}
    
    def on(self, event_name: str, callback: Callable) -> None:
        """
        Suscribirse a un evento.
        
        Args:
            event_name: Nombre del evento (puede ser string o EventType)
            callback: Función a ejecutar cuando ocurra el evento
        """
        if isinstance(event_name, EventType):
            event_name = event_name.value
        
        if event_name not in self._listeners:
            self._listeners[event_name] = []
        
        self._listeners[event_name].append(callback)
    
    def off(self, event_name: str, callback: Callable) -> None:
        """Desuscribirse de un evento."""
        if isinstance(event_name, EventType):
            event_name = event_name.value
        
        if event_name in self._listeners:
            self._listeners[event_name].remove(callback)
    
    def emit(self, event_name: str, *args, **kwargs) -> None:
        """
        Emitir un evento a todos los suscriptores.
        
        Args:
            event_name: Nombre del evento
            *args: Argumentos posicionales para los callbacks
            **kwargs: Argumentos nombrados para los callbacks
        """
        if isinstance(event_name, EventType):
            event_name = event_name.value
        
        if event_name in self._listeners:
            for callback in self._listeners[event_name]:
                try:
                    callback(*args, **kwargs)
                except Exception as e:
                    print(f"Error en callback de evento '{event_name}': {e}")
    
    def clear(self) -> None:
        """Limpiar todos los listeners."""
        self._listeners.clear()
