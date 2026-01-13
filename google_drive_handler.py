"""
Módulo para trabajar con PDFs directamente desde Google Drive.
Permite descargar y procesar PDFs sin necesidad de descargarlos manualmente.
"""
import logging
import io
from pathlib import Path
from typing import Optional
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import gspread

from config import CREDENTIALS_FILE, TOKEN_FILE, SCOPES

logger = logging.getLogger(__name__)


class GoogleDriveHandler:
    """Manejador para operaciones con Google Drive."""
    
    def __init__(self, credentials_file: Optional[Path] = None, token_file: Optional[Path] = None):
        """
        Inicializa el manejador de Google Drive.
        
        Args:
            credentials_file: Ruta al archivo de credenciales JSON
            token_file: Ruta al archivo de token
        """
        self.credentials_file = Path(credentials_file or CREDENTIALS_FILE)
        self.token_file = Path(token_file or TOKEN_FILE)
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        """Autentica con Google Drive API."""
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
                        f"Archivo de credenciales no encontrado: {self.credentials_file}\n"
                        "Por favor, descarga las credenciales desde Google Cloud Console."
                    )
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.credentials_file), SCOPES
                )
                creds = flow.run_local_server(port=0)
            
            # Guardar credenciales para la próxima vez
            self.token_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.token_file, 'w') as token:
                token.write(creds.to_json())
        
        # Crear servicio de Drive
        self.service = build('drive', 'v3', credentials=creds)
        logger.info("Autenticacion exitosa con Google Drive")
    
    def get_file_id_from_url(self, url: str) -> str:
        """
        Extrae el ID de archivo de una URL de Google Drive.
        
        Args:
            url: URL de Google Drive (formato compartir o ver)
            
        Returns:
            ID del archivo
        """
        # Diferentes formatos de URL de Google Drive
        if '/file/d/' in url:
            # Formato: https://drive.google.com/file/d/FILE_ID/view
            file_id = url.split('/file/d/')[1].split('/')[0]
        elif 'id=' in url:
            # Formato: https://drive.google.com/open?id=FILE_ID
            file_id = url.split('id=')[1].split('&')[0]
        elif '/folders/' in url:
            raise ValueError("La URL es de una carpeta, no de un archivo")
        else:
            # Asumir que es solo el ID
            file_id = url.strip()
        
        return file_id
    
    def download_pdf(self, file_id: str, output_path: Optional[Path] = None) -> Path:
        """
        Descarga un PDF desde Google Drive.
        
        Args:
            file_id: ID del archivo en Google Drive (o URL completa)
            output_path: Ruta donde guardar el PDF (opcional)
            
        Returns:
            Ruta al archivo descargado
        """
        # Si es una URL, extraer el ID
        if 'http' in file_id or 'drive.google.com' in file_id:
            file_id = self.get_file_id_from_url(file_id)
        
        # Obtener información del archivo
        try:
            file_metadata = self.service.files().get(fileId=file_id, fields='name, mimeType').execute()
            file_name = file_metadata.get('name', 'documento.pdf')
            mime_type = file_metadata.get('mimeType', '')
            
            # Verificar que sea un PDF
            if 'pdf' not in mime_type.lower() and not file_name.lower().endswith('.pdf'):
                logger.warning(f"El archivo parece no ser un PDF: {mime_type}")
            
            # Determinar ruta de salida
            if not output_path:
                output_path = Path("data/input") / file_name
            else:
                output_path = Path(output_path)
            
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Descargar archivo
            logger.info(f"Descargando PDF: {file_name}")
            request = self.service.files().get_media(fileId=file_id)
            
            with io.BytesIO() as fh:
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while not done:
                    status, done = downloader.next_chunk()
                    if status:
                        logger.info(f"  Progreso: {int(status.progress() * 100)}%")
                
                # Guardar archivo
                with open(output_path, 'wb') as f:
                    f.write(fh.getvalue())
            
            logger.info(f"PDF descargado: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error descargando PDF: {e}")
            raise
    
    def list_pdfs_in_folder(self, folder_id: str) -> list:
        """
        Lista todos los PDFs en una carpeta de Google Drive.
        
        Args:
            folder_id: ID de la carpeta en Google Drive
            
        Returns:
            Lista de diccionarios con información de los PDFs
        """
        try:
            # Buscar archivos PDF en la carpeta
            query = f"'{folder_id}' in parents and mimeType='application/pdf' and trashed=false"
            
            results = self.service.files().list(
                q=query,
                fields="files(id, name, modifiedTime, size)"
            ).execute()
            
            files = results.get('files', [])
            logger.info(f"Encontrados {len(files)} PDFs en la carpeta")
            
            return files
            
        except Exception as e:
            logger.error(f"Error listando PDFs: {e}")
            return []
    
    def search_pdf_by_name(self, name: str) -> list:
        """
        Busca PDFs por nombre en Google Drive.
        
        Args:
            name: Nombre o parte del nombre del archivo
            
        Returns:
            Lista de archivos encontrados
        """
        try:
            query = f"name contains '{name}' and mimeType='application/pdf' and trashed=false"
            
            results = self.service.files().list(
                q=query,
                fields="files(id, name, modifiedTime)"
            ).execute()
            
            files = results.get('files', [])
            return files
            
        except Exception as e:
            logger.error(f"Error buscando PDF: {e}")
            return []

