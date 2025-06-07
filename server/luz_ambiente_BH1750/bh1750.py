"""
Sistema completo de monitoreo de intensidad luminosa con sensor BH1750 (GY-30)
Para uso en huerta inteligente - medición y análisis de luz solar
"""

from machine import Pin, I2C
import time
import json
import gc
import math


class BH1750LightSensor:
    """
    Sensor BH1750 completo para monitoreo de intensidad luminosa en huerta
    """

    def __init__(self, sda_pin=0, scl_pin=1, addr=0x23, enable_auto_mode=True):
        """
        Inicializa el sensor BH1750 con configuración completa

        Args:
            sda_pin (int): Pin SDA para I2C
            scl_pin (int): Pin SCL para I2C
            addr (int): Dirección I2C del sensor (0x23 o 0x5C)
            enable_auto_mode (bool): Habilitar modo automático de resolución
        """
        try:
            self.sda_pin = sda_pin
            self.scl_pin = scl_pin
            self.addr = addr

            # Inicializar I2C
            self.i2c = I2C(0, sda=Pin(sda_pin), scl=Pin(scl_pin), freq=100000)

            # Comandos del BH1750
            self.commands = {
                "power_on": 0x01,
                "reset": 0x07,
                "continuous_high_res": 0x10,  # 1 lx resolución
                "continuous_high_res2": 0x11,  # 0.5 lx resolución
                "continuous_low_res": 0x13,  # 4 lx resolución
                "one_time_high_res": 0x20,  # Una medición 1 lx
                "one_time_high_res2": 0x21,  # Una medición 0.5 lx
                "one_time_low_res": 0x23,  # Una medición 4 lx
            }

            # Configuración del sensor
            self.config = {
                "reading_interval_min": 1.0,  # Intervalo mínimo entre lecturas
                "max_retry_attempts": 3,  # Intentos máximos por lectura
                "error_threshold": 0.15,  # 15% de errores máximo aceptable
                "enable_auto_mode": enable_auto_mode,
                "auto_mode_thresholds": {  # Umbrales para cambio automático de modo
                    "low_to_high": 1000,  # lux - cambiar a alta resolución
                    "high_to_low": 50000,  # lux - cambiar a baja resolución
                },
                "measurement_delay": {  # Tiempos de espera por modo (ms)
                    "high_res": 180,
                    "high_res2": 180,
                    "low_res": 24,
                },
            }

            # Estado actual del sensor
            self.current_mode = "continuous_high_res"
            self.last_measurement_time = 0

            # Estadísticas de funcionamiento
            self.stats = {
                "total_readings": 0,
                "successful_readings": 0,
                "failed_readings": 0,
                "mode_switches": 0,
                "uptime_start": time.time(),
                "last_error": None,
            }

            # Verificar conexión e inicializar
            if self.initialize_sensor():
                print(f"💡 BH1750 inicializado correctamente")
                print(
                    f"📍 I2C: SDA=GPIO{sda_pin}, SCL=GPIO{scl_pin}, Addr=0x{addr:02X}"
                )
                print(
                    f"⚙️  Modo automático: {'HABILITADO' if enable_auto_mode else 'DESHABILITADO'}"
                )
            else:
                raise Exception("Fallo en inicialización del sensor")

        except Exception as e:
            print(f"❌ Error inicializando BH1750: {e}")
            raise

    def initialize_sensor(self):
        """
        Inicializa el sensor con la secuencia correcta

        Returns:
            bool: True si la inicialización fue exitosa
        """
        try:
            # Verificar presencia en bus I2C
            devices = self.i2c.scan()
            if self.addr not in devices:
                print(f"❌ Sensor no encontrado en dirección 0x{self.addr:02X}")
                print(f"💡 Dispositivos I2C encontrados: {[hex(d) for d in devices]}")
                return False

            # Secuencia de inicialización
            self.i2c.writeto(self.addr, bytes([self.commands["power_on"]]))
            time.sleep_ms(10)

            self.i2c.writeto(self.addr, bytes([self.commands["reset"]]))
            time.sleep_ms(10)

            # Configurar modo inicial
            self.set_measurement_mode(self.current_mode)

            return True

        except Exception as e:
            print(f"❌ Error en inicialización: {e}")
            return False

    def set_measurement_mode(self, mode):
        """
        Configura el modo de medición del sensor

        Args:
            mode (str): Modo de medición

        Returns:
            bool: True si el cambio fue exitoso
        """
        try:
            if mode not in self.commands:
                print(f"❌ Modo inválido: {mode}")
                return False

            # Enviar comando de modo
            cmd = self.commands[mode]
            self.i2c.writeto(self.addr, bytes([cmd]))

            # Esperar tiempo apropiado según el modo
            if "high_res" in mode:
                time.sleep_ms(self.config["measurement_delay"]["high_res"])
            elif "low_res" in mode:
                time.sleep_ms(self.config["measurement_delay"]["low_res"])

            old_mode = self.current_mode
            self.current_mode = mode

            if old_mode != mode:
                self.stats["mode_switches"] += 1

            return True

        except Exception as e:
            print(f"❌ Error cambiando modo: {e}")
            return False

    def read_raw_light(self):
        """
        Lee los valores crudos del sensor con reintentos

        Returns:
            dict: Resultado de la lectura cruda
        """
        self.stats["total_readings"] += 1

        # Verificar intervalo mínimo
        current_time = time.time()
        if (current_time - self.last_measurement_time) < self.config[
            "reading_interval_min"
        ]:
            time.sleep(self.config["reading_interval_min"])

        # Intentar lectura con reintentos
        for attempt in range(self.config["max_retry_attempts"]):
            try:
                gc.collect()  # Limpiar memoria

                # Leer 2 bytes del sensor
                data = self.i2c.readfrom(self.addr, 2)

                # Convertir datos a valor crudo y lux
                raw_value = (data[0] << 8) | data[1]
                lux_value = raw_value / 1.2  # Fórmula estándar BH1750

                # Validar rango físico del sensor (0-65535 lux aproximadamente)
                if 0 <= lux_value <= 100000:  # Rango extendido para casos extremos
                    self.stats["successful_readings"] += 1
                    self.last_measurement_time = current_time

                    return {
                        "success": True,
                        "lux_raw": lux_value,
                        "raw_value": raw_value,
                        "mode": self.current_mode,
                        "attempt": attempt + 1,
                        "timestamp": current_time,
                        "error": None,
                    }
                else:
                    raise ValueError(f"Valor fuera de rango: {lux_value} lux")

            except OSError as e:
                error_msg = f"Error comunicación I2C (intento {attempt + 1}): {e}"
                if attempt == self.config["max_retry_attempts"] - 1:
                    break
                time.sleep(0.2)

            except Exception as e:
                error_msg = f"Error general (intento {attempt + 1}): {e}"
                if attempt == self.config["max_retry_attempts"] - 1:
                    break
                time.sleep(0.2)

        # Si llegamos aquí, todos los intentos fallaron
        self.stats["failed_readings"] += 1
        self.stats["last_error"] = error_msg

        return {
            "success": False,
            "lux_raw": None,
            "raw_value": None,
            "mode": self.current_mode,
            "attempt": self.config["max_retry_attempts"],
            "timestamp": current_time,
            "error": error_msg,
        }

    def get_optimized_reading(self):
        """
        Obtiene lectura optimizada con modo automático si está habilitado

        Returns:
            dict: Lectura optimizada con análisis de luz
        """
        raw_reading = self.read_raw_light()

        if not raw_reading["success"]:
            return {
                "success": False,
                "error": raw_reading["error"],
                "timestamp": raw_reading["timestamp"],
            }

        lux = raw_reading["lux_raw"]

        # Modo automático: ajustar resolución según intensidad
        if self.config["enable_auto_mode"]:
            optimal_mode = self.determine_optimal_mode(lux)
            if optimal_mode != self.current_mode:
                if self.set_measurement_mode(optimal_mode):
                    # Tomar nueva lectura con el modo optimizado
                    time.sleep(0.5)  # Pequeña pausa para estabilización
                    raw_reading = self.read_raw_light()
                    if raw_reading["success"]:
                        lux = raw_reading["lux_raw"]

        # Clasificar tipo de luz
        light_classification = self.classify_light_intensity(lux)

        # Evaluar condiciones para plantas
        plant_analysis = self.analyze_plant_light_conditions(lux)

        # Calcular métricas adicionales
        light_metrics = self.calculate_light_metrics(lux)

        return {
            "success": True,
            "timestamp": raw_reading["timestamp"],
            "lux": round(lux, 1),
            "raw_value": raw_reading["raw_value"],
            "classification": light_classification,
            "plant_analysis": plant_analysis,
            "metrics": light_metrics,
            "sensor_info": {
                "mode_used": raw_reading["mode"],
                "attempt_used": raw_reading["attempt"],
                "auto_mode_enabled": self.config["enable_auto_mode"],
            },
        }

    def determine_optimal_mode(self, lux):
        """
        Determina el modo óptimo según la intensidad de luz

        Args:
            lux (float): Intensidad luminosa actual

        Returns:
            str: Modo óptimo recomendado
        """
        thresholds = self.config["auto_mode_thresholds"]

        if lux < 10:
            # Muy baja luz - usar máxima resolución
            return "continuous_high_res2"
        elif lux < thresholds["low_to_high"]:
            # Luz baja a media - usar alta resolución
            return "continuous_high_res"
        elif lux < thresholds["high_to_low"]:
            # Luz media a alta - mantener alta resolución
            return "continuous_high_res"
        else:
            # Luz muy alta - usar baja resolución para evitar saturación
            return "continuous_low_res"

    def classify_light_intensity(self, lux):
        """
        Clasifica la intensidad de luz en categorías descriptivas

        Args:
            lux (float): Intensidad luminosa en lux

        Returns:
            dict: Clasificación de la luz
        """
        classifications = [
            (0, 1, "OSCURIDAD_TOTAL", "Noche sin luna", "🌑"),
            (1, 10, "MUY_OSCURO", "Noche con luna o interior muy tenue", "🌒"),
            (10, 50, "OSCURO", "Interior con luz tenue", "🌓"),
            (50, 200, "INTERIOR_NORMAL", "Habitación bien iluminada", "🏠"),
            (200, 500, "INTERIOR_BRILLANTE", "Oficina o cocina", "🏢"),
            (500, 1000, "TRANSICIÓN", "Cerca de ventana o entrada", "🚪"),
            (1000, 5000, "EXTERIOR_SOMBRA", "Sombra en día nublado", "☁️"),
            (5000, 10000, "EXTERIOR_NUBLADO", "Día nublado", "🌤️"),
            (10000, 25000, "EXTERIOR_PARCIAL", "Día parcialmente soleado", "⛅"),
            (25000, 50000, "EXTERIOR_SOLEADO", "Día soleado", "☀️"),
            (50000, 100000, "SOL_DIRECTO", "Sol directo", "🌞"),
            (100000, float("inf"), "EXTREMO", "Luz artificial intensa o reflejo", "🔆"),
        ]

        for min_lux, max_lux, category, description, emoji in classifications:
            if min_lux <= lux < max_lux:
                return {
                    "category": category,
                    "description": description,
                    "emoji": emoji,
                    "range": f"{min_lux}-{max_lux if max_lux != float('inf') else '∞'} lux",
                }

        return {
            "category": "UNKNOWN",
            "description": "Valor fuera de rangos conocidos",
            "emoji": "❓",
            "range": "N/A",
        }

    def analyze_plant_light_conditions(self, lux):
        """
        Analiza las condiciones de luz para el crecimiento de plantas

        Args:
            lux (float): Intensidad luminosa en lux

        Returns:
            dict: Análisis de condiciones para plantas
        """
        analysis = {
            "suitability": "UNKNOWN",
            "growth_stage_recommendations": [],
            "plant_type_recommendations": [],
            "action_needed": [],
            "photoperiod_analysis": {},
            "energy_level": "UNKNOWN",
        }

        # Evaluar niveles de luz para fotosíntesis
        if lux < 100:
            analysis["suitability"] = "INSUFICIENTE"
            analysis["energy_level"] = "MUY_BAJO"
            analysis["action_needed"].append("💡 Agregar iluminación artificial")
            analysis["plant_type_recommendations"].append(
                "Solo plantas tolerantes a sombra extrema"
            )
        elif lux < 500:
            analysis["suitability"] = "MINIMA"
            analysis["energy_level"] = "BAJO"
            analysis["action_needed"].append("💡 Considerar luz suplementaria")
            analysis["plant_type_recommendations"].extend(
                ["Plantas de sombra", "Helechos", "Algunas hierbas"]
            )
        elif lux < 1000:
            analysis["suitability"] = "LIMITADA"
            analysis["energy_level"] = "BAJO_MEDIO"
            analysis["plant_type_recommendations"].extend(
                ["Lechugas", "Espinacas", "Plantas de hoja"]
            )
            analysis["growth_stage_recommendations"].append("Germinación y plántulas")
        elif lux < 5000:
            analysis["suitability"] = "MODERADA"
            analysis["energy_level"] = "MEDIO"
            analysis["plant_type_recommendations"].extend(
                ["Hierbas aromáticas", "Vegetales de hoja", "Plantas de interior"]
            )
            analysis["growth_stage_recommendations"].append(
                "Crecimiento vegetativo lento"
            )
        elif lux < 15000:
            analysis["suitability"] = "BUENA"
            analysis["energy_level"] = "MEDIO_ALTO"
            analysis["plant_type_recommendations"].extend(
                ["Mayoría de vegetales", "Hierbas", "Plantas ornamentales"]
            )
            analysis["growth_stage_recommendations"].extend(
                ["Crecimiento vegetativo", "Desarrollo de hojas"]
            )
        elif lux < 30000:
            analysis["suitability"] = "EXCELENTE"
            analysis["energy_level"] = "ALTO"
            analysis["plant_type_recommendations"].extend(
                ["Tomates", "Pimientos", "Plantas fructíferas"]
            )
            analysis["growth_stage_recommendations"].extend(
                ["Floración", "Fructificación"]
            )
        elif lux < 60000:
            analysis["suitability"] = "OPTIMA"
            analysis["energy_level"] = "MUY_ALTO"
            analysis["plant_type_recommendations"].extend(
                ["Plantas de sol pleno", "Cultivos de temporada"]
            )
            analysis["growth_stage_recommendations"].append(
                "Máximo rendimiento fotosintético"
            )
        else:
            analysis["suitability"] = "EXCESIVA"
            analysis["energy_level"] = "EXTREMO"
            analysis["action_needed"].extend(
                ["☂️ Proporcionar sombra", "💧 Aumentar riego"]
            )
            analysis["plant_type_recommendations"].append(
                "Solo plantas muy resistentes al sol"
            )

        # Análisis de fotoperiodo (necesita historial para ser preciso)
        if lux > 1000:
            analysis["photoperiod_analysis"] = {
                "daylight_detected": True,
                "suitable_for_flowering": lux > 10000,
                "light_stress_risk": lux > 80000,
            }
        else:
            analysis["photoperiod_analysis"] = {
                "daylight_detected": False,
                "night_period": True,
                "artificial_light_needed": lux < 100,
            }

        return analysis

    def calculate_light_metrics(self, lux):
        """
        Calcula métricas adicionales de luz

        Args:
            lux (float): Intensidad luminosa en lux

        Returns:
            dict: Métricas calculadas
        """
        metrics = {}

        # Conversión a otras unidades
        metrics["footcandles"] = lux * 0.0929  # Conversión aproximada
        metrics["watts_per_m2"] = lux * 0.0079  # Conversión aproximada para luz solar

        # Estimación de eficiencia fotosintética
        if lux <= 0:
            metrics["photosynthetic_efficiency"] = 0
        elif lux < 1000:
            metrics["photosynthetic_efficiency"] = (lux / 1000) * 20  # 0-20%
        elif lux < 30000:
            metrics["photosynthetic_efficiency"] = (
                20 + ((lux - 1000) / 29000) * 60
            )  # 20-80%
        else:
            metrics["photosynthetic_efficiency"] = min(
                95, 80 + ((lux - 30000) / 20000) * 15
            )  # 80-95%

        # Categoría de actividad fotosintética
        if metrics["photosynthetic_efficiency"] < 10:
            metrics["photosynthetic_category"] = "INACTIVA"
        elif metrics["photosynthetic_efficiency"] < 30:
            metrics["photosynthetic_category"] = "BAJA"
        elif metrics["photosynthetic_efficiency"] < 60:
            metrics["photosynthetic_category"] = "MODERADA"
        elif metrics["photosynthetic_efficiency"] < 80:
            metrics["photosynthetic_category"] = "ALTA"
        else:
            metrics["photosynthetic_category"] = "ÓPTIMA"

        return metrics

    def get_light_status(self):
        """
        Obtiene estado completo de iluminación con análisis

        Returns:
            dict: Estado completo de la luz
        """
        reading = self.get_optimized_reading()

        if not reading["success"]:
            return {
                "status": "ERROR",
                "error": reading["error"],
                "timestamp": reading["timestamp"],
            }

        # Calcular estadísticas de funcionamiento
        success_rate = (
            self.stats["successful_readings"] / max(1, self.stats["total_readings"])
        ) * 100
        uptime = time.time() - self.stats["uptime_start"]

        return {
            "status": "SUCCESS",
            "timestamp": reading["timestamp"],
            "light_data": {
                "intensity_lux": reading["lux"],
                "classification": reading["classification"],
                "plant_analysis": reading["plant_analysis"],
                "metrics": reading["metrics"],
            },
            "sensor_health": {
                "success_rate": round(success_rate, 1),
                "total_readings": self.stats["total_readings"],
                "mode_switches": self.stats["mode_switches"],
                "uptime_hours": round(uptime / 3600, 1),
                "current_mode": self.current_mode,
                "status": (
                    "HEALTHY"
                    if success_rate >= 90
                    else "DEGRADED" if success_rate >= 70 else "CRITICAL"
                ),
            },
            "raw_data": {
                "raw_value": reading["raw_value"],
                "mode": reading["sensor_info"]["mode_used"],
            },
        }

    def monitor_light_cycle(self, duration_hours=24, interval_minutes=15):
        """
        Monitoreo del ciclo de luz durante un período extenso

        Args:
            duration_hours (int): Duración del monitoreo en horas
            interval_minutes (int): Intervalo entre mediciones en minutos
        """
        print(f"\n☀️ MONITOREO DE CICLO DE LUZ - {duration_hours} horas")
        print(
            f"📊 Intervalo: {interval_minutes} min | Modo: {'AUTO' if self.config['enable_auto_mode'] else 'MANUAL'}"
        )
        print("\n⏰ Hora\t\t💡 Lux\t\t🌱 Condición\t\t📊 Fotosíntesis")
        print("-" * 75)

        start_time = time.time()
        end_time = start_time + (duration_hours * 3600)
        interval_seconds = interval_minutes * 60

        light_history = []
        max_lux = 0
        min_lux = float("inf")

        try:
            while time.time() < end_time:
                current_time = time.time()
                elapsed_hours = (current_time - start_time) / 3600

                # Formatear hora actual
                time_tuple = time.localtime(current_time)
                time_str = f"{time_tuple[3]:02d}:{time_tuple[4]:02d}"

                status = self.get_light_status()

                if status["status"] == "SUCCESS":
                    light = status["light_data"]
                    lux = light["intensity_lux"]
                    classification = light["classification"]["category"]
                    plant_condition = light["plant_analysis"]["suitability"]
                    photosynthesis = light["metrics"]["photosynthetic_efficiency"]

                    # Actualizar extremos
                    max_lux = max(max_lux, lux)
                    if lux > 0:  # Ignorar 0 para el mínimo
                        min_lux = min(min_lux, lux)

                    # Mostrar línea de datos
                    print(
                        f"{time_str}\t\t{lux:8.1f}\t{plant_condition:12s}\t{photosynthesis:5.1f}%"
                    )

                    # Guardar para análisis
                    light_history.append(
                        {
                            "hour": elapsed_hours,
                            "time_str": time_str,
                            "lux": lux,
                            "classification": classification,
                            "plant_analysis": plant_condition,
                            "photosynthesis": photosynthesis,
                        }
                    )

                    # Alertas especiales
                    if lux > 80000:
                        print(f"      ⚠️  Luz extrema detectada - riesgo de estrés")
                    elif lux < 100 and 6 <= time_tuple[3] <= 18:  # Horas de día
                        print(f"      ⚠️  Luz insuficiente durante el día")

                else:
                    print(f"{time_str}\t\t❌ ERROR: {status['error'][:30]}...")

                time.sleep(interval_seconds)

        except KeyboardInterrupt:
            print("\n⏹️  Monitoreo detenido por usuario")

        # Generar análisis del ciclo
        self.analyze_light_cycle(light_history, max_lux, min_lux)

    def analyze_light_cycle(self, light_history, max_lux, min_lux):
        """
        Analiza el ciclo de luz registrado

        Args:
            light_history (list): Historial de mediciones
            max_lux (float): Intensidad máxima registrada
            min_lux (float): Intensidad mínima registrada
        """
        if not light_history:
            print("\n❌ No hay datos para analizar")
            return

        # Estadísticas básicas
        lux_values = [reading["lux"] for reading in light_history]
        avg_lux = sum(lux_values) / len(lux_values)

        # Detectar período de día y noche
        day_readings = [r for r in light_history if r["lux"] > 1000]
        night_readings = [r for r in light_history if r["lux"] <= 100]

        # Calcular horas de luz útil para plantas
        useful_light_hours = len([r for r in light_history if r["lux"] > 5000])
        optimal_light_hours = len(
            [r for r in light_history if 15000 <= r["lux"] <= 60000]
        )

        print(f"\n📈 ANÁLISIS DEL CICLO DE LUZ:")
        print(f"📊 Total de mediciones: {len(light_history)}")
        print(f"☀️ Intensidad promedio: {avg_lux:.1f} lux")
        print(f"🔆 Pico máximo: {max_lux:.1f} lux")
        print(f"🌑 Mínimo nocturno: {min_lux:.1f} lux")

        print(f"\n🌞 ANÁLISIS DE FOTOPERIODO:")
        print(f"🌅 Horas con luz diurna: {len(day_readings) * (15/60):.1f} horas")
        print(f"🌃 Horas nocturnas: {len(night_readings) * (15/60):.1f} horas")
        print(
            f"🌱 Horas de luz útil para plantas: {useful_light_hours * (15/60):.1f} horas"
        )
        print(f"⭐ Horas de luz óptima: {optimal_light_hours * (15/60):.1f} horas")

        # Recomendaciones
        print(f"\n💡 RECOMENDACIONES:")

        if useful_light_hours < 8:  # Menos de 2 horas de luz útil
            print("   • ⚠️  Período de luz insuficiente para la mayoría de plantas")
            print("   • 💡 Considerar iluminación artificial suplementaria")
        elif useful_light_hours < 24:  # Menos de 6 horas
            print(
                "   • 🟡 Luz limitada - adecuada solo para plantas tolerantes a sombra"
            )
            print("   • 🌿 Cultivar lechugas, espinacas o hierbas de sombra")
        else:
            print("   • ✅ Período de luz adecuado para cultivo")

        if max_lux > 80000:
            print("   • ☂️ Picos de luz muy intensos - considerar sombra parcial")

        if optimal_light_hours > 16:  # Más de 4 horas de luz óptima
            print("   • 🚀 Excelentes condiciones para plantas de sol pleno")
            print("   • 🍅 Ideal para tomates, pimientos y plantas fructíferas")

    def greenhouse_light_controller(self):
        """
        Sistema de control automático de iluminación para invernadero
        """
        print("\n🏠 CONTROLADOR AUTOMÁTICO DE ILUMINACIÓN")
        print("=" * 50)

        status = self.get_light_status()

        if status["status"] != "SUCCESS":
            print(f"❌ Error del sensor: {status['error']}")
            return

        light = status["light_data"]
        lux = light["intensity_lux"]
        plant_analysis = light["plant_analysis"]

        print(f"💡 Intensidad actual: {lux:.1f} lux")
        print(f"🌱 Condición para plantas: {plant_analysis['suitability']}")
        print(f"📊 Clasificación: {light['classification']['description']}")

        # Decisiones de control automático
        actions = []

        # Control de iluminación artificial
        if lux < 500:
            actions.append("💡 ACTIVAR luces LED de crecimiento (espectro completo)")
            actions.append("⏰ PROGRAMAR temporizador para fotoperiodo")
        elif lux < 1000:
            actions.append("💡 ACTIVAR luces suplementarias (bajo consumo)")
        elif lux > 80000:
            actions.append("☂️ DESPLEGAR pantalla de sombra")
            actions.append("🌬️ ACTIVAR ventilación extra")

        # Control de sombreado
        if 60000 <= lux <= 80000:
            actions.append("☂️ PREPARAR sombra parcial (50%)")
        elif lux > 100000:
            actions.append("🚨 SOMBRA URGENTE - Riesgo de daño por luz")

        # Recomendaciones de cultivo
        if plant_analysis["suitability"] in ["EXCELENTE", "OPTIMA"]:
            actions.append("🌱 CONDICIONES IDEALES - Maximizar plantación")
        elif plant_analysis["suitability"] == "INSUFICIENTE":
            actions.append("🚫 SUSPENDER siembra hasta mejorar iluminación")

        # Mostrar acciones
        if actions:
            print(f"\n🎯 ACCIONES RECOMENDADAS:")
            for action in actions:
                print(f"   • {action}")
        else:
            print(f"\n✅ CONDICIONES ÓPTIMAS - No se requieren acciones")

        # Mostrar recomendaciones específicas de plantas
        if plant_analysis["plant_type_recommendations"]:
            print(f"\n🌿 PLANTAS RECOMENDADAS PARA ESTAS CONDICIONES:")
            for plant in plant_analysis["plant_type_recommendations"]:
                print(f"   • {plant}")


