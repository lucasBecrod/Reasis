#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Limpiador de Datos - Proyecto Reasis
Script para limpiar y corregir problemas de calidad de datos
"""

import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime

def limpiar_datos():
    """Limpia y corrige los problemas de calidad de datos"""
    print("🧹 LIMPIADOR DE DATOS - PROYECTO REASIS")
    print("=" * 60)
    
    db_path = "reasis_database.db"
    
    if not Path(db_path).exists():
        print(f"❌ Base de datos no encontrada: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        
        # Crear backup antes de limpiar
        backup_path = f"reasis_database_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        import shutil
        shutil.copy2(db_path, backup_path)
        print(f"📋 Backup creado: {backup_path}")
        
        # 1. CORREGIR DUPLICADOS EN indicadores_academicos_base
        print("\n🔄 1. CORRIGIENDO DUPLICADOS")
        print("=" * 40)
        
        # Contar duplicados antes
        df_duplicados_antes = pd.read_sql_query("""
            SELECT COUNT(*) as total_duplicados
            FROM (
                SELECT institucion_id, materia, nivel_educativo, grado, COUNT(*) as cnt
                FROM indicadores_academicos_base
                GROUP BY institucion_id, materia, nivel_educativo, grado
                HAVING COUNT(*) > 1
            ) duplicados
        """, conn)
        
        total_duplicados = df_duplicados_antes.iloc[0]['total_duplicados']
        print(f"   📊 Duplicados encontrados: {total_duplicados}")
        
        if total_duplicados > 0:
            # Eliminar duplicados manteniendo solo el primer registro
            conn.execute("""
                DELETE FROM indicadores_academicos_base 
                WHERE id NOT IN (
                    SELECT MIN(id)
                    FROM indicadores_academicos_base
                    GROUP BY institucion_id, materia, nivel_educativo, grado
                )
            """)
            conn.commit()
            print("   ✅ Duplicados eliminados")
        
        # 2. CORREGIR INCONSISTENCIAS EN GRADOS
        print("\n📚 2. CORRIGIENDO INCONSISTENCIAS EN GRADOS")
        print("=" * 40)
        
        # Verificar grados inconsistentes
        df_grados_inconsistentes = pd.read_sql_query("""
            SELECT grado, COUNT(*) as total
            FROM indicadores_academicos_base
            GROUP BY grado
            ORDER BY total
        """, conn)
        
        print("   📋 Grados encontrados:")
        for _, row in df_grados_inconsistentes.iterrows():
            print(f"      - {row['grado']}: {row['total']} registros")
        
        # Corregir "2 primaria" a "2 Primaria"
        conn.execute("""
            UPDATE indicadores_academicos_base 
            SET grado = '2 Primaria'
            WHERE grado = '2 primaria'
        """)
        conn.commit()
        print("   ✅ Grados inconsistentes corregidos")
        
        # 3. CORREGIR COMPLETITUD EN instituciones_educativas
        print("\n🏫 3. CORRIGIENDO COMPLETITUD EN INSTITUCIONES")
        print("=" * 40)
        
        # Verificar instituciones sin nombre_institucion pero con nombre_rer
        df_inst_sin_nombre = pd.read_sql_query("""
            SELECT id, nombre_institucion, nombre_rer, año
            FROM instituciones_educativas
            WHERE (nombre_institucion IS NULL OR nombre_institucion = '')
            AND (nombre_rer IS NOT NULL AND nombre_rer != '')
        """, conn)
        
        if len(df_inst_sin_nombre) > 0:
            print(f"   📊 Instituciones sin nombre_institucion: {len(df_inst_sin_nombre)}")
            # Copiar nombre_rer a nombre_institucion donde sea necesario
            conn.execute("""
                UPDATE instituciones_educativas 
                SET nombre_institucion = nombre_rer
                WHERE (nombre_institucion IS NULL OR nombre_institucion = '')
                AND (nombre_rer IS NOT NULL AND nombre_rer != '')
            """)
            conn.commit()
            print("   ✅ Nombres de instituciones corregidos")
        
        # 4. CORREGIR AMBITO VACÍO
        print("\n🌍 4. CORRIGIENDO ÁMBITO VACÍO")
        print("=" * 40)
        
        # Establecer ámbito como "Rural" por defecto para las RER
        conn.execute("""
            UPDATE instituciones_educativas 
            SET ambito = 'Rural'
            WHERE (ambito IS NULL OR ambito = '')
            AND nombre_rer LIKE '%RER%'
        """)
        conn.commit()
        print("   ✅ Ámbito corregido para instituciones RER")
        
        # 5. VERIFICAR Y CORREGIR RESPUESTAS VACÍAS
        print("\n📝 5. CORRIGIENDO RESPUESTAS VACÍAS")
        print("=" * 40)
        
        # Contar respuestas vacías
        df_respuestas_vacias = pd.read_sql_query("""
            SELECT COUNT(*) as total_vacias
            FROM datos_competencia_digital
            WHERE respuesta IS NULL OR respuesta = '' OR respuesta = 'nan'
        """, conn)
        
        total_vacias = df_respuestas_vacias.iloc[0]['total_vacias']
        print(f"   📊 Respuestas vacías: {total_vacias}")
        
        if total_vacias > 0:
            # Marcar respuestas vacías como "No aplica"
            conn.execute("""
                UPDATE datos_competencia_digital 
                SET respuesta = 'No aplica'
                WHERE respuesta IS NULL OR respuesta = '' OR respuesta = 'nan'
            """)
            conn.commit()
            print("   ✅ Respuestas vacías corregidas")
        
        # 6. VERIFICACIÓN FINAL
        print("\n✅ 6. VERIFICACIÓN FINAL")
        print("=" * 40)
        
        # Contar registros finales
        df_final = pd.read_sql_query("""
            SELECT 
                (SELECT COUNT(*) FROM instituciones_educativas) as inst,
                (SELECT COUNT(*) FROM indicadores_academicos_base) as acad,
                (SELECT COUNT(*) FROM datos_competencia_digital) as comp
        """, conn)
        
        print(f"   📋 Registros finales:")
        print(f"      - Instituciones: {df_final.iloc[0]['inst']}")
        print(f"      - Académicos: {df_final.iloc[0]['acad']}")
        print(f"      - Competencia digital: {df_final.iloc[0]['comp']}")
        
        # Verificar duplicados finales
        df_duplicados_final = pd.read_sql_query("""
            SELECT COUNT(*) as total_duplicados
            FROM (
                SELECT institucion_id, materia, nivel_educativo, grado, COUNT(*) as cnt
                FROM indicadores_academicos_base
                GROUP BY institucion_id, materia, nivel_educativo, grado
                HAVING COUNT(*) > 1
            ) duplicados
        """, conn)
        
        if df_duplicados_final.iloc[0]['total_duplicados'] == 0:
            print("   ✅ No quedan duplicados")
        else:
            print(f"   ⚠️ Quedan {df_duplicados_final.iloc[0]['total_duplicados']} duplicados")
        
        # Verificar completitud final
        df_completitud_final = pd.read_sql_query("""
            SELECT 
                SUM(CASE WHEN nombre_institucion IS NULL OR nombre_institucion = '' THEN 1 ELSE 0 END) as nombre_nulos,
                SUM(CASE WHEN nombre_rer IS NULL OR nombre_rer = '' THEN 1 ELSE 0 END) as rer_nulos,
                SUM(CASE WHEN ambito IS NULL OR ambito = '' THEN 1 ELSE 0 END) as ambito_nulos
            FROM instituciones_educativas
        """, conn)
        
        row = df_completitud_final.iloc[0]
        print(f"   📊 Completitud final:")
        print(f"      - nombre_institucion nulos: {row['nombre_nulos']}")
        print(f"      - nombre_rer nulos: {row['rer_nulos']}")
        print(f"      - ambito nulos: {row['ambito_nulos']}")
        
        conn.close()
        
        print(f"\n✅ LIMPIEZA DE DATOS COMPLETADA")
        print("=" * 60)
        print("💡 Los datos están ahora listos para análisis estadístico")
        print(f"📋 Backup disponible en: {backup_path}")
        
    except Exception as e:
        print(f"❌ Error en limpieza: {e}")

if __name__ == "__main__":
    limpiar_datos()
