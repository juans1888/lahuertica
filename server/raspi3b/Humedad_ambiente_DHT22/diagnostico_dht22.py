#!/usr/bin/env python3
"""
Sistema de Diagnostico DHT22 - La Huertica
Realiza pruebas completas del sensor DHT22 y genera estadisticas de confiabilidad
Compatible con Raspberry Pi 3 B+ y sistemas mas recientes
"""

import time
import sys
import statistics
from datetime import datetime

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


def read_dht22_raw(pin):
    """
    Lee datos raw del sensor DHT22 (version mejorada para diagnostico)

    Args:
        pin (int): Numero de pin GPIO donde esta conectado el sensor

    Returns:
        tuple: (temperatura, humedad, tiempo_lectura) o (None, None, None) si hay error
    """
    start_time = time.time()

    # Configurar GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(pin, GPIO.OUT)

    # Lista para almacenar bits de datos
    data = []

    try:
        # Senal de inicio
        GPIO.output(pin, GPIO.LOW)
        time.sleep(0.02)  # 20ms
        GPIO.output(pin, GPIO.HIGH)

        # Cambiar a modo entrada
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        # Esperar respuesta del sensor
        timeout = time.time() + 0.1
        while GPIO.input(pin) == GPIO.HIGH:
            if time.time() > timeout:
                return None, None, None

        while GPIO.input(pin) == GPIO.LOW:
            if time.time() > timeout:
                return None, None, None

        while GPIO.input(pin) == GPIO.HIGH:
            if time.time() > timeout:
                return None, None, None

        # Leer 40 bits de datos
        for i in range(40):
            # Esperar inicio del bit
            while GPIO.input(pin) == GPIO.LOW:
                if time.time() > timeout:
                    return None, None, None

            # Medir duracion del pulso alto
            bit_start = time.time()
            while GPIO.input(pin) == GPIO.HIGH:
                if time.time() > timeout:
                    return None, None, None

            # Si el pulso es largo, es un '1', si es corto es un '0'
            if (time.time() - bit_start) > 0.00005:  # 50 microsegundos
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
            checksum = (
                bytes_data[0] + bytes_data[1] + bytes_data[2] + bytes_data[3]
            ) & 0xFF
            if checksum == bytes_data[4]:
                # Calcular humedad y temperatura
                humidity = ((bytes_data[0] << 8) + bytes_data[1]) / 10.0
                temperature = (((bytes_data[2] & 0x7F) << 8) + bytes_data[3]) / 10.0

                # Verificar signo de temperatura
                if bytes_data[2] & 0x80:
                    temperature = -temperature

                read_time = time.time() - start_time
                return temperature, humidity, read_time

        return None, None, None

    except Exception as e:
        return None, None, None

    finally:
        GPIO.cleanup()


def test_connectivity(pin, num_tests=5):
    """
    Prueba basica de conectividad del sensor

    Args:
        pin (int): Pin GPIO del sensor
        num_tests (int): Numero de pruebas a realizar

    Returns:
        dict: Resultados de la prueba de conectividad
    """
    print("[TEST] Prueba de conectividad basica...")
    print(f"       Realizando {num_tests} lecturas...")

    successful_reads = 0
    failed_reads = 0
    read_times = []

    for i in range(num_tests):
        print(f"       Lectura {i+1}/{num_tests}...", end=" ")
        temp, hum, read_time = read_dht22_raw(pin)

        if temp is not None and hum is not None:
            successful_reads += 1
            read_times.append(read_time)
            print("OK")
        else:
            failed_reads += 1
            print("FALLO")

        time.sleep(1)

    success_rate = (successful_reads / num_tests) * 100

    result = {
        "total_tests": num_tests,
        "successful": successful_reads,
        "failed": failed_reads,
        "success_rate": success_rate,
        "avg_read_time": statistics.mean(read_times) if read_times else 0,
    }

    print(f"[RESULT] Exito: {successful_reads}/{num_tests} ({success_rate:.1f}%)")
    return result


