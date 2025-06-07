"""
Código de diagnóstico para sensor DHT22
Verifica funcionamiento y detecta problemas comunes
"""

import dht
from machine import Pin
import time
import gc


class DHT22Diagnostics:
    """
    Clase para diagnóstico completo del sensor DHT22
    """

    def __init__(self, data_pin=15):
        """
        Inicializa el diagnóstico del DHT22

        Args:
            data_pin (int): Pin de datos (por defecto 15)
        """
        try:
            self.pin = Pin(data_pin, Pin.IN, Pin.PULL_UP)
            self.sensor = dht.DHT22(self.pin)
            self.data_pin = data_pin

            print(f"🌡️  Sensor DHT22 inicializado en GPIO{data_pin}")
            print("🔍 Modo diagnóstico activado")
            print("⚠️  IMPORTANTE: Conectar resistor pull-up 4.7kΩ entre DATA y 3.3V")

        except Exception as e:
            print(f"❌ Error inicializando DHT22: {e}")
            raise

    def single_reading(self):
        """
        Realiza una lectura individual del sensor

        Returns:
            dict: Resultado de la lectura con estado
        """
        try:
            # Limpiar memoria antes de la lectura
            gc.collect()

            # Realizar lectura
            self.sensor.measure()

            # Obtener valores
            temperature = self.sensor.temperature()
            humidity = self.sensor.humidity()

            return {
                "success": True,
                "temperature": temperature,
                "humidity": humidity,
                "error": None,
                "timestamp": time.time(),
            }

        except OSError as e:
            return {
                "success": False,
                "temperature": None,
                "humidity": None,
                "error": f"Error comunicación: {e}",
                "timestamp": time.time(),
            }
        except Exception as e:
            return {
                "success": False,
                "temperature": None,
                "humidity": None,
                "error": f"Error general: {e}",
                "timestamp": time.time(),
            }

    def test_basic_functionality(self):
        """
        Prueba básica de funcionamiento del sensor
        """
        print("\n🧪 PRUEBA BÁSICA DE FUNCIONAMIENTO")
        print("-" * 40)

        # Intentar 5 lecturas básicas
        successful_readings = 0
        failed_readings = 0

        for i in range(5):
            print(f"Intento {i+1}/5: ", end="")

            result = self.single_reading()

            if result["success"]:
                print(f"✅ T={result['temperature']}°C, H={result['humidity']}%")
                successful_readings += 1
            else:
                print(f"❌ {result['error']}")
                failed_readings += 1

            time.sleep(2.5)  # Esperar entre lecturas

        # Resultado de la prueba
        success_rate = (successful_readings / 5) * 100

        print(f"\n📊 RESULTADO:")
        print(f"✅ Lecturas exitosas: {successful_readings}/5 ({success_rate:.0f}%)")
        print(f"❌ Lecturas fallidas: {failed_readings}/5")

        if success_rate >= 80:
            print("🎉 Sensor funcionando CORRECTAMENTE")
            return True
        elif success_rate >= 60:
            print("⚠️  Sensor funcionando con PROBLEMAS menores")
            return True
        else:
            print("🚫 Sensor con PROBLEMAS graves o mal conectado")
            return False

    def stability_test(self, duration_minutes=3):
        """
        Prueba de estabilidad del sensor durante un período

        Args:
            duration_minutes (int): Duración de la prueba
        """
        print(f"\n⏱️  PRUEBA DE ESTABILIDAD - {duration_minutes} minutos")
        print("-" * 50)
        print("Tiempo\t\tTemperatura\tHumedad\t\tEstado")
        print("-" * 50)

        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)

        readings = []
        error_count = 0

        try:
            while time.time() < end_time:
                elapsed = (time.time() - start_time) / 60

                result = self.single_reading()

                if result["success"]:
                    temp = result["temperature"]
                    humid = result["humidity"]

                    print(f"{elapsed:5.1f}m\t\t{temp:5.1f}°C\t\t{humid:5.1f}%\t\t✅")

                    readings.append(
                        {"time": elapsed, "temperature": temp, "humidity": humid}
                    )
                else:
                    print(
                        f"{elapsed:5.1f}m\t\t---\t\t---\t\t❌ {result['error'][:20]}..."
                    )
                    error_count += 1

                time.sleep(10)  # Lectura cada 10 segundos

        except KeyboardInterrupt:
            print("\n⏹️  Prueba detenida por usuario")

        # Análisis de estabilidad
        self.analyze_stability(readings, error_count)

    def analyze_stability(self, readings, error_count):
        """
        Analiza la estabilidad de las lecturas

        Args:
            readings (list): Lista de lecturas válidas
            error_count (int): Número de errores
        """
        if not readings:
            print("\n❌ No hay lecturas válidas para analizar")
            return

        # Extraer datos
        temperatures = [r["temperature"] for r in readings]
        humidities = [r["humidity"] for r in readings]

        # Estadísticas de temperatura
        temp_avg = sum(temperatures) / len(temperatures)
        temp_min = min(temperatures)
        temp_max = max(temperatures)
        temp_range = temp_max - temp_min

        # Estadísticas de humedad
        humid_avg = sum(humidities) / len(humidities)
        humid_min = min(humidities)
        humid_max = max(humidities)
        humid_range = humid_max - humid_min

        # Calcular variabilidad
        temp_variance = sum([(t - temp_avg) ** 2 for t in temperatures]) / len(
            temperatures
        )
        humid_variance = sum([(h - humid_avg) ** 2 for h in humidities]) / len(
            humidities
        )

        print(f"\n📈 ANÁLISIS DE ESTABILIDAD:")
        print(f"📊 Lecturas válidas: {len(readings)}")
        print(f"❌ Errores: {error_count}")
        print(f"\n🌡️  TEMPERATURA:")
        print(f"   Promedio: {temp_avg:.1f}°C")
        print(f"   Rango: {temp_min:.1f}°C - {temp_max:.1f}°C")
        print(f"   Variación: {temp_range:.1f}°C")
        print(
            f"   Estabilidad: {'EXCELENTE' if temp_range < 1 else 'BUENA' if temp_range < 2 else 'REGULAR'}"
        )

        print(f"\n💧 HUMEDAD:")
        print(f"   Promedio: {humid_avg:.1f}%")
        print(f"   Rango: {humid_min:.1f}% - {humid_max:.1f}%")
        print(f"   Variación: {humid_range:.1f}%")
        print(
            f"   Estabilidad: {'EXCELENTE' if humid_range < 3 else 'BUENA' if humid_range < 5 else 'REGULAR'}"
        )

        # Evaluación general
        total_readings = len(readings) + error_count
        success_rate = (
            (len(readings) / total_readings) * 100 if total_readings > 0 else 0
        )

        print(f"\n🎯 EVALUACIÓN GENERAL:")
        print(f"   Tasa de éxito: {success_rate:.1f}%")

        if success_rate >= 90 and temp_range < 2 and humid_range < 5:
            print("   🟢 SENSOR EXCELENTE - Listo para uso")
        elif success_rate >= 75 and temp_range < 3 and humid_range < 8:
            print("   🟡 SENSOR BUENO - Aceptable para uso")
        else:
            print("   🔴 SENSOR PROBLEMÁTICO - Revisar conexiones")

    def connection_test(self):
        """
        Prueba específica de conexión y cableado
        """
        print("\n🔌 PRUEBA DE CONEXIÓN Y CABLEADO")
        print("-" * 40)

        print("1. Verificando configuración de pin...")
        try:
            pin_value = self.pin.value()
            print(f"   📍 Estado del pin: {'HIGH' if pin_value else 'LOW'}")

            if pin_value:
                print("   ✅ Pin en estado HIGH (correcto con pull-up)")
            else:
                print("   ⚠️  Pin en estado LOW (verificar pull-up)")

        except Exception as e:
            print(f"   ❌ Error leyendo pin: {e}")

        print("\n2. Verificando respuesta del sensor...")
        consecutive_failures = 0

        for i in range(10):
            result = self.single_reading()

            if result["success"]:
                print(f"   Intento {i+1}: ✅ Comunicación OK")
                consecutive_failures = 0
                break
            else:
                consecutive_failures += 1
                print(f"   Intento {i+1}: ❌ {result['error']}")

                if consecutive_failures >= 3:
                    print("   🚫 Múltiples fallos consecutivos detectados")
                    break

            time.sleep(2)

        # Diagnóstico de problemas
        if consecutive_failures >= 3:
            print("\n🔧 POSIBLES PROBLEMAS:")
            print("   • Sensor no conectado o dañado")
            print("   • Falta resistor pull-up de 4.7kΩ")
            print("   • Cable DATA suelto o cortado")
            print("   • Voltaje insuficiente (verificar VCC)")
            print("   • Pin GPIO incorrecto")

    def environmental_ranges_check(self):
        """
        Verifica que las lecturas estén en rangos ambientales normales
        """
        print("\n🌍 VERIFICACIÓN DE RANGOS AMBIENTALES")
        print("-" * 45)

        result = self.single_reading()

        if not result["success"]:
            print(f"❌ No se pudo verificar: {result['error']}")
            return

        temp = result["temperature"]
        humid = result["humidity"]

        print(f"Lectura actual: {temp}°C, {humid}%")

        # Verificar rangos normales
        temp_status = "🟢 NORMAL"
        if temp < -10 or temp > 60:
            temp_status = "🔴 FUERA DE RANGO TÍPICO"
        elif temp < 0 or temp > 50:
            temp_status = "🟡 RANGO EXTREMO"

        humid_status = "🟢 NORMAL"
        if humid < 0 or humid > 100:
            humid_status = "🔴 FUERA DE RANGO FÍSICO"
        elif humid < 10 or humid > 95:
            humid_status = "🟡 RANGO EXTREMO"

        print(f"Temperatura: {temp_status}")
        print(f"Humedad: {humid_status}")

        # Coherencia entre valores
        if temp > 40 and humid > 80:
            print("⚠️  Advertencia: Temperatura alta + Humedad alta (poco común)")
        elif temp < 5 and humid < 20:
            print(
                "⚠️  Advertencia: Temperatura baja + Humedad baja (verificar ambiente)"
            )


