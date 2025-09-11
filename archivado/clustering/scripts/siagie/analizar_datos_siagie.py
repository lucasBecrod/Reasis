#!/usr/bin/env python3
"""
Script para analizar datos SIAGIE con búsqueda por código modular y código local
"""

import sqlite3
from dbfread import DBF
import pandas as pd

def analizar_estructura_siagie():
    """Analiza la estructura de archivos SIAGIE"""
    print("=== ANÁLISIS ESTRUCTURA SIAGIE 2024 ===\n")
    
    siagie_file = 'data/bases_de_datos/siagie/SIAGIE Reporte Matricula 2024.dbf'
    
    with DBF(siagie_file, encoding='latin1') as table:
        # Tomar muestra
        sample_records = []
        for i, record in enumerate(table):
            if i >= 1000:
                break
            sample_records.append(dict(record))
    
    df = pd.DataFrame(sample_records)
    print(f"Columnas disponibles: {list(df.columns)}")
    print(f"Total registros en muestra: {len(df)}")
    
    # Analizar códigos modulares
    print("\n=== CÓDIGOS MODULARES (CODIGOMODU) ===")
    df['cod_mod_str'] = df['CODIGOMODU'].astype(str).str.strip()
    valid_cod_mod = df[df['cod_mod_str'].str.len() >= 6]
    print(f"Registros con CODIGOMODU válido: {len(valid_cod_mod)}")
    
    if len(valid_cod_mod) > 0:
        print("Primeros CODIGOMODU válidos:")
        for _, row in valid_cod_mod.head().iterrows():
            print(f"  {row['cod_mod_str']}: {str(row['NOMBRE_IE'])[:40]} - {row['TOTAL']} alumnos")
    
    # Analizar códigos locales
    print("\n=== CÓDIGOS LOCALES (CODIGOLOCA) ===")
    df['cod_local_str'] = df['CODIGOLOCA'].astype(str).str.strip()
    valid_cod_local = df[df['cod_local_str'].str.len() >= 4]
    print(f"Registros con CODIGOLOCA válido: {len(valid_cod_local)}")
    
    if len(valid_cod_local) > 0:
        print("Primeros CODIGOLOCA válidos:")
        for _, row in valid_cod_local.head().iterrows():
            print(f"  {row['cod_local_str']}: {str(row['NOMBRE_IE'])[:40]} - {row['TOTAL']} alumnos")
    
    return df

