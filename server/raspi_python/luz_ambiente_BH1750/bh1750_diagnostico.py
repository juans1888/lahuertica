#!/usr/bin/env python3
"""
Sistema de Diagnóstico BH1750 - La Huertica
Realiza pruebas completas del sensor de luz BH1750 (GY-30) y genera estadísticas de confiabilidad
Compatible con Raspberry Pi 3 B+ y sistemas más recientes

CONEXIÓN RECOMENDADA BH1750 (GY-30):
========================================

   BH1750/GY-30 Module      Raspberry Pi 3 B+
   ┌─────────────────┐      ┌─────────────────┐
   │ VCC  (Rojo)     │ ───► │ 3.3V   (Pin 1)  │ ⚠️  NO usar 5V
   │ GND  (Negro)    │ ───► │ GND    (Pin 6)  │
   │ SCL  (Amarillo) │ ───► │ GPIO3  (Pin 5)  │ (SCL)
   │ SDA  (Verde)    │ ───► │ GPIO2  (Pin 3)  │ (SDA)
   │ ADDR (Azul)     │ ───► │ GND    (Pin 6)  │ ⚠️  Para dirección 0x23
   └─────────────────┘      └─────────────────┘

ESQUEMA VISUAL:
==============
                  Raspberry Pi 3 B+
                 ┌─────────────────────┐
              1  │ 3.3V            5V  │ 2
              3  │ GPIO2 (SDA) ●   5V  │ 4
              5  │ GPIO3 (SCL) ●  GND  │ 6  ◄── GND + ADDR
              7  │ GPIO4          GPIO │ 8
              9  │ GND         ●  GPIO │ 10
                 │  ...              │
                 └─────────────────────┘
                          │  │  │
                    ┌─────┴──┴──┴─────┐
                    │   BH1750 GY-30  │
                    │ VCC GND SCL SDA │
                    │  │   │   │   │  │
                    │  ●   ●   ●   ●  │ ADDR
                    └─────────────────┘

NOTAS IMPORTANTES:
==================
• Pin ADDR determina dirección I2C:
  - ADDR a GND (o sin conectar) = 0x23 (predeterminado)
  - ADDR a VCC = 0x5C
• Resistencias pull-up 4.7kΩ en SDA y SCL (generalmente ya incluidas en RPi)
• Usar cables cortos (< 20cm) para evitar interferencias
• Habilitar I2C: sudo raspi-config → Interface Options → I2C → Enable
• Verificar I2C: sudo i2cdetect -y 1

"""

import time
import sys
import statistics
from datetime import datetime

# Manejo de compatibilidad I2C - Múltiples opciones para máxima compatibilidad
I2C_BACKEND = None
i2c_bus = None

try:
    import smbus2 as smbus

    I2C_BACKEND = "smbus2"
    print("[I2C] Usando smbus2 como backend I2C (recomendado)")
except ImportError:
    try:
        import smbus

        I2C_BACKEND = "smbus"
        print("[I2C] Usando smbus como backend I2C (clásico)")
    except ImportError:
        try:
            import board
            import busio

            I2C_BACKEND = "busio"
            print("[I2C] Usando busio como backend I2C (CircuitPython)")
        except ImportError:
            print("[ERROR] No se pudo importar ninguna biblioteca I2C")
            print("Soluciones:")
            print("  sudo apt update && sudo apt install python3-smbus")
            print("  pip3 install smbus2")
            print("  sudo raspi-config -> Interface Options -> I2C -> Enable")
            sys.exit(1)

# Constantes del sensor BH1750
BH1750_ADDR_LOW = 0x23  # ADDR pin a GND o flotante
BH1750_ADDR_HIGH = 0x5C  # ADDR pin a VCC
BH1750_POWER_DOWN = 0x00
BH1750_POWER_ON = 0x01
BH1750_RESET = 0x07
BH1750_CONTINUOUS_HIGH_RES = 0x10  # 1 lux resolución, 180ms
BH1750_CONTINUOUS_HIGH_RES2 = 0x11  # 0.5 lux resolución, 180ms
BH1750_CONTINUOUS_LOW_RES = 0x13  # 4 lux resolución, 31ms
BH1750_ONE_TIME_HIGH_RES = 0x20  # 1 lux resolución, 180ms, un disparo
BH1750_ONE_TIME_LOW_RES = 0x23  # 4 lux resolución, 31ms, un disparo

