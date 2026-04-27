import argparse
from pymodbus.client import ModbusTcpClient

PLC_IP = "192.168.3.12"
PLC_PORT = 502
TIMEOUT = 3


def connect_client() -> ModbusTcpClient:
    client = ModbusTcpClient(host=PLC_IP, port=PLC_PORT, timeout=TIMEOUT)
    connected = client.connect()

    if not connected:
        print(f"[ERROR] No se pudo conectar al PLC en {PLC_IP}:{PLC_PORT}")
        raise SystemExit(1)

    return client


def normalize_bool(value: str) -> bool:
    value = value.strip().lower()

    if value in {"1", "true", "on", "yes"}:
        return True
    if value in {"0", "false", "off", "no"}:
        return False

    raise argparse.ArgumentTypeError(
        "El valor booleano debe ser uno de: 1, 0, true, false, on, off, yes, no"
    )


def cmd_read_coil(args):
    client = connect_client()
    try:
        result = client.read_coils(args.address, count=1)

        if result.isError():
            print(f"[ERROR] Falló la lectura de coil {args.address}: {result}")
            raise SystemExit(1)

        print(f"Coil {args.address} = {result.bits[0]}")
    finally:
        client.close()


def cmd_write_coil(args):
    client = connect_client()
    try:
        result = client.write_coil(args.address, args.value)

        if result.isError():
            print(f"[ERROR] Falló la escritura de coil {args.address}: {result}")
            raise SystemExit(1)

        print(f"Coil {args.address} <- {args.value}")
    finally:
        client.close()


def cmd_read_reg(args):
    client = connect_client()
    try:
        result = client.read_holding_registers(address=args.address, count=1)

        if result.isError():
            print(f"[ERROR] Falló la lectura de registro {args.address}: {result}")
            raise SystemExit(1)

        print(f"Register {args.address} = {result.registers[0]}")
    finally:
        client.close()


def cmd_write_reg(args):
    client = connect_client()
    try:
        result = client.write_register(address=args.address, value=args.value)

        if result.isError():
            print(f"[ERROR] Falló la escritura de registro {args.address}: {result}")
            raise SystemExit(1)

        print(f"Register {args.address} <- {args.value}")
    finally:
        client.close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="CLI mínima para probar Modbus TCP con Horner XL4"
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # read-coil
    parser_read_coil = subparsers.add_parser(
        "read-coil", help="Leer una coil"
    )
    parser_read_coil.add_argument("address", type=int, help="Direccion de coil")
    parser_read_coil.set_defaults(func=cmd_read_coil)

    # write-coil
    parser_write_coil = subparsers.add_parser(
        "write-coil", help="Escribir una coil"
    )
    parser_write_coil.add_argument("address", type=int, help="Direccion de coil")
    parser_write_coil.add_argument(
        "value",
        type=normalize_bool,
        help="Valor booleano: 1/0, true/false, on/off"
    )
    parser_write_coil.set_defaults(func=cmd_write_coil)

    # read-reg
    parser_read_reg = subparsers.add_parser(
        "read-reg", help="Leer un holding register"
    )
    parser_read_reg.add_argument("address", type=int, help="Direccion de registro")
    parser_read_reg.set_defaults(func=cmd_read_reg)

    # write-reg
    parser_write_reg = subparsers.add_parser(
        "write-reg", help="Escribir un holding register"
    )
    parser_write_reg.add_argument("address", type=int, help="Direccion de registro")
    parser_write_reg.add_argument("value", type=int, help="Valor entero a escribir")
    parser_write_reg.set_defaults(func=cmd_write_reg)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()