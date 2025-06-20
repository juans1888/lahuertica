"""
🔧 Código de diagnóstico para sensor BH1750 (GY-30)
Verifica funcionamiento, conectividad I2C y detecta problemas comunes
"""

from machine import Pin, I2C
import utime
import gc


class BH1750Diagnostics:
    """
    Clase para diagnóstico completo del sensor BH1750 (GY-30)
    """

    def __init__(self, sda_pin=0, scl_pin=1, i2c_freq=100000):
        """
        Inicializa el diagnóstico del BH1750

        Args:
            sda_pin (int): Pin SDA del I2C (por defecto 0)
            scl_pin (int): Pin SCL del I2C (por defecto 1)
            i2c_freq (int): Frecuencia I2C (por defecto 100000)
        """
        try:
            self.sda_pin = sda_pin
            self.scl_pin = scl_pin
            self.i2c_freq = i2c_freq

            # Constantes del BH1750
            self.BH1750_ADDR = 0x23
            self.BH1750_CMD_POWER_ON = 0x01
            self.BH1750_CMD_RESET = 0x07
            self.BH1750_CMD_CONTINUOUS_HIGH_RES = 0x10

            # Inicializar I2C
            self.i2c = I2C(0, sda=Pin(sda_pin), scl=Pin(scl_pin), freq=i2c_freq)

            print(f"💡 Sensor BH1750 (GY-30) inicializado")
            print(f"🔌 I2C: SDA=GPIO{sda_pin}, SCL=GPIO{scl_pin}, Freq={i2c_freq}Hz")
            print(f"📍 Dirección: 0x{self.BH1750_ADDR:02X}")
            print("⚠️  IMPORTANTE: Verificar conexiones VCC, GND, SDA, SCL")

        except Exception as e:
            print(f"❌ Error inicializando diagnóstico BH1750: {e}")
            raise

    def scan_i2c_bus(self):
        """
        Escanea el bus I2C para detectar dispositivos conectados

        Returns:
            list: Lista de direcciones I2C encontradas
        """
        try:
            print("\n🔍 ESCANEANDO BUS I2C...")
            devices = self.i2c.scan()

            print(f"📡 Dispositivos encontrados: {len(devices)}")

            if devices:
                for addr in devices:
                    device_name = (
                        "BH1750 (GY-30)" if addr == self.BH1750_ADDR else "Desconocido"
                    )
                    print(f"   📍 0x{addr:02X} - {device_name}")
            else:
                print("❌ No se encontraron dispositivos en el bus I2C")

            return devices

        except Exception as e:
            print(f"❌ Error escaneando I2C: {e}")
            return []

    def check_sensor_presence(self):
        """
        Verifica si el sensor BH1750 está presente en el bus I2C

        Returns:
            bool: True si el sensor está presente
        """
        try:
            devices = self.scan_i2c_bus()

            if self.BH1750_ADDR in devices:
                print(f"✅ BH1750 detectado en dirección 0x{self.BH1750_ADDR:02X}")
                return True
            else:
                print(f"❌ BH1750 NO detectado en dirección 0x{self.BH1750_ADDR:02X}")
                print("🔧 Verificar:")
                print("   • Conexiones VCC (3.3V), GND")
                print("   • Conexiones SDA y SCL")
                print("   • Pin ADDR (flotante = 0x23, GND = 0x23, VCC = 0x5C)")
                return False

        except Exception as e:
            print(f"❌ Error verificando presencia: {e}")
            return False

    def initialize_sensor(self):
        """
        Inicializa el sensor BH1750 con comandos básicos

        Returns:
            bool: True si la inicialización fue exitosa
        """
        try:
            print("\n🔧 INICIALIZANDO SENSOR...")

            # Verificar presencia primero
            if not self.check_sensor_presence():
                return False

            # Encender el sensor
            print("   📡 Enviando comando POWER_ON...")
            self.i2c.writeto(self.BH1750_ADDR, bytes([self.BH1750_CMD_POWER_ON]))
            utime.sleep_ms(10)

            # Resetear el sensor
            print("   🔄 Enviando comando RESET...")
            self.i2c.writeto(self.BH1750_ADDR, bytes([self.BH1750_CMD_RESET]))
            utime.sleep_ms(10)

            # Configurar modo continuo de alta resolución
            print("   ⚙️ Configurando modo alta resolución...")
            self.i2c.writeto(
                self.BH1750_ADDR, bytes([self.BH1750_CMD_CONTINUOUS_HIGH_RES])
            )
            utime.sleep_ms(180)  # Esperar primera medición

            print("✅ Sensor inicializado correctamente")
            return True

        except OSError as e:
            print(f"❌ Error de comunicación I2C: {e}")
            print("🔧 Verificar conexiones físicas")
            return False
        except Exception as e:
            print(f"❌ Error inicializando sensor: {e}")
            return False

    def single_reading(self):
        """
        Realiza una lectura individual del sensor

        Returns:
            dict: Resultado de la lectura con estado
        """
        try:
            gc.collect()  # Limpiar memoria

            # Leer 2 bytes del sensor
            data = self.i2c.readfrom(self.BH1750_ADDR, 2)

            # Convertir a valor en lux
            raw_value = (data[0] << 8) | data[1]
            lux_value = raw_value / 1.2

            return {
                "success": True,
                "lux": lux_value,
                "raw_value": raw_value,
                "data_bytes": data,
                "error": None,
                "timestamp": utime.time(),
            }

        except OSError as e:
            return {
                "success": False,
                "lux": None,
                "raw_value": None,
                "data_bytes": None,
                "error": f"Error comunicación I2C: {e}",
                "timestamp": utime.time(),
            }
        except Exception as e:
            return {
                "success": False,
                "lux": None,
                "raw_value": None,
                "data_bytes": None,
                "error": f"Error general: {e}",
                "timestamp": utime.time(),
            }

    def test_basic_functionality(self):
        """
        Prueba básica de funcionamiento del sensor
        """
        print("\n🧪 PRUEBA BÁSICA DE FUNCIONAMIENTO")
        print("-" * 45)

        # Inicializar sensor
        if not self.initialize_sensor():
            print("❌ No se pudo inicializar el sensor")
            return False

        # Intentar 5 lecturas básicas
        successful_readings = 0
        failed_readings = 0
        lux_values = []

        print("\nRealizando 5 lecturas de prueba...")
        print("Lectura\t\tLux\t\tRaw\t\tEstado")
        print("-" * 50)

        for i in range(5):
            result = self.single_reading()

            if result["success"]:
                lux = result["lux"]
                raw = result["raw_value"]
                print(f"{i+1}\t\t{lux:6.1f}\t\t{raw}\t\t✅")
                successful_readings += 1
                lux_values.append(lux)
            else:
                print(f"{i+1}\t\t---\t\t---\t\t❌ {result['error'][:20]}...")
                failed_readings += 1

            utime.sleep(1)  # Esperar entre lecturas

        # Resultado de la prueba
        success_rate = (successful_readings / 5) * 100

        print(f"\n📊 RESULTADO:")
        print(f"✅ Lecturas exitosas: {successful_readings}/5 ({success_rate:.0f}%)")
        print(f"❌ Lecturas fallidas: {failed_readings}/5")

        if lux_values:
            avg_lux = sum(lux_values) / len(lux_values)
            min_lux = min(lux_values)
            max_lux = max(lux_values)
            print(f"💡 Promedio: {avg_lux:.1f} lux")
            print(f"💡 Rango: {min_lux:.1f} - {max_lux:.1f} lux")

        if success_rate >= 80:
            print("🎉 Sensor funcionando CORRECTAMENTE")
            return True
        elif success_rate >= 60:
            print("⚠️  Sensor funcionando con PROBLEMAS menores")
            return True
        else:
            print("🚫 Sensor con PROBLEMAS graves")
            return False

    def light_response_test(self):
        """
        Prueba de respuesta a cambios de luz
        """
        print("\n💡 PRUEBA DE RESPUESTA A CAMBIOS DE LUZ")
        print("-" * 50)
        print("Esta prueba verifica que el sensor responda a cambios de iluminación")
        print("\n📋 INSTRUCCIONES:")
        print("1. Deja el sensor en condiciones normales de luz")
        print("2. Cuando se indique, cubre el sensor con la mano")
        print("3. Luego destápalo y ponlo bajo luz brillante")

        input("\nPresiona ENTER para comenzar...")

        if not self.initialize_sensor():
            return False

        # Lectura base
        print("\n📊 Tomando lectura base (luz normal)...")
        base_result = self.single_reading()

        if not base_result["success"]:
            print(f"❌ Error en lectura base: {base_result['error']}")
            return False

        base_lux = base_result["lux"]
        print(f"💡 Luz base: {base_lux:.1f} lux")

        # Prueba con sensor cubierto
        input("\n👋 CUBRE el sensor con la mano y presiona ENTER...")

        utime.sleep(1)  # Estabilizar
        dark_result = self.single_reading()

        if dark_result["success"]:
            dark_lux = dark_result["lux"]
            print(f"🌑 Luz cubierta: {dark_lux:.1f} lux")

            # Verificar reducción significativa
            reduction = ((base_lux - dark_lux) / base_lux) * 100 if base_lux > 0 else 0

            if reduction > 50:
                print(f"✅ Buena respuesta a oscuridad (-{reduction:.0f}%)")
            elif reduction > 20:
                print(f"⚠️  Respuesta moderada a oscuridad (-{reduction:.0f}%)")
            else:
                print(f"❌ Poca respuesta a oscuridad (-{reduction:.0f}%)")
        else:
            print(f"❌ Error en lectura oscura: {dark_result['error']}")

        # Prueba con luz brillante
        input(
            "\n💡 DESTAPA el sensor y ponlo bajo LUZ BRILLANTE, luego presiona ENTER..."
        )

        utime.sleep(1)  # Estabilizar
        bright_result = self.single_reading()

        if bright_result["success"]:
            bright_lux = bright_result["lux"]
            print(f"☀️ Luz brillante: {bright_lux:.1f} lux")

            # Verificar aumento significativo
            if bright_lux > base_lux:
                increase = ((bright_lux - base_lux) / base_lux) * 100
                print(f"✅ Buena respuesta a luz brillante (+{increase:.0f}%)")
            else:
                print(f"⚠️  No se detectó aumento de luz")
        else:
            print(f"❌ Error en lectura brillante: {bright_result['error']}")

        print(f"\n🎯 EVALUACIÓN DE RESPUESTA:")
        if (
            dark_result["success"]
            and bright_result["success"]
            and dark_lux < base_lux < bright_lux
        ):
            print("✅ Sensor responde correctamente a cambios de luz")
            return True
        else:
            print("❌ Sensor no responde adecuadamente a cambios de luz")
            return False

    def stability_test(self, duration_minutes=2):
        """
        Prueba de estabilidad durante un período

        Args:
            duration_minutes (int): Duración de la prueba en minutos
        """
        print(f"\n⏱️  PRUEBA DE ESTABILIDAD - {duration_minutes} minutos")
        print("-" * 50)
        print("Mantén condiciones de luz constantes durante la prueba")
        print("\nTiempo\t\tLux\t\tRaw\t\tEstado")
        print("-" * 50)

        if not self.initialize_sensor():
            return False

        start_time = utime.time()
        end_time = start_time + (duration_minutes * 60)

        readings = []
        error_count = 0

        try:
            while utime.time() < end_time:
                elapsed = (utime.time() - start_time) / 60

                result = self.single_reading()

                if result["success"]:
                    lux = result["lux"]
                    raw = result["raw_value"]

                    print(f"{elapsed:5.1f}m\t\t{lux:6.1f}\t\t{raw}\t\t✅")

                    readings.append({"time": elapsed, "lux": lux, "raw": raw})
                else:
                    print(
                        f"{elapsed:5.1f}m\t\t---\t\t---\t\t❌ {result['error'][:15]}..."
                    )
                    error_count += 1

                utime.sleep(5)  # Lectura cada 5 segundos

        except KeyboardInterrupt:
            print("\n⏹️  Prueba detenida por usuario")

        # Análisis de estabilidad
        self.analyze_stability(readings, error_count)

    def analyze_stability(self, readings, error_count):
        """
        Analiza la estabilidad de las lecturas

        Args:
            readings (list): Lista de lecturas válidas
            error_count (int): Número de errores
        """
        if not readings:
            print("\n❌ No hay lecturas válidas para analizar")
            return

        # Extraer datos
        lux_values = [r["lux"] for r in readings]
        raw_values = [r["raw"] for r in readings]

        # Estadísticas
        lux_avg = sum(lux_values) / len(lux_values)
        lux_min = min(lux_values)
        lux_max = max(lux_values)
        lux_range = lux_max - lux_min

        raw_avg = sum(raw_values) / len(raw_values)
        raw_min = min(raw_values)
        raw_max = max(raw_values)
        raw_range = raw_max - raw_min

        # Calcular coeficiente de variación
        if lux_avg > 0:
            lux_variance = sum([(l - lux_avg) ** 2 for l in lux_values]) / len(
                lux_values
            )
            lux_std = lux_variance**0.5
            lux_cv = (lux_std / lux_avg) * 100
        else:
            lux_cv = 0

        print(f"\n📈 ANÁLISIS DE ESTABILIDAD:")
        print(f"📊 Lecturas válidas: {len(readings)}")
        print(f"❌ Errores: {error_count}")

        print(f"\n💡 INTENSIDAD LUMINOSA:")
        print(f"   Promedio: {lux_avg:.1f} lux")
        print(f"   Rango: {lux_min:.1f} - {lux_max:.1f} lux")
        print(f"   Variación: {lux_range:.1f} lux")
        print(f"   Coef. variación: {lux_cv:.1f}%")

        print(f"\n📊 VALORES RAW:")
        print(f"   Promedio: {raw_avg:.0f}")
        print(f"   Rango: {raw_min} - {raw_max}")
        print(f"   Variación: {raw_range}")

        # Evaluación de estabilidad
        if lux_cv < 5:
            stability_rating = "EXCELENTE"
        elif lux_cv < 10:
            stability_rating = "BUENA"
        elif lux_cv < 20:
            stability_rating = "REGULAR"
        else:
            stability_rating = "POBRE"

        print(f"\n🎯 ESTABILIDAD: {stability_rating}")

        # Evaluación general
        total_readings = len(readings) + error_count
        success_rate = (
            (len(readings) / total_readings) * 100 if total_readings > 0 else 0
        )

        print(f"🎯 Tasa de éxito: {success_rate:.1f}%")

        if success_rate >= 90 and lux_cv < 10:
            print("🟢 SENSOR EXCELENTE - Listo para uso")
        elif success_rate >= 75 and lux_cv < 20:
            print("🟡 SENSOR BUENO - Aceptable para uso")
        else:
            print("🔴 SENSOR PROBLEMÁTICO - Revisar conexiones")

    def check_light_ranges(self):
        """
        Verifica rangos típicos de luz en diferentes condiciones
        """
        print("\n🌍 VERIFICACIÓN DE RANGOS DE LUZ")
        print("-" * 40)

        if not self.initialize_sensor():
            return False

        result = self.single_reading()

        if not result["success"]:
            print(f"❌ No se pudo verificar: {result['error']}")
            return False

        lux = result["lux"]

        print(f"💡 Lectura actual: {lux:.1f} lux")

        # Clasificar tipo de iluminación
        if lux < 0.1:
            light_type = "🌑 Muy oscuro"
            description = "Noche sin luna"
        elif lux < 1:
            light_type = "🌙 Oscuro"
            description = "Noche con luna llena"
        elif lux < 10:
            light_type = "🏠 Muy tenue"
            description = "Habitación con velas"
        elif lux < 50:
            light_type = "💡 Tenue"
            description = "Habitación con luz artificial tenue"
        elif lux < 200:
            light_type = "🏢 Interior normal"
            description = "Oficina o habitación iluminada"
        elif lux < 500:
            light_type = "🏢 Interior brillante"
            description = "Oficina muy iluminada"
        elif lux < 1000:
            light_type = "🌤️ Exterior nublado"
            description = "Día nublado"
        elif lux < 10000:
            light_type = "☀️ Exterior soleado"
            description = "Día soleado típico"
        elif lux < 50000:
            light_type = "☀️ Muy brillante"
            description = "Día muy soleado"
        else:
            light_type = "🔆 Extremadamente brillante"
            description = "Sol directo o luz artificial muy intensa"

        print(f"🏷️  Tipo: {light_type}")
        print(f"📝 Descripción: {description}")

        # Verificar si está en rango del sensor
        if 0.1 <= lux <= 65535:
            print("✅ Dentro del rango óptimo del sensor")
        elif lux < 0.1:
            print("⚠️  Por debajo del rango mínimo (pero normal en oscuridad)")
        else:
            print("⚠️  Cerca del límite máximo del sensor")

        return True

    def connection_troubleshooting(self):
        """
        Guía de solución de problemas de conexión
        """
        print("\n🔧 SOLUCIÓN DE PROBLEMAS DE CONEXIÓN")
        print("-" * 50)

        print("📋 VERIFICACIONES PASO A PASO:")

        print("\n1. 🔌 Conexiones físicas:")
        print("   ✓ VCC → 3.3V del Raspberry Pi")
        print("   ✓ GND → GND del Raspberry Pi")
        print("   ✓ SDA → GPIO0 (pin 1)")
        print("   ✓ SCL → GPIO1 (pin 2)")
        print("   ✓ ADDR → Sin conectar (o a GND para dir 0x23)")

        print("\n2. 🔍 Escaneo I2C:")
        devices = self.scan_i2c_bus()

        if not devices:
            print("\n❌ PROBLEMA: No se detectan dispositivos I2C")
            print("🔧 Soluciones:")
            print("   • Verificar todas las conexiones")
            print("   • Comprobar que VCC esté a 3.3V")
            print("   • Verificar continuidad de cables")
            print("   • Probar con cables más cortos")

        elif self.BH1750_ADDR not in devices:
            print(f"\n❌ PROBLEMA: BH1750 no en dirección 0x{self.BH1750_ADDR:02X}")
            print("🔧 Soluciones:")
            print("   • Verificar pin ADDR del módulo")
            print("   • Probar dirección 0x5C (ADDR a VCC)")
            print("   • Verificar integridad del módulo")

        else:
            print("\n✅ Dispositivo I2C detectado correctamente")

        print("\n3. ⚡ Alimentación:")
        print("   • Verificar que VCC = 3.3V (NO 5V)")
        print("   • Comprobar consumo de corriente normal")
        print("   • Verificar que GND esté bien conectado")

        print("\n4. 📡 Comunicación:")
        if devices and self.BH1750_ADDR in devices:
            print("   ✅ Comunicación I2C establecida")

            # Probar inicialización
            try:
                self.initialize_sensor()
                print("   ✅ Inicialización exitosa")
            except:
                print("   ❌ Error en inicialización")
                print("   🔧 Verificar integridad del sensor")
        else:
            print("   ❌ Sin comunicación I2C")


