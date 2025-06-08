"""
Sensor HW-080 con calibración final exitosa
Valores calibrados: dry_value=65535, wet_value=26221
"""

from machine import Pin, ADC
import time
import json


class HW080FinalCalibrated:
    """
    Sensor HW-080 con calibración personalizada exitosa
    """

    def __init__(self, adc_pin=26, digital_pin=16):
        """
        Inicializa el sensor con los valores calibrados

        Args:
            adc_pin (int): Pin ADC (por defecto 26)
            digital_pin (int): Pin digital (por defecto 16)
        """
        try:
            self.adc = ADC(Pin(adc_pin))
            self.digital_pin = Pin(digital_pin, Pin.IN)

            # TUS VALORES CALIBRADOS EXITOSAMENTE
            self.calibration = {
                "dry_value": 65535,  # Perfecto: máximo ADC
                "wet_value": 26221,  # Tu calibración húmeda
                "range": 39314,  # Excelente rango de trabajo
            }

            print("🌱 Sensor HW-080 inicializado con calibración exitosa")
            print(f"📊 Rango de trabajo: {self.calibration['range']} puntos")

        except Exception as e:
            print(f"❌ Error inicializando sensor: {e}")
            raise

    def read_raw_value(self):
        """
        Lee el valor analógico crudo del sensor

        Returns:
            int: Valor ADC entre 0 y 65535
        """
        try:
            return self.adc.read_u16()
        except Exception as e:
            print(f"Error leyendo valor: {e}")
            return None

    def read_digital_state(self):
        """
        Lee el estado digital del sensor

        Returns:
            bool: True si húmedo, False si seco
        """
        try:
            return not self.digital_pin.value()
        except Exception as e:
            print(f"Error leyendo digital: {e}")
            return None

    def calculate_humidity_percentage(self, raw_value=None):
        """
        Calcula porcentaje de humedad con TU calibración

        Args:
            raw_value (int, optional): Valor crudo

        Returns:
            float: Porcentaje de humedad (0-100%+)
        """
        try:
            if raw_value is None:
                raw_value = self.read_raw_value()

            if raw_value is None:
                return None

            dry_val = self.calibration["dry_value"]  # 65535
            wet_val = self.calibration["wet_value"]  # 26221

            # Calcular porcentaje usando TU calibración
            humidity = ((dry_val - raw_value) / (dry_val - wet_val)) * 100

            # Permitir valores > 100% (tierra muy húmeda)
            # Limitar valores < 0% (aire muy seco)
            humidity = max(0, humidity)

            return round(humidity, 1)

        except Exception as e:
            print(f"Error calculando porcentaje: {e}")
            return None

    def get_moisture_level_description(self, humidity_percent):
        """
        Convierte porcentaje a descripción de humedad

        Args:
            humidity_percent (float): Porcentaje de humedad

        Returns:
            tuple: (nivel, descripción, emoji)
        """
        if humidity_percent is None:
            return "ERROR", "Error de lectura", "❌"
        elif humidity_percent >= 100:
            return "SATURADO", "Muy húmedo o encharcado", "💧"
        elif humidity_percent >= 80:
            return "MUY_HÚMEDO", "Perfecta para plantas", "🌿"
        elif humidity_percent >= 60:
            return "HÚMEDO", "Buena humedad", "🌱"
        elif humidity_percent >= 40:
            return "MODERADO", "Humedad aceptable", "🟡"
        elif humidity_percent >= 20:
            return "SECO", "Necesita riego", "🟠"
        else:
            return "MUY_SECO", "Riego urgente", "🔴"

    def get_complete_reading(self):
        """
        Obtiene lectura completa del sensor

        Returns:
            dict: Datos completos con interpretación
        """
        try:
            # Lecturas básicas
            raw_value = self.read_raw_value()
            digital_state = self.read_digital_state()
            humidity_percent = self.calculate_humidity_percentage(raw_value)

            # Interpretación
            level, description, emoji = self.get_moisture_level_description(
                humidity_percent
            )

            # Recomendación de riego
            if humidity_percent is not None:
                if humidity_percent < 30:
                    irrigation_recommendation = "REGAR_AHORA"
                elif humidity_percent < 50:
                    irrigation_recommendation = "CONSIDERAR_RIEGO"
                elif humidity_percent < 90:
                    irrigation_recommendation = "NO_REGAR"
                else:
                    irrigation_recommendation = "ESPERAR_DRENAJE"
            else:
                irrigation_recommendation = "ERROR_SENSOR"

            return {
                "timestamp": time.time(),
                "raw_value": raw_value,
                "humidity_percentage": humidity_percent,
                "digital_state": digital_state,
                "moisture_level": level,
                "description": description,
                "emoji": emoji,
                "irrigation_recommendation": irrigation_recommendation,
                "calibration_info": {
                    "dry_value": self.calibration["dry_value"],
                    "wet_value": self.calibration["wet_value"],
                    "working_range": self.calibration["range"],
                },
                "status": "success",
            }

        except Exception as e:
            return {"timestamp": time.time(), "error": str(e), "status": "error"}

    def monitor_smart(self, duration_minutes=10, interval_seconds=5):
        """
        Monitoreo inteligente con interpretación

        Args:
            duration_minutes (int): Duración del monitoreo
            interval_seconds (int): Intervalo entre lecturas
        """
        print(f"\n🔍 MONITOREO INTELIGENTE - {duration_minutes} minutos")
        print(
            f"📊 Calibración: Seco={self.calibration['dry_value']}, Húmedo={self.calibration['wet_value']}"
        )
        print("⏰ Tiempo\t💧 Humedad%\t📊 Nivel\t\t🎯 Acción")
        print("-" * 65)

        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)

        readings_history = []

        try:
            while time.time() < end_time:
                data = self.get_complete_reading()

                if data["status"] == "success":
                    elapsed = (time.time() - start_time) / 60  # en minutos

                    print(
                        f"{elapsed:5.1f}m\t\t{data['humidity_percentage']:5.1f}%\t\t"
                        f"{data['moisture_level']:10s}\t{data['irrigation_recommendation']}"
                    )

                    readings_history.append(data)

                    # Alerta si cambio significativo
                    if len(readings_history) >= 2:
                        prev_humidity = readings_history[-2]["humidity_percentage"]
                        curr_humidity = data["humidity_percentage"]

                        if prev_humidity and curr_humidity:
                            change = abs(curr_humidity - prev_humidity)
                            if change > 10:  # Cambio > 10%
                                print(
                                    f"  ⚠️  Cambio significativo: {change:.1f}% en {interval_seconds}s"
                                )

                else:
                    print(f"❌ Error: {data['error']}")

                time.sleep(interval_seconds)

        except KeyboardInterrupt:
            print("\n⏹️  Monitoreo detenido por usuario")

        # Resumen final
        if readings_history:
            valid_readings = [
                r["humidity_percentage"]
                for r in readings_history
                if r["humidity_percentage"] is not None
            ]

            if valid_readings:
                avg_humidity = sum(valid_readings) / len(valid_readings)
                min_humidity = min(valid_readings)
                max_humidity = max(valid_readings)

                print(f"\n📈 RESUMEN DEL MONITOREO:")
                print(f"🔸 Humedad promedio: {avg_humidity:.1f}%")
                print(f"🔸 Rango: {min_humidity:.1f}% - {max_humidity:.1f}%")
                print(f"🔸 Variación: {max_humidity - min_humidity:.1f}%")
                print(
                    f"🔸 Lecturas válidas: {len(valid_readings)}/{len(readings_history)}"
                )

    def quick_soil_check(self):
        """
        Verificación rápida del estado del suelo

        Returns:
            str: Reporte rápido del estado
        """
        data = self.get_complete_reading()

        if data["status"] == "success":
            report = f"""
🌱 ESTADO ACTUAL DEL SUELO:
{data['emoji']} Humedad: {data['humidity_percentage']}%
📊 Nivel: {data['description']}
🎯 Recomendación: {data['irrigation_recommendation'].replace('_', ' ')}
📡 Digital: {'Húmedo' if data['digital_state'] else 'Seco'}
🔧 Valor crudo: {data['raw_value']}
            """
            return report.strip()
        else:
            return f"❌ Error leyendo sensor: {data['error']}"


