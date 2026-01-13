"""
Script maestro para el proceso completo con el cliente:
1. Comparar y relacionar datos del cliente con nuestro archivo
2. Crear múltiples filas para ALTA/BAJA
3. Preparar archivo final para migración
"""
import pandas as pd
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

ARCHIVO_CLIENTE = Path("data/input/LISTADO TRABAJADORES 2024.xlsx")
ARCHIVO_NUESTRO = Path("data/output/VIDA LABORAL 2024_COMPLETO.csv")
ARCHIVO_MULTIPLES_FILAS = Path("data/output/VIDA_LABORAL_MULTIPLES_FILAS.csv")
ARCHIVO_FINAL = Path("data/output/VIDA_LABORAL_FINAL_CLIENTE.csv")

def normalizar_nombre(nombre, es_cliente=False):
    """Normaliza nombres para comparación."""
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

def buscar_nombre_similar(nombre_buscado, nombres_cliente, umbral=0.8):
    """Busca nombre similar usando comparación flexible."""
    from difflib import SequenceMatcher
    
    mejor_match = None
    mejor_score = 0
    
    for nombre_cliente in nombres_cliente:
        if not nombre_cliente:
            continue
        # Comparar similitud
        score = SequenceMatcher(None, nombre_buscado, nombre_cliente).ratio()
        if score > mejor_score:
            mejor_score = score
            mejor_match = nombre_cliente
    
    if mejor_score >= umbral:
        return mejor_match, mejor_score
    return None, mejor_score

def leer_datos_cliente():
    """Lee el Excel del cliente."""
    if not ARCHIVO_CLIENTE.exists():
        logging.warning(f"⚠️  Archivo del cliente no encontrado: {ARCHIVO_CLIENTE}")
        logging.info("Por favor:")
        logging.info("1. Descarga el Excel del cliente desde OneDrive")
        logging.info("2. Guárdalo en: data/input/LISTADO TRABAJADORES 2024.xlsx")
        return None
    
    try:
        logging.info(f"Leyendo Excel del cliente: {ARCHIVO_CLIENTE}")
        
        # Intentar leer con diferentes métodos
        try:
            df_cliente = pd.read_excel(ARCHIVO_CLIENTE, sheet_name="Datos originales", header=4, engine='openpyxl')
        except:
            try:
                df_cliente = pd.read_excel(ARCHIVO_CLIENTE, header=4, engine='openpyxl')
            except:
                df_cliente = pd.read_excel(ARCHIVO_CLIENTE, engine='openpyxl')
        
        logging.info(f"✅ Filas leídas del cliente: {len(df_cliente)}")
        logging.info(f"   Columnas encontradas: {list(df_cliente.columns)}")
        
        # Verificar que tenemos las columnas necesarias
        columnas_necesarias = ['Nombre2', 'Código']
        columnas_encontradas = []
        for col in df_cliente.columns:
            if 'nombre' in str(col).lower() or 'nombre2' in str(col).lower():
                columnas_encontradas.append(col)
            if 'código' in str(col).lower() or 'codigo' in str(col).lower():
                columnas_encontradas.append(col)
        
        logging.info(f"   Columnas relevantes encontradas: {columnas_encontradas}")
        
        return df_cliente
    except Exception as e:
        logging.error(f"Error leyendo Excel: {e}")
        import traceback
        logging.error(traceback.format_exc())
        return None

def crear_multiples_filas():
    """Crea múltiples filas para empleados con ALTA/BAJA."""
    logging.info("\n" + "="*60)
    logging.info("PASO 1: Creando múltiples filas por situación")
    logging.info("="*60)
    
    if not ARCHIVO_NUESTRO.exists():
        logging.error(f"Archivo no encontrado: {ARCHIVO_NUESTRO}")
        return None
    
    df = pd.read_csv(ARCHIVO_NUESTRO, encoding='utf-8-sig')
    logging.info(f"Empleados originales: {len(df)}")
    
    nuevas_filas = []
    for idx, row in df.iterrows():
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
    
    df_multiple = pd.DataFrame(nuevas_filas).reset_index(drop=True)
    df_multiple.to_csv(ARCHIVO_MULTIPLES_FILAS, index=False, encoding='utf-8-sig')
    
    logging.info(f"✅ Archivo guardado: {ARCHIVO_MULTIPLES_FILAS}")
    logging.info(f"   Filas nuevas: {len(df_multiple)} (+{len(df_multiple) - len(df)})")
    
    return df_multiple

