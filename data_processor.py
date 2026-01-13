"""
Módulo de procesamiento y limpieza de datos.
Aplica transformaciones, validaciones y normalizaciones a los datos extraídos.
"""
import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime
import re

logger = logging.getLogger(__name__)


class DataProcessor:
    """Procesador de datos para limpieza y transformación."""
    
    def __init__(self):
        """Inicializa el procesador."""
        self.transformations_applied = []
    
    def clean_dataframe(self, df: pd.DataFrame, config: Optional[Dict] = None) -> pd.DataFrame:
        """
        Limpia y procesa un DataFrame.
        
        Args:
            df: DataFrame a limpiar
            config: Configuración de limpieza personalizada
            
        Returns:
            DataFrame limpio
        """
        logger.info("Iniciando limpieza de datos...")
        
        df_clean = df.copy()
        self.transformations_applied = []
        
        # Eliminar filas completamente vacías
        df_clean = self._remove_empty_rows(df_clean)
        
        # Limpiar nombres de columnas
        df_clean = self._clean_column_names(df_clean)
        
        # Detectar y convertir tipos de datos
        df_clean = self._detect_and_convert_types(df_clean)
        
        # Limpiar valores de texto
        df_clean = self._clean_text_values(df_clean)
        
        # Normalizar fechas
        df_clean = self._normalize_dates(df_clean)
        
        # Eliminar duplicados
        df_clean = self._remove_duplicates(df_clean)
        
        # Aplicar configuraciones personalizadas
        if config:
            df_clean = self._apply_custom_config(df_clean, config)
        
        logger.info(f"✓ Limpieza completada. Transformaciones aplicadas: {len(self.transformations_applied)}")
        return df_clean
    
    def _remove_empty_rows(self, df: pd.DataFrame) -> pd.DataFrame:
        """Elimina filas completamente vacías."""
        initial_rows = len(df)
        df_clean = df.dropna(how='all')
        removed = initial_rows - len(df_clean)
        if removed > 0:
            self.transformations_applied.append(f"Eliminadas {removed} filas vacías")
        return df_clean
    
    def _clean_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """Limpia y normaliza nombres de columnas."""
        df_clean = df.copy()
        
        # Eliminar espacios al inicio y final
        df_clean.columns = df_clean.columns.str.strip()
        
        # Reemplazar espacios múltiples por uno solo
        df_clean.columns = df_clean.columns.str.replace(r'\s+', ' ', regex=True)
        
        # Normalizar mayúsculas/minúsculas (primera letra mayúscula)
        df_clean.columns = df_clean.columns.str.title()
        
        return df_clean
    
    def _detect_and_convert_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """Detecta y convierte tipos de datos automáticamente."""
        df_clean = df.copy()
        
        for col in df_clean.columns:
            # Intentar convertir a numérico
            if df_clean[col].dtype == 'object':
                numeric_series = pd.to_numeric(df_clean[col], errors='ignore')
                if numeric_series.notna().sum() > len(df_clean) * 0.8:  # Si >80% son numéricos
                    df_clean[col] = numeric_series
                    self.transformations_applied.append(f"Columna '{col}' convertida a numérico")
        
        return df_clean
    
    def _clean_text_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """Limpia valores de texto."""
        df_clean = df.copy()
        
        for col in df_clean.select_dtypes(include=['object']).columns:
            # Eliminar espacios al inicio y final
            df_clean[col] = df_clean[col].astype(str).str.strip()
            
            # Reemplazar múltiples espacios por uno solo
            df_clean[col] = df_clean[col].str.replace(r'\s+', ' ', regex=True)
            
            # Reemplazar valores que indican "vacío"
            empty_indicators = ['nan', 'none', 'null', 'n/a', 'na', '']
            df_clean[col] = df_clean[col].replace(empty_indicators, np.nan)
        
        return df_clean
    
    def _normalize_dates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normaliza columnas de fecha."""
        df_clean = df.copy()
        date_patterns = [
            (r'\d{2}-\d{2}-\d{2}', '%d-%m-%y'),
            (r'\d{2}-\d{2}-\d{4}', '%d-%m-%Y'),
            (r'\d{2}/\d{2}/\d{2}', '%d/%m/%y'),
            (r'\d{2}/\d{2}/\d{4}', '%d/%m/%Y'),
        ]
        
        for col in df_clean.columns:
            col_lower = col.lower()
            if any(keyword in col_lower for keyword in ['fecha', 'date', 'nacimiento', 'contratación']):
                # Intentar convertir a fecha
                for pattern, date_format in date_patterns:
                    sample = df_clean[col].dropna().head(10)
                    if len(sample) > 0:
                        if sample.astype(str).str.match(pattern).any():
                            try:
                                df_clean[col] = pd.to_datetime(
                                    df_clean[col], 
                                    format=date_format, 
                                    errors='ignore'
                                )
                                self.transformations_applied.append(f"Columna '{col}' normalizada como fecha")
                                break
                            except:
                                pass
        
        return df_clean
    
    def _remove_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Elimina filas duplicadas."""
        initial_rows = len(df)
        df_clean = df.drop_duplicates()
        removed = initial_rows - len(df_clean)
        if removed > 0:
            self.transformations_applied.append(f"Eliminadas {removed} filas duplicadas")
        return df_clean
    
    def _apply_custom_config(self, df: pd.DataFrame, config: Dict) -> pd.DataFrame:
        """Aplica configuraciones personalizadas."""
        df_clean = df.copy()
        
        # Mapeo de columnas
        if 'column_mapping' in config:
            df_clean = df_clean.rename(columns=config['column_mapping'])
            self.transformations_applied.append("Mapeo de columnas aplicado")
        
        # Eliminar columnas específicas
        if 'drop_columns' in config:
            df_clean = df_clean.drop(columns=config['drop_columns'], errors='ignore')
            self.transformations_applied.append(f"Columnas eliminadas: {config['drop_columns']}")
        
        # Filtrar filas
        if 'filters' in config:
            for filter_config in config['filters']:
                col = filter_config.get('column')
                condition = filter_config.get('condition')
                value = filter_config.get('value')
                
                if col in df_clean.columns:
                    if condition == 'equals':
                        df_clean = df_clean[df_clean[col] == value]
                    elif condition == 'not_equals':
                        df_clean = df_clean[df_clean[col] != value]
                    elif condition == 'contains':
                        df_clean = df_clean[df_clean[col].astype(str).str.contains(value, na=False)]
                    
                    self.transformations_applied.append(f"Filtro aplicado: {col} {condition} {value}")
        
        return df_clean
    
    def validate_data(self, df: pd.DataFrame, rules: Optional[Dict] = None) -> Dict:
        """
        Valida los datos según reglas específicas.
        
        Args:
            df: DataFrame a validar
            rules: Reglas de validación personalizadas
            
        Returns:
            Diccionario con resultados de validación
        """
        validation_results = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'summary': {}
        }
        
        # Validaciones básicas
        if df.empty:
            validation_results['is_valid'] = False
            validation_results['errors'].append("El DataFrame está vacío")
        
        # Validar columnas requeridas
        if rules and 'required_columns' in rules:
            missing_cols = set(rules['required_columns']) - set(df.columns)
            if missing_cols:
                validation_results['is_valid'] = False
                validation_results['errors'].append(
                    f"Columnas requeridas faltantes: {', '.join(missing_cols)}"
                )
        
        # Validar valores nulos en columnas críticas
        if rules and 'critical_columns' in rules:
            for col in rules['critical_columns']:
                if col in df.columns:
                    null_count = df[col].isna().sum()
                    null_pct = (null_count / len(df)) * 100
                    if null_pct > 50:
                        validation_results['warnings'].append(
                            f"Columna '{col}' tiene {null_pct:.1f}% de valores nulos"
                        )
        
        validation_results['summary'] = {
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'errors_count': len(validation_results['errors']),
            'warnings_count': len(validation_results['warnings'])
        }
        
        return validation_results
    
    def merge_dataframes(self, df1: pd.DataFrame, df2: pd.DataFrame,
                        on: str, how: str = 'outer') -> pd.DataFrame:
        """
        Combina dos DataFrames.
        
        Args:
            df1: Primer DataFrame
            df2: Segundo DataFrame
            on: Columna para hacer el merge
            how: Tipo de merge ('inner', 'outer', 'left', 'right')
            
        Returns:
            DataFrame combinado
        """
        if on not in df1.columns or on not in df2.columns:
            raise ValueError(f"Columna '{on}' no encontrada en ambos DataFrames")
        
        merged = pd.merge(df1, df2, on=on, how=how, suffixes=('_old', '_new'))
        logger.info(f"✓ DataFrames combinados: {len(merged)} filas")
        return merged

