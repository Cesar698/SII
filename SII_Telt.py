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
    reconnect_delay_max= 6000,
    retries= 5,
    name= "com",
    handle_local_echo= False
)

print("\n🔍 Verificando dispositivos Modbus...\n")

def probar_dispositivo(nombre, slave_id):
    try:
        resp = client.read_input_registers(address=0, count=1, slave=slave_id)
        if resp.isError():
            print(f"❌ {nombre} (ID {slave_id}) NO responde")
            return False
        else:
            print(f"✅ {nombre} (ID {slave_id}) detectado correctamente")
            return True
    except Exception as e:
        print(f"❌ Error comunicando con {nombre} (ID {slave_id}): {e}")
        return False


equipo_31_ok = probar_dispositivo("Equipo de Pozo", 31)
equipo_32_ok = probar_dispositivo("Equipo del Tanque", 32)

print("")  # línea en blanco


print("\n🔧 Iniciando Proceso\n")

while True:
    Bajo = client.read_discrete_inputs(address= 0, slave= 32)
    #entrada = client.read_discrete_inputs(DIG_ACTIVAR, 2, unit=UNIT_ENTRADAS)
    Alto = client.read_discrete_inputs(address= 1, slave= 32 )

    if Alto.isError ():
        print("⚠ Error leyendo Flotador Alto.")
        print("🔵 Desactivando salida (Equipo 1)")
        client.write_coil(address=0, value=False, slave=31)
        time.sleep(2)
        continue
    if Bajo.isError ():
        print("⚠ Error leyendo Flotador Bajo.")
        print("🔵 Desactivando salida (Equipo 1)")
        client.write_coil(address=0, value=False, slave=31)
        time.sleep(2)
        continue
    Flotador_A = Alto.bits[0]
    Flotador_B = Bajo.bits[0]


    print(f"Flotador Alto: {'ON' if Flotador_A else 'OFF'}")
    print(f"Flotador Bajo: {'ON' if Flotador_B else 'OFF'}")


    # Control del equipo de SALIDA
    if  not Flotador_B and not Flotador_A:
        print("🔴 Activando salida (Equipo 1)")
        client.write_coil(address=0, value=True, slave= 31)
        #client.write_coil(COIL_SALIDA, True, unit=UNIT_SALIDA)

    if Flotador_A and Flotador_B :
        print("🔵 Desactivando salida (Equipo 1)")
        client.write_coil(address=0, value=False, slave=31)
        #client.write_coil(COIL_SALIDA, False, unit=UNIT_SALIDA)
        
    if Flotador_A and not Flotador_B :
        print ("Error en flotadores, Favor de Revisar")
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

