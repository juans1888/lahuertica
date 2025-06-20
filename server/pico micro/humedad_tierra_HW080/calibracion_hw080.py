"""
Sistema de calibración automática para sensor HW-080
Permite calibrar el sensor paso a paso con validación
"""

from machine import Pin, ADC
import time
import json


class HW080Calibrator:
    """
    Clase para calibración automática del sensor HW-080
    """

    def __init__(self, adc_pin=26, digital_pin=16):
        """
        Inicializa el calibrador del sensor

        Args:
            adc_pin (int): Pin ADC
            digital_pin (int): Pin digital
        """
        try:
            self.adc = ADC(Pin(adc_pin))
            self.digital_pin = Pin(digital_pin, Pin.IN)
            self.calibration_data = {}

            print("Calibrador HW-080 inicializado")
            print("IMPORTANTE: Sigue las instrucciones exactamente")

        except Exception as e:
            print(f"Error inicializando calibrador: {e}")
            raise

    def take_stable_readings(self, condition_name, samples=15, stabilization_time=3):
        """
        Toma lecturas estables para una condición específica

        Args:
            condition_name (str): Nombre de la condición
            samples (int): Número de muestras
            stabilization_time (int): Tiempo de estabilización

        Returns:
            dict: Estadísticas de las lecturas
        """
        print(f"\n--- CALIBRANDO: {condition_name.upper()} ---")
        print(f"Tiempo de estabilización: {stabilization_time} segundos")

        # Tiempo de estabilización
        for i in range(stabilization_time, 0, -1):
            print(f"Estabilizando... {i}s", end="\r")
            time.sleep(1)

        print(f"\nTomando {samples} lecturas...")

        readings = []
        digital_states = []

        for i in range(samples):
            # Lectura analógica
            raw_value = self.adc.read_u16()
            readings.append(raw_value)

            # Lectura digital
            digital_state = not self.digital_pin.value()
            digital_states.append(digital_state)

            print(
                f"Lectura {i+1:2d}: {raw_value:5d} | Digital: {'H' if digital_state else 'S'}"
            )
            time.sleep(0.3)

        # Calcular estadísticas
        if readings:
            avg = sum(readings) / len(readings)
            min_val = min(readings)
            max_val = max(readings)
            deviation = max_val - min_val
            digital_humid_count = sum(digital_states)

            stats = {
                "condition": condition_name,
                "average": avg,
                "minimum": min_val,
                "maximum": max_val,
                "deviation": deviation,
                "samples": len(readings),
                "digital_humid_ratio": digital_humid_count / len(digital_states),
                "raw_readings": readings,
                "digital_readings": digital_states,
            }

            print(f"\nEstadísticas para {condition_name}:")
            print(f"Promedio: {avg:.1f}")
            print(f"Rango: {min_val} - {max_val}")
            print(f"Desviación: {deviation}")
            print(
                f"Digital húmedo: {digital_humid_count}/{len(digital_states)} lecturas"
            )

            return stats

        return None

    def validate_readings(self, dry_stats, wet_stats):
        """
        Valida que las lecturas de calibración sean correctas

        Args:
            dry_stats (dict): Estadísticas del estado seco
            wet_stats (dict): Estadísticas del estado húmedo

        Returns:
            tuple: (es_válido, mensaje)
        """
        print("\n--- VALIDANDO CALIBRACIÓN ---")

        # Verificar que hay diferencia significativa
        difference = dry_stats["average"] - wet_stats["average"]
        min_difference = 5000  # Diferencia mínima esperada

        if difference < min_difference:
            return (
                False,
                f"Diferencia insuficiente ({difference:.0f}). Mínimo: {min_difference}",
            )

        # Verificar que seco > húmedo (lógica del sensor capacitivo)
        if dry_stats["average"] <= wet_stats["average"]:
            return False, "Valores invertidos: seco debe ser mayor que húmedo"

        # Verificar estabilidad (desviación no muy alta)
        max_deviation = 3000
        if dry_stats["deviation"] > max_deviation:
            return False, f"Lecturas secas inestables (desv: {dry_stats['deviation']})"

        if wet_stats["deviation"] > max_deviation:
            return (
                False,
                f"Lecturas húmedas inestables (desv: {wet_stats['deviation']})",
            )

        # Verificar estado digital
        if wet_stats["digital_humid_ratio"] < 0.7:
            print(
                f"ADVERTENCIA: Estado digital húmedo solo {wet_stats['digital_humid_ratio']*100:.0f}% del tiempo"
            )
            print("Puede necesitar ajustar el potenciómetro del módulo")

        print("✓ Calibración VÁLIDA")
        print(f"✓ Diferencia: {difference:.0f} puntos")
        print(f"✓ Rango útil: {wet_stats['average']:.0f} - {dry_stats['average']:.0f}")

        return True, "Calibración exitosa"

    def run_full_calibration(self):
        """
        Ejecuta el proceso completo de calibración

        Returns:
            dict: Datos de calibración finales
        """
        print("\n" + "=" * 60)
        print("CALIBRACIÓN AUTOMÁTICA SENSOR HW-080")
        print("=" * 60)
        print("\nSigue las instrucciones cuidadosamente...")

        # FASE 1: Calibración en SECO
        print("\n🌵 FASE 1: CALIBRACIÓN EN SECO")
        print("Instrucciones:")
        print("1. Retira el sensor de cualquier superficie")
        print("2. Déjalo en el aire libre")
        print("3. NO toques las placas metálicas")

        input("\nPresiona ENTER cuando el sensor esté en el aire...")

        dry_stats = self.take_stable_readings("SECO", samples=15)

        if not dry_stats:
            print("❌ Error en calibración seca")
            return None

        # FASE 2: Calibración en HÚMEDO
        print("\n💧 FASE 2: CALIBRACIÓN EN HÚMEDO")
        print("Instrucciones:")
        print("1. Prepara tierra húmeda (no barro)")
        print("2. Inserta el sensor COMPLETAMENTE")
        print("3. Asegúrate que las placas toquen la tierra")
        print("4. La tierra debe estar húmeda, no encharcada")

        input("\nPresiona ENTER cuando el sensor esté en tierra húmeda...")

        wet_stats = self.take_stable_readings("HÚMEDO", samples=15)

        if not wet_stats:
            print("❌ Error en calibración húmeda")
            return None

        # VALIDACIÓN
        is_valid, message = self.validate_readings(dry_stats, wet_stats)

        if not is_valid:
            print(f"\n❌ CALIBRACIÓN INVÁLIDA: {message}")
            print("Repite el proceso de calibración")
            return None

        # GUARDAR CALIBRACIÓN
        calibration = {
            "dry_value": int(dry_stats["average"]),
            "wet_value": int(wet_stats["average"]),
            "timestamp": time.time(),
            "validation_passed": True,
            "dry_stats": dry_stats,
            "wet_stats": wet_stats,
        }

        self.calibration_data = calibration

        print(f"\n✅ CALIBRACIÓN COMPLETADA")
        print(f"Valor SECO: {calibration['dry_value']}")
        print(f"Valor HÚMEDO: {calibration['wet_value']}")
        print(
            f"Rango de trabajo: {calibration['wet_value']} - {calibration['dry_value']}"
        )

        return calibration

    def save_calibration_to_file(self, filename="hw080_calibration.json"):
        """
        Guarda la calibración en un archivo JSON

        Args:
            filename (str): Nombre del archivo
        """
        if not self.calibration_data:
            print("No hay datos de calibración para guardar")
            return False

        try:
            # Crear versión simplificada para guardar
            save_data = {
                "dry_value": self.calibration_data["dry_value"],
                "wet_value": self.calibration_data["wet_value"],
                "timestamp": self.calibration_data["timestamp"],
                "validation_passed": self.calibration_data["validation_passed"],
            }

            with open(filename, "w") as f:
                json.dump(save_data, f)

            print(f"✅ Calibración guardada en {filename}")
            return True

        except Exception as e:
            print(f"❌ Error guardando calibración: {e}")
            return False

    def test_calibration(self, duration_seconds=30):
        """
        Prueba la calibración obtenida

        Args:
            duration_seconds (int): Duración del test
        """
        if not self.calibration_data:
            print("No hay calibración para probar")
            return

        print(f"\n--- PROBANDO CALIBRACIÓN ---")
        print(f"Duración: {duration_seconds} segundos")
        print("Tiempo\t\tValor\tHumedad%\tDigital")
        print("-" * 50)

        start_time = time.time()

        try:
            while (time.time() - start_time) < duration_seconds:
                # Leer valor
                raw_value = self.adc.read_u16()
                digital_state = not self.digital_pin.value()

                # Calcular porcentaje usando calibración
                dry_val = self.calibration_data["dry_value"]
                wet_val = self.calibration_data["wet_value"]

                humidity = ((dry_val - raw_value) / (dry_val - wet_val)) * 100
                humidity = max(0, min(100, humidity))

                elapsed = time.time() - start_time
                digital_text = "HÚMEDO" if digital_state else "SECO"

                print(
                    f"{elapsed:6.1f}s\t\t{raw_value}\t{humidity:5.1f}%\t\t{digital_text}"
                )

                time.sleep(2)

        except KeyboardInterrupt:
            print("\nTest detenido por usuario")


def main():
    """
    Función principal para ejecutar calibración
    """
    try:
        calibrator = HW080Calibrator()

        # Ejecutar calibración completa
        result = calibrator.run_full_calibration()

        if result:
            # Guardar calibración
            calibrator.save_calibration_to_file()

            # Probar calibración
            print("\n¿Quieres probar la calibración? (s/n): ", end="")
            if input().lower().startswith("s"):
                print("\nMueve el sensor entre seco y húmedo para ver los cambios...")
                calibrator.test_calibration(duration_seconds=60)

            print("\n🎉 Proceso completado exitosamente!")
            print("Puedes usar estos valores en tu código principal:")
            print(f"dry_value = {result['dry_value']}")
            print(f"wet_value = {result['wet_value']}")
        else:
            print("\n❌ Calibración fallida. Revisa las conexiones y repite.")

    except Exception as e:
        print(f"Error en calibración: {e}")


if __name__ == "__main__":
    main()