def relacionar_con_cliente(df_multiple, df_cliente):
    """Relaciona datos del cliente con nuestro archivo."""
    logging.info("\n" + "="*60)
    logging.info("PASO 2: Relacionando con datos del cliente")
    logging.info("="*60)
    
    # Normalizar nombres
    df_multiple['Nombre_Normalizado'] = df_multiple['Nombre_Apellidos'].apply(normalizar_nombre)
    
    # Usar específicamente 'Nombre2' (no 'Nombre' que es empresa)
    columna_nombre_cliente = None
    for col in df_cliente.columns:
        col_str = str(col).strip()
        # Buscar exactamente 'Nombre2' o variantes
        if col_str == 'Nombre2' or col_str.lower() == 'nombre2':
            columna_nombre_cliente = col
            break
    
    if columna_nombre_cliente is None:
        logging.error("No se encontró columna 'Nombre2' en el Excel del cliente")
        logging.info(f"Columnas disponibles: {list(df_cliente.columns)}")
        logging.info("Buscando manualmente...")
        # Buscar manualmente
        for i, col in enumerate(df_cliente.columns):
            logging.info(f"  Columna {i}: '{col}' (tipo: {type(col)})")
            if 'nombre' in str(col).lower() and '2' in str(col):
                columna_nombre_cliente = col
                logging.info(f"  ✅ Encontrada: '{col}'")
                break
        if columna_nombre_cliente is None:
            return df_multiple
    
    logging.info(f"✅ Usando columna '{columna_nombre_cliente}' para nombres del cliente")
    
    # Filtrar filas vacías
    df_cliente = df_cliente[df_cliente[columna_nombre_cliente].notna()].copy()
    logging.info(f"Filas después de filtrar vacías: {len(df_cliente)}")
    
    df_cliente['Nombre_Normalizado'] = df_cliente[columna_nombre_cliente].apply(lambda x: normalizar_nombre(x, es_cliente=True))
    
    # Buscar columnas en el Excel del cliente
    col_codigo = None
    col_nif = None
    col_nacimiento = None
    col_puesto = None
    col_sexo = None
    
    for col in df_cliente.columns:
        col_lower = str(col).lower()
        if 'código' in col_lower or ('codigo' in col_lower and col_codigo is None):
            col_codigo = col
        if 'n.i.f' in col_lower or 'nif' in col_lower:
            col_nif = col
        if 'nacimiento' in col_lower:
            col_nacimiento = col
        if 'puesto' in col_lower:
            col_puesto = col
        if 'sexo' in col_lower:
            col_sexo = col
    
    logging.info(f"Columnas mapeadas:")
    logging.info(f"   Código: {col_codigo}")
    logging.info(f"   NIF: {col_nif}")
    logging.info(f"   Nacimiento: {col_nacimiento}")
    logging.info(f"   Puesto: {col_puesto}")
    logging.info(f"   Sexo: {col_sexo}")
    
    # Crear diccionario del cliente
    cliente_dict = {}
    for idx, row in df_cliente.iterrows():
        nombre_norm = row['Nombre_Normalizado']
        if nombre_norm:
            cliente_dict[nombre_norm] = {
                'Codigo': str(row.get(col_codigo, '')) if col_codigo else '',
                'Nombre': str(row.get(columna_nombre_cliente, '')),
                'NIF': str(row.get(col_nif, '')) if col_nif else '',
                'Nacimiento': str(row.get(col_nacimiento, '')) if col_nacimiento else '',
                'Puesto': str(row.get(col_puesto, '')) if col_puesto else '',
                'Sexo': str(row.get(col_sexo, '')) if col_sexo else '',
                'Alta': str(row.get('Alta', '')) if 'Alta' in df_cliente.columns else '',
                'Final': str(row.get('Final', '')) if 'Final' in df_cliente.columns else '',
                'Antiguedad': str(row.get('Antiguedad', '')) if 'Antiguedad' in df_cliente.columns else '',
            }
    
    # Agregar datos del cliente
    datos_finales = []
    encontrados = 0
    no_encontrados = []
    nombres_cliente_norm = list(cliente_dict.keys())
    
    logging.info(f"Total nombres en cliente: {len(nombres_cliente_norm)}")
    logging.info(f"Ejemplos nombres cliente: {nombres_cliente_norm[:3]}")
    logging.info(f"Ejemplos nombres nuestro: {df_multiple['Nombre_Normalizado'].head(3).tolist()}")
    
    for idx, row in df_multiple.iterrows():
        datos = row.to_dict()
        nombre_norm = row['Nombre_Normalizado']
        
        if nombre_norm in cliente_dict:
            # Coincidencia exacta
            datos_cliente = cliente_dict[nombre_norm]
            datos['Codigo_Cliente'] = datos_cliente['Codigo']
            datos['Nacimiento'] = datos_cliente['Nacimiento']
            datos['Puesto'] = datos_cliente['Puesto']
            datos['Sexo'] = datos_cliente['Sexo']
            datos['Alta_Cliente'] = datos_cliente['Alta']
            datos['Final_Cliente'] = datos_cliente['Final']
            datos['Antiguedad_Cliente'] = datos_cliente['Antiguedad']
            encontrados += 1
        else:
            # Buscar nombre similar
            match_similar, score = buscar_nombre_similar(nombre_norm, nombres_cliente_norm)
            if match_similar and score >= 0.85:
                datos_cliente = cliente_dict[match_similar]
                datos['Codigo_Cliente'] = datos_cliente['Codigo']
                datos['Nacimiento'] = datos_cliente['Nacimiento']
                datos['Puesto'] = datos_cliente['Puesto']
                datos['Sexo'] = datos_cliente['Sexo']
                datos['Alta_Cliente'] = datos_cliente['Alta']
                datos['Final_Cliente'] = datos_cliente['Final']
                datos['Antiguedad_Cliente'] = datos_cliente['Antiguedad']
                encontrados += 1
                logging.info(f"  Match similar ({score:.2f}): {row['Nombre_Apellidos']} → {datos_cliente['Nombre']}")
            else:
                datos['Codigo_Cliente'] = ''
                datos['Nacimiento'] = ''
                datos['Puesto'] = ''
                datos['Sexo'] = ''
                datos['Alta_Cliente'] = ''
                datos['Final_Cliente'] = ''
                datos['Antiguedad_Cliente'] = ''
                no_encontrados.append(row['Nombre_Apellidos'])
        
        datos_finales.append(datos)
    
    df_final = pd.DataFrame(datos_finales)
    
    logging.info(f"✅ Empleados relacionados: {encontrados}/{len(df_multiple)}")
    if no_encontrados:
        logging.warning(f"⚠️  No encontrados en cliente: {len(no_encontrados)}")
        logging.info("   Primeros 5:")
        for nombre in no_encontrados[:5]:
            logging.info(f"      - {nombre}")
    
    return df_final

