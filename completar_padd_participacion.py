#!/usr/bin/env python3
"""
Completador de PADD Participación - Proyecto Reasis
Completa valores NULL usando datos de la misma institución en otras filas
"""

import sqlite3
import pandas as pd

def diagnosticar_padd_participacion():
    """Diagnosticar estado actual de la columna padd_participacion"""
    print("DIAGNÓSTICO: Estado actual de padd_participacion")
    print("=" * 60)
    
    conn = sqlite3.connect('reasis_database.db')
    
    # Estadísticas generales
    total_registros = pd.read_sql_query('SELECT COUNT(*) as count FROM resultados_academicos', conn).iloc[0, 0]
    
    con_padd = pd.read_sql_query('''
        SELECT COUNT(*) as count FROM resultados_academicos 
        WHERE padd_participacion IS NOT NULL AND padd_participacion != ''
    ''', conn).iloc[0, 0]
    
    sin_padd = total_registros - con_padd
    porcentaje_completo = (con_padd / total_registros * 100) if total_registros > 0 else 0
    
    print(f"Total registros: {total_registros:,}")
    print(f"Con padd_participacion: {con_padd:,} ({porcentaje_completo:.1f}%)")
    print(f"Sin padd_participacion: {sin_padd:,} ({(sin_padd/total_registros*100):.1f}%)")
    
    # Análisis por institución
    instituciones_padd = pd.read_sql_query('''
        SELECT 
            codigo_local,
            COUNT(*) as total_registros,
            COUNT(CASE WHEN padd_participacion IS NOT NULL AND padd_participacion != '' THEN 1 END) as con_padd,
            MIN(padd_participacion) as padd_ejemplo
        FROM resultados_academicos 
        WHERE codigo_modular IS NOT NULL
        GROUP BY codigo_local
        HAVING COUNT(*) > 1
        ORDER BY total_registros DESC
        LIMIT 10
    ''', conn)
    
    print(f"\nTOP 10 INSTITUCIONES CON MÁS REGISTROS:")
    print(instituciones_padd.to_string(index=False))
    
    # Valores únicos de padd_participacion
    valores_padd = pd.read_sql_query('''
        SELECT padd_participacion, COUNT(*) as frecuencia
        FROM resultados_academicos 
        WHERE padd_participacion IS NOT NULL AND padd_participacion != ''
        GROUP BY padd_participacion
        ORDER BY frecuencia DESC
        LIMIT 10
    ''', conn)
    
    print(f"\nVALORES MÁS FRECUENTES DE PADD:")
    print(valores_padd.to_string(index=False))
    
    conn.close()
    
    return {
        'total': total_registros,
        'con_padd': con_padd,
        'sin_padd': sin_padd,
        'porcentaje_completo': porcentaje_completo
    }

def identificar_instituciones_completables():
    """Identificar instituciones que pueden completarse"""
    print("\nIDENTIFICACIÓN: Instituciones completables")
    print("=" * 60)
    
    conn = sqlite3.connect('reasis_database.db')
    
    # Instituciones con datos parciales (algunas filas con padd, otras sin padd)
    instituciones_parciales = pd.read_sql_query('''
        SELECT 
            codigo_local,
            COUNT(*) as total_filas,
            COUNT(CASE WHEN padd_participacion IS NOT NULL AND padd_participacion != '' THEN 1 END) as con_padd,
            COUNT(CASE WHEN padd_participacion IS NULL OR padd_participacion = '' THEN 1 END) as sin_padd,
            MIN(CASE WHEN padd_participacion IS NOT NULL AND padd_participacion != '' THEN padd_participacion END) as padd_valor
        FROM resultados_academicos 
        WHERE codigo_modular IS NOT NULL
        GROUP BY codigo_local
        HAVING COUNT(CASE WHEN padd_participacion IS NOT NULL AND padd_participacion != '' THEN 1 END) > 0
        AND COUNT(CASE WHEN padd_participacion IS NULL OR padd_participacion = '' THEN 1 END) > 0
        ORDER BY sin_padd DESC
    ''', conn)
    
    print(f"Instituciones con datos parciales (completables): {len(instituciones_parciales)}")
    
    if len(instituciones_parciales) > 0:
        print(f"\nTOP 10 INSTITUCIONES COMPLETABLES:")
        print(instituciones_parciales.head(10).to_string(index=False))
        
        total_completables = instituciones_parciales['sin_padd'].sum()
        print(f"\nTotal registros que se pueden completar: {total_completables:,}")
    
    conn.close()
    
    return instituciones_parciales

