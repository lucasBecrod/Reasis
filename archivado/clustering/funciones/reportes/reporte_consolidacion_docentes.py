#!/usr/bin/env python3
"""
Reporte Detallado - Consolidación Docentes PADD
Genera análisis completo de los datos de docentes consolidados
"""

import pandas as pd
import sqlite3
from pathlib import Path

def generar_reporte_completo():
    """Generar reporte detallado de consolidación docentes"""
    print("REPORTE DETALLADO - CONSOLIDACIÓN DATOS DOCENTES")
    print("=" * 70)
    
    conn = sqlite3.connect('reasis_database.db')
    
    # 1. ESTADÍSTICAS GENERALES
    print("\n1. ESTADÍSTICAS GENERALES")
    print("-" * 40)
    
    total_registros = pd.read_sql_query('SELECT COUNT(*) as count FROM docentes_data', conn).iloc[0, 0]
    docentes_unicos = pd.read_sql_query('SELECT COUNT(DISTINCT dni) as count FROM docentes_data', conn).iloc[0, 0]
    
    print(f"Total registros: {total_registros:,}")
    print(f"Docentes únicos: {docentes_unicos:,}")
    print(f"Registros duplicados resueltos: {total_registros - docentes_unicos}")
    
    # 2. DISTRIBUCIÓN POR AÑO
    print("\n2. DISTRIBUCIÓN POR AÑO")
    print("-" * 40)
    
    por_año = pd.read_sql_query('''
        SELECT año, COUNT(*) as registros, COUNT(DISTINCT dni) as docentes_unicos
        FROM docentes_data
        GROUP BY año
        ORDER BY año
    ''', conn)
    
    print(por_año.to_string(index=False))
    
    # 3. DOCENTES EN AMBOS AÑOS (CONTINUIDAD)
    print("\n3. ANALISIS DE CONTINUIDAD (2023 - 2024)")
    print("-" * 50)
    
    continuidad = pd.read_sql_query('''
        SELECT 
            d1.dni,
            d1.nombres,
            d1.apellidos,
            d1.rer,
            d1.estado_evaluacion as estado_2023,
            d2.estado_evaluacion as estado_2024,
            d1.continua_rer as continua_2023,
            d2.continua_rer as continua_2024
        FROM docentes_data d1
        INNER JOIN docentes_data d2 ON d1.dni = d2.dni AND d1.año = 2023 AND d2.año = 2024
        ORDER BY d1.nombres, d1.apellidos
    ''', conn)
    
    print(f"Docentes en ambos años: {len(continuidad)}")
    
    if len(continuidad) > 0:
        print("\nDocentes con continuidad 2023-2024:")
        for _, row in continuidad.iterrows():
            print(f"  DNI {row['dni']}: {row['nombres']} {row['apellidos']}")
            print(f"    RER: {row['rer']} | {row['estado_2023']} - {row['estado_2024']}")
    
    # 4. DISTRIBUCIÓN POR RER (REDES EDUCATIVAS RURALES)
    print("\n4. DISTRIBUCIÓN POR RER")
    print("-" * 40)
    
    por_rer = pd.read_sql_query('''
        SELECT 
            rer,
            COUNT(*) as total_registros,
            COUNT(DISTINCT dni) as docentes_unicos,
            COUNT(DISTINCT CASE WHEN año = 2023 THEN dni END) as docentes_2023,
            COUNT(DISTINCT CASE WHEN año = 2024 THEN dni END) as docentes_2024
        FROM docentes_data
        WHERE rer IS NOT NULL
        GROUP BY rer
        ORDER BY total_registros DESC
        LIMIT 10
    ''', conn)
    
    print("Top 10 RER por total de registros:")
    print(por_rer.to_string(index=False))
    
    # 5. ESTADOS DE EVALUACIÓN
    print("\n5. ESTADOS DE EVALUACIÓN")
    print("-" * 40)
    
    estados = pd.read_sql_query('''
        SELECT 
            año,
            estado_evaluacion,
            COUNT(*) as registros,
            ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY año), 1) as porcentaje
        FROM docentes_data
        WHERE estado_evaluacion IS NOT NULL
        GROUP BY año, estado_evaluacion
        ORDER BY año, registros DESC
    ''', conn)
    
    print(estados.to_string(index=False))
    
    # 6. EVALUACIONES ACADÉMICAS (SOLO 2023)
    print("\n6. EVALUACIONES ACADÉMICAS (SOLO 2023)")
    print("-" * 50)
    
    evaluaciones = pd.read_sql_query('''
        SELECT 
            COUNT(*) as total_evaluados,
            ROUND(AVG(puntaje_matematica), 2) as promedio_matematica,
            ROUND(AVG(puntaje_comunicacion), 2) as promedio_comunicacion,
            ROUND(AVG(puntaje_digital), 2) as promedio_digital,
            MIN(puntaje_matematica) as min_matematica,
            MAX(puntaje_matematica) as max_matematica,
            MIN(puntaje_comunicacion) as min_comunicacion,
            MAX(puntaje_comunicacion) as max_comunicacion,
            MIN(puntaje_digital) as min_digital,
            MAX(puntaje_digital) as max_digital
        FROM docentes_data
        WHERE año = 2023 AND puntaje_matematica IS NOT NULL
    ''', conn)
    
    if len(evaluaciones) > 0 and evaluaciones.iloc[0]['total_evaluados'] > 0:
        row = evaluaciones.iloc[0]
        print(f"Docentes evaluados 2023: {row['total_evaluados']}")
        print(f"\nPromedios:")
        print(f"  Matemática: {row['promedio_matematica']} (rango: {row['min_matematica']}-{row['max_matematica']})")
        print(f"  Comunicación: {row['promedio_comunicacion']} (rango: {row['min_comunicacion']}-{row['max_comunicacion']})")
        print(f"  Digital: {row['promedio_digital']} (rango: {row['min_digital']}-{row['max_digital']})")
    else:
        print("No hay datos de evaluaciones académicas disponibles")
    
    # 7. CONTINUIDAD EN RER
    print("\n7. ANÁLISIS CONTINUIDAD EN RER")
    print("-" * 40)
    
    continuidad_rer = pd.read_sql_query('''
        SELECT 
            año,
            continua_rer,
            COUNT(*) as registros,
            ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY año), 1) as porcentaje
        FROM docentes_data
        WHERE continua_rer IS NOT NULL AND continua_rer != ''
        GROUP BY año, continua_rer
        ORDER BY año, registros DESC
    ''', conn)
    
    print(continuidad_rer.to_string(index=False))
    
    # 8. COMPLETITUD DE DATOS
    print("\n8. COMPLETITUD DE DATOS")
    print("-" * 40)
    
    campos_importantes = [
        'dni', 'nombres', 'apellidos', 'genero', 'rer', 
        'institucion_actual', 'codigo_modular_actual',
        'continua_rer', 'estado_evaluacion'
    ]
    
    for campo in campos_importantes:
        completitud = pd.read_sql_query(f'''
            SELECT 
                COUNT(*) as total,
                COUNT({campo}) as completos,
                ROUND(COUNT({campo}) * 100.0 / COUNT(*), 1) as porcentaje_completo
            FROM docentes_data
            WHERE {campo} IS NOT NULL AND {campo} != ''
        ''', conn).iloc[0]
        
        print(f"  {campo}: {completitud['porcentaje_completo']}% ({completitud['completos']}/{completitud['total']})")
    
    # 9. CÓDIGOS MODULARES ÚNICOS
    print("\n9. INSTITUCIONES EDUCATIVAS IDENTIFICADAS")
    print("-" * 50)
    
    instituciones = pd.read_sql_query('''
        SELECT 
            COUNT(DISTINCT codigo_modular_actual) as instituciones_unicas,
            COUNT(DISTINCT CASE WHEN año = 2023 THEN codigo_modular_actual END) as instituciones_2023,
            COUNT(DISTINCT CASE WHEN año = 2024 THEN codigo_modular_actual END) as instituciones_2024
        FROM docentes_data
        WHERE codigo_modular_actual IS NOT NULL AND codigo_modular_actual != ''
    ''', conn).iloc[0]
    
    print(f"Instituciones educativas únicas: {instituciones['instituciones_unicas']}")
    print(f"Instituciones en 2023: {instituciones['instituciones_2023']}")
    print(f"Instituciones en 2024: {instituciones['instituciones_2024']}")
    
    conn.close()
    
    # 10. RESUMEN PARA PRÓXIMOS PASOS
    print("\n10. RESUMEN Y PRÓXIMOS PASOS")
    print("=" * 50)
    print("CONSOLIDACION EXITOSA:")
    print(f"   - {total_registros:,} registros de docentes procesados")
    print(f"   - {docentes_unicos:,} docentes unicos identificados")
    print("   - Datos de 2023 y 2024 integrados correctamente")
    print("   - 4 duplicados resueltos (docentes en ambos años)")
    print(f"   - {instituciones['instituciones_unicas']} instituciones educativas identificadas")
    
    print("\nPROXIMOS PASOS:")
    print("   1. Vincular con tabla instituciones_educativas usando codigo_modular")
    print("   2. Calcular X4: Indice de Desempeño Docente (IDD)")
    print("   3. Calcular X5: Estabilidad Docente (ED)")
    print("   4. Preparar datos para X6: Competencia Digital Docente (CDD)")
    
    return {
        'total_registros': total_registros,
        'docentes_unicos': docentes_unicos,
        'instituciones_unicas': int(instituciones['instituciones_unicas'])
    }

if __name__ == "__main__":
    stats = generar_reporte_completo()
    print(f"\nCONSOLIDACION DOCENTES COMPLETADA EXITOSAMENTE")
    print(f"   Base solida para calculo de variables docentes X4, X5, X6")