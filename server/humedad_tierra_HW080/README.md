# 🌱 Sensor HW-080 - Monitoreo de Humedad del Suelo para Huerta Inteligente

## 📖 Descripción

Este módulo proporciona un sistema completo para el monitoreo de humedad del suelo usando el sensor capacitivo HW-080 en Raspberry Pi Pico con MicroPython. Ideal para sistemas de riego automático y huertas inteligentes que requieren control preciso de la humedad del sustrato.

### ✨ Características Principales

- 🎯 **Sensor Capacitivo**: Tecnología sin contacto directo, mayor durabilidad
- 🔧 **Calibración Automática**: Sistema paso a paso para máxima precisión
- 📊 **Medición Dual**: Lectura analógica (0-100%) + digital (húmedo/seco)
- 🌱 **Decisiones de Riego**: Sistema inteligente de recomendaciones
- 🛠️ **Diagnóstico Completo**: Herramientas para validación y troubleshooting
- 📈 **Monitoreo Continuo**: Análisis de tendencias y alertas automáticas

## 🔌 Conexiones del Sensor

### Esquema de Conexión

```
HW-080 (Capacitivo)   Raspberry Pi Pico
┌─────────────────┐   ┌─────────────────┐
│ VCC (Rojo)      │───│ 3.3V            │
│ GND (Negro)     │───│ GND             │
│ AOUT (Amarillo) │───│ ADC0 (GPIO26)   │ (analógico)
│ DOUT (Azul)     │───│ GPIO16          │ (digital)
└─────────────────┘   └─────────────────┘
```

### ⚙️ Ajuste del Potenciómetro

**IMPORTANTE**: El sensor incluye un potenciómetro para ajustar la sensibilidad de la salida digital. Calibra según tus necesidades específicas.

## 📁 Estructura de Archivos

```
humedad_tierra_HW080/
├── humedad_hw080.py           # 🎯 Sistema principal con calibración
├── calibracion_hw080.py       # 🔧 Herramienta de calibración automática
├── diagnostico_hw080.py       # 🔍 Diagnóstico y validación
└── README.md                  # 📖 Esta documentación
```

## 🚀 Guía de Uso Paso a Paso

### 1️⃣ Calibración Inicial (OBLIGATORIO)

**El sensor HW-080 DEBE calibrarse antes del primer uso:**

```python
# Ejecutar calibración automática
exec(open('calibracion_hw080.py').read())
```

**Proceso de calibración:**

1. 🌵 **Estado SECO**: Sensor en el aire libre
2. 💧 **Estado HÚMEDO**: Sensor en tierra húmeda (no barro)
3. ✅ **Validación**: Verificación automática de valores
4. 💾 **Guardado**: Configuración persistente en archivo JSON

**¿Por qué calibrar?**

- Cada sensor tiene variaciones de fábrica
- Las condiciones ambientales afectan las lecturas
- La calibración garantiza precisión del 0-100%

### 2️⃣ Diagnóstico de Sistema (Opcional)

**Si tienes problemas o quieres verificar el funcionamiento:**

```python
# Diagnóstico completo del sensor
exec(open('diagnostico_hw080.py').read())
```

**Herramientas de diagnóstico:**

- 🧪 **Prueba básica**: Verificación de conectividad
- 📊 **Análisis de rangos**: Validación de valores
- 🔌 **Test de conexiones**: Verificación de cableado
- ⚙️ **Ajuste de potenciómetro**: Guía para calibrar salida digital

### 3️⃣ Uso en Producción

**Una vez calibrado, usa el sistema principal:**

```python
# Sistema completo de monitoreo
exec(open('humedad_hw080.py').read())
```

## 🎛️ Opciones del Sistema Principal

### Menú Interactivo

Al ejecutar `humedad_hw080.py` obtendrás:

1. 🔍 **Verificación rápida**

   - Estado actual del suelo
   - Recomendación de riego
   - Nivel de humedad descriptivo

