"""
Verificación de soporte DHT22 en MicroPython
Comprueba que la librería esté disponible
"""


def check_dht_support():
    """
    Verifica si el módulo DHT está disponible en MicroPython

    Returns:
        bool: True si está disponible, False si no
    """
    try:
        import dht

        print("✅ Módulo 'dht' disponible")
        print(
            f"📦 Ubicación: {dht.__file__ if hasattr(dht, '__file__') else 'Módulo nativo'}"
        )
        return True

    except ImportError as e:
        print(f"❌ Error importando módulo 'dht': {e}")
        print("💡 Soluciones posibles:")
        print("   1. Actualizar MicroPython a versión reciente")
        print("   2. Verificar que estés usando MicroPython oficial")
        print("   3. Reinstalar firmware si es necesario")
        return False


def check_machine_support():
    """
    Verifica soporte del módulo machine para pines
    """
    try:
        from machine import Pin

        print("✅ Módulo 'machine.Pin' disponible")
        return True

    except ImportError as e:
        print(f"❌ Error importando 'machine.Pin': {e}")
        return False


def show_dht_info():
    """
    Muestra información sobre los sensores DHT soportados
    """
    try:
        import dht

        print("\n📚 INFORMACIÓN DHT:")
        print("🔸 DHT11: Temperatura ±2°C, Humedad ±5%")
        print("🔸 DHT22: Temperatura ±0.5°C, Humedad ±2-5%")
        print("🔸 Protocolo: 1-Wire digital")
        print("🔸 Tiempo mínimo entre lecturas: 2 segundos")

        # Verificar clases disponibles
        available_classes = []

        if hasattr(dht, "DHT11"):
            available_classes.append("DHT11")
        if hasattr(dht, "DHT22"):
            available_classes.append("DHT22")

        print(f"🔸 Clases disponibles: {', '.join(available_classes)}")

        return available_classes

    except Exception as e:
        print(f"❌ Error obteniendo información DHT: {e}")
        return []


def main():
    """
    Función principal de verificación
    """
    print("🔍 VERIFICANDO SOPORTE DHT22 EN MICROPYTHON")
    print("=" * 50)

    # Verificar módulos básicos
    machine_ok = check_machine_support()
    dht_ok = check_dht_support()

    if machine_ok and dht_ok:
        print("\n🎉 ¡SISTEMA LISTO PARA DHT22!")

        # Mostrar información adicional
        classes = show_dht_info()

        if "DHT22" in classes:
            print("\n✅ DHT22 específicamente soportado")
            print("🚀 Puedes proceder con la configuración")
        else:
            print("\n⚠️  DHT22 no encontrado en clases disponibles")
            print("💡 Verificar versión de MicroPython")

    else:
        print("\n❌ PROBLEMAS DETECTADOS")
        print("🔧 Resolver problemas antes de continuar")

    # Información adicional de sistema
    try:
        import sys

        print(f"\n📋 Información del sistema:")
        print(f"🔸 Plataforma: {sys.platform}")
        print(f"🔸 Implementación: {sys.implementation.name}")

    except Exception as e:
        print(f"No se pudo obtener información del sistema: {e}")


if __name__ == "__main__":
    main()
