"""
CLI para escribir/leer variables directamente al PLC Entrada (HORNER_2).
Uso:
  T30 1       -> write_coil(6030, True)
  T30 0       -> write_coil(6030, False)
  T9          -> read_coil(6009)
  R498 500    -> write_register(3497, 500)
  R508        -> read_register(3507)
  I4          -> read_discrete_input(3)
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
        address = 6000 + num

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
        (6030, "T30 STOP (integracion)"),
        (6099, "T99 INICIO (integracion)"),
        (6033, "T33 STOP (individual)"),
        (6999, "T999 INICIO (individual)"),
        (6009, "T9 Lampara verde"),
        (6088, "T88 Lampara amarilla"),
        (6077, "T77 Lampara roja"),
        (6005, "T5 Pluma inicio sube"),
        (6006, "T6 Pluma inicio baja"),
        (6007, "T7 Pluma fin"),
        (6045, "T45 Banda derecha"),
        (6044, "T44 Banda izquierda"),
        (6046, "T46 Banda stop"),
        (6345, "T345 Torreta verde"),
        (6346, "T346 Torreta amarilla"),
        (6347, "T347 Torreta roja"),
        (6995, "T995 sebListo"),
        (6998, "T998 sebCaja"),
        (6997, "T997 UR1"),
        (6996, "T996 UR2"),
    ]
    print("  --- SCAN ENTRADA (HORNER_2) ---")
    for addr, desc in known:
        result = client.read_coils(addr, count=1)
        if result and not result.isError():
            val = 1 if result.bits[0] else 0
            marker = " <--" if val else ""
            print(f"  addr {addr} = {val}  | {desc}{marker}")
        else:
            print(f"  addr {addr} = ERR | {desc}")
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
