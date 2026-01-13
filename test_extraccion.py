"""
Script de prueba para verificar que la extracción funciona correctamente
con la plantilla de Streamlit.
"""

from pathlib import Path
from src.templates import VidaLaboralSecuenciaTemplate  # Template con secuencia completa de scripts
import pandas as pd

def test_extraccion_pdf():
    """Prueba la extracción con un PDF real."""
    
    # Buscar PDF en data/input
    input_dir = Path("data/input")
    pdfs = list(input_dir.glob("*.pdf"))
    
    if not pdfs:
        print("[ERROR] No se encontraron PDFs en data/input/")
        print("Por favor, coloca un PDF de prueba en esa carpeta.")
        return False
    
    pdf_path = pdfs[0]
    print(f"\nProbando con: {pdf_path.name}")
    print("=" * 60)
    
    try:
        # Crear plantilla
        print("\n1. Inicializando plantilla SECUENCIA (usa ambos scripts que funcionan)...")
        template = VidaLaboralSecuenciaTemplate()
        
        # Procesar PDF
        print("2. Procesando PDF...")
        resultado = template.process_pdf(pdf_path)
        
        if not resultado['success']:
            print(f"[ERROR] {resultado.get('error')}")
            return False
        
        # Obtener datos
        df = resultado['data']
        
        print("\n[EXITO] Extraccion exitosa!")
        print(f"\nRESULTADOS:")
        print(f"   - Filas: {len(df)}")
        print(f"   - Columnas: {len(df.columns)}")
        print(f"\nColumnas extraidas:")
        for col in df.columns:
            print(f"   - {col}")
        
        # Verificar columnas importantes
        columnas_esperadas = [
            'Nombre_Apellidos', 'Situacion', 'F_Real_Alta', 
            'T_C', 'G_C_M', 'C_T_P'
        ]
        
        print(f"\nVerificacion de columnas importantes:")
        for col in columnas_esperadas:
            if col in df.columns:
                no_vacios = df[col].notna().sum()
                print(f"   [OK] {col}: {no_vacios} registros con datos")
            else:
                print(f"   [FALTA] {col}: NO ENCONTRADA")
        
        # Mostrar muestra
        print(f"\nMuestra de datos (primeras 3 filas):")
        print(df.head(3).to_string())
        
        # Guardar resultado de prueba
        output_path = Path("data/output/PRUEBA_EXTRACCION.xlsx")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_excel(output_path, index=False)
        print(f"\nResultado guardado en: {output_path}")
        print("   IMPORTANTE: Abre este archivo en Excel y verifica que tiene TODOS los datos correctos")
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("PRUEBA DE EXTRACCIÓN DE PDF")
    print("=" * 60)
    
    success = test_extraccion_pdf()
    
    print("\n" + "=" * 60)
    if success:
        print("[EXITO] PRUEBA EXITOSA")
        print("\nSiguientes pasos:")
        print("1. Abre data/output/PRUEBA_EXTRACCION.xlsx")
        print("2. Verifica que tiene TODOS los datos del PDF")
        print("3. Si falta algo, avisame para ajustar la extraccion")
    else:
        print("[ERROR] PRUEBA FALLIDA")
        print("\nNecesitamos ajustar la extraccion antes de desplegar")
    print("=" * 60 + "\n")