def completar_padd_por_institucion(instituciones_completables):
    """Completar valores PADD usando datos de la misma institución"""
    print("\nCOMPLETANDO: Valores PADD por institución")
    print("=" * 60)
    
    conn = sqlite3.connect('reasis_database.db')
    
    total_completados = 0
    instituciones_procesadas = 0
    
    print("Procesando instituciones...")
    
    for _, row in instituciones_completables.iterrows():
        codigo_local = row['codigo_local']
        sin_padd = row['sin_padd']
        padd_valor = row['padd_valor']
        
        if padd_valor is None or padd_valor == '':
            continue
        
        # Actualizar registros sin padd_participacion para esta institución
        updated = conn.execute('''
            UPDATE resultados_academicos 
            SET padd_participacion = ?
            WHERE codigo_local = ? 
            AND (padd_participacion IS NULL OR padd_participacion = '')
        ''', (padd_valor, codigo_local)).rowcount
        
        if updated > 0:
            total_completados += updated
            instituciones_procesadas += 1
            
            if instituciones_procesadas % 10 == 0:  # Progreso cada 10 instituciones
                print(f"  Procesadas {instituciones_procesadas} instituciones, completados {total_completados} registros")
    
    conn.commit()
    
    print(f"\nRESULTADO COMPLETADO:")
    print(f"Instituciones procesadas: {instituciones_procesadas}")
    print(f"Total registros completados: {total_completados:,}")
    
    conn.close()
    
    return total_completados

def completar_padd_por_nombre_ie():
    """Completar valores PADD usando nombre_ie_original como alternativa"""
    print("\nCOMPLETANDO: Valores PADD por nombre IE (alternativa)")
    print("=" * 60)
    
    conn = sqlite3.connect('reasis_database.db')
    
    # Identificar registros que aún tienen PADD NULL pero podrían completarse por nombre
    nombres_completables = pd.read_sql_query('''
        SELECT 
            nombre_ie_original,
            COUNT(*) as total_filas,
            COUNT(CASE WHEN padd_participacion IS NOT NULL AND padd_participacion != '' THEN 1 END) as con_padd,
            COUNT(CASE WHEN padd_participacion IS NULL OR padd_participacion = '' THEN 1 END) as sin_padd,
            MIN(CASE WHEN padd_participacion IS NOT NULL AND padd_participacion != '' THEN padd_participacion END) as padd_valor
        FROM resultados_academicos 
        WHERE codigo_modular IS NOT NULL
        AND nombre_ie_original IS NOT NULL
        GROUP BY nombre_ie_original
        HAVING COUNT(CASE WHEN padd_participacion IS NOT NULL AND padd_participacion != '' THEN 1 END) > 0
        AND COUNT(CASE WHEN padd_participacion IS NULL OR padd_participacion = '' THEN 1 END) > 0
        ORDER BY sin_padd DESC
        LIMIT 20
    ''', conn)
    
    print(f"Nombres IE con datos parciales: {len(nombres_completables)}")
    
    total_completados = 0
    
    for _, row in nombres_completables.iterrows():
        nombre_ie = row['nombre_ie_original']
        padd_valor = row['padd_valor']
        
        if padd_valor is None or padd_valor == '':
            continue
        
        # Actualizar registros sin padd_participacion para este nombre IE
        updated = conn.execute('''
            UPDATE resultados_academicos 
            SET padd_participacion = ?
            WHERE nombre_ie_original = ? 
            AND (padd_participacion IS NULL OR padd_participacion = '')
        ''', (padd_valor, nombre_ie)).rowcount
        
        if updated > 0:
            total_completados += updated
            print(f"  {nombre_ie}: +{updated} registros completados")
    
    conn.commit()
    
    print(f"\nRegistros completados por nombre IE: {total_completados:,}")
    
    conn.close()
    
    return total_completados

