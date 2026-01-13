"""
Módulo para extracción de datos de PDFs usando múltiples métodos.
Soporta tablas, texto estructurado y datos no estructurados.
"""
import logging
import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import warnings

# Suprimir warnings de librerías
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)


class PDFExtractor:
    """Extractor de PDFs con múltiples métodos de respaldo."""
    
    def __init__(self, method: str = "auto"):
        """
        Inicializa el extractor.
        
        Args:
            method: Método de extracción ('auto', 'pdfplumber', 'camelot', 'tabula', 'pymupdf', 'PyPDF2')
        """
        self.method = method
        self.available_methods = []
        self._check_available_methods()
    
    def _check_available_methods(self):
        """Verifica qué métodos están disponibles."""
        methods_to_check = {
            'pdfplumber': self._check_pdfplumber,
            'camelot': self._check_camelot,
            'tabula': self._check_tabula,
            'pymupdf': self._check_pymupdf,
            'PyPDF2': self._check_pypdf2
        }
        
        for method_name, check_func in methods_to_check.items():
            if check_func():
                self.available_methods.append(method_name)
        
        logger.info(f"Métodos disponibles: {', '.join(self.available_methods)}")
    
    def _check_pdfplumber(self) -> bool:
        try:
            import pdfplumber
            return True
        except ImportError:
            return False
    
    def _check_camelot(self) -> bool:
        try:
            import camelot
            return True
        except ImportError:
            return False
    
    def _check_tabula(self) -> bool:
        try:
            import tabula
            return True
        except ImportError:
            return False
    
    def _check_pymupdf(self) -> bool:
        try:
            import fitz  # PyMuPDF
            return True
        except ImportError:
            return False
    
    def _check_pypdf2(self) -> bool:
        try:
            import PyPDF2
            return True
        except ImportError:
            return False
    
    def extract_tables(self, pdf_path: Path, pages: Optional[List[int]] = None) -> List[pd.DataFrame]:
        """
        Extrae tablas de un PDF.
        
        Args:
            pdf_path: Ruta al archivo PDF
            pages: Lista de páginas a procesar (None = todas)
            
        Returns:
            Lista de DataFrames con las tablas extraídas
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF no encontrado: {pdf_path}")
        
        if self.method == "auto":
            return self._extract_auto(pdf_path, pages)
        else:
            return self._extract_with_method(pdf_path, pages, self.method)
    
    def _extract_auto(self, pdf_path: Path, pages: Optional[List[int]]) -> List[pd.DataFrame]:
        """Intenta extraer con múltiples métodos en orden de preferencia."""
        methods_order = ["pdfplumber", "camelot", "tabula", "pymupdf"]
        
        for method in methods_order:
            if method in self.available_methods:
                try:
                    logger.info(f"Intentando extracción con {method}...")
                    tables = self._extract_with_method(pdf_path, pages, method)
                    if tables and len(tables) > 0:
                        logger.info(f"✓ Extracción exitosa con {method}")
                        return tables
                except Exception as e:
                    logger.warning(f"Error con {method}: {str(e)}")
                    continue
        
        # Si todos fallan, intentar con PyPDF2 para texto plano
        logger.warning("Métodos de tabla fallaron, intentando extracción de texto...")
        return self._extract_text_fallback(pdf_path, pages)
    
    def _extract_with_method(self, pdf_path: Path, pages: Optional[List[int]], method: str) -> List[pd.DataFrame]:
        """Extrae usando un método específico."""
        if method == "pdfplumber":
            return self._extract_pdfplumber(pdf_path, pages)
        elif method == "camelot":
            return self._extract_camelot(pdf_path, pages)
        elif method == "tabula":
            return self._extract_tabula(pdf_path, pages)
        elif method == "pymupdf":
            return self._extract_pymupdf(pdf_path, pages)
        elif method == "PyPDF2":
            return self._extract_text_fallback(pdf_path, pages)
        else:
            raise ValueError(f"Método desconocido: {method}")
    
    def _extract_pdfplumber(self, pdf_path: Path, pages: Optional[List[int]]) -> List[pd.DataFrame]:
        """Extracción con pdfplumber (mejor para tablas complejas)."""
        import pdfplumber
        
        tables = []
        with pdfplumber.open(pdf_path) as pdf:
            page_range = pages if pages else range(len(pdf.pages))
            
            for page_num in page_range:
                page = pdf.pages[page_num]
                page_tables = page.extract_tables()
                
                for table in page_tables:
                    if table and len(table) > 0:
                        # Manejar columnas duplicadas agregando sufijos
                        headers = table[0]
                        seen = {}
                        new_headers = []
                        for h in headers:
                            if h in seen:
                                seen[h] += 1
                                new_headers.append(f"{h}_{seen[h]}")
                            else:
                                seen[h] = 0
                                new_headers.append(h)
                        
                        df = pd.DataFrame(table[1:], columns=new_headers)
                        df = df.dropna(how='all')  # Eliminar filas completamente vacías
                        if not df.empty:
                            tables.append(df)
        
        return tables
    
    def _extract_camelot(self, pdf_path: Path, pages: Optional[List[int]]) -> List[pd.DataFrame]:
        """Extracción con camelot (mejor para tablas con bordes)."""
        import camelot
        
        if pages:
            pages_str = ",".join(map(str, pages))
        else:
            pages_str = "all"
        
        tables = camelot.read_pdf(str(pdf_path), pages=pages_str, flavor='lattice')
        return [table.df for table in tables]
    
    def _extract_tabula(self, pdf_path: Path, pages: Optional[List[int]]) -> List[pd.DataFrame]:
        """Extracción con tabula (requiere Java)."""
        import tabula
        
        if pages:
            pages_list = [p + 1 for p in pages]  # tabula usa índice base 1
        else:
            pages_list = None
        
        tables = tabula.read_pdf(str(pdf_path), pages=pages_list, multiple_tables=True)
        return [df for df in tables if not df.empty]
    
    def _extract_pymupdf(self, pdf_path: Path, pages: Optional[List[int]]) -> List[pd.DataFrame]:
        """Extracción con PyMuPDF (rápido pero menos preciso)."""
        import fitz
        
        tables = []
        doc = fitz.open(pdf_path)
        
        page_range = pages if pages else range(len(doc))
        
        for page_num in page_range:
            page = doc[page_num]
            tabs = page.find_tables()
            
            for tab in tabs:
                table_data = tab.extract()
                if table_data and len(table_data) > 1:
                    df = pd.DataFrame(table_data[1:], columns=table_data[0])
                    if not df.empty:
                        tables.append(df)
        
        doc.close()
        return tables
    
    def _extract_text_fallback(self, pdf_path: Path, pages: Optional[List[int]]) -> List[pd.DataFrame]:
        """Extracción de texto plano como fallback."""
        import PyPDF2
        
        text_data = []
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            page_range = pages if pages else range(len(pdf_reader.pages))
            
            for page_num in page_range:
                page = pdf_reader.pages[page_num]
                text = page.extract_text()
                if text.strip():
                    # Intentar parsear como tabla si hay líneas estructuradas
                    lines = [line.strip() for line in text.split('\n') if line.strip()]
                    if lines:
                        text_data.append(lines)
        
        # Convertir a DataFrame si es posible
        if text_data:
            # Intentar detectar estructura de tabla
            max_cols = max(len(line.split()) for line in text_data[0] if text_data)
            data = []
            for line in text_data[0]:
                parts = line.split()
                if len(parts) > 1:
                    data.append(parts[:max_cols])
            
            if data:
                df = pd.DataFrame(data)
                return [df]
        
        return []
    
    def extract_all_tables(self, pdf_path: Path, pages: Optional[List[int]] = None) -> pd.DataFrame:
        """
        Extrae todas las tablas y las combina en un solo DataFrame.
        
        Args:
            pdf_path: Ruta al archivo PDF
            pages: Lista de páginas a procesar
            
        Returns:
            DataFrame combinado con todas las tablas
        """
        tables = self.extract_tables(pdf_path, pages)
        
        if not tables:
            logger.warning("No se encontraron tablas en el PDF")
            return pd.DataFrame()
        
        # Combinar todas las tablas
        combined_df = pd.concat(tables, ignore_index=True)
        
        # Limpiar duplicados exactos
        combined_df = combined_df.drop_duplicates()
        
        return combined_df
    
    def get_pdf_info(self, pdf_path: Path) -> Dict:
        """Obtiene información básica del PDF."""
        import PyPDF2
        
        info = {
            'path': str(pdf_path),
            'pages': 0,
            'size_mb': 0
        }
        
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                info['pages'] = len(pdf_reader.pages)
                info['size_mb'] = pdf_path.stat().st_size / (1024 * 1024)
        except Exception as e:
            logger.error(f"Error obteniendo info del PDF: {e}")
        
        return info

