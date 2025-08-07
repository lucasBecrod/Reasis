#!/usr/bin/env python3
"""
Cargar tabla base de equivalencias desde Excel
"""

import pandas as pd
import sqlite3
from pathlib import Path

def cargar_tabla_base():
    print('PASO 2: PROCESAR Y CARGAR TABLA DE EQUIVALENCIAS BASE')
    print('=' * 60)

    # Cargar tabla de equivalencias original
    excel_path = Path('assets/Consultoria/Información actualizada/1. Ruralidad, EIB y TOE.xlsx')
    df_equiv = pd.read_excel(excel_path, sheet_name='Escuelas confirmadas FyA a Juli')

    # Limpiar y procesar - usar índices para evitar problemas con caracteres especiales
    df_clean = df_equiv.iloc[:, [4, 7, 8]].copy()  # Cols: Institución, Código Local, cod_mod
    df_clean.columns = ['institucion', 'codigo_local', 'cod_mod']
    df_clean = df_clean.dropna(subset=['codigo_local', 'cod_mod'])  # Solo registros completos

    # Convertir tipos
    df_clean['codigo_local'] = df_clean['codigo_local'].astype(str).str.strip()
    df_clean['cod_mod'] = df_clean['cod_mod'].astype(str).str.strip()

    # Eliminar registros con valores inválidos
    df_clean = df_clean[df_clean['codigo_local'] != 'nan']
    df_clean = df_clean[df_clean['cod_mod'] != 'nan']

    print(f'Registros originales: {len(df_equiv)}')
    print(f'Registros limpios: {len(df_clean)}')

    # Conectar a BD
    conn = sqlite3.connect('reasis_database.db')

    # Limpiar tabla anterior
    conn.execute('DELETE FROM mapeo_codigos_ie')

    # Insertar equivalencias base
    registros_insertados = 0
    for _, row in df_clean.iterrows():
        conn.execute('''
            INSERT OR REPLACE INTO mapeo_codigos_ie 
            (codigo_local, nivel_educativo, codigo_modular, nombre_ie_encontrado, metodo_encontrado)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            row['codigo_local'],
            'Todos',
            row['cod_mod'],
            row['institucion'],
            'tabla_equivalencias_excel'
        ))
        registros_insertados += 1

    conn.commit()

    total_mapeos = pd.read_sql_query('SELECT COUNT(*) as count FROM mapeo_codigos_ie', conn).iloc[0,0]
    print(f'Registros insertados: {registros_insertados}')
    print(f'Total en tabla: {total_mapeos}')

    conn.close()
    print('\nTABLA BASE DE EQUIVALENCIAS CARGADA EXITOSAMENTE')
    return registros_insertados

if __name__ == "__main__":
    cargar_tabla_base()