def test_stability(pin, duration_minutes=2):
    """
    Prueba de estabilidad y consistencia de lecturas

    Args:
        pin (int): Pin GPIO del sensor
        duration_minutes (int): Duracion de la prueba en minutos

    Returns:
        dict: Estadisticas de estabilidad
    """
    print(f"[TEST] Prueba de estabilidad ({duration_minutes} minutos)...")

    temperatures = []
    humidities = []
    read_times = []
    failed_reads = 0

    start_time = time.time()
    end_time = start_time + (duration_minutes * 60)

    reading_count = 0

    while time.time() < end_time:
        reading_count += 1
        remaining_time = int(end_time - time.time())
        print(f"       Lectura {reading_count} (quedan {remaining_time}s)...", end=" ")

        temp, hum, read_time = read_dht22_raw(pin)

        if temp is not None and hum is not None:
            temperatures.append(temp)
            humidities.append(hum)
            read_times.append(read_time)
            print(f"T:{temp:.1f}C H:{hum:.1f}%")
        else:
            failed_reads += 1
            print("FALLO")

        time.sleep(3)  # Lectura cada 3 segundos

    if temperatures and humidities:
        temp_stats = {
            "min": min(temperatures),
            "max": max(temperatures),
            "avg": statistics.mean(temperatures),
            "std_dev": statistics.stdev(temperatures) if len(temperatures) > 1 else 0,
            "range": max(temperatures) - min(temperatures),
        }

        hum_stats = {
            "min": min(humidities),
            "max": max(humidities),
            "avg": statistics.mean(humidities),
            "std_dev": statistics.stdev(humidities) if len(humidities) > 1 else 0,
            "range": max(humidities) - min(humidities),
        }

        performance_stats = {
            "total_readings": reading_count,
            "successful_readings": len(temperatures),
            "failed_readings": failed_reads,
            "success_rate": (len(temperatures) / reading_count) * 100,
            "avg_read_time": statistics.mean(read_times),
            "max_read_time": max(read_times),
            "min_read_time": min(read_times),
        }
    else:
        temp_stats = hum_stats = performance_stats = {}

    return {
        "temperature": temp_stats,
        "humidity": hum_stats,
        "performance": performance_stats,
    }


def test_anomaly_detection(pin, num_samples=20):
    """
    Detecta valores anomalos en las lecturas

    Args:
        pin (int): Pin GPIO del sensor
        num_samples (int): Numero de muestras para analizar

    Returns:
        dict: Reporte de anomalias detectadas
    """
    print(f"[TEST] Deteccion de anomalias ({num_samples} muestras)...")

    temperatures = []
    humidities = []
    anomalies = []

    for i in range(num_samples):
        print(f"       Muestra {i+1}/{num_samples}...", end=" ")
        temp, hum, _ = read_dht22_raw(pin)

        if temp is not None and hum is not None:
            temperatures.append(temp)
            humidities.append(hum)

            # Detectar anomalias basicas
            anomaly_detected = False
            reasons = []

            # Temperatura fuera de rango esperado
            if temp < -40 or temp > 80:
                anomaly_detected = True
                reasons.append("Temperatura fuera de rango")

            # Humedad fuera de rango
            if hum < 0 or hum > 100:
                anomaly_detected = True
                reasons.append("Humedad fuera de rango")

            # Cambios drasticos (si hay lecturas previas)
            if len(temperatures) > 1:
                temp_change = abs(temp - temperatures[-2])
                hum_change = abs(hum - humidities[-2])

                if temp_change > 10:  # Cambio mayor a 10 grados
                    anomaly_detected = True
                    reasons.append(f"Cambio drastico temperatura: {temp_change:.1f}C")

                if hum_change > 20:  # Cambio mayor a 20%
                    anomaly_detected = True
                    reasons.append(f"Cambio drastico humedad: {hum_change:.1f}%")

            if anomaly_detected:
                anomalies.append(
                    {
                        "sample": i + 1,
                        "temperature": temp,
                        "humidity": hum,
                        "reasons": reasons,
                    }
                )
                print(f"ANOMALIA: {', '.join(reasons)}")
            else:
                print("OK")
        else:
            print("FALLO")

        time.sleep(1)

    return {
        "total_samples": num_samples,
        "valid_samples": len(temperatures),
        "anomalies_detected": len(anomalies),
        "anomaly_rate": (
            (len(anomalies) / len(temperatures)) * 100 if temperatures else 0
        ),
        "anomalies": anomalies,
    }


