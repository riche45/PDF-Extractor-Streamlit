# 🚀 Guía de Despliegue en Streamlit Cloud

## ✅ Versión Simplificada - Sin Google APIs

**Modo:** 100% Local
- ✅ Subir PDF → Procesar → Descargar Excel
- ✅ Compatible con Microsoft Office
- ✅ Sin configuraciones complejas
- ✅ Sin dependencias de Google

---

## 📋 Preparación (5 minutos)

### Paso 1: Verificar que funciona localmente

```bash
# Ejecuta la app
streamlit run app.py

# Prueba:
1. Sube un PDF
2. Selecciona formato: Excel (.xlsx)
3. Procesa
4. Descarga el Excel
5. Abre en Microsoft Excel → Debe funcionar perfecto
```

### Paso 2: Preparar requirements.txt (Opcional - Simplificar)

Puedes quitar dependencias de Google si quieres reducir el tamaño:

```txt
# Mantén solo:
streamlit>=1.28.0
pdfplumber>=0.10.0
PyPDF2>=3.0.0
pandas>=2.0.0
openpyxl>=3.1.0
matplotlib>=3.7.0
python-dotenv>=1.0.0

# Opcional (para mejor extracción):
PyMuPDF>=1.23.0
tabula-py>=2.8.0
```

---

## ☁️ Despliegue en Streamlit Cloud

### Paso 1: Subir a GitHub

```bash
# 1. Inicializa git (si no lo has hecho)
git init

# 2. Agrega archivos
git add .

# 3. Commit
git commit -m "App lista para despliegue - modo local"

# 4. Crea repositorio en GitHub
# Ve a: https://github.com/new
# Nombre: extractor-pdf-contable
# Descripción: Extractor de PDFs para equipos contables

# 5. Conecta y sube
git remote add origin https://github.com/TU_USUARIO/extractor-pdf-contable.git
git branch -M main
git push -u origin main
```

### Paso 2: Desplegar en Streamlit Cloud

1. **Ve a Streamlit Cloud:**
   ```
   https://share.streamlit.io/
   ```

2. **Inicia sesión** con tu cuenta de GitHub

3. **New app:**
   ```
   Repository: TU_USUARIO/extractor-pdf-contable
   Branch: main
   Main file path: app.py
   
   Advanced settings:
   └─ Python version: 3.9
   
   → Deploy!
   ```

4. **Espera unos minutos** (primera vez tarda ~5 min)

5. **Tu app estará en:**
   ```
   https://tu-usuario-extractor-pdf-contable.streamlit.app
   ```

### Paso 3: Configurar Acceso (Opcional)

**Opción A: Pública** (Cualquiera con el link)
```
Settings > Sharing > Public
└─ Cualquiera puede usar la app
└─ Bueno para demos
```

**Opción B: Privada** (Solo usuarios autorizados)
```
Settings > Sharing > Private
└─ Solo invitados pueden acceder
└─ Agrega emails de los 3 contables
└─ Recomendado para datos empresariales
```

**Recomendación:** Usa **Privada** para datos sensibles.

---

## 👥 Dar Acceso a los Contables

### Si configuraste como Privada:

1. **En Streamlit Cloud:**
   ```
   Tu app > Settings > Sharing
   ```

2. **Invita a los contables:**
   ```
   Add email:
   ├─ contable1@empresa.com
   ├─ contable2@empresa.com
   └─ contable3@empresa.com
   
   → Send invitations
   ```

3. **Ellos recibirán email:**
   ```
   Subject: You've been invited to access an app
   └─ Clic en link
   └─ Inician sesión con su cuenta Google (solo para autenticación)
   └─ Acceden a la app
   ```

### Envía este mensaje a los contables:

```
Hola equipo,

Ya está lista la herramienta de extracción de PDFs.

🔗 URL: https://tu-app-extractor.streamlit.app

📖 Instrucciones:
1. Abre el link en tu navegador
2. Sube tu archivo PDF (arrastra y suelta o selecciona)
3. Elige el formato: Excel (.xlsx)
4. Clic en "🚀 Procesar Documento"
5. Espera a que termine (verás barra de progreso)
6. Descarga el archivo Excel
7. Abre en Microsoft Excel normalmente

✅ Compatible con Microsoft Office
✅ Los archivos se procesan y descargan directamente
✅ No requiere instalación de nada

¡Cualquier duda me avisan!
```

