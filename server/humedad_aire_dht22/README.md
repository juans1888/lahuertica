# 🌡️ Sensor DHT22 - Monitoreo Ambiental para Huerta Inteligente

## 📖 Descripción

Este módulo proporciona un sistema completo para el monitoreo de temperatura y humedad ambiental usando el sensor DHT22 en Raspberry Pi Pico con MicroPython. Ideal para huertas inteligentes que requieren control preciso de las condiciones ambientales.

### ✨ Características Principales

- 🎯 **Alta Precisión**: DHT22 con precisión de ±0.5°C y ±2-5% humedad
- 🔧 **Calibración Automática**: Sistema de validación y compensación de offset
- 📊 **Monitoreo Continuo**: Lecturas estables con análisis de tendencias
- 🌱 **Evaluación para Plantas**: Interpretación de condiciones óptimas de cultivo
- 🛠️ **Diagnóstico Completo**: Herramientas para detectar y resolver problemas
- 📈 **Análisis Avanzado**: Cálculo de punto de rocío e índice de calor

## 🔌 Conexiones del Sensor

### Esquema de Conexión

```
DHT22 (AM2302)        Raspberry Pi Pico
┌─────────────┐       ┌─────────────┐
│ VCC (Rojo)  │────── │ 3.3V        │
│ DATA (Azul) │────── │ GPIO15      │ (configurable)
│ NC          │       │             │
│ GND (Negro) │────── │ GND         │
└─────────────┘       └─────────────┘
```

### ⚠️ Resistor Pull-up Requerido

**IMPORTANTE**: Conectar resistor de 4.7kΩ entre DATA y 3.3V para garantizar comunicación estable.

## 📁 Estructura de Archivos

```
humedad_aire_dht22/
├── dht22.py                    # 🎯 Sistema principal completo
├── diagnostico_dht22.py        # 🔍 Herramientas de diagnóstico
├── validacion_dht22.py         # ✅ Validación y calibración
├── verificar_libreria_dht22.py # 📦 Verificación de dependencias
└── README.md                   # 📖 Esta documentación
```

## 🚀 Guía de Uso Paso a Paso

### 1️⃣ Verificación Inicial

**Antes de comenzar, verifica que el sistema esté listo:**

```python
# Ejecutar primero para verificar dependencias
exec(open('verificar_libreria_dht22.py').read())
```

**¿Qué hace?**

- ✅ Verifica que MicroPython tenga soporte para DHT22
- 📦 Confirma disponibilidad de módulos necesarios
- 🚨 Alerta sobre problemas de configuración

### 2️⃣ Diagnóstico de Conexión

**Si es tu primera vez o tienes problemas, ejecuta el diagnóstico:**

```python
# Diagnóstico completo del sensor
exec(open('diagnostico_dht22.py').read())
```

**Opciones disponibles:**

1. 🧪 **Prueba básica**: Verifica que el sensor responda
2. ⏱️ **Prueba de estabilidad**: Monitoreo durante 3 minutos
3. 🔌 **Prueba de conexión**: Verifica cableado y pull-up
4. 🌍 **Verificación de rangos**: Confirma lecturas realistas
5. 📊 **Lectura única**: Test rápido del sensor
6. 🔄 **Lecturas continuas**: Monitoreo en tiempo real

### 3️⃣ Validación y Calibración (Opcional)

**Para aplicaciones críticas, valida la precisión del sensor:**

```python
# Sistema de validación completa
exec(open('validacion_dht22.py').read())
```

**Procesos de validación:**

- 🔍 **Funcionalidad básica**: Tasa de éxito >80%
- 📐 **Precisión**: Variación <2°C temperatura, <5% humedad
- 🌍 **Rangos ambientales**: Verificación de valores normales
- 🎯 **Detección de offset**: Comparación con valores de referencia

### 4️⃣ Uso en Producción

**Una vez validado, usa el sistema principal:**

