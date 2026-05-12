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
    # Addresses con offset -1 aplicado (T_n → addr 5999+n)
    # El tuple es (addr_real, "T<num_pdf> - descripcion")
    known = [
        (6050, "T51 Modo Prueba"),
        (6075, "T76 Modo Proceso"),
        (6069, "T70 Modo Integracion"),
        (6052, "T53 Menu"),
        (6048, "T49 STOP"),
        (6023, "T24 Llego caja"),
        (6027, "T28 Recibio banda 3"),
        (6078, "T79 UR3 fin"),
        (6025, "T26 Piloto recibido"),
        (6033, "T34 Piloto listo"),
        (6062, "T63 Rotador antihorario"),
        (6054, "T55 Rotador horario"),
        (6055, "T56 Rotador stop"),
        (6056, "T57 Banda adelante"),
        (6057, "T58 Banda atras"),
        (6058, "T59 Banda stop"),
        (6059, "T60 Torreta verde"),
        (6060, "T61 Torreta amarillo"),
        (6053, "T54 Torreta rojo"),
        (6063, "T64 Piloto sen. salida"),
        (6064, "T65 Piloto sen. entrada"),
        (6065, "T66 Piloto sen. giro"),
        (6066, "T67 Piloto btn verde"),
        (6067, "T68 Piloto btn rojo"),
        (6068, "T69 Piloto btn paro"),
    ]
    print("  --- SCAN CENTRAL (HORNER_3) ---")
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
