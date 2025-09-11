#!/usr/bin/env python3
"""
Script para analizar tendencias históricas SIAGIE (2019-2024) para Fe y Alegría
"""

import sqlite3
from dbfread import DBF
import pandas as pd
import os

def obtener_codigos_fya():
    """Obtiene códigos de instituciones Fe y Alegría"""
    conn = sqlite3.connect('reasis_database.db')
    
    cursor = conn.execute('''
        SELECT codigo_modular, codigo_local, nombre_institucion, numero_fya
        FROM instituciones_educativas 
        WHERE codigo_modular IS NOT NULL AND codigo_modular != ''
        LIMIT 50  -- Ampliamos a 50 para mejor cobertura
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
    return instituciones_fya

def analizar_año(año, instituciones_fya):
    """Analiza un año específico de SIAGIE"""
    siagie_file = f'data/bases_de_datos/siagie/SIAGIE Reporte Matricula {año}.dbf'
    
    if not os.path.exists(siagie_file):
        print(f"Archivo no encontrado: {siagie_file}")
        return []
    
    print(f"\n=== ANALIZANDO AÑO {año} ===")
    
    # Crear diccionarios de búsqueda
    dict_cod_mod = {inst['codigo_modular']: inst for inst in instituciones_fya}
    dict_cod_local = {inst['codigo_local']: inst for inst in instituciones_fya if inst['codigo_local']}
    
    encontrados = []
    registros_procesados = 0
    
    try:
        with DBF(siagie_file, encoding='latin1') as table:
            for record in table:
                registros_procesados += 1
                
                cod_mod = str(record.get('CODIGOMODU', '')).strip()
                cod_local = str(record.get('CODIGOLOCA', '')).strip()
                
                institucion_encontrada = None
                metodo = ""
                
                # Buscar por código modular primero
                if cod_mod in dict_cod_mod:
                    institucion_encontrada = dict_cod_mod[cod_mod]
                    metodo = "CODIGO_MODULAR"
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
                        'año': año,
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
                        'turno': record.get('TURNO', ''),
                        'gestion': record.get('GESTION', '')
                    })
                
                # Procesar hasta 400K registros por año
                if registros_procesados >= 400000:
                    break
    
    except Exception as e:
        print(f"Error procesando {año}: {e}")
        return []
    
    print(f"Registros procesados: {registros_procesados:,}")
    print(f"Instituciones Fe y Alegría encontradas: {len(encontrados)}")
    
    if encontrados:
        df = pd.DataFrame(encontrados)
        total_alumnos = df['alumnos'].sum()
        print(f"Total alumnos matriculados: {total_alumnos:,}")
        
        # Estadísticas por nivel
        print("Distribución por nivel:")
        nivel_stats = df.groupby('nivel')['alumnos'].agg(['count', 'sum'])
        for nivel, stats in nivel_stats.iterrows():
            print(f"  {nivel}: {stats['count']} registros, {int(stats['sum'])} alumnos")
    
    return encontrados

def generar_reporte_historico():
    """Genera reporte histórico completo"""
    print("=== ANÁLISIS HISTÓRICO SIAGIE FE Y ALEGRÍA (2019-2024) ===\n")
    
    # Obtener instituciones Fe y Alegría
    instituciones_fya = obtener_codigos_fya()
    print(f"Instituciones Fe y Alegría disponibles: {len(instituciones_fya)}")
    
    # Analizar cada año
    años = [2019, 2020, 2021, 2022, 2023, 2024]
    todos_resultados = []
    
    for año in años:
        resultados_año = analizar_año(año, instituciones_fya)
        todos_resultados.extend(resultados_año)
    
    if todos_resultados:
        print(f"\n=== RESUMEN GENERAL HISTÓRICO ===")
        df_historico = pd.DataFrame(todos_resultados)
        
        # Estadísticas generales
        print(f"Total registros encontrados (2019-2024): {len(df_historico):,}")
        print(f"Total alumnos acumulados: {df_historico['alumnos'].sum():,}")
        
        # Tendencia por año
        print("\n=== EVOLUCIÓN POR AÑO ===")
        tendencia = df_historico.groupby('año')['alumnos'].agg(['count', 'sum']).reset_index()
        for _, row in tendencia.iterrows():
            print(f"{int(row['año'])}: {int(row['count'])} registros, {int(row['sum']):,} alumnos matriculados")
        
        # Instituciones más representadas
        print("\n=== INSTITUCIONES CON MÁS DATOS HISTÓRICOS ===")
        inst_frecuentes = df_historico['nombre_fya'].value_counts().head(10)
        for nombre, freq in inst_frecuentes.items():
            print(f"{nombre[:50]}...: {freq} registros históricos")
        
        # Por red
        print("\n=== DISTRIBUCIÓN POR RED FE Y ALEGRÍA ===")
        red_stats = df_historico.groupby('red_fya')['alumnos'].agg(['count', 'sum']).reset_index()
        red_stats = red_stats.sort_values('sum', ascending=False)
        for _, row in red_stats.iterrows():
            print(f"Red {row['red_fya']}: {int(row['count'])} registros, {int(row['sum']):,} alumnos")
        
        # Por nivel educativo
        print("\n=== DISTRIBUCIÓN POR NIVEL EDUCATIVO (HISTÓRICO) ===")
        nivel_historico = df_historico.groupby('nivel')['alumnos'].agg(['count', 'sum']).reset_index()
        nivel_historico = nivel_historico.sort_values('sum', ascending=False)
        for _, row in nivel_historico.iterrows():
            print(f"{row['nivel']}: {int(row['count'])} registros, {int(row['sum']):,} alumnos")
        
        # Guardar resultados
        df_historico.to_csv('historico_siagie_fya_2019_2024.csv', index=False, encoding='utf-8')
        print(f"\n✅ Resultados históricos guardados en: historico_siagie_fya_2019_2024.csv")
        
        # Crear resumen por año
        tendencia.to_csv('tendencia_matricula_fya_2019_2024.csv', index=False, encoding='utf-8')
        print(f"✅ Tendencia por año guardada en: tendencia_matricula_fya_2019_2024.csv")
        
        return df_historico
    
    else:
        print("No se encontraron datos históricos")
        return None

if __name__ == "__main__":
    df_resultados = generar_reporte_historico()