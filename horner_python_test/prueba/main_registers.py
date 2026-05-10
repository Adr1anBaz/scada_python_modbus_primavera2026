from pymodbus.client import ModbusTcpClient
import time

PLC_IP = "192.168.3.12"
PLC_PORT = 502

# Según la guía:
# R1 -> 3000
REGISTER_R1 = 3000

VALUE_TO_WRITE = 123

print(f"Intentando conectar a {PLC_IP}:{PLC_PORT} ...")

client = ModbusTcpClient(host=PLC_IP, port=PLC_PORT, timeout=3)

connected = client.connect()

if not connected:
    print("No se pudo conectar al PLC.")
    client.close()
    raise SystemExit

print("Conexion exitosa con el PLC.")

print(f"Leyendo R1 antes de escribir...")
read_before = client.read_holding_registers(address=REGISTER_R1, count=1)
print(f"Lectura antes: {read_before}")
if hasattr(read_before, "registers"):
    print(f"Valor actual de R1: {read_before.registers[0]}")

time.sleep(1)

print(f"Escribiendo {VALUE_TO_WRITE} en R1 ...")
write_result = client.write_register(address=REGISTER_R1, value=VALUE_TO_WRITE)
print(f"Respuesta write: {write_result}")

time.sleep(1)

print("Leyendo R1 despues de escribir...")
read_after = client.read_holding_registers(address=REGISTER_R1, count=1)
print(f"Lectura despues: {read_after}")
if hasattr(read_after, "registers"):
    print(f"Valor leido de R1: {read_after.registers[0]}")

client.close()
print("Conexion cerrada.")