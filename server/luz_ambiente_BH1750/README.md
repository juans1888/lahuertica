# 💡 Sensor BH1750 (GY-30) - Intensidad Luminosa

> **Sensor de luz digital para huerta inteligente**  
> Medición precisa de intensidad luminosa para optimización de cultivos

## 📖 Descripción General

El **BH1750** es un sensor digital de intensidad luminosa que mide la luz ambiental en **lux**. Es ideal para sistemas de huerta inteligente donde necesitas:

- 🌱 **Monitoreo de luz** para plantas
- 🚿 **Optimización de riego** según condiciones lumínicas
- 🏠 **Control de iluminación artificial**
- 📊 **Registro de datos** ambientales

### Especificaciones Técnicas

| Característica           | Valor                   |
| ------------------------ | ----------------------- |
| **Voltaje**              | 3.3V - 5V               |
| **Rango de medición**    | 0.1 - 65,535 lux        |
| **Precisión**            | ±20%                    |
| **Interfaz**             | I2C                     |
| **Resolución**           | 1 lux                   |
| **Tiempo de conversión** | 180ms (alta resolución) |

## 🔌 Conexiones

### Raspberry Pi Pico

```
BH1750 (GY-30)    →    Raspberry Pi Pico
─────────────────      ─────────────────
VCC              →     3.3V (pin 36)
GND              →     GND (pin 38)
SDA              →     GPIO0 (pin 1)
SCL              →     GPIO1 (pin 2)
ADDR             →     Sin conectar (o GND)
```

### Diagrama Visual

```
    ┌─────────────┐
    │   BH1750    │
    │   (GY-30)   │
    └─────────────┘
         │ │ │ │
         │ │ │ └── ADDR (opcional)
         │ │ └──── SCL → GPIO1
         │ └────── SDA → GPIO0
         └──────── VCC → 3.3V
                   GND → GND
```

### ⚠️ Importante

- **Usar 3.3V**, no 5V
- Pin **ADDR** controla la dirección I2C:
  - Sin conectar o GND = `0x23`
  - Conectado a VCC = `0x5C`
- Cables cortos para evitar interferencias

## 📁 Archivos del Proyecto

### 🔧 `diagnostico_bh1750.py`

**Uso**: Verificación completa del sensor y solución de problemas

```python
# Ejecutar diagnóstico completo
python diagnostico_bh1750.py
```

**Funciones principales**:

- ✅ Escaneo del bus I2C
- 🧪 Pruebas de funcionamiento básico
- 💡 Test de respuesta a cambios de luz
- ⏱️ Análisis de estabilidad
- 🔧 Guía de solución de problemas

### 💡 `bh1750_simple.py`

**Uso**: Operación directa del sensor (después del diagnóstico)

```python
# Usar sensor directamente
python bh1750_simple.py
```

**Funciones principales**:

- 📊 Lecturas instantáneas
- 🔄 Monitoreo continuo
- 🌱 Consejero de riego basado en luz
- 📈 Múltiples mediciones rápidas

## 🚀 Guía de Uso Rápido

### 1. Primera Instalación

```bash
# 1. Conectar según el diagrama
# 2. Ejecutar diagnóstico
python diagnostico_bh1750.py

# 3. Seleccionar opción 1: Escanear I2C
# 4. Si aparece 0x23, ¡sensor detectado!
```

### 2. Verificación Básica

```bash
# Ejecutar diagnóstico → Opción 2: Prueba básica
# Debe mostrar 5 lecturas exitosas
```

### 3. Uso Normal

```python
from bh1750_simple import BH1750Simple

# Inicializar
sensor = BH1750Simple()

# Lectura única
lux = sensor.read_lux()
print(f"Luz: {lux} lux")

# Con interpretación
reading = sensor.quick_reading()
print(f"Condición: {reading['descripcion']}")
```

## 📊 Interpretación de Valores

| Rango (lux)  | Condición        | Descripción            | Para Plantas                |
| ------------ | ---------------- | ---------------------- | --------------------------- |
| < 10         | 🌑 Muy oscuro    | Noche sin luna         | Luz artificial necesaria    |
| 10-100       | 🌙 Oscuro        | Interior tenue         | Plantas de muy poca luz     |
| 100-500      | 💡 Interior      | Habitación normal      | Plantas de sombra           |
| 500-1,000    | 🏢 Brillante     | Interior muy iluminado | Mayoría de plantas interior |
| 1,000-5,000  | 🌤️ Nublado       | Exterior día nublado   | Excelente para plantas      |
| 5,000-25,000 | ☀️ Soleado       | Día soleado normal     | Óptimo para plantas de sol  |
| > 25,000     | 🔆 Muy brillante | Sol directo intenso    | Proteger plantas sensibles  |

