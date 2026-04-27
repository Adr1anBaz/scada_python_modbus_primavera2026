#!/usr/bin/env python3
"""
CLI de ejemplo usando el nuevo sistema PLCManager.
Demuestra cómo trabajar con PLCs de forma centralizada.

Uso:
    python system_cli.py connect
    python system_cli.py status
    python system_cli.py read-coil HORNER_1 6000
    python system_cli.py write-coil HORNER_1 6000 true
    python system_cli.py read-register HORNER_1 3000
    python system_cli.py write-register HORNER_1 3000 123
    python system_cli.py sync-read-coil 6000
    python system_cli.py sync-read-register 3000
"""

import argparse
import sys
from system import PLCManager, EventType
from system.constants import COIL_T1, COIL_Q10, REGISTER_R1


def format_bool(value: bool) -> str:
    """Formatea booleano para salida."""
    return "ON" if value else "OFF"


def setup_event_listeners(manager: PLCManager) -> None:
    """
    Configura listeners de eventos para mostrar cambios en tiempo real.
    Útil para debugging y monitoring.
    """
    
    def on_coil_read(**kwargs):
        plc_id = kwargs.get('plc_id')
        address = kwargs.get('address')
        value = kwargs.get('value')
        print(f"  [EVENTO] Coil leída: {plc_id} @ {address} = {format_bool(value)}")
    
    def on_coil_written(**kwargs):
        plc_id = kwargs.get('plc_id')
        address = kwargs.get('address')
        value = kwargs.get('value')
        print(f"  [EVENTO] Coil escrita: {plc_id} @ {address} = {format_bool(value)}")
    
    def on_register_read(**kwargs):
        plc_id = kwargs.get('plc_id')
        address = kwargs.get('address')
        value = kwargs.get('value')
        print(f"  [EVENTO] Registro leído: {plc_id} @ {address} = {value}")
    
    def on_register_written(**kwargs):
        plc_id = kwargs.get('plc_id')
        address = kwargs.get('address')
        value = kwargs.get('value')
        print(f"  [EVENTO] Registro escrito: {plc_id} @ {address} = {value}")
    
    def on_plc_connected(**kwargs):
        plc_id = kwargs.get('plc_id')
        print(f"  [EVENTO] ✓ PLC conectado: {plc_id}")
    
    def on_plc_error(**kwargs):
        plc_id = kwargs.get('plc_id')
        error = kwargs.get('error')
        print(f"  [EVENTO] ✗ Error en {plc_id}: {error}")
    
    manager.on("coil_read", on_coil_read)
    manager.on("coil_written", on_coil_written)
    manager.on("register_read", on_register_read)
    manager.on("register_written", on_register_written)
    manager.on("plc_connected", on_plc_connected)
    manager.on("plc_error", on_plc_error)


# ============================================================================
# COMANDOS CLI
# ============================================================================

def cmd_connect(manager: PLCManager, args):
    """Conecta a todos los PLCs definidos."""
    print("Conectando PLCs...")
    results = manager.initialize()
    
    for plc_id, success in results.items():
        status = "✓ CONECTADO" if success else "✗ ERROR"
        print(f"  {plc_id}: {status}")
    
    if all(results.values()):
        print("✓ Todos los PLCs conectados exitosamente")
        return 0
    else:
        print("✗ Algunos PLCs no se conectaron")
        return 1


def cmd_status(manager: PLCManager, args):
    """Muestra el estado actual del sistema."""
    print(f"Estado del Sistema: {manager}")
    print("\nPLCs Disponibles:")
    
    for plc_id, name in manager.list_devices().items():
        device = manager.get_device(plc_id)
        status = "✓ CONECTADO" if device.is_connected() else "✗ DESCONECTADO"
        print(f"  {plc_id:20} {name:30} {status}")
    
    return 0


def cmd_disconnect(manager: PLCManager, args):
    """Desconecta todos los PLCs."""
    print("Desconectando PLCs...")
    manager.shutdown()
    print("✓ Todos los PLCs desconectados")
    return 0


def cmd_read_coil(manager: PLCManager, args):
    """Lee una coil específica de un PLC."""
    plc_id = args.plc_id
    address = args.address
    
    try:
        value = manager.read_coil(plc_id, address)
        print(f"Coil {address} en {plc_id} = {format_bool(value)}")
        return 0
    except Exception as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        return 1


