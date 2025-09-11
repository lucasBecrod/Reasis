#!/usr/bin/env python3
"""
Procesar todos los años SIAGIE uno por uno para evitar problemas de memoria
"""

import sqlite3
from dbfread import DBF
import pandas as pd
import os
from datetime import datetime
import gc

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
    return dict_mod, dict_local

def procesar_año(año, dict_mod, dict_local):
    """Procesar un año específico"""
    archivo = f'data/bases_de_datos/siagie/SIAGIE Reporte Matricula {año}.dbf'
    
    if not os.path.exists(archivo):
        print(f"[OMITIDO] Archivo no encontrado para año {año}: {archivo}")
        return None
    
    print(f"\n=== PROCESANDO AÑO {año} ===")
    
    archivo_salida = f"data/siagie_procesado/siagie_fya_{año}_completo.csv"
    
    registros_encontrados = []
    total_procesados = 0
    total_encontrados = 0
    
    print(f"Procesando: {archivo}")
    
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
        print(f"[ERROR] Error procesando año {año}: {e}")
        return None
    
    # Guardar resultados
    if registros_encontrados:
        df = pd.DataFrame(registros_encontrados)
        df.to_csv(archivo_salida, index=False, encoding='utf-8')
        
        # Estadísticas
        instituciones_unicas = df['CODIGOMODU'].nunique()
        
        # Calcular total alumnos con manejo de errores
        try:
            if 'TOTAL' in df.columns:
                # Convertir a numérico manejando errores
                df['TOTAL_NUM'] = pd.to_numeric(df['TOTAL'], errors='coerce')
                total_alumnos = int(df['TOTAL_NUM'].sum())
            else:
                total_alumnos = 0
        except:
            total_alumnos = 0
        
        print(f"\n[COMPLETADO] Año {año}:")
        print(f"   Registros procesados: {total_procesados:,}")
        print(f"   Registros FyA encontrados: {total_encontrados:,}")
        print(f"   Instituciones únicas: {instituciones_unicas}")
        print(f"   Total alumnos: {total_alumnos:,}")
        print(f"   Archivo: {archivo_salida}")
        
        # Distribución por red
        if 'RED_FYA' in df.columns:
            print(f"   Distribución por red:")
            dist_red = df.groupby('RED_FYA').size().sort_values(ascending=False)
            for red, cantidad in dist_red.items():
                print(f"     Red {red}: {cantidad} registros")
        
        # Limpiar memoria
        del df
        del registros_encontrados
        gc.collect()
        
        return {
            'año': año,
            'registros_procesados': total_procesados,
            'registros_encontrados': total_encontrados,
            'instituciones_unicas': instituciones_unicas,
            'total_alumnos': total_alumnos,
            'archivo': archivo_salida
        }
    
    else:
        print(f"[INFO] No se encontraron registros Fe y Alegría para año {año}")
        return None

def main():
    """Procesar todos los años disponibles"""
    años = [2019, 2020, 2021, 2022, 2023, 2024]
    
    print("=" * 60)
    print("PROCESADOR SIAGIE - TODOS LOS AÑOS")
    print("=" * 60)
    
    # Crear directorio de salida
    os.makedirs("data/siagie_procesado", exist_ok=True)
    
    # Cargar instituciones FyA una sola vez
    print("Cargando instituciones Fe y Alegría...")
    dict_mod, dict_local = cargar_instituciones_fya()
    print(f"Cargadas {len(dict_mod)} instituciones con código modular")
    print(f"Cargadas {len(dict_local)} instituciones con código local")
    
    resultados = []
    
    for año in años:
        resultado = procesar_año(año, dict_mod, dict_local)
        if resultado:
            resultados.append(resultado)
        
        # Forzar limpieza de memoria entre años
        gc.collect()
    
    # Resumen final
    print("\n" + "=" * 60)
    print("RESUMEN FINAL - PROCESAMIENTO COMPLETO")
    print("=" * 60)
    
    if resultados:
        total_registros_procesados = sum(r['registros_procesados'] for r in resultados)
        total_registros_encontrados = sum(r['registros_encontrados'] for r in resultados)
        total_alumnos_todos = sum(r['total_alumnos'] for r in resultados)
        
        print(f"Años procesados exitosamente: {len(resultados)}")
        print(f"Total registros procesados: {total_registros_procesados:,}")
        print(f"Total registros Fe y Alegría: {total_registros_encontrados:,}")
        print(f"Total alumnos (todos los años): {total_alumnos_todos:,}")
        
        print(f"\nDetalle por año:")
        for resultado in resultados:
            print(f"  {resultado['año']}: {resultado['registros_encontrados']:,} registros FyA, {resultado['total_alumnos']:,} alumnos")
    
    else:
        print("No se pudieron procesar datos de ningún año")

if __name__ == "__main__":
    main()