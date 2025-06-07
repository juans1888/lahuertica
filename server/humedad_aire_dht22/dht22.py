"""
Sistema completo de monitoreo ambiental con sensor DHT22
Para uso en huerta inteligente - temperatura y humedad ambiental
"""

import dht
from machine import Pin
import time
import json
import gc
import math

class DHT22EnvironmentalSensor:
    """
    Sensor DHT22 completo para monitoreo ambiental de huerta
    """
    
    def __init__(self, data_pin=15, enable_offset_compensation=False):
        """
        Inicializa el sensor DHT22 con configuración completa
        
        Args:
            data_pin (int): Pin de datos del sensor
            enable_offset_compensation (bool): Habilitar compensación de offset
        """
        try:
            self.pin = Pin(data_pin, Pin.IN, Pin.PULL_UP)
            self.sensor = dht.DHT22(self.pin)
            self.data_pin = data_pin
            
            # Configuración del sensor
            self.config = {
                'reading_interval_min': 2.0,    # Intervalo mínimo entre lecturas
                'max_retry_attempts': 3,        # Intentos máximos por lectura
                'error_threshold': 0.2,         # 20% de errores máximo aceptable
                'enable_offset_compensation': enable_offset_compensation
            }
            
            # Compensación de offset (configurar después de validación)
            self.offset_compensation = {
                'temperature_offset': 0.0,  # °C a restar de la lectura
                'humidity_offset': 0.0,     # % a restar de la lectura
                'last_calibration': None
            }
            
            # Estadísticas de funcionamiento
            self.stats = {
                'total_readings': 0,
                'successful_readings': 0,
                'failed_readings': 0,
                'last_reading_time': 0,
                'uptime_start': time.time()
            }
            
            # Cargar configuración si existe
            self.load_configuration()
            
            print(f"🌡️  DHT22 inicializado en GPIO{data_pin}")
            print(f"🔧 Compensación offset: {'HABILITADA' if enable_offset_compensation else 'DESHABILITADA'}")
            
        except Exception as e:
            print(f"❌ Error inicializando DHT22: {e}")
            raise

    def load_configuration(self, filename="dht22_config.json"):
        """
        Carga configuración guardada desde archivo
        
        Args:
            filename (str): Archivo de configuración
        """
        try:
            with open(filename, 'r') as f:
                config_data = json.load(f)
            
            if 'offset_compensation' in config_data:
                self.offset_compensation.update(config_data['offset_compensation'])
                print(f"✅ Configuración cargada desde {filename}")
                
                if (self.offset_compensation['temperature_offset'] != 0 or 
                    self.offset_compensation['humidity_offset'] != 0):
                    print(f"🎯 Offset cargado: T={self.offset_compensation['temperature_offset']:+.1f}°C, "
                          f"H={self.offset_compensation['humidity_offset']:+.1f}%")
                          
        except Exception:
            print("⚠️  Sin configuración previa - usando valores por defecto")

    def save_configuration(self, filename="dht22_config.json"):
        """
        Guarda la configuración actual
        
        Args:
            filename (str): Archivo donde guardar
        """
        config_data = {
            'config': self.config,
            'offset_compensation': self.offset_compensation,
            'stats': self.stats,
            'timestamp': time.time()
        }
        
        try:
            with open(filename, 'w') as f:
                json.dump(config_data, f)
            print(f"✅ Configuración guardada en {filename}")
        except Exception as e:
            print(f"❌ Error guardando configuración: {e}")

    def set_offset_compensation(self, temperature_offset=0.0, humidity_offset=0.0):
        """
        Configura compensación de offset
        
        Args:
            temperature_offset (float): Offset de temperatura en °C
            humidity_offset (float): Offset de humedad en %
        """
        self.offset_compensation['temperature_offset'] = temperature_offset
        self.offset_compensation['humidity_offset'] = humidity_offset
        self.offset_compensation['last_calibration'] = time.time()
        
        print(f"🎯 Offset configurado: T={temperature_offset:+.1f}°C, H={humidity_offset:+.1f}%")

    def read_sensor_raw(self):
        """
        Lee valores crudos del sensor con reintentos
        
        Returns:
            dict: Resultado de la lectura cruda
        """
        self.stats['total_readings'] += 1
        
        # Verificar intervalo mínimo
        current_time = time.time()
        if (current_time - self.stats['last_reading_time']) < self.config['reading_interval_min']:
            time.sleep(self.config['reading_interval_min'])
        
        # Intentar lectura con reintentos
        for attempt in range(self.config['max_retry_attempts']):
            try:
                gc.collect()  # Limpiar memoria
                
                self.sensor.measure()
                
                temperature = self.sensor.temperature()
                humidity = self.sensor.humidity()
                
                # Validar rangos físicos del sensor
                if (-40 <= temperature <= 80) and (0 <= humidity <= 100):
                    self.stats['successful_readings'] += 1
                    self.stats['last_reading_time'] = current_time
                    
                    return {
                        'success': True,
                        'temperature_raw': temperature,
                        'humidity_raw': humidity,
                        'attempt': attempt + 1,
                        'timestamp': current_time,
                        'error': None
                    }
                else:
                    raise ValueError(f"Valores fuera de rango: T={temperature}, H={humidity}")
                    
            except OSError as e:
                error_msg = f"Error comunicación (intento {attempt + 1}): {e}"
                if attempt == self.config['max_retry_attempts'] - 1:
                    break
                time.sleep(0.5)  # Esperar antes de reintentar
                
            except Exception as e:
                error_msg = f"Error general (intento {attempt + 1}): {e}"
                if attempt == self.config['max_retry_attempts'] - 1:
                    break
                time.sleep(0.5)
        
        # Si llegamos aquí, todos los intentos fallaron
        self.stats['failed_readings'] += 1
        
        return {
            'success': False,
            'temperature_raw': None,
            'humidity_raw': None,
            'attempt': self.config['max_retry_attempts'],
            'timestamp': current_time,
            'error': error_msg
        }

    def get_compensated_reading(self):
        """
        Obtiene lectura con compensación de offset aplicada
        
        Returns:
            dict: Lectura compensada con interpretación
        """
        raw_reading = self.read_sensor_raw()
        
        if not raw_reading['success']:
            return {
                'success': False,
                'error': raw_reading['error'],
                'timestamp': raw_reading['timestamp']
            }
        
        # Aplicar compensación de offset si está habilitada
        if self.config['enable_offset_compensation']:
            temperature = raw_reading['temperature_raw'] - self.offset_compensation['temperature_offset']
            humidity = raw_reading['humidity_raw'] - self.offset_compensation['humidity_offset']
        else:
            temperature = raw_reading['temperature_raw']
            humidity = raw_reading['humidity_raw']
        
        # Limitar humedad a rango válido después de compensación
        humidity = max(0, min(100, humidity))
        
        # Calcular punto de rocío
        dew_point = self.calculate_dew_point(temperature, humidity)
        
        # Calcular índice de calor (sensación térmica)
        heat_index = self.calculate_heat_index(temperature, humidity)
        
        # Determinar condiciones para plantas
        plant_conditions = self.evaluate_plant_conditions(temperature, humidity)
        
        return {
            'success': True,
            'timestamp': raw_reading['timestamp'],
            'temperature': round(temperature, 1),
            'humidity': round(humidity, 1),
            'dew_point': round(dew_point, 1),
            'heat_index': round(heat_index, 1),
            'plant_conditions': plant_conditions,
            'raw_values': {
                'temperature_raw': raw_reading['temperature_raw'],
                'humidity_raw': raw_reading['humidity_raw']
            },
            'sensor_info': {
                'attempt_used': raw_reading['attempt'],
                'offset_applied': self.config['enable_offset_compensation'],
                'compensation': self.offset_compensation if self.config['enable_offset_compensation'] else None
            }
        }

    def calculate_dew_point(self, temperature, humidity):
        """
        Calcula el punto de rocío usando la fórmula de Magnus
        
        Args:
            temperature (float): Temperatura en °C
            humidity (float): Humedad relativa en %
            
        Returns:
            float: Punto de rocío en °C
        """
        try:
            if humidity <= 0:
                return float('-inf')
            
            # Constantes de Magnus
            a = 17.27
            b = 237.7
            
            # Calcular punto de rocío
            alpha = ((a * temperature) / (b + temperature)) + math.log(humidity / 100.0)
            dew_point = (b * alpha) / (a - alpha)
            
            return dew_point
            
        except Exception:
            return None

    def calculate_heat_index(self, temperature, humidity):
        """
        Calcula el índice de calor (sensación térmica)
        
        Args:
            temperature (float): Temperatura en °C
            humidity (float): Humedad relativa en %
            
        Returns:
            float: Índice de calor en °C
        """
        try:
            # Convertir a Fahrenheit para cálculo
            temp_f = (temperature * 9/5) + 32
            
            if temp_f < 80:  # Menos de 26.7°C
                return temperature  # No aplica índice de calor
            
            # Fórmula simplificada del índice de calor
            hi_f = (
                -42.379 + 
                2.04901523 * temp_f + 
                10.14333127 * humidity - 
                0.22475541 * temp_f * humidity - 
                6.83783e-3 * temp_f**2 - 
                5.481717e-2 * humidity**2 + 
                1.22874e-3 * temp_f**2 * humidity + 
                8.5282e-4 * temp_f * humidity**2 - 
                1.99e-6 * temp_f**2 * humidity**2
            )
            
            # Convertir de vuelta a Celsius
            heat_index = (hi_f - 32) * 5/9
            
            return heat_index
            
        except Exception:
            return temperature  # Retornar temperatura original si falla

    def evaluate_plant_conditions(self, temperature, humidity):
        """
        Evalúa las condiciones ambientales para el crecimiento de plantas
        
        Args:
            temperature (float): Temperatura en °C
            humidity (float): Humedad relativa en %
            
        Returns:
            dict: Evaluación de condiciones para plantas
        """
        conditions = {
            'overall_rating': 'UNKNOWN',
            'temperature_status': 'UNKNOWN',
            'humidity_status': 'UNKNOWN',
            'recommendations': [],
            'alerts': [],
            'optimal_for': []
        }
        
        # Evaluar temperatura
        if temperature < 5:
            conditions['temperature_status'] = 'MUY_FRÍA'
            conditions['alerts'].append('🥶 Temperatura muy baja - riesgo de daño por frío')
            conditions['recommendations'].append('Proteger plantas del frío o usar calefacción')
        elif temperature < 15:
            conditions['temperature_status'] = 'FRÍA'
            conditions['recommendations'].append('Considerar protección para plantas sensibles')
            conditions['optimal_for'].append('Plantas de clima frío')
        elif temperature <= 25:
            conditions['temperature_status'] = 'ÓPTIMA'
            conditions['optimal_for'].extend(['Mayoría de vegetales', 'Hierbas aromáticas'])
        elif temperature <= 30:
            conditions['temperature_status'] = 'CÁLIDA'
            conditions['optimal_for'].extend(['Plantas tropicales', 'Tomates', 'Pimientos'])
        elif temperature <= 35:
            conditions['temperature_status'] = 'CALIENTE'
            conditions['recommendations'].append('Proporcionar sombra durante las horas más calientes')
            conditions['optimal_for'].append('Plantas resistentes al calor')
        else:
            conditions['temperature_status'] = 'MUY_CALIENTE'
            conditions['alerts'].append('🔥 Temperatura muy alta - riesgo de estrés térmico')
            conditions['recommendations'].append('Sombra urgente y riego frecuente')
        
        # Evaluar humedad
        if humidity < 30:
            conditions['humidity_status'] = 'MUY_SECA'
            conditions['alerts'].append('🏜️ Aire muy seco - aumentar humedad ambiental')
            conditions['recommendations'].append('Nebulización foliar o humidificadores')
        elif humidity < 40:
            conditions['humidity_status'] = 'SECA'
            conditions['recommendations'].append('Monitorear hidratación de plantas')
        elif humidity <= 60:
            conditions['humidity_status'] = 'ÓPTIMA'
        elif humidity <= 70:
            conditions['humidity_status'] = 'HÚMEDA'
        elif humidity <= 85:
            conditions['humidity_status'] = 'MUY_HÚMEDA'
            conditions['recommendations'].append('Mejorar ventilación para prevenir hongos')
        else:
            conditions['humidity_status'] = 'SATURADA'
            conditions['alerts'].append('💧 Humedad excesiva - riesgo de enfermedades fúngicas')
            conditions['recommendations'].append('Ventilación urgente y control de hongos')
        
        # Evaluación general
        temp_score = {
            'MUY_FRÍA': 1, 'FRÍA': 2, 'ÓPTIMA': 5, 'CÁLIDA': 4, 'CALIENTE': 3, 'MUY_CALIENTE': 1
        }.get(conditions['temperature_status'], 0)
        
        humid_score = {
            'MUY_SECA': 2, 'SECA': 3, 'ÓPTIMA': 5, 'HÚMEDA': 4, 'MUY_HÚMEDA': 3, 'SATURADA': 1
        }.get(conditions['humidity_status'], 0)
        
        overall_score = (temp_score + humid_score) / 2
        
        if overall_score >= 4.5:
            conditions['overall_rating'] = 'EXCELENTE'
        elif overall_score >= 3.5:
            conditions['overall_rating'] = 'BUENA'
        elif overall_score >= 2.5:
            conditions['overall_rating'] = 'REGULAR'
        else:
            conditions['overall_rating'] = 'PROBLEMÁTICA'
        
        return conditions

    def get_environmental_status(self):
        """
        Obtiene estado ambiental completo con interpretación
        
        Returns:
            dict: Estado ambiental completo
        """
        reading = self.get_compensated_reading()
        
        if not reading['success']:
            return {
                'status': 'ERROR',
                'error': reading['error'],
                'timestamp': reading['timestamp']
            }
        
        # Calcular estadísticas de funcionamiento
        success_rate = (self.stats['successful_readings'] / max(1, self.stats['total_readings'])) * 100
        uptime = time.time() - self.stats['uptime_start']
        
        return {
            'status': 'SUCCESS',
            'timestamp': reading['timestamp'],
            'environmental_data': {
                'temperature': reading['temperature'],
                'humidity': reading['humidity'],
                'dew_point': reading['dew_point'],
                'heat_index': reading['heat_index'],
                'conditions': reading['plant_conditions']
            },
            'sensor_health': {
                'success_rate': round(success_rate, 1),
                'total_readings': self.stats['total_readings'],
                'uptime_hours': round(uptime / 3600, 1),
                'last_reading_age': round(time.time() - self.stats['last_reading_time'], 1),
                'status': 'HEALTHY' if success_rate >= 80 else 'DEGRADED' if success_rate >= 60 else 'CRITICAL'
            },
            'raw_data': reading['raw_values'],
            'technical_info': reading['sensor_info']
        }

    def monitor_environment(self, duration_minutes=10, interval_seconds=30):
        """
        Monitoreo continuo del ambiente
        
        Args:
            duration_minutes (int): Duración del monitoreo
            interval_seconds (int): Intervalo entre lecturas
        """
        print(f"\n🌡️  MONITOREO AMBIENTAL - {duration_minutes} minutos")
        print(f"📊 Intervalo: {interval_seconds}s | Compensación: {'ON' if self.config['enable_offset_compensation'] else 'OFF'}")
        print("\n⏰ Tiempo\t🌡️ Temp\t💧 Humedad\t🌿 Condiciones\t\t📊 Estado")
        print("-" * 80)
        
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        
        readings_history = []
        alert_count = 0
        
        try:
            while time.time() < end_time:
                elapsed = (time.time() - start_time) / 60
                
                status = self.get_environmental_status()
                
                if status['status'] == 'SUCCESS':
                    env = status['environmental_data']
                    conditions = env['conditions']
                    
                    # Formato de salida
                    temp_str = f"{env['temperature']:5.1f}°C"
                    humid_str = f"{env['humidity']:5.1f}%"
                    condition_str = f"{conditions['overall_rating']:12s}"
                    health_str = status['sensor_health']['status']
                    
                    print(f"{elapsed:5.1f}m\t{temp_str}\t{humid_str}\t\t{condition_str}\t{health_str}")
                    
                    # Guardar para análisis
                    readings_history.append({
                        'time': elapsed,
                        'temperature': env['temperature'],
                        'humidity': env['humidity'],
                        'conditions': conditions
                    })
                    
                    # Contar alertas
                    if conditions['alerts']:
                        alert_count += len(conditions['alerts'])
                        for alert in conditions['alerts']:
                            print(f"      ⚠️  {alert}")
                
                else:
                    print(f"{elapsed:5.1f}m\t❌ ERROR: {status['error'][:30]}...")
                
                time.sleep(interval_seconds)
                
        except KeyboardInterrupt:
            print("\n⏹️  Monitoreo detenido por usuario")
        
        # Generar resumen
        self.generate_monitoring_summary(readings_history, alert_count)

    def generate_monitoring_summary(self, readings_history, alert_count):
        """
        Genera resumen del monitoreo realizado
        
        Args:
            readings_history (list): Historial de lecturas
            alert_count (int): Número total de alertas
        """
        if not readings_history:
            print("\n❌ No hay datos para generar resumen")
            return
        
        # Estadísticas básicas
        temperatures = [r['temperature'] for r in readings_history]
        humidities = [r['humidity'] for r in readings_history]
        
        temp_avg = sum(temperatures) / len(temperatures)
        humid_avg = sum(humidities) / len(humidities)
        temp_range = max(temperatures) - min(temperatures)
        humid_range = max(humidities) - min(humidities)
        
        # Análisis de condiciones
        condition_counts = {}
        for reading in readings_history:
            condition = reading['conditions']['overall_rating']
            condition_counts[condition] = condition_counts.get(condition, 0) + 1
        
        most_common_condition = max(condition_counts, key=condition_counts.get)
        
        print(f"\n📈 RESUMEN DEL MONITOREO:")
        print(f"📊 Lecturas válidas: {len(readings_history)}")
        print(f"🌡️  Temperatura promedio: {temp_avg:.1f}°C (variación: ±{temp_range/2:.1f}°C)")
        print(f"💧 Humedad promedio: {humid_avg:.1f}% (variación: ±{humid_range/2:.1f}%)")
        print(f"🌿 Condición predominante: {most_common_condition}")
        print(f"⚠️  Total de alertas: {alert_count}")
        
        # Recomendaciones finales
        print(f"\n💡 RECOMENDACIONES FINALES:")
        if temp_range > 5:
            print("   • Temperatura muy variable - verificar aislamiento")
        if humid_range > 15:
            print("   • Humedad muy variable - mejorar control ambiental")
        if alert_count > len(readings_history) * 0.3:
            print("   • Muchas alertas - atender condiciones ambientales")
        if alert_count == 0:
            print("   • ✅ Condiciones ambientales estables y saludables")