def daily_light_summary(sensor, readings_per_hour=4):
    """
    Genera un resumen diario de condiciones de luz

    Args:
        sensor: Instancia del sensor BH1750
        readings_per_hour: Lecturas por hora para el análisis
    """
    print("\n📊 RESUMEN DIARIO DE LUZ")
    print("=" * 40)

    # Simular lecturas durante diferentes horas del día
    hours_to_test = [6, 9, 12, 15, 18, 21]  # Representativo del día
    daily_data = []

    for hour in hours_to_test:
        print(f"\n🕐 Simulando hora {hour:02d}:00")
        status = sensor.get_light_status()

        if status["status"] == "SUCCESS":
            light_data = status["light_data"]
            daily_data.append(
                {
                    "hour": hour,
                    "lux": light_data["intensity_lux"],
                    "suitability": light_data["plant_analysis"]["suitability"],
                    "photosynthesis": light_data["metrics"][
                        "photosynthetic_efficiency"
                    ],
                }
            )

            print(f"   💡 {light_data['intensity_lux']:.1f} lux")
            print(f"   🌱 {light_data['plant_analysis']['suitability']}")

        time.sleep(2)  # Breve pausa entre lecturas

    # Análisis del día
    if daily_data:
        avg_lux = sum(d["lux"] for d in daily_data) / len(daily_data)
        max_lux = max(d["lux"] for d in daily_data)

        good_hours = len([d for d in daily_data if d["lux"] > 5000])
        optimal_hours = len([d for d in daily_data if 15000 <= d["lux"] <= 60000])

        print(f"\n📈 RESUMEN DEL DÍA:")
        print(f"☀️ Promedio de luz: {avg_lux:.1f} lux")
        print(f"🔆 Pico de luz: {max_lux:.1f} lux")
        print(f"⏰ Horas de buena luz: {good_hours}/{len(daily_data)}")
        print(f"⭐ Horas de luz óptima: {optimal_hours}/{len(daily_data)}")

        # Recomendación general
        if avg_lux > 20000:
            print("🚀 DÍA EXCELENTE para cultivo solar")
        elif avg_lux > 10000:
            print("✅ BUEN DÍA para la mayoría de plantas")
        elif avg_lux > 5000:
            print("🟡 DÍA REGULAR - plantas tolerantes a sombra")
        else:
            print("🔴 DÍA PROBLEMÁTICO - iluminación insuficiente")


