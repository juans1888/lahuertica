"""
💡 Sensor BH1750 (GY-30) - Uso Simple
Lectura directa de intensidad luminosa para huerta inteligente
"""

from machine import Pin, I2C
import utime


class BH1750Simple:
    """
    Clase simple para usar el sensor BH1750 (GY-30)
    """

    def __init__(self, sda_pin=0, scl_pin=1):
        """
        Inicializa el sensor BH1750

        Args:
            sda_pin (int): Pin SDA (por defecto 0)
            scl_pin (int): Pin SCL (por defecto 1)
        """
        # Configurar I2C
        self.i2c = I2C(0, sda=Pin(sda_pin), scl=Pin(scl_pin), freq=100000)

        # Constantes del sensor
        self.BH1750_ADDR = 0x23
        self.CMD_POWER_ON = 0x01
        self.CMD_RESET = 0x07
        self.CMD_CONTINUOUS_HIGH_RES = 0x10

        # Inicializar sensor
        self._setup_sensor()

        print(f"💡 BH1750 listo en SDA={sda_pin}, SCL={scl_pin}")

    def _setup_sensor(self):
        """Configura el sensor para medición continua"""
        try:
            # Encender
            self.i2c.writeto(self.BH1750_ADDR, bytes([self.CMD_POWER_ON]))
            utime.sleep_ms(10)

            # Reset
            self.i2c.writeto(self.BH1750_ADDR, bytes([self.CMD_RESET]))
            utime.sleep_ms(10)

            # Modo continuo alta resolución
            self.i2c.writeto(self.BH1750_ADDR, bytes([self.CMD_CONTINUOUS_HIGH_RES]))
            utime.sleep_ms(180)  # Esperar primera medición

        except Exception as e:
            raise Exception(f"Error configurando BH1750: {e}")

    def read_lux(self):
        """
        Lee intensidad luminosa en lux

        Returns:
            float: Intensidad en lux, o None si hay error
        """
        try:
            # Leer 2 bytes
            data = self.i2c.readfrom(self.BH1750_ADDR, 2)

            # Convertir a lux
            raw_value = (data[0] << 8) | data[1]
            lux = raw_value / 1.2

            return round(lux, 1)

        except Exception:
            return None

    def get_light_condition(self, lux):
        """
        Clasifica condición de luz para plantas

        Args:
            lux (float): Valor en lux

        Returns:
            tuple: (nivel, descripción, recomendación)
        """
        if lux is None:
            return "ERROR", "Sensor no responde", "Verificar conexiones"

        if lux < 10:
            return "MUY_OSCURO", "Noche o muy oscuro", "Luz artificial necesaria"
        elif lux < 100:
            return "OSCURO", "Interior tenue", "Más luz para plantas"
        elif lux < 500:
            return (
                "INTERIOR",
                "Luz interior normal",
                "Suficiente para plantas de sombra",
            )
        elif lux < 1000:
            return "BUENA", "Luz interior brillante", "Buena para mayoría de plantas"
        elif lux < 5000:
            return "EXTERIOR_NUBLADO", "Día nublado", "Excelente para plantas"
        elif lux < 25000:
            return "EXTERIOR_SOLEADO", "Día soleado", "Óptimo para plantas de sol"
        else:
            return "MUY_BRILLANTE", "Sol directo intenso", "Proteger plantas sensibles"

    def monitor_light(self, interval_seconds=2):
        """
        Monitoreo continuo de luz

        Args:
            interval_seconds (int): Intervalo entre lecturas
        """
        print(f"\n💡 MONITOREO DE LUZ - cada {interval_seconds}s")
        print("Presiona Ctrl+C para detener")
        print("\nTiempo\t\tLux\t\tCondición\t\tRecomendación")
        print("-" * 75)

        start_time = utime.time()

        try:
            while True:
                elapsed = utime.time() - start_time
                lux = self.read_lux()

                if lux is not None:
                    nivel, desc, rec = self.get_light_condition(lux)

                    # Formato de salida
                    time_str = f"{elapsed/60:.1f}m"
                    lux_str = f"{lux:6.1f}"

                    print(f"{time_str:8s}\t{lux_str:8s}\t{desc:15s}\t{rec}")

                else:
                    print(f"{elapsed/60:.1f}m\t\t---\t\tERROR\t\t\tVerificar sensor")

                utime.sleep(interval_seconds)

        except KeyboardInterrupt:
            print(f"\n⏹️  Monitoreo detenido después de {elapsed/60:.1f} minutos")

    def quick_reading(self):
        """
        Lectura rápida con interpretación

        Returns:
            dict: Datos de la lectura
        """
        lux = self.read_lux()
        nivel, desc, rec = self.get_light_condition(lux)

        return {
            "lux": lux,
            "nivel": nivel,
            "descripcion": desc,
            "recomendacion": rec,
            "timestamp": utime.time(),
        }


