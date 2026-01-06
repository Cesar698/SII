from pymodbus.client import ModbusSerialClient
import time


# ---------------------------------------------------
# CONFIGURACIÓN
# ---------------------------------------------------
PUERTO = "/dev/ttyHS0"
BAUDIOS = 9600
ID_POZO = 31    # Esclavo que controla la bomba (Salida)
ID_TANQUE = 32  # Esclavo que lee los flotadores (Entradas)

# Tiempos
TIEMPO_ESPERA_CICLO = 60  # Segundos entre escaneos normales (reducido para mejor monitoreo)
TIEMPO_REINTENTO_ERROR = 10 # Segundos tras un error

def iniciar_cliente():
    """Crea y conecta el cliente Modbus asegurando un inicio limpio."""
    client = ModbusSerialClient(
        port="/dev/ttyHS0",
        baudrate=9600,
        bytesize=8,
        parity='N',
        stopbits=1,
        timeout=1,
        reconnect_delay= 600,
        reconnect_delay_max= 6000,
        retries= 10,
        name= "com",
        handle_local_echo= False
    )
    return client

def reiniciar_conexion(client):
    """Cierra y reabre el puerto para limpiar buffers colgados."""
    print("Reiniciando conexión serial...")
    client.close()
    time.sleep(2) # Dar tiempo al SO del Teltonika para liberar el recurso
    client.connect()
    return client

def control_pozo():
    client = iniciar_cliente()
    
    if not client.connect():
        print(f"Error fatal: No se puede abrir el puerto {PUERTO}")
        return

    print("\nIniciando sistema de control Pozo-Tanque (Modo Robusto)\n")

    # Variables de estado para evitar escrituras innecesarias
    ultimo_estado_bomba = None 
    errores_consecutivos = 0

    while True:
        try:
            # ---------------------------------------------------
            # PASO 1: LEER ESTADO DEL TANQUE (Esclavo 32)
            # Leemos 2 bits juntos (Dirección 0 y 1) para eficiencia
            # ---------------------------------------------------
            lectura_tanque = client.read_discrete_inputs(address=0, count=2, device_id=ID_TANQUE)

            if lectura_tanque.isError():
                print(f"Error leyendo Tanque (ID {ID_TANQUE}). Intento de recuperación...")
                errores_consecutivos += 1
                
                # Si fallamos 3 veces seguidas, asumimos desconexión y reiniciamos puerto
                if errores_consecutivos >= 3:
                    print("Demasiados errores. Apagando bomba por seguridad.")
                    # Intentar apagar bomba antes de reiniciar (Fail-safe)
                    client.write_coil(address=0, value=False, device_id=ID_POZO)
                    client = reiniciar_conexion(client)
                    errores_consecutivos = 0
                
                time.sleep(TIEMPO_REINTENTO_ERROR)
                continue # Salta al siguiente ciclo del while
            else:
                
            # Si la lectura es exitosa, reseteamos contador de errores
                errores_consecutivos = 0
                
                # Decodificar bits
                # bit 0 = Flotador Bajo, bit 1 = Flotador Alto
                bits = lectura_tanque.bits
                flotador_bajo = bits[0]
                flotador_alto = bits[1]

                print(f"📊 Estado Tanque -> Bajo: {'ON' if flotador_bajo else 'OFF'} | Alto: {'ON' if flotador_alto else 'OFF'}")

                # ---------------------------------------------------
                # PASO 2: LÓGICA DE CONTROL (Histéresis)
                # ---------------------------------------------------
                accion_requerida = None # True=Encender, False=Apagar, None=No hacer nada

                # CASO A: Tanque vacío (Ambos abajo) -> ENCENDER
                if not flotador_bajo and not flotador_alto:
                    print("Lógica: Tanque Vacío ->  ENCENDER BOMBA")
                    accion_requerida = True

                # CASO B: Tanque lleno (Ambos arriba) -> APAGAR
                elif flotador_bajo and flotador_alto:
                    print("Lógica: Tanque Lleno ->  APAGAR BOMBA")
                    accion_requerida = False
                
                # CASO C: Error de sensores (Alto activado pero bajo no) -> APAGAR (Seguridad)
                elif not flotador_bajo and flotador_alto:
                    print("Lógica: Error en flotadores (Imposible físico) -> APAGAR BOMBA")
                    accion_requerida = False

                # CASO D: Estado intermedio (Bajo ON, Alto OFF) -> MANTENER ESTADO
                # No hacemos nada, dejamos que la bomba siga como estaba.

                # ---------------------------------------------------
                # PASO 3: EJECUTAR ACCIÓN EN POZO (Esclavo 31)
                # Solo escribimos si el estado deseado cambia para no saturar la red
                # ---------------------------------------------------
                if accion_requerida is not None:
                    if accion_requerida != ultimo_estado_bomba:
                        resp_pozo = client.write_coil(address=0, value=accion_requerida, device_id=ID_POZO)
                        
                        if resp_pozo.isError():
                            print(f" Error escribiendo en Pozo (ID {ID_POZO})")
                            # No actualizamos ultimo_estado_bomba para reintentar en el prox ciclo
                        else:
                            print(f"Comando enviado al Pozo: {'ENCENDER' if accion_requerida else 'APAGAR'}")
                            ultimo_estado_bomba = accion_requerida
                    else:
                        print("ℹ Sin cambios en la bomba.")

                # ---------------------------------------------------
                # PASO 4: ESPERA INTELIGENTE
                # ---------------------------------------------------
                print(f"⏳ Esperando {TIEMPO_ESPERA_CICLO}s...\n")
                time.sleep(TIEMPO_ESPERA_CICLO)

        except Exception as e:
            print(f" Excepción no controlada: {e}")
            client = reiniciar_conexion(client)
            time.sleep(10)

if __name__ == "__main__":
    try:
        control_pozo()
    except KeyboardInterrupt:
        print("\nPrograma terminado por usuario.")