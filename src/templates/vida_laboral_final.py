"""
Plantilla que usa DIRECTAMENTE reorganizar_datos_completo.py
(El script que YA funciona perfectamente)
"""

from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd
import logging
import subprocess
import sys
import re

from .template_base import PDFTemplate

logger = logging.getLogger(__name__)


class VidaLaboralFinalTemplate(PDFTemplate):
    """
    Ejecuta el flujo completo que YA funciona:
    PDF → extractor → CSV sin CID → reorganizar_datos_completo.py → resultado final
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config or {
            'name': 'Vida Laboral Final',
            'description': 'Usa el script reorganizar_datos_completo.py que ya funciona',
            'version': '4.0'
        })

    def extract_data(self, pdf_path: Path) -> pd.DataFrame:
        """
        Extrae datos del PDF y los limpia (quita códigos CID).
        """
        logger.info(f"Extrayendo datos del PDF: {pdf_path.name}")
        
        from ..processors.pdf_extractor import PDFExtractor
        
        extractor = PDFExtractor(method="auto")
        df_raw = extractor.extract_all_tables(pdf_path)
        
        if df_raw.empty:
            raise ValueError("No se pudieron extraer datos del PDF")
        
        logger.info(f"Datos extraídos: {len(df_raw)} filas, {len(df_raw.columns)} columnas")
        
        # Limpiar códigos (cid:X)
        df_limpio = self._limpiar_codigos_cid(df_raw)
        
        # Guardar en el lugar que espera reorganizar_datos_completo.py
        output_path = Path("data/output/VIDA LABORAL 2024_SIN_CID.csv")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df_limpio.to_csv(output_path, index=False, encoding='utf-8-sig')
        logger.info(f"CSV limpio guardado: {output_path}")
        
        return df_limpio

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

    def validate_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Validación básica."""
        return {
            'is_valid': not df.empty,
            'errors': [] if not df.empty else ["DataFrame vacío"],
            'warnings': [],
            'stats': {'total_rows': len(df)}
        }

    def transform_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Ejecuta reorganizar_datos_completo.py y retorna el resultado.
        """
        logger.info("Ejecutando reorganizar_datos_completo.py...")
        
        try:
            # Ejecutar el script que YA funciona
            resultado = subprocess.run(
                [sys.executable, "reorganizar_datos_completo.py"],
                capture_output=True,
                text=True,
                cwd=Path.cwd(),
                encoding='utf-8'
            )
            
            # Leer el archivo generado
            output_file = Path("data/output/VIDA LABORAL 2024_COMPLETO.csv")
            
            if output_file.exists():
                df_final = pd.read_csv(output_file, encoding='utf-8-sig')
                logger.info(f"✅ Datos procesados: {len(df_final)} filas, {len(df_final.columns)} columnas")
                
                # Mostrar muestra
                logger.info("\nMuestra de datos finales:")
                logger.info(f"\n{df_final.head(3).to_string()}")
                
                return df_final
            else:
                logger.error("El script no generó el archivo esperado")
                return df
                
        except Exception as e:
            logger.error(f"Error ejecutando reorganizar_datos_completo.py: {e}")
            logger.warning("Retornando datos sin procesar")
            return df