def cmd_write_coil(manager: PLCManager, args):
    """Escribe una coil específica en un PLC."""
    plc_id = args.plc_id
    address = args.address
    value = args.value.lower() in {'true', '1', 'on', 'yes'}
    
    try:
        manager.write_coil(plc_id, address, value)
        print(f"✓ Coil {address} en {plc_id} escrita con valor {format_bool(value)}")
        return 0
    except Exception as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        return 1


def cmd_read_register(manager: PLCManager, args):
    """Lee un registro específico de un PLC."""
    plc_id = args.plc_id
    address = args.address
    
    try:
        value = manager.read_register(plc_id, address)
        print(f"Registro {address} en {plc_id} = {value}")
        return 0
    except Exception as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        return 1


def cmd_write_register(manager: PLCManager, args):
    """Escribe un registro específico en un PLC."""
    plc_id = args.plc_id
    address = args.address
    value = args.value
    
    try:
        manager.write_register(plc_id, address, value)
        print(f"✓ Registro {address} en {plc_id} escrito con valor {value}")
        return 0
    except Exception as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        return 1


def cmd_sync_read_coil(manager: PLCManager, args):
    """Lee una coil en TODOS los PLCs conectados."""
    address = args.address
    
    print(f"Leyendo coil {address} de todos los PLCs...")
    results = manager.read_coil_from_all(address)
    
    for plc_id, value in results.items():
        status = format_bool(value) if value is not None else "ERROR"
        print(f"  {plc_id}: {status}")
    
    return 0


def cmd_sync_read_register(manager: PLCManager, args):
    """Lee un registro en TODOS los PLCs conectados."""
    address = args.address
    
    print(f"Leyendo registro {address} de todos los PLCs...")
    results = manager.read_register_from_all(address)
    
    for plc_id, value in results.items():
        status = str(value) if value is not None else "ERROR"
        print(f"  {plc_id}: {status}")
    
    return 0


def cmd_demo(manager: PLCManager, args):
    """Demo completo del sistema."""
    print("=" * 70)
    print("DEMO DEL SISTEMA MULTICONTROLADOR")
    print("=" * 70)
    
    # 1. Estado inicial
    print("\n[1] Conectando PLCs...")
    results = manager.initialize()
    for plc_id, success in results.items():
        status = "✓" if success else "✗"
        print(f"  {status} {plc_id}")
    
    # 2. Leer coil Q10
    print("\n[2] Leyendo Q10 (coil de salida)...")
    try:
        q10_value = manager.read_coil("HORNER_1", COIL_Q10)
        print(f"  Q10 = {format_bool(q10_value)}")
    except Exception as e:
        print(f"  ✗ Error: {e}")
    
    # 3. Escribir T1
    print("\n[3] Escribiendo T1 = ON...")
    try:
        manager.write_coil("HORNER_1", COIL_T1, True)
        print(f"  ✓ T1 = ON")
    except Exception as e:
        print(f"  ✗ Error: {e}")
    
    # 4. Leer Q10 nuevamente
    print("\n[4] Leyendo Q10 nuevamente...")
    try:
        q10_value = manager.read_coil("HORNER_1", COIL_Q10)
        print(f"  Q10 = {format_bool(q10_value)}")
    except Exception as e:
        print(f"  ✗ Error: {e}")
    
    # 5. Leer/Escribir registro
    print("\n[5] Leyendo registro R1...")
    try:
        r1_value = manager.read_register("HORNER_1", REGISTER_R1)
        print(f"  R1 (antes) = {r1_value}")
    except Exception as e:
        print(f"  ✗ Error: {e}")
    
    print("\n[6] Escribiendo R1 = 9999...")
    try:
        manager.write_register("HORNER_1", REGISTER_R1, 9999)
        print(f"  ✓ R1 = 9999")
    except Exception as e:
        print(f"  ✗ Error: {e}")
    
    print("\n[7] Verificando R1...")
    try:
        r1_value = manager.read_register("HORNER_1", REGISTER_R1)
        print(f"  R1 (después) = {r1_value}")
    except Exception as e:
        print(f"  ✗ Error: {e}")
    
    # 8. Apagar T1
    print("\n[8] Escribiendo T1 = OFF...")
    try:
        manager.write_coil("HORNER_1", COIL_T1, False)
        print(f"  ✓ T1 = OFF")
    except Exception as e:
        print(f"  ✗ Error: {e}")
    
    print("\n[9] Estado final de Q10...")
    try:
        q10_value = manager.read_coil("HORNER_1", COIL_Q10)
        print(f"  Q10 = {format_bool(q10_value)}")
    except Exception as e:
        print(f"  ✗ Error: {e}")
    
    print("\n" + "=" * 70)
    print("✓ DEMO COMPLETADA")
    print("=" * 70)
    
    return 0


