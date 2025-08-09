#!/usr/bin/env python3
"""
Vinculador Homologación Inteligente - Proyecto Reasis  
Vincula por códigos y nombres para maximizar coincidencias RER
"""

import pandas as pd
import sqlite3
import re

def extraer_codigo_numerico(codigo_str):
    """Extraer código numérico de strings mixtos"""
    if pd.isna(codigo_str):
        return None
    
    codigo_str = str(codigo_str).strip()
    
    # Buscar números al inicio
    match = re.match(r'^(\d+)', codigo_str)
    if match:
        return match.group(1)
    
    return None

def normalizar_nombre(nombre):
    """Normalizar nombre para comparación"""
    if pd.isna(nombre):
        return ""
    
    nombre = str(nombre).upper()
    # Remover caracteres especiales y espacios extra
    nombre = re.sub(r'[^\w\s]', ' ', nombre)
    nombre = re.sub(r'\s+', ' ', nombre).strip()
    return nombre

def procesar_homologacion_inteligente():
    """Procesar homologación con múltiples estrategias de vinculación"""
    print("VINCULADOR HOMOLOGACIÓN INTELIGENTE")
    print("=" * 60)
    
    # Leer archivo de homologación
    try:
        df_homolog = pd.read_excel('assets/Consultoria/DatosLucas/homologacionManualLucas.xlsx', sheet_name='colegios')
        print(f"Archivo homologación: {len(df_homolog)} registros")
    except Exception as e:
        print(f"ERROR leyendo homologación: {e}")
        return 0
    
    # Leer datos de instituciones
    conn = sqlite3.connect('reasis_database.db')
    
    df_ie = pd.read_sql_query('''
        SELECT codigo_modular, codigo_local, nombre_institucion, codigo_red
        FROM instituciones_educativas
        WHERE codigo_local IS NOT NULL
    ''', conn)
    
    print(f"Instituciones educativas: {len(df_ie)} registros")
    
    # Preparar datos para vinculación
    df_homolog['codigo_numerico'] = df_homolog['codigo_local'].apply(extraer_codigo_numerico)
    df_homolog['nombre_normalizado'] = df_homolog['nombre_ie'].apply(normalizar_nombre)
    df_homolog['rer_numero'] = df_homolog['rer'].str.extract(r'(\d+)').iloc[:, 0]
    
    df_ie['nombre_normalizado'] = df_ie['nombre_institucion'].apply(normalizar_nombre)
    
    print(f"\nEstrategias de vinculación:")
    
    vinculaciones_exitosas = []
    
    # ESTRATEGIA 1: Coincidencia exacta por código numérico extraído
    print("1. Vinculación por código numérico...")
    
    for _, row_h in df_homolog.iterrows():
        if pd.notna(row_h['codigo_numerico']) and pd.notna(row_h['rer_numero']):
            codigo_buscar = str(row_h['codigo_numerico'])
            
            # Buscar en codigo_local de IE
            coincidencias = df_ie[df_ie['codigo_local'].str.contains(codigo_buscar, na=False)]
            
            if len(coincidencias) > 0:
                for _, row_ie in coincidencias.iterrows():
                    vinculaciones_exitosas.append({
                        'codigo_modular': row_ie['codigo_modular'],
                        'codigo_local': row_ie['codigo_local'],
                        'nombre_ie': row_ie['nombre_institucion'],
                        'rer_numero': row_h['rer_numero'],
                        'metodo': 'codigo_numerico',
                        'fuente_homolog': row_h['nombre_ie']
                    })
    
    print(f"   Encontradas: {len(vinculaciones_exitosas)} por código")
    
    # ESTRATEGIA 2: Coincidencia por nombre normalizado
    print("2. Vinculación por nombre...")
    
    codigos_ya_vinculados = set([v['codigo_modular'] for v in vinculaciones_exitosas])
    
    for _, row_h in df_homolog.iterrows():
        if pd.notna(row_h['nombre_normalizado']) and pd.notna(row_h['rer_numero']):
            nombre_buscar = row_h['nombre_normalizado']
            
            # Buscar coincidencias de nombre
            for _, row_ie in df_ie.iterrows():
                if row_ie['codigo_modular'] not in codigos_ya_vinculados:
                    nombre_ie = row_ie['nombre_normalizado']
                    
                    # Verificar si el nombre de homologación está contenido en el nombre de IE
                    if nombre_buscar in nombre_ie or nombre_ie in nombre_buscar:
                        # Verificar coincidencia más estricta (al menos 3 palabras en común)
                        palabras_h = set(nombre_buscar.split())
                        palabras_ie = set(nombre_ie.split())
                        
                        if len(palabras_h.intersection(palabras_ie)) >= min(3, len(palabras_h)):
                            vinculaciones_exitosas.append({
                                'codigo_modular': row_ie['codigo_modular'],
                                'codigo_local': row_ie['codigo_local'],
                                'nombre_ie': row_ie['nombre_institucion'],
                                'rer_numero': row_h['rer_numero'],
                                'metodo': 'nombre_normalizado',
                                'fuente_homolog': row_h['nombre_ie']
                            })
                            codigos_ya_vinculados.add(row_ie['codigo_modular'])
                            break
    
    vinculaciones_por_nombre = len(vinculaciones_exitosas) - len([v for v in vinculaciones_exitosas if v['metodo'] == 'codigo_numerico'])
    print(f"   Encontradas: {vinculaciones_por_nombre} por nombre")
    
    # ESTRATEGIA 3: Coincidencia por palabras clave específicas
    print("3. Vinculación por palabras clave...")
    
    palabras_clave_fe_alegria = ['FE Y ALEGRIA', 'FEY ALEGRIA', 'CRISTO REY', 'CORAZON DE JESUS', 'VIRGEN DEL CARMEN', 'SANTA ROSA']
    
    vinculaciones_iniciales = len(vinculaciones_exitosas)
    
    for palabra_clave in palabras_clave_fe_alegria:
        # Buscar en homologación
        homolog_con_palabra = df_homolog[df_homolog['nombre_normalizado'].str.contains(palabra_clave, na=False)]
        
        # Buscar en IE
        ie_con_palabra = df_ie[df_ie['nombre_normalizado'].str.contains(palabra_clave, na=False)]
        ie_con_palabra = ie_con_palabra[~ie_con_palabra['codigo_modular'].isin(codigos_ya_vinculados)]
        
        # Vincular si hay exactamente una coincidencia en cada lado
        if len(homolog_con_palabra) == 1 and len(ie_con_palabra) == 1:
            row_h = homolog_con_palabra.iloc[0]
            row_ie = ie_con_palabra.iloc[0]
            
            vinculaciones_exitosas.append({
                'codigo_modular': row_ie['codigo_modular'],
                'codigo_local': row_ie['codigo_local'],
                'nombre_ie': row_ie['nombre_institucion'],
                'rer_numero': row_h['rer_numero'],
                'metodo': 'palabra_clave',
                'fuente_homolog': row_h['nombre_ie']
            })
            codigos_ya_vinculados.add(row_ie['codigo_modular'])
    
    vinculaciones_por_palabra = len(vinculaciones_exitosas) - vinculaciones_iniciales
    print(f"   Encontradas: {vinculaciones_por_palabra} por palabra clave")
    
    print(f"\nTOTAL VINCULACIONES IDENTIFICADAS: {len(vinculaciones_exitosas)}")
    
    # Mostrar muestra de vinculaciones
    if len(vinculaciones_exitosas) > 0:
        print(f"\nMuestra de vinculaciones encontradas:")
        df_vinc = pd.DataFrame(vinculaciones_exitosas)
        print(df_vinc[['nombre_ie', 'rer_numero', 'metodo', 'fuente_homolog']].head(10).to_string(index=False))
        
        # Aplicar vinculaciones a la base de datos
        aplicar_vinculaciones(df_vinc, conn)
    
    conn.close()
    return len(vinculaciones_exitosas)

