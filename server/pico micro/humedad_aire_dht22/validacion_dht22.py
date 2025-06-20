"""
Sistema de validación y verificación para sensor DHT22
Verifica precisión, detecta offsets y valida funcionamiento
"""

import dht
from machine import Pin
import time
import json
import gc


class DHT22Validator:
    """
    Clase para validación y verificación del DHT22
    """

    def __init__(self, data_pin=15):
        """
        Inicializa el validador del DHT22

        Args:
            data_pin (int): Pin de datos
        """
        try:
            self.pin = Pin(data_pin, Pin.IN, Pin.PULL_UP)
            self.sensor = dht.DHT22(self.pin)
            self.data_pin = data_pin

            # Configuración de validación
            self.validation_config = {
                "min_successful_readings": 8,  # de 10 intentos
                "max_temperature_variation": 2.0,  # °C
                "max_humidity_variation": 5.0,  # %
                "expected_temp_range": (-10, 50),  # °C ambiente normal
                "expected_humid_range": (10, 95),  # % ambiente normal
                "reading_interval": 2.5,  # segundos entre lecturas
                "stability_samples": 15,  # muestras para estabilidad
            }

            # Resultados de validación
            self.validation_results = {
                "sensor_working": False,
                "precision_ok": False,
                "stability_ok": False,
                "ranges_ok": False,
                "offset_detected": False,
                "temperature_offset": 0.0,
                "humidity_offset": 0.0,
                "recommendations": [],
            }

            print("🌡️  Validador DHT22 inicializado")
            print("🔍 Preparado para verificación completa")

        except Exception as e:
            print(f"❌ Error inicializando validador: {e}")
            raise

    def take_stable_readings(self, num_samples=10, description="lecturas"):
        """
        Toma múltiples lecturas estables del sensor

        Args:
            num_samples (int): Número de muestras
            description (str): Descripción del proceso

        Returns:
            dict: Estadísticas de las lecturas
        """
        print(f"\n📊 Tomando {num_samples} {description}...")
        print("Muestra\t\tTemperatura\tHumedad\t\tEstado")
        print("-" * 55)

        successful_readings = []
        failed_readings = []

        for i in range(num_samples):
            try:
                gc.collect()  # Limpiar memoria
                self.sensor.measure()

                temp = self.sensor.temperature()
                humid = self.sensor.humidity()

                # Validar que los valores sean razonables
                if (-40 <= temp <= 80) and (0 <= humid <= 100):
                    successful_readings.append(
                        {"temperature": temp, "humidity": humid, "sample": i + 1}
                    )
                    print(f"{i+1:2d}\t\t{temp:5.1f}°C\t\t{humid:5.1f}%\t\t✅")
                else:
                    failed_readings.append(
                        {
                            "error": f"Valores fuera de rango: T={temp}, H={humid}",
                            "sample": i + 1,
                        }
                    )
                    print(f"{i+1:2d}\t\t{temp:5.1f}°C\t\t{humid:5.1f}%\t\t⚠️ Rango")

            except OSError as e:
                failed_readings.append(
                    {"error": f"Error comunicación: {e}", "sample": i + 1}
                )
                print(f"{i+1:2d}\t\t---\t\t---\t\t❌ Error")

            except Exception as e:
                failed_readings.append(
                    {"error": f"Error general: {e}", "sample": i + 1}
                )
                print(f"{i+1:2d}\t\t---\t\t---\t\t❌ Fallo")

            if i < num_samples - 1:  # No esperar después de la última lectura
                time.sleep(self.validation_config["reading_interval"])

        # Calcular estadísticas
        if successful_readings:
            temperatures = [r["temperature"] for r in successful_readings]
            humidities = [r["humidity"] for r in successful_readings]

            stats = {
                "successful_count": len(successful_readings),
                "failed_count": len(failed_readings),
                "success_rate": (len(successful_readings) / num_samples) * 100,
                "temperature": {
                    "average": sum(temperatures) / len(temperatures),
                    "min": min(temperatures),
                    "max": max(temperatures),
                    "range": max(temperatures) - min(temperatures),
                    "values": temperatures,
                },
                "humidity": {
                    "average": sum(humidities) / len(humidities),
                    "min": min(humidities),
                    "max": max(humidities),
                    "range": max(humidities) - min(humidities),
                    "values": humidities,
                },
                "raw_data": successful_readings,
                "errors": failed_readings,
            }

            print(f"\n📈 Estadísticas de {description}:")
            print(
                f"✅ Exitosas: {stats['successful_count']}/{num_samples} ({stats['success_rate']:.1f}%)"
            )
            print(
                f"🌡️  Temperatura: {stats['temperature']['average']:.1f}°C (±{stats['temperature']['range']/2:.1f}°C)"
            )
            print(
                f"💧 Humedad: {stats['humidity']['average']:.1f}% (±{stats['humidity']['range']/2:.1f}%)"
            )

            return stats
        else:
            return {
                "successful_count": 0,
                "failed_count": len(failed_readings),
                "success_rate": 0,
                "errors": failed_readings,
            }

    def validate_sensor_functionality(self):
        """
        Valida la funcionalidad básica del sensor

        Returns:
            bool: True si el sensor funciona correctamente
        """
        print("\n🧪 VALIDACIÓN DE FUNCIONALIDAD BÁSICA")
        print("=" * 45)

        stats = self.take_stable_readings(10, "muestras de funcionalidad")

        # Evaluar funcionalidad
        min_success_rate = (
            self.validation_config["min_successful_readings"] / 10
        ) * 100

        if stats["success_rate"] >= min_success_rate:
            print(f"✅ Sensor FUNCIONAL (≥{min_success_rate:.0f}% éxito)")
            self.validation_results["sensor_working"] = True
            return True
        else:
            print(f"❌ Sensor PROBLEMÁTICO (<{min_success_rate:.0f}% éxito)")
            self.validation_results["sensor_working"] = False
            self.validation_results["recommendations"].append(
                "Verificar conexiones, resistor pull-up y alimentación"
            )
            return False

    def validate_precision_and_stability(self):
        """
        Valida la precisión y estabilidad del sensor

        Returns:
            bool: True si la precisión es aceptable
        """
        print("\n📐 VALIDACIÓN DE PRECISIÓN Y ESTABILIDAD")
        print("=" * 45)

        stats = self.take_stable_readings(
            self.validation_config["stability_samples"], "muestras de estabilidad"
        )

        if stats["successful_count"] < 5:
            print("❌ Insuficientes lecturas para evaluar precisión")
            return False

        # Evaluar variación de temperatura
        temp_variation = stats["temperature"]["range"]
        max_temp_var = self.validation_config["max_temperature_variation"]

        if temp_variation <= max_temp_var:
            print(
                f"✅ Estabilidad temperatura OK (±{temp_variation/2:.1f}°C ≤ ±{max_temp_var/2:.1f}°C)"
            )
            temp_stable = True
        else:
            print(
                f"⚠️  Temperatura inestable (±{temp_variation/2:.1f}°C > ±{max_temp_var/2:.1f}°C)"
            )
            temp_stable = False
            self.validation_results["recommendations"].append(
                "Temperatura muy variable - verificar corrientes de aire o vibraciones"
            )

        # Evaluar variación de humedad
        humid_variation = stats["humidity"]["range"]
        max_humid_var = self.validation_config["max_humidity_variation"]

        if humid_variation <= max_humid_var:
            print(
                f"✅ Estabilidad humedad OK (±{humid_variation/2:.1f}% ≤ ±{max_humid_var/2:.1f}%)"
            )
            humid_stable = True
        else:
            print(
                f"⚠️  Humedad inestable (±{humid_variation/2:.1f}% > ±{max_humid_var/2:.1f}%)"
            )
            humid_stable = False
            self.validation_results["recommendations"].append(
                "Humedad muy variable - verificar flujo de aire o cambios ambientales"
            )

        # Resultado general
        precision_ok = temp_stable and humid_stable
        self.validation_results["precision_ok"] = precision_ok
        self.validation_results["stability_ok"] = precision_ok

        if precision_ok:
            print("🎯 Precisión y estabilidad ACEPTABLES")
        else:
            print("🎯 Precisión o estabilidad PROBLEMÁTICAS")

        return precision_ok

    def validate_environmental_ranges(self):
        """
        Valida que las lecturas estén en rangos ambientales esperados

        Returns:
            bool: True si los rangos son normales
        """
        print("\n🌍 VALIDACIÓN DE RANGOS AMBIENTALES")
        print("=" * 40)

        stats = self.take_stable_readings(5, "muestras ambientales")

        if stats["successful_count"] == 0:
            print("❌ No hay lecturas para validar rangos")
            return False

        # Verificar rangos de temperatura
        temp_avg = stats["temperature"]["average"]
        temp_range = self.validation_config["expected_temp_range"]

        if temp_range[0] <= temp_avg <= temp_range[1]:
            print(f"✅ Temperatura en rango normal ({temp_avg:.1f}°C)")
            temp_range_ok = True
        else:
            print(f"⚠️  Temperatura fuera de rango típico ({temp_avg:.1f}°C)")
            print(f"   Rango esperado: {temp_range[0]}°C - {temp_range[1]}°C")
            temp_range_ok = False

            if temp_avg < temp_range[0]:
                self.validation_results["recommendations"].append(
                    "Temperatura muy baja - verificar calefacción o ambiente frío"
                )
            else:
                self.validation_results["recommendations"].append(
                    "Temperatura muy alta - verificar refrigeración o fuente de calor"
                )

        # Verificar rangos de humedad
        humid_avg = stats["humidity"]["average"]
        humid_range = self.validation_config["expected_humid_range"]

        if humid_range[0] <= humid_avg <= humid_range[1]:
            print(f"✅ Humedad en rango normal ({humid_avg:.1f}%)")
            humid_range_ok = True
        else:
            print(f"⚠️  Humedad fuera de rango típico ({humid_avg:.1f}%)")
            print(f"   Rango esperado: {humid_range[0]}% - {humid_range[1]}%")
            humid_range_ok = False

            if humid_avg < humid_range[0]:
                self.validation_results["recommendations"].append(
                    "Humedad muy baja - ambiente muy seco"
                )
            else:
                self.validation_results["recommendations"].append(
                    "Humedad muy alta - verificar ventilación o fuentes de humedad"
                )

        # Resultado general
        ranges_ok = temp_range_ok and humid_range_ok
        self.validation_results["ranges_ok"] = ranges_ok

        return ranges_ok

    def detect_systematic_offset(self, reference_temp=None, reference_humid=None):
        """
        Detecta offset sistemático comparando con valores de referencia

        Args:
            reference_temp (float, optional): Temperatura de referencia conocida
            reference_humid (float, optional): Humedad de referencia conocida

        Returns:
            dict: Información sobre offsets detectados
        """
        print("\n🎯 DETECCIÓN DE OFFSET SISTEMÁTICO")
        print("=" * 40)

        if reference_temp is None and reference_humid is None:
            print("⚠️  Sin valores de referencia - saltando detección de offset")
            print("💡 Para detectar offset, proporciona valores de referencia")
            return {"offset_detected": False}

        stats = self.take_stable_readings(10, "muestras para offset")

        if stats["successful_count"] < 5:
            print("❌ Insuficientes lecturas para detectar offset")
            return {"offset_detected": False}

        sensor_temp = stats["temperature"]["average"]
        sensor_humid = stats["humidity"]["average"]

        offset_info = {"offset_detected": False}

        # Detectar offset de temperatura
        if reference_temp is not None:
            temp_offset = sensor_temp - reference_temp

            if abs(temp_offset) > 1.0:  # Offset significativo > 1°C
                print(f"🌡️  OFFSET TEMPERATURA detectado: {temp_offset:+.1f}°C")
                print(
                    f"   Sensor: {sensor_temp:.1f}°C | Referencia: {reference_temp:.1f}°C"
                )

                offset_info["temperature_offset"] = temp_offset
                offset_info["offset_detected"] = True

                self.validation_results["temperature_offset"] = temp_offset
                self.validation_results["offset_detected"] = True

                if abs(temp_offset) > 3.0:
                    self.validation_results["recommendations"].append(
                        f"Offset de temperatura alto ({temp_offset:+.1f}°C) - considerar reemplazo"
                    )
                else:
                    self.validation_results["recommendations"].append(
                        f"Aplicar compensación de temperatura: valor_real = lectura - ({temp_offset:+.1f})"
                    )
            else:
                print(f"✅ Temperatura sin offset significativo ({temp_offset:+.1f}°C)")

        # Detectar offset de humedad
        if reference_humid is not None:
            humid_offset = sensor_humid - reference_humid

            if abs(humid_offset) > 3.0:  # Offset significativo > 3%
                print(f"💧 OFFSET HUMEDAD detectado: {humid_offset:+.1f}%")
                print(
                    f"   Sensor: {sensor_humid:.1f}% | Referencia: {reference_humid:.1f}%"
                )

                offset_info["humidity_offset"] = humid_offset
                offset_info["offset_detected"] = True

                self.validation_results["humidity_offset"] = humid_offset
                self.validation_results["offset_detected"] = True

                if abs(humid_offset) > 8.0:
                    self.validation_results["recommendations"].append(
                        f"Offset de humedad alto ({humid_offset:+.1f}%) - considerar reemplazo"
                    )
                else:
                    self.validation_results["recommendations"].append(
                        f"Aplicar compensación de humedad: valor_real = lectura - ({humid_offset:+.1f})"
                    )
            else:
                print(f"✅ Humedad sin offset significativo ({humid_offset:+.1f}%)")

        return offset_info

    def run_complete_validation(self):
        """
        Ejecuta validación completa del sensor

        Returns:
            dict: Resultados completos de validación
        """
        print("\n" + "=" * 60)
        print("🌡️  VALIDACIÓN COMPLETA SENSOR DHT22")
        print("=" * 60)

        # Resetear resultados
        self.validation_results = {
            "sensor_working": False,
            "precision_ok": False,
            "stability_ok": False,
            "ranges_ok": False,
            "offset_detected": False,
            "temperature_offset": 0.0,
            "humidity_offset": 0.0,
            "recommendations": [],
        }

        # Fase 1: Funcionalidad básica
        print("🔄 FASE 1: Validando funcionalidad básica...")
        if not self.validate_sensor_functionality():
            print("❌ Sensor no funcional - deteniendo validación")
            return self.validation_results

        # Fase 2: Precisión y estabilidad
        print("\n🔄 FASE 2: Validando precisión y estabilidad...")
        self.validate_precision_and_stability()

        # Fase 3: Rangos ambientales
        print("\n🔄 FASE 3: Validando rangos ambientales...")
        self.validate_environmental_ranges()

        # Fase 4: Detección de offset (opcional)
        print("\n🔄 FASE 4: Detección de offset...")
        print("💡 Para detectar offset, necesitas valores de referencia")

        try:
            ref_temp_input = input(
                "Temperatura de referencia (°C) [Enter para saltar]: "
            ).strip()
            ref_humid_input = input(
                "Humedad de referencia (%) [Enter para saltar]: "
            ).strip()

            ref_temp = float(ref_temp_input) if ref_temp_input else None
            ref_humid = float(ref_humid_input) if ref_humid_input else None

            if ref_temp or ref_humid:
                self.detect_systematic_offset(ref_temp, ref_humid)
            else:
                print("⏭️  Saltando detección de offset")

        except ValueError:
            print("❌ Valores de referencia inválidos - saltando offset")

        # Generar reporte final
        self.generate_validation_report()

        return self.validation_results

    def generate_validation_report(self):
        """
        Genera reporte final de validación
        """
        print("\n" + "=" * 50)
        print("📋 REPORTE FINAL DE VALIDACIÓN")
        print("=" * 50)

        results = self.validation_results

        # Estado general
        overall_status = (
            "APROBADO"
            if (results["sensor_working"] and results["precision_ok"])
            else "PROBLEMÁTICO"
        )

        status_emoji = "✅" if overall_status == "APROBADO" else "❌"

        print(f"\n🎯 ESTADO GENERAL: {status_emoji} {overall_status}")

        # Detalles por categoría
        print(f"\n📊 DETALLES:")
        print(
            f"   🔧 Funcionalidad: {'✅ OK' if results['sensor_working'] else '❌ FALLO'}"
        )
        print(
            f"   🎯 Precisión: {'✅ OK' if results['precision_ok'] else '❌ PROBLEMÁTICA'}"
        )
        print(
            f"   📈 Estabilidad: {'✅ OK' if results['stability_ok'] else '❌ INESTABLE'}"
        )
        print(
            f"   🌍 Rangos: {'✅ NORMALES' if results['ranges_ok'] else '⚠️ EXTREMOS'}"
        )

        # Offsets detectados
        if results["offset_detected"]:
            print(f"\n⚠️  OFFSETS DETECTADOS:")
            if results["temperature_offset"] != 0:
                print(f"   🌡️  Temperatura: {results['temperature_offset']:+.1f}°C")
            if results["humidity_offset"] != 0:
                print(f"   💧 Humedad: {results['humidity_offset']:+.1f}%")
        else:
            print(f"\n✅ Sin offsets significativos detectados")

        # Recomendaciones
        if results["recommendations"]:
            print(f"\n💡 RECOMENDACIONES:")
            for i, rec in enumerate(results["recommendations"], 1):
                print(f"   {i}. {rec}")
        else:
            print(f"\n🎉 No hay recomendaciones - sensor funcionando óptimamente")

        # Veredicto final
        if overall_status == "APROBADO":
            print(f"\n🚀 SENSOR LISTO PARA USO EN PRODUCCIÓN")
        else:
            print(f"\n🔧 SENSOR NECESITA ATENCIÓN ANTES DEL USO")

    def save_validation_config(self, filename="dht22_validation.json"):
        """
        Guarda configuración de validación en archivo

        Args:
            filename (str): Nombre del archivo
        """
        config_data = {
            "validation_config": self.validation_config,
            "validation_results": self.validation_results,
            "timestamp": time.time(),
            "pin_used": self.data_pin,
        }

        try:
            with open(filename, "w") as f:
                json.dump(config_data, f)
            print(f"✅ Configuración guardada en {filename}")
        except Exception as e:
            print(f"❌ Error guardando configuración: {e}")


