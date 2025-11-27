from pymodbus.client import ModbusSerialClient
import time


# ===================================================
# CONFIGURACIÓN GENERAL DEL PUERTO MODBUS
# ===================================================
client = ModbusSerialClient(
    port="/dev/ttyHS0",
    baudrate=9600,
    bytesize=8,
    parity='N',
    stopbits=1,
    timeout=1
)

if not client.connect():
    print("❌ No se pudo abrir el puerto Modbus.")
    exit()
else:
    print("✅ Conectado al puerto Modbus.\n")


# ===================================================
# CONFIGURACIÓN DE DISPOSITIVOS MODBUS
# ===================================================
UNIT_SALIDA    = 31   # Equipo con salida digital
UNIT_ENTRADAS  = 32   # Equipo con analógico y digitales

COIL_SALIDA    = 1    # Coil en esclavo 31
REG_ANALOG     = 1    # Registro analógico en esclavo 32
DIG_ACTIVAR    = 1    # Entrada digital activar
DIG_DESACTIVAR = 2    # Entrada digital desactivar


# ===================================================
# MODO 1: SENSOR ANALÓGICO (EQUIPO 32)
# ===================================================
def modo_analogico():
    print("\n🔧 MODO 1: Sensor analógico 4–20 mA (Esclavo 32)\n")

    # --- Configuración previa ---
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
        # Leer registro: (slave, address, count)
        lectura = client.read_holding_registers(UNIT_ENTRADAS, REG_ANALOG, 1)

        if lectura.isError():
            print("⚠ Error leyendo analógico.")
            time.sleep(2)
            continue

        raw = lectura.registers[0]
        bar_actual = raw / 100.0
        metros = bar_actual * 10.1972

        print(f"📏 Nivel actual: {metros:.2f} m")

        # Control automático según nivel
        if metros >= nivel_max:
            print("🔴 Activando salida (Esclavo 31)")
            client.write_coil(UNIT_SALIDA, COIL_SALIDA, True)

        elif metros <= nivel_min:
            print("🔵 Desactivando salida (Esclavo 31)")
            client.write_coil(UNIT_SALIDA, COIL_SALIDA, False)

        # Leer estado real
        salida = client.read_coils(UNIT_SALIDA, COIL_SALIDA, 1)
        estado = "ENCENDIDA" if salida.bits[0] else "APAGADA"
        print(f"💡 Estado salida: {estado}")

        print("⏳ Escaneo...\n")
        time.sleep(5)



# ===================================================
# MODO 2: DIGITALES (EQUIPO 32)
# ===================================================
def modo_digital():
    print("\n🔧 MODO 2: Control por entradas digitales (Esclavo 32)\n")

    while True:
        # Leer entradas digitales:
        # (slave, address, count)
        entrada = client.read_discrete_inputs(UNIT_ENTRADAS, DIG_ACTIVAR, 2)

        if entrada.isError():
            print("⚠ Error leyendo entradas digitales.")
            time.sleep(2)
            continue

        activar = entrada.bits[0]
        desactivar = entrada.bits[1]

        print(f"Entrada Activar:    {'ON' if activar else 'OFF'}")
        print(f"Entrada Desactivar: {'ON' if desactivar else 'OFF'}")

        # Acciones
        if activar:
            print("🔴 Activando salida (Esclavo 31)")
            client.write_coil(UNIT_SALIDA, COIL_SALIDA, True)

        if desactivar:
            print("🔵 Desactivando salida (Esclavo 31)")
            client.write_coil(UNIT_SALIDA, COIL_SALIDA, False)

        # Estado de la salida
        salida = client.read_coils(UNIT_SALIDA, COIL_SALIDA, 1)
        estado = "ENCENDIDA" if salida.bits[0] else "APAGADA"
        print(f"💡 Estado salida: {estado}")

        print("⏳ Escaneo...\n")
        time.sleep(2)



# ===================================================
# MENÚ PRINCIPAL
# ===================================================
print("Seleccione el modo de operación:")
print("1) Sensor analógico 4–20 mA")
print("2) Entradas digitales (activar/desactivar salida)")

while True:
    opcion = input("\nSeleccione 1 o 2: ")

    if opcion == "1":
        modo_analogico()
        break

    elif opcion == "2":
        modo_digital()
        break

    else:
        print("❌ Opción inválida.")
