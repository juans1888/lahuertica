# 🗂️ Estructura de Directorios - La Huertica

## 📁 Organización Completa del Proyecto

```
server/
├── README.md                           # Documentación principal del servidor
├──
├── 🌡️ humedad_aire_dht22/
│   ├── README.md                       # Documentación específica DHT22
│   ├── verificar_libreria_dht22.py     # Verificación de soporte MicroPython
│   ├── diagnostico_dht22.py           # Sistema de diagnóstico completo
│   ├── validacion_dht22.py            # Sistema de validación automática
│   └── dht22.py                       # Sistema completo de producción
│
├── 💧 humedad_tierra_HW080/
│   ├── README.md                       # Documentación específica HW-080
│   ├── diagnostico_hw080.py           # Sistema de diagnóstico completo
│   ├── calibracion_hw080.py           # Sistema de calibración automática
│   └── humedad_hw080.py               # Sistema completo calibrado
│
├── 💡 sensor_luz_bh1750/              # 🆕 NUEVA CARPETA
│   ├── README.md                       # Documentación específica BH1750
│   ├── diagnostico_bh1750.py          # Sistema de diagnóstico completo
│   ├── validacion_bh1750.py           # Sistema de validación automática
│   └── bh1750_complete.py             # Sistema completo de producción
│
└── BH1750.py                          # Archivo básico "Hello World" (mover a carpeta)
```

## 🔄 Migración Recomendada

### Paso 1: Crear Nueva Estructura

```bash
# Crear carpeta para sensor de luz
mkdir server/sensor_luz_bh1750

# Mover archivo básico existente
mv server/BH1750.py server/sensor_luz_bh1750/

# Crear nuevos archivos del sistema completo
touch server/sensor_luz_bh1750/README.md
touch server/sensor_luz_bh1750/diagnostico_bh1750.py
touch server/sensor_luz_bh1750/validacion_bh1750.py
touch server/sensor_luz_bh1750/bh1750_complete.py
```

### Paso 2: Implementar Archivos

Copiar el contenido de los artifacts creados a cada archivo correspondiente.

## 📊 Comparativa de Sistemas por Sensor

| Característica       | DHT22 🌡️          | HW-080 💧         | BH1750 💡      |
| -------------------- | ----------------- | ----------------- | -------------- |
| **Tipo**             | Temp/Humedad Aire | Humedad Suelo     | Intensidad Luz |
| **Protocolo**        | 1-Wire Digital    | Analógico/Digital | I2C Digital    |
| **Diagnóstico**      | ✅ Completo       | ✅ Completo       | ✅ Completo    |
| **Validación**       | ✅ Automática     | ⚠️ Manual         | ✅ Automática  |
| **Calibración**      | 🎯 Offset         | 🎯 Seco/Húmedo    | 🎯 Automática  |
| **Producción**       | ✅ Avanzado       | ✅ Calibrado      | ✅ Completo    |
| **Auto-Modo**        | ❌                | ❌                | ✅             |
| **Análisis Plantas** | ✅                | ✅                | ✅             |

## 🚀 Guía de Implementación por Fases

### Fase 1: Verificación Básica (Todos los Sensores)

```python
# Para cada sensor, ejecutar:
python diagnostico_[sensor].py
# Seleccionar: "1. Prueba básica de funcionamiento"
```

### Fase 2: Validación Completa

```python
# DHT22 - Validación con offset
python validacion_dht22.py

# HW-080 - Calibración personalizada
python calibracion_hw080.py

# BH1750 - Validación automática
python validacion_bh1750.py
```

### Fase 3: Sistema de Producción

```python
# Ejecutar sistema completo de cada sensor
python dht22.py              # Ambiente
python humedad_hw080.py      # Suelo
python bh1750_complete.py    # Luz
```

## 🔗 Integración de Sensores

### Sistema Integrado Completo

```python
"""
Sistema maestro que integra los 3 sensores
"""
from humedad_aire_dht22.dht22 import DHT22EnvironmentalSensor
from humedad_tierra_HW080.humedad_hw080 import HW080FinalCalibrated
from sensor_luz_bh1750.bh1750_complete import BH1750LightSensor

class HuertaInteligente:
    def __init__(self):
        # Inicializar sensores
        self.ambiente = DHT22EnvironmentalSensor(data_pin=15)
        self.suelo = HW080FinalCalibrated(adc_pin=26, digital_pin=16)
        self.luz = BH1750LightSensor(sda_pin=0, scl_pin=1)

    def get_complete_status(self):
        """Obtener estado completo de la huerta"""
        return {
            'ambiente': self.ambiente.get_environmental_status(),
            'suelo': self.suelo.get_complete_reading(),
            'luz': self.luz.get_light_status(),
            'timestamp': time.time()
        }

    def generate_recommendations(self):
        """Generar recomendaciones basadas en todos los sensores"""
        status = self.get_complete_status()

        recommendations = []

        # Análisis integrado
        if status['luz']['light_data']['intensity_lux'] < 1000:
            recommendations.append("💡 Aumentar iluminación")

        if status['suelo']['humidity_percentage'] < 30:
            recommendations.append("💧 Riego necesario")

        if status['ambiente']['environmental_data']['humidity'] > 80:
            recommendations.append("🌬️ Mejorar ventilación")

        return recommendations
```