def greenhouse_controller_example(sensor):
    """
    Ejemplo de controlador automático para invernadero
    
    Args:
        sensor: Instancia del sensor DHT22
    """
    print("\n🏠 CONTROLADOR AUTOMÁTICO DE INVERNADERO")
    print("=" * 50)
    
    status = sensor.get_environmental_status()
    
    if status['status'] != 'SUCCESS':
        print(f"❌ Error del sensor: {status['error']}")
        return
    
    env = status['environmental_data']
    conditions = env['conditions']
    
    print(f"🌡️  Temperatura: {env['temperature']}°C")
    print(f"💧 Humedad: {env['humidity']}%")
    print(f"🌿 Estado: {conditions['overall_rating']}")
    
    # Decisiones de control
    actions = []
    
    # Control de temperatura
    if env['temperature'] > 30:
        actions.append("🌬️ ACTIVAR ventilación")
        actions.append("☂️ DESPLEGAR sombra")
    elif env['temperature'] < 15:
        actions.append("🔥 ACTIVAR calefacción")
        actions.append("🚪 CERRAR ventilación")
    
    # Control de humedad
    if env['humidity'] > 80:
        actions.append("💨 AUMENTAR ventilación")
        actions.append("💡 ACTIVAR deshumidificador")
    elif env['humidity'] < 40:
        actions.append("💦 ACTIVAR nebulización")
        actions.append("🚿 AUMENTAR riego por aspersión")
    
    # Mostrar acciones
    if actions:
        print(f"\n🎯 ACCIONES RECOMENDADAS:")
        for action in actions:
            print(f"   • {action}")
    else:
        print(f"\n✅ CONDICIONES ÓPTIMAS - No se requieren acciones")
    
    # Alertas críticas
    if conditions['alerts']:
        print(f"\n🚨 ALERTAS CRÍTICAS:")
        for alert in conditions['alerts']:
            print(f"   • {alert}")


