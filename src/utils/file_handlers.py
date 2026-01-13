"""
Manejadores de archivos para el sistema de extracción.
"""

from pathlib import Path
from typing import Optional
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class FileHandler:
    """Utilidades para manejo de archivos."""

    @staticmethod
    def save_dataframe(df: pd.DataFrame, output_path: Path,
                      format_type: str = 'csv', **kwargs) -> bool:
        """
        Guarda un DataFrame en diferentes formatos.

        Args:
            df: DataFrame a guardar
            output_path: Ruta de salida (sin extensión si se especifica format_type)
            format_type: Tipo de archivo ('csv', 'excel', 'json')
            **kwargs: Argumentos adicionales para to_csv, to_excel, etc.

        Returns:
            True si se guardó correctamente
        """
        try:
            if format_type.lower() == 'csv':
                if not output_path.suffix:
                    output_path = output_path.with_suffix('.csv')
                df.to_csv(output_path, index=False, encoding='utf-8-sig', **kwargs)
            elif format_type.lower() in ['excel', 'xlsx']:
                if not output_path.suffix:
                    output_path = output_path.with_suffix('.xlsx')
                df.to_excel(output_path, index=False, **kwargs)
            elif format_type.lower() == 'json':
                if not output_path.suffix:
                    output_path = output_path.with_suffix('.json')
                df.to_json(output_path, orient='records', **kwargs)
            else:
                raise ValueError(f"Formato no soportado: {format_type}")

            logger.info(f"Archivo guardado: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Error guardando archivo: {e}")
            return False

    @staticmethod
    def ensure_directory(path: Path) -> Path:
        """Asegura que un directorio existe."""
        path.mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def get_file_info(file_path: Path) -> Optional[dict]:
        """Obtiene información básica de un archivo."""
        if not file_path.exists():
            return None

        stat = file_path.stat()
        return {
            'name': file_path.name,
            'size': stat.st_size,
            'size_mb': stat.st_size / (1024 * 1024),
            'modified': stat.st_mtime,
            'extension': file_path.suffix
        }