# Rangos de referencia para luz ambiental (en lux)
LIGHT_RANGES = {
    "oscuridad_total": (0, 0.1),
    "luz_luna": (0.1, 1),
    "interior_muy_tenue": (1, 10),
    "interior_tenue": (10, 50),
    "interior_normal": (50, 200),
    "interior_brillante": (200, 500),
    "exterior_sombra": (500, 1000),
    "exterior_nublado": (1000, 10000),
    "exterior_parcial": (10000, 25000),
    "exterior_soleado": (25000, 50000),
    "sol_directo": (50000, 65535),
}


def init_i2c_bus(bus_number=1):
    """
    Inicializa el bus I2C con el backend disponible

    Args:
        bus_number (int): Número del bus I2C (1 para RPi 3 B+)

    Returns:
        object: Objeto del bus I2C o None si hay error
    """
    global i2c_bus, I2C_BACKEND

    try:
        if I2C_BACKEND == "smbus2" or I2C_BACKEND == "smbus":
            i2c_bus = smbus.SMBus(bus_number)
            return i2c_bus
        elif I2C_BACKEND == "busio":
            import board
            import busio

            i2c_bus = busio.I2C(board.SCL, board.SDA)
            return i2c_bus
        else:
            return None
    except Exception as e:
        print(f"[ERROR] No se pudo inicializar I2C: {e}")
        return None


def scan_i2c_devices():
    """
    Escanea el bus I2C para encontrar dispositivos conectados

    Returns:
        list: Lista de direcciones I2C encontradas
    """
    if not i2c_bus:
        return []

    devices = []
    print("[SCAN] Escaneando bus I2C...")

    try:
        if I2C_BACKEND in ["smbus2", "smbus"]:
            for addr in range(0x03, 0x78):
                try:
                    i2c_bus.read_byte(addr)
                    devices.append(addr)
                    device_name = ""
                    if addr == BH1750_ADDR_LOW:
                        device_name = " (BH1750 - ADDR=GND)"
                    elif addr == BH1750_ADDR_HIGH:
                        device_name = " (BH1750 - ADDR=VCC)"
                    print(f"       Dispositivo encontrado: 0x{addr:02X}{device_name}")
                except:
                    pass
        elif I2C_BACKEND == "busio":
            # Para busio, usamos scan()
            import board
            import busio

            i2c = busio.I2C(board.SCL, board.SDA)
            while not i2c.try_lock():
                pass
            try:
                devices = i2c.scan()
                for addr in devices:
                    device_name = ""
                    if addr == BH1750_ADDR_LOW:
                        device_name = " (BH1750 - ADDR=GND)"
                    elif addr == BH1750_ADDR_HIGH:
                        device_name = " (BH1750 - ADDR=VCC)"
                    print(f"       Dispositivo encontrado: 0x{addr:02X}{device_name}")
            finally:
                i2c.unlock()
    except Exception as e:
        print(f"[ERROR] Error durante escaneo I2C: {e}")

    if not devices:
        print("       No se encontraron dispositivos")
        print("       Verificar:")
        print("         • Conexiones VCC, GND, SDA, SCL")
        print("         • I2C habilitado: sudo raspi-config")
        print("         • Comando: sudo i2cdetect -y 1")

    return devices


def find_bh1750_address():
    """
    Encuentra automáticamente la dirección del BH1750

    Returns:
        int or None: Dirección I2C del BH1750 o None si no se encuentra
    """
    devices = scan_i2c_devices()

    # Priorizar dirección estándar (ADDR=GND)
    if BH1750_ADDR_LOW in devices:
        print(
            f"[FOUND] BH1750 encontrado en dirección estándar 0x{BH1750_ADDR_LOW:02X}"
        )
        return BH1750_ADDR_LOW
    elif BH1750_ADDR_HIGH in devices:
        print(
            f"[FOUND] BH1750 encontrado en dirección alternativa 0x{BH1750_ADDR_HIGH:02X}"
        )
        return BH1750_ADDR_HIGH
    else:
        print("[ERROR] BH1750 no encontrado en direcciones conocidas")
        return None


