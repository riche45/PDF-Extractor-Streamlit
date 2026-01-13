"""
Configuración centralizada del sistema de extracción y actualización de datos.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Rutas del proyecto
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
INPUT_DIR = DATA_DIR / "input"
OUTPUT_DIR = DATA_DIR / "output"
REPORTS_DIR = DATA_DIR / "reports"
LOGS_DIR = PROJECT_ROOT / "logs"

# Crear directorios si no existen
for directory in [INPUT_DIR, OUTPUT_DIR, REPORTS_DIR, LOGS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Configuración de Google Sheets
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "")
GOOGLE_SHEET_NAME = os.getenv("GOOGLE_SHEET_NAME", "DATOS")
CREDENTIALS_FILE = PROJECT_ROOT / "credentials.json"
TOKEN_FILE = PROJECT_ROOT / "token.json"

# Configuración de extracción
EXTRACTION_METHOD = os.getenv("EXTRACTION_METHOD", "auto")  # auto, pdfplumber, camelot, tabula, pymupdf
OUTPUT_FORMAT = os.getenv("OUTPUT_FORMAT", "csv")  # csv, excel, json

# Configuración de logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = LOGS_DIR / "extraction.log"

# Configuración de análisis
ANALYSIS_OUTPUT_FORMAT = "html"  # html, pdf, json

# Métodos de extracción disponibles (en orden de preferencia)
EXTRACTION_METHODS = ["pdfplumber", "camelot", "tabula", "pymupdf", "PyPDF2"]

# Configuración de validación de datos
REQUIRED_COLUMNS = []  # Se puede personalizar según el tipo de documento
DATE_FORMATS = ["%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d", "%d-%m-%y", "%d/%m/%y"]

# Configuración de Google Sheets y Google Drive
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive.readonly"  # Para leer PDFs desde Drive
]

