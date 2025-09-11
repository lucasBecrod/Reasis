#!/usr/bin/env python3
"""
Vinculación de último recurso - Búsqueda directa en tabla instituciones_educativas
Metodología final para completar vinculaciones faltantes
"""

import sqlite3
import pandas as pd

def extraer_codigos_sin_vincular():
    """Extraer listas únicas de códigos y nombres sin vincular"""
    print("PASO 1: EXTRAER CÓDIGOS Y NOMBRES SIN VINCULAR")
    print("=" * 60)
    
    conn = sqlite3.connect('reasis_database.db')
    
    # Lista única de codigo_local donde codigo_modular es NULL
    codigos_null = pd.read_sql_query('''
        SELECT DISTINCT codigo_local, COUNT(*) as estudiantes
        FROM resultados_academicos 
        WHERE codigo_modular IS NULL AND codigo_local IS NOT NULL
        GROUP BY codigo_local
        ORDER BY estudiantes DESC
    ''', conn)
    
    # Lista única de nombre_ie_original donde codigo_modular es NULL
    nombres_null = pd.read_sql_query('''
        SELECT DISTINCT nombre_ie_original, COUNT(*) as estudiantes
        FROM resultados_academicos 
        WHERE codigo_modular IS NULL AND nombre_ie_original IS NOT NULL
        GROUP BY nombre_ie_original
        ORDER BY estudiantes DESC
    ''', conn)
    
    print(f"Códigos locales sin vincular: {len(codigos_null)}")
    print(f"Nombres IE sin vincular: {len(nombres_null)}")
    
    total_estudiantes_null = pd.read_sql_query('''
        SELECT COUNT(*) as count FROM resultados_academicos WHERE codigo_modular IS NULL
    ''', conn).iloc[0, 0]
    
    print(f"Total estudiantes sin vincular: {total_estudiantes_null:,}")
    
    conn.close()
    
    return codigos_null, nombres_null

def buscar_coincidencias_directas_codigos(codigos_null):
    """Buscar coincidencias directas por código local"""
    print("\nPASO 2: BUSCAR COINCIDENCIAS DIRECTAS POR CÓDIGO LOCAL")
    print("=" * 60)
    
    conn = sqlite3.connect('reasis_database.db')
    
    coincidencias_codigo = []
    
    print("Buscando coincidencias directas...")
    
    for i, row in codigos_null.iterrows():
        codigo = row['codigo_local']
        estudiantes = row['estudiantes']
        
        if (i + 1) % 20 == 0:  # Progreso cada 20
            print(f"Procesado {i+1}/{len(codigos_null)} códigos...")
        
        # Búsqueda exacta en codigo_local
        match = pd.read_sql_query('''
            SELECT codigo_modular, codigo_local, nombre_institucion
            FROM instituciones_educativas 
            WHERE codigo_local = ?
            LIMIT 1
        ''', conn, params=[codigo])
        
        if len(match) > 0:
            coincidencias_codigo.append({
                'codigo_local': codigo,
                'codigo_modular': match.iloc[0]['codigo_modular'],
                'nombre_institucion': match.iloc[0]['nombre_institucion'],
                'estudiantes_afectados': estudiantes,
                'metodo': 'codigo_local_directo'
            })
    
    print(f"Coincidencias encontradas por código: {len(coincidencias_codigo)}")
    
    conn.close()
    return coincidencias_codigo

def buscar_coincidencias_directas_nombres(nombres_null):
    """Buscar coincidencias directas por nombre IE"""
    print("\nPASO 3: BUSCAR COINCIDENCIAS DIRECTAS POR NOMBRE IE")
    print("=" * 60)
    
    conn = sqlite3.connect('reasis_database.db')
    
    coincidencias_nombre = []
    
    print("Buscando coincidencias por nombre...")
    
    for i, row in nombres_null.iterrows():
        nombre = row['nombre_ie_original']
        estudiantes = row['estudiantes']
        
        if (i + 1) % 20 == 0:  # Progreso cada 20
            print(f"Procesado {i+1}/{len(nombres_null)} nombres...")
        
        # Búsqueda exacta en nombre_institucion
        match = pd.read_sql_query('''
            SELECT codigo_modular, codigo_local, nombre_institucion
            FROM instituciones_educativas 
            WHERE UPPER(TRIM(nombre_institucion)) = UPPER(TRIM(?))
            LIMIT 1
        ''', conn, params=[nombre])
        
        if len(match) > 0:
            coincidencias_nombre.append({
                'codigo_local_encontrado': match.iloc[0]['codigo_local'],
                'codigo_modular': match.iloc[0]['codigo_modular'],
                'nombre_institucion': match.iloc[0]['nombre_institucion'],
                'nombre_original': nombre,
                'estudiantes_afectados': estudiantes,
                'metodo': 'nombre_ie_directo'
            })
    
    print(f"Coincidencias encontradas por nombre: {len(coincidencias_nombre)}")
    
    conn.close()
    return coincidencias_nombre

