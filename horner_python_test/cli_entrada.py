"""
CLI para escribir/leer variables directamente al PLC Entrada (HORNER_2).
Uso:
  T30 1       -> write_coil(6029, True)   [offset -1: addr = 5999 + n]
  T30 0       -> write_coil(6029, False)
  T9          -> read_coil(6008)
  R498 500    -> write_register(3497, 500)
  R508        -> read_register(3507)
  I4          -> read_discrete_input(3)
  Q8          -> read_coil(7) [salidas fisicas]
  scan        -> lee todas las T conocidas y muestra su estado
  q           -> salir
"""

from pymodbus.client import ModbusTcpClient

HOST = "192.168.3.132"
PORT = 502

client = ModbusTcpClient(host=HOST, port=PORT, timeout=3)


def parse_command(cmd: str):
    parts = cmd.strip().split()
    if not parts:
        return

    token = parts[0].upper()

    if token == "Q":
        return "quit"

    if token == "SCAN":
        scan_coils()
        return

    if token.startswith("I"):
        try:
            num = int(token[1:])
        except ValueError:
            print(f"  Error: '{token}' no es un I valido")
            return
        address = num - 1  # I1=0, I2=1, ...
        result = client.read_discrete_inputs(address, count=1)
        if result and not result.isError():
            val = 1 if result.bits[0] else 0
            print(f"  I{num} (addr {address}) = {val}")
        else:
            print(f"  ERROR leyendo I{num}: {result}")
        return

    if token.startswith("T"):
        try:
            num = int(token[1:])
        except ValueError:
            print(f"  Error: '{token}' no es una T valida")
            return
        address = 5999 + num

        if len(parts) >= 2:
            try:
                val = int(parts[1])
            except ValueError:
                val = 0
            value = val != 0
            result = client.write_coil(address, value)
            if result and not result.isError():
                print(f"  OK: T{num} (addr {address}) = {1 if value else 0}")
            else:
                print(f"  ERROR escribiendo T{num}: {result}")
        else:
            result = client.read_coils(address, count=1)
            if result and not result.isError():
                val = result.bits[0]
                print(f"  T{num} (addr {address}) = {1 if val else 0}")
            else:
                print(f"  ERROR leyendo T{num}: {result}")
        return

    if token.startswith("R"):
        try:
            num = int(token[1:])
        except ValueError:
            print(f"  Error: '{token}' no es un R valido")
            return
        address = 2999 + num  # R1 = 3000, R2 = 3001, ...

        if len(parts) >= 2:
            try:
                val = int(parts[1])
            except ValueError:
                val = 0
            result = client.write_register(address, val)
            if result and not result.isError():
                print(f"  OK: R{num} (addr {address}) = {val}")
            else:
                print(f"  ERROR escribiendo R{num}: {result}")
        else:
            result = client.read_holding_registers(address, count=1)
            if result and not result.isError():
                val = result.registers[0]
                print(f"  R{num} (addr {address}) = {val}")
            else:
                print(f"  ERROR leyendo R{num}: {result}")
        return

    if token.startswith("Q"):
        try:
            num = int(token[1:])
        except ValueError:
            print(f"  Error: '{token}' no es un Q valido")
            return
        address = num - 1  # Q1=0, Q2=1, ...
        result = client.read_coils(address, count=1)
        if result and not result.isError():
            val = 1 if result.bits[0] else 0
            print(f"  Q{num} (addr {address}) = {val}")
        else:
            print(f"  ERROR leyendo Q{num}: {result}")
        return

    print(f"  Comando no reconocido: {token}")
    print("  Uso: T<num> [0|1]  |  R<num> [valor]  |  I<num>  |  Q<num>  |  scan  |  q")


def scan_coils():
    known = [
        (6050, "T51 Modo Integracion"),
        (6051, "T52 Modo Individual"),
        (6052, "T53 Modo Prueba (hold)"),
        (6029, "T30 STOP (integracion)"),
        (6098, "T99 INICIO (integracion)"),
        (6032, "T33 STOP (individual)"),
        (6998, "T999 INICIO (individual)"),
        (6008, "T9 Lampara verde"),
        (6087, "T88 Lampara amarilla"),
        (6076, "T77 Lampara roja"),
        (6004, "T5 Pluma inicio sube"),
        (6005, "T6 Pluma inicio baja"),
        (6006, "T7 Pluma fin sube"),
        (6007, "T8 Pluma fin baja"),
        (6043, "T44 Banda izquierda"),
        (6044, "T45 Banda stop/paro"),
        (6045, "T46 Banda derecha"),
        (6344, "T345 Torreta verde"),
        (6345, "T346 Torreta amarilla"),
        (6346, "T347 Torreta roja"),
        (6994, "T995 sebListo"),
        (6997, "T998 sebCaja"),
        (6996, "T997 UR1"),
        (6995, "T996 UR2"),
    ]
    print("  --- SCAN ENTRADA (HORNER_2) ---")
    print("  --- Coils (T markers) ---")
    for addr, desc in known:
        result = client.read_coils(addr, count=1)
        if result and not result.isError():
            val = 1 if result.bits[0] else 0
            marker = " <--" if val else ""
            print(f"  addr {addr} = {val}{marker}  | {desc}")
        else:
            print(f"  addr {addr} = ERR  | {desc}")

    print()
    print("  --- Salidas fisicas (Q) ---")
    q_outputs = [
        (5, "Q6 Pluma fin arriba"),
        (6, "Q7 Pluma fin abajo"),
        (7, "Q8 Pluma inicio arriba"),
        (8, "Q9 Pluma inicio abajo"),
    ]
    for addr, desc in q_outputs:
        result = client.read_coils(addr, count=1)
        if result and not result.isError():
            val = 1 if result.bits[0] else 0
            marker = " <--" if val else ""
            print(f"  addr {addr} = {val}{marker}  | {desc}")
        else:
            print(f"  addr {addr} = ERR  | {desc}")

    print()
    print("  --- Entradas fisicas (I) ---")
    inputs = [
        (3, "I4 Sensor entrada"),
        (4, "I5 Sensor salida"),
    ]
    for addr, desc in inputs:
        result = client.read_discrete_inputs(addr, count=1)
        if result and not result.isError():
            val = 1 if result.bits[0] else 0
            marker = " <--" if val else ""
            print(f"  addr {addr} = {val}{marker}  | {desc}")
        else:
            print(f"  addr {addr} = ERR  | {desc}")

    print()
    print("  --- Registros ---")
    regs = [
        (3497, "R498 - VFD escribir"),
        (3507, "R508 - VFD leer"),
    ]
    for addr, desc in regs:
        result = client.read_holding_registers(addr, count=1)
        if result and not result.isError():
            val = result.registers[0]
            print(f"  addr {addr} = {val}  | {desc}")
        else:
            print(f"  addr {addr} = ERR  | {desc}")

    print("  --- FIN SCAN ---")


def main():
    print(f"Conectando a HORNER_2 ({HOST}:{PORT})...")
    if not client.connect():
        print("ERROR: No se pudo conectar al PLC Entrada.")
        return

    print("Conectado. Escribe comandos (T<num> [val], R<num> [val], I<num>, Q<num>, scan, q)")
    print()

    try:
        while True:
            try:
                cmd = input("entrada> ")
            except (EOFError, KeyboardInterrupt):
                break

            result = parse_command(cmd)
            if result == "quit":
                break
    finally:
        client.close()
        print("Desconectado.")


if __name__ == "__main__":
    main()
