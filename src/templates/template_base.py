"""
Clase base para plantillas de extracción de PDFs.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional, Any
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class PDFTemplate(ABC):
    """
    Clase base abstracta para plantillas de extracción de PDFs.

    Define la interfaz común que deben implementar todas las plantillas.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Inicializa la plantilla.

        Args:
            config: Configuración específica de la plantilla
        """
        self.config = config or {}
        self.name = self.config.get('name', self.__class__.__name__)

    @abstractmethod
    def extract_data(self, pdf_path: Path) -> pd.DataFrame:
        """
        Extrae datos del PDF según la lógica específica de la plantilla.

        Args:
            pdf_path: Ruta al archivo PDF

        Returns:
            DataFrame con los datos extraídos
        """
        pass

    @abstractmethod
    def validate_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Valida los datos extraídos según reglas específicas.

        Args:
            df: DataFrame a validar

        Returns:
            Diccionario con resultados de validación
        """
        pass

    @abstractmethod
    def transform_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Transforma los datos según reglas específicas de la plantilla.

        Args:
            df: DataFrame original

        Returns:
            DataFrame transformado
        """
        pass

    def get_template_info(self) -> Dict[str, Any]:
        """
        Retorna información sobre la plantilla.

        Returns:
            Diccionario con metadatos de la plantilla
        """
        return {
            'name': self.name,
            'description': self.config.get('description', ''),
            'version': self.config.get('version', '1.0'),
            'supported_formats': self.config.get('supported_formats', []),
            'output_columns': self.config.get('output_columns', [])
        }

    def process_pdf(self, pdf_path: Path) -> Dict[str, Any]:
        """
        Procesa un PDF completo usando el flujo estándar.

        Args:
            pdf_path: Ruta al archivo PDF

        Returns:
            Diccionario con resultados del procesamiento
        """
        try:
            logger.info(f"Procesando PDF con plantilla {self.name}: {pdf_path.name}")

            # 1. Extracción
            df_raw = self.extract_data(pdf_path)
            logger.info(f"Datos extraídos: {len(df_raw)} filas, {len(df_raw.columns)} columnas")

            # 2. Validación
            validation = self.validate_data(df_raw)
            if not validation.get('is_valid', True):
                logger.warning("Errores de validación encontrados")
                for error in validation.get('errors', []):
                    logger.warning(f"  - {error}")

            # 3. Transformación
            df_transformed = self.transform_data(df_raw)
            logger.info(f"Datos transformados: {len(df_transformed)} filas, {len(df_transformed.columns)} columnas")

            return {
                'success': True,
                'data': df_transformed,
                'validation': validation,
                'raw_data': df_raw,
                'template_info': self.get_template_info()
            }

        except Exception as e:
            logger.error(f"Error procesando PDF: {e}")
            return {
                'success': False,
                'error': str(e),
                'template_info': self.get_template_info()
            }