def irrigation_light_advisor(sensor):
    """
    Consejero de riego basado en luz para plantas

    Args:
        sensor: Instancia del sensor BH1750
    """
    print("\n🌱 CONSEJERO DE RIEGO BASADO EN LUZ")
    print("-" * 40)

    reading = sensor.quick_reading()

    if reading["lux"] is None:
        print("❌ Error del sensor - verificar conexiones")
        return

    lux = reading["lux"]

    print(f"💡 Luz actual: {lux} lux")
    print(f"🏷️  Condición: {reading['descripcion']}")

    # Consejos de riego según luz
    if lux < 100:
        print("🚿 RIEGO: Reducir frecuencia - plantas consumen menos agua en poca luz")
        print("⏰ Momento: Cualquier hora del día")
    elif 100 <= lux < 1000:
        print("🚿 RIEGO: Normal según humedad del suelo")
        print("⏰ Momento: Temprano en mañana o tarde")
    elif 1000 <= lux < 10000:
        print("🚿 RIEGO: Aumentar si es día soleado - mayor evaporación")
        print("⏰ Momento: Temprano en mañana (antes del calor)")
    else:
        print("🚿 RIEGO: Aumentar frecuencia - alta evaporación")
        print("⏰ Momento: Muy temprano o al atardecer")
        print("☂️ EXTRA: Considerar sombra temporal si >50,000 lux")


def main():
    """
    Función principal - menú simple de uso
    """
    try:
        # Inicializar sensor
        sensor = BH1750Simple()

        while True:
            print("\n" + "=" * 45)
            print("💡 SENSOR BH1750 - HUERTA INTELIGENTE")
            print("=" * 45)
            print("1. 📊 Lectura única")
            print("2. 🔄 Monitoreo continuo")
            print("3. 🌱 Consejero de riego")
            print("4. 📈 Lecturas rápidas (5 mediciones)")
            print("5. 🚪 Salir")

            option = input("\nSelecciona (1-5): ").strip()

            if option == "1":
                reading = sensor.quick_reading()
                if reading["lux"] is not None:
                    print(f"\n💡 Intensidad: {reading['lux']} lux")
                    print(f"🏷️  Nivel: {reading['descripcion']}")
                    print(f"💡 Recomendación: {reading['recomendacion']}")
                else:
                    print("❌ Error leyendo sensor")

            elif option == "2":
                interval = input("Intervalo en segundos (por defecto 2): ").strip()
                interval = int(interval) if interval.isdigit() else 2
                sensor.monitor_light(interval)

            elif option == "3":
                irrigation_light_advisor(sensor)

            elif option == "4":
                print("\n📊 5 LECTURAS RÁPIDAS:")
                print("Lectura\t\tLux\t\tCondición")
                print("-" * 40)

                for i in range(5):
                    lux = sensor.read_lux()
                    if lux is not None:
                        _, desc, _ = sensor.get_light_condition(lux)
                        print(f"{i+1}\t\t{lux:6.1f}\t\t{desc}")
                    else:
                        print(f"{i+1}\t\t---\t\tERROR")

                    if i < 4:  # No esperar después de la última
                        utime.sleep(1)

            elif option == "5":
                print("👋 ¡Hasta luego!")
                break

            else:
                print("❌ Opción no válida")

    except Exception as e:
        print(f"❌ Error: {e}")
        print("🔧 Verificar conexiones:")
        print("   VCC → 3.3V, GND → GND")
        print("   SDA → GPIO0, SCL → GPIO1")


if __name__ == "__main__":
    main()
