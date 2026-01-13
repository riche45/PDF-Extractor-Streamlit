"""
Script completo para reorganizar datos según estructura del PDF original.
Extrae todas las columnas según el formato del PDF.
"""
import pandas as pd
import re
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

input_file = Path("data/output/VIDA LABORAL 2024_SIN_CID.csv")
output_file = Path("data/output/VIDA LABORAL 2024_COMPLETO.csv")

logging.info("="*60)
logging.info("REORGANIZACIÓN COMPLETA DE DATOS")
logging.info("="*60)

# Leer datos
logging.info(f"\nLeyendo: {input_file}")
df = pd.read_csv(input_file, encoding='utf-8-sig')
logging.info(f"Datos originales: {len(df)} filas, {len(df.columns)} columnas")

def extraer_afiliacion(texto):
    """Extrae número de afiliación."""
    if pd.isna(texto):
        return None
    texto = str(texto).strip()
    match = re.search(r'(\d{2}\s+\d{9,10})', texto)
    return match.group(1) if match else None

def extraer_dni(texto):
    """Extrae DNI."""
    if pd.isna(texto):
        return None
    texto = str(texto).strip()
    match = re.search(r'(\d\s+\d{8,9}[A-Z])', texto)
    return match.group(1) if match else None

def limpiar_nombre(texto, dni=None):
    """Extrae y limpia el nombre completo."""
    if pd.isna(texto):
        return None
    
    texto = str(texto).strip()
    
    # Si hay DNI, quitar su letra final del texto si aparece al inicio
    if dni:
        letra_dni = dni[-1] if len(dni) > 0 else None
        if letra_dni and texto.startswith(letra_dni + ' '):
            texto = texto[len(letra_dni) + 1:].strip()
    
    # Buscar nombres en mayúsculas
    patrones = [
        r'([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ\s]{8,60})',
    ]
    
    for patron in patrones:
        matches = re.findall(patron, texto)
        for match in matches:
            nombre = match.strip()
            palabras = nombre.split()
            if (len(palabras) >= 2 and 
                not re.search(r'^\d', nombre) and
                not re.match(r'^[A-Z0-9]{2,4}$', nombre) and
                len(nombre) >= 10):
                # Quitar letras sueltas al inicio
                nombre = re.sub(r'^[A-Z]\s+', '', nombre).strip()
                # Quitar códigos al final
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

