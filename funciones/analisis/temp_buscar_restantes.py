#!/usr/bin/env python3
"""
Buscar códigos restantes críticos en BD instituciones 
Continuación del proceso de expansión masiva
"""

import sqlite3
import pandas as pd
import re

def buscar_codigo_en_bd(conn, codigo_buscar, nombre_ejemplo):
    """Busca un código en BD instituciones usando múltiples estrategias LIKE"""
    
    print(f"\nBuscando: '{codigo_buscar}' (ejemplo: {nombre_ejemplo})")
    
    # Estrategia 1: Búsqueda directa en codigo_local
    match1 = pd.read_sql_query('''
        SELECT codigo_modular, codigo_local, nombre_institucion, 'codigo_local_exacto' as metodo
        FROM instituciones_educativas 
        WHERE codigo_local = ?
        LIMIT 1
    ''', conn, params=[codigo_buscar])
    
    if len(match1) > 0:
        print(f"  EXACTO en codigo_local: {match1.iloc[0]['codigo_modular']} - {match1.iloc[0]['nombre_institucion']}")
        return match1.iloc[0]
    
    # Estrategia 2: Búsqueda en codigo_modular
    match2 = pd.read_sql_query('''
        SELECT codigo_modular, codigo_local, nombre_institucion, 'codigo_modular_exacto' as metodo
        FROM instituciones_educativas 
        WHERE codigo_modular = ?
        LIMIT 1
    ''', conn, params=[codigo_buscar])
    
    if len(match2) > 0:
        print(f"  EXACTO en codigo_modular: {match2.iloc[0]['codigo_modular']} - {match2.iloc[0]['nombre_institucion']}")
        return match2.iloc[0]
    
    # Estrategia 3: LIKE en nombre_institucion usando código
    codigo_limpio = re.sub(r'\D', '', codigo_buscar)  # Solo números
    if codigo_limpio:
        match3 = pd.read_sql_query('''
            SELECT codigo_modular, codigo_local, nombre_institucion, 'nombre_like_codigo' as metodo
            FROM instituciones_educativas 
            WHERE nombre_institucion LIKE ?
            LIMIT 1
        ''', conn, params=[f'%{codigo_limpio}%'])
        
        if len(match3) > 0:
            print(f"  LIKE en nombre (codigo): {match3.iloc[0]['codigo_modular']} - {match3.iloc[0]['nombre_institucion']}")
            return match3.iloc[0]
    
    # Estrategia 4: LIKE en nombre_institucion usando nombre ejemplo
    if nombre_ejemplo and len(nombre_ejemplo) > 5:
        # Extraer palabras clave del nombre
        palabras = re.findall(r'\b[A-Z][A-Z\s]{3,}\b', nombre_ejemplo.upper())
        if palabras:
            palabra_clave = palabras[0].strip()
            match4 = pd.read_sql_query('''
                SELECT codigo_modular, codigo_local, nombre_institucion, 'nombre_like_palabras' as metodo
                FROM instituciones_educativas 
                WHERE UPPER(nombre_institucion) LIKE ?
                LIMIT 1
            ''', conn, params=[f'%{palabra_clave}%'])
            
            if len(match4) > 0:
                print(f"  LIKE en nombre (palabras): {match4.iloc[0]['codigo_modular']} - {match4.iloc[0]['nombre_institucion']}")
                return match4.iloc[0]
    
    # Estrategia 5: LIKE parcial en codigo_local
    if len(codigo_buscar) >= 4:
        codigo_parcial = codigo_buscar[:4]  # Primeros 4 caracteres
        match5 = pd.read_sql_query('''
            SELECT codigo_modular, codigo_local, nombre_institucion, 'codigo_local_like' as metodo
            FROM instituciones_educativas 
            WHERE codigo_local LIKE ?
            LIMIT 1
        ''', conn, params=[f'{codigo_parcial}%'])
        
        if len(match5) > 0:
            print(f"  LIKE en codigo_local: {match5.iloc[0]['codigo_modular']} - {match5.iloc[0]['nombre_institucion']}")
            return match5.iloc[0]
    
    print(f"  NO ENCONTRADO")
    return None

def buscar_codigos_restantes():
    print('PASO 7: BÚSQUEDA DE CÓDIGOS RESTANTES MÁS CRÍTICOS')
    print('=' * 70)
    
    conn = sqlite3.connect('reasis_database.db')
    
    # Obtener códigos restantes más críticos
    codigos_restantes = pd.read_sql_query('''
        SELECT 
            codigo_local, 
            COUNT(*) as estudiantes_afectados,
            MIN(nombre_ie_original) as nombre_ie_ejemplo
        FROM resultados_academicos 
        WHERE codigo_modular IS NULL
        GROUP BY codigo_local 
        ORDER BY estudiantes_afectados DESC
        LIMIT 20
    ''', conn)
    
    equivalencias_encontradas = []
    
    for i, row in codigos_restantes.iterrows():
        print(f"\n{i+1:2}/20. Código crítico restante: {row['codigo_local']}")
        print(f"      Estudiantes afectados: {row['estudiantes_afectados']}")
        
        match = buscar_codigo_en_bd(conn, row['codigo_local'], row['nombre_ie_ejemplo'])
        
        if match is not None:
            equivalencias_encontradas.append({
                'codigo_local': row['codigo_local'],
                'codigo_modular': match['codigo_modular'],
                'nombre_ie_encontrado': match['nombre_institucion'],
                'metodo_encontrado': f'busqueda_restante_{match["metodo"]}'
            })
    
    print(f'\n{"="*60}')
    print(f'RESUMEN DE BÚSQUEDA RESTANTE:')
    print(f'{"="*60}')
    print(f'Códigos buscados: {len(codigos_restantes)}')
    print(f'Equivalencias encontradas: {len(equivalencias_encontradas)}')
    
    # Insertar nuevas equivalencias en tabla mapeo_codigos_ie
    if equivalencias_encontradas:
        print(f'\nInsertando {len(equivalencias_encontradas)} nuevas equivalencias...')
        
        for equiv in equivalencias_encontradas:
            conn.execute('''
                INSERT OR REPLACE INTO mapeo_codigos_ie 
                (codigo_local, nivel_educativo, codigo_modular, nombre_ie_encontrado, metodo_encontrado)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                equiv['codigo_local'],
                'Todos',
                equiv['codigo_modular'],
                equiv['nombre_ie_encontrado'],
                equiv['metodo_encontrado']
            ))
        
        conn.commit()
        print(f'{len(equivalencias_encontradas)} equivalencias adicionales insertadas')
        
        # Total equivalencias ahora
        total_equiv = pd.read_sql_query('SELECT COUNT(*) as count FROM mapeo_codigos_ie', conn).iloc[0,0]
        print(f'Total equivalencias ahora: {total_equiv}')
        
        # Mostrar equivalencias encontradas
        print(f'\nEQUIVALENCIAS RESTANTES ENCONTRADAS:')
        for i, equiv in enumerate(equivalencias_encontradas, 1):
            print(f"{i:2}. {equiv['codigo_local']} -> {equiv['codigo_modular']} ({equiv['nombre_ie_encontrado']})")
    
    conn.close()
    
    return len(equivalencias_encontradas)

if __name__ == "__main__":
    encontradas = buscar_codigos_restantes()