# ============================================================================
# PARSER DE ARGUMENTOS
# ============================================================================

def build_parser() -> argparse.ArgumentParser:
    """Construye el parser de línea de comandos."""
    
    parser = argparse.ArgumentParser(
        description="CLI para controlar múltiples PLCs Horner vía Modbus TCP",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python system_cli.py connect
  python system_cli.py status
  python system_cli.py read-coil HORNER_1 6000
  python system_cli.py write-coil HORNER_1 6000 true
  python system_cli.py read-register HORNER_1 3000
  python system_cli.py sync-read-coil 6000
  python system_cli.py demo
        """
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Mostrar eventos en tiempo real'
    )
    
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # connect
    subparsers.add_parser("connect", help="Conectar a todos los PLCs")
    
    # status
    subparsers.add_parser("status", help="Mostrar estado del sistema")
    
    # disconnect
    subparsers.add_parser("disconnect", help="Desconectar todos los PLCs")
    
    # read-coil
    parser_read_coil = subparsers.add_parser("read-coil", help="Leer una coil")
    parser_read_coil.add_argument("plc_id", help="ID del PLC")
    parser_read_coil.add_argument("address", type=int, help="Dirección de la coil")
    
    # write-coil
    parser_write_coil = subparsers.add_parser("write-coil", help="Escribir una coil")
    parser_write_coil.add_argument("plc_id", help="ID del PLC")
    parser_write_coil.add_argument("address", type=int, help="Dirección de la coil")
    parser_write_coil.add_argument("value", help="Valor (true/false, 1/0, on/off)")
    
    # read-register
    parser_read_reg = subparsers.add_parser("read-register", help="Leer un registro")
    parser_read_reg.add_argument("plc_id", help="ID del PLC")
    parser_read_reg.add_argument("address", type=int, help="Dirección del registro")
    
    # write-register
    parser_write_reg = subparsers.add_parser("write-register", help="Escribir un registro")
    parser_write_reg.add_argument("plc_id", help="ID del PLC")
    parser_write_reg.add_argument("address", type=int, help="Dirección del registro")
    parser_write_reg.add_argument("value", type=int, help="Valor a escribir")
    
    # sync-read-coil (lectura en TODOS los PLCs)
    parser_sync_coil = subparsers.add_parser(
        "sync-read-coil",
        help="Leer coil en TODOS los PLCs"
    )
    parser_sync_coil.add_argument("address", type=int, help="Dirección de la coil")
    
    # sync-read-register (lectura en TODOS los PLCs)
    parser_sync_reg = subparsers.add_parser(
        "sync-read-register",
        help="Leer registro en TODOS los PLCs"
    )
    parser_sync_reg.add_argument("address", type=int, help="Dirección del registro")
    
    # demo
    subparsers.add_parser("demo", help="Ejecutar demo completo del sistema")
    
    return parser


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Entrada principal."""
    
    parser = build_parser()
    args = parser.parse_args()
    
    # Crear manager
    manager = PLCManager()
    
    # Configurar listeners si está en debug
    if args.debug:
        setup_event_listeners(manager)
    
    # Ejecutar comando
    if args.command == "connect":
        return cmd_connect(manager, args)
    
    elif args.command == "status":
        return cmd_status(manager, args)
    
    elif args.command == "disconnect":
        return cmd_disconnect(manager, args)
    
    elif args.command == "read-coil":
        manager.initialize()
        try:
            return cmd_read_coil(manager, args)
        finally:
            manager.shutdown()
    
    elif args.command == "write-coil":
        manager.initialize()
        try:
            return cmd_write_coil(manager, args)
        finally:
            manager.shutdown()
    
    elif args.command == "read-register":
        manager.initialize()
        try:
            return cmd_read_register(manager, args)
        finally:
            manager.shutdown()
    
    elif args.command == "write-register":
        manager.initialize()
        try:
            return cmd_write_register(manager, args)
        finally:
            manager.shutdown()
    
    elif args.command == "sync-read-coil":
        manager.initialize()
        try:
            return cmd_sync_read_coil(manager, args)
        finally:
            manager.shutdown()
    
    elif args.command == "sync-read-register":
        manager.initialize()
        try:
            return cmd_sync_read_register(manager, args)
        finally:
            manager.shutdown()
    
    elif args.command == "demo":
        try:
            return cmd_demo(manager, args)
        finally:
            manager.shutdown()


if __name__ == "__main__":
    sys.exit(main())