2. 📊 **Monitoreo inteligente**

   - Duración configurable
   - Detección de cambios significativos
   - Análisis de tendencias
   - Alertas automáticas

3. 🚿 **Sistema de decisión de riego**

   - Análisis con umbrales personalizables
   - Múltiples lecturas para decisión robusta
   - Justificación de recomendaciones

4. 📈 **Lecturas continuas simples**
   - Visualización básica cada 3 segundos
   - Ideal para monitoreo en tiempo real

## 💡 Ejemplos de Código

### Ejemplo Básico - Lectura Simple

```python
from machine import Pin, ADC

# Configurar sensor
adc = ADC(Pin(26))           # Pin analógico
digital_pin = Pin(16, Pin.IN) # Pin digital

# Leer valores crudos
raw_value = adc.read_u16()
digital_state = not digital_pin.value()  # Invertir lógica

print(f"Valor crudo: {raw_value}")
print(f"Estado digital: {'Húmedo' if digital_state else 'Seco'}")
```

### Ejemplo Avanzado - Sistema Calibrado

```python
from humedad_hw080 import HW080FinalCalibrated

# Crear sensor con calibración
sensor = HW080FinalCalibrated(adc_pin=26, digital_pin=16)

# Obtener lectura completa
data = sensor.get_complete_reading()

if data['status'] == 'success':
    print(f"🌱 Humedad: {data['humidity_percentage']}%")
    print(f"📊 Nivel: {data['description']}")
    print(f"🎯 Recomendación: {data['irrigation_recommendation']}")
    print(f"{data['emoji']} Estado: {data['moisture_level']}")
```

### Ejemplo de Sistema de Riego Automático

```python
from humedad_hw080 import HW080FinalCalibrated, irrigation_decision_system

# Configurar sensor
sensor = HW080FinalCalibrated()

# Tomar decisión de riego
decision = irrigation_decision_system(sensor, humidity_threshold=40)

print(f"🚿 Regar: {'SÍ' if decision['should_irrigate'] else 'NO'}")
print(f"📝 Razón: {decision['reason']}")
print(f"🎯 Confianza: {decision['confidence']}%")

# Ejecutar riego si es necesario
if decision['should_irrigate'] and decision['confidence'] > 80:
    # activar_sistema_riego()
    print("💧 Activando sistema de riego...")
```

## 🎯 Interpretación de Niveles de Humedad

### Estados del Suelo

- **🔴 MUY_SECO** (0-20%): Riego urgente necesario
- **🟠 SECO** (20-40%): Necesita riego pronto
- **🟡 MODERADO** (40-60%): Humedad aceptable
- **🟢 HÚMEDO** (60-80%): Buena humedad para plantas
- **🌿 MUY_HÚMEDO** (80-100%): Perfecta para plantas exigentes
- **💧 SATURADO** (>100%): Muy húmedo o encharcado

### Recomendaciones de Riego

- **REGAR_AHORA**: Humedad crítica (<30%)
- **CONSIDERAR_RIEGO**: Humedad baja (30-50%)
- **NO_REGAR**: Humedad adecuada (50-90%)
- **ESPERAR_DRENAJE**: Suelo saturado (>90%)

## 🔧 Proceso de Calibración Detallado

### ¿Cuándo Calibrar?

- ✅ Primera instalación del sensor
- ✅ Cambio de tipo de sustrato/tierra
- ✅ Lecturas inconsistentes o sospechosas
- ✅ Después de 6 meses de uso continuo

### Pasos de Calibración

#### 1. **Preparación**

```python
# Ejecutar calibrador
calibrator = HW080Calibrator(adc_pin=26, digital_pin=16)
```

#### 2. **Calibración en Seco**

- Retirar sensor de cualquier superficie
- Mantener en aire libre
- NO tocar las placas metálicas
- Tomar 15 muestras automáticamente

#### 3. **Calibración en Húmedo**