def aplicar_vinculaciones(df_vinculaciones, conn):
    """Aplicar vinculaciones encontradas a la base de datos"""
    print(f"\nAPLICANDO VINCULACIONES A LA BASE DE DATOS")
    print("-" * 50)
    
    cursor = conn.cursor()
    actualizadas = 0
    
    for _, row in df_vinculaciones.iterrows():
        rer_numero = str(row['rer_numero'])
        codigo_modular = row['codigo_modular']
        
        # Mapear número RER a código de red
        codigo_red = None
        if rer_numero == '44':
            codigo_red = 'RER FA 44'
        elif rer_numero == '47':
            codigo_red = 'RER FA 47'
        elif rer_numero == '48':
            codigo_red = 'RER FA 48'
        elif rer_numero == '54':
            codigo_red = 'RER FA 54'
        elif rer_numero == '72':
            codigo_red = 'RER FA 72'
        elif rer_numero == '79':
            codigo_red = 'RER FA 79'
        
        if codigo_red:
            # Actualizar solo si no tiene RER asignada
            cursor.execute('''
                UPDATE instituciones_educativas 
                SET codigo_red = ?
                WHERE codigo_modular = ? 
                AND (codigo_red IS NULL OR codigo_red = '')
            ''', [codigo_red, codigo_modular])
            
            if cursor.rowcount > 0:
                actualizadas += 1
                print(f"  {row['nombre_ie'][:50]}... -> {codigo_red}")
    
    conn.commit()
    
    print(f"\nInstituciones actualizadas: {actualizadas}")
    
    # Generar reporte final
    resultado_final = pd.read_sql_query('''
        SELECT 
            ie.codigo_red,
            r.nombre_completo,
            r.lugar,
            COUNT(*) as instituciones_vinculadas
        FROM instituciones_educativas ie
        INNER JOIN redes_fe_y_alegria r ON ie.codigo_red = r.codigo_red
        GROUP BY ie.codigo_red, r.nombre_completo, r.lugar
        ORDER BY instituciones_vinculadas DESC
    ''', conn)
    
    print(f"\nRESULTADO FINAL DESPUÉS DE VINCULACIÓN INTELIGENTE:")
    print(resultado_final.to_string(index=False))
    
    # Estadísticas totales
    total_vinculadas = resultado_final['instituciones_vinculadas'].sum()
    total_instituciones = pd.read_sql_query('SELECT COUNT(*) as count FROM instituciones_educativas', conn).iloc[0, 0]
    
    print(f"\nESTADÍSTICAS FINALES:")
    print(f"Total instituciones: {total_instituciones}")
    print(f"Vinculadas con RER: {total_vinculadas}")
    print(f"Porcentaje vinculado: {total_vinculadas/total_instituciones*100:.1f}%")
    print(f"Mejora lograda: +{actualizadas} instituciones")
    
    return actualizadas

def main():
    """Función principal"""
    print("PROCESO DE VINCULACIÓN HOMOLOGACIÓN INTELIGENTE")
    print("=" * 70)
    
    mejoras = procesar_homologacion_inteligente()
    
    print(f"\n{'='*70}")
    print("VINCULACIÓN HOMOLOGACIÓN INTELIGENTE COMPLETADA")
    print(f"Total vinculaciones identificadas y aplicadas: {mejoras}")
    print("="*70)
    
    return mejoras

if __name__ == "__main__":
    main()