"""
Plantilla completa para procesamiento de Vida Laboral.
Integra TODA la lógica de reorganizar_datos_completo.py
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
import pandas as pd
import logging
import re

from .template_base import PDFTemplate

logger = logging.getLogger(__name__)


class VidaLaboralCompleteTemplate(PDFTemplate):
    """
    Plantilla COMPLETA para procesar PDFs de Vida Laboral.
    Usa la lógica completa y probada de reorganizar_datos_completo.py
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config or {
            'name': 'Vida Laboral Completo',
            'description': 'Extrae y procesa datos completos de Vida Laboral',
            'version': '2.0',
            'supported_formats': ['pdf'],
            'output_columns': [
                'Codigo_Cliente', 'Nombre_Apellidos', 'DNI', 'Numero_Afiliacion',
                'Situacion', 'F_Real_Alta', 'F_Efecto_Alta', 'F_Real_Sit', 'F_Efecto_Sit',
                'G_C_M', 'T_C', 'C_T_P', 'Tipos_AT_IT', 'IMS', 'Total', 'Dias_Cot'
            ]
        })

    def extract_data(self, pdf_path: Path) -> pd.DataFrame:
        """
        Extrae datos del PDF usando pdf_extractor básico.
        """
        logger.info(f"Paso 1: Extrayendo datos del PDF: {pdf_path.name}")
        
        # Usar extractor básico (el código que YA tienes)
        from ..processors.pdf_extractor import PDFExtractor
        
        extractor = PDFExtractor(method="auto")
        df_raw = extractor.extract_all_tables(pdf_path)
        
        if df_raw.empty:
            raise ValueError("No se pudieron extraer datos del PDF")
        
        logger.info(f"Datos extraídos: {len(df_raw)} filas, {len(df_raw.columns)} columnas")
        
        # Aplicar limpieza de códigos CID
        df_clean = self._limpiar_codigos_cid(df_raw)
        
        return df_clean

    def _limpiar_codigos_cid(self, df: pd.DataFrame) -> pd.DataFrame:
        """Limpia códigos (cid:X) del DataFrame."""
        logger.info("Paso 2: Limpiando códigos (cid:X)...")
        
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
        """Valida los datos extraídos."""
        validation = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'stats': {}
        }

        if df.empty:
            validation['errors'].append("DataFrame está vacío")
            validation['is_valid'] = False
            return validation

        validation['stats'] = {
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'empleados_unicos': df['Nombre_Apellidos'].nunique() if 'Nombre_Apellidos' in df.columns else 0
        }

        return validation

    def transform_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Transforma los datos aplicando TODA la lógica de reorganización.
        Esta es la función principal que aplica toda la lógica completa.
        """
        logger.info("Paso 3: Aplicando transformaciones completas...")
        
        # Reorganizar datos aplicando toda la lógica
        df_reorganizado = self._reorganizar_datos_completo(df)
        
        return df_reorganizado

    def _reorganizar_datos_completo(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Aplica TODA la lógica de reorganizar_datos_completo.py
        Esta función contiene todo el procesamiento que funciona.
        """
        empleados = []
        empleado_actual = None
        
        for _, row in df.iterrows():
            # Convertir fila a texto para análisis
            fila_texto = ' '.join([str(val) for val in row.values if pd.notna(val)])
            
            # Detectar si es inicio de nuevo empleado (tiene número de afiliación)
            numero_afiliacion = self._extraer_afiliacion(fila_texto)
            dni = self._extraer_dni(fila_texto)
            
            if numero_afiliacion or dni:
                # Guardar empleado anterior si existe
                if empleado_actual and empleado_actual.get('Nombre_Apellidos'):
                    empleados.append(empleado_actual.copy())
                
                # Iniciar nuevo empleado
                empleado_actual = self._crear_empleado_vacio()
                empleado_actual['Numero_Afiliacion'] = numero_afiliacion
                empleado_actual['DNI'] = dni
                
                # Extraer nombre
                nombre = self._limpiar_nombre(fila_texto, dni)
                if nombre:
                    empleado_actual['Nombre_Apellidos'] = nombre
            
            # Si ya tenemos un empleado, procesar fechas y situaciones
            if empleado_actual:
                fila_fechas = self._parsear_fila_fechas(fila_texto)
                
                if fila_fechas:
                    situacion = fila_fechas.get('Situacion')
                    
                    if situacion == 'ALTA/BAJA':
                        # Crear DOS filas: una para ALTA y otra para BAJA
                        # Fila ALTA
                        emp_alta = empleado_actual.copy()
                        emp_alta['Situacion'] = 'ALTA'
                        emp_alta['F_Real_Alta'] = fila_fechas.get('F_Real_Alta')
                        emp_alta['F_Efecto_Alta'] = fila_fechas.get('F_Efecto_Alta')
                        emp_alta['G_C_M'] = fila_fechas.get('G_C_M')
                        emp_alta['T_C'] = fila_fechas.get('T_C')
                        emp_alta['C_T_P'] = fila_fechas.get('C_T_P')
                        empleados.append(emp_alta)
                        
                        # Fila BAJA
                        emp_baja = empleado_actual.copy()
                        emp_baja['Situacion'] = 'BAJA'
                        emp_baja['F_Real_Alta'] = fila_fechas.get('F_Real_Alta')
                        emp_baja['F_Efecto_Alta'] = fila_fechas.get('F_Efecto_Alta')
                        emp_baja['F_Real_Sit'] = fila_fechas.get('F_Real_Sit')
                        emp_baja['F_Efecto_Sit'] = fila_fechas.get('F_Efecto_Sit')
                        emp_baja['G_C_M'] = fila_fechas.get('G_C_M')
                        emp_baja['T_C'] = fila_fechas.get('T_C')
                        emp_baja['C_T_P'] = fila_fechas.get('C_T_P')
                        emp_baja['Tipos_AT_IT'] = fila_fechas.get('Tipos_AT_IT')
                        emp_baja['IMS'] = fila_fechas.get('IMS')
                        emp_baja['Total'] = fila_fechas.get('Total')
                        emp_baja['Dias_Cot'] = fila_fechas.get('Dias_Cot')
                        empleados.append(emp_baja)
                        
                        # Reiniciar empleado para próxima iteración
                        empleado_actual = self._crear_empleado_vacio()
                        empleado_actual['Numero_Afiliacion'] = numero_afiliacion or empleado_actual.get('Numero_Afiliacion')
                        empleado_actual['DNI'] = dni or empleado_actual.get('DNI')
                        empleado_actual['Nombre_Apellidos'] = empleado_actual.get('Nombre_Apellidos')
                        
                    elif situacion in ['ALTA', 'BAJA']:
                        # Actualizar datos del empleado actual
                        empleado_actual['Situacion'] = situacion
                        empleado_actual['F_Real_Alta'] = fila_fechas.get('F_Real_Alta')
                        empleado_actual['F_Efecto_Alta'] = fila_fechas.get('F_Efecto_Alta')
                        if situacion == 'BAJA':
                            empleado_actual['F_Real_Sit'] = fila_fechas.get('F_Real_Sit')
                            empleado_actual['F_Efecto_Sit'] = fila_fechas.get('F_Efecto_Sit')
                        empleado_actual['G_C_M'] = fila_fechas.get('G_C_M')
                        empleado_actual['T_C'] = fila_fechas.get('T_C')
                        empleado_actual['C_T_P'] = fila_fechas.get('C_T_P')
                        empleado_actual['Tipos_AT_IT'] = fila_fechas.get('Tipos_AT_IT')
                        empleado_actual['IMS'] = fila_fechas.get('IMS')
                        empleado_actual['Total'] = fila_fechas.get('Total')
                        empleado_actual['Dias_Cot'] = fila_fechas.get('Dias_Cot')
        
        # Agregar último empleado
        if empleado_actual and empleado_actual.get('Nombre_Apellidos'):
            empleados.append(empleado_actual)
        
        # Crear DataFrame final
        df_final = pd.DataFrame(empleados)
        
        logger.info(f"Datos reorganizados: {len(df_final)} filas")
        
        # Ordenar columnas
        columnas_orden = [
            'Codigo_Cliente', 'Nombre_Apellidos', 'DNI', 'Numero_Afiliacion',
            'Situacion', 'F_Real_Alta', 'F_Efecto_Alta', 'F_Real_Sit', 'F_Efecto_Sit',
            'G_C_M', 'T_C', 'C_T_P', 'Tipos_AT_IT', 'IMS', 'Total', 'Dias_Cot'
        ]
        
        columnas_presentes = [col for col in columnas_orden if col in df_final.columns]
        df_final = df_final[columnas_presentes]
        
        return df_final

    def _crear_empleado_vacio(self) -> Dict:
        """Crea un diccionario vacío para un empleado."""
        return {
            'Codigo_Cliente': None,
            'Nombre_Apellidos': None,
            'DNI': None,
            'Numero_Afiliacion': None,
            'Situacion': None,
            'F_Real_Alta': None,
            'F_Efecto_Alta': None,
            'F_Real_Sit': None,
            'F_Efecto_Sit': None,
            'G_C_M': None,
            'T_C': None,
            'C_T_P': None,
            'Tipos_AT_IT': None,
            'IMS': None,
            'Total': None,
            'Dias_Cot': None
        }

    def _extraer_afiliacion(self, texto: str) -> Optional[str]:
        """Extrae número de afiliación."""
        if not texto:
            return None
        match = re.search(r'(\d{2}\s+\d{9,10})', texto)
        return match.group(1) if match else None

    def _extraer_dni(self, texto: str) -> Optional[str]:
        """Extrae DNI."""
        if not texto:
            return None
        match = re.search(r'(\d\s+\d{8,9}[A-Z])', texto)
        return match.group(1) if match else None

    def _limpiar_nombre(self, texto: str, dni: Optional[str] = None) -> Optional[str]:
        """Extrae y limpia el nombre completo."""
        if not texto:
            return None
        
        texto = texto.strip()
        
        # Si hay DNI, quitar su letra final del texto si aparece al inicio
        if dni:
            letra_dni = dni[-1] if len(dni) > 0 else None
            if letra_dni and texto.startswith(letra_dni + ' '):
                texto = texto[len(letra_dni) + 1:].strip()
        
        # Buscar nombres en mayúsculas
        patron = r'([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ\s]{8,60})'
        matches = re.findall(patron, texto)
        
        for match in matches:
            nombre = match.strip()
            palabras = nombre.split()
            
            if (len(palabras) >= 2 and 
                not re.search(r'^\d', nombre) and
                not re.match(r'^[A-Z0-9]{2,4}$', nombre) and
                len(nombre) >= 10):
                
                # Limpiar
                nombre = re.sub(r'^[A-Z]\s+', '', nombre).strip()
                nombre = re.sub(r'\s+[A-Z0-9]{2,4}$', '', nombre).strip()
                
                # Limpiar letras sueltas al final
                palabras_finales = nombre.split()
                if len(palabras_finales) >= 3:
                    while len(palabras_finales) > 0:
                        ultima_palabra = palabras_finales[-1]
                        if len(ultima_palabra) == 1 and ultima_palabra.isupper():
                            palabras_finales = palabras_finales[:-1]
                        else:
                            break
                    nombre = ' '.join(palabras_finales).strip()
                
                if len(nombre.split()) >= 2 and len(nombre) >= 10:
                    return nombre
        
        return None

    def _parsear_fila_fechas(self, texto: str) -> Dict:
        """
        Parsea una fila de fechas y datos adicionales.
        COPIA EXACTA de la lógica que funciona en reorganizar_datos_completo.py
        """
        if not texto:
            return {}
        
        resultado = {}
        
        # Detectar situación
        tiene_alta = 'ALTA' in texto
        tiene_baja = 'BAJA' in texto
        
        # Extraer fechas
        fechas = re.findall(r'\d{2}-\d{2}-\d{4}', texto)
        partes = texto.split()
        
        if tiene_alta and tiene_baja:
            resultado['Situacion'] = 'ALTA/BAJA'
            
            # Procesar ALTA
            match_alta = re.search(r'ALTA\s+(\d{2}-\d{2}-\d{4})\s+(\d{2}-\d{2}-\d{4})', texto)
            if match_alta:
                resultado['F_Real_Alta'] = match_alta.group(1)
                resultado['F_Efecto_Alta'] = match_alta.group(2)
            
            # Procesar BAJA (todas las ocurrencias, tomar última)
            todas_bajas = list(re.finditer(r'BAJA\s+(\d{2}-\d{2}-\d{4})\s+(\d{2}-\d{2}-\d{4})\s+(\d{2}-\d{2}-\d{4})\s+(\d{2}-\d{2}-\d{4})', texto))
            if todas_bajas:
                ultima_baja = todas_bajas[-1]
                if not resultado.get('F_Real_Alta'):
                    resultado['F_Real_Alta'] = ultima_baja.group(1)
                    resultado['F_Efecto_Alta'] = ultima_baja.group(2)
                resultado['F_Real_Sit'] = ultima_baja.group(3)
                resultado['F_Efecto_Sit'] = ultima_baja.group(4)
            
            # Extraer datos después de última BAJA
            ultima_pos_baja = texto.rfind('BAJA')
            if ultima_pos_baja != -1:
                texto_despues_baja = texto[ultima_pos_baja:]
                match_datos_baja = re.search(r'BAJA\s+\d{2}-\d{2}-\d{4}\s+\d{2}-\d{2}-\d{4}\s+\d{2}-\d{2}-\d{4}\s+\d{2}-\d{2}-\d{4}\s+(.+)', texto_despues_baja)
                if match_datos_baja:
                    texto_datos = match_datos_baja.group(1)
                    texto_datos = re.sub(r'\s+[A-Z][A-Z0-9]{1,3}(\s+[A-Z][A-Z0-9]{1,3})*$', '', texto_datos).strip()
                    partes = texto_datos.split()
                    if len(partes) >= 6:
                        resultado['G_C_M'] = partes[0] if partes[0].isdigit() else None
                        resultado['T_C'] = partes[1] if len(partes) > 1 else None
                        
                        # Detectar C_T_P
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
                            
                            resultado['Tipos_AT_IT'] = partes[idx_tipos] if idx_tipos < len(partes) else None
                            resultado['IMS'] = partes[idx_tipos + 1] if idx_tipos + 1 < len(partes) else None
                            resultado['Total'] = partes[idx_tipos + 2] if idx_tipos + 2 < len(partes) else None
                            resultado['Dias_Cot'] = partes[idx_tipos + 3] if idx_tipos + 3 < len(partes) else None
        
        elif tiene_alta:
            resultado['Situacion'] = 'ALTA'
            match_alta = re.search(r'ALTA\s+(\d{2}-\d{2}-\d{4})\s+(\d{2}-\d{2}-\d{4})\s+(.+)', texto)
            if match_alta:
                resultado['F_Real_Alta'] = match_alta.group(1)
                resultado['F_Efecto_Alta'] = match_alta.group(2)
                texto_datos = match_alta.group(3)
                texto_datos = re.sub(r'\s+[A-Z0-9]{2,4}$', '', texto_datos).strip()
                
                partes = texto_datos.split()
                if len(partes) >= 6:
                    resultado['G_C_M'] = partes[0] if partes[0].isdigit() else None
                    resultado['T_C'] = partes[1] if len(partes) > 1 else None
                    
                    # Detectar C_T_P
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
                        
                        resultado['Tipos_AT_IT'] = partes[idx_tipos] if idx_tipos < len(partes) else None
                        resultado['IMS'] = partes[idx_tipos + 1] if idx_tipos + 1 < len(partes) else None
                        resultado['Total'] = partes[idx_tipos + 2] if idx_tipos + 2 < len(partes) else None
                        resultado['Dias_Cot'] = partes[idx_tipos + 3] if idx_tipos + 3 < len(partes) else None
        
        elif tiene_baja:
            resultado['Situacion'] = 'BAJA'
            # Similar a ALTA pero con 4 fechas
            match_baja = re.search(r'BAJA\s+(\d{2}-\d{2}-\d{4})\s+(\d{2}-\d{2}-\d{4})\s+(\d{2}-\d{2}-\d{4})\s+(\d{2}-\d{2}-\d{4})\s+(.+)', texto)
            if match_baja:
                resultado['F_Real_Alta'] = match_baja.group(1)
                resultado['F_Efecto_Alta'] = match_baja.group(2)
                resultado['F_Real_Sit'] = match_baja.group(3)
                resultado['F_Efecto_Sit'] = match_baja.group(4)
                texto_datos = match_baja.group(5)
                texto_datos = re.sub(r'\s+[A-Z0-9]{2,4}$', '', texto_datos).strip()
                
                partes = texto_datos.split()
                if len(partes) >= 6:
                    resultado['G_C_M'] = partes[0] if partes[0].isdigit() else None
                    resultado['T_C'] = partes[1] if len(partes) > 1 else None
                    
                    # Detectar C_T_P (mismo código que ALTA)
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
                        
                        resultado['Tipos_AT_IT'] = partes[idx_tipos] if idx_tipos < len(partes) else None
                        resultado['IMS'] = partes[idx_tipos + 1] if idx_tipos + 1 < len(partes) else None
                        resultado['Total'] = partes[idx_tipos + 2] if idx_tipos + 2 < len(partes) else None
                        resultado['Dias_Cot'] = partes[idx_tipos + 3] if idx_tipos + 3 < len(partes) else None
        
        return resultado
