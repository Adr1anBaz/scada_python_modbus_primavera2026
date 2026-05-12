"""
CLI para escribir/leer variables directamente al PLC Central (HORNER_3).
Uso:
  T51 1       -> write_coil(6051, True)
  T51 0       -> write_coil(6051, False)
  T49         -> read_coil(6049)
  R1 500      -> write_register(3000, 500)
  R1          -> read_register(3000)
  scan        -> lee todas las T conocidas y muestra su estado
  q           -> salir
"""

from pymodbus.client import ModbusTcpClient

HOST = "192.168.3.133"
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

    print(f"  Comando no reconocido: {token}")
    print("  Uso: T<num> [0|1]  |  R<num> [valor]  |  scan  |  q")


def scan_coils():
    known = [
        (51, "Modo Prueba"),
        (76, "Modo Proceso"),
        (70, "Modo Integracion"),
        (49, "STOP"),
        (24, "Llego caja"),
        (28, "Recibio banda 3"),
        (79, "UR3 fin"),
        (26, "Piloto recibido"),
        (34, "Piloto listo"),
        (63, "Rotador antihorario"),
        (55, "Rotador horario"),
        (56, "Rotador stop"),
        (57, "Banda adelante"),
        (58, "Banda atras"),
        (59, "Banda stop"),
        (60, "Torreta verde"),
        (61, "Torreta amarillo"),
        (54, "Torreta rojo"),
        (53, "Menu"),
        (64, "Piloto sen. salida"),
        (65, "Piloto sen. entrada"),
        (66, "Piloto sen. giro"),
        (67, "Piloto btn verde"),
        (68, "Piloto btn rojo"),
        (69, "Piloto btn paro"),
    ]
    print("  --- SCAN CENTRAL (HORNER_3) ---")
    for num, desc in known:
        addr = 6000 + num
        result = client.read_coils(addr, count=1)
        if result and not result.isError():
            val = 1 if result.bits[0] else 0
            marker = " <--" if val else ""
            print(f"  T{num:3d} = {val}  | {desc}{marker}")
        else:
            print(f"  T{num:3d} = ERR | {desc}")
    print("  --- FIN SCAN ---")


def main():
    print(f"Conectando a HORNER_3 ({HOST}:{PORT})...")
    if not client.connect():
        print("ERROR: No se pudo conectar al PLC Central.")
        return

    print("Conectado. Escribe comandos (T<num> [val], R<num> [val], scan, q)")
    print()

    try:
        while True:
            try:
                cmd = input("central> ")
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
