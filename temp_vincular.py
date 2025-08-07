#!/usr/bin/env python3
"""
Aplicar vinculación inicial con tabla base
"""

import sqlite3
import pandas as pd

def aplicar_vinculacion_inicial():
    print('PASO 3: APLICAR VINCULACIÓN INICIAL CON TABLA BASE')
    print('=' * 60)

    conn = sqlite3.connect('reasis_database.db')

    # Verificar tabla de equivalencias
    equivalencias = pd.read_sql_query('''
        SELECT COUNT(*) as total
        FROM mapeo_codigos_ie
    ''', conn)
    
    validas = pd.read_sql_query('''
        SELECT COUNT(*) as count
        FROM mapeo_codigos_ie
        WHERE codigo_modular IS NOT NULL AND codigo_modular != 'nan'
    ''', conn)

    print(f'Equivalencias totales: {equivalencias.iloc[0]["total"]}')
    print(f'Equivalencias válidas: {validas.iloc[0]["count"]}')

    # Aplicar vinculación a resultados_academicos
    print('\nAplicando vinculación...')

    # Limpiar vinculaciones anteriores
    conn.execute('UPDATE resultados_academicos SET codigo_modular = NULL, metodo_vinculacion = NULL')

    # Aplicar vinculación usando tabla de equivalencias
    updated = conn.execute('''
        UPDATE resultados_academicos 
        SET codigo_modular = (
            SELECT codigo_modular 
            FROM mapeo_codigos_ie 
            WHERE mapeo_codigos_ie.codigo_local = resultados_academicos.codigo_local
            AND mapeo_codigos_ie.codigo_modular IS NOT NULL
            AND mapeo_codigos_ie.codigo_modular != 'nan'
            LIMIT 1
        ),
        metodo_vinculacion = (
            SELECT metodo_encontrado
            FROM mapeo_codigos_ie 
            WHERE mapeo_codigos_ie.codigo_local = resultados_academicos.codigo_local
            AND mapeo_codigos_ie.codigo_modular IS NOT NULL
            AND mapeo_codigos_ie.codigo_modular != 'nan'
            LIMIT 1
        )
        WHERE codigo_local IN (
            SELECT codigo_local FROM mapeo_codigos_ie 
            WHERE codigo_modular IS NOT NULL AND codigo_modular != 'nan'
        )
    ''').rowcount

    conn.commit()

    print(f'Registros actualizados: {updated:,}')

    # Verificar resultado
    total = pd.read_sql_query('SELECT COUNT(*) as count FROM resultados_academicos', conn).iloc[0,0]
    vinculados = pd.read_sql_query('SELECT COUNT(*) as count FROM resultados_academicos WHERE codigo_modular IS NOT NULL', conn).iloc[0,0]
    sin_vincular = total - vinculados
    porcentaje = (vinculados / total * 100) if total > 0 else 0

    print(f'\nRESULTADOS DE VINCULACIÓN INICIAL:')
    print(f'Total registros: {total:,}')
    print(f'Vinculados: {vinculados:,}')
    print(f'Sin vincular: {sin_vincular:,}')
    print(f'Porcentaje éxito: {porcentaje:.1f}%')

    # Contar instituciones con ILA
    instituciones_ila = pd.read_sql_query('''
        SELECT COUNT(DISTINCT codigo_modular) as count 
        FROM resultados_academicos 
        WHERE codigo_modular IS NOT NULL
    ''', conn).iloc[0,0]

    print(f'Instituciones con ILA: {instituciones_ila}')

    conn.close()

    print(f'\nVINCULACIÓN INICIAL COMPLETADA: {porcentaje:.1f}% éxito')
    return porcentaje

if __name__ == "__main__":
    aplicar_vinculacion_inicial()