```python
# Sistema completo de monitoreo
exec(open('dht22.py').read())
```

## 🎛️ Opciones del Sistema Principal

### Menú Interactivo

Al ejecutar `dht22.py` obtendrás:

1. 📊 **Estado ambiental actual**

   - Temperatura, humedad, punto de rocío
   - Índice de calor y condiciones para plantas
   - Recomendaciones específicas

2. 🔍 **Monitoreo continuo**

   - Duración configurable (minutos)
   - Intervalo de lecturas (segundos)
   - Análisis de tendencias y alertas

3. 🏠 **Simulador de invernadero**

   - Decisiones automáticas de control
   - Recomendaciones de ventilación/calefacción
   - Alertas críticas

4. 📈 **Lecturas simples**

   - Visualización básica cada 3 segundos
   - Ideal para monitoreo rápido

5. ⚙️ **Configuración**
   - Ajustes de compensación de offset
   - Estadísticas de funcionamiento

## 💡 Ejemplos de Código

### Ejemplo Básico - Lectura Simple

```python
from machine import Pin
import dht
import time

# Configurar sensor
sensor = dht.DHT22(Pin(15))

# Leer valores
sensor.measure()
temperatura = sensor.temperature()
humedad = sensor.humidity()

print(f"Temperatura: {temperatura}°C")
print(f"Humedad: {humedad}%")
```

### Ejemplo Avanzado - Sistema Completo

```python
from dht22 import DHT22EnvironmentalSensor

# Crear sensor con compensación habilitada
sensor = DHT22EnvironmentalSensor(
    data_pin=15,
    enable_offset_compensation=True
)

# Configurar offset si es necesario
sensor.set_offset_compensation(
    temperature_offset=0.5,  # Compensar +0.5°C
    humidity_offset=-2.0     # Compensar -2.0%
)

# Obtener estado completo
status = sensor.get_environmental_status()

if status['status'] == 'SUCCESS':
    env = status['environmental_data']
    print(f"🌡️ Temperatura: {env['temperature']}°C")
    print(f"💧 Humedad: {env['humidity']}%")
    print(f"🌿 Condiciones: {env['conditions']['overall_rating']}")
```

## 🎯 Interpretación de Condiciones para Plantas

### Estados de Temperatura

- **🥶 MUY_FRÍA** (<5°C): Riesgo de daño por frío
- **❄️ FRÍA** (5-15°C): Plantas de clima frío
- **✅ ÓPTIMA** (15-25°C): Ideal para mayoría de vegetales
- **🌡️ CÁLIDA** (25-30°C): Plantas tropicales
- **🔥 CALIENTE** (30-35°C): Requiere sombra
- **🌋 MUY_CALIENTE** (>35°C): Estrés térmico crítico

### Estados de Humedad

- **🏜️ MUY_SECA** (<30%): Nebulización necesaria
- **🌵 SECA** (30-40%): Monitorear hidratación
- **✅ ÓPTIMA** (40-60%): Condiciones ideales
- **💧 HÚMEDA** (60-70%): Aceptable
- **🌊 MUY_HÚMEDA** (70-85%): Mejorar ventilación
- **💦 SATURADA** (>85%): Riesgo de hongos

## 🔧 Solución de Problemas Comunes

### ❌ Error: "Sensor no encontrado"

**Causas:**

- Conexión suelta en pin DATA
- Falta resistor pull-up 4.7kΩ
- Sensor dañado

**Solución:**

1. Verificar todas las conexiones
2. Confirmar resistor pull-up entre DATA y 3.3V
3. Probar con otro pin GPIO
4. Ejecutar `diagnostico_dht22.py`

### ⚠️ Lecturas Inconsistentes

**Causas:**

- Interferencia electromagnética
- Sensor cerca de fuentes de calor
- Vibraciones en el cableado

**Solución:**

1. Alejar de motores/relés
2. Usar cable blindado
3. Fijar conexiones firmemente
4. Ejecutar prueba de estabilidad

