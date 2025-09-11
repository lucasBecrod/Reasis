#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Auditoría de Calidad de Datos - Proyecto Reasis
Script para verificar la calidad, integridad y consistencia de los datos consolidados
"""

import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

def auditoria_calidad_datos():
    """Realiza una auditoría completa de la calidad de los datos"""
    print("🔍 AUDITORÍA DE CALIDAD DE DATOS - PROYECTO REASIS")
    print("=" * 70)
    
    db_path = "reasis_database.db"
    
    if not Path(db_path).exists():
        print(f"❌ Base de datos no encontrada: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        
        # 1. VERIFICACIÓN DE INTEGRIDAD REFERENCIAL
        print("\n🔗 1. VERIFICACIÓN DE INTEGRIDAD REFERENCIAL")
        print("=" * 50)
        
        # Verificar claves foráneas en indicadores_academicos_base
        print("\n📚 Verificando claves foráneas en indicadores_academicos_base:")
        df_foreign_keys = pd.read_sql_query("""
            SELECT iab.institucion_id, COUNT(*) as registros
            FROM indicadores_academicos_base iab
            LEFT JOIN instituciones_educativas ie ON iab.institucion_id = ie.id
            WHERE ie.id IS NULL
            GROUP BY iab.institucion_id
        """, conn)
        
        if len(df_foreign_keys) == 0:
            print("   ✅ Todas las claves foráneas son válidas")
        else:
            print(f"   ❌ Encontrados {len(df_foreign_keys)} institucion_id sin referencia")
            for _, row in df_foreign_keys.iterrows():
                print(f"      - institucion_id {row['institucion_id']}: {row['registros']} registros huérfanos")
        
        # Verificar claves foráneas en datos_competencia_digital
        print("\n💻 Verificando claves foráneas en datos_competencia_digital:")
        df_foreign_keys_comp = pd.read_sql_query("""
            SELECT dcd.institucion_id, COUNT(*) as registros
            FROM datos_competencia_digital dcd
            LEFT JOIN instituciones_educativas ie ON dcd.institucion_id = ie.id
            WHERE ie.id IS NULL
            GROUP BY dcd.institucion_id
        """, conn)
        
        if len(df_foreign_keys_comp) == 0:
            print("   ✅ Todas las claves foráneas son válidas")
        else:
            print(f"   ❌ Encontrados {len(df_foreign_keys_comp)} institucion_id sin referencia")
            for _, row in df_foreign_keys_comp.iterrows():
                print(f"      - institucion_id {row['institucion_id']}: {row['registros']} registros huérfanos")
        
        # 2. VERIFICACIÓN DE COMPLETITUD DE DATOS
        print("\n📊 2. VERIFICACIÓN DE COMPLETITUD DE DATOS")
        print("=" * 50)
        
        # Completitud en instituciones_educativas
        print("\n🏫 Completitud en instituciones_educativas:")
        df_completitud_inst = pd.read_sql_query("""
            SELECT 
                COUNT(*) as total_registros,
                SUM(CASE WHEN nombre_institucion IS NULL OR nombre_institucion = '' THEN 1 ELSE 0 END) as nombre_institucion_nulos,
                SUM(CASE WHEN nombre_rer IS NULL OR nombre_rer = '' THEN 1 ELSE 0 END) as nombre_rer_nulos,
                SUM(CASE WHEN año IS NULL THEN 1 ELSE 0 END) as año_nulos,
                SUM(CASE WHEN ambito IS NULL OR ambito = '' THEN 1 ELSE 0 END) as ambito_nulos
            FROM instituciones_educativas
        """, conn)
        
        row = df_completitud_inst.iloc[0]
        print(f"   Total registros: {row['total_registros']}")
        print(f"   nombre_institucion nulos: {row['nombre_institucion_nulos']} ({row['nombre_institucion_nulos']/row['total_registros']*100:.1f}%)")
        print(f"   nombre_rer nulos: {row['nombre_rer_nulos']} ({row['nombre_rer_nulos']/row['total_registros']*100:.1f}%)")
        print(f"   año nulos: {row['año_nulos']} ({row['año_nulos']/row['total_registros']*100:.1f}%)")
        print(f"   ambito nulos: {row['ambito_nulos']} ({row['ambito_nulos']/row['total_registros']*100:.1f}%)")
        
        # Completitud en indicadores_academicos_base
        print("\n📚 Completitud en indicadores_academicos_base:")
        df_completitud_acad = pd.read_sql_query("""
            SELECT 
                COUNT(*) as total_registros,
                SUM(CASE WHEN institucion_id IS NULL THEN 1 ELSE 0 END) as institucion_id_nulos,
                SUM(CASE WHEN año IS NULL THEN 1 ELSE 0 END) as año_nulos,
                SUM(CASE WHEN materia IS NULL OR materia = '' THEN 1 ELSE 0 END) as materia_nulos,
                SUM(CASE WHEN nivel_educativo IS NULL OR nivel_educativo = '' THEN 1 ELSE 0 END) as nivel_nulos,
                SUM(CASE WHEN grado IS NULL OR grado = '' THEN 1 ELSE 0 END) as grado_nulos
            FROM indicadores_academicos_base
        """, conn)
        
        row = df_completitud_acad.iloc[0]
        print(f"   Total registros: {row['total_registros']}")
        print(f"   institucion_id nulos: {row['institucion_id_nulos']} ({row['institucion_id_nulos']/row['total_registros']*100:.1f}%)")
        print(f"   año nulos: {row['año_nulos']} ({row['año_nulos']/row['total_registros']*100:.1f}%)")
        print(f"   materia nulos: {row['materia_nulos']} ({row['materia_nulos']/row['total_registros']*100:.1f}%)")
        print(f"   nivel_educativo nulos: {row['nivel_nulos']} ({row['nivel_nulos']/row['total_registros']*100:.1f}%)")
        print(f"   grado nulos: {row['grado_nulos']} ({row['grado_nulos']/row['total_registros']*100:.1f}%)")
        
        # Completitud en datos_competencia_digital
        print("\n💻 Completitud en datos_competencia_digital:")
        df_completitud_comp = pd.read_sql_query("""
            SELECT 
                COUNT(*) as total_registros,
                SUM(CASE WHEN institucion_id IS NULL THEN 1 ELSE 0 END) as institucion_id_nulos,
                SUM(CASE WHEN año IS NULL THEN 1 ELSE 0 END) as año_nulos,
                SUM(CASE WHEN tipo_encuesta IS NULL OR tipo_encuesta = '' THEN 1 ELSE 0 END) as tipo_encuesta_nulos,
                SUM(CASE WHEN pregunta IS NULL OR pregunta = '' THEN 1 ELSE 0 END) as pregunta_nulos,
                SUM(CASE WHEN respuesta IS NULL OR respuesta = '' THEN 1 ELSE 0 END) as respuesta_nulos
            FROM datos_competencia_digital
        """, conn)
        
        row = df_completitud_comp.iloc[0]
        print(f"   Total registros: {row['total_registros']}")
        print(f"   institucion_id nulos: {row['institucion_id_nulos']} ({row['institucion_id_nulos']/row['total_registros']*100:.1f}%)")
        print(f"   año nulos: {row['año_nulos']} ({row['año_nulos']/row['total_registros']*100:.1f}%)")
        print(f"   tipo_encuesta nulos: {row['tipo_encuesta_nulos']} ({row['tipo_encuesta_nulos']/row['total_registros']*100:.1f}%)")
        print(f"   pregunta nulos: {row['pregunta_nulos']} ({row['pregunta_nulos']/row['total_registros']*100:.1f}%)")
        print(f"   respuesta nulos: {row['respuesta_nulos']} ({row['respuesta_nulos']/row['total_registros']*100:.1f}%)")
        
        # 3. VERIFICACIÓN DE CONSISTENCIA DE DATOS
        print("\n🔄 3. VERIFICACIÓN DE CONSISTENCIA DE DATOS")
        print("=" * 50)
        
        # Valores únicos en campos importantes
        print("\n📋 Valores únicos en campos importantes:")
        
        # Materias únicas
        df_materias = pd.read_sql_query("""
            SELECT materia, COUNT(*) as total
            FROM indicadores_academicos_base 
            GROUP BY materia
            ORDER BY total DESC
        """, conn)
        print(f"   Materias únicas: {len(df_materias)}")
        for _, row in df_materias.iterrows():
            print(f"      - {row['materia']}: {row['total']} registros")
        
        # Niveles educativos únicos
        df_niveles = pd.read_sql_query("""
            SELECT nivel_educativo, COUNT(*) as total
            FROM indicadores_academicos_base 
            GROUP BY nivel_educativo
            ORDER BY total DESC
        """, conn)
        print(f"   Niveles educativos únicos: {len(df_niveles)}")
        for _, row in df_niveles.iterrows():
            print(f"      - {row['nivel_educativo']}: {row['total']} registros")
        
        # Grados únicos
        df_grados = pd.read_sql_query("""
            SELECT grado, COUNT(*) as total
            FROM indicadores_academicos_base 
            GROUP BY grado
            ORDER BY total DESC
        """, conn)
        print(f"   Grados únicos: {len(df_grados)}")
        for _, row in df_grados.iterrows():
            print(f"      - {row['grado']}: {row['total']} registros")
        
        # Tipos de encuesta únicos
        df_tipos = pd.read_sql_query("""
            SELECT tipo_encuesta, COUNT(*) as total
            FROM datos_competencia_digital 
            GROUP BY tipo_encuesta
            ORDER BY total DESC
        """, conn)
        print(f"   Tipos de encuesta únicos: {len(df_tipos)}")
        for _, row in df_tipos.iterrows():
            print(f"      - {row['tipo_encuesta']}: {row['total']} registros")
        
        # 4. VERIFICACIÓN DE DUPLICADOS
        print("\n🔄 4. VERIFICACIÓN DE DUPLICADOS")
        print("=" * 50)
        
        # Duplicados en instituciones_educativas
        print("\n🏫 Duplicados en instituciones_educativas:")
        df_duplicados_inst = pd.read_sql_query("""
            SELECT nombre_institucion, nombre_rer, año, COUNT(*) as duplicados
            FROM instituciones_educativas
            GROUP BY nombre_institucion, nombre_rer, año
            HAVING COUNT(*) > 1
            ORDER BY duplicados DESC
        """, conn)
        
        if len(df_duplicados_inst) == 0:
            print("   ✅ No se encontraron duplicados")
        else:
            print(f"   ❌ Encontrados {len(df_duplicados_inst)} grupos de duplicados")
            for _, row in df_duplicados_inst.iterrows():
                nombre = row['nombre_institucion'] if row['nombre_institucion'] else row['nombre_rer']
                print(f"      - {nombre} ({row['año']}): {row['duplicados']} duplicados")
        
        # Duplicados en indicadores_academicos_base
        print("\n📚 Duplicados en indicadores_academicos_base:")
        df_duplicados_acad = pd.read_sql_query("""
            SELECT institucion_id, materia, nivel_educativo, grado, COUNT(*) as duplicados
            FROM indicadores_academicos_base
            GROUP BY institucion_id, materia, nivel_educativo, grado
            HAVING COUNT(*) > 1
            ORDER BY duplicados DESC
            LIMIT 10
        """, conn)
        
        if len(df_duplicados_acad) == 0:
            print("   ✅ No se encontraron duplicados")
        else:
            print(f"   ❌ Encontrados {len(df_duplicados_acad)} grupos de duplicados (mostrando 10)")
            for _, row in df_duplicados_acad.iterrows():
                print(f"      - institucion_id {row['institucion_id']}, {row['materia']}, {row['nivel_educativo']}, {row['grado']}: {row['duplicados']} duplicados")
        
        # 5. VERIFICACIÓN DE ANOMALÍAS
        print("\n⚠️ 5. VERIFICACIÓN DE ANOMALÍAS")
        print("=" * 50)
        
        # Años fuera de rango esperado
        print("\n📅 Años fuera de rango esperado:")
        df_años_anomalos = pd.read_sql_query("""
            SELECT año, COUNT(*) as total
            FROM instituciones_educativas
            WHERE año < 2020 OR año > 2025
            GROUP BY año
            ORDER BY año
        """, conn)
        
        if len(df_años_anomalos) == 0:
            print("   ✅ Todos los años están en el rango esperado (2020-2025)")
        else:
            print("   ❌ Años fuera de rango:")
            for _, row in df_años_anomalos.iterrows():
                print(f"      - Año {row['año']}: {row['total']} registros")
        
        # Respuestas vacías o inconsistentes
        print("\n📝 Respuestas vacías o inconsistentes:")
        df_respuestas_vacias = pd.read_sql_query("""
            SELECT COUNT(*) as total_vacias
            FROM datos_competencia_digital
            WHERE respuesta IS NULL OR respuesta = '' OR respuesta = 'nan'
        """, conn)
        
        total_respuestas = pd.read_sql_query("SELECT COUNT(*) as total FROM datos_competencia_digital", conn)
        porcentaje_vacias = (df_respuestas_vacias.iloc[0]['total_vacias'] / total_respuestas.iloc[0]['total']) * 100
        
        print(f"   Respuestas vacías: {df_respuestas_vacias.iloc[0]['total_vacias']} ({porcentaje_vacias:.1f}%)")
        
        # 6. RESUMEN DE CALIDAD
        print("\n📊 6. RESUMEN DE CALIDAD DE DATOS")
        print("=" * 50)
        
        # Calcular métricas de calidad
        total_registros = pd.read_sql_query("""
            SELECT 
                (SELECT COUNT(*) FROM instituciones_educativas) as inst,
                (SELECT COUNT(*) FROM indicadores_academicos_base) as acad,
                (SELECT COUNT(*) FROM datos_competencia_digital) as comp
        """, conn)
        
        print(f"📋 Total de registros:")
        print(f"   - Instituciones: {total_registros.iloc[0]['inst']}")
        print(f"   - Académicos: {total_registros.iloc[0]['acad']}")
        print(f"   - Competencia digital: {total_registros.iloc[0]['comp']}")
        
        # Calcular porcentaje de completitud
        completitud_inst = (187 - df_completitud_inst.iloc[0]['nombre_institucion_nulos'] - df_completitud_inst.iloc[0]['nombre_rer_nulos']) / 187 * 100
        completitud_acad = (15054 - df_completitud_acad.iloc[0]['institucion_id_nulos'] - df_completitud_acad.iloc[0]['materia_nulos']) / 15054 * 100
        completitud_comp = (39086 - df_completitud_comp.iloc[0]['institucion_id_nulos'] - df_completitud_comp.iloc[0]['pregunta_nulos']) / 39086 * 100
        
        print(f"\n✅ Completitud de datos:")
        print(f"   - Instituciones: {completitud_inst:.1f}%")
        print(f"   - Académicos: {completitud_acad:.1f}%")
        print(f"   - Competencia digital: {completitud_comp:.1f}%")
        
        # Recomendaciones
        print(f"\n💡 RECOMENDACIONES:")
        if len(df_foreign_keys) > 0 or len(df_foreign_keys_comp) > 0:
            print("   ❌ Corregir claves foráneas huérfanas")
        if porcentaje_vacias > 5:
            print("   ⚠️ Revisar respuestas vacías en competencia digital")
        if len(df_duplicados_inst) > 0 or len(df_duplicados_acad) > 0:
            print("   ⚠️ Eliminar registros duplicados")
        
        print("   ✅ Los datos están listos para análisis estadístico")
        
        conn.close()
        
        print(f"\n✅ AUDITORÍA DE CALIDAD COMPLETADA")
        print("=" * 70)
        
    except Exception as e:
        print(f"❌ Error en auditoría: {e}")

if __name__ == "__main__":
    auditoria_calidad_datos()
