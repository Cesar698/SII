from pymodbus.client import ModbusSerialClient
import time

# -----------------------------------------------------------
# CONFIGURACIÓN MODBUS SERIAL (Teltonika)
# -----------------------------------------------------------
client = ModbusSerialClient(
    port="/dev/ttyUSB0",
    baudrate=9600,
    parity="N",
    stopbits=1,
    bytesize=8,
    timeout=1
)

# IDs de los dos equipos
EQUIPO_SALIDA_DIGITAL = 31
EQUIPO_ENTRADAS_O_ANALOG = 32

# -----------------------------------------------------------
# CONEXIÓN MODBUS
# -----------------------------------------------------------
if not client.connect():
    print("❌ Error: No se pudo conectar al bus Modbus.")
    exit()
else:
    print("✅ Conectado al bus Modbus correctamente.")


# ===========================================================
# MODO ANALÓGICO (LEE ENTRADA ANALÓGICA DEL EQUIPO 32)
# ===========================================================
def modo_analogico():

    print("\n---- MODO ANALÓGICO ----")
    print("Leyendo entrada analógica del equipo 32...\n")

    while True:
        try:
            lectura = client.read_holding_registers(address=0, count=1, unit=EQUIPO_ENTRADAS_O_ANALOG)

            if lectura.isError():
                print("❌ Error al leer la entrada analógica.")
            else:
                valor_raw = lectura.registers[0]
                # Conversión típica 4-20 mA → 0-100%
                porcentaje = (valor_raw / 4095) * 100

                print(f"Valor bruto: {valor_raw}   →   {porcentaje:.2f}%")

            time.sleep(2)

        except Exception as e:
            print(f"⚠ Error en modo analógico: {e}")
            time.sleep(2)


# ===========================================================
# MODO DIGITAL (LEE 2 ENTRADAS Y CONTROLA UNA SALIDA EN EQUIPO 31)
# ===========================================================
def modo_digital():

    print("\n---- MODO DIGITAL ----")
    print("Leyendo entradas digitales del equipo 32 y controlando salida del equipo 31...\n")

    salida_actual = 0  # estado local de la salida digital

    while True:
        try:
            # Leer dos entradas digitales del equipo 32
            entradas = client.read_discrete_inputs(address=0, count=2, unit=EQUIPO_ENTRADAS_O_ANALOG)

            if entradas.isError():
                print("❌ Error al leer entradas digitales.")
            else:
                entrada1 = entradas.bits[0]
                entrada2 = entradas.bits[1]

                print(f"Entrada 1: {entrada1}   |   Entrada 2: {entrada2}")

                # Lógica:
                # Entrada 1 → activa salida del equipo 31
                # Entrada 2 → desactiva salida del equipo 31

                nuevo_estado = salida_actual

                if entrada1 == 1:
                    nuevo_estado = 1
                    print("➡ Activando salida digital del equipo 31...")

                if entrada2 == 1:
                    nuevo_estado = 0
                    print("➡ Desactivando salida digital del equipo 31...")

                # Si hay cambio, escribir al equipo 31
                if nuevo_estado != salida_actual:
                    respuesta = client.write_coil(address=0, value=nuevo_estado, unit=EQUIPO_SALIDA_DIGITAL)

                    if respuesta.isError():
                        print("❌ Error al escribir la salida digital.")
                    else:
                        estado_txt = "ACTIVADA" if nuevo_estado else "DESACTIVADA"
                        print(f"✔ Salida digital {estado_txt} correctamente.")

                    salida_actual = nuevo_estado

            time.sleep(1)

        except Exception as e:
            print(f"⚠ Error en modo digital: {e}")
            time.sleep(1)


# ===========================================================
# MENÚ PRINCIPAL
# ===========================================================
def menu():
    print("\n====================================")
    print("   SISTEMA DE MONITOREO MODBUS")
    print("====================================")
    print("1) Modo Analógico")
    print("2) Modo Digital")
    print("====================================\n")

    opcion = input("Seleccione una opción (1 o 2): ")

    if opcion == "1":
        modo_analogico()
    elif opcion == "2":
        modo_digital()
    else:
        print("Opción inválida.")
        menu()


# Iniciar programa
menu()
