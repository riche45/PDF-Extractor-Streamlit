"""
Aplicación Streamlit para extracción de datos de PDFs.
Interfaz profesional y intuitiva para procesar documentos.
"""

import streamlit as st
import pandas as pd
from pathlib import Path
import time
import logging
from typing import Optional

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Importar módulos del sistema
try:
    from src.templates import VidaLaboralSecuenciaTemplate
    from src.utils.file_handlers import FileHandler
except ImportError as e:
    st.error(f"Error importando módulos: {e}")
    st.error("Asegúrate de que la estructura src/ esté correctamente configurada")
    st.stop()

# Importar integraciones de Google (opcional)
GOOGLE_AVAILABLE = False
try:
    from src.integrations import GoogleDriveHandler, GoogleSheetsHandler
    GOOGLE_AVAILABLE = True
except ImportError:
    logger.info("Integraciones de Google no disponibles (modo local solamente)")
    pass


# Configuración de la página
st.set_page_config(
    page_title="📊 Extractor de PDFs",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #1f77b4;
        font-size: 2.5em;
        margin-bottom: 1em;
    }
    .sub-header {
        color: #2c3e50;
        font-size: 1.5em;
        margin-bottom: 1em;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 1em;
        border-radius: 5px;
        margin: 1em 0;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        color: #856404;
        padding: 1em;
        border-radius: 5px;
        margin: 1em 0;
    }
    .error-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        padding: 1em;
        border-radius: 5px;
        margin: 1em 0;
    }
    .info-box {
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        color: #0c5460;
        padding: 1em;
        border-radius: 5px;
        margin: 1em 0;
    }
    
    /* Ocultar menú de GitHub y elementos no deseados */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Ocultar botón de GitHub en el toolbar */
    .viewerBadge_container__1QSob {display: none;}
    button[kind="header"] {display: none;}
    
    /* Ocultar el botón "Deploy" y "GitHub" */
    [data-testid="stToolbar"] {display: none;}
    
    /* Ocultar badge de perfil del creador (esquina inferior derecha) - FORZADO */
    [data-testid="stCommunityCloudStatusOverlay"] {display: none !important;}
    .stCommunityCloudStatusOverlay {display: none !important;}
    .viewerBadge_link__qRIco {display: none !important;}
    .viewerBadge_container__r5tak {display: none !important;}
    .viewerBadge_container__1QSob {display: none !important;}
    
    /* Ocultar cualquier elemento de perfil/usuario */
    iframe[title*="Streamlit Community Cloud"] {display: none !important;}
    iframe[title*="streamlit_community_cloud"] {display: none !important;}
    
    /* Ocultar todos los badges y overlays posibles */
    div[class*="viewerBadge"] {display: none !important;}
    div[class*="ViewerBadge"] {display: none !important;}
    div[data-testid*="badge"] {display: none !important;}
    
    /* Ocultar elementos flotantes en esquinas */
    div[style*="position: fixed"][style*="bottom"][style*="right"] {display: none !important;}
    
    /* Selector más específico para el badge de Community Cloud */
    .main > div[style*="position: fixed"] {display: none !important;}
    
    /* Estilo profesional sin marca de Streamlit */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# JavaScript para remover elementos del DOM dinámicamente
st.markdown("""
<script>
    // Función para remover el badge de Streamlit
    function removeBadges() {
        // Remover por atributos data-testid
        const testIds = [
            'stCommunityCloudStatusOverlay',
            'stToolbar',
            'stDecoration',
            'stHeader'
        ];
        testIds.forEach(id => {
            const elements = document.querySelectorAll(`[data-testid="${id}"]`);
            elements.forEach(el => el.remove());
        });
        
        // Remover por clases parciales
        const classPatterns = ['viewerBadge', 'ViewerBadge', 'StatusWidget'];
        classPatterns.forEach(pattern => {
            const elements = document.querySelectorAll(`[class*="${pattern}"]`);
            elements.forEach(el => el.remove());
        });
        
        // Remover iframes de Streamlit
        const iframes = document.querySelectorAll('iframe');
        iframes.forEach(iframe => {
            const title = iframe.getAttribute('title') || '';
            if (title.includes('streamlit') || title.includes('Streamlit')) {
                iframe.remove();
            }
        });
        
        // Remover elementos fixed en esquina inferior derecha
        const allDivs = document.querySelectorAll('div');
        allDivs.forEach(div => {
            const style = window.getComputedStyle(div);
            if (style.position === 'fixed' && 
                parseInt(style.bottom) < 100 && 
                parseInt(style.right) < 200) {
                // Verificar si contiene links o badges
                if (div.querySelector('a') || div.querySelector('button') || 
                    div.textContent.includes('Hosted') || div.textContent.includes('View profile')) {
                    div.remove();
                }
            }
        });
    }
    
    // Ejecutar inmediatamente
    removeBadges();
    
    // Ejecutar cada 500ms para capturar elementos que se cargan dinámicamente
    setInterval(removeBadges, 500);
    
    // Ejecutar cuando el DOM cambie
    const observer = new MutationObserver(removeBadges);
    observer.observe(document.body, { childList: true, subtree: true });
</script>
""", unsafe_allow_html=True)