- Preparar tierra húmeda (no barro)
- Insertar sensor completamente
- Asegurar contacto total con las placas
- Tomar 15 muestras automáticamente

#### 4. **Validación Automática**

- Verificar diferencia mínima de 5000 puntos
- Confirmar estabilidad de lecturas
- Validar lógica seco > húmedo
- Guardar configuración si es válida

### Valores de Ejemplo Exitosos

```json
{
  "dry_value": 65535,    # Máximo ADC (aire)
  "wet_value": 26221,    # Tierra húmeda
  "range": 39314,        # Excelente rango de trabajo
  "validation_passed": true
}
```

## 🔍 Solución de Problemas Comunes

### ❌ Error: "Diferencia insuficiente"

**Causas:**

- Tierra no lo suficientemente húmeda
- Sensor no insertado completamente
- Placas del sensor sucias u oxidadas

**Solución:**

1. Usar tierra bien húmeda (no encharcada)
2. Insertar sensor hasta cubrir completamente las placas
3. Limpiar placas con alcohol isopropílico
4. Repetir calibración

### ⚠️ Lecturas Erráticas

**Causas:**

- Interferencia electromagnética
- Conexiones sueltas
- Sensor defectuoso

**Solución:**

1. Alejar de motores y relés
2. Verificar todas las conexiones firmemente
3. Ejecutar `diagnostico_hw080.py`
4. Usar cables blindados si es necesario

### 📊 Valores Siempre en Extremos

**Causas:**

- Calibración incorrecta
- Sensor en corto circuito
- Problemas de alimentación

**Solución:**

1. Re-calibrar completamente
2. Verificar voltaje de alimentación (3.3V)
3. Inspeccionar sensor por daños físicos
4. Probar con otro sensor

### 🔧 Salida Digital No Funciona

**Causas:**

- Potenciómetro mal ajustado
- Pin digital desconectado
- Configuración incorrecta

**Solución:**

1. Ajustar potenciómetro en el módulo
2. Verificar conexión del pin DOUT
3. Usar `diagnostico_hw080.py` para test

## 📊 Configuración de Producción

### Configuración Recomendada para Huerta

```python
# Configuración óptima
sensor = HW080FinalCalibrated(adc_pin=26, digital_pin=16)

# Monitoreo cada 5 minutos
sensor.monitor_smart(
    duration_minutes=60,    # 1 hora
    interval_seconds=300    # Cada 5 minutos
)
```

### Sistema de Riego Automático

```python
import time

def sistema_riego_automatico():
    """Sistema completo de riego automático"""
    sensor = HW080FinalCalibrated()

    while True:
        # Tomar decisión de riego
        decision = irrigation_decision_system(
            sensor,
            humidity_threshold=35  # Regar cuando <35%
        )

        if decision['should_irrigate'] and decision['confidence'] > 85:
            print(f"💧 Activando riego: {decision['reason']}")
            # activar_bomba_riego(duracion=30)  # 30 segundos

        # Esperar 30 minutos antes de siguiente verificación
        time.sleep(1800)

# Ejecutar sistema
# sistema_riego_automatico()
```

### Integración con Control de Invernadero

```python
def control_inteligente_invernadero():
    """Control combinado de riego y ambiente"""
    sensor_suelo = HW080FinalCalibrated()

    data = sensor_suelo.get_complete_reading()

    if data['status'] == 'success':
        humedad = data['humidity_percentage']

        # Lógica de control según humedad
        if humedad < 20:
            # Riego urgente + notificación
            activar_riego_intensivo()
            enviar_alerta("Humedad crítica detectada")

        elif humedad < 40:
            # Riego moderado
            activar_riego_normal()

        elif humedad > 90:
            # Suspender riego + mejorar drenaje
            desactivar_riego()
            activar_ventilacion_suelo()

        # Log para análisis
        registrar_lectura(data)
```

## 📈 Análisis y Tendencias

