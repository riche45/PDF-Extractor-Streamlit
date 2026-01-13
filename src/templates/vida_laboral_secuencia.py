"""
Template que ejecuta la secuencia correcta de scripts para generar el archivo final.
Usa los scripts originales que ya funcionaban correctamente.
"""
import pandas as pd
from pathlib import Path
import logging
import subprocess
import re
from typing import Dict, Any

from src.processors.pdf_extractor import PDFExtractor

logger = logging.getLogger(__name__)


class VidaLaboralSecuenciaTemplate:
    """
    Template que ejecuta la secuencia completa de procesamiento:
    1. Extracción PDF -> VIDA LABORAL 2024_SIN_CID.csv
    2. Script reorganizar_datos_completo.py -> VIDA LABORAL 2024_COMPLETO.csv
    3. Script proceso_completo_cliente.py -> VIDA_LABORAL_FINAL_CLIENTE.csv
    """
    
    def __init__(self):
        self.extractor = PDFExtractor()
        
        # Archivos intermedios
        self.raw_output = Path("data/output/VIDA LABORAL 2024_SIN_CID.csv")
        self.completo_output = Path("data/output/VIDA LABORAL 2024_COMPLETO.csv")
        self.final_output = Path("data/output/VIDA_LABORAL_FINAL_CLIENTE.csv")
        
        # Scripts originales
        self.script_reorganizar = Path("reorganizar_datos_completo.py")
        self.script_proceso_cliente = Path("proceso_completo_cliente.py")
    
    def process_pdf(self, pdf_path: Path) -> Dict[str, Any]:
        """
        Procesa el PDF usando la secuencia completa de scripts originales.
        
        IMPORTANTE: Los scripts originales esperan trabajar con el PDF directamente,
        no con un CSV intermedio. Por eso, simplemente copiamos el PDF a la ubicación
        esperada y dejamos que los scripts hagan todo el trabajo.
        """
        try:
            logger.info(f"Iniciando procesamiento completo para: {pdf_path.name}")
            
            # ============================================================
            # PASO 0: Preparar el PDF para los scripts originales
            # ============================================================
            # Los scripts originales esperan el PDF en data/input/
            # y generan automáticamente el CSV intermedio
            pdf_destino = Path("data/input/VIDA LABORAL 2024.pdf")
            pdf_destino.parent.mkdir(parents=True, exist_ok=True)
            
            # Copiar PDF a la ubicación esperada
            import shutil
            shutil.copy(pdf_path, pdf_destino)
            logger.info(f"PDF copiado a: {pdf_destino}")
            
            # ============================================================
            # PASO 1: Extraer datos brutos del PDF usando el extractor
            # ============================================================
            logger.info("\n" + "="*60)
            logger.info("PASO 1/3: Extracción de datos del PDF")
            logger.info("="*60)
            
            df_raw = self.extractor.extract_all_tables(pdf_path)
            if df_raw.empty:
                return {
                    'success': False,
                    'error': "No se pudieron extraer datos del PDF."
                }
            
            # Limpiar códigos (cid:X) antes de guardar
            df_limpio = self._limpiar_codigos_cid(df_raw)
            
            # Guardar datos limpios en el formato que espera reorganizar_datos_completo.py
            self.raw_output.parent.mkdir(parents=True, exist_ok=True)
            df_limpio.to_csv(self.raw_output, index=False, encoding='utf-8-sig')
            logger.info(f"✅ Datos brutos guardados: {self.raw_output}")
            logger.info(f"   Filas: {len(df_limpio)}, Columnas: {len(df_limpio.columns)}")
            logger.info(f"   Columnas: {list(df_limpio.columns)[:5]}...")  # Mostrar primeras columnas
            
            # ============================================================
            # PASO 2: Ejecutar reorganizar_datos_completo.py
            # ============================================================
            logger.info("\n" + "="*60)
            logger.info("PASO 2/3: Reorganización de datos")
            logger.info("="*60)
            
            if not self.script_reorganizar.exists():
                return {
                    'success': False,
                    'error': f"Script no encontrado: {self.script_reorganizar}"
                }
            
            result = subprocess.run(
                ["python", str(self.script_reorganizar)],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',  # Reemplazar caracteres problemáticos en lugar de fallar
                check=False
            )
            
            if result.returncode != 0:
                logger.error(f"Error en reorganización: {result.stderr}")
                return {
                    'success': False,
                    'error': f"Error en reorganización de datos: {result.stderr}"
                }
            
            logger.info(result.stdout)
            
            if not self.completo_output.exists():
                return {
                    'success': False,
                    'error': f"El script no generó el archivo esperado: {self.completo_output}"
                }
            
            # ============================================================
            # PASO 3: Ejecutar proceso_completo_cliente.py
            # ============================================================
            logger.info("\n" + "="*60)
            logger.info("PASO 3/3: Creación de múltiples filas ALTA/BAJA")
            logger.info("="*60)
            
            if not self.script_proceso_cliente.exists():
                return {
                    'success': False,
                    'error': f"Script no encontrado: {self.script_proceso_cliente}"
                }
            
            result = subprocess.run(
                ["python", str(self.script_proceso_cliente)],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',  # Reemplazar caracteres problemáticos en lugar de fallar
                check=False
            )
            
            if result.returncode != 0:
                logger.error(f"Error en proceso cliente: {result.stderr}")
                return {
                    'success': False,
                    'error': f"Error en proceso de cliente: {result.stderr}"
                }
            
            logger.info(result.stdout)
            
            if not self.final_output.exists():
                return {
                    'success': False,
                    'error': f"El script no generó el archivo final esperado: {self.final_output}"
                }
            
            # ============================================================
            # PASO 4: Leer resultado final
            # ============================================================
            logger.info("\n" + "="*60)
            logger.info("RESULTADO FINAL")
            logger.info("="*60)
            
            df_final = pd.read_csv(self.final_output, encoding='utf-8-sig')
            logger.info(f"✅ Archivo final leído: {self.final_output}")
            logger.info(f"   Filas: {len(df_final)}")
            logger.info(f"   Columnas: {len(df_final.columns)}")
            logger.info(f"   Columnas: {list(df_final.columns)}")
            
            # Mostrar estadísticas
            if 'Situacion' in df_final.columns:
                situaciones = df_final['Situacion'].value_counts()
                logger.info(f"\n📊 Distribución de situaciones:")
                for sit, count in situaciones.items():
                    logger.info(f"   {sit}: {count}")
            
            return {
                'success': True,
                'data': df_final  # Usar 'data' para compatibilidad con app.py y test
            }
            
        except FileNotFoundError as e:
            logger.error(f"Archivo no encontrado: {e}")
            return {
                'success': False,
                'error': f"Error de archivo: {e}"
            }
        except Exception as e:
            logger.error(f"Error inesperado: {e}", exc_info=True)
            return {
                'success': False,
                'error': f"Error inesperado durante el procesamiento: {str(e)}"
            }
        finally:
            # Limpiar solo el archivo temporal inicial
            # Los demás archivos se mantienen para debug
            self.raw_output.unlink(missing_ok=True)
            logger.info("\n✅ Procesamiento completado. Archivos temporales limpiados.")
    
    def _limpiar_codigos_cid(self, df: pd.DataFrame) -> pd.DataFrame:
        """Limpia códigos (cid:X) del DataFrame."""
        logger.info("Limpiando códigos (cid:X)...")
        
        def limpiar_texto(texto):
            if pd.isna(texto):
                return texto
            texto_str = str(texto)
            # Eliminar (cid:X)
            texto_limpio = re.sub(r'\(cid:\d+\)', '', texto_str)
            return texto_limpio.strip()
        
        df_limpio = df.copy()
        for col in df_limpio.columns:
            if df_limpio[col].dtype == 'object':
                df_limpio[col] = df_limpio[col].apply(limpiar_texto)
        
        return df_limpio

