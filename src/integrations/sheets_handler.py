"""
Módulo para interactuar con Google Sheets API.
Permite leer, escribir y actualizar datos en hojas de cálculo de Google.
Soporta tanto OAuth 2.0 como Service Account.
"""
import logging
import pandas as pd
from pathlib import Path
from typing import Optional, List, Dict
import gspread
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
import os
import json

try:
    from config import CREDENTIALS_FILE, TOKEN_FILE, SCOPES, GOOGLE_SHEET_NAME
except:
    # Valores por defecto si config no está disponible
    CREDENTIALS_FILE = Path("credentials.json")
    TOKEN_FILE = Path("token.json")
    SCOPES = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.file"
    ]
    GOOGLE_SHEET_NAME = "DATOS"

logger = logging.getLogger(__name__)


class GoogleSheetsHandler:
    """Manejador para operaciones con Google Sheets."""
    
    def __init__(self, credentials_file: Optional[Path] = None, 
                 token_file: Optional[Path] = None,
                 service_account_file: Optional[Path] = None):
        """
        Inicializa el manejador de Google Sheets.
        
        Args:
            credentials_file: Ruta al archivo de credenciales OAuth JSON
            token_file: Ruta al archivo de token (se crea automáticamente)
            service_account_file: Ruta al archivo de Service Account JSON (opcional, preferido)
        """
        self.credentials_file = Path(credentials_file or CREDENTIALS_FILE)
        self.token_file = Path(token_file or TOKEN_FILE)
        self.service_account_file = Path(service_account_file or "service_account.json")
        self.client = None
        self.auth_method = None
        self._authenticate()
    
    def _authenticate(self):
        """
        Autentica con Google Sheets API.
        Prioriza Service Account sobre OAuth para despliegues.
        """
        # OPCIÓN 1: Service Account (preferido para producción)
        if self.service_account_file.exists():
            try:
                logger.info("Usando Service Account para autenticación...")
                creds = service_account.Credentials.from_service_account_file(
                    str(self.service_account_file),
                    scopes=SCOPES
                )
                self.client = gspread.authorize(creds)
                self.auth_method = "service_account"
                logger.info("✓ Autenticación exitosa con Service Account")
                return
            except Exception as e:
                logger.warning(f"Error con Service Account: {e}")
                logger.info("Intentando con OAuth 2.0...")
        
        # OPCIÓN 2: OAuth 2.0 (para desarrollo local)
        creds = None
        
        # Cargar token existente si existe
        if self.token_file.exists():
            try:
                creds = Credentials.from_authorized_user_file(str(self.token_file), SCOPES)
            except Exception as e:
                logger.warning(f"Error cargando token: {e}")
        
        # Si no hay credenciales válidas, solicitar autorización
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    logger.error(f"Error refrescando token: {e}")
                    creds = None
            
            if not creds:
                if not self.credentials_file.exists():
                    raise FileNotFoundError(
                        f"No se encontraron credenciales:\n"
                        f"- Service Account: {self.service_account_file} (recomendado)\n"
                        f"- OAuth 2.0: {self.credentials_file}\n\n"
                        "Por favor, configura al menos uno de los métodos de autenticación."
                    )
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.credentials_file), SCOPES
                )
                creds = flow.run_local_server(port=0)
            
            # Guardar credenciales para la próxima vez
            self.token_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.token_file, 'w') as token:
                token.write(creds.to_json())
        
        # Crear cliente de gspread
        self.client = gspread.authorize(creds)
        self.auth_method = "oauth"
        logger.info("✓ Autenticación exitosa con OAuth 2.0")
    
    def open_sheet(self, sheet_id: str, sheet_name: Optional[str] = None) -> gspread.Spreadsheet:
        """
        Abre una hoja de cálculo.
        
        Args:
            sheet_id: ID de la hoja de cálculo
            sheet_name: Nombre de la hoja específica (opcional)
            
        Returns:
            Objeto Spreadsheet o Worksheet
        """
        try:
            spreadsheet = self.client.open_by_key(sheet_id)
            if sheet_name:
                try:
                    return spreadsheet.worksheet(sheet_name)
                except gspread.exceptions.WorksheetNotFound:
                    # Si no encuentra la hoja, usar la primera hoja disponible
                    logger.warning(f"Hoja '{sheet_name}' no encontrada. Usando primera hoja disponible.")
                    return spreadsheet.sheet1
            return spreadsheet
        except Exception as e:
            logger.error(f"Error abriendo hoja: {e}")
            # Intentar con método alternativo
            try:
                spreadsheet = self.client.open_by_key(sheet_id)
                return spreadsheet.sheet1
            except:
                raise
    
    def read_sheet(self, sheet_id: str, sheet_name: Optional[str] = None) -> pd.DataFrame:
        """
        Lee una hoja completa como DataFrame.
        
        Args:
            sheet_id: ID de la hoja de cálculo
            sheet_name: Nombre de la hoja específica
            
        Returns:
            DataFrame con los datos de la hoja
        """
        worksheet = self.open_sheet(sheet_id, sheet_name or GOOGLE_SHEET_NAME)
        records = worksheet.get_all_records()
        return pd.DataFrame(records)
    
    def write_dataframe(self, df: pd.DataFrame, sheet_id: str, 
                       sheet_name: Optional[str] = None, 
                       start_cell: str = "A1",
                       clear_first: bool = False) -> bool:
        """
        Escribe un DataFrame en Google Sheets.
        
        Args:
            df: DataFrame a escribir
            sheet_id: ID de la hoja de cálculo
            sheet_name: Nombre de la hoja específica
            start_cell: Celda inicial (ej: "A1")
            clear_first: Si True, limpia la hoja antes de escribir
            
        Returns:
            True si fue exitoso
        """
        try:
            # Intentar método estándar primero
            try:
                worksheet = self.open_sheet(sheet_id, sheet_name or GOOGLE_SHEET_NAME)
                
                if clear_first:
                    worksheet.clear()
                
                # Preparar datos (incluir headers)
                values = [df.columns.tolist()] + df.fillna('').astype(str).values.tolist()
                
                # Escribir datos
                worksheet.update(start_cell, values)
                
                logger.info(f"Datos escritos exitosamente en {sheet_name or GOOGLE_SHEET_NAME}")
                return True
            except Exception as e1:
                # Si falla, intentar con método alternativo usando API directa
                logger.warning(f"Método estándar falló: {e1}")
                logger.info("Intentando método alternativo con API directa...")
                
                from googleapiclient.discovery import build
                from google.oauth2.credentials import Credentials
                
                # Obtener credenciales del token
                if self.token_file.exists():
                    creds = Credentials.from_authorized_user_file(str(self.token_file), SCOPES)
                else:
                    raise Exception("No se encontraron credenciales")
                
                service = build('sheets', 'v4', credentials=creds)
                
                # Preparar datos
                values = [df.columns.tolist()] + df.fillna('').astype(str).values.tolist()
                
                # Determinar rango
                range_name = f"{sheet_name or 'Sheet1'}!{start_cell}"
                
                # Limpiar si es necesario
                if clear_first:
                    service.spreadsheets().values().clear(
                        spreadsheetId=sheet_id,
                        range=range_name
                    ).execute()
                
                # Escribir datos
                body = {'values': values}
                result = service.spreadsheets().values().update(
                    spreadsheetId=sheet_id,
                    range=range_name,
                    valueInputOption='RAW',
                    body=body
                ).execute()
                
                logger.info(f"Datos escritos exitosamente usando API directa")
                return True
            
        except Exception as e:
            logger.error(f"Error escribiendo datos: {e}")
            return False
    
    def append_dataframe(self, df: pd.DataFrame, sheet_id: str,
                        sheet_name: Optional[str] = None) -> bool:
        """
        Añade datos al final de una hoja existente.
        
        Args:
            df: DataFrame a añadir
            sheet_id: ID de la hoja de cálculo
            sheet_name: Nombre de la hoja específica
            
        Returns:
            True si fue exitoso
        """
        try:
            worksheet = self.open_sheet(sheet_id, sheet_name or GOOGLE_SHEET_NAME)
            
            # Preparar datos (sin headers)
            values = df.fillna('').astype(str).values.tolist()
            
            # Añadir datos
            worksheet.append_rows(values)
            
            logger.info(f"✓ Datos añadidos exitosamente a {sheet_name or GOOGLE_SHEET_NAME}")
            return True
            
        except Exception as e:
            logger.error(f"Error añadiendo datos: {e}")
            return False
    
    def update_cells(self, sheet_id: str, updates: List[Dict],
                    sheet_name: Optional[str] = None) -> bool:
        """
        Actualiza celdas específicas.
        
        Args:
            sheet_id: ID de la hoja de cálculo
            updates: Lista de diccionarios con formato:
                    [{'range': 'A1', 'values': [['valor']]}, ...]
            sheet_name: Nombre de la hoja específica
            
        Returns:
            True si fue exitoso
        """
        try:
            worksheet = self.open_sheet(sheet_id, sheet_name or GOOGLE_SHEET_NAME)
            worksheet.batch_update(updates)
            logger.info(f"✓ Celdas actualizadas exitosamente")
            return True
        except Exception as e:
            logger.error(f"Error actualizando celdas: {e}")
            return False
    
    def find_and_update(self, df: pd.DataFrame, sheet_id: str,
                       key_column: str, sheet_name: Optional[str] = None) -> bool:
        """
        Actualiza filas existentes basándose en una columna clave.
        
        Args:
            df: DataFrame con datos a actualizar
            sheet_id: ID de la hoja de cálculo
            key_column: Nombre de la columna que se usa como clave
            sheet_name: Nombre de la hoja específica
            
        Returns:
            True si fue exitoso
        """
        try:
            worksheet = self.open_sheet(sheet_id, sheet_name or GOOGLE_SHEET_NAME)
            
            # Leer datos existentes
            existing_df = self.read_sheet(sheet_id, sheet_name)
            
            if key_column not in existing_df.columns:
                logger.error(f"Columna clave '{key_column}' no encontrada en la hoja")
                return False
            
            if key_column not in df.columns:
                logger.error(f"Columna clave '{key_column}' no encontrada en los datos nuevos")
                return False
            
            # Obtener headers
            headers = worksheet.row_values(1)
            key_col_index = headers.index(key_column)
            
            updates = []
            for _, new_row in df.iterrows():
                key_value = str(new_row[key_column])
                
                # Buscar fila existente
                try:
                    cell = worksheet.find(key_value, in_column=key_col_index + 1)
                    row_num = cell.row
                    
                    # Preparar actualización
                    for col in df.columns:
                        if col in headers:
                            col_index = headers.index(col)
                            cell_address = f"{chr(65 + col_index)}{row_num}"
                            updates.append({
                                'range': f"{sheet_name or GOOGLE_SHEET_NAME}!{cell_address}",
                                'values': [[str(new_row[col])]]
                            })
                except gspread.exceptions.CellNotFound:
                    # Si no se encuentra, añadir nueva fila
                    logger.info(f"Nueva fila encontrada para {key_column}={key_value}")
                    self.append_dataframe(pd.DataFrame([new_row]), sheet_id, sheet_name)
            
            if updates:
                self.update_cells(sheet_id, updates, sheet_name)
            
            logger.info(f"✓ Actualización completada")
            return True
            
        except Exception as e:
            logger.error(f"Error en find_and_update: {e}")
            return False
    
    def get_sheet_info(self, sheet_id: str) -> Dict:
        """
        Obtiene información sobre la hoja de cálculo.
        
        Args:
            sheet_id: ID de la hoja de cálculo
            
        Returns:
            Diccionario con información de la hoja
        """
        try:
            spreadsheet = self.client.open_by_key(sheet_id)
            worksheets = spreadsheet.worksheets()
            
            info = {
                'title': spreadsheet.title,
                'id': sheet_id,
                'worksheets': [{'name': ws.title, 'id': ws.id} for ws in worksheets],
                'url': spreadsheet.url
            }
            
            return info
        except Exception as e:
            logger.error(f"Error obteniendo info de la hoja: {e}")
            return {}

