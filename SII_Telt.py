from pymodbus.client import ModbusSerialClient
import time


# ---------------------------------------------------
# CONFIGURACIÓN MODBUS
# ---------------------------------------------------
client = ModbusSerialClient(
    port="/dev/ttyHS0",
    baudrate=9600,
    bytesize=8,
    parity='N',
    stopbits=1,
    timeout=1,
    reconnect_delay=5,
    reconnect_delay_max=60,
    retries=3,
    handle_local_echo=False
)

print("🔄 Conectando al bus Modbus...")
if not client.connect():
    print("❌ Error: NO se pudo conectar al Modbus.")
    exit()
print("✅ Conexión Modbus establecida.\n")


# ---------------------------------------------------
# IDs DE EQUIPO
# ---------------------------------------------------
UNIT_SALIDA = 31       # Equipo que TIENE la salida digital
UNIT_ENTRADAS = 32     # Equipo que TIENE el sensor y/o digitales

# Direcciones Modbus
COIL_SALIDA = 1        # Salida digital del equipo 31
REG_ANALOG = 1         # Registro analógico del equipo 32
DIG_ACTIVAR = 1        # Digital activar
DIG_DESACTIVAR = 2     # Digital desactivar


# ---------------------------------------------------
# FUNCIÓN: LECTURA ANALÓGICA
# ---------------------------------------------------
def modo_analogico():
    print("\n------ MODO ANALÓGICO 4-20 mA ------\n")

    # Parámetros de usuario
    while True:
        try:
            base_bar = float(input("Valor de referencia del sensor (3, 6 o 10 bares): "))
            if base_bar in (3, 6, 10):
                break
        except:
            pass
        print("❌ Valor no válido.")

    nivel_max = float(input("Nivel máximo (m): "))
    nivel_min = float(input("Nivel mínimo (m): "))

    print("\n📡 Iniciando lectura de sensor…\n")

    while True:
        lectura = client.read_holding_registers(
            address=REG_ANALOG,
            count=1,
            device_id=UNIT_ENTRADAS
        )

        if lectura.isError():
            print("⚠ Error leyendo el sensor, esperando...")
            time.sleep(2)
            continue

        raw = lectura.registers[0]
        bar_actual = raw / 100.0
        metros = bar_actual * 10.1972

        print(f"📏 Nivel estimado: {metros:.2f} m")

        # Control automático
        if metros >= nivel_max:
            print("🔴 Nivel alto → Activando salida")
            client.write_coil(address=COIL_SALIDA, value=True, device_id=UNIT_SALIDA)

        elif metros <= nivel_min:
            print("🔵 Nivel bajo → Desactivando salida")
            client.write_coil(address=COIL_SALIDA, value=False, device_id=UNIT_SALIDA)

        # Leer estado real
        salida = client.read_coils(
            address=COIL_SALIDA,
            count=1,
            device_id=UNIT_SALIDA
        )

        estado = "ENCENDIDA" if salida.bits and salida.bits[0] else "APAGADA"
        print(f"💡 Estado salida: {estado}")

        print("⏳ Esperando siguiente lectura...\n")
        time.sleep(5)


# ---------------------------------------------------
# FUNCIÓN: MODO DIGITAL
# ---------------------------------------------------
def modo_digital():
    print("\n------ MODO DIGITAL POR FLOTADORES ------\n")

    while True:
        entrada = client.read_discrete_inputs(
            address=DIG_ACTIVAR,
            count=2,
            device_id=UNIT_ENTRADAS
        )

        if entrada.isError():
            print("⚠ Error leyendo entradas digitales.")
            time.sleep(2)
            continue

        activar = entrada.bits[0] if len(entrada.bits) > 0 else False
        desactivar = entrada.bits[1] if len(entrada.bits) > 1 else False

        print(f"Entrada Activar:    {'ON' if activar else 'OFF'}")
        print(f"Entrada Desactivar: {'ON' if desactivar else 'OFF'}")

        # Control por señales digitales
        if activar:
            print("🔴 Activando salida...")
            client.write_coil(address=COIL_SALIDA, value=True, device_id=UNIT_SALIDA)

        if desactivar:
            print("🔵 Desactivando salida...")
            client.write_coil(address=COIL_SALIDA, value=False, device_id=UNIT_SALIDA)

        # Ver estado real
        salida = client.read_coils(
            address=COIL_SALIDA,
            count=1,
            device_id=UNIT_SALIDA
        )

        estado = "ENCENDIDA" if salida.bits and salida.bits[0] else "APAGADA"
        print(f"💡 Estado salida: {estado}")

        print("⏳ Próximo escaneo...\n")
        time.sleep(2)


# ---------------------------------------------------
# MENÚ PRINCIPAL
# ---------------------------------------------------
print("Seleccione el modo:")
print("1) Sensor de presión (4-20 mA)")
print("2) FLOTADORES (entradas digitales)")

while True:
    opcion = input("\nIngrese opción 1 o 2: ")

    if opcion == "1":
        modo_analogico()
        break

    elif opcion == "2":
        modo_digital()
        break

    else:
        print("❌ Opción inválida.")

