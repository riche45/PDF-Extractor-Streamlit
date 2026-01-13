"""
Script principal para procesamiento de PDFs y actualización de Google Sheets.
"""
import argparse
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict
import pandas as pd

from config import (
    INPUT_DIR, OUTPUT_DIR, REPORTS_DIR, LOGS_DIR,
    GOOGLE_SHEET_ID, GOOGLE_SHEET_NAME, LOG_LEVEL
)
from pdf_extractor import PDFExtractor
from data_processor import DataProcessor
from data_analyzer import DataAnalyzer
from google_sheets_handler import GoogleSheetsHandler
from google_drive_handler import GoogleDriveHandler

# Configurar logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / 'extraction.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def process_pdf(pdf_path: Path, sheet_id: str = None, sheet_name: str = None,
                method: str = "auto", analyze: bool = True, update_sheet: bool = True) -> bool:
    """
    Procesa un PDF completo: extracción, análisis y actualización.
    
    Args:
        pdf_path: Ruta al archivo PDF
        sheet_id: ID de Google Sheet (opcional, usa config si no se proporciona)
        sheet_name: Nombre de la hoja (opcional)
        method: Método de extracción
        analyze: Si True, genera análisis exploratorio
        update_sheet: Si True, actualiza Google Sheets
        
    Returns:
        True si el proceso fue exitoso
    """
    try:
        logger.info(f"=" * 60)
        logger.info(f"Procesando PDF: {pdf_path.name}")
        logger.info(f"=" * 60)
        
        # 1. Extracción
        logger.info("\n[1/4] Extrayendo datos del PDF...")
        extractor = PDFExtractor(method=method)
        pdf_info = extractor.get_pdf_info(pdf_path)
        logger.info(f"  Páginas: {pdf_info['pages']}, Tamaño: {pdf_info['size_mb']:.2f} MB")
        
        df = extractor.extract_all_tables(pdf_path)
        
        if df.empty:
            logger.error("No se pudieron extraer datos del PDF")
            return False
        
        logger.info(f"✓ Datos extraídos: {len(df)} filas, {len(df.columns)} columnas")
        
        # Guardar datos crudos
        output_file = OUTPUT_DIR / f"{pdf_path.stem}_raw.csv"
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        logger.info(f"  Datos guardados en: {output_file}")
        
        # 2. Procesamiento y limpieza
        logger.info("\n[2/4] Limpiando y procesando datos...")
        processor = DataProcessor()
        df_clean = processor.clean_dataframe(df)
        
        # Validación
        validation = processor.validate_data(df_clean)
        if not validation['is_valid']:
            logger.warning("⚠️ Problemas de validación encontrados:")
            for error in validation['errors']:
                logger.warning(f"  - {error}")
        
        if validation['warnings']:
            for warning in validation['warnings']:
                logger.warning(f"  ⚠️ {warning}")
        
        # Guardar datos limpios
        output_file_clean = OUTPUT_DIR / f"{pdf_path.stem}_clean.csv"
        df_clean.to_csv(output_file_clean, index=False, encoding='utf-8-sig')
        logger.info(f"✓ Datos limpios guardados en: {output_file_clean}")
        
        # 3. Análisis exploratorio
        if analyze:
            logger.info("\n[3/4] Generando análisis exploratorio...")
            analyzer = DataAnalyzer(output_dir=REPORTS_DIR)
            analysis_results = analyzer.analyze(df_clean, output_name=pdf_path.stem)
            
            logger.info("✓ Análisis completado")
            logger.info(f"  Completitud: {analysis_results['data_quality']['completeness_score']}%")
            logger.info(f"  Filas duplicadas: {analysis_results['data_quality']['duplicate_rows']}")
            
            if analysis_results['recommendations']:
                logger.info("\n  Recomendaciones:")
                for rec in analysis_results['recommendations']:
                    logger.info(f"    {rec}")
        
        # 4. Actualización de Google Sheets
        if update_sheet:
            logger.info("\n[4/4] Actualizando Google Sheets...")
            
            if not sheet_id:
                sheet_id = GOOGLE_SHEET_ID
            
            if not sheet_id:
                logger.error("No se proporcionó ID de Google Sheet")
                return False
            
            try:
                sheets_handler = GoogleSheetsHandler()
                
                # Leer datos existentes para comparar
                try:
                    existing_df = sheets_handler.read_sheet(sheet_id, sheet_name)
                    logger.info(f"  Datos existentes: {len(existing_df)} filas")
                    
                    # Intentar actualización inteligente si hay columna ID
                    id_columns = [col for col in df_clean.columns if 'id' in col.lower()]
                    if id_columns:
                        key_column = id_columns[0]
                        logger.info(f"  Usando columna '{key_column}' como clave")
                        success = sheets_handler.find_and_update(
                            df_clean, sheet_id, key_column, sheet_name
                        )
                    else:
                        # Actualización completa
                        success = sheets_handler.write_dataframe(
                            df_clean, sheet_id, sheet_name, clear_first=True
                        )
                except Exception as e:
                    logger.warning(f"  No se pudieron leer datos existentes: {e}")
                    logger.info("  Escribiendo datos nuevos...")
                    success = sheets_handler.write_dataframe(
                        df_clean, sheet_id, sheet_name, clear_first=True
                    )
                
                if success:
                    logger.info("✓ Google Sheets actualizado exitosamente")
                else:
                    logger.error("✗ Error actualizando Google Sheets")
                    return False
                    
            except Exception as e:
                logger.error(f"Error con Google Sheets: {e}")
                logger.error("  Verifica tus credenciales y permisos")
                return False
        
        logger.info("\n" + "=" * 60)
        logger.info("✓ Procesamiento completado exitosamente")
        logger.info("=" * 60 + "\n")
        
        return True
        
    except Exception as e:
        logger.error(f"Error procesando PDF: {e}", exc_info=True)
        return False