---

## 🎨 Personalización (Opcional)

### Cambiar Título y Favicon

En Streamlit Cloud:
```
Settings > General
├─ App title: Extractor PDF - [Nombre Empresa]
├─ Favicon: 📊 (emoji) o sube imagen .png
└─ Save
```

### Personalizar URL

Streamlit Cloud permite:
```
Gratis: https://tu-usuario-extractor-pdf.streamlit.app
Pro: https://tudominio.com (custom domain)
```

---

## 📊 Recursos y Límites

### Plan Gratuito de Streamlit Cloud:

```
✅ 1 app privada
✅ 1 GB de RAM
✅ Ilimitados procesamientos
✅ Sin límite de usuarios
✅ Actualizaciones automáticas desde GitHub

Límites:
⚠️ App se "duerme" después de inactividad (se reactiva en ~30s)
⚠️ Máximo 1 GB de RAM (suficiente para PDFs < 50MB)
```

**Para tu caso:**
- ✅ 3 usuarios → Perfecto
- ✅ PDFs típicos de vida laboral → Perfecto
- ✅ Procesamiento ocasional → Perfecto

### Si necesitas más:

```
Streamlit Cloud Pro: $20/mes
├─ Apps siempre activas
├─ 4 GB de RAM
└─ Soporte prioritario
```

---

## 🔄 Actualizar la App

### Cuando hagas cambios al código:

```bash
# 1. Haz tus cambios en app.py u otros archivos

# 2. Commit y push
git add .
git commit -m "Actualización: [descripción del cambio]"
git push

# 3. Streamlit Cloud detecta automáticamente
#    Se actualiza en ~2 minutos
#    Los usuarios ven la nueva versión automáticamente
```

**No necesitas hacer nada en Streamlit Cloud** - se actualiza solo.

---

## 🐛 Troubleshooting

### Error: "App is not loading"

**Solución:**
```
1. Ve a Streamlit Cloud > Tu app > Logs
2. Revisa el error
3. Comunes:
   - Dependencia faltante → Agrega a requirements.txt
   - Error de código → Revisa logs para detalles
```

### Error: "Module not found"

**Solución:**
```
Asegúrate que requirements.txt tiene todas las dependencias:

streamlit
pandas
openpyxl
pdfplumber
PyPDF2
matplotlib
python-dotenv
```

### App muy lenta

**Solución:**
```
1. Revisa tamaño del PDF (< 50MB recomendado)
2. Si necesitas más recursos, considera Streamlit Cloud Pro
3. Optimiza el código (elimina imports innecesarios)
```

### Los contables no pueden acceder

**Solución:**
```
1. Verifica que los agregaste en Settings > Sharing
2. Verifica que app esté en "Private" con emails correctos
3. Pide que revisen carpeta de Spam
4. Pueden acceder directo desde el link si iniciaron sesión en Streamlit
```

---

## ✅ Checklist Pre-Despliegue

Antes de dar la URL a los contables:

- [ ] App funciona perfectamente en local
- [ ] PDF de prueba procesa correctamente
- [ ] Excel descargado abre bien en Microsoft Office
- [ ] Código subido a GitHub
- [ ] App desplegada en Streamlit Cloud
- [ ] App configurada como Privada
- [ ] 3 contables agregados con sus emails
- [ ] Probado: subir PDF y descargar Excel desde la URL pública
- [ ] Mensaje con instrucciones listo para enviar

---

## 🎉 Resultado Final

**Para ti:**
```
✅ Setup de ~30 minutos (una sola vez)
✅ App en la nube funcionando 24/7
✅ Actualizaciones automáticas
✅ Sin servidores que mantener
```

**Para los contables:**
```
✅ Solo abren URL
✅ Suben PDF
✅ Descargan Excel
✅ Sin instalaciones
✅ Sin configuraciones
✅ Funciona en cualquier computadora
```

**Costo:**
```
💰 $0/mes (plan gratuito de Streamlit Cloud)
```

---

## 📞 Soporte

**Documentación de Streamlit Cloud:**
- https://docs.streamlit.io/streamlit-community-cloud

**Comunidad:**
- https://discuss.streamlit.io/

**Status de Streamlit Cloud:**
- https://streamlitstatus.com/

---

¿Listo para desplegar? ¡Solo sigue los pasos y en 30 minutos estará funcionando!