def main():
    """
    Función principal de demostración
    """
    try:
        # Configuración inicial
        pin_input = input("Pin de datos DHT22 (por defecto 15): ").strip()
        pin_number = int(pin_input) if pin_input else 15
        
        offset_input = input("¿Habilitar compensación de offset? (s/n): ").strip().lower()
        enable_offset = offset_input.startswith('s')
        
        # Crear sensor
        sensor = DHT22EnvironmentalSensor(
            data_pin=pin_number, 
            enable_offset_compensation=enable_offset
        )
        
        # Configurar offset si está habilitado
        if enable_offset:
            try:
                temp_offset = input("Offset temperatura °C (0 para saltear): ").strip()
                humid_offset = input("Offset humedad % (0 para saltear): ").strip()
                
                temp_offset = float(temp_offset) if temp_offset else 0.0
                humid_offset = float(humid_offset) if humid_offset else 0.0
                
                if temp_offset != 0 or humid_offset != 0:
                    sensor.set_offset_compensation(temp_offset, humid_offset)
                    
            except ValueError:
                print("⚠️  Valores de offset inválidos - usando 0")
        
        # Menú principal
        while True:
            print("\n" + "="*50)
            print("🌡️  SISTEMA AMBIENTAL DHT22")
            print("="*50)
            print("1. 📊 Estado ambiental actual")
            print("2. 🔍 Monitoreo continuo")
            print("3. 🏠 Simulador de invernadero")
            print("4. 📈 Lecturas simples")
            print("5. ⚙️ Configuración")
            print("6. 💾 Guardar configuración")
            print("7. 🚪 Salir")
            
            option = input("\nSelecciona (1-7): ").strip()
            
            if option == "1":
                status = sensor.get_environmental_status()
                if status['status'] == 'SUCCESS':
                    env = status['environmental_data']
                    print(f"\n🌡️  Temperatura: {env['temperature']}°C")
                    print(f"💧 Humedad: {env['humidity']}%")
                    print(f"🌡️  Punto de rocío: {env['dew_point']}°C")
                    print(f"🔥 Índice de calor: {env['heat_index']}°C")
                    print(f"🌿 Condiciones: {env['conditions']['overall_rating']}")
                    
                    if env['conditions']['recommendations']:
                        print("\n💡 Recomendaciones:")
                        for rec in env['conditions']['recommendations']:
                            print(f"   • {rec}")
                            
                else:
                    print(f"❌ Error: {status['error']}")
            
            elif option == "2":
                duration = int(input("Duración en minutos (10): ") or "10")
                interval = int(input("Intervalo en segundos (30): ") or "30")
                sensor.monitor_environment(duration, interval)
            
            elif option == "3":
                greenhouse_controller_example(sensor)
            
            elif option == "4":
                print("\n📊 Lecturas cada 3s (Ctrl+C para parar)")
                try:
                    while True:
                        reading = sensor.get_compensated_reading()
                        if reading['success']:
                            print(f"🌡️ {reading['temperature']:5.1f}°C | "
                                  f"💧 {reading['humidity']:5.1f}% | "
                                  f"🌿 {reading['plant_conditions']['overall_rating']}")
                        else:
                            print(f"❌ {reading['error']}")
                        time.sleep(3)
                except KeyboardInterrupt:
                    print("\n⏹️  Lecturas detenidas")
            
            elif option == "5":
                print(f"\n⚙️  CONFIGURACIÓN ACTUAL:")
                print(f"📍 Pin: GPIO{sensor.data_pin}")
                print(f"🎯 Offset: T={sensor.offset_compensation['temperature_offset']:+.1f}°C, "
                      f"H={sensor.offset_compensation['humidity_offset']:+.1f}%")
                print(f"📊 Estadísticas: {sensor.stats['successful_readings']}/{sensor.stats['total_readings']} lecturas exitosas")
            
            elif option == "6":
                sensor.save_configuration()
            
            elif option == "7":
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
