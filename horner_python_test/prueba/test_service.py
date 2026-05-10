from modbus_service import HornerModbusService, COIL_T1, REGISTER_R1

service = HornerModbusService()

if not service.connect():
    print("No se pudo conectar al PLC.")
    raise SystemExit(1)

print("Conectado al PLC.")

try:
    print("Escribiendo T1 = True")
    service.write_coil(COIL_T1, True)
    print("Leyendo T1:", service.read_coil(COIL_T1))

    print("Escribiendo T1 = False")
    service.write_coil(COIL_T1, False)
    print("Leyendo T1:", service.read_coil(COIL_T1))

    print("Escribiendo R1 = 77")
    service.write_register(REGISTER_R1, 77)
    print("Leyendo R1:", service.read_register(REGISTER_R1))

finally:
    service.close()
    print("Conexion cerrada.")