def irrigation_decision_system(sensor, humidity_threshold=40):
    """
    Sistema de decisión para riego automático

    Args:
        sensor: Instancia del sensor calibrado
        humidity_threshold: Umbral mínimo de humedad

    Returns:
        dict: Decisión de riego con justificación
    """
    data = sensor.get_complete_reading()

    if data["status"] != "success":
        return {
            "should_irrigate": False,
            "reason": f"Error sensor: {data['error']}",
            "confidence": 0,
        }

    humidity = data["humidity_percentage"]

    # Lógica de decisión
    if humidity >= 90:
        decision = {
            "should_irrigate": False,
            "reason": f"Suelo saturado ({humidity}%). Esperar drenaje.",
            "confidence": 95,
        }
    elif humidity >= humidity_threshold:
        decision = {
            "should_irrigate": False,
            "reason": f"Humedad adecuada ({humidity}% >= {humidity_threshold}%).",
            "confidence": 85,
        }
    elif humidity >= 20:
        decision = {
            "should_irrigate": True,
            "reason": f"Humedad baja ({humidity}%). Riego recomendado.",
            "confidence": 80,
        }
    else:
        decision = {
            "should_irrigate": True,
            "reason": f"Humedad crítica ({humidity}%). Riego urgente.",
            "confidence": 95,
        }

    # Agregar información adicional
    decision.update(
        {
            "current_humidity": humidity,
            "threshold": humidity_threshold,
            "sensor_data": data,
        }
    )

    return decision