def read_bh1750_raw(address, mode=BH1750_CONTINUOUS_HIGH_RES):
    """
    Lee datos raw del sensor BH1750

    Args:
        address (int): Dirección I2C del sensor
        mode (int): Modo de medición del sensor

    Returns:
        tuple: (lux_value, read_time) o (None, None) si hay error
    """
    if not i2c_bus:
        return None, None

    start_time = time.time()

    try:
        # Enviar comando de medición
        if I2C_BACKEND in ["smbus2", "smbus"]:
            i2c_bus.write_byte(address, mode)
        elif I2C_BACKEND == "busio":
            i2c_bus.writeto(address, bytes([mode]))

        # Esperar según el modo
        if mode in [
            BH1750_CONTINUOUS_HIGH_RES,
            BH1750_CONTINUOUS_HIGH_RES2,
            BH1750_ONE_TIME_HIGH_RES,
        ]:
            time.sleep(0.18)  # 180ms para alta resolución
        else:
            time.sleep(0.031)  # 31ms para baja resolución

        # Leer 2 bytes de datos
        if I2C_BACKEND in ["smbus2", "smbus"]:
            data = i2c_bus.read_i2c_block_data(address, 0x00, 2)
        elif I2C_BACKEND == "busio":
            data = bytearray(2)
            i2c_bus.readfrom_into(address, data)

        # Convertir a valor lux
        raw_value = (data[0] << 8) | data[1]
        lux_value = raw_value / 1.2  # Factor de conversión estándar

        read_time = time.time() - start_time
        return lux_value, read_time

    except Exception as e:
        return None, None


def classify_light_level(lux_value):
    """
    Clasifica el nivel de luz según los rangos definidos

    Args:
        lux_value (float): Valor en lux

    Returns:
        str: Categoría de luz
    """
    if lux_value is None:
        return "error"

    for category, (min_val, max_val) in LIGHT_RANGES.items():
        if min_val <= lux_value < max_val:
            return category

    return "fuera_de_rango"


def test_connectivity(address, num_tests=10):
    """
    Prueba básica de conectividad del sensor BH1750

    Args:
        address (int): Dirección I2C del sensor
        num_tests (int): Número de pruebas a realizar

    Returns:
        dict: Resultados de la prueba de conectividad
    """
    print(f"[TEST] Prueba de conectividad BH1750 (dirección 0x{address:02X})...")
    print(f"       Realizando {num_tests} lecturas...")

    successful_reads = 0
    failed_reads = 0
    read_times = []
    lux_values = []

    for i in range(num_tests):
        print(f"       Lectura {i+1}/{num_tests}...", end=" ")
        lux_value, read_time = read_bh1750_raw(address)

        if lux_value is not None:
            successful_reads += 1
            read_times.append(read_time)
            lux_values.append(lux_value)
            light_category = classify_light_level(lux_value)
            print(f"OK - {lux_value:.1f} lux ({light_category})")
        else:
            failed_reads += 1
            print("FALLO")

        time.sleep(0.5)  # Breve pausa entre lecturas

    success_rate = (successful_reads / num_tests) * 100

    result = {
        "total_tests": num_tests,
        "successful": successful_reads,
        "failed": failed_reads,
        "success_rate": success_rate,
        "avg_read_time": statistics.mean(read_times) if read_times else 0,
        "lux_values": lux_values,
        "avg_lux": statistics.mean(lux_values) if lux_values else 0,
    }

    print(f"[RESULT] Éxito: {successful_reads}/{num_tests} ({success_rate:.1f}%)")
    if lux_values:
        print(f"[RESULT] Promedio: {result['avg_lux']:.1f} lux")

    return result