def main():
    """Función principal."""
    logging.info("="*60)
    logging.info("PROCESO COMPLETO CON CLIENTE")
    logging.info("="*60)
    
    # Paso 1: Crear múltiples filas
    df_multiple = crear_multiples_filas()
    if df_multiple is None:
        return
    
    # Paso 2: Leer datos del cliente (opcional)
    df_cliente = leer_datos_cliente()
    
    if df_cliente is not None:
        # Paso 3: Relacionar con cliente
        df_final = relacionar_con_cliente(df_multiple, df_cliente)
    else:
        logging.warning("\n⚠️  Continuando sin datos del cliente (solo múltiples filas)")
        df_final = df_multiple
    
    # Guardar archivo final
    df_final.to_csv(ARCHIVO_FINAL, index=False, encoding='utf-8-sig')
    
    logging.info("\n" + "="*60)
    logging.info("✅ PROCESO COMPLETADO")
    logging.info("="*60)
    logging.info(f"Archivo final: {ARCHIVO_FINAL}")
    logging.info(f"Total filas: {len(df_final)}")
    logging.info(f"Columnas: {len(df_final.columns)}")
    
    if df_cliente is not None:
        logging.info(f"\n📊 Resumen:")
        logging.info(f"   - Empleados del cliente: {len(df_cliente)}")
        logging.info(f"   - Filas en archivo final: {len(df_final)}")
        logging.info(f"   - Diferencia: {len(df_cliente) - len(df_final)}")

if __name__ == "__main__":
    main()

