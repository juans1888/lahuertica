#!/usr/bin/env python3
"""
DHT22 Sensor Reader - La Huertica
Lectura basica de temperatura y humedad del sensor DHT22
Compatible con Raspberry Pi 3 B+ y sistemas mas recientes
"""

import time
import sys

# Manejo de compatibilidad GPIO
try:
    import RPi.GPIO as GPIO
except ImportError:
    try:
        import rpi_lgpio as GPIO
        print("Usando rpi-lgpio como backend GPIO")
    except ImportError:
        print("Error: No se pudo importar biblioteca GPIO")
        print("Instale rpi-lgpio: pip install rpi-lgpio")
        sys.exit(1)

def read_dht22(pin):
    """
    Lee datos del sensor DHT22 conectado al pin especificado
    
    Args:
        pin (int): Numero de pin GPIO donde esta conectado el sensor
        
    Returns:
        tuple: (temperatura, humedad) o (None, None) si hay error
    """
    # Configurar GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(pin, GPIO.OUT)
    
    # Lista para almacenar bits de datos
    data = []
    
    try:
        # Se�al de inicio
        GPIO.output(pin, GPIO.LOW)
        time.sleep(0.02)  # 20ms
        GPIO.output(pin, GPIO.HIGH)
        
        # Cambiar a modo entrada
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
        # Esperar respuesta del sensor
        timeout = time.time() + 0.1
        while GPIO.input(pin) == GPIO.HIGH:
            if time.time() > timeout:
                return None, None
        
        while GPIO.input(pin) == GPIO.LOW:
            if time.time() > timeout:
                return None, None
        
        while GPIO.input(pin) == GPIO.HIGH:
            if time.time() > timeout:
                return None, None
        
        # Leer 40 bits de datos
        for i in range(40):
            # Esperar inicio del bit
            while GPIO.input(pin) == GPIO.LOW:
                if time.time() > timeout:
                    return None, None
            
            # Medir duraci�n del pulso alto
            start_time = time.time()
            while GPIO.input(pin) == GPIO.HIGH:
                if time.time() > timeout:
                    return None, None
            
            # Si el pulso es largo, es un '1', si es corto es un '0'
            if (time.time() - start_time) > 0.00005:  # 50 microsegundos
                data.append(1)
            else:
                data.append(0)
        
        # Procesar datos
        if len(data) == 40:
            # Convertir bits a bytes
            bytes_data = []
            for i in range(0, 40, 8):
                byte = 0
                for j in range(8):
                    byte = byte << 1
                    if data[i + j] == 1:
                        byte = byte | 1
                bytes_data.append(byte)
            
            # Verificar checksum
            checksum = (bytes_data[0] + bytes_data[1] + bytes_data[2] + bytes_data[3]) & 0xFF
            if checksum == bytes_data[4]:
                # Calcular humedad y temperatura
                humidity = ((bytes_data[0] << 8) + bytes_data[1]) / 10.0
                temperature = (((bytes_data[2] & 0x7F) << 8) + bytes_data[3]) / 10.0
                
                # Verificar signo de temperatura
                if bytes_data[2] & 0x80:
                    temperature = -temperature
                
                return temperature, humidity
        
        return None, None
        
    except Exception as e:
        print(f"Error leyendo sensor: {e}")
        return None, None
    
    finally:
        GPIO.cleanup()

def main():
    """
    Funcion principal - Lee y muestra datos del sensor DHT22
    """
    # Pin GPIO donde esta conectado el sensor (cambiar segun tu conexion)
    SENSOR_PIN = 4
    
    print("Sensor DHT22 - La Huertica")
    print("=" * 40)
    print(f"Leyendo datos del pin GPIO {SENSOR_PIN}...")
    print("Inicializando sensor, espere...")
    print()
    
    # Dar tiempo al sensor para estabilizarse
    time.sleep(2)
    
    try:
        while True:
            # Leer datos del sensor
            temperature, humidity = read_dht22(SENSOR_PIN)
            
            if temperature is not None and humidity is not None:
                print(f"[TEMP] Temperatura: {temperature:.1f}C")
                print(f"[HUM]  Humedad: {humidity:.1f}%")
                print("-" * 30)
            else:
                print("[ERROR] No se pudieron leer los datos del sensor")
                print("        Verifica las conexiones y vuelve a intentar")
            
            # Esperar 2 segundos antes de la siguiente lectura
            time.sleep(2)
            
    except KeyboardInterrupt:
        print("\n[EXIT] Programa terminado por el usuario")
    except Exception as e:
        print(f"[ERROR] Error inesperado: {e}")
    finally:
        GPIO.cleanup()
        print("[CLEAN] GPIO limpiado correctamente")

if __name__ == "__main__":
    main()