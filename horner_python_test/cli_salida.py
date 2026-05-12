"""
CLI para escribir/leer variables directamente al PLC Salida (HORNER_1).
Uso:
  M29 1       -> write_register_bit(3169, bit0, True)
  M29 0       -> write_register_bit(3169, bit0, False)
  M29         -> read_register_bit(3169, bit0)
  R498 500    -> write_register(3497, 500)
  R508        -> read_register(3507)
  R1          -> read_register(3000)
  R100        -> read_register(3099) [switch banda]
  I1          -> read_discrete_input(0)
  scan        -> lee todas las M y registros conocidos
  q           -> salir
"""

from pymodbus.client import ModbusTcpClient

HOST = "192.168.3.131"
PORT = 502

client = ModbusTcpClient(host=HOST, port=PORT, timeout=3)

REG_CONTROL = 3169  # R170

M_BITS = {
    29: (0, "Modo Integracion → Modo Proceso"),
    33: (1, "Modo Proceso → Modo Integracion"),
    32: (2, "initPru (Estado 0 → Estado 1)"),
    36: (3, "Modo Proceso → Modo Individual"),
    46: (4, "LED rojo"),
    47: (5, "LED amarillo"),
    49: (6, "STOP/paro"),
    41: (7, "LED verde / abrir pluma entrada"),
    42: (8, "Cerrar pluma entrada"),
    43: (9, "Abrir pluma salida"),
    44: (10, "Cerrar pluma salida"),
    37: (11, "Modo Individual → Modo Proceso"),
    45: (12, "Banda salida (enclavable)"),
}

INPUTS = {
    1: (0, "Boton NA"),
    2: (1, "Boton NC"),
    3: (2, "Emergencia NC"),
    4: (3, "Sensor salida"),
    5: (4, "Sensor entrada"),
}


def read_register_bit(address, bit):
    result = client.read_holding_registers(address, count=1)
    if result and not result.isError():
        val = (result.registers[0] >> bit) & 1
        return val
    return None


def write_register_bit(address, bit, state):
    result = client.read_holding_registers(address, count=1)
    if result and not result.isError():
        current = result.registers[0]
        if state:
            new_val = current | (1 << bit)
        else:
            new_val = current & ~(1 << bit)
        return client.write_register(address, new_val)
    return None


def parse_command(cmd: str):
    parts = cmd.strip().split()
    if not parts:
        return

    token = parts[0].upper()

    if token == "Q":
        return "quit"

    if token == "SCAN":
        scan_all()
        return

    if token.startswith("M"):
        try:
            num = int(token[1:])
        except ValueError:
            print(f"  Error: '{token}' no es una M valida")
            return

        if num not in M_BITS:
            print(f"  Error: M{num} no esta mapeada. Disponibles: {sorted(M_BITS.keys())}")
            return

        bit, desc = M_BITS[num]

        if len(parts) >= 2:
            try:
                val = int(parts[1])
            except ValueError:
                val = 0
            state = val != 0
            result = write_register_bit(REG_CONTROL, bit, state)
            if result and not result.isError():
                print(f"  OK: M{num} (R170.{bit}) = {1 if state else 0}  | {desc}")
            else:
                print(f"  ERROR escribiendo M{num}: {result}")
        else:
            val = read_register_bit(REG_CONTROL, bit)
            if val is not None:
                print(f"  M{num} (R170.{bit}) = {val}  | {desc}")
            else:
                print(f"  ERROR leyendo M{num}")
        return

    if token.startswith("I"):
        try:
            num = int(token[1:])
        except ValueError:
            print(f"  Error: '{token}' no es un I valido")
            return
        if num not in INPUTS:
            print(f"  Error: I{num} no mapeada. Disponibles: {sorted(INPUTS.keys())}")
            return
        address, desc = INPUTS[num]
        result = client.read_discrete_inputs(address, count=1)
        if result and not result.isError():
            val = 1 if result.bits[0] else 0
            print(f"  I{num} (addr {address}) = {val}  | {desc}")
        else:
            print(f"  ERROR leyendo I{num}: {result}")
        return

    if token.startswith("R"):
        try:
            num = int(token[1:])
        except ValueError:
            print(f"  Error: '{token}' no es un R valido")
            return
        address = 2999 + num  # R1=3000, R2=3001, ...

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
    print("  Uso: M<num> [0|1]  |  R<num> [valor]  |  I<num>  |  scan  |  q")


def scan_all():
    print("  --- SCAN SALIDA (HORNER_1) ---")

    # R170 completo
    result = client.read_holding_registers(REG_CONTROL, count=1)
    if result and not result.isError():
        raw = result.registers[0]
        print(f"  R170 (addr {REG_CONTROL}) raw = {raw} (0x{raw:04X}, bin {raw:016b})")
    else:
        print(f"  R170 = ERROR")
        raw = None

    print()
    print("  --- Bits de R170 (M markers) ---")
    for m_num in sorted(M_BITS.keys()):
        bit, desc = M_BITS[m_num]
        if raw is not None:
            val = (raw >> bit) & 1
            marker = " <--" if val else ""
            print(f"  M{m_num:2d} (bit {bit:2d}) = {val}{marker}  | {desc}")
        else:
            print(f"  M{m_num:2d} (bit {bit:2d}) = ERR  | {desc}")

    print()
    print("  --- Registros directos ---")
    regs = [
        (3000, "R1 - Maquina de estados"),
        (3497, "R498 - VFD escribir (in freq)"),
        (3507, "R508 - VFD leer (out freq)"),
        (3099, "R100 - Switch banda (5376=izq,5377=off,5378=der)"),
    ]
    for addr, desc in regs:
        result = client.read_holding_registers(addr, count=1)
        if result and not result.isError():
            val = result.registers[0]
            print(f"  addr {addr} = {val}  | {desc}")
        else:
            print(f"  addr {addr} = ERR  | {desc}")

    print()
    print("  --- Entradas fisicas ---")
    for i_num in sorted(INPUTS.keys()):
        address, desc = INPUTS[i_num]
        result = client.read_discrete_inputs(address, count=1)
        if result and not result.isError():
            val = 1 if result.bits[0] else 0
            marker = " <--" if val else ""
            print(f"  I{i_num} (addr {address}) = {val}{marker}  | {desc}")
        else:
            print(f"  I{i_num} (addr {address}) = ERR  | {desc}")

    print("  --- FIN SCAN ---")


def main():
    print(f"Conectando a HORNER_1 ({HOST}:{PORT})...")
    if not client.connect():
        print("ERROR: No se pudo conectar al PLC Salida.")
        return

    print("Conectado. Escribe comandos (M<num> [0|1], R<num> [val], I<num>, scan, q)")
    print(f"  M disponibles: {sorted(M_BITS.keys())}")
    print(f"  I disponibles: {sorted(INPUTS.keys())}")
    print()

    try:
        while True:
            try:
                cmd = input("salida> ")
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