def buscar_fya_doble_estrategia():
    """Busca Fe y Alegría usando código modular y código local"""
    print("\n=== BÚSQUEDA FE Y ALEGRÍA - DOBLE ESTRATEGIA ===\n")
    
    # Obtener códigos de nuestra BD
    conn = sqlite3.connect('reasis_database.db')
    
    # Obtener códigos modulares y locales
    cursor = conn.execute('''
        SELECT codigo_modular, codigo_local, nombre_institucion, numero_fya
        FROM instituciones_educativas 
        WHERE codigo_modular IS NOT NULL AND codigo_modular != ''
        LIMIT 20
    ''')
    
    instituciones_fya = []
    for row in cursor.fetchall():
        instituciones_fya.append({
            'codigo_modular': str(row[0]).strip(),
            'codigo_local': str(row[1]).strip() if row[1] else '',
            'nombre': row[2],
            'red': row[3]
        })
    
    conn.close()
    
    print(f"Instituciones Fe y Alegría para buscar: {len(instituciones_fya)}")
    
    # Crear diccionarios de búsqueda
    dict_cod_mod = {inst['codigo_modular']: inst for inst in instituciones_fya}
    dict_cod_local = {inst['codigo_local']: inst for inst in instituciones_fya if inst['codigo_local']}
    
    print(f"Códigos modulares: {len(dict_cod_mod)}")
    print(f"Códigos locales: {len(dict_cod_local)}")
    
    # Buscar en SIAGIE
    siagie_file = 'data/bases_de_datos/siagie/SIAGIE Reporte Matricula 2024.dbf'
    encontrados = []
    registros_procesados = 0
    
    with DBF(siagie_file, encoding='latin1') as table:
        for record in table:
            registros_procesados += 1
            
            cod_mod = str(record.get('CODIGOMODU', '')).strip()
            cod_local = str(record.get('CODIGOLOCA', '')).strip()
            
            institucion_encontrada = None
            metodo = ""
            
            # ESTRATEGIA 1: Buscar por código modular
            if cod_mod in dict_cod_mod:
                institucion_encontrada = dict_cod_mod[cod_mod]
                metodo = "CODIGO_MODULAR"
            
            # ESTRATEGIA 2: Si no encontró, buscar por código local
            elif cod_local in dict_cod_local:
                institucion_encontrada = dict_cod_local[cod_local]
                metodo = "CODIGO_LOCAL"
            
            if institucion_encontrada:
                alumnos = record.get('TOTAL', 0)
                try:
                    alumnos = int(alumnos)
                except:
                    alumnos = 0
                
                encontrados.append({
                    'codigo_modular': cod_mod,
                    'codigo_local': cod_local,
                    'metodo_encontrado': metodo,
                    'nombre_siagie': record.get('NOMBRE_IE', ''),
                    'nombre_fya': institucion_encontrada['nombre'],
                    'red_fya': institucion_encontrada['red'],
                    'nivel': record.get('DSC_NIVEL', ''),
                    'grado': record.get('DSC_GRADO', ''),
                    'alumnos': alumnos,
                    'departamento': record.get('DEPARTAMEN', ''),
                    'provincia': record.get('PROVINCIA', ''),
                    'distrito': record.get('DISTRITO', ''),
                    'turno': record.get('TURNO', '')
                })
            
            # Límite de búsqueda
            if registros_procesados >= 300000:
                break
    
    print(f"\nRegistros SIAGIE procesados: {registros_procesados:,}")
    print(f"Instituciones Fe y Alegría encontradas: {len(encontrados)}")
    
    if encontrados:
        print("\n=== RESULTADOS ENCONTRADOS ===")
        
        # Estadísticas por método
        df_encontrados = pd.DataFrame(encontrados)
        print("\nMétodo de vinculación:")
        print(df_encontrados['metodo_encontrado'].value_counts())
        
        # Estadísticas de matrícula
        total_alumnos = df_encontrados['alumnos'].sum()
        print(f"\nTotal alumnos matriculados: {total_alumnos:,}")
        
        # Por nivel educativo
        print("\nDistribución por nivel:")
        nivel_stats = df_encontrados.groupby('nivel')['alumnos'].agg(['count', 'sum'])
        for nivel, stats in nivel_stats.iterrows():
            print(f"  {nivel}: {stats['count']} registros, {int(stats['sum'])} alumnos")
        
        # Por departamento
        print("\nDistribución por departamento:")
        dept_stats = df_encontrados.groupby('departamento')['alumnos'].agg(['count', 'sum'])
        for dept, stats in dept_stats.iterrows():
            print(f"  {dept}: {stats['count']} registros, {int(stats['sum'])} alumnos")
        
        # Muestra de registros
        print("\n=== MUESTRA DE INSTITUCIONES ENCONTRADAS ===")
        for i, row in df_encontrados.head(5).iterrows():
            print(f"\n{i+1}. Código: {row['codigo_modular']} (Método: {row['metodo_encontrado']})")
            print(f"   SIAGIE: {row['nombre_siagie'][:50]}...")
            print(f"   Fe y Alegría: {row['nombre_fya'][:50]}... (Red {row['red_fya']})")
            print(f"   Nivel: {row['nivel']} - {row['alumnos']} alumnos")
            print(f"   Ubicación: {row['departamento']}, {row['provincia']}")
        
        # Guardar resultados
        df_encontrados.to_csv('resultados_siagie_fya_2024.csv', index=False, encoding='utf-8')
        print(f"\nResultados guardados en: resultados_siagie_fya_2024.csv")
        
        return encontrados
    
    else:
        print("No se encontraron instituciones Fe y Alegría en SIAGIE")
        return []

if __name__ == "__main__":
    # Primero analizar estructura
    df_muestra = analizar_estructura_siagie()
    
    # Luego buscar Fe y Alegría
    resultados = buscar_fya_doble_estrategia()