def parsear_fila_fechas(texto):
    """
    Parsea una fila de fechas y datos adicionales.
    Formato: "ALTA DD-MM-YYYY DD-MM-YYYY ..." o "BAJA DD-MM-YYYY DD-MM-YYYY ..."
    Ejemplo: "ALTA 10-05-2018 10-05-2018 08 540 0,250 1,80 1,50 3,30 1794"
    Ejemplo: "BAJA 15-07-2024 15-07-2024 24-07-2024 24-07-2024 08 300 1,80 1,50 3,30 10"
    """
    if pd.isna(texto):
        return {}
    
    texto = str(texto).strip()
    resultado = {}
    
    # Detectar situación (ALTA o BAJA)
    tiene_alta = 'ALTA' in texto
    tiene_baja = 'BAJA' in texto
    
    # Extraer todas las fechas primero
    fechas = re.findall(r'\d{2}-\d{2}-\d{4}', texto)
    
    # Extraer números y valores después de las fechas
    # Dividir el texto en partes después de las fechas
    partes = texto.split()
    
    if tiene_alta and tiene_baja:
        # Caso especial: tiene ambas (puede haber múltiples BAJA)
        resultado['Situacion'] = 'ALTA/BAJA'
        
        # Procesar ALTA (primera ocurrencia)
        match_alta = re.search(r'ALTA\s+(\d{2}-\d{2}-\d{4})\s+(\d{2}-\d{2}-\d{4})', texto)
        if match_alta:
            resultado['F_Real_Alta'] = match_alta.group(1)
            resultado['F_Efecto_Alta'] = match_alta.group(2)
        
        # Procesar BAJA - buscar TODAS las ocurrencias y tomar la ÚLTIMA
        # Formato BAJA: "BAJA DD-MM-YYYY DD-MM-YYYY DD-MM-YYYY DD-MM-YYYY"
        # Las 4 fechas son: F_Real_Alta, F_Efecto_Alta, F_Real_Sit, F_Efecto_Sit
        todas_bajas = list(re.finditer(r'BAJA\s+(\d{2}-\d{2}-\d{4})\s+(\d{2}-\d{2}-\d{4})\s+(\d{2}-\d{2}-\d{4})\s+(\d{2}-\d{2}-\d{4})', texto))
        if todas_bajas:
            # Tomar la última BAJA
            ultima_baja = todas_bajas[-1]
            # Si no tenemos F_Real_Alta de ALTA, usar las primeras dos fechas de BAJA
            if not resultado.get('F_Real_Alta'):
                resultado['F_Real_Alta'] = ultima_baja.group(1)
                resultado['F_Efecto_Alta'] = ultima_baja.group(2)
            # Las siguientes dos fechas son F_Real_Sit y F_Efecto_Sit
            resultado['F_Real_Sit'] = ultima_baja.group(3)
            resultado['F_Efecto_Sit'] = ultima_baja.group(4)
        
        # Extraer datos después de la ÚLTIMA BAJA (última sección)
        # Encontrar la posición de la última BAJA
        ultima_pos_baja = texto.rfind('BAJA')
        if ultima_pos_baja != -1:
            texto_despues_baja = texto[ultima_pos_baja:]
            # Buscar el patrón completo después de BAJA: DD-MM-YYYY DD-MM-YYYY DD-MM-YYYY DD-MM-YYYY G_C_M T_C Tipos_AT_IT IMS Total Dias_Cot
            match_datos_baja = re.search(r'BAJA\s+\d{2}-\d{2}-\d{4}\s+\d{2}-\d{2}-\d{4}\s+\d{2}-\d{2}-\d{4}\s+\d{2}-\d{2}-\d{4}\s+(.+)', texto_despues_baja)
            if match_datos_baja:
                texto_datos = match_datos_baja.group(1)
                # Eliminar código CLV al final si existe (códigos con letras, no números puros)
                # Los códigos CLV suelen tener letras, así que solo eliminamos si tienen al menos una letra
                texto_datos = re.sub(r'\s+[A-Z][A-Z0-9]{1,3}(\s+[A-Z][A-Z0-9]{1,3})*$', '', texto_datos).strip()
                partes = texto_datos.split()
                if len(partes) >= 6:
                    resultado['G_C_M'] = partes[0] if partes[0].isdigit() else None
                    resultado['T_C'] = partes[1] if len(partes) > 1 else None
                    
                    # Detectar C_T_P igual que en ALTA
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
                    else:
                        resultado['C_T_P'] = '100'
                        resultado['Tipos_AT_IT'] = partes[-4] if len(partes) >= 4 else None
                        resultado['IMS'] = partes[-3] if len(partes) >= 3 else None
                        resultado['Total'] = partes[-2] if len(partes) >= 2 else None
                        resultado['Dias_Cot'] = partes[-1] if len(partes) >= 1 else None
        
    elif tiene_alta:
        resultado['Situacion'] = 'ALTA'
        # Formato: "ALTA DD-MM-YYYY DD-MM-YYYY G_C_M T_C [valor_adicional] Tipos_AT_IT IMS Total Dias_Cot [CLV]"
        # Ejemplo: "ALTA 10-05-2018 10-05-2018 08 540 0,250 1,80 1,50 3,30 1794 FE4"
        match_alta = re.search(r'ALTA\s+(\d{2}-\d{2}-\d{4})\s+(\d{2}-\d{2}-\d{4})\s+(.+)', texto)
        if match_alta:
            resultado['F_Real_Alta'] = match_alta.group(1)
            resultado['F_Efecto_Alta'] = match_alta.group(2)
            texto_datos = match_alta.group(3)
            
            # Eliminar código CLV al final si existe (2-4 caracteres alfanuméricos)
            texto_datos = re.sub(r'\s+[A-Z0-9]{2,4}$', '', texto_datos).strip()
            
            # Extraer números y valores decimales después de las fechas
            # Formato: "08 540 0,250 1,80 1,50 3,30 1794" (con C_T_P)
            # O: "08 100 1,80 1,50 3,30 12081" (sin C_T_P, significa 100%)
            # Estructura: G_C_M T_C [C_T_P_opcional] Tipos_AT_IT IMS Total Dias_Cot
            partes = texto_datos.split()
            if len(partes) >= 6:
                resultado['G_C_M'] = partes[0] if partes[0].isdigit() else None
                resultado['T_C'] = partes[1] if len(partes) > 1 else None
                
                # Detectar C_T_P: puede estar después de T_C y antes de Tipos_AT_IT
                # C_T_P puede ser: 250, 500, 125, 750, 1000, 0,250, 0,500, etc.
                # Los últimos 4 valores siempre son: Tipos_AT_IT, IMS, Total, Dias_Cot
                # Estructura: ['08', '540', '0,250', '1,80', '1,50', '3,30', '1794']
                # O: ['08', '100', '1,80', '1,50', '3,30', '12081'] (sin C_T_P)
                
                # Identificar Tipos_AT_IT (siempre tiene formato decimal como "1,80")
                idx_tipos = None
                for i in range(len(partes)):
                    if re.match(r'^\d+,\d{2}$', partes[i]):  # Formato "1,80" o "2,10"
                        idx_tipos = i
                        break
                
                if idx_tipos and idx_tipos >= 2:
                    # Hay valores antes de Tipos_AT_IT
                    # Si hay más de 2 valores antes de Tipos_AT_IT, el tercero es C_T_P
                    if idx_tipos > 2:
                        posible_ctp = partes[2]
                        # Verificar si es un valor válido de C_T_P
                        # Formatos: 250, 500, 125, 750, 1000, 0,250, 0,500, 0,125, 0,750, 0,338, etc.
                        # Cualquier decimal con coma o número de 3-4 dígitos
                        if re.match(r'^\d+,\d+$', posible_ctp) or re.match(r'^\d{3,4}$', posible_ctp):
                            resultado['C_T_P'] = posible_ctp
                        else:
                            # Si no es C_T_P válido, significa que no hay C_T_P (100%)
                            resultado['C_T_P'] = '100'
                    else:
                        # No hay C_T_P, significa 100%
                        resultado['C_T_P'] = '100'
                    
                    # Los últimos 4 valores son siempre: Tipos_AT_IT, IMS, Total, Dias_Cot
                    resultado['Tipos_AT_IT'] = partes[idx_tipos] if idx_tipos < len(partes) else None
                    resultado['IMS'] = partes[idx_tipos + 1] if idx_tipos + 1 < len(partes) else None
                    resultado['Total'] = partes[idx_tipos + 2] if idx_tipos + 2 < len(partes) else None
                    resultado['Dias_Cot'] = partes[idx_tipos + 3] if idx_tipos + 3 < len(partes) else None
                else:
                    # Fallback: usar método anterior si no encontramos Tipos_AT_IT
                    resultado['C_T_P'] = '100'  # Por defecto 100%
                    resultado['Tipos_AT_IT'] = partes[-4] if len(partes) >= 4 else None
                    resultado['IMS'] = partes[-3] if len(partes) >= 3 else None
                    resultado['Total'] = partes[-2] if len(partes) >= 2 else None
                    resultado['Dias_Cot'] = partes[-1] if len(partes) >= 1 else None
    
    elif tiene_baja:
        resultado['Situacion'] = 'BAJA'
        # Formato: "BAJA DD-MM-YYYY DD-MM-YYYY DD-MM-YYYY DD-MM-YYYY G_C_M T_C Tipos_AT_IT IMS Total Dias_Cot [CLV]"
        # Ejemplo: "BAJA 15-07-2024 15-07-2024 24-07-2024 24-07-2024 08 300 1,80 1,50 3,30 10 7VH"
        # Las 4 fechas en BAJA son: F_Real_Alta, F_Efecto_Alta, F_Real_Sit, F_Efecto_Sit
        match_baja = re.search(r'BAJA\s+(\d{2}-\d{2}-\d{4})\s+(\d{2}-\d{2}-\d{4})\s+(\d{2}-\d{2}-\d{4})\s+(\d{2}-\d{2}-\d{4})\s+(.+)', texto)
        if match_baja:
            # Las primeras dos fechas son F_Real_Alta y F_Efecto_Alta (fechas de la alta previa)
            resultado['F_Real_Alta'] = match_baja.group(1)
            resultado['F_Efecto_Alta'] = match_baja.group(2)
            # Las siguientes dos fechas son F_Real_Sit y F_Efecto_Sit (fechas de la baja actual)
            resultado['F_Real_Sit'] = match_baja.group(3)
            resultado['F_Efecto_Sit'] = match_baja.group(4)
            texto_datos = match_baja.group(5)
            
            # Eliminar código CLV al final si existe (códigos con letras, no números puros)
            texto_datos = re.sub(r'\s+[A-Z][A-Z0-9]{1,3}(\s+[A-Z][A-Z0-9]{1,3})*$', '', texto_datos).strip()
            
            # Extraer números y valores decimales después de las 4 fechas
            # Formato: "08 300 1,80 1,50 3,30 10" (sin C_T_P) o "08 300 250 1,80 1,50 3,30 10" (con C_T_P)
            partes = texto_datos.split()
            if len(partes) >= 6:
                resultado['G_C_M'] = partes[0] if partes[0].isdigit() else None
                resultado['T_C'] = partes[1] if len(partes) > 1 else None
                
                # Detectar C_T_P igual que en ALTA
                idx_tipos = None
                for i in range(len(partes)):
                    if re.match(r'^\d+,\d{2}$', partes[i]):
                        idx_tipos = i
                        break
                
                if idx_tipos and idx_tipos >= 2:
                    if idx_tipos > 2:
                        posible_ctp = partes[2]
                        # Formatos: 250, 500, 125, 750, 1000, 0,250, 0,500, 0,125, 0,750, 0,338, etc.
                        if re.match(r'^\d+,\d+$', posible_ctp) or re.match(r'^\d{3,4}$', posible_ctp):
                            resultado['C_T_P'] = posible_ctp
                        else:
                            resultado['C_T_P'] = '100'
                    else:
                        resultado['C_T_P'] = '100'
                    
                    resultado['Tipos_AT_IT'] = partes[idx_tipos] if idx_tipos < len(partes) else None
                    resultado['IMS'] = partes[idx_tipos + 1] if idx_tipos + 1 < len(partes) else None
                    resultado['Total'] = partes[idx_tipos + 2] if idx_tipos + 2 < len(partes) else None
                    resultado['Dias_Cot'] = partes[idx_tipos + 3] if idx_tipos + 3 < len(partes) else None
                else:
                    resultado['C_T_P'] = '100'
                    resultado['Tipos_AT_IT'] = partes[-4] if len(partes) >= 4 else None
                    resultado['IMS'] = partes[-3] if len(partes) >= 3 else None
                    resultado['Total'] = partes[-2] if len(partes) >= 2 else None
                    resultado['Dias_Cot'] = partes[-1] if len(partes) >= 1 else None
    
    return resultado

