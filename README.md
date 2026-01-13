# 📊 PDF Extractor - Streamlit

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.52%2B-FF4B4B.svg)](https://streamlit.io/)
[![License](https://img.shields.io/badge/License-Private-red.svg)]()

Sistema moderno para extracción automática de datos desde documentos PDF con interfaz web profesional. Convierte PDFs complejos en datos estructurados listos para análisis.

🔗 **Repositorio**: [https://github.com/riche45/PDF-Extractor-Streamlit](https://github.com/riche45/PDF-Extractor-Streamlit)

## ✨ Características Principales

- 🚀 **Interfaz Web Moderna**: Aplicación Streamlit intuitiva y profesional
- 📄 **Múltiples Formatos PDF**: Soporte para tablas, texto estructurado y documentos complejos
- 🎯 **Plantillas Especializadas**: Templates optimizados para diferentes tipos de documentos
- 📊 **Salida Múltiples Formatos**: Exporta a Excel, CSV o JSON
- ⚡ **Procesamiento Automático**: Extracción inteligente sin configuración manual
- 🔍 **Vista Previa**: Revisa datos antes de descargar
- 📈 **Estadísticas en Tiempo Real**: Métricas de procesamiento y calidad
- 🏢 **Especializado en Vida Laboral**: Optimizado para documentos empresariales

## 🎯 Casos de Uso

- 📋 **Recursos Humanos**: Procesar documentos de vida laboral
- 💼 **Contabilidad**: Extraer datos de nóminas y facturas
- 📊 **Business Intelligence**: Convertir PDFs en datos analizables
- 🔄 **Automatización**: Procesamiento batch de documentos

## 🛠️ Tecnologías

- **Python 3.8+**: Lenguaje principal
- **Streamlit**: Framework de interfaz web
- **PyPDF2 / pypdf**: Extracción de texto
- **tabula-py**: Extracción de tablas
- **pandas**: Manipulación de datos
- **openpyxl**: Exportación a Excel

## 📋 Requisitos

- Python 3.8 o superior
- Navegador web moderno

## 🚀 Inicio Rápido

### 1. Clonar el repositorio

```bash
git clone https://github.com/riche45/PDF-Extractor-Streamlit.git
cd PDF-Extractor-Streamlit
```

### 2. Crear entorno virtual

```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Ejecutar la aplicación

```bash
# Usar el Python del entorno virtual
python -m streamlit run app.py
```

### 5. Abrir en navegador

Ve a `http://localhost:8501` 🎉

## 📖 Cómo Usar

1. **Sube un PDF**: Selecciona tu archivo desde la interfaz
2. **Elige plantilla**: Selecciona el tipo de documento (Vida Laboral, Nóminas, etc.)
3. **Configura opciones**: Elige formato de salida y opciones de procesamiento
4. **Procesa**: Haz clic en "Procesar Documento"
5. **Descarga**: Obtén tus datos en Excel, CSV o JSON
5. Descarga el JSON y renómbralo a `credentials.json` en la raíz del proyecto
6. Agrega tu email como usuario de prueba en "Pantalla de consentimiento OAuth"

### 5. Configurar variables de entorno

Crea un archivo `.env` en la raíz:

```env
GOOGLE_SHEET_ID=tu_sheet_id_aqui
GOOGLE_SHEET_NAME=DATOS
```

## 🏗️ Arquitectura del Sistema

### Estructura Modular

```
EmpresadClara-project/
├── app.py                        # 🖥️ Aplicación Streamlit principal
├── requirements.txt              # 📦 Dependencias Python
├── README.md                     # 📖 Este archivo
│
├── src/                          # 📂 Código fuente modular
│   ├── templates/               # 📋 Plantillas de extracción
│   │   ├── __init__.py
│   │   ├── template_base.py     # 🏗️ Clase base para plantillas
│   │   └── vida_laboral_template.py  # 💼 Plantilla Vida Laboral
│   │
│   ├── processors/              # ⚙️ Procesadores de datos
│   │   ├── __init__.py
│   │   └── pdf_extractor.py     # 📄 Extractor de PDFs
│   │
│   ├── integrations/            # ☁️ Integraciones externas
│   │   ├── __init__.py
│   │   ├── drive_handler.py     # 📁 Google Drive
│   │   └── sheets_handler.py    # 📊 Google Sheets
│   │
│   └── utils/                   # 🔧 Utilidades
│       ├── __init__.py
│       └── file_handlers.py     # 💾 Manejo de archivos
│
├── data/                        # 📊 Datos y configuraciones
│   ├── input/                   # 📥 PDFs de entrada
│   ├── output/                  # 📤 Datos procesados
│   └── reports/                 # 📈 Reportes de análisis
│
└── logs/                        # 📝 Logs del sistema
```

### Componentes Principales

- **🖥️ app.py**: Interfaz web Streamlit
- **📋 Templates**: Plantillas especializadas por tipo de documento
- **⚙️ Processors**: Lógica de extracción y procesamiento
- **🔧 Utils**: Utilidades compartidas

## 🎯 Plantillas Disponibles

### 📄 Vida Laboral
- **Especialización**: Documentos de empleados y contratos
- **Características**:
  - Creación automática de filas ALTA/BAJA
  - Normalización de nombres y fechas
  - Relación con datos del cliente
  - Formatos específicos de RRHH


## 🔧 Uso de la Aplicación

### Modo Local (Sin Google)

1. **Inicio**: Ejecuta `streamlit run app.py`
2. **Subida**: Arrastra y suelta o selecciona un PDF local
3. **Configuración**: Elige plantilla y formato de salida
4. **Procesamiento**: Haz clic en "Procesar Documento"
5. **Resultado**: Descarga Excel/CSV/JSON a tu computadora

**✅ Ideal para:**
- Trabajo individual
- Datos sensibles que no deben estar en la nube
- Procesamiento offline

### Modo Colaborativo (Con Google) 🆕

1. **Inicio**: Ejecuta `streamlit run app.py`
2. **Habilitar Google**: Activa "🔗 Habilitar integración Google" en sidebar
3. **Opciones**:
   - 📁 **Leer desde Drive**: Procesa PDFs directamente desde carpeta compartida
   - 📊 **Actualizar Sheets**: Sincroniza resultados en Google Sheets en tiempo real
4. **Configurar Sheet**: Proporciona ID del Sheet y nombre de la hoja
5. **Procesamiento**: El sistema actualiza Sheets + ofrece descarga local
6. **Colaboración**: Todo el equipo ve los mismos datos actualizados

**✅ Ideal para:**
- Equipos distribuidos
- Colaboración en tiempo real
- Fuente única de verdad
- Acceso desde cualquier lugar

### Características de la UI

- 🎨 **Diseño Profesional**: Interfaz moderna y responsiva
- 📊 **Estadísticas en Tiempo Real**: Métricas de procesamiento
- 👀 **Vista Previa**: Revisa datos antes de descargar
- ⚡ **Procesamiento Visual**: Barra de progreso y estados
- 📥 **Descarga Múltiple**: Excel, CSV o JSON
- ☁️ **Modo Híbrido**: Local O Colaborativo (tú eliges)
- 🔄 **Backup Automático**: Respaldo antes de actualizar Sheets

## ☁️ Configurar Integración con Google (Opcional)

Para habilitar el **Modo Colaborativo** con Google Drive y Sheets:

### Paso 1: Crear Proyecto en Google Cloud

1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Crea un proyecto nuevo o selecciona uno existente
3. Habilita las siguientes APIs:
   - **Google Drive API**
   - **Google Sheets API**

### Paso 2: Crear Credenciales OAuth 2.0

1. Ve a **APIs & Services** > **Credentials**
2. Haz clic en **+ CREATE CREDENTIALS** > **OAuth client ID**
3. Tipo de aplicación: **Desktop app**
4. Descarga el archivo JSON de credenciales
5. Renombra el archivo a `credentials.json`
6. Coloca `credentials.json` en la raíz del proyecto

### Paso 3: Configurar Pantalla de Consentimiento

1. Ve a **OAuth consent screen**
2. Configura como aplicación **External** (para equipos pequeños) o **Internal** (para G Suite)
3. Agrega los emails de tu equipo como **Test users**
4. Guarda los cambios

### Paso 4: Primera Autenticación

1. Ejecuta la aplicación: `streamlit run app.py`
2. Habilita "🔗 Habilitar integración Google"
3. Al procesar el primer documento, se abrirá ventana de autenticación
4. Autoriza el acceso (se creará `token.json` automáticamente)
5. ¡Listo! Ahora puedes usar Drive y Sheets

### Configuración del Google Sheet

Para actualizar un Sheet automáticamente:

1. **Obtén el ID del Sheet**: Está en la URL
   ```
   https://docs.google.com/spreadsheets/d/[ESTE_ES_EL_ID]/edit
   ```

2. **Comparte el Sheet** con la cuenta que autenticaste

3. **Pega el ID** en la aplicación cuando habilites "Actualizar Google Sheets"

4. **Especifica el nombre de la hoja** (por defecto: "DATOS")

### Variables de Entorno (Opcional)

Para configuración por defecto, crea un archivo `.env`:

```env
GOOGLE_SHEET_ID=tu_sheet_id_por_defecto
GOOGLE_SHEET_NAME=DATOS
```

## 🚀 Despliegue

### Desarrollo Local

```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar aplicación
streamlit run app.py

# Acceder en: http://localhost:8501
```

### Producción (Streamlit Cloud)

1. **Sube a GitHub** tu repositorio
2. **Ve a [Streamlit Cloud](https://streamlit.io/cloud)**
3. **Conecta tu repo** y configura la app
4. **Despliega** automáticamente

### Docker (Opcional)

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.address", "0.0.0.0"]
```

## 📋 API Programática

También puedes usar las plantillas directamente en código Python:

```python
from src.templates import VidaLaboralTemplate

# Crear instancia de plantilla
template = VidaLaboralTemplate()

# Procesar PDF
resultado = template.process_pdf("mi_documento.pdf")

if resultado['success']:
    df = resultado['data']
    df.to_excel("datos_extraidos.xlsx", index=False)
```

## 🔍 Ejemplos de Uso

### Caso 1: Procesar Vida Laboral

**Entrada**: PDF con datos de empleados
```
EMPLEADO: JUAN GARCIA
ALTA: 01/01/2020
BAJA: 15/06/2023
```

**Salida**: Excel estructurado
| Nombre_Apellidos | Situacion | F_Real_Alta | F_Efecto_Sit |
|------------------|-----------|-------------|--------------|
| JUAN GARCIA     | ALTA      | 01/01/2020 |             |
| JUAN GARCIA     | BAJA      | 15/06/2023 | 15/06/2023  |

### Caso 2: Relación con Datos Cliente

Si tienes un Excel con datos adicionales del cliente, la plantilla puede relacionarlos automáticamente por nombre.

## ⚡ Rendimiento

- **PDF típico**: Procesamiento en 10-30 segundos
- **Archivos grandes**: Optimizado para PDFs de hasta 100MB
- **Múltiples métodos**: Fallback automático si un método falla

### Procesamiento de Vida Laboral (Flujo Completo)

1. **Extraer datos del PDF**:
```bash
python main.py --pdf "data/input/VIDA LABORAL 2024.pdf"
```

2. **Reorganizar y estructurar datos**:
```bash
python reorganizar_datos_completo.py
```

3. **Actualizar Google Sheet** (con backup automático):
```bash
python actualizar_sheet.py "data/output/VIDA LABORAL 2024_COMPLETO.csv"
```

### Desde Google Drive

```bash
python main.py --drive-url "https://drive.google.com/file/d/ID_DEL_ARCHIVO/view"
```

### Solo Extracción (sin actualizar Sheet)

```bash
python main.py --pdf "archivo.pdf" --no-update-sheet
```

## 📊 Flujo de Trabajo Típico

1. **Extracción**: El PDF se procesa con múltiples métodos para extraer tablas y texto
2. **Limpieza**: Se eliminan códigos corruptos (`(cid:X)`), se normalizan formatos
3. **Reorganización**: Se asocian fechas, situaciones y datos con cada empleado
4. **Validación**: Se verifica la integridad de los datos
5. **Backup**: Se crea backup automático del Google Sheet
6. **Actualización**: Los datos se sincronizan con Google Sheets

## 🔐 Seguridad

- ⚠️ **NUNCA** subas `credentials.json` o `.env` a repositorios públicos
- Usa `.gitignore` para excluir archivos sensibles
- Revisa los permisos de Google Sheets antes de compartir
- Los backups se guardan localmente en `data/backups/`

## 🛠️ Scripts Principales

### `main.py`
Script principal para extracción general de PDFs. Soporta múltiples métodos y formatos.

### `reorganizar_datos_completo.py`
Script específico para documentos de vida laboral. Extrae y estructura:
- Número de afiliación, DNI, Nombre
- Situación contractual (ALTA/BAJA)
- Fechas (Real Alta, Efecto Alta, Real Sit, Efecto Sit)
- Datos numéricos (G_C_M, T_C, Tipos_AT_IT, IMS, Total, Días Cotización)
- Código CLV

### `actualizar_sheet.py`
Actualiza Google Sheets con backup automático. Incluye:
- Backup antes de actualizar
- Validación de datos
- Logging detallado

## 📝 Notas Importantes

### Tipos de Google Sheets
- ✅ **Nativo de Google Sheets**: Funciona perfectamente
- ❌ **Excel importado**: Funcionalidad limitada, crear nuevo Sheet nativo

### Empleados Sin Fechas
Algunos empleados pueden aparecer sin fechas si el PDF original no las contiene. Estos casos pueden completarse manualmente en el Google Sheet.

### Nombre Corrupto
El sistema filtra automáticamente nombres corruptos detectados durante la extracción.

## 🐛 Solución de Problemas

### Error 403: Access Blocked
- Verifica que tu email esté agregado como usuario de prueba en Google Cloud Console
- Espera 2-3 minutos después de agregar el usuario

### Error 400: Operation Not Supported
- El Sheet es un Excel importado, no nativo
- Crea un nuevo Google Sheet nativo

### Códigos (cid:X) en los datos
- Ejecuta `reorganizar_datos_completo.py` que incluye limpieza automática

## 📞 Soporte

Para problemas o preguntas, revisa los logs en `logs/extraction.log`.

## 📄 Licencia

Uso interno del cliente.

## 🤝 Contribuciones

Este es un proyecto privado. Para sugerencias o mejoras, contacta al propietario del repositorio.

## 👨‍💻 Autor

**Richard Garcia**  
📧 Email: tayrona7@hotmail.com  
🔗 GitHub: [@riche45](https://github.com/riche45)

---

**Versión**: 1.0  
**Última actualización**: Enero 2026  
**Desarrollado **para Clara Ruiz Company**
