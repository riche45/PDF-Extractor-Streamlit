"""
Módulo de Análisis Exploratorio de Datos (EDA).
Genera reportes automáticos sobre la calidad y estructura de los datos extraídos.
"""
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Optional, List
import json
from datetime import datetime

try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    PLOTTING_AVAILABLE = True
except ImportError:
    PLOTTING_AVAILABLE = False
    logging.warning("Matplotlib/Seaborn no disponibles. Los gráficos se omitirán.")

logger = logging.getLogger(__name__)


class DataAnalyzer:
    """Analizador exploratorio de datos."""
    
    def __init__(self, output_dir: Optional[Path] = None):
        """
        Inicializa el analizador.
        
        Args:
            output_dir: Directorio para guardar reportes
        """
        self.output_dir = output_dir or Path("data/reports")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def analyze(self, df: pd.DataFrame, output_name: str = "analysis_report") -> Dict:
        """
        Realiza análisis exploratorio completo.
        
        Args:
            df: DataFrame a analizar
            output_name: Nombre base para los archivos de salida
            
        Returns:
            Diccionario con todos los análisis realizados
        """
        logger.info("Iniciando análisis exploratorio de datos...")
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'basic_info': self._basic_info(df),
            'data_quality': self._data_quality(df),
            'column_analysis': self._column_analysis(df),
            'statistics': self._statistical_summary(df),
            'recommendations': []
        }
        
        # Generar recomendaciones
        results['recommendations'] = self._generate_recommendations(results)
        
        # Guardar reporte JSON
        self._save_json_report(results, output_name)
        
        # Generar reporte HTML si es posible
        if PLOTTING_AVAILABLE:
            self._generate_html_report(df, results, output_name)
        
        logger.info("Análisis completado")
        return results
    
    def _basic_info(self, df: pd.DataFrame) -> Dict:
        """Información básica del DataFrame."""
        return {
            'shape': {
                'rows': len(df),
                'columns': len(df.columns)
            },
            'columns': list(df.columns),
            'dtypes': {col: str(dtype) for col, dtype in df.dtypes.items()},
            'memory_usage_mb': df.memory_usage(deep=True).sum() / (1024 * 1024)
        }
    
    def _data_quality(self, df: pd.DataFrame) -> Dict:
        """Análisis de calidad de datos."""
        quality = {
            'missing_values': {},
            'duplicate_rows': int(df.duplicated().sum()),
            'empty_rows': int(df.isna().all(axis=1).sum()),
            'completeness_score': 0.0
        }
        
        total_cells = len(df) * len(df.columns)
        missing_cells = 0
        
        for col in df.columns:
            missing = df[col].isna().sum()
            missing_pct = (missing / len(df)) * 100
            quality['missing_values'][col] = {
                'count': int(missing),
                'percentage': round(missing_pct, 2)
            }
            missing_cells += missing
        
        quality['completeness_score'] = round(
            ((total_cells - missing_cells) / total_cells) * 100, 2
        )
        
        return quality
    
    def _column_analysis(self, df: pd.DataFrame) -> Dict:
        """Análisis detallado por columna."""
        analysis = {}
        
        for col in df.columns:
            col_data = df[col]
            col_info = {
                'dtype': str(col_data.dtype),
                'unique_values': int(col_data.nunique()),
                'null_count': int(col_data.isna().sum())
            }
            
            # Detectar tipo de dato semántico
            col_info['semantic_type'] = self._detect_semantic_type(col_data)
            
            # Análisis específico por tipo
            if pd.api.types.is_numeric_dtype(col_data):
                col_info['numeric_stats'] = {
                    'mean': float(col_data.mean()) if not col_data.isna().all() else None,
                    'median': float(col_data.median()) if not col_data.isna().all() else None,
                    'std': float(col_data.std()) if not col_data.isna().all() else None,
                    'min': float(col_data.min()) if not col_data.isna().all() else None,
                    'max': float(col_data.max()) if not col_data.isna().all() else None
                }
            
            if pd.api.types.is_datetime64_any_dtype(col_data):
                col_info['date_range'] = {
                    'min': str(col_data.min()),
                    'max': str(col_data.max())
                }
            
            # Valores más frecuentes
            if col_data.nunique() < 50:  # Solo si hay pocos valores únicos
                col_info['top_values'] = col_data.value_counts().head(10).to_dict()
            
            analysis[col] = col_info
        
        return analysis
    
    def _detect_semantic_type(self, series: pd.Series) -> str:
        """Detecta el tipo semántico de una columna."""
        # Intentar detectar fechas
        if self._is_date_column(series):
            return 'date'
        
        # Detectar IDs
        if self._is_id_column(series):
            return 'id'
        
        # Detectar porcentajes
        if self._is_percentage_column(series):
            return 'percentage'
        
        # Detectar moneda
        if self._is_currency_column(series):
            return 'currency'
        
        # Tipo numérico
        if pd.api.types.is_numeric_dtype(series):
            return 'numeric'
        
        # Tipo texto
        return 'text'
    
    def _is_date_column(self, series: pd.Series) -> bool:
        """Detecta si una columna contiene fechas."""
        date_keywords = ['fecha', 'date', 'nacimiento', 'contratación', 'fin']
        col_name_lower = series.name.lower() if hasattr(series, 'name') and series.name else ''
        
        if any(keyword in col_name_lower for keyword in date_keywords):
            return True
        
        # Intentar convertir a fecha
        sample = series.dropna().head(100)
        if len(sample) == 0:
            return False
        
        date_patterns = [
            r'\d{2}-\d{2}-\d{2,4}',
            r'\d{2}/\d{2}/\d{2,4}',
            r'\d{4}-\d{2}-\d{2}'
        ]
        
        for pattern in date_patterns:
            if sample.astype(str).str.match(pattern).any():
                return True
        
        return False
    
    def _is_id_column(self, series: pd.Series) -> bool:
        """Detecta si una columna es un ID."""
        id_keywords = ['id', 'codigo', 'código', 'numero', 'número']
        col_name_lower = series.name.lower() if hasattr(series, 'name') and series.name else ''
        
        if any(keyword in col_name_lower for keyword in id_keywords):
            return True
        
        # Si todos los valores son únicos y numéricos
        if pd.api.types.is_numeric_dtype(series) and series.nunique() == len(series.dropna()):
            return True
        
        return False
    
    def _is_percentage_column(self, series: pd.Series) -> bool:
        """Detecta si una columna contiene porcentajes."""
        pct_keywords = ['porcentaje', 'porcent', '%', 'jornada']
        col_name_lower = series.name.lower() if hasattr(series, 'name') and series.name else ''
        
        if any(keyword in col_name_lower for keyword in pct_keywords):
            return True
        
        # Si los valores están entre 0 y 100
        if pd.api.types.is_numeric_dtype(series):
            sample = series.dropna()
            if len(sample) > 0:
                if 0 <= sample.min() <= 100 and 0 <= sample.max() <= 100:
                    return True
        
        return False
    
    def _is_currency_column(self, series: pd.Series) -> bool:
        """Detecta si una columna contiene valores monetarios."""
        currency_keywords = ['precio', 'importe', 'salario', 'sueldo', 'euro', '€']
        col_name_lower = series.name.lower() if hasattr(series, 'name') and series.name else ''
        
        return any(keyword in col_name_lower for keyword in currency_keywords)
    
    def _statistical_summary(self, df: pd.DataFrame) -> Dict:
        """Resumen estadístico."""
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        stats = {
            'numeric_columns': list(numeric_cols),
            'categorical_columns': list(df.select_dtypes(include=['object']).columns),
            'summary_statistics': {}
        }
        
        if len(numeric_cols) > 0:
            stats['summary_statistics'] = df[numeric_cols].describe().to_dict()
        
        return stats
    
    def _generate_recommendations(self, results: Dict) -> List[str]:
        """Genera recomendaciones basadas en el análisis."""
        recommendations = []
        
        # Recomendaciones sobre valores faltantes
        quality = results['data_quality']
        for col, missing_info in quality['missing_values'].items():
            if missing_info['percentage'] > 50:
                recommendations.append(
                    f"⚠️ Columna '{col}' tiene {missing_info['percentage']}% de valores faltantes. "
                    "Considerar eliminar o investigar la causa."
                )
            elif missing_info['percentage'] > 10:
                recommendations.append(
                    f"⚠️ Columna '{col}' tiene {missing_info['percentage']}% de valores faltantes. "
                    "Considerar estrategia de imputación."
                )
        
        # Recomendaciones sobre duplicados
        if quality['duplicate_rows'] > 0:
            recommendations.append(
                f"⚠️ Se encontraron {quality['duplicate_rows']} filas duplicadas. "
                "Considerar eliminarlas antes de actualizar Google Sheets."
            )
        
        # Recomendaciones sobre completitud
        if quality['completeness_score'] < 80:
            recommendations.append(
                f"⚠️ Score de completitud bajo ({quality['completeness_score']}%). "
                "Revisar la calidad de los datos extraídos del PDF."
            )
        
        # Recomendaciones sobre tipos de datos
        for col, col_info in results['column_analysis'].items():
            if col_info['semantic_type'] == 'date' and col_info['dtype'] != 'datetime64[ns]':
                recommendations.append(
                    f"💡 Columna '{col}' parece contener fechas pero está como {col_info['dtype']}. "
                    "Considerar convertir a tipo fecha."
                )
        
        if not recommendations:
            recommendations.append("✅ Los datos parecen estar en buen estado. Listos para actualizar Google Sheets.")
        
        return recommendations
    
    def _save_json_report(self, results: Dict, output_name: str):
        """Guarda el reporte en formato JSON."""
        output_path = self.output_dir / f"{output_name}.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        logger.info(f"Reporte JSON guardado: {output_path}")
    
    def _generate_html_report(self, df: pd.DataFrame, results: Dict, output_name: str):
        """Genera reporte HTML con visualizaciones."""
        if not PLOTTING_AVAILABLE:
            return
        
        html_content = self._create_html_template(df, results)
        output_path = self.output_dir / f"{output_name}.html"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"Reporte HTML guardado: {output_path}")
    
    def _create_html_template(self, df: pd.DataFrame, results: Dict) -> str:
        """Crea el template HTML del reporte."""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Análisis Exploratorio de Datos</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }}
        h1 {{ color: #333; }}
        h2 {{ color: #555; border-bottom: 2px solid #ddd; padding-bottom: 10px; }}
        .metric {{ display: inline-block; margin: 10px; padding: 15px; background: #f0f0f0; border-radius: 5px; }}
        .metric-label {{ font-weight: bold; color: #666; }}
        .metric-value {{ font-size: 24px; color: #333; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #4CAF50; color: white; }}
        .recommendation {{ padding: 10px; margin: 10px 0; border-left: 4px solid #2196F3; background: #e3f2fd; }}
        .warning {{ border-left-color: #ff9800; background: #fff3e0; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Análisis Exploratorio de Datos</h1>
        <p><strong>Fecha:</strong> {results['timestamp']}</p>
        
        <h2>📈 Información Básica</h2>
        <div class="metric">
            <div class="metric-label">Filas</div>
            <div class="metric-value">{results['basic_info']['shape']['rows']}</div>
        </div>
        <div class="metric">
            <div class="metric-label">Columnas</div>
            <div class="metric-value">{results['basic_info']['shape']['columns']}</div>
        </div>
        <div class="metric">
            <div class="metric-label">Completitud</div>
            <div class="metric-value">{results['data_quality']['completeness_score']}%</div>
        </div>
        
        <h2>🔍 Calidad de Datos</h2>
        <table>
            <tr>
                <th>Columna</th>
                <th>Valores Faltantes</th>
                <th>Porcentaje</th>
            </tr>
"""
        
        for col, missing_info in results['data_quality']['missing_values'].items():
            html += f"""
            <tr>
                <td>{col}</td>
                <td>{missing_info['count']}</td>
                <td>{missing_info['percentage']}%</td>
            </tr>
"""
        
        html += f"""
        </table>
        
        <h2>💡 Recomendaciones</h2>
"""
        
        for rec in results['recommendations']:
            warning_class = "warning" if "⚠️" in rec else ""
            html += f'<div class="recommendation {warning_class}">{rec}</div>\n'
        
        html += """
    </div>
</body>
</html>
"""
        
        return html

