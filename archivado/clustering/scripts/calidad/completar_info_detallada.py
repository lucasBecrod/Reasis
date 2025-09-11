#!/usr/bin/env python3
"""
Script para extraer información detallada de las 9 instituciones del padrón MINEDU
"""

from dbfread import DBF
import pandas as pd
import sqlite3
import re

def extraer_info_completa_padron():
    """Extrae toda la información disponible del padrón MINEDU"""
    
    # Lista de códigos modulares a buscar
    codigos = ['0600692', '1768829', '0481093', '0488403', '0304642', '0428714', '3025715', '2533906', '1781897']
    
    print("Extrayendo información completa del padrón MINEDU...")
    
    try:
        # Leer archivo DBF
        table = DBF('data/bases_de_datos/Padron_web_20250731/Padron_web.dbf', encoding='latin-1')
        
        # Convertir a DataFrame
        records = []
        for record in table:
            records.append(dict(record))
        
        df = pd.DataFrame(records)
        df['COD_MOD'] = df['COD_MOD'].astype(str)
        
        # Buscar todas nuestras instituciones
        todas_variantes = []
        for codigo in codigos:
            todas_variantes.extend([codigo, codigo.zfill(7), codigo.lstrip('0')])
        
        df_encontradas = df[df['COD_MOD'].isin(todas_variantes)].copy()
        
        if len(df_encontradas) == 0:
            print("No se encontraron instituciones")
            return []
        
        print(f"Encontradas {len(df_encontradas)} instituciones")
        print(f"Columnas disponibles: {len(df.columns)}")
        
        # Mapear columnas útiles
        instituciones_completas = []
        
        for _, row in df_encontradas.iterrows():
            codigo_original = next((c for c in codigos if c in [row['COD_MOD'], row['COD_MOD'].lstrip('0'), row['COD_MOD'].zfill(7)]), row['COD_MOD'])
            
            info = {
                'codigo_modular': codigo_original,
                # Información básica
                'nombre_ie': limpiar_texto(str(row.get('CEN_EDU', ''))),
                'anexo': row.get('ANEXO', 0),
                'codigo_local': str(row.get('CODLOCAL', '')),
                
                # Ubicación geográfica
                'departamento': limpiar_texto(str(row.get('D_DPTO', ''))),
                'provincia': limpiar_texto(str(row.get('D_PROV', ''))),
                'distrito': limpiar_texto(str(row.get('D_DIST', ''))),
                'centro_poblado': limpiar_texto(str(row.get('D_CP', ''))),
                'direccion': limpiar_texto(str(row.get('DIRECCION', ''))),
                
                # Características educativas
                'nivel_educativo': limpiar_texto(str(row.get('D_NIV_MOD', ''))),
                'modalidad': limpiar_texto(str(row.get('D_FORMA', ''))),
                'gestion': limpiar_texto(str(row.get('D_GESTION', ''))),
                'tipo_sexo': limpiar_texto(str(row.get('D_TIPSSEXO', ''))),
                'turno': limpiar_texto(str(row.get('D_COD_TUR', ''))),
                
                # Datos académicos si están disponibles
                'total_alumnos': obtener_numero(row.get('TALUM')),
                'alumnos_hombres': obtener_numero(row.get('HALUM')),
                'alumnos_mujeres': obtener_numero(row.get('MALUM')),
                'total_docentes': obtener_numero(row.get('TDOC')),
                'docentes_hombres': obtener_numero(row.get('HDOC')),
                'docentes_mujeres': obtener_numero(row.get('MDOC')),
                'total_secciones': obtener_numero(row.get('TSEC')),
                
                # Características específicas
                'es_rural': determinar_ruralidad(row),
                'es_eib': determinar_eib(row),
                
                # Coordenadas si están disponibles
                'latitud': obtener_numero(row.get('NLAT_IE')),
                'longitud': obtener_numero(row.get('NLONG_IE')),
                'altitud': obtener_numero(row.get('ALTITUD'))
            }
            
            instituciones_completas.append(info)
            
            print(f"\n=== {info['codigo_modular']} - {info['nombre_ie']} ===")
            print(f"Ubicación: {info['departamento']}, {info['provincia']}, {info['distrito']}")
            print(f"Nivel: {info['nivel_educativo']}")
            print(f"Alumnos: {info['total_alumnos']}, Docentes: {info['total_docentes']}, Secciones: {info['total_secciones']}")
            print(f"Rural: {info['es_rural']}, EIB: {info['es_eib']}")
            if info['latitud'] and info['longitud']:
                print(f"Coordenadas: {info['latitud']}, {info['longitud']}")
        
        return instituciones_completas
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return []