def aplicar_vinculaciones_directas(coincidencias_codigo, coincidencias_nombre):
    """Aplicar las vinculaciones directas encontradas"""
    print("\nPASO 4: APLICAR VINCULACIONES DIRECTAS")
    print("=" * 60)
    
    conn = sqlite3.connect('reasis_database.db')
    
    total_actualizados = 0
    
    # Aplicar vinculaciones por código local
    print("Aplicando vinculaciones por código local...")
    for coincidencia in coincidencias_codigo:
        updated = conn.execute('''
            UPDATE resultados_academicos 
            SET codigo_modular = ?, 
                metodo_vinculacion = ?
            WHERE codigo_local = ? 
            AND codigo_modular IS NULL
        ''', (
            coincidencia['codigo_modular'],
            coincidencia['metodo'],
            coincidencia['codigo_local']
        )).rowcount
        
        total_actualizados += updated
        
        if updated > 0:
            print(f"  {coincidencia['codigo_local']} -> {coincidencia['codigo_modular']} ({updated} estudiantes)")
    
    # Aplicar vinculaciones por nombre IE
    print("\nAplicando vinculaciones por nombre IE...")
    for coincidencia in coincidencias_nombre:
        updated = conn.execute('''
            UPDATE resultados_academicos 
            SET codigo_modular = ?, 
                metodo_vinculacion = ?
            WHERE UPPER(TRIM(nombre_ie_original)) = UPPER(TRIM(?))
            AND codigo_modular IS NULL
        ''', (
            coincidencia['codigo_modular'],
            coincidencia['metodo'],
            coincidencia['nombre_original']
        )).rowcount
        
        total_actualizados += updated
        
        if updated > 0:
            print(f"  {coincidencia['nombre_original']} -> {coincidencia['codigo_modular']} ({updated} estudiantes)")
    
    conn.commit()
    conn.close()
    
    return total_actualizados

def generar_reporte_final():
    """Generar reporte final de vinculación"""
    print("\nRESULTADO FINAL - VINCULACIÓN DE ÚLTIMO RECURSO")
    print("=" * 60)
    
    conn = sqlite3.connect('reasis_database.db')
    
    # Métricas finales
    total = 15054
    vinculados = pd.read_sql_query('SELECT COUNT(*) as count FROM resultados_academicos WHERE codigo_modular IS NOT NULL', conn).iloc[0, 0]
    sin_vincular = total - vinculados
    porcentaje = (vinculados / total * 100) if total > 0 else 0
    
    instituciones_ila = pd.read_sql_query('''
        SELECT COUNT(DISTINCT codigo_modular) as count 
        FROM resultados_academicos 
        WHERE codigo_modular IS NOT NULL
    ''', conn).iloc[0, 0]
    
    print(f"Total registros académicos: {total:,}")
    print(f"Registros vinculados: {vinculados:,}")
    print(f"Sin vincular: {sin_vincular:,}")
    print(f"Porcentaje éxito: {porcentaje:.1f}%")
    print(f"Instituciones con ILA: {instituciones_ila}")
    
    # Comparar con objetivo
    objetivo_958 = int(total * 0.958)
    objetivo_63_iiee = 63
    
    print(f"\nCOMPARACIÓN CON OBJETIVOS:")
    print(f"Objetivo 95.8%: {objetivo_958:,} registros -> Logrado: {vinculados:,} ({porcentaje:.1f}%)")
    print(f"Objetivo 63 IIEE: {objetivo_63_iiee} -> Logrado: {instituciones_ila}")
    
    if porcentaje >= 95.8:
        print("OBJETIVO PORCENTAJE ALCANZADO!")
    else:
        faltante = objetivo_958 - vinculados
        print(f"Faltan: {faltante:,} registros ({faltante/total*100:.1f}%)")
    
    if instituciones_ila >= 63:
        print("OBJETIVO INSTITUCIONES ALCANZADO!")
    else:
        faltante_iiee = 63 - instituciones_ila
        print(f"Faltan: {faltante_iiee} instituciones")
    
    conn.close()
    
    return porcentaje, instituciones_ila

def vinculacion_ultimo_recurso():
    """Función principal - Vinculación de último recurso"""
    print("VINCULACION DE ULTIMO RECURSO - METODOLOGIA FINAL")
    print("=" * 70)
    
    # Paso 1: Extraer códigos y nombres sin vincular
    codigos_null, nombres_null = extraer_codigos_sin_vincular()
    
    # Paso 2: Buscar coincidencias por código local
    coincidencias_codigo = buscar_coincidencias_directas_codigos(codigos_null)
    
    # Paso 3: Buscar coincidencias por nombre IE
    coincidencias_nombre = buscar_coincidencias_directas_nombres(nombres_null)
    
    # Paso 4: Aplicar vinculaciones
    actualizados = aplicar_vinculaciones_directas(coincidencias_codigo, coincidencias_nombre)
    
    print(f"\nTOTAL REGISTROS ACTUALIZADOS: {actualizados:,}")
    
    # Paso 5: Reporte final
    porcentaje, instituciones = generar_reporte_final()
    
    return porcentaje, instituciones

if __name__ == "__main__":
    porcentaje_final, iiee_final = vinculacion_ultimo_recurso()
    print(f"\nRESULTADO FINAL: {porcentaje_final:.1f}% vinculacion, {iiee_final} IIEE con ILA")