#!/usr/bin/env python3
"""
Procesador simple para SIAGIE 2024
"""

import sqlite3
from dbfread import DBF
import pandas as pd
import os
from datetime import datetime

def cargar_instituciones_fya():
    """Cargar todas las instituciones Fe y Alegría"""
    conn = sqlite3.connect('reasis_database.db')
    cursor = conn.execute('''
        SELECT codigo_modular, codigo_local, nombre_institucion, numero_fya,
               departamento, provincia, distrito
        FROM instituciones_educativas 
        WHERE codigo_modular IS NOT NULL AND codigo_modular != ''
        ORDER BY numero_fya
    ''')
    
    dict_mod = {}
    dict_local = {}
    
    for row in cursor.fetchall():
        cod_mod = str(row[0]).strip()
        cod_local = str(row[1]).strip() if row[1] else ''
        
        data = {
            'nombre': row[2],
            'red': row[3],
            'departamento': row[4],
            'provincia': row[5],
            'distrito': row[6]
        }
        
        dict_mod[cod_mod] = data
        if cod_local:
            dict_local[cod_local] = data
    
    conn.close()
    print(f"Cargadas {len(dict_mod)} instituciones con código modular")
    print(f"Cargadas {len(dict_local)} instituciones con código local")
    return dict_mod, dict_local

def procesar_siagie_2024():
    """Procesar archivo SIAGIE 2024"""
    archivo = 'data/bases_de_datos/siagie/SIAGIE Reporte Matricula 2024.dbf'
    
    if not os.path.exists(archivo):
        print(f"Archivo no encontrado: {archivo}")
        return
    
    print("=== PROCESADOR SIAGIE 2024 SIMPLE ===")
    
    # Crear directorio de salida
    os.makedirs("data/siagie_procesado", exist_ok=True)
    
    # Cargar instituciones FyA
    dict_mod, dict_local = cargar_instituciones_fya()
    
    archivo_salida = "data/siagie_procesado/siagie_fya_2024_completo.csv"
    
    registros_encontrados = []
    total_procesados = 0
    total_encontrados = 0
    
    print(f"Procesando archivo: {archivo}")
    
    try:
        with DBF(archivo, encoding='latin1') as table:
            for record in table:
                total_procesados += 1
                
                # Obtener códigos
                cod_mod = str(record.get('CODIGOMODU', '')).strip()
                cod_local = str(record.get('CODLOCALU', '')).strip()
                
                encontrado = False
                metodo = ''
                data_inst = None
                
                # Buscar por código modular
                if cod_mod in dict_mod:
                    encontrado = True
                    metodo = 'CODIGO_MODULAR'
                    data_inst = dict_mod[cod_mod]
                
                # Si no encontrado, buscar por código local
                elif cod_local in dict_local:
                    encontrado = True
                    metodo = 'CODIGO_LOCAL'
                    data_inst = dict_local[cod_local]
                
                if encontrado:
                    # Crear registro completo
                    registro_completo = dict(record)
                    registro_completo['METODO_VINCULACION'] = metodo
                    registro_completo['NOMBRE_FYA'] = data_inst['nombre']
                    registro_completo['RED_FYA'] = data_inst['red']
                    registro_completo['DEPTO_BD'] = data_inst['departamento']
                    registro_completo['PROV_BD'] = data_inst['provincia']
                    registro_completo['DIST_BD'] = data_inst['distrito']
                    registro_completo['FECHA_PROCESO'] = datetime.now().isoformat()
                    
                    registros_encontrados.append(registro_completo)
                    total_encontrados += 1
                
                # Progress cada 100k registros
                if total_procesados % 100000 == 0:
                    print(f"  Procesados: {total_procesados:,}, Encontrados: {total_encontrados}")
    
    except Exception as e:
        print(f"Error procesando: {e}")
        return
    
    # Guardar resultados
    if registros_encontrados:
        df = pd.DataFrame(registros_encontrados)
        df.to_csv(archivo_salida, index=False, encoding='utf-8')
        
        # Estadísticas
        instituciones_unicas = df['CODIGOMODU'].nunique()
        total_alumnos = df['TOTAL'].sum() if 'TOTAL' in df.columns else 0
        
        print(f"\n=== RESULTADOS FINALES ===")
        print(f"Registros procesados: {total_procesados:,}")
        print(f"Registros Fe y Alegría encontrados: {total_encontrados:,}")
        print(f"Instituciones únicas: {instituciones_unicas}")
        print(f"Total alumnos: {int(total_alumnos):,}")
        print(f"Archivo guardado: {archivo_salida}")
        
        # Mostrar distribución por red
        if 'RED_FYA' in df.columns:
            print(f"\nDistribución por red:")
            dist_red = df.groupby('RED_FYA').size().sort_values(ascending=False)
            for red, cantidad in dist_red.items():
                print(f"  Red {red}: {cantidad} registros")
    
    else:
        print("No se encontraron registros de Fe y Alegría")

if __name__ == "__main__":
    procesar_siagie_2024()