def limpiar_texto(texto):
    """Limpia texto de caracteres especiales"""
    if not texto or texto == 'None':
        return None
    # Limpiar caracteres especiales comunes
    texto = texto.replace('Ñ', 'N').replace('ñ', 'n')
    # Remover caracteres de control
    texto = re.sub(r'[^\w\s\-\.]', '', texto)
    return texto.strip() if texto.strip() else None

def obtener_numero(valor):
    """Convierte valor a número o None"""
    if valor is None or valor == '' or str(valor).strip() == '':
        return None
    try:
        return int(float(str(valor)))
    except:
        return None

def determinar_ruralidad(row):
    """Determina si la institución es rural basado en datos del padrón"""
    # Buscar indicadores de ruralidad en las columnas disponibles
    campos_rural = ['D_AREA', 'AREA', 'D_CP', 'CARACTERISTICA']
    
    for campo in campos_rural:
        if campo in row and row[campo]:
            valor = str(row[campo]).upper()
            if any(keyword in valor for keyword in ['RURAL', 'SIERRA', 'SELVA', 'CENTRO POBLADO']):
                return 1
    
    # Si no hay información clara, usar None para mantener el valor actual
    return None

def determinar_eib(row):
    """Determina si es institución EIB"""
    # Buscar indicadores EIB en modalidad o características
    campos_eib = ['D_FORMA', 'MODALIDAD', 'CARACTERISTICA', 'D_COD_CAR']
    
    for campo in campos_eib:
        if campo in row and row[campo]:
            valor = str(row[campo]).upper()
            if any(keyword in valor for keyword in ['EIB', 'INTERCULTURAL', 'BILINGUE']):
                return 1
    
    # Para instituciones Fe y Alegría regulares, típicamente no son EIB
    return 0

def generar_script_actualizacion(instituciones):
    """Genera script SQL para actualizar la base de datos"""
    
    if not instituciones:
        print("No hay instituciones para actualizar")
        return
    
    updates = []
    updates.append("-- Script de actualización para las 9 instituciones integradas")
    updates.append("-- Generado automáticamente desde el padrón MINEDU")
    updates.append("")
    
    for inst in instituciones:
        codigo = inst['codigo_modular']
        
        # Construir UPDATE statement
        sets = []
        
        # Campos de texto
        campos_texto = ['direccion', 'centro_poblado', 'tipo_sexo', 'turno']
        for campo in campos_texto:
            if inst[campo]:
                valor_limpio = inst[campo].replace("'", "''")  # Escapar comillas
                sets.append(f"{campo} = '{valor_limpio}'")
        
        # Campos numéricos
        campos_numericos = ['total_alumnos', 'alumnos_hombres', 'alumnos_mujeres', 
                           'total_docentes', 'docentes_hombres', 'docentes_mujeres',
                           'total_secciones', 'latitud', 'longitud', 'altitud']
        for campo in campos_numericos:
            if inst[campo] is not None:
                sets.append(f"{campo} = {inst[campo]}")
        
        # Campos booleanos
        if inst['es_rural'] is not None:
            sets.append(f"es_rural = {inst['es_rural']}")
        if inst['es_eib'] is not None:
            sets.append(f"es_eib = {inst['es_eib']}")
        
        if sets:
            update_sql = f"UPDATE instituciones_educativas SET {', '.join(sets)} WHERE codigo_modular = '{codigo}';"
            updates.append(update_sql)
            updates.append("")
    
    # Guardar archivo
    with open('actualizacion_completa_9_instituciones.sql', 'w', encoding='utf-8') as f:
        f.write('\n'.join(updates))
    
    print(f"\nScript de actualización generado: 'actualizacion_completa_9_instituciones.sql'")
    print(f"Total de instituciones a actualizar: {len(instituciones)}")

if __name__ == "__main__":
    instituciones = extraer_info_completa_padron()
    if instituciones:
        generar_script_actualizacion(instituciones)