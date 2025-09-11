#!/usr/bin/env python3
"""
Script para explorar datos SIAGIE y buscar instituciones Fe y Alegría
"""

import sqlite3
from dbfread import DBF
import os
import pandas as pd

def buscar_fya_en_siagie():
    print("=== ANÁLISIS DATOS SIAGIE FE Y ALEGRÍA ===\n")
    
    # 1. Obtener códigos Fe y Alegría
    conn = sqlite3.connect('reasis_database.db')
    cursor = conn.execute('''
        SELECT codigo_modular, nombre_institucion, numero_fya 
        FROM instituciones_educativas 
        WHERE codigo_modular IS NOT NULL AND codigo_modular != ''
        ORDER BY numero_fya
        LIMIT 50
    ''')
    
    codigos_fya = {}
    for row in cursor.fetchall():
        codigos_fya[str(row[0]).strip()] = (row[1], row[2])
    conn.close()
    
    print(f"Instituciones Fe y Alegría disponibles: {len(codigos_fya)}")
    print("Muestra de códigos:")
    for i, (cod, (nombre, red)) in enumerate(list(codigos_fya.items())[:3]):
        print(f"  {cod}: {nombre[:40]}... (Red {red})")
    
    # 2. Buscar en SIAGIE 2024
    siagie_file = 'data/bases_de_datos/siagie/SIAGIE Reporte Matricula 2024.dbf'
    print(f"\n=== BÚSQUEDA EN {siagie_file} ===")
    
    encontrados = []
    registros_revisados = 0
    
    try:
        with DBF(siagie_file, encoding='latin1') as table:
            for record in table:
                registros_revisados += 1
                
                cod_mod = str(record.get('COD_MOD', '')).strip()
                if cod_mod in codigos_fya:
                    alumnos = record.get('TALUMNOS', 0)
                    try:
                        alumnos = int(alumnos)
                    except:
                        alumnos = 0
                    
                    encontrados.append({
                        'codigo': cod_mod,
                        'nombre_siagie': record.get('NOMBRE_IIE', ''),
                        'nivel': record.get('NIVEL', ''),
                        'grado': record.get('GRADO', ''),
                        'alumnos': alumnos,
                        'departamento': record.get('DPTO', ''),
                        'provincia': record.get('PROV', ''),
                        'distrito': record.get('DIST', ''),
                        'gestion': record.get('GESTION', ''),
                        'turno': record.get('TURNO', '')
                    })
                
                # Parar en muestra representativa
                if registros_revisados >= 200000:
                    break
    
    except Exception as e:
        print(f"Error leyendo SIAGIE: {e}")
        return
    
    print(f"Registros SIAGIE revisados: {registros_revisados:,}")
    print(f"Instituciones Fe y Alegría encontradas: {len(encontrados)}")
    
    if encontrados:
        # Estadísticas básicas
        total_alumnos = sum(item['alumnos'] for item in encontrados)
        print(f"\nTotal alumnos encontrados: {total_alumnos:,}")
        
        # Agrupación por nivel
        df = pd.DataFrame(encontrados)
        print("\n=== DISTRIBUCIÓN POR NIVEL ===")
        nivel_stats = df.groupby('nivel')['alumnos'].agg(['count', 'sum']).reset_index()
        for _, row in nivel_stats.iterrows():
            print(f"{row['nivel']}: {row['count']} registros, {int(row['sum'])} alumnos")
        
        # Agrupación por departamento
        print("\n=== DISTRIBUCIÓN POR DEPARTAMENTO ===")
        dept_stats = df.groupby('departamento')['alumnos'].agg(['count', 'sum']).reset_index()
        for _, row in dept_stats.iterrows():
            print(f"{row['departamento']}: {row['count']} registros, {int(row['sum'])} alumnos")
        
        # Muestra de registros
        print("\n=== MUESTRA DE REGISTROS ENCONTRADOS ===")
        for item in encontrados[:5]:
            print(f"\nCódigo: {item['codigo']}")
            print(f"  Nombre: {item['nombre_siagie'][:50]}")
            print(f"  Nivel: {item['nivel']}")
            print(f"  Alumnos: {item['alumnos']}")
            print(f"  Ubicación: {item['departamento']}, {item['provincia']}, {item['distrito']}")
    
    else:
        print("No se encontraron instituciones Fe y Alegría en la muestra revisada")

if __name__ == "__main__":
    buscar_fya_en_siagie()