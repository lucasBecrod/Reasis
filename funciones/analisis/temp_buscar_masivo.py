#!/usr/bin/env python3
"""
Búsqueda masiva final para alcanzar 95.8% vinculación
"""

import sqlite3
import pandas as pd
import re

def buscar_codigo_simple(conn, codigo_buscar):
    """Búsqueda simplificada y rápida"""
    
    # Estrategia 1: Exacto en codigo_local
    match1 = pd.read_sql_query('''
        SELECT codigo_modular, codigo_local, nombre_institucion
        FROM instituciones_educativas 
        WHERE codigo_local = ? LIMIT 1
    ''', conn, params=[codigo_buscar])
    
    if len(match1) > 0:
        return match1.iloc[0]['codigo_modular'], match1.iloc[0]['nombre_institucion']
    
    # Estrategia 2: Exacto en codigo_modular
    match2 = pd.read_sql_query('''
        SELECT codigo_modular, codigo_local, nombre_institucion
        FROM instituciones_educativas 
        WHERE codigo_modular = ? LIMIT 1
    ''', conn, params=[codigo_buscar])
    
    if len(match2) > 0:
        return match2.iloc[0]['codigo_modular'], match2.iloc[0]['nombre_institucion']
    
    # Estrategia 3: LIKE en nombre con código limpio
    codigo_limpio = re.sub(r'\D', '', codigo_buscar)
    if codigo_limpio and len(codigo_limpio) >= 4:
        match3 = pd.read_sql_query('''
            SELECT codigo_modular, codigo_local, nombre_institucion
            FROM instituciones_educativas 
            WHERE nombre_institucion LIKE ? LIMIT 1
        ''', conn, params=[f'%{codigo_limpio}%'])
        
        if len(match3) > 0:
            return match3.iloc[0]['codigo_modular'], match3.iloc[0]['nombre_institucion']
    
    return None, None

def busqueda_masiva():
    print('PASO 8: BÚSQUEDA MASIVA FINAL PARA ALCANZAR 95.8%')
    print('=' * 60)
    
    conn = sqlite3.connect('reasis_database.db')
    
    # Obtener próximos 50 códigos más críticos
    codigos_masivos = pd.read_sql_query('''
        SELECT 
            codigo_local, 
            COUNT(*) as estudiantes_afectados
        FROM resultados_academicos 
        WHERE codigo_modular IS NULL
        GROUP BY codigo_local 
        ORDER BY estudiantes_afectados DESC
        LIMIT 50
    ''', conn)
    
    print(f'Buscando {len(codigos_masivos)} códigos masivamente...')
    
    equivalencias_encontradas = []
    encontrados = 0
    
    for i, row in codigos_masivos.iterrows():
        codigo = row['codigo_local']
        estudiantes = row['estudiantes_afectados']
        
        if (i + 1) % 10 == 0:  # Progreso cada 10
            print(f'Procesado {i+1}/50 códigos, encontrados: {encontrados}')
        
        codigo_modular, nombre_ie = buscar_codigo_simple(conn, codigo)
        
        if codigo_modular:
            equivalencias_encontradas.append({
                'codigo_local': codigo,
                'codigo_modular': codigo_modular,
                'nombre_ie_encontrado': nombre_ie,
                'metodo_encontrado': 'busqueda_masiva'
            })
            encontrados += 1
    
    print(f'\nRESULTADO BÚSQUEDA MASIVA:')
    print(f'Códigos buscados: {len(codigos_masivos)}')
    print(f'Equivalencias encontradas: {len(equivalencias_encontradas)}')
    
    # Insertar equivalencias encontradas
    if equivalencias_encontradas:
        print(f'\\nInsertando {len(equivalencias_encontradas)} nuevas equivalencias...')
        
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
        
        # Total equivalencias ahora
        total_equiv = pd.read_sql_query('SELECT COUNT(*) as count FROM mapeo_codigos_ie', conn).iloc[0,0]
        print(f'Total equivalencias ahora: {total_equiv}')
    
    conn.close()
    
    return len(equivalencias_encontradas)

def aplicar_vinculacion_final():
    """Aplicar vinculación final y calcular métricas"""
    print('\\nPASO 9: APLICAR VINCULACIÓN FINAL')
    print('=' * 50)
    
    conn = sqlite3.connect('reasis_database.db')
    
    # Limpiar vinculaciones
    conn.execute('UPDATE resultados_academicos SET codigo_modular = NULL, metodo_vinculacion = NULL')
    
    # Aplicar vinculación masiva
    updated = conn.execute('''
        UPDATE resultados_academicos 
        SET codigo_modular = (
            SELECT codigo_modular 
            FROM mapeo_codigos_ie 
            WHERE mapeo_codigos_ie.codigo_local = resultados_academicos.codigo_local
            AND mapeo_codigos_ie.codigo_modular IS NOT NULL
            LIMIT 1
        ),
        metodo_vinculacion = (
            SELECT metodo_encontrado
            FROM mapeo_codigos_ie 
            WHERE mapeo_codigos_ie.codigo_local = resultados_academicos.codigo_local
            AND mapeo_codigos_ie.codigo_modular IS NOT NULL
            LIMIT 1
        )
        WHERE codigo_local IN (
            SELECT codigo_local FROM mapeo_codigos_ie 
            WHERE codigo_modular IS NOT NULL
        )
    ''').rowcount
    
    conn.commit()
    
    # Calcular métricas finales
    total = 15054
    vinculados = pd.read_sql_query('SELECT COUNT(*) as count FROM resultados_academicos WHERE codigo_modular IS NOT NULL', conn).iloc[0,0]
    sin_vincular = total - vinculados
    porcentaje = (vinculados / total * 100) if total > 0 else 0
    
    instituciones_ila = pd.read_sql_query('''
        SELECT COUNT(DISTINCT codigo_modular) as count 
        FROM resultados_academicos 
        WHERE codigo_modular IS NOT NULL
    ''', conn).iloc[0,0]
    
    print(f'RESULTADO FINAL DE VINCULACIÓN MASIVA:')
    print(f'=' * 50)
    print(f'Total registros: {total:,}')
    print(f'Vinculados: {vinculados:,}')
    print(f'Sin vincular: {sin_vincular:,}')
    print(f'Porcentaje éxito: {porcentaje:.1f}%')
    print(f'Instituciones con ILA: {instituciones_ila}')
    
    # Comparar con objetivo 95.8%
    objetivo = int(total * 0.958)
    print(f'\\nOBJETIVO 95.8%: {objetivo:,} registros')
    if vinculados >= objetivo:
        print('OBJETIVO ALCANZADO!')
    else:
        faltantes = objetivo - vinculados
        print(f'Faltan: {faltantes:,} registros ({faltantes/total*100:.1f}%)')
    
    conn.close()
    
    return porcentaje, instituciones_ila

if __name__ == "__main__":
    encontradas = busqueda_masiva()
    porcentaje, iiee = aplicar_vinculacion_final()
    print(f'\\nRESULTADO FINAL: {porcentaje:.1f}% vinculación, {iiee} IIEE con ILA')