## 📈 Roadmap de Desarrollo

### ✅ Completado

- [x] Sistema DHT22 completo con validación y offset
- [x] Sistema HW-080 con calibración automática
- [x] Sistema BH1750 completo con modo automático
- [x] Documentación completa para cada sensor
- [x] Herramientas de diagnóstico unificadas

### 🔄 En Desarrollo

- [ ] Sistema maestro integrado
- [ ] API REST para acceso remoto
- [ ] Dashboard web en tiempo real
- [ ] Base de datos histórica
- [ ] Alertas automáticas

### 🎯 Futuro

- [ ] Machine Learning para predicciones
- [ ] Control automático de riego
- [ ] Integración con apps móviles
- [ ] Sensores adicionales (pH, EC, CO2)

## 🛠️ Herramientas de Desarrollo

### Scripts de Utilidad

```bash
# Diagnóstico rápido de todos los sensores
python -c "
import os
os.system('python humedad_aire_dht22/diagnostico_dht22.py')
os.system('python humedad_tierra_HW080/diagnostico_hw080.py')
os.system('python sensor_luz_bh1750/diagnostico_bh1750.py')
"

# Validación completa del sistema
python -c "
print('🌡️ Validando DHT22...')
# exec(open('humedad_aire_dht22/validacion_dht22.py').read())
print('💧 Calibrando HW-080...')
# exec(open('humedad_tierra_HW080/calibracion_hw080.py').read())
print('💡 Validando BH1750...')
# exec(open('sensor_luz_bh1750/validacion_bh1750.py').read())
"
```

### Configuración de Desarrollo

```python
# config.py - Configuración centralizada
SENSOR_CONFIG = {
    'dht22': {
        'pin': 15,
        'enable_offset': True,
        'temp_offset': 0.0,
        'humid_offset': 0.0
    },
    'hw080': {
        'adc_pin': 26,
        'digital_pin': 16,
        'dry_value': 65535,
        'wet_value': 26221
    },
    'bh1750': {
        'sda_pin': 0,
        'scl_pin': 1,
        'addr': 0x23,
        'auto_mode': True
    }
}
```

## 📚 Documentación Adicional

### Manuales por Sensor

- **[DHT22](humedad_aire_dht22/README.md)**: Sensor de temperatura y humedad ambiental
- **[HW-080](humedad_tierra_HW080/README.md)**: Sensor de humedad del suelo
- **[BH1750](sensor_luz_bh1750/README.md)**: Sensor de intensidad luminosa

### Guías Técnicas

- **Calibración**: Procedimientos de calibración para cada sensor
- **Solución de Problemas**: Diagnóstico y resolución de fallos comunes
- **Integración**: Cómo combinar múltiples sensores
- **Automatización**: Sistemas de control automático

## 🤖 Automatización Avanzada

### Control Inteligente de Huerta

```python
class ControladorHuerta:
    def __init__(self, huerta):
        self.huerta = huerta
        self.thresholds = {
            'luz_min': 5000,      # lux mínimos
            'humedad_suelo_min': 40,  # % mínimo suelo
            'temp_max': 30,       # °C máxima
            'humedad_aire_max': 85    # % máximo aire
        }

    def run_automation_cycle(self):
        """Ejecutar ciclo de automatización"""
        status = self.huerta.get_complete_status()
        actions = []

        # Control de iluminación
        if status['luz']['light_data']['intensity_lux'] < self.thresholds['luz_min']:
            actions.append(self.activate_grow_lights())

        # Control de riego
        if status['suelo']['humidity_percentage'] < self.thresholds['humedad_suelo_min']:
            actions.append(self.activate_irrigation())

        # Control de temperatura
        if status['ambiente']['environmental_data']['temperature'] > self.thresholds['temp_max']:
            actions.append(self.activate_cooling())

        # Control de humedad
        if status['ambiente']['environmental_data']['humidity'] > self.thresholds['humedad_aire_max']:
            actions.append(self.activate_ventilation())

        return actions
```

---

🎉 **¡Sistema Completo de Sensores Implementado!**

Con esta estructura, tienes un sistema robusto y escalable para monitoreo completo de huerta inteligente con tres sensores fundamentales: ambiente, suelo y luz.