def test_light_response(address):
    """
    Prueba de respuesta a cambios de luz

    Args:
        address (int): Dirección I2C del sensor

    Returns:
        dict: Resultados de la prueba de respuesta
    """
    print("[TEST] Prueba de respuesta a cambios de luz...")
    print("       Esta prueba verifica que el sensor responda a cambios lumínicos")
    print("       Sigue las instrucciones cuidadosamente")
    print()

    # Lectura base
    print("1. Lectura en condiciones normales...")
    input("   Deja el sensor en condiciones normales de luz y presiona ENTER...")

    base_lux, _ = read_bh1750_raw(address)
    if base_lux is None:
        print("[ERROR] No se pudo obtener lectura base")
        return {"success": False, "error": "No hay lectura base"}

    print(f"   Luz base: {base_lux:.1f} lux ({classify_light_level(base_lux)})")

    # Prueba con sensor cubierto
    print("\n2. Prueba con sensor cubierto...")
    input("   CUBRE completamente el sensor con la mano y presiona ENTER...")

    time.sleep(1)  # Esperar estabilización
    dark_lux, _ = read_bh1750_raw(address)

    if dark_lux is not None:
        print(f"   Luz cubierta: {dark_lux:.1f} lux ({classify_light_level(dark_lux)})")

        reduction_absolute = base_lux - dark_lux
        reduction_percent = (reduction_absolute / base_lux) * 100 if base_lux > 0 else 0

        print(f"   Reducción: {reduction_absolute:.1f} lux ({reduction_percent:.1f}%)")

        if reduction_percent > 80:
            response_rating = "EXCELENTE"
        elif reduction_percent > 60:
            response_rating = "BUENA"
        elif reduction_percent > 30:
            response_rating = "REGULAR"
        else:
            response_rating = "POBRE"

        print(f"   Respuesta a oscuridad: {response_rating}")
    else:
        print("   ERROR en lectura oscura")
        dark_lux = 0
        reduction_percent = 0
        response_rating = "ERROR"

    # Prueba con luz brillante
    print("\n3. Prueba con luz brillante...")
    input("   DESTAPA el sensor y ponlo bajo LUZ BRILLANTE, luego presiona ENTER...")

    time.sleep(1)  # Esperar estabilización
    bright_lux, _ = read_bh1750_raw(address)

    if bright_lux is not None:
        print(
            f"   Luz brillante: {bright_lux:.1f} lux ({classify_light_level(bright_lux)})"
        )

        increase_absolute = bright_lux - base_lux
        increase_percent = (increase_absolute / base_lux) * 100 if base_lux > 0 else 0

        print(f"   Aumento: {increase_absolute:.1f} lux ({increase_percent:.1f}%)")

        if increase_percent > 100:
            brightness_rating = "EXCELENTE"
        elif increase_percent > 50:
            brightness_rating = "BUENA"
        elif increase_percent > 20:
            brightness_rating = "REGULAR"
        else:
            brightness_rating = "POBRE"

        print(f"   Respuesta a luz brillante: {brightness_rating}")
    else:
        print("   ERROR en lectura brillante")
        bright_lux = base_lux
        increase_percent = 0
        brightness_rating = "ERROR"

    # Evaluación general
    overall_success = (
        base_lux is not None
        and dark_lux is not None
        and bright_lux is not None
        and reduction_percent > 30
        and increase_percent > 20
    )

    return {
        "success": overall_success,
        "base_lux": base_lux,
        "dark_lux": dark_lux,
        "bright_lux": bright_lux,
        "reduction_percent": reduction_percent,
        "increase_percent": increase_percent,
        "response_rating": response_rating,
        "brightness_rating": brightness_rating,
    }


def test_stability(address, duration_minutes=2):
    """
    Prueba de estabilidad y consistencia de lecturas

    Args:
        address (int): Dirección I2C del sensor
        duration_minutes (int): Duración de la prueba en minutos

    Returns:
        dict: Estadísticas de estabilidad
    """
    print(f"[TEST] Prueba de estabilidad ({duration_minutes} minutos)...")
    print("       Mantén condiciones de luz CONSTANTES durante la prueba")

    lux_values = []
    read_times = []
    failed_reads = 0

    start_time = time.time()
    end_time = start_time + (duration_minutes * 60)

    reading_count = 0

    while time.time() < end_time:
        reading_count += 1
        remaining_time = int(end_time - time.time())
        print(f"       Lectura {reading_count} (quedan {remaining_time}s)...", end=" ")

        lux_value, read_time = read_bh1750_raw(address)

        if lux_value is not None:
            lux_values.append(lux_value)
            read_times.append(read_time)
            light_category = classify_light_level(lux_value)
            print(f"L:{lux_value:.1f} lux ({light_category[:10]})")
        else:
            failed_reads += 1
            print("FALLO")

        time.sleep(3)  # Lectura cada 3 segundos

    if lux_values:
        lux_stats = {
            "min": min(lux_values),
            "max": max(lux_values),
            "avg": statistics.mean(lux_values),
            "std_dev": statistics.stdev(lux_values) if len(lux_values) > 1 else 0,
            "range": max(lux_values) - min(lux_values),
            "coefficient_variation": (
                (statistics.stdev(lux_values) / statistics.mean(lux_values)) * 100
                if len(lux_values) > 1 and statistics.mean(lux_values) > 0
                else 0
            ),
        }

        performance_stats = {
            "total_readings": reading_count,
            "successful_readings": len(lux_values),
            "failed_readings": failed_reads,
            "success_rate": (len(lux_values) / reading_count) * 100,
            "avg_read_time": statistics.mean(read_times),
            "max_read_time": max(read_times),
            "min_read_time": min(read_times),
        }
    else:
        lux_stats = performance_stats = {}

    return {"lux_data": lux_stats, "performance": performance_stats}


