from pymodbus.client import ModbusTcpClient

PLC_IP = "192.168.3.12"
PLC_PORT = 502
TIMEOUT = 3

# Mapeos base según la guía y tus pruebas
COIL_T1 = 6000
COIL_Q10 = 9
REGISTER_R1 = 3000


class HornerModbusService:
    def __init__(self, host: str = PLC_IP, port: int = PLC_PORT, timeout: int = TIMEOUT):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.client = ModbusTcpClient(host=self.host, port=self.port, timeout=self.timeout)

    def connect(self) -> bool:
        return self.client.connect()

    def close(self) -> None:
        self.client.close()

    def read_coil(self, address: int) -> bool:
        result = self.client.read_coils(address, count=1)

        if result is None or result.isError():
            raise RuntimeError(f"Error al leer coil {address}: {result}")

        return bool(result.bits[0])

    def write_coil(self, address: int, value: bool) -> None:
        result = self.client.write_coil(address, value)

        if result is None or result.isError():
            raise RuntimeError(f"Error al escribir coil {address}={value}: {result}")

    def read_register(self, address: int) -> int:
        result = self.client.read_holding_registers(address=address, count=1)

        if result is None or result.isError():
            raise RuntimeError(f"Error al leer registro {address}: {result}")

        return int(result.registers[0])

    def write_register(self, address: int, value: int) -> None:
        result = self.client.write_register(address=address, value=value)

        if result is None or result.isError():
            raise RuntimeError(f"Error al escribir registro {address}={value}: {result}")