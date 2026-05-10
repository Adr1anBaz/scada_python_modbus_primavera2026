from pymodbus.client import ModbusTcpClient
import time

PLC_IP = "192.168.3.12"
PLC_PORT = 502

# Según la guía:
# T1 -> 6000
# Q1 -> 0  => Q10 -> 9
COIL_T1 = 6000
COIL_Q10 = 9

print(f"Intentando conectar a {PLC_IP}:{PLC_PORT} ...")

client = ModbusTcpClient(host=PLC_IP, port=PLC_PORT, timeout=3)

connected = client.connect()

if not connected:
    print("No se pudo conectar al PLC.")
    client.close()
    raise SystemExit

print("Conexion exitosa con el PLC.")

print("Escribiendo T1 = OFF para iniciar limpio ...")
result_init = client.write_coil(COIL_T1, False)
print(f"Respuesta write init OFF: {result_init}")

time.sleep(1)

print("Leyendo Q10 antes de activar T1 ...")
read_q10_before = client.read_coils(COIL_Q10, count=1)
print(f"Lectura Q10 antes: {read_q10_before}")
if hasattr(read_q10_before, "bits"):
    print(f"Bit leido Q10 antes: {read_q10_before.bits[0]}")

print("Escribiendo T1 = ON ...")
result_on = client.write_coil(COIL_T1, True)
print(f"Respuesta write ON: {result_on}")

time.sleep(1)

print("Leyendo Q10 despues de activar T1 ...")
read_q10_on = client.read_coils(COIL_Q10, count=1)
print(f"Lectura Q10 despues de ON: {read_q10_on}")
if hasattr(read_q10_on, "bits"):
    print(f"Bit leido Q10 despues de ON: {read_q10_on.bits[0]}")

time.sleep(2)

print("Escribiendo T1 = OFF ...")
result_off = client.write_coil(COIL_T1, False)
print(f"Respuesta write OFF: {result_off}")

time.sleep(1)

print("Leyendo Q10 despues de desactivar T1 ...")
read_q10_off = client.read_coils(COIL_Q10, count=1)
print(f"Lectura Q10 despues de OFF: {read_q10_off}")
if hasattr(read_q10_off, "bits"):
    print(f"Bit leido Q10 despues de OFF: {read_q10_off.bits[0]}")

client.close()
print("Conexion cerrada.")