def generate_report(connectivity_results, stability_results, anomaly_results, pin):
    """
    Genera reporte completo de diagnostico

    Args:
        connectivity_results (dict): Resultados prueba conectividad
        stability_results (dict): Resultados prueba estabilidad
        anomaly_results (dict): Resultados deteccion anomalias
        pin (int): Pin GPIO usado
    """
    print("\n" + "=" * 60)
    print("REPORTE DE DIAGNOSTICO DHT22 - LA HUERTICA")
    print("=" * 60)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Pin GPIO: {pin}")
    print()

    # Resumen general
    print("RESUMEN GENERAL:")
    print("-" * 20)
    overall_success = connectivity_results.get("success_rate", 0)
    stability_success = stability_results.get("performance", {}).get("success_rate", 0)
    anomaly_rate = anomaly_results.get("anomaly_rate", 0)

    if overall_success >= 90:
        health_status = "EXCELENTE"
    elif overall_success >= 75:
        health_status = "BUENO"
    elif overall_success >= 50:
        health_status = "REGULAR"
    else:
        health_status = "DEFICIENTE"

    print(f"Estado general del sensor: {health_status}")
    print(f"Confiabilidad promedio: {overall_success:.1f}%")
    print(f"Tasa de anomalias: {anomaly_rate:.1f}%")
    print()

    # Detalles de conectividad
    print("CONECTIVIDAD:")
    print("-" * 15)
    print(
        f"Lecturas exitosas: {connectivity_results['successful']}/{connectivity_results['total_tests']}"
    )
    print(f"Tasa de exito: {connectivity_results['success_rate']:.1f}%")
    print(f"Tiempo promedio lectura: {connectivity_results['avg_read_time']:.3f}s")
    print()

    # Detalles de estabilidad
    if stability_results.get("temperature"):
        print("ESTABILIDAD - TEMPERATURA:")
        print("-" * 30)
        temp = stability_results["temperature"]
        print(f"Rango: {temp['min']:.1f}C a {temp['max']:.1f}C")
        print(f"Promedio: {temp['avg']:.1f}C")
        print(f"Desviacion estandar: {temp['std_dev']:.2f}C")
        print(f"Variacion maxima: {temp['range']:.1f}C")
        print()

        print("ESTABILIDAD - HUMEDAD:")
        print("-" * 25)
        hum = stability_results["humidity"]
        print(f"Rango: {hum['min']:.1f}% a {hum['max']:.1f}%")
        print(f"Promedio: {hum['avg']:.1f}%")
        print(f"Desviacion estandar: {hum['std_dev']:.2f}%")
        print(f"Variacion maxima: {hum['range']:.1f}%")
        print()

    # Detalles de anomalias
    print("DETECCION DE ANOMALIAS:")
    print("-" * 25)
    print(f"Muestras analizadas: {anomaly_results['valid_samples']}")
    print(f"Anomalias detectadas: {anomaly_results['anomalies_detected']}")
    print(f"Tasa de anomalias: {anomaly_results['anomaly_rate']:.1f}%")

    if anomaly_results["anomalies"]:
        print("\nAnomalias encontradas:")
        for anomaly in anomaly_results["anomalies"][:5]:  # Mostrar max 5
            print(f"  - Muestra {anomaly['sample']}: {', '.join(anomaly['reasons'])}")
    print()

    # Recomendaciones
    print("RECOMENDACIONES:")
    print("-" * 18)

    if overall_success < 75:
        print("- Verificar conexiones fisicas del sensor")
        print("- Revisar alimentacion electrica")
        print("- Considerar reemplazar el sensor")

    if stability_results.get("temperature", {}).get("std_dev", 0) > 2:
        print("- Alta variacion en temperatura, verificar estabilidad termica")

    if stability_results.get("humidity", {}).get("std_dev", 0) > 5:
        print("- Alta variacion en humedad, verificar flujo de aire")

    if anomaly_rate > 10:
        print("- Alta tasa de anomalias, revisar entorno del sensor")

    if connectivity_results.get("avg_read_time", 0) > 0.2:
        print("- Tiempo de lectura alto, verificar interferencias")

    if overall_success >= 90 and anomaly_rate < 5:
        print("- Sensor funcionando correctamente")
        print("- Continuar con monitoreo regular")

    print("\n" + "=" * 60)


def main():
    """
    Funcion principal del sistema de diagnostico
    """
    print("SISTEMA DE DIAGNOSTICO DHT22 - LA HUERTICA")
    print("=" * 50)
    print("Este sistema realizara pruebas completas del sensor DHT22")
    print()

    # Configuracion
    SENSOR_PIN = 15  # Cambiar segun tu configuracion

    print(f"Configuracion:")
    print(f"- Pin GPIO: {SENSOR_PIN}")
    print(f"- Tiempo estimado: 5-7 minutos")
    print()

    input("Presiona ENTER para comenzar las pruebas...")
    print()

    try:
        # Prueba 1: Conectividad basica
        connectivity_results = test_connectivity(SENSOR_PIN, 10)
        print()

        # Prueba 2: Estabilidad (2 minutos)
        stability_results = test_stability(SENSOR_PIN, 2)
        print()

        # Prueba 3: Deteccion de anomalias
        anomaly_results = test_anomaly_detection(SENSOR_PIN, 15)
        print()

        # Generar reporte final
        generate_report(
            connectivity_results, stability_results, anomaly_results, SENSOR_PIN
        )

    except KeyboardInterrupt:
        print("\n[EXIT] Diagnostico interrumpido por el usuario")
    except Exception as e:
        print(f"[ERROR] Error durante el diagnostico: {e}")
    finally:
        GPIO.cleanup()
        print("[CLEAN] GPIO limpiado correctamente")


if __name__ == "__main__":
    main()