### Guardado de Datos Históricos

```python
import json
import time

def guardar_lectura_historica(sensor):
    """Guarda lecturas para análisis de tendencias"""
    data = sensor.get_complete_reading()

    if data['status'] == 'success':
        registro = {
            'timestamp': time.time(),
            'humidity_percentage': data['humidity_percentage'],
            'raw_value': data['raw_value'],
            'digital_state': data['digital_state'],
            'irrigation_recommendation': data['irrigation_recommendation']
        }

        # Agregar a archivo histórico
        try:
            with open('humedad_historico.json', 'a') as f:
                f.write(json.dumps(registro) + '\n')
        except:
            # Crear archivo si no existe
            with open('humedad_historico.json', 'w') as f:
                f.write(json.dumps(registro) + '\n')
```

### Análisis de Tendencias

```python
def analizar_tendencias():
    """Analiza patrones de humedad del suelo"""
    try:
        with open('humedad_historico.json', 'r') as f:
            lecturas = [json.loads(line) for line in f]

        if len(lecturas) >= 10:
            # Últimas 10 lecturas
            recientes = lecturas[-10:]
            humedades = [r['humidity_percentage'] for r in recientes]

            promedio = sum(humedades) / len(humedades)
            tendencia = "BAJANDO" if humedades[-1] < humedades[0] else "SUBIENDO"

            print(f"📈 Análisis de Tendencias:")
            print(f"   Promedio últimas 10 lecturas: {promedio:.1f}%")
            print(f"   Tendencia: {tendencia}")

            # Recomendaciones basadas en tendencia
            if tendencia == "BAJANDO" and promedio < 30:
                print("   🚨 Alerta: Humedad bajando rápidamente")
                print("   💡 Recomendación: Aumentar frecuencia de riego")

    except Exception as e:
        print(f"Error analizando tendencias: {e}")
```

## 🔗 Integración con Otros Sistemas

### API REST para Monitoreo Remoto

```python
import ujson as json

def api_estado_humedad():
    """API REST para obtener estado actual"""
    sensor = HW080FinalCalibrated()
    data = sensor.get_complete_reading()

    if data['status'] == 'success':
        response = {
            'humidity_percentage': data['humidity_percentage'],
            'moisture_level': data['moisture_level'],
            'irrigation_needed': data['irrigation_recommendation'] in ['REGAR_AHORA', 'CONSIDERAR_RIEGO'],
            'timestamp': data['timestamp'],
            'sensor_status': 'online'
        }
    else:
        response = {
            'error': data['error'],
            'sensor_status': 'error',
            'timestamp': time.time()
        }

    return json.dumps(response)
```

### Notificaciones Push

```python
def sistema_alertas(sensor, umbral_critico=15):
    """Sistema de alertas para humedad crítica"""
    data = sensor.get_complete_reading()

    if data['status'] == 'success':
        humedad = data['humidity_percentage']

        if humedad <= umbral_critico:
            mensaje = f"🚨 ALERTA: Humedad crítica {humedad}% - Riego urgente necesario"
            # enviar_notificacion_push(mensaje)
            # enviar_sms(mensaje)
            # enviar_email(mensaje)
            print(mensaje)

        elif humedad > 95:
            mensaje = f"💧 ALERTA: Suelo saturado {humedad}% - Verificar drenaje"
            # enviar_notificacion(mensaje)
            print(mensaje)
```

## 📋 Especificaciones Técnicas

### Sensor HW-080 (Capacitivo)

- **Tecnología**: Capacitivo (sin contacto directo)
- **Voltaje de Operación**: 3.3V - 5V
- **Corriente**: <20mA
- **Salida Analógica**: 0V - 3.3V (0-65535 ADC)
- **Salida Digital**: TTL (configurable con potenciómetro)
- **Tiempo de Respuesta**: <1 segundo
- **Durabilidad**: Alta (sin corrosión de electrodos)