def extraer_codigo_situacion(row):
    """Extrae código de situación de la última columna con valor."""
    for col in reversed(df.columns):
        valor = row[col]
        if pd.notna(valor):
            texto = str(valor).strip()
            # Buscar código de 2-4 caracteres alfanuméricos al final
            match = re.search(r'([A-Z0-9]{2,4})$', texto)
            if match:
                codigo = match.group(1)
                # Filtrar códigos comunes válidos
                if not re.match(r'^\d{4,}$', codigo):
                    return codigo
    return None

# Procesar datos
logging.info("\nProcesando y relacionando datos...")

empleados = []
empleado_actual = None

for idx in range(len(df)):
    row = df.iloc[idx]
    fila_texto = ' '.join([str(v) for v in row.values if pd.notna(v) and str(v) != 'nan'])
    
    if not fila_texto.strip():
        continue
    
    # Verificar si es una fila de fecha (ALTA/BAJA)
    tiene_fecha = bool(re.search(r'(ALTA|BAJA)\s+\d{2}-\d{2}-\d{4}', fila_texto))
    
    if tiene_fecha:
        # Es una fila de fecha, relacionarla con el empleado anterior (si existe)
        if empleado_actual:
            # Parsear fechas y agregar al empleado actual
            fila_fechas = parsear_fila_fechas(fila_texto)
            
            # Si el empleado ya tenía una situación, combinar (ALTA/BAJA)
            if empleado_actual['Situacion'] and fila_fechas.get('Situacion'):
                if empleado_actual['Situacion'] != fila_fechas.get('Situacion'):
                    empleado_actual['Situacion'] = 'ALTA/BAJA'
            else:
                empleado_actual['Situacion'] = fila_fechas.get('Situacion')
            
            # Actualizar fechas (solo si no estaban ya asignadas)
            if not empleado_actual['F_Real_Alta']:
                empleado_actual['F_Real_Alta'] = fila_fechas.get('F_Real_Alta')
            if not empleado_actual['F_Efecto_Alta']:
                empleado_actual['F_Efecto_Alta'] = fila_fechas.get('F_Efecto_Alta')
            # F_Real_Sit y F_Efecto_Sit siempre se actualizan con la última situación
            empleado_actual['F_Real_Sit'] = fila_fechas.get('F_Real_Sit')
            empleado_actual['F_Efecto_Sit'] = fila_fechas.get('F_Efecto_Sit')
            
            # Actualizar valores numéricos (solo si no estaban ya asignados)
            if not empleado_actual['G_C_M']:
                empleado_actual['G_C_M'] = fila_fechas.get('G_C_M')
            if not empleado_actual['T_C']:
                empleado_actual['T_C'] = fila_fechas.get('T_C')
            # C_T_P: actualizar siempre con el valor de la fila de fechas (puede ser 100 si no aparece)
            if fila_fechas.get('C_T_P'):
                empleado_actual['C_T_P'] = fila_fechas.get('C_T_P')
            elif empleado_actual['C_T_P'] is None:
                # Si no hay C_T_P en la fila de fechas y el empleado no tiene uno, usar 100
                empleado_actual['C_T_P'] = '100'
            if not empleado_actual['Tipos_AT_IT']:
                empleado_actual['Tipos_AT_IT'] = fila_fechas.get('Tipos_AT_IT')
            if not empleado_actual['IMS']:
                empleado_actual['IMS'] = fila_fechas.get('IMS')
            if not empleado_actual['Total']:
                empleado_actual['Total'] = fila_fechas.get('Total')
            if not empleado_actual['Dias_Cot']:
                empleado_actual['Dias_Cot'] = fila_fechas.get('Dias_Cot')
            
            # El código CLV de la fila de fechas puede ser diferente, pero mantenemos el del empleado
            # Solo actualizamos si el empleado no tenía código
            if not empleado_actual['CLV']:
                codigo_fecha = extraer_codigo_situacion(row)
                if codigo_fecha:
                    empleado_actual['CLV'] = codigo_fecha
            
            # Guardar empleado y resetear
            empleados.append(empleado_actual)
            empleado_actual = None
        else:
            # Fila de fecha sin empleado previo - buscar empleado en filas anteriores (máximo 3 filas)
            empleado_encontrado = None
            for i in range(max(0, idx-3), idx):
                fila_ant = ' '.join([str(v) for v in df.iloc[i].values if pd.notna(v) and str(v) != 'nan'])
                afiliacion_ant = extraer_afiliacion(fila_ant)
                dni_ant = extraer_dni(fila_ant)
                if afiliacion_ant or dni_ant:
                    # Verificar si este empleado ya fue guardado
                    nombre_ant = limpiar_nombre(fila_ant, dni_ant)
                    # Buscar en empleados guardados recientemente
                    for emp in empleados[-5:]:
                        if emp.get('Numero_Afiliacion') == afiliacion_ant or emp.get('Documento_Identificativo') == dni_ant:
                            if not emp.get('Situacion'):
                                # Este empleado no tenía situación, asignarle esta fecha
                                fila_fechas = parsear_fila_fechas(fila_texto)
                                emp['Situacion'] = fila_fechas.get('Situacion')
                                emp['F_Real_Alta'] = fila_fechas.get('F_Real_Alta')
                                emp['F_Efecto_Alta'] = fila_fechas.get('F_Efecto_Alta')
                                emp['F_Real_Sit'] = fila_fechas.get('F_Real_Sit')
                                emp['F_Efecto_Sit'] = fila_fechas.get('F_Efecto_Sit')
                                emp['G_C_M'] = fila_fechas.get('G_C_M')
                                emp['T_C'] = fila_fechas.get('T_C')
                                emp['Tipos_AT_IT'] = fila_fechas.get('Tipos_AT_IT')
                                emp['IMS'] = fila_fechas.get('IMS')
                                emp['Total'] = fila_fechas.get('Total')
                                emp['Dias_Cot'] = fila_fechas.get('Dias_Cot')
                                logging.info(f"Fila de fecha asignada retroactivamente a empleado en línea {i+1}")
                                break
                    break
        continue
    
    # Verificar si es una fila de empleado (tiene afiliación o DNI)
    afiliacion = extraer_afiliacion(fila_texto)
    dni = extraer_dni(fila_texto)
    
    if afiliacion or dni:
        # Si hay un empleado anterior sin guardar (sin fechas), buscar fechas antes de guardarlo
        if empleado_actual:
            # Buscar fila de fecha en la fila inmediatamente siguiente (índice actual)
            encontro_fecha = False
            if idx < len(df):
                fila_sig = ' '.join([str(v) for v in df.iloc[idx].values if pd.notna(v) and str(v) != 'nan'])
                tiene_fecha_sig = bool(re.search(r'(ALTA|BAJA)\s+\d{2}-\d{2}-\d{4}', fila_sig))
                
                if tiene_fecha_sig:
                    # Verificar que no sea otro empleado (no debe tener afiliación o DNI)
                    tiene_afiliacion_sig = bool(extraer_afiliacion(fila_sig) or extraer_dni(fila_sig))
                    if not tiene_afiliacion_sig:
                        # Es una fila de fecha válida, asignarla
                        fila_fechas = parsear_fila_fechas(fila_sig)
                        empleado_actual['Situacion'] = fila_fechas.get('Situacion')
                        empleado_actual['F_Real_Alta'] = fila_fechas.get('F_Real_Alta')
                        empleado_actual['F_Efecto_Alta'] = fila_fechas.get('F_Efecto_Alta')
                        empleado_actual['F_Real_Sit'] = fila_fechas.get('F_Real_Sit')
                        empleado_actual['F_Efecto_Sit'] = fila_fechas.get('F_Efecto_Sit')
                        empleado_actual['G_C_M'] = fila_fechas.get('G_C_M')
                        empleado_actual['T_C'] = fila_fechas.get('T_C')
                        empleado_actual['Tipos_AT_IT'] = fila_fechas.get('Tipos_AT_IT')
                        empleado_actual['IMS'] = fila_fechas.get('IMS')
                        empleado_actual['Total'] = fila_fechas.get('Total')
                        empleado_actual['Dias_Cot'] = fila_fechas.get('Dias_Cot')
                        encontro_fecha = True
                        logging.info(f"Fila de fecha encontrada para empleado {empleado_actual.get('Nombre_Apellidos', 'N/A')} en línea {idx+1}")
            
            # Guardar empleado (con o sin fechas)
            empleados.append(empleado_actual)
        
        # Es un empleado nuevo, extraer datos básicos
        nombre = limpiar_nombre(fila_texto, dni)
        
        # Si no encontramos nombre en esta fila, buscar en las columnas
        if not nombre:
            for col in df.columns:
                valor_col = row[col]
                if pd.notna(valor_col):
                    nombre_temp = limpiar_nombre(str(valor_col), dni)
                    if nombre_temp:
                        nombre = nombre_temp
                        break
        
        # Extraer código de situación de esta fila (del empleado)
        codigo_empleado = extraer_codigo_situacion(row)
        
        # Crear registro de empleado básico (sin fechas aún)
        empleado_actual = {
            'Numero_Afiliacion': afiliacion,
            'Situacion': None,
            'Documento_Identificativo': dni,
            'F_Real_Alta': None,
            'F_Efecto_Alta': None,
            'F_Real_Sit': None,
            'F_Efecto_Sit': None,
            'Nombre_Apellidos': nombre,
            'G_C_M': None,
            'T_C': None,
            'C_T_P': None,  # Porcentaje de jornada (100% si no aparece)
            'EP_OC': None,  # No aparece en los datos extraídos
            'Tipos_AT_IT': None,
            'IMS': None,
            'Total': None,
            'Dias_Cot': None,
            'CLV': codigo_empleado,  # Código del empleado (de la fila del empleado)
        }
        
        # NO agregar aún, esperar a ver si viene una fila de fecha después

