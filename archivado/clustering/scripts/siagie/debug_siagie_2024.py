#!/usr/bin/env python3
"""
Debug SIAGIE 2024 - Revisar por qué no encontramos instituciones FyA
"""

import sqlite3
from dbfread import DBF
import os

def cargar_codigos_fya():
    """Cargar códigos FyA de la BD"""
    conn = sqlite3.connect('reasis_database.db')
    cursor = conn.execute('''
        SELECT codigo_modular, codigo_local, nombre_institucion, numero_fya
        FROM instituciones_educativas 
        WHERE codigo_modular IS NOT NULL AND codigo_modular != ''
        LIMIT 10
    ''')
    
    codigos = {}
    for row in cursor.fetchall():
        cod_mod = str(row[0]).strip()
        codigos[cod_mod] = {
            'codigo_local': str(row[1]).strip() if row[1] else '',
            'nombre': row[2],
            'red': row[3]
        }
    
    conn.close()
    return codigos

def debug_archivo_2024():
    """Revisar una muestra del archivo 2024"""
    archivo = 'data/bases_de_datos/siagie/SIAGIE Reporte Matricula 2024.dbf'
    
    if not os.path.exists(archivo):
        print(f"Archivo no encontrado: {archivo}")
        return
    
    print("=== DEBUG SIAGIE 2024 ===")
    
    # Cargar códigos FyA
    codigos_fya = cargar_codigos_fya()
    print(f"Códigos FyA cargados: {len(codigos_fya)}")
    print("Primeros 5 códigos:")
    for i, (cod, data) in enumerate(codigos_fya.items()):
        if i < 5:
            print(f"  {cod}: {data['nombre'][:50]}...")
    
    print(f"\nRevisando archivo: {archivo}")
    
    total_registros = 0
    encontrados = 0
    muestra_codigos = set()
    
    try:
        with DBF(archivo, encoding='latin1') as table:
            print("Columnas disponibles:")
            for i, field in enumerate(table.field_names):
                if i < 10:  # Mostrar primeras 10 columnas
                    print(f"  {field}")
            
            print(f"\nRevisando registros...")
            
            for i, record in enumerate(table):
                total_registros += 1
                
                # Obtener códigos del registro
                cod_mod = str(record.get('CODIGOMODU', '')).strip()
                cod_local = str(record.get('CODLOCALU', '')).strip()
                
                # Agregar a muestra de códigos
                if len(muestra_codigos) < 20:
                    muestra_codigos.add(cod_mod)
                
                # Revisar si coincide con FyA
                if cod_mod in codigos_fya:
                    encontrados += 1
                    if encontrados <= 5:  # Mostrar primeros 5 coincidencias
                        print(f"  ¡ENCONTRADO! {cod_mod}: {codigos_fya[cod_mod]['nombre'][:50]}...")
                
                # Revisar solo primeros 100k para debug
                if i >= 100000:
                    break
    
    except Exception as e:
        print(f"Error: {e}")
    
    print(f"\nResumen Debug:")
    print(f"  Registros revisados: {total_registros:,}")
    print(f"  FyA encontradas: {encontrados}")
    print(f"  \nMuestra de códigos SIAGIE 2024:")
    for i, cod in enumerate(muestra_codigos):
        if i < 10:
            print(f"    {cod}")

if __name__ == "__main__":
    debug_archivo_2024()