### 📊 Valores Fuera de Rango

**Causas:**

- Sensor requiere calibración
- Condiciones ambientales extremas
- Sensor degradado

**Solución:**

1. Ejecutar `validacion_dht22.py`
2. Configurar compensación de offset
3. Verificar ambiente de instalación

## 📋 Configuración de Producción

### Configuración Recomendada

```python
# Configuración óptima para huerta
sensor = DHT22EnvironmentalSensor(
    data_pin=15,
    enable_offset_compensation=True
)

# Monitoreo cada 30 segundos
sensor.monitor_environment(
    duration_minutes=60,    # 1 hora
    interval_seconds=30     # Cada 30 segundos
)
```

### Integración con Sistema de Control

```python
# Ejemplo de integración con control automático
def control_invernadero():
    status = sensor.get_environmental_status()

    if status['status'] == 'SUCCESS':
        temp = status['environmental_data']['temperature']
        humid = status['environmental_data']['humidity']

        # Lógica de control
        if temp > 30:
            activar_ventilacion()
        elif temp < 15:
            activar_calefaccion()

        if humid > 80:
            activar_deshumidificador()
        elif humid < 40:
            activar_nebulizador()
```

## 📊 Persistencia de Datos

### Guardar Configuración

```python
# El sistema guarda automáticamente la configuración
sensor.save_configuration("mi_config_dht22.json")
```

### Formato de Archivo de Configuración

```json
{
  "config": {
    "enable_offset_compensation": true,
    "reading_interval_min": 2.0
  },
  "offset_compensation": {
    "temperature_offset": 0.5,
    "humidity_offset": -2.0,
    "last_calibration": 1640995200
  },
  "stats": {
    "total_readings": 1000,
    "successful_readings": 980,
    "uptime_start": 1640991600
  }
}
```

## 🔗 Integración con Otros Sistemas

### API REST Simple

```python
import ujson as json

def get_environmental_data():
    """Función para API REST"""
    status = sensor.get_environmental_status()

    if status['status'] == 'SUCCESS':
        return json.dumps({
            'temperature': status['environmental_data']['temperature'],
            'humidity': status['environmental_data']['humidity'],
            'conditions': status['environmental_data']['conditions']['overall_rating'],
            'timestamp': status['timestamp']
        })
    else:
        return json.dumps({'error': status['error']})
```

## 📈 Especificaciones Técnicas

### Sensor DHT22 (AM2302)

- **Rango Temperatura**: -40°C a +80°C
- **Precisión Temperatura**: ±0.5°C
- **Rango Humedad**: 0% a 100% RH
- **Precisión Humedad**: ±2-5% RH
- **Tiempo de Respuesta**: 2 segundos
- **Intervalo Mínimo**: 2 segundos entre lecturas

### Requisitos del Sistema

- **Plataforma**: Raspberry Pi Pico
- **Firmware**: MicroPython 1.19+
- **Memoria**: ~50KB para sistema completo
- **Alimentación**: 3.3V, <2.5mA

## 🤝 Contribuciones y Soporte

### Reportar Problemas

Si encuentras problemas:

1. 🔍 Ejecuta `diagnostico_dht22.py`
2. 📋 Anota el mensaje de error completo
3. 📝 Describe las condiciones ambientales
4. 🔧 Incluye tu configuración de hardware

### Mejoras Sugeridas

- 📡 Integración con WiFi para monitoreo remoto
- 📱 App móvil para control
- 🤖 Machine Learning para predicciones
- ⚡ Optimización de consumo energético

---

> 💡 **Tip**: Ejecuta siempre `verificar_libreria_dht22.py` antes de usar el sistema en un nuevo dispositivo para evitar problemas de compatibilidad.

> ⚠️ **Importante**: Usa resistor pull-up de 4.7kΩ para garantizar comunicación estable con el sensor DHT22.