## 🛠️ Solución de Problemas

### ❌ Sensor no detectado en I2C

**Síntomas**: `scan_i2c_bus()` no muestra 0x23

**Soluciones**:

1. ✅ Verificar conexiones VCC y GND
2. ✅ Comprobar cables SDA y SCL
3. ✅ Probar con cables más cortos
4. ✅ Verificar que VCC = 3.3V (NO 5V)

### ❌ Lecturas erráticas o None

**Síntomas**: Valores `None` o muy variables

**Soluciones**:

1. ✅ Ejecutar `diagnostico_bh1750.py` → Opción 4: Estabilidad
2. ✅ Verificar iluminación estable durante pruebas
3. ✅ Comprobar calidad de conexiones
4. ✅ Evitar interferencias electromagnéticas

### ❌ Valores fuera de rango esperado

**Síntomas**: Lecturas no coherentes con luz visible

**Soluciones**:

1. ✅ Limpiar superficie del sensor
2. ✅ Verificar que no hay objetos bloqueando
3. ✅ Ejecutar test de respuesta (Diagnóstico → Opción 3)

## 💡 Integración con Huerta Inteligente

### Automatización de Riego

```python
def should_water_based_on_light(lux_value, soil_humidity):
    """Decide riego considerando luz y humedad del suelo"""

    if lux_value < 100:  # Poca luz
        return soil_humidity < 30  # Regar menos frecuente
    elif lux_value > 10000:  # Mucha luz
        return soil_humidity < 50  # Regar más frecuente
    else:
        return soil_humidity < 40  # Riego normal
```

### Control de Iluminación LED

```python
def led_intensity_needed(current_lux, target_lux=1000):
    """Calcula intensidad LED necesaria"""

    if current_lux < target_lux:
        deficit = target_lux - current_lux
        led_intensity = min(100, (deficit / target_lux) * 100)
        return led_intensity
    return 0  # No necesita LED
```

### Logging de Datos

```python
def log_light_data(sensor):
    """Registra datos de luz para análisis"""

    reading = sensor.quick_reading()

    data = {
        'timestamp': reading['timestamp'],
        'lux': reading['lux'],
        'condition': reading['nivel'],
        'recommendation': reading['recomendacion']
    }

    # Guardar en archivo o base de datos
    return data
```

## 📈 Monitoreo Avanzado

### Script de Monitoreo 24/7

```python
# Monitoreo continuo con guardado de datos
sensor = BH1750Simple()

while True:
    reading = sensor.quick_reading()

    # Guardar datos cada 5 minutos
    log_light_data(reading)

    # Alertas automáticas
    if reading['lux'] and reading['lux'] > 50000:
        print("⚠️ Luz muy intensa - activar sombra")

    time.sleep(300)  # 5 minutos
```

### Gráficos de Luz Diaria

```python
# Registrar curva de luz durante el día
import matplotlib.pyplot as plt

def plot_daily_light():
    # Recopilar datos cada 30 min durante 24h
    # Generar gráfico de intensidad vs tiempo
    pass
```

## 🔧 Configuración Avanzada

### Cambio de Dirección I2C

```python
# Para usar dirección 0x5C en lugar de 0x23
# Conectar pin ADDR a VCC
sensor = BH1750Simple()
sensor.BH1750_ADDR = 0x5C  # Cambiar dirección
```

### Múltiples Sensores

```python
# Usar varios sensores BH1750 simultaneamente
sensor_interior = BH1750Simple()  # ADDR = GND (0x23)
sensor_exterior = BH1750Simple()  # ADDR = VCC (0x5C)
sensor_exterior.BH1750_ADDR = 0x5C
```

## 📚 Referencias

- **Datasheet**: [BH1750 Official Datasheet](https://www.mouser.com/datasheet/2/348/bh1750fvi-e-186247.pdf)
- **Módulo GY-30**: Breakout board popular del BH1750
- **I2C Protocol**: Protocolo de comunicación estándar
- **Lux vs Lumens**: Lux mide iluminancia, lumens miden flujo luminoso

## 🤝 Contribuir

¿Encontraste un problema o tienes una mejora?

1. 📝 Documenta el issue con detalles
2. 🧪 Incluye resultados del diagnóstico
3. 💡 Propón soluciones o mejoras
4. 🔧 Prueba en tu configuración

---

> **💡 Tip**: Siempre ejecuta el diagnóstico antes de reportar problemas. Incluye los resultados en tu reporte.

**Proyecto**: La Huertica - Sistema de Huerta Inteligente  
**Sensor**: BH1750 (GY-30) - Medición de Intensidad Luminosa