def main():
    """
    Función principal de demostración
    """
    try:
        # Configuración inicial
        print("🔧 CONFIGURACIÓN DEL SENSOR BH1750:")

        sda_input = input("Pin SDA (por defecto 0): ").strip()
        sda_pin = int(sda_input) if sda_input else 0

        scl_input = input("Pin SCL (por defecto 1): ").strip()
        scl_pin = int(scl_input) if scl_input else 1

        addr_input = input("Dirección I2C hex (por defecto 0x23): ").strip()
        if addr_input.startswith("0x"):
            addr = int(addr_input, 16)
        elif addr_input:
            addr = int(addr_input)
        else:
            addr = 0x23

        auto_mode_input = input("¿Habilitar modo automático? (s/n): ").strip().lower()
        auto_mode = auto_mode_input.startswith("s")

        # Crear sensor
        sensor = BH1750LightSensor(
            sda_pin=sda_pin, scl_pin=scl_pin, addr=addr, enable_auto_mode=auto_mode
        )

        # Menú principal
        while True:
            print("\n" + "=" * 50)
            print("💡 SISTEMA DE MONITOREO DE LUZ BH1750")
            print("=" * 50)
            print("1. 📊 Estado de iluminación actual")
            print("2. 🔍 Monitoreo continuo corto")
            print("3. ☀️ Monitoreo de ciclo de luz (24h)")
            print("4. 🏠 Controlador de invernadero")
            print("5. 📈 Resumen diario simulado")
            print("6. 📊 Lecturas simples")
            print("7. ⚙️  Configuración del sensor")
            print("8. 📋 Estadísticas del sensor")
            print("9. 🚪 Salir")

            option = input("\nSelecciona (1-9): ").strip()

            if option == "1":
                status = sensor.get_light_status()
                if status["status"] == "SUCCESS":
                    light = status["light_data"]
                    print(f"\n💡 Intensidad: {light['intensity_lux']} lux")
                    print(
                        f"🏷️  Clasificación: {light['classification']['description']} {light['classification']['emoji']}"
                    )
                    print(
                        f"🌱 Condiciones plantas: {light['plant_analysis']['suitability']}"
                    )
                    print(
                        f"📊 Eficiencia fotosintética: {light['metrics']['photosynthetic_efficiency']:.1f}%"
                    )

                    if light["plant_analysis"]["action_needed"]:
                        print("\n💡 Acciones recomendadas:")
                        for action in light["plant_analysis"]["action_needed"]:
                            print(f"   • {action}")
                else:
                    print(f"❌ Error: {status['error']}")

            elif option == "2":
                duration = int(input("Duración en minutos (10): ") or "10")
                sensor.monitor_light_cycle(
                    duration_hours=duration / 60, interval_minutes=1
                )

            elif option == "3":
                hours = int(input("Duración en horas (24): ") or "24")
                interval = int(input("Intervalo en minutos (15): ") or "15")
                sensor.monitor_light_cycle(
                    duration_hours=hours, interval_minutes=interval
                )

            elif option == "4":
                sensor.greenhouse_light_controller()

            elif option == "5":
                daily_light_summary(sensor)

            elif option == "6":
                print("\n📊 Lecturas cada 2s (Ctrl+C para parar)")
                try:
                    while True:
                        reading = sensor.get_optimized_reading()
                        if reading["success"]:
                            print(
                                f"💡 {reading['lux']:8.1f} lux | "
                                f"{reading['classification']['emoji']} {reading['classification']['category']} | "
                                f"🌱 {reading['plant_analysis']['suitability']}"
                            )
                        else:
                            print(f"❌ {reading['error']}")
                        time.sleep(2)
                except KeyboardInterrupt:
                    print("\n⏹️  Lecturas detenidas")

            elif option == "7":
                print(f"\n⚙️  CONFIGURACIÓN ACTUAL:")
                print(f"📍 I2C: SDA=GPIO{sensor.sda_pin}, SCL=GPIO{sensor.scl_pin}")
                print(f"📡 Dirección: 0x{sensor.addr:02X}")
                print(
                    f"🔄 Modo automático: {'HABILITADO' if sensor.config['enable_auto_mode'] else 'DESHABILITADO'}"
                )
                print(f"⚙️  Modo actual: {sensor.current_mode}")

            elif option == "8":
                stats = sensor.stats
                success_rate = (
                    stats["successful_readings"] / max(1, stats["total_readings"])
                ) * 100
                uptime = time.time() - stats["uptime_start"]

                print(f"\n📊 ESTADÍSTICAS DEL SENSOR:")
                print(f"📈 Tasa de éxito: {success_rate:.1f}%")
                print(f"📊 Lecturas totales: {stats['total_readings']}")
                print(f"⚙️  Cambios de modo: {stats['mode_switches']}")
                print(f"⏱️  Tiempo funcionando: {uptime/3600:.1f} horas")
                if stats["last_error"]:
                    print(f"❌ Último error: {stats['last_error']}")

            elif option == "9":
                print("👋 ¡Hasta luego!")
                break

            else:
                print("❌ Opción no válida")

    except KeyboardInterrupt:
        print("\n👋 ¡Hasta luego!")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
