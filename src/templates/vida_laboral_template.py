"""
Plantilla específica para extracción de datos de Vida Laboral.
"""

from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import pandas as pd
import logging
from difflib import SequenceMatcher

from .template_base import PDFTemplate
from ..processors.pdf_extractor import PDFExtractor
import subprocess
import tempfile

logger = logging.getLogger(__name__)


class VidaLaboralTemplate(PDFTemplate):
    """
    Plantilla para procesar PDFs de Vida Laboral.

    Maneja la lógica específica de:
    - Extracción de datos de empleados
    - Normalización de nombres
    - Creación de múltiples filas para ALTA/BAJA
    - Relación con datos del cliente
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config or {
            'name': 'Vida Laboral',
            'description': 'Extrae y procesa datos de Vida Laboral de empleados',
            'version': '1.0',
            'supported_formats': ['pdf'],
            'output_columns': [
                'Nombre_Apellidos', 'Codigo_Cliente', 'NIF', 'Nacimiento',
                'Puesto', 'Sexo', 'F_Real_Alta', 'F_Real_Sit', 'F_Efecto_Sit',
                'Final_Cliente', 'Antiguedad_Cliente', 'T_C', 'Numero_Afiliacion',
                'G_C_M', 'C_T_P', 'Situacion'
            ]
        })

        self.extractor = PDFExtractor()

    def extract_data(self, pdf_path: Path) -> pd.DataFrame:
        """
        Extrae datos del PDF de Vida Laboral usando la lógica completa.

        Args:
            pdf_path: Ruta al archivo PDF

        Returns:
            DataFrame con datos extraídos y procesados
        """
        logger.info(f"Extrayendo datos de PDF: {pdf_path.name}")

        # OPCIÓN 1: Intentar usar el script completo que funciona
        try:
            df_processed = self._usar_script_completo(pdf_path)
            if not df_processed.empty:
                logger.info("✅ Usando script reorganizar_datos_completo.py (versión que funciona)")
                return df_processed
        except Exception as e:
            logger.warning(f"No se pudo usar script completo: {e}")
            logger.info("Usando método alternativo...")

        # OPCIÓN 2: Usar lógica integrada
        df_raw = self.extractor.extract_all_tables(pdf_path)

        if df_raw.empty:
            raise ValueError("No se pudieron extraer datos del PDF")

        df_processed = self._reorganizar_datos_completo(df_raw)

        return df_processed
    
    def _usar_script_completo(self, pdf_path: Path) -> pd.DataFrame:
        """
        Usa el script reorganizar_datos_completo.py directamente.
        """
        import sys
        import importlib.util
        
        # Verificar que existe el script
        script_path = Path("reorganizar_datos_completo.py")
        if not script_path.exists():
            raise FileNotFoundError("Script reorganizar_datos_completo.py no encontrado")
        
        # Primero extraer el PDF a CSV
        temp_csv = Path(f"temp_{pdf_path.stem}_raw.csv")
        df_raw = self.extractor.extract_all_tables(pdf_path)
        df_raw.to_csv(temp_csv, index=False, encoding='utf-8-sig')
        
        # Ejecutar el script de reorganización sobre el CSV
        spec = importlib.util.spec_from_file_location("reorganizar", script_path)
        reorganizar = importlib.util.module_from_spec(spec)
        
        # Modificar las rutas en el módulo antes de ejecutar
        reorganizar.input_file = temp_csv
        reorganizar.output_file = Path(f"temp_{pdf_path.stem}_completo.csv")
        
        # Ejecutar el script
        spec.loader.exec_module(reorganizar)
        
        # Leer resultado
        if reorganizar.output_file.exists():
            df_result = pd.read_csv(reorganizar.output_file, encoding='utf-8-sig')
            
            # Limpiar archivos temporales
            temp_csv.unlink(missing_ok=True)
            reorganizar.output_file.unlink(missing_ok=True)
            
            return df_result
        else:
            raise FileNotFoundError("No se generó el archivo de salida")
    

    def _reorganizar_datos_completo(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Aplica toda la lógica de reorganizar_datos_completo.py
        """
        import re
        
        logger.info("Aplicando lógica completa de reorganización...")
        
        # Funciones de extracción (del script original)
        def extraer_afiliacion(texto):
            if pd.isna(texto):
                return None
            texto = str(texto).strip()
            match = re.search(r'(\d{2}\s+\d{9,10})', texto)
            return match.group(1) if match else None
        
        def extraer_dni(texto):
            if pd.isna(texto):
                return None
            texto = str(texto).strip()
            match = re.search(r'(\d\s+\d{8,9}[A-Z])', texto)
            return match.group(1) if match else None
        
        def limpiar_nombre(texto, dni=None):
            if pd.isna(texto):
                return None
            texto = str(texto).strip()
            if dni:
                letra_dni = dni[-1] if len(dni) > 0 else None
                if letra_dni and texto.startswith(letra_dni + ' '):
                    texto = texto[2:].strip()
            texto = re.sub(r'\s*\d\s+\d{8,9}[A-Z].*$', '', texto)
            texto = re.sub(r'\s*\d{2}\s+\d{9,10}.*$', '', texto)
            return texto.strip()
        
        def parsear_fila_fechas(texto):
            if pd.isna(texto):
                return {}
            texto = str(texto).strip()
            partes = texto.split()
            resultado = {}
            
            # Buscar G_C_M
            for i, parte in enumerate(partes):
                if re.match(r'^\d{1,3}$', parte):
                    resultado['G_C_M'] = parte
                    break
            
            # Buscar T_C
            for parte in partes:
                if re.match(r'^\d{3}$', parte):
                    resultado['T_C'] = parte
                    break
            
            # Buscar C_T_P
            idx_tipos = None
            for i in range(len(partes)):
                if re.match(r'^\d+,\d{2}$', partes[i]):
                    idx_tipos = i
                    break
            
            if idx_tipos and idx_tipos >= 2:
                if idx_tipos > 2:
                    posible_ctp = partes[2]
                    if re.match(r'^(\d{3,4}|0,\d{3})$', posible_ctp):
                        resultado['C_T_P'] = posible_ctp
                    else:
                        resultado['C_T_P'] = '100'
                else:
                    resultado['C_T_P'] = '100'
            
            return resultado
        
        # Reorganizar datos
        empleados = []
        empleado_actual = None
        
        for idx, row in df.iterrows():
            # Detectar inicio de empleado (tiene número de afiliación)
            afiliacion = None
            for col in df.columns:
                valor = row[col]
                if pd.notna(valor):
                    afiliacion = extraer_afiliacion(str(valor))
                    if afiliacion:
                        dni = extraer_dni(str(valor))
                        nombre = limpiar_nombre(str(valor), dni)
                        
                        empleado_actual = {
                            'Numero_Afiliacion': afiliacion,
                            'DNI': dni,
                            'Nombre_Apellidos': nombre,
                            'Situacion': None,
                            'F_Real_Alta': None,
                            'F_Real_Sit': None,
                            'F_Efecto_Sit': None,
                            'G_C_M': None,
                            'T_C': None,
                            'C_T_P': None,
                            'Tipos_AT_IT': None
                        }
                        break
            
            # Si no hay empleado actual, buscar datos de situación
            if empleado_actual:
                for col in df.columns:
                    valor = row[col]
                    if pd.notna(valor):
                        texto = str(valor).strip()
                        
                        # Detectar situaciones
                        if 'ALTA' in texto and 'BAJA' in texto:
                            empleado_actual['Situacion'] = 'ALTA/BAJA'
                        elif 'ALTA' in texto and empleado_actual['Situacion'] is None:
                            empleado_actual['Situacion'] = 'ALTA'
                        elif 'BAJA' in texto and empleado_actual['Situacion'] is None:
                            empleado_actual['Situacion'] = 'BAJA'
                        
                        # Parsear fechas y códigos
                        fila_fechas = parsear_fila_fechas(texto)
                        if fila_fechas.get('G_C_M'):
                            empleado_actual['G_C_M'] = fila_fechas['G_C_M']
                        if fila_fechas.get('T_C'):
                            empleado_actual['T_C'] = fila_fechas['T_C']
                        if fila_fechas.get('C_T_P'):
                            empleado_actual['C_T_P'] = fila_fechas['C_T_P']
                
                # Guardar empleado cuando está completo
                if empleado_actual['Situacion']:
                    empleados.append(empleado_actual.copy())
                    empleado_actual = None
        
        # Crear DataFrame final
        if not empleados:
            raise ValueError("No se pudieron extraer empleados del PDF")
        
        df_final = pd.DataFrame(empleados)
        
        logger.info(f"Empleados extraídos: {len(df_final)}")
        return df_final

    def validate_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Valida datos de Vida Laboral.
        """
        validation = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'stats': {}
        }

        # Validaciones básicas
        required_columns = ['Nombre_Apellidos', 'Situacion']
        for col in required_columns:
            if col not in df.columns:
                validation['errors'].append(f"Columna requerida faltante: {col}")
                validation['is_valid'] = False

        if df.empty:
            validation['errors'].append("DataFrame está vacío")
            validation['is_valid'] = False

        # Estadísticas
        validation['stats'] = {
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'situaciones_alta_baja': len(df[df['Situacion'] == 'ALTA/BAJA']) if 'Situacion' in df.columns else 0
        }

        return validation

    def transform_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Transforma datos aplicando reglas específicas de Vida Laboral.
        """
        logger.info("Aplicando transformaciones de Vida Laboral")

        # 1. Crear múltiples filas para ALTA/BAJA
        df = self._crear_multiples_filas(df)

        # 2. Normalizar nombres
        if 'Nombre_Apellidos' in df.columns:
            df['Nombre_Normalizado'] = df['Nombre_Apellidos'].apply(self._normalizar_nombre)

        # 3. Limpiar fechas (convertir NaT a vacío)
        columnas_fecha = ['Nacimiento', 'F_Real_Alta', 'F_Real_Sit', 'F_Efecto_Sit',
                         'Final_Cliente', 'Antiguedad_Cliente']

        for col in columnas_fecha:
            if col in df.columns:
                df[col] = df[col].apply(self._formatear_fecha)

        # 4. Reordenar columnas según especificación
        columnas_orden = [
            'Nombre_Apellidos', 'Codigo_Cliente', 'NIF', 'Nacimiento',
            'Puesto', 'Sexo', 'F_Real_Alta', 'F_Real_Sit', 'F_Efecto_Sit',
            'Final_Cliente', 'Antiguedad_Cliente', 'T_C', 'Numero_Afiliacion',
            'G_C_M', 'C_T_P', 'Situacion'
        ]

        columnas_presentes = [col for col in columnas_orden if col in df.columns]
        df = df[columnas_presentes]

        return df

    def _crear_multiples_filas(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Crea múltiples filas para empleados con situación ALTA/BAJA.
        """
        nuevas_filas = []

        for _, row in df.iterrows():
            situacion = row.get('Situacion', '')

            if situacion == 'ALTA/BAJA':
                # Fila ALTA
                fila_alta = row.copy()
                fila_alta['Situacion'] = 'ALTA'
                fila_alta['F_Real_Sit'] = None
                fila_alta['F_Efecto_Sit'] = None
                nuevas_filas.append(fila_alta)

                # Fila BAJA
                fila_baja = row.copy()
                fila_baja['Situacion'] = 'BAJA'
                nuevas_filas.append(fila_baja)
            else:
                nuevas_filas.append(row)

        return pd.DataFrame(nuevas_filas).reset_index(drop=True)

    def _normalizar_nombre(self, nombre: str, es_cliente: bool = False) -> str:
        """
        Normaliza nombres para comparación.
        """
        if pd.isna(nombre) or nombre == '':
            return ""

        nombre = str(nombre).upper().strip()

        # Si es del cliente y tiene formato "APELLIDOS, NOMBRES", convertir a "NOMBRES APELLIDOS"
        if es_cliente and ',' in nombre:
            partes = nombre.split(',')
            if len(partes) == 2:
                apellidos = partes[0].strip()
                nombres = partes[1].strip()
                nombre = f"{nombres} {apellidos}"

        # Eliminar acentos
        nombre = nombre.replace("Á", "A").replace("É", "E").replace("Í", "I").replace("Ó", "O").replace("Ú", "U")
        nombre = nombre.replace("Ñ", "N")

        # Eliminar espacios extra
        nombre = " ".join(nombre.split())

        # Eliminar comas y puntos
        nombre = nombre.replace(",", "").replace(".", "")

        return nombre

    def _formatear_fecha(self, fecha) -> str:
        """
        Formatea fechas eliminando NaT y timestamps.
        """
        if pd.isna(fecha) or str(fecha).lower() == 'nat':
            return ""
        return str(fecha).split(' ')[0] if ' ' in str(fecha) else str(fecha)

    def relacionar_con_cliente(self, df_empleados: pd.DataFrame,
                             archivo_cliente: Path) -> pd.DataFrame:
        """
        Relaciona datos de empleados con Excel del cliente.

        Args:
            df_empleados: DataFrame con datos de empleados
            archivo_cliente: Ruta al Excel del cliente

        Returns:
            DataFrame con datos relacionados
        """
        logger.info("Relacionando con datos del cliente")

        try:
            # Leer Excel del cliente
            df_cliente = self._leer_excel_cliente(archivo_cliente)

            if df_cliente is None:
                return df_empleados

            # Normalizar nombres para comparación
            df_empleados['Nombre_Normalizado'] = df_empleados['Nombre_Apellidos'].apply(self._normalizar_nombre)

            # Buscar columna de nombres en cliente
            columna_nombre = self._encontrar_columna_nombre(df_cliente)
            if not columna_nombre:
                return df_empleados

            df_cliente['Nombre_Normalizado'] = df_cliente[columna_nombre].apply(
                lambda x: self._normalizar_nombre(x, es_cliente=True)
            )

            # Relacionar datos
            df_resultado = self._merge_con_cliente(df_empleados, df_cliente, columna_nombre)

            logger.info(f"Relacionamiento completado. Filas resultantes: {len(df_resultado)}")

            return df_resultado

        except Exception as e:
            logger.error(f"Error relacionando con cliente: {e}")
            return df_empleados

    def _leer_excel_cliente(self, archivo: Path) -> Optional[pd.DataFrame]:
        """Lee Excel del cliente con diferentes estrategias."""
        if not archivo.exists():
            logger.warning(f"Archivo del cliente no encontrado: {archivo}")
            return None

        try:
            # Intentar diferentes formas de leer
            try:
                df = pd.read_excel(archivo, sheet_name="Datos originales", header=4)
            except:
                try:
                    df = pd.read_excel(archivo, header=4)
                except:
                    df = pd.read_excel(archivo)

            logger.info(f"Datos del cliente leídos: {len(df)} filas")
            return df

        except Exception as e:
            logger.error(f"Error leyendo Excel del cliente: {e}")
            return None

    def _encontrar_columna_nombre(self, df_cliente: pd.DataFrame) -> Optional[str]:
        """Encuentra la columna de nombres en el Excel del cliente."""
        # Buscar exactamente 'Nombre2'
        for col in df_cliente.columns:
            if str(col).strip() == 'Nombre2':
                return col

        # Buscar otras variantes
        for col in df_cliente.columns:
            col_str = str(col).lower()
            if 'nombre' in col_str and '2' in col_str:
                return col

        logger.warning("No se encontró columna 'Nombre2' en Excel del cliente")
        return None

    def _merge_con_cliente(self, df_empleados: pd.DataFrame,
                          df_cliente: pd.DataFrame,
                          columna_nombre: str) -> pd.DataFrame:
        """Realiza el merge inteligente con datos del cliente."""

        # Buscar columnas relevantes en cliente
        columnas_mapping = {
            'codigo': ['Código', 'Codigo', 'Código_Cliente'],
            'nif': ['N.I.F.', 'NIF', 'DNI'],
            'nacimiento': ['Nacimiento', 'Fecha Nacimiento'],
            'puesto': ['Puesto', 'Cargo'],
            'sexo': ['Sexo', 'Género']
        }

        # Encontrar columnas disponibles
        cliente_cols = {}
        for tipo, posibles in columnas_mapping.items():
            for col in df_cliente.columns:
                col_str = str(col).strip()
                if any(posible.lower() in col_str.lower() for posible in posibles):
                    cliente_cols[tipo] = col
                    break

        # Merge inteligente por nombre normalizado
        df_merged = df_empleados.copy()

        # Para cada empleado, buscar match en cliente
        for idx, row in df_merged.iterrows():
            nombre_norm = row.get('Nombre_Normalizado', '')
            if not nombre_norm:
                continue

            # Buscar mejor match
            mejor_match = self._buscar_mejor_match(nombre_norm, df_cliente, columna_nombre)

            if mejor_match is not None:
                cliente_row = df_cliente.iloc[mejor_match]

                # Actualizar con datos del cliente
                for tipo, col_cliente in cliente_cols.items():
                    if tipo == 'codigo':
                        df_merged.at[idx, 'Codigo_Cliente'] = cliente_row.get(col_cliente)
                    elif tipo == 'nif':
                        df_merged.at[idx, 'NIF'] = cliente_row.get(col_cliente)
                    elif tipo == 'nacimiento':
                        df_merged.at[idx, 'Nacimiento'] = cliente_row.get(col_cliente)
                    elif tipo == 'puesto':
                        df_merged.at[idx, 'Puesto'] = cliente_row.get(col_cliente)
                    elif tipo == 'sexo':
                        df_merged.at[idx, 'Sexo'] = cliente_row.get(col_cliente)

        return df_merged

    def _buscar_mejor_match(self, nombre_buscado: str,
                           df_cliente: pd.DataFrame,
                           columna_nombre: str,
                           umbral: float = 0.8) -> Optional[int]:
        """Busca el mejor match para un nombre."""
        mejor_score = 0
        mejor_idx = None

        for idx, row in df_cliente.iterrows():
            nombre_cliente = str(row.get(columna_nombre, '')).strip()
            if not nombre_cliente:
                continue

            nombre_cliente_norm = self._normalizar_nombre(nombre_cliente, es_cliente=True)

            score = SequenceMatcher(None, nombre_buscado, nombre_cliente_norm).ratio()
            if score > mejor_score and score >= umbral:
                mejor_score = score
                mejor_idx = idx

        return mejor_idx