def main():
    """Función principal de la aplicación."""

    # Título principal
    st.markdown('<h1 class="main-header">📊 Extractor de Datos PDF</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; font-size: 1.2em; color: #666;">Extrae y procesa datos de documentos PDF a Excel</p>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; color: #888;">CLARA RUIZ COMPANY</p>', unsafe_allow_html=True)

    # Sidebar para configuración
    with st.sidebar:
        st.markdown("## ⚙️ Configuración")

        # Selección de plantilla
        st.markdown("### 📋 Tipo de Documento")
        plantilla_seleccionada = st.selectbox(
            "Selecciona el tipo de documento:",
            ["Vida Laboral", "Nóminas", "Facturas"],
            help="Elige el tipo de documento que quieres procesar"
        )

        # Opciones de procesamiento
        st.markdown("### 🔧 Opciones")

        mostrar_preview = st.checkbox("Mostrar vista previa", value=True,
                                    help="Muestra una preview de los datos antes de descargar")

        formato_salida = st.selectbox(
            "Formato de salida:",
            ["Excel (.xlsx)", "CSV (.csv)", "JSON (.json)"],
            help="Formato en el que quieres descargar los datos"
        )

        # Opciones adicionales
        st.markdown("---")
        st.markdown("### 🎨 Personalización")
        
        incluir_metadatos = st.checkbox(
            "📋 Incluir metadatos del documento",
            value=True,
            help="Incluye información adicional como fecha de procesamiento"
        )
        
        # Variables para compatibilidad (deshabilitadas)
        modo_google = False
        leer_desde_drive = False
        actualizar_sheets = False
        sheet_id = None
        sheet_name = None

        # Información del sistema
        st.markdown("---")
        st.markdown("### ℹ️ Información")
        st.markdown(f"**Plantilla:** {plantilla_seleccionada}")
        st.markdown(f"**Formato:** {formato_salida}")
        st.markdown(f"**Versión:** 1.0.0")
        st.markdown("")
        st.markdown("💼 **Compatible con Microsoft Office**")
        
        # Estadísticas (movidas al sidebar)
        st.markdown("---")
        st.markdown("### 📊 Estadísticas")
        
        # Estadísticas de ejemplo (se actualizarían con datos reales)
        stats = {
            "Documentos procesados": 0,
            "Filas extraídas": 0,
            "Tiempo promedio": "0s",
            "Tasa de éxito": "0%"
        }
        
        for key, value in stats.items():
            st.metric(key, value)
        
        # Tipos de documentos soportados
        st.markdown("---")
        st.markdown("### 🎯 Documentos Soportados")
        documentos = {
            "Vida Laboral": "Datos de empleados y contratos",
            "Facturas": "Datos de proveedores y montos",
            "Personalizado": "Configuración avanzada"
        }
        
        for doc, desc in documentos.items():
            if doc == plantilla_seleccionada:
                st.markdown(f"✅ **{doc}**: {desc}")
            else:
                st.markdown(f"○ {doc}: {desc}")

    # Área principal centrada
    st.markdown('<div style="max-width: 800px; margin: 0 auto;">', unsafe_allow_html=True)
    st.markdown('<h2 class="sub-header" style="text-align: center;">📤 Subir Documento</h2>', unsafe_allow_html=True)
    
    # Upload de archivo
    uploaded_file = st.file_uploader(
        "Arrastra y suelta o selecciona un archivo PDF",
        type=['pdf'],
        help="Formatos soportados: PDF"
    )

    if uploaded_file is not None:
        # Información del archivo
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("### 📄 Información del Archivo")
            file_details = {
                "Nombre": uploaded_file.name,
                "Tamaño": f"{uploaded_file.size / 1024:.1f} KB",
                "Tipo": uploaded_file.type
            }
            info_df = pd.DataFrame(list(file_details.items()), columns=['Propiedad', 'Valor'])
            st.dataframe(info_df, use_container_width=True)
        
        with col2:
            st.markdown("###")  # Spacing
            # Botón de procesamiento centrado
            if st.button("🚀 Procesar Documento", type="primary", use_container_width=True, key="process_btn"):
                opciones_google = {
                    'actualizar_sheets': actualizar_sheets if modo_google else False,
                    'sheet_id': sheet_id if modo_google else None,
                    'sheet_name': sheet_name if modo_google else 'DATOS'
                }
                procesar_documento(uploaded_file, plantilla_seleccionada, formato_salida, 
                                 mostrar_preview, opciones_google)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Espaciado antes del footer
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    
    # Footer integrado (instrucciones + información)
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; padding: 30px 20px;'>"
        "<div style='color: #888; font-size: 0.85em; margin-bottom: 15px;'>📖 Instrucciones de Uso</div>"
        "<div style='color: #666; font-size: 0.8em; margin-bottom: 20px;'>"
        "1️⃣ Sube tu PDF · 2️⃣ Selecciona tipo de documento · 3️⃣ Configura opciones · 4️⃣ Procesa · 5️⃣ Descarga"
        "</div>"
        "<div style='color: #666; font-size: 0.8em; border-top: 1px solid #333; padding-top: 15px;'>"
        "💼 Compatible con Microsoft Office | 🔒 Procesamiento local seguro | ⚡ Optimizado para equipos contables"
        "</div>"
        "</div>",
        unsafe_allow_html=True
    )