def diagnostic_menu():
    """
    Menú interactivo para diagnóstico del DHT22
    """
    print("\n" + "=" * 60)
    print("🌡️  DIAGNÓSTICO SENSOR DHT22")
    print("=" * 60)

    # Solicitar pin
    try:
        pin_input = input("Pin de datos DHT22 (por defecto 15): ").strip()
        pin_number = int(pin_input) if pin_input else 15
    except ValueError:
        pin_number = 15
        print(f"Usando pin por defecto: {pin_number}")

    try:
        sensor = DHT22Diagnostics(data_pin=pin_number)

        while True:
            print("\n" + "-" * 40)
            print("🔍 OPCIONES DE DIAGNÓSTICO:")
            print("-" * 40)
            print("1. 🧪 Prueba básica de funcionamiento")
            print("2. ⏱️  Prueba de estabilidad (3 min)")
            print("3. 🔌 Prueba de conexión")
            print("4. 🌍 Verificación de rangos ambientales")
            print("5. 📊 Lectura única")
            print("6. 🔄 Lecturas continuas")
            print("7. 🚪 Salir")

            option = input("\nSelecciona (1-7): ").strip()

            if option == "1":
                sensor.test_basic_functionality()

            elif option == "2":
                duration = input("Duración en minutos (por defecto 3): ").strip()
                duration = int(duration) if duration.isdigit() else 3
                sensor.stability_test(duration)

            elif option == "3":
                sensor.connection_test()

            elif option == "4":
                sensor.environmental_ranges_check()

            elif option == "5":
                result = sensor.single_reading()
                if result["success"]:
                    print(f"🌡️  Temperatura: {result['temperature']}°C")
                    print(f"💧 Humedad: {result['humidity']}%")
                else:
                    print(f"❌ Error: {result['error']}")

            elif option == "6":
                print("📊 Lecturas continuas cada 3s (Ctrl+C para parar)")
                try:
                    while True:
                        result = sensor.single_reading()
                        if result["success"]:
                            print(
                                f"🌡️ {result['temperature']:5.1f}°C | 💧 {result['humidity']:5.1f}%"
                            )
                        else:
                            print(f"❌ {result['error']}")
                        time.sleep(3)
                except KeyboardInterrupt:
                    print("\n⏹️  Lecturas detenidas")

            elif option == "7":
                print("👋 Saliendo del diagnóstico...")
                break

            else:
                print("❌ Opción no válida")

    except Exception as e:
        print(f"❌ Error en diagnóstico: {e}")
        print("🔧 Verificar conexiones y configuración")


if __name__ == "__main__":
    diagnostic_menu()