def main():
    """
    Función principal de demostración
    """
    try:
        # Inicializar sensor calibrado
        sensor = HW080FinalCalibrated()

        print("\n🚀 SENSOR HW-080 CALIBRADO LISTO")
        print("¿Qué quieres hacer?")
        print("1. 🔍 Verificación rápida")
        print("2. 📊 Monitoreo inteligente")
        print("3. 🚿 Sistema de decisión de riego")
        print("4. 📈 Lecturas continuas simples")

        option = input("\nSelecciona (1-4): ").strip()

        if option == "1":
            print(sensor.quick_soil_check())

        elif option == "2":
            duration = int(input("Duración en minutos (por defecto 5): ") or "5")
            sensor.monitor_smart(duration_minutes=duration)

        elif option == "3":
            threshold = int(input("Umbral de humedad % (por defecto 40): ") or "40")

            for i in range(3):
                print(f"\n--- DECISIÓN {i+1} ---")
                decision = irrigation_decision_system(sensor, threshold)

                print(f"🚿 Regar: {'SÍ' if decision['should_irrigate'] else 'NO'}")
                print(f"📝 Razón: {decision['reason']}")
                print(f"🎯 Confianza: {decision['confidence']}%")

                if i < 2:
                    input("Presiona ENTER para otra decisión...")

        elif option == "4":
            print("\n📈 Lecturas cada 3 segundos (Ctrl+C para parar)")
            while True:
                data = sensor.get_complete_reading()
                if data["status"] == "success":
                    print(
                        f"💧 {data['humidity_percentage']:5.1f}% | "
                        f"{data['description']} | "
                        f"Crudo: {data['raw_value']}"
                    )
                time.sleep(3)

    except KeyboardInterrupt:
        print("\n👋 ¡Hasta luego!")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