def procesar_documento(uploaded_file, plantilla: str, formato: str, preview: bool, 
                      opciones_google: dict = None):
    """
    Procesa el documento subido.

    Args:
        uploaded_file: Archivo subido por el usuario
        plantilla: Tipo de plantilla seleccionada
        formato: Formato de salida
        preview: Si mostrar preview
        opciones_google: Configuración de integración con Google
    """
    
    if opciones_google is None:
        opciones_google = {'actualizar_sheets': False, 'sheet_id': None, 'sheet_name': 'DATOS'}

    # Crear barra de progreso
    progress_bar = st.progress(0)
    status_text = st.empty()

    try:
        # Paso 1: Guardar archivo temporalmente
        status_text.text("📁 Guardando archivo...")
        progress_bar.progress(10)

        temp_path = Path(f"temp_{uploaded_file.name}")
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getvalue())

        # Paso 2: Inicializar plantilla
        status_text.text("🔧 Inicializando plantilla...")
        progress_bar.progress(25)

        if plantilla == "Vida Laboral":
            template = VidaLaboralSecuenciaTemplate()
        else:
            st.error(f"Plantilla '{plantilla}' aún no implementada")
            return

        # Paso 3: Procesar documento
        status_text.text("⚙️ Procesando documento...")
        progress_bar.progress(50)

        resultado = template.process_pdf(temp_path)

        if not resultado['success']:
            st.error(f"Error procesando documento: {resultado.get('error', 'Error desconocido')}")
            return

        df = resultado['data']

        # Paso 4: Mostrar resultados
        status_text.text("✅ Procesamiento completado")
        progress_bar.progress(80)

        # Información de validación
        validation = resultado.get('validation', {})
        if validation.get('warnings'):
            st.markdown('<div class="warning-box">', unsafe_allow_html=True)
            st.markdown("### ⚠️ Advertencias")
            for warning in validation['warnings']:
                st.markdown(f"- {warning}")
            st.markdown('</div>', unsafe_allow_html=True)

        # Estadísticas
        st.markdown('<div class="success-box">', unsafe_allow_html=True)
        st.markdown("### ✅ Procesamiento Exitoso")
        col_stats1, col_stats2, col_stats3 = st.columns(3)
        with col_stats1:
            st.metric("Filas extraídas", len(df))
        with col_stats2:
            st.metric("Columnas", len(df.columns))
        with col_stats3:
            st.metric("Plantilla", plantilla)
        st.markdown('</div>', unsafe_allow_html=True)

        # Preview de datos
        if preview and not df.empty:
            st.markdown("### 👀 Vista Previa de Datos")
            st.dataframe(df.head(10), use_container_width=True)

            if len(df) > 10:
                st.info(f"Mostrando 10 de {len(df)} filas. Descarga el archivo completo para ver todos los datos.")

        # Paso 5: Preparar descarga
        status_text.text("📦 Preparando archivo...")
        progress_bar.progress(75)

        # Convertir formato
        formato_ext = {'Excel (.xlsx)': 'xlsx', 'CSV (.csv)': 'csv', 'JSON (.json)': 'json'}[formato]

        # Crear archivo para descarga
        output_filename = f"{Path(uploaded_file.name).stem}_procesado.{formato_ext}"

        # Usar FileHandler para guardar
        output_path = Path(f"temp_output_{output_filename}")
        FileHandler.save_dataframe(df, output_path, formato_ext)

        # Leer archivo para descarga
        with open(output_path, "rb") as f:
            file_data = f.read()

        # Botón de descarga
        st.download_button(
            label=f"📥 Descargar {formato}",
            data=file_data,
            file_name=output_filename,
            mime={
                'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                'csv': 'text/csv',
                'json': 'application/json'
            }[formato_ext],
            use_container_width=True
        )

        # Finalizar
        status_text.text("🎉 ¡Listo para descargar!")
        progress_bar.progress(100)

        # Limpiar archivos temporales
        temp_path.unlink(missing_ok=True)
        output_path.unlink(missing_ok=True)

    except Exception as e:
        st.markdown('<div class="error-box">', unsafe_allow_html=True)
        st.markdown(f"### ❌ Error de Procesamiento")
        st.markdown(f"**Error:** {str(e)}")
        st.markdown("Por favor, verifica que el archivo PDF sea válido y vuelve a intentarlo.")
        st.markdown('</div>', unsafe_allow_html=True)

        logger.error(f"Error procesando documento: {e}", exc_info=True)

    finally:
        progress_bar.empty()
        status_text.empty()


if __name__ == "__main__":
    main()