def test_anomaly_detection(address, num_samples=20):
    """
    Detecta valores anómalos en las lecturas

    Args:
        address (int): Dirección I2C del sensor
        num_samples (int): Número de muestras para analizar

    Returns:
        dict: Reporte de anomalías detectadas
    """
    print(f"[TEST] Detección de anomalías ({num_samples} muestras)...")

    lux_values = []
    anomalies = []

    for i in range(num_samples):
        print(f"       Muestra {i+1}/{num_samples}...", end=" ")
        lux_value, _ = read_bh1750_raw(address)

        if lux_value is not None:
            lux_values.append(lux_value)

            # Detectar anomalías específicas del BH1750
            anomaly_detected = False
            reasons = []

            # Valores fuera de rango físico del sensor
            if lux_value < 0:
                anomaly_detected = True
                reasons.append("Valor negativo imposible")
            elif lux_value > 65535:
                anomaly_detected = True
                reasons.append("Valor excede máximo del sensor")

            # Saturación del sensor
            if lux_value >= 65535:
                anomaly_detected = True
                reasons.append("Sensor saturado (luz excesiva)")

            # Cambios drásticos (si hay lecturas previas)
            if len(lux_values) > 1:
                change = abs(lux_value - lux_values[-2])
                change_percent = (
                    (change / lux_values[-2]) * 100 if lux_values[-2] > 0 else 0
                )

                if change > 10000:  # Cambio mayor a 10,000 lux
                    anomaly_detected = True
                    reasons.append(f"Cambio drástico: {change:.0f} lux")
                elif change_percent > 500:  # Cambio mayor a 500%
                    anomaly_detected = True
                    reasons.append(f"Cambio porcentual excesivo: {change_percent:.0f}%")

            # Valores sospechosos por contexto
            if lux_value == 0:
                anomaly_detected = True
                reasons.append("Valor exactamente cero (posible error)")

            if anomaly_detected:
                anomalies.append(
                    {"sample": i + 1, "lux_value": lux_value, "reasons": reasons}
                )
                print(f"ANOMALÍA: {', '.join(reasons)}")
            else:
                print("OK")
        else:
            print("FALLO - Error de lectura")

        time.sleep(0.5)

    return {
        "total_samples": num_samples,
        "valid_samples": len(lux_values),
        "anomalies_detected": len(anomalies),
        "anomaly_rate": (len(anomalies) / len(lux_values)) * 100 if lux_values else 0,
        "anomalies": anomalies,
    }


