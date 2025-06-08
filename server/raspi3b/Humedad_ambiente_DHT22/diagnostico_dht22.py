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
            checksum = (bytes_data[0] + bytes_data[1] + bytes_data[2] + bytes_data[3]) & 0xFF
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
        'total_tests': num_tests,
        'successful': successful_reads,
        'failed': failed_reads,
        'success_rate': success_rate,
        'avg_read_time': statistics.mean(read_times) if read_times else 0
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
            'min': min(temperatures),
            'max': max(temperatures),
            'avg': statistics.mean(temperatures),
            'std_dev': statistics.stdev(temperatures) if len(temperatures) > 1 else 0,
            'range': max(temperatures) - min(temperatures)
        }
        
        hum_stats = {
            'min': min(humidities),
            'max': max(humidities),
            'avg': statistics.mean(humidities),
            'std_dev': statistics.stdev(humidities) if len(humidities) > 1 else 0,
            'range': max(humidities) - min(humidities)
        }
        
        performance_stats = {
            'total_readings': reading_count,
            'successful_readings': len(temperatures),
            'failed_readings': failed_reads,
            'success_rate': (len(temperatures) / reading_count) * 100,
            'avg_read_time': statistics.mean(read_times),
            'max_read_time': max(read_times),
            'min_read_time': min(read_times)
        }
    else:
        temp_stats = hum_stats = performance_stats = {}
    
    return {
        'temperature': temp_stats,
        'humidity': hum_stats,
        'performance': performance_stats
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
                anomalies.append({
                    'sample': i+1,
                    'temperature': temp,
                    'humidity': hum,
                    'reasons': reasons
                })
                print(f"ANOMALIA: {', '.join(reasons)}")
            else:
                print("OK")
        else:
            print("FALLO")
        
        time.sleep(1)
    
    return {
        'total_samples': num_samples,
        'valid_samples': len(temperatures),
        'anomalies_detected': len(anomalies),
        'anomaly_rate': (len(anomalies) / le     >#!/usr/bin/env python3
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
            checksum = (bytes_data[0] + bytes_data[1] + bytes_data[2] + bytes_data[3]) & 0xFF
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
        'total_tests': num_tests,
        'successful': successful_reads,
        'failed': failed_reads,
        'success_rate': success_rate,
        'avg_read_time': statistics.mean(read_times) if read_times else 0
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
    read_times = []

    start_time = time.time()
    end_time = start_time + (duration_minutes * 60)
    
    reading_count = 0
    
    