"""
GY-30 (BH1750) Light Intensity Sensor - Hello World Example

Este script demuestra cómo leer valores de intensidad luminosa desde un sensor 
GY-30 (BH1750) usando Raspberry Pi Pico con MicroPython.

Conexiones:
- GY-30 VCC -> Pico 3.3V
- GY-30 GND -> Pico GND
- GY-30 SCL -> Pico GP1 (I2C0 SCL)
- GY-30 SDA -> Pico GP0 (I2C0 SDA)
"""

from machine import Pin, I2C
import utime

# Constantes del BH1750 (GY-30)
BH1750_ADDR = 0x23  # Dirección del sensor (puede ser 0x23 o 0x5C dependiendo del pin ADDR)
BH1750_CMD_POWER_ON = 0x01  # Encendido
BH1750_CMD_RESET = 0x07  # Reset
BH1750_CMD_CONTINUOUS_HIGH_RES = 0x10  # Modo continuo de alta resolución (1 lx)

def setup_sensor(i2c):
    """
    Inicializa el sensor BH1750.
    
    Args:
        i2c: Interfaz I2C configurada
        
    Returns:
        bool: True si la configuración fue exitosa, False en caso contrario
    """
    try:
        # Verificar si el sensor está presente en el bus I2C
        if BH1750_ADDR not in i2c.scan():
            print("Error: Sensor BH1750 no encontrado en el bus I2C")
            return False
        
        # Encender el sensor
        i2c.writeto(BH1750_ADDR, bytes([BH1750_CMD_POWER_ON]))
        utime.sleep_ms(10)
        
        # Resetear el sensor
        i2c.writeto(BH1750_ADDR, bytes([BH1750_CMD_RESET]))
        utime.sleep_ms(10)
        
        # Configurar modo continuo de alta resolución
        i2c.writeto(BH1750_ADDR, bytes([BH1750_CMD_CONTINUOUS_HIGH_RES]))
        utime.sleep_ms(180)  # Esperar a que complete la primera medición
        
        return True
    except Exception as e:
        print(f"Error al inicializar el sensor: {e}")
        return False

def read_light_intensity(i2c):
    """
    Lee la intensidad luminosa del sensor BH1750.
    
    Args:
        i2c: Interfaz I2C configurada
        
    Returns:
        float: Intensidad luminosa en lux, o None si la lectura falló
    """
    try:
        # Leer 2 bytes del sensor
        data = i2c.readfrom(BH1750_ADDR, 2)
        
        # Convertir los datos a valor en lux
        # La fórmula es: (MSB << 8 | LSB) / 1.2
        light_intensity = ((data[0] << 8) | data[1]) / 1.2
        
        return light_intensity
    except Exception as e:
        print(f"Error al leer el sensor: {e}")
        return None

def main():
    """
    Función principal para leer y mostrar valores de intensidad luminosa.
    """
    try:
        # Inicializar I2C con pines predeterminados para Raspberry Pi Pico
        # I2C0: SDA en GP0 (pin 1), SCL en GP1 (pin 2)
        i2c = I2C(0, sda=Pin(0), scl=Pin(1), freq=100000)
        
        print("Inicializando sensor de intensidad luminosa GY-30 (BH1750)...")
        
        if not setup_sensor(i2c):
            print("Error al inicializar el sensor. Verifica las conexiones e intenta de nuevo.")
            return
        
        print("¡Sensor inicializado correctamente!")
        print("Leyendo valores de intensidad luminosa (Ctrl+C para salir)...")
        
        # Bucle simple para leer y mostrar continuamente la intensidad luminosa
        while True:
            lux = read_light_intensity(i2c)
            
            if lux is not None:
                print(f"Intensidad Luminosa: {lux:.2f} lux")
            else:
                print("Error al leer la intensidad luminosa")
            
            utime.sleep(1)  # Leer cada segundo
            
    except KeyboardInterrupt:
        print("\nPrograma terminado por el usuario")
    except Exception as e:
        print(f"Error inesperado: {e}")

if __name__ == "__main__":
    main()