def generate_report(
    connectivity_results, response_results, stability_results, anomaly_results, address
):
    """
    Genera reporte completo de diagnóstico

    Args:
        connectivity_results (dict): Resultados prueba conectividad
        response_results (dict): Resultados prueba respuesta
        stability_results (dict): Resultados prueba estabilidad
        anomaly_results (dict): Resultados detección anomalías
        address (int): Dirección I2C usada
    """
    print("\n" + "=" * 60)
    print("REPORTE DE DIAGNÓSTICO BH1750 - LA HUERTICA")
    print("=" * 60)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Dirección I2C: 0x{address:02X}")
    print(f"Backend I2C: {I2C_BACKEND}")
    print()

    # Resumen general
    print("RESUMEN GENERAL:")
    print("-" * 20)
    connectivity_success = connectivity_results.get("success_rate", 0)
    stability_success = stability_results.get("performance", {}).get("success_rate", 0)
    anomaly_rate = anomaly_results.get("anomaly_rate", 0)
    response_success = response_results.get("success", False)

    # Calificación general
    overall_score = (connectivity_success + stability_success) / 2
    if overall_score >= 90 and anomaly_rate < 5 and response_success:
        health_status = "EXCELENTE"
    elif overall_score >= 75 and anomaly_rate < 10:
        health_status = "BUENO"
    elif overall_score >= 50 and anomaly_rate < 20:
        health_status = "REGULAR"
    else:
        health_status = "DEFICIENTE"

    print(f"Estado general del sensor: {health_status}")
    print(f"Confiabilidad promedio: {overall_score:.1f}%")
    print(f"Tasa de anomalías: {anomaly_rate:.1f}%")
    print(f"Respuesta a cambios: {'SÍ' if response_success else 'NO'}")
    print()

    # Detalles de conectividad
    print("CONECTIVIDAD I2C:")
    print("-" * 18)
    print(
        f"Lecturas exitosas: {connectivity_results['successful']}/{connectivity_results['total_tests']}"
    )
    print(f"Tasa de éxito: {connectivity_results['success_rate']:.1f}%")
    print(f"Tiempo promedio lectura: {connectivity_results['avg_read_time']:.3f}s")
    if connectivity_results.get("avg_lux", 0) > 0:
        print(f"Luz promedio detectada: {connectivity_results['avg_lux']:.1f} lux")
    print()

    # Detalles de respuesta a cambios
    if response_results.get("success") is not None:
        print("RESPUESTA A CAMBIOS DE LUZ:")
        print("-" * 30)
        print(f"Luz base: {response_results.get('base_lux', 0):.1f} lux")
        print(f"Luz cubierta: {response_results.get('dark_lux', 0):.1f} lux")
        print(f"Luz brillante: {response_results.get('bright_lux', 0):.1f} lux")
        print(
            f"Reducción al cubrir: {response_results.get('reduction_percent', 0):.1f}%"
        )
        print(f"Aumento con luz: {response_results.get('increase_percent', 0):.1f}%")
        print(
            f"Calificación respuesta: {response_results.get('response_rating', 'N/A')}"
        )
        print()

    # Detalles de estabilidad
    if stability_results.get("lux_data"):
        print("ESTABILIDAD DE MEDICIÓN:")
        print("-" * 26)
        lux = stability_results["lux_data"]
        print(f"Rango: {lux['min']:.1f} - {lux['max']:.1f} lux")
        print(f"Promedio: {lux['avg']:.1f} lux")
        print(f"Desviación estándar: {lux['std_dev']:.2f} lux")
        print(f"Variación máxima: {lux['range']:.1f} lux")
        print(f"Coeficiente variación: {lux['coefficient_variation']:.2f}%")
        print()

    # Detalles de anomalías
    print("DETECCIÓN DE ANOMALÍAS:")
    print("-" * 25)
    print(f"Muestras analizadas: {anomaly_results['valid_samples']}")
    print(f"Anomalías detectadas: {anomaly_results['anomalies_detected']}")
    print(f"Tasa de anomalías: {anomaly_results['anomaly_rate']:.1f}%")

    if anomaly_results["anomalies"]:
        print("\nAnomalías encontradas:")
        for anomaly in anomaly_results["anomalies"][:5]:  # Mostrar máximo 5
            print(f"  - Muestra {anomaly['sample']}: {', '.join(anomaly['reasons'])}")
    print()

    # Recomendaciones específicas
    print("RECOMENDACIONES:")
    print("-" * 18)

    if connectivity_success < 80:
        print("- Verificar conexiones I2C (SDA, SCL)")
        print("- Comprobar alimentación 3.3V (NO 5V)")
        print("- Habilitar I2C: sudo raspi-config")
        print("- Verificar con: sudo i2cdetect -y 1")

    if not response_success:
        print("- Limpiar superficie del sensor")
        print("- Verificar que no esté obstruido permanentemente")
        print("- Comprobar integridad física del módulo")

    if stability_results.get("lux_data", {}).get("coefficient_variation", 0) > 10:
        print("- Alta variación en lecturas, verificar:")
        print("  • Estabilidad de la fuente de luz")
        print("  • Interferencias electromagnéticas")
        print("  • Vibración del sensor")

    if anomaly_rate > 10:
        print("- Alta tasa de anomalías:")
        print("  • Verificar ambiente lumínico estable")
        print("  • Comprobar conexiones firmes")
        print("  • Considerar reemplazar el sensor")

    if connectivity_results.get("avg_read_time", 0) > 0.3:
        print("- Tiempo de lectura alto:")
        print("  • Verificar velocidad del bus I2C")
        print("  • Usar cables más cortos")
        print("  • Evitar interferencias")

    # Recomendaciones para horticultura
    avg_lux = connectivity_results.get("avg_lux", 0)
    if avg_lux > 0:
        print(f"\n- Nivel de luz actual ({avg_lux:.0f} lux):")
        light_category = classify_light_level(avg_lux)
        if "interior_tenue" in light_category:
            print("  • Adecuado para plantas de sombra")
            print("  • Considerar luz artificial para vegetales")
        elif "exterior" in light_category:
            print("  • Excelente para cultivos de sol")
            print("  • Ideal para huerta exterior")
        elif "interior_brillante" in light_category:
            print("  • Bueno para plantas de interior")
            print("  • Suficiente para hierbas aromáticas")

    if health_status == "EXCELENTE":
        print("\n- ✅ Sensor funcionando óptimamente")
        print("- ✅ Listo para monitoreo de huerta")
        print("- ✅ Continuar con monitoreo regular")
    elif health_status == "BUENO":
        print("\n- ⚠️  Sensor funcional con observaciones")
        print("- ⚠️  Monitorear tendencias de funcionamiento")
    else:
        print("\n- ❌ Sensor requiere atención antes del uso")
        print("- ❌ Resolver problemas identificados")

    print("\n" + "=" * 60)