def diagnostic_menu():
    """
    Menú interactivo para diagnóstico del BH1750
    """
    print("\n" + "=" * 60)
    print("💡 DIAGNÓSTICO SENSOR BH1750 (GY-30)")
    print("=" * 60)

    # Configuración de pines
    try:
        sda_input = input("Pin SDA (por defecto 0): ").strip()
        sda_pin = int(sda_input) if sda_input else 0

        scl_input = input("Pin SCL (por defecto 1): ").strip()
        scl_pin = int(scl_input) if scl_input else 1
    except ValueError:
        sda_pin, scl_pin = 0, 1
        print(f"Usando pines por defecto: SDA={sda_pin}, SCL={scl_pin}")

    try:
        sensor = BH1750Diagnostics(sda_pin=sda_pin, scl_pin=scl_pin)

        while True:
            print("\n" + "-" * 45)
            print("💡 OPCIONES DE DIAGNÓSTICO:")
            print("-" * 45)
            print("1. 🔍 Escanear bus I2C")
            print("2. 🧪 Prueba básica de funcionamiento")
            print("3. 💡 Prueba de respuesta a luz")
            print("4. ⏱️  Prueba de estabilidad (2 min)")
            print("5. 🌍 Verificación de rangos de luz")
            print("6. 📊 Lectura única")
            print("7. 🔄 Lecturas continuas")
            print("8. 🔧 Solución de problemas")
            print("9. 🚪 Salir")

            option = input("\nSelecciona (1-9): ").strip()

            if option == "1":
                sensor.scan_i2c_bus()

            elif option == "2":
                sensor.test_basic_functionality()

            elif option == "3":
                sensor.light_response_test()

            elif option == "4":
                duration = input("Duración en minutos (por defecto 2): ").strip()
                duration = int(duration) if duration.isdigit() else 2
                sensor.stability_test(duration)

            elif option == "5":
                sensor.check_light_ranges()

            elif option == "6":
                if sensor.initialize_sensor():
                    result = sensor.single_reading()
                    if result["success"]:
                        print(f"💡 Intensidad: {result['lux']:.1f} lux")
                        print(f"📊 Raw: {result['raw_value']}")
                    else:
                        print(f"❌ Error: {result['error']}")

            elif option == "7":
                print("📊 Lecturas continuas cada 2s (Ctrl+C para parar)")
                if sensor.initialize_sensor():
                    try:
                        while True:
                            result = sensor.single_reading()
                            if result["success"]:
                                lux = result["lux"]
                                raw = result["raw_value"]
                                print(f"💡 {lux:8.1f} lux | Raw: {raw:5d}")
                            else:
                                print(f"❌ {result['error']}")
                            utime.sleep(2)
                    except KeyboardInterrupt:
                        print("\n⏹️  Lecturas detenidas")

            elif option == "8":
                sensor.connection_troubleshooting()

            elif option == "9":
                print("👋 Saliendo del diagnóstico...")
                break

            else:
                print("❌ Opción no válida")

    except Exception as e:
        print(f"❌ Error en diagnóstico: {e}")
        print("🔧 Verificar conexiones y configuración")


if __name__ == "__main__":
    diagnostic_menu()