def generar_reporte_final():
    """Generar reporte final del proceso de completado"""
    print("\nREPORTE FINAL: Completado de padd_participacion")
    print("=" * 60)
    
    conn = sqlite3.connect('reasis_database.db')
    
    # Estadísticas finales
    total_registros = pd.read_sql_query('SELECT COUNT(*) as count FROM resultados_academicos', conn).iloc[0, 0]
    
    con_padd = pd.read_sql_query('''
        SELECT COUNT(*) as count FROM resultados_academicos 
        WHERE padd_participacion IS NOT NULL AND padd_participacion != ''
    ''', conn).iloc[0, 0]
    
    sin_padd = total_registros - con_padd
    porcentaje_completo = (con_padd / total_registros * 100) if total_registros > 0 else 0
    
    print(f"ESTADO FINAL:")
    print(f"Total registros: {total_registros:,}")
    print(f"Con padd_participacion: {con_padd:,} ({porcentaje_completo:.1f}%)")
    print(f"Sin padd_participacion: {sin_padd:,} ({(sin_padd/total_registros*100):.1f}%)")
    
    # Análisis por institución vinculada
    instituciones_vinculadas = pd.read_sql_query('''
        SELECT 
            COUNT(DISTINCT codigo_modular) as instituciones_total,
            COUNT(DISTINCT CASE WHEN padd_participacion IS NOT NULL AND padd_participacion != '' THEN codigo_modular END) as instituciones_con_padd
        FROM resultados_academicos 
        WHERE codigo_modular IS NOT NULL
    ''', conn)
    
    inst_total = instituciones_vinculadas.iloc[0]['instituciones_total']
    inst_con_padd = instituciones_vinculadas.iloc[0]['instituciones_con_padd']
    
    print(f"\nINSTITUCIONES VINCULADAS:")
    print(f"Total instituciones con ILA: {inst_total}")
    print(f"Instituciones con datos PADD: {inst_con_padd} ({(inst_con_padd/inst_total*100):.1f}%)")
    
    # Valores finales únicos
    valores_finales = pd.read_sql_query('''
        SELECT padd_participacion, COUNT(*) as frecuencia
        FROM resultados_academicos 
        WHERE padd_participacion IS NOT NULL AND padd_participacion != ''
        GROUP BY padd_participacion
        ORDER BY frecuencia DESC
    ''', conn)
    
    print(f"\nVALORES PADD FINALES ({len(valores_finales)} únicos):")
    print(valores_finales.to_string(index=False))
    
    conn.close()
    
    return porcentaje_completo

def completar_padd_participacion_completo():
    """Función principal para completar padd_participacion"""
    print("COMPLETADOR DE PADD PARTICIPACIÓN - PROYECTO REASIS")
    print("=" * 70)
    
    # Paso 1: Diagnóstico inicial
    estado_inicial = diagnosticar_padd_participacion()
    
    # Paso 2: Identificar instituciones completables
    instituciones_completables = identificar_instituciones_completables()
    
    if len(instituciones_completables) == 0:
        print("\n✅ No hay registros para completar por código local")
    else:
        # Paso 3: Completar por código local (institución)
        completados_codigo = completar_padd_por_institucion(instituciones_completables)
        print(f"\n✅ Completados por código local: {completados_codigo:,} registros")
    
    # Paso 4: Completar por nombre IE (alternativa)
    completados_nombre = completar_padd_por_nombre_ie()
    print(f"✅ Completados por nombre IE: {completados_nombre:,} registros")
    
    # Paso 5: Reporte final
    porcentaje_final = generar_reporte_final()
    
    # Resumen de mejora
    mejora_porcentaje = porcentaje_final - estado_inicial['porcentaje_completo']
    total_completados = completados_codigo + completados_nombre if 'completados_codigo' in locals() else completados_nombre
    
    print(f"\nMEJORA LOGRADA:")
    print(f"Porcentaje inicial: {estado_inicial['porcentaje_completo']:.1f}%")
    print(f"Porcentaje final: {porcentaje_final:.1f}%")
    print(f"Mejora: +{mejora_porcentaje:.1f} puntos porcentuales")
    print(f"Registros completados: {total_completados:,}")
    
    return porcentaje_final

if __name__ == "__main__":
    porcentaje_final = completar_padd_participacion_completo()
    print(f"\nRESULTADO FINAL: {porcentaje_final:.1f}% completitud en padd_participacion")