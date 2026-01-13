#!/usr/bin/env python
"""
Script de inicio rápido para la aplicación Extractor de PDFs.
Ejecuta este archivo para iniciar la aplicación Streamlit automáticamente.
"""

import subprocess
import sys
import os
from pathlib import Path

def check_requirements():
    """Verifica que las dependencias estén instaladas."""
    try:
        import streamlit
        import pandas
        import pdfplumber
        print("✅ Dependencias verificadas correctamente")
        return True
    except ImportError as e:
        print(f"❌ Falta instalar dependencias: {e}")
        print("Ejecuta: pip install -r requirements.txt")
        return False

def check_structure():
    """Verifica que la estructura del proyecto esté correcta."""
    required_files = [
        'app.py',
        'src/templates/__init__.py',
        'src/templates/template_base.py',
        'src/templates/vida_laboral_template.py',
        'requirements.txt'
    ]

    missing = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing.append(file_path)

    if missing:
        print("❌ Archivos faltantes:")
        for file in missing:
            print(f"   - {file}")
        return False

    print("✅ Estructura del proyecto verificada")
    return True

def main():
    """Función principal."""
    print("🚀 Iniciando Extractor de PDFs...")
    print("=" * 50)

    # Verificar estructura
    if not check_structure():
        sys.exit(1)

    # Verificar dependencias
    if not check_requirements():
        sys.exit(1)

    print("\n📊 Iniciando aplicación Streamlit...")
    print("🔗 Una vez iniciada, abre: http://localhost:8501")
    print("🛑 Presiona Ctrl+C para detener")
    print("-" * 50)

    try:
        # Ejecutar Streamlit
        cmd = [sys.executable, "-m", "streamlit", "run", "app.py",
               "--server.headless", "true", "--server.port", "8501"]
        subprocess.run(cmd, check=True)

    except KeyboardInterrupt:
        print("\n\n👋 Aplicación detenida por el usuario")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error ejecutando Streamlit: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