# Si queda un empleado sin guardar al final, buscar fechas en rango amplio antes de guardarlo
if empleado_actual:
    # Buscar fila de fecha en las siguientes 3 filas
    encontro_fecha = False
    for i in range(len(df), min(len(df)+4, len(df))):
        if i < len(df):
            fila_sig = ' '.join([str(v) for v in df.iloc[i].values if pd.notna(v) and str(v) != 'nan'])
            tiene_fecha_sig = bool(re.search(r'(ALTA|BAJA)\s+\d{2}-\d{2}-\d{4}', fila_sig))
            
            if tiene_fecha_sig:
                tiene_afiliacion_sig = bool(extraer_afiliacion(fila_sig) or extraer_dni(fila_sig))
                if not tiene_afiliacion_sig:
                    fila_fechas = parsear_fila_fechas(fila_sig)
                    empleado_actual['Situacion'] = fila_fechas.get('Situacion')
                    empleado_actual['F_Real_Alta'] = fila_fechas.get('F_Real_Alta')
                    empleado_actual['F_Efecto_Alta'] = fila_fechas.get('F_Efecto_Alta')
                    empleado_actual['F_Real_Sit'] = fila_fechas.get('F_Real_Sit')
                    empleado_actual['F_Efecto_Sit'] = fila_fechas.get('F_Efecto_Sit')
                    empleado_actual['G_C_M'] = fila_fechas.get('G_C_M')
                    empleado_actual['T_C'] = fila_fechas.get('T_C')
                    empleado_actual['Tipos_AT_IT'] = fila_fechas.get('Tipos_AT_IT')
                    empleado_actual['IMS'] = fila_fechas.get('IMS')
                    empleado_actual['Total'] = fila_fechas.get('Total')
                    empleado_actual['Dias_Cot'] = fila_fechas.get('Dias_Cot')
                    encontro_fecha = True
                    break
    
    empleados.append(empleado_actual)