def process_folder(folder_path: Path, sheet_id: str = None, **kwargs) -> Dict:
    """
    Procesa múltiples PDFs de una carpeta.
    
    Args:
        folder_path: Ruta a la carpeta con PDFs
        sheet_id: ID de Google Sheet
        **kwargs: Argumentos adicionales para process_pdf
        
    Returns:
        Diccionario con resultados del procesamiento
    """
    pdf_files = list(folder_path.glob("*.pdf"))
    
    if not pdf_files:
        logger.warning(f"No se encontraron PDFs en {folder_path}")
        return {'success': 0, 'failed': 0, 'total': 0}
    
    logger.info(f"Procesando {len(pdf_files)} archivos PDF...")
    
    results = {'success': 0, 'failed': 0, 'total': len(pdf_files), 'files': []}
    
    for pdf_file in pdf_files:
        logger.info(f"\n{'='*60}")
        logger.info(f"Archivo: {pdf_file.name}")
        logger.info(f"{'='*60}")
        
        success = process_pdf(pdf_file, sheet_id=sheet_id, **kwargs)
        
        if success:
            results['success'] += 1
            results['files'].append({'file': pdf_file.name, 'status': 'success'})
        else:
            results['failed'] += 1
            results['files'].append({'file': pdf_file.name, 'status': 'failed'})
    
    logger.info(f"\n{'='*60}")
    logger.info(f"Resumen: {results['success']}/{results['total']} exitosos")
    logger.info(f"{'='*60}\n")
    
    return results


def main():
    """Función principal."""
    parser = argparse.ArgumentParser(
        description="Sistema de extracción de PDFs y actualización de Google Sheets"
    )
    
    parser.add_argument(
        '--pdf',
        type=str,
        help='Ruta al archivo PDF a procesar (local) o URL/ID de Google Drive'
    )
    
    parser.add_argument(
        '--drive-url',
        type=str,
        help='URL o ID de PDF en Google Drive (alternativa a --pdf)'
    )
    
    parser.add_argument(
        '--folder',
        type=str,
        help='Carpeta con PDFs a procesar'
    )
    
    parser.add_argument(
        '--sheet-id',
        type=str,
        help='ID de Google Sheet (o usar variable de entorno)'
    )
    
    parser.add_argument(
        '--sheet-name',
        type=str,
        help='Nombre de la hoja específica (opcional)'
    )
    
    parser.add_argument(
        '--method',
        type=str,
        default='auto',
        choices=['auto', 'pdfplumber', 'camelot', 'tabula', 'pymupdf'],
        help='Método de extracción (default: auto)'
    )
    
    parser.add_argument(
        '--no-analyze',
        action='store_true',
        help='Omitir análisis exploratorio'
    )
    
    parser.add_argument(
        '--no-update',
        action='store_true',
        help='No actualizar Google Sheets (solo extraer y analizar)'
    )
    
    args = parser.parse_args()
    
    # Validar argumentos
    if not args.pdf and not args.folder and not args.drive_url:
        parser.error("Debes proporcionar --pdf, --folder o --drive-url")
    
    # Procesar
    if args.drive_url:
        # Descargar desde Google Drive
        logger.info("Descargando PDF desde Google Drive...")
        try:
            drive_handler = GoogleDriveHandler()
            pdf_path = drive_handler.download_pdf(args.drive_url)
            logger.info(f"PDF descargado: {pdf_path}")
        except Exception as e:
            logger.error(f"Error descargando desde Google Drive: {e}")
            sys.exit(1)
        
        success = process_pdf(
            pdf_path,
            sheet_id=args.sheet_id,
            sheet_name=args.sheet_name,
            method=args.method,
            analyze=not args.no_analyze,
            update_sheet=not args.no_update
        )
        
        sys.exit(0 if success else 1)
    
    elif args.pdf:
        # Verificar si es URL de Google Drive
        if 'drive.google.com' in args.pdf or len(args.pdf) > 50:
            logger.info("Detectada URL de Google Drive, descargando...")
            try:
                drive_handler = GoogleDriveHandler()
                pdf_path = drive_handler.download_pdf(args.pdf)
            except Exception as e:
                logger.error(f"Error descargando desde Google Drive: {e}")
                sys.exit(1)
        else:
            pdf_path = Path(args.pdf)
            if not pdf_path.exists():
                logger.error(f"PDF no encontrado: {pdf_path}")
                sys.exit(1)
        
        success = process_pdf(
            pdf_path,
            sheet_id=args.sheet_id,
            sheet_name=args.sheet_name,
            method=args.method,
            analyze=not args.no_analyze,
            update_sheet=not args.no_update
        )
        
        sys.exit(0 if success else 1)
    
    elif args.folder:
        folder_path = Path(args.folder)
        if not folder_path.exists():
            logger.error(f"Carpeta no encontrada: {folder_path}")
            sys.exit(1)
        
        results = process_folder(
            folder_path,
            sheet_id=args.sheet_id,
            sheet_name=args.sheet_name,
            method=args.method,
            analyze=not args.no_analyze,
            update_sheet=not args.no_update
        )
        
        sys.exit(0 if results['failed'] == 0 else 1)


if __name__ == "__main__":
    main()