def main():
    """
    Función principal de validación
    """
    try:
        # Solicitar pin
        pin_input = input("Pin de datos DHT22 (por defecto 15): ").strip()
        pin_number = int(pin_input) if pin_input else 15

        # Crear validador
        validator = DHT22Validator(data_pin=pin_number)

        print("\n🌡️  OPCIONES DE VALIDACIÓN:")
        print("1. 🔍 Validación completa automática")
        print("2. 🎛️  Validación paso a paso")

        option = input("Selecciona (1-2): ").strip()

        if option == "1":
            # Validación completa
            results = validator.run_complete_validation()

            # Guardar resultados
            save_option = (
                input("\n¿Guardar resultados? (s/n): ").lower().startswith("s")
            )
            if save_option:
                validator.save_validation_config()

        elif option == "2":
            # Validación manual paso a paso
            print("🔧 Modo manual - ejecuta cada fase por separado")

            while True:
                print("\n🔍 FASES DISPONIBLES:")
                print("1. Funcionalidad básica")
                print("2. Precisión y estabilidad")
                print("3. Rangos ambientales")
                print("4. Detección de offset")
                print("5. Reporte final")
                print("6. Salir")

                phase = input("Selecciona fase (1-6): ").strip()

                if phase == "1":
                    validator.validate_sensor_functionality()
                elif phase == "2":
                    validator.validate_precision_and_stability()
                elif phase == "3":
                    validator.validate_environmental_ranges()
                elif phase == "4":
                    ref_temp = input("Temp. referencia (°C): ").strip()
                    ref_humid = input("Humedad referencia (%): ").strip()

                    ref_temp = float(ref_temp) if ref_temp else None
                    ref_humid = float(ref_humid) if ref_humid else None

                    validator.detect_systematic_offset(ref_temp, ref_humid)
                elif phase == "5":
                    validator.generate_validation_report()
                elif phase == "6":
                    break
                else:
                    print("❌ Fase no válida")

        print("\n🎉 Validación completada")

    except Exception as e:
        print(f"❌ Error en validación: {e}")


if __name__ == "__main__":
    main()