# Crear DataFrame final
df_final = pd.DataFrame(empleados)

# Filtrar nombre corrupto
nombre_corrupto = "LACIOSN ÓZRA NÓCIAZITCO DE ANTCUE OGDICÓ"
if 'Nombre_Apellidos' in df_final.columns:
    antes = len(df_final)
    df_final = df_final[df_final['Nombre_Apellidos'] != nombre_corrupto].copy()
    despues = len(df_final)
    if antes != despues:
        logging.info(f"Filtrado nombre corrupto: {antes - despues} registro(s) eliminado(s)")

# Limpiar filas sin datos esenciales
df_final = df_final.dropna(subset=['Numero_Afiliacion', 'Documento_Identificativo', 'Nombre_Apellidos'], how='all')

# Ordenar por número de afiliación si está disponible
if 'Numero_Afiliacion' in df_final.columns:
    df_final = df_final.sort_values('Numero_Afiliacion', na_position='last')

logging.info(f"\nDatos procesados: {len(df_final)} empleados")

# Estadísticas
logging.info("\n" + "="*60)
logging.info("ESTADÍSTICAS FINALES")
logging.info("="*60)
logging.info(f"Total empleados: {len(df_final)}")
logging.info(f"Con situación: {df_final['Situacion'].notna().sum()}")
logging.info(f"Con F_Real_Alta: {df_final['F_Real_Alta'].notna().sum()}")
logging.info(f"Con F_Efecto_Alta: {df_final['F_Efecto_Alta'].notna().sum()}")
logging.info(f"Con F_Real_Sit: {df_final['F_Real_Sit'].notna().sum()}")
logging.info(f"Con F_Efecto_Sit: {df_final['F_Efecto_Sit'].notna().sum()}")
logging.info(f"Con G_C_M: {df_final['G_C_M'].notna().sum()}")
logging.info(f"Con T_C: {df_final['T_C'].notna().sum()}")
logging.info(f"Con Tipos_AT_IT: {df_final['Tipos_AT_IT'].notna().sum()}")
logging.info(f"Con IMS: {df_final['IMS'].notna().sum()}")
logging.info(f"Con Total: {df_final['Total'].notna().sum()}")
logging.info(f"Con Dias_Cot: {df_final['Dias_Cot'].notna().sum()}")
logging.info(f"Con CLV: {df_final['CLV'].notna().sum()}")

# Guardar
logging.info(f"\nGuardando archivo completo: {output_file}")
df_final.to_csv(output_file, index=False, encoding='utf-8-sig')

logging.info("\n" + "="*60)
logging.info("MUESTRA DE DATOS FINALES")
logging.info("="*60)
print(df_final.head(5).to_string())

logging.info(f"\n✓ Archivo guardado: {output_file}")
logging.info(f"✓ Filas: {len(df_final)}")
logging.info(f"✓ Columnas: {len(df_final.columns)}")

