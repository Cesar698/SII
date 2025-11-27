from pymodbus.client import ModbusSerialClient
import time


# ---------------------------------------------------
# CONFIGURACIÓN GENERAL DE MODBUS (UN SOLO CLIENTE)
# ---------------------------------------------------
client = ModbusSerialClient(
    port="/dev/ttyHS0",
    baudrate=9600,
    bytesize=8,
    parity='N',
    stopbits=1,
    timeout=1,
    reconnect_delay= 10,
    reconnect_delay_max= 600,
    retries= 3,
    name= "com",
    handle_local_echo= False
)

if not client.connect():
    print("❌ Error: no se pudo conectar al puerto COM.")
    exit()
else:
    print("✅ Conexión Modbus establecida.\n")


# ---------------------------------------------------
# CONFIGURACIÓN DE DISPOSITIVOS MODBUS
# ---------------------------------------------------
UNIT_SALIDA = 31      # Equipo con salida digital
UNIT_ENTRADAS = 32     # Equipo con entradas analógicas/digitales

COIL_SALIDA = 0       # Dirección coil en equipo 1
REG_ANALOG =  0       # Register analógico en equipo 2
DIG_ACTIVAR = 0     # Input digital activar
DIG_DESACTIVAR = 1    # Input digital desactivar


# ---------------------------------------------------
# FUNCIÓN: MODO ANALÓGICO (EQUIPO 2)
# ---------------------------------------------------
def modo_analogico():
    """Modo Sensor Presion"""
    print("\n🔧 MODO 1: Sensor analógico 4–20 mA (Equipo 2)\n")

    # Configuración del sensor
    while True:
        try:
            base_bar = float(input("Valor de referencia (3, 6 o 10 bares): "))
            if base_bar in (3, 6, 10):
                break
        except:
            pass
        print("Valor incorrecto.")

    nivel_max = float(input("Nivel máximo (m): "))
    nivel_min = float(input("Nivel mínimo (m): "))

    print("\nIniciando monitoreo analógico…\n")

    while True:
        # Leer registro del equipo de ENTRADAS
        lectura = client.read_holding_registers(address= 0, slave= 32)
        #lectura = client.read_holding_registers(REG_ANALOG, 1, device_id=UNIT_ENTRADAS)

        if lectura.isError():
            print("⚠ Error leyendo sensor.")
            time.sleep(2)
            continue

        raw = lectura.registers[0]
        bar_actual = raw / 100.0
        metros = bar_actual * 10.1972

        print(f"📏 Nivel actual: {metros:.2f} m")

        # Control del equipo de SALIDA
        if metros >= nivel_max:
            print("🔴 Activando salida (Equipo 1)")
            client.write_coil(address= 0, value= True, slave= 31)
            #client.write_coil(COIL_SALIDA, True, unit=UNIT_SALIDA)

        elif metros <= nivel_min:
            print("🔵 Desactivando salida (Equipo 1)")
            client.write_coil(address= 0, value= False, slave= 31)
            #client.write_coil(COIL_SALIDA, False, unit=UNIT_SALIDA)

        # Estado real de la salida
        salida = client.read_coils(address=1,device_id=31)
        #salida = client.read_coils(COIL_SALIDA, 1, unit=UNIT_SALIDA)
        estado = "ENCENDIDA" if salida.bits[0] else "APAGADA"
        print(f"💡 Estado salida: {estado}")

        print("⏳ Escaneo...\n")
        time.sleep(5)


# ---------------------------------------------------
# FUNCIÓN: MODO DIGITAL (EQUIPO 2)
# ---------------------------------------------------
def modo_digital():
    """"Modo Flotadores"""
    print("\n🔧 MODO 2: Control digital por Modbus (Equipo 2)\n")

    while True:
        Flotador_Alto = client.read_discrete_inputs(address= 0, slave= 32)
        #entrada = client.read_discrete_inputs(DIG_ACTIVAR, 2, unit=UNIT_ENTRADAS)
        Flotador_Bajo = client.read_discrete_inputs(address= 1, slave= 32)
        if Flotador_Alto.isError():
            print("⚠ Error leyendo digital 2.")
            time.sleep(2)
            continue
        if Flotador_Bajo.isError():
            print("⚠ Error leyendo digital 1.")
            time.sleep(2)
            continue


        activar = Flotador_Bajo.bits[0]
        desactivar = Flotador_Alto.bits[0]

        print(f"Entrada Activar:    {'ON' if activar else 'OFF'}")
        print(f"Entrada Desactivar: {'ON' if desactivar else 'OFF'}")

        # Control del equipo de SALIDA
        if activar:
            print("🔴 Activando salida (Equipo 1)")
            client.write_coil(address=0, value=True, slave= 31)
            #client.write_coil(COIL_SALIDA, True, unit=UNIT_SALIDA)

        if desactivar:
            print("🔵 Desactivando salida (Equipo 1)")
            client.write_coil(address=0, value=False, slave=31)
            #client.write_coil(COIL_SALIDA, False, unit=UNIT_SALIDA)

        # Estado actual de salida
        salida = client.read_coils(address=0,slave=31)
        #salida = client.read_coils(COIL_SALIDA, 1, unit=UNIT_SALIDA)
        estado = "ENCENDIDA" if salida.bits[0] else "APAGADA"
        print(f"💡 Estado salida: {estado}")

        print("⏳ Escaneo...\n")
        time.sleep(2)



# ---------------------------------------------------
# MENÚ DE OPERACIÓN
# ---------------------------------------------------
print("Seleccione el modo de operación:")
print("1) Sensor analógico 4–20 mA")
print("2) Control por entradas digitales")

while True:
    opcion = input("\n Seleccione la Opcion 1 (Sensor Presion) u Opcion 2 (Flotadores) ")

    if opcion == "1":
        modo_analogico()
        break

    elif opcion == "2":
        modo_digital()
        break

    else:
        print("❌ Opción inválida.")