### Ventajas vs Sensores Resistivos

- ✅ **Sin corrosión**: No hay contacto directo con el suelo
- ✅ **Mayor durabilidad**: Vida útil extendida
- ✅ **Menos mantenimiento**: No requiere limpieza frecuente
- ✅ **Medición estable**: No se ve afectado por sales del suelo

### Requisitos del Sistema

- **Plataforma**: Raspberry Pi Pico
- **Firmware**: MicroPython 1.19+
- **Memoria**: ~30KB para sistema completo
- **Pines requeridos**: 1 ADC + 1 GPIO digital

## 🎯 Casos de Uso Específicos

### Para Diferentes Tipos de Plantas

```python
# Configuración por tipo de planta
UMBRALES_PLANTAS = {
    'cactus': {'min': 10, 'max': 30},
    'vegetales': {'min': 40, 'max': 70},
    'flores': {'min': 50, 'max': 80},
    'hierbas': {'min': 30, 'max': 60},
    'frutales': {'min': 45, 'max': 75}
}

def riego_por_tipo_planta(sensor, tipo_planta='vegetales'):
    """Sistema de riego adaptado por tipo de planta"""
    config = UMBRALES_PLANTAS.get(tipo_planta, UMBRALES_PLANTAS['vegetales'])

    data = sensor.get_complete_reading()
    humedad = data['humidity_percentage']

    if humedad < config['min']:
        return {'regar': True, 'razon': f'Humedad {humedad}% < mínimo {config["min"]}% para {tipo_planta}'}
    elif humedad > config['max']:
        return {'regar': False, 'razon': f'Humedad {humedad}% > máximo {config["max"]}% para {tipo_planta}'}
    else:
        return {'regar': False, 'razon': f'Humedad {humedad}% óptima para {tipo_planta}'}
```

### Sistema de Múltiples Sensores

```python
def monitoreo_multiple_zonas():
    """Monitoreo de múltiples zonas con diferentes sensores"""
    zonas = {
        'zona_1': HW080FinalCalibrated(adc_pin=26, digital_pin=16),
        'zona_2': HW080FinalCalibrated(adc_pin=27, digital_pin=17),
        'zona_3': HW080FinalCalibrated(adc_pin=28, digital_pin=18)
    }

    for nombre, sensor in zonas.items():
        data = sensor.get_complete_reading()
        if data['status'] == 'success':
            print(f"🌱 {nombre}: {data['humidity_percentage']}% - {data['description']}")

            if data['irrigation_recommendation'] == 'REGAR_AHORA':
                print(f"   💧 Activando riego en {nombre}")
                # activar_riego_zona(nombre)
```

## 🤝 Mantenimiento y Cuidados

### Rutina de Mantenimiento Mensual

1. 🔍 **Inspección visual**: Verificar estado físico del sensor
2. 🧽 **Limpieza**: Limpiar placas con paño seco
3. 📊 **Verificación de lecturas**: Comparar con medición manual
4. 🔧 **Re-calibración**: Si hay desviaciones significativas

### Señales de Que Necesita Mantenimiento

- Lecturas siempre en extremos (0% o 100%)
- Variaciones erráticas sin cambios ambientales
- Diferencia entre digital y analógico inconsistente
- Respuesta lenta a cambios de humedad

### Vida Útil Esperada

- **Sensor HW-080**: 2-3 años en uso continuo
- **Cables y conexiones**: 1-2 años (revisar anualmente)
- **Calibración**: Re-calibrar cada 6 meses

---

> 💡 **Tip importante**: Siempre calibra el sensor antes del primer uso. Una calibración correcta es crucial para obtener mediciones precisas del 0-100%.

> ⚠️ **Precaución**: No sumergir completamente el sensor en agua. Solo las placas metálicas deben tener contacto con el sustrato húmedo.

> 🔧 **Mantenimiento**: Limpia las placas del sensor mensualmente para mantener la precisión de las lecturas.