def main():
    """
    Función principal del sistema de diagnóstico
    """
    print("SISTEMA DE DIAGNÓSTICO BH1750 - LA HUERTICA")
    print("=" * 50)
    print("Sensor de Luz Digital para Monitoreo de Huerta Inteligente")
    print()

    # Inicializar I2C
    print("[INIT] Inicializando bus I2C...")
    if not init_i2c_bus():
        print("[ERROR] No se pudo inicializar el bus I2C")
        print("Soluciones:")
        print("  • sudo raspi-config → Interface Options → I2C → Enable")
        print("  • sudo reboot")
        print("  • Verificar conexiones de hardware")
        return

    # Encontrar sensor BH1750
    sensor_address = find_bh1750_address()
    if not sensor_address:
        print("\n[ERROR] Sensor BH1750 no detectado")
        print("Verificar:")
        print("  • Conexiones VCC (3.3V), GND, SDA, SCL")
        print("  • Pin ADDR: GND para 0x23, VCC para 0x5C")
        print("  • Comando: sudo i2cdetect -y 1")
        return

    print(f"\n[SUCCESS] Sensor detectado en 0x{sensor_address:02X}")
    print(f"Tiempo estimado de diagnóstico: 6-8 minutos")
    print()

    input("Presiona ENTER para comenzar las pruebas...")
    print()

    try:
        # Prueba 1: Conectividad básica
        print("🔍 INICIANDO DIAGNÓSTICO COMPLETO")
        print("-" * 40)
        connectivity_results = test_connectivity(sensor_address, 12)
        print()

        # Prueba 2: Respuesta a cambios de luz
        response_results = test_light_response(sensor_address)
        print()

        # Prueba 3: Estabilidad (2 minutos)
        stability_results = test_stability(sensor_address, 2)
        print()

        # Prueba 4: Detección de anomalías
        anomaly_results = test_anomaly_detection(sensor_address, 18)
        print()

        # Generar reporte final
        generate_report(
            connectivity_results,
            response_results,
            stability_results,
            anomaly_results,
            sensor_address,
        )

    except KeyboardInterrupt:
        print("\n[EXIT] Diagnóstico interrumpido por el usuario")
    except Exception as e:
        print(f"[ERROR] Error durante el diagnóstico: {e}")
        print("Verificar conexiones y volver a intentar")
    finally:
        if i2c_bus and I2C_BACKEND in ["smbus2", "smbus"]:
            try:
                i2c_bus.close()
            except:
                pass
        print("[CLEAN] Recursos I2C liberados correctamente")


if __name__ == "__main__":
    main()
