#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Árbol de Base de Datos - Proyecto Reasis
Script para mostrar la estructura completa de la base de datos
"""

import sqlite3
import pandas as pd
from pathlib import Path

def mostrar_arbol_base_datos():
    """Muestra el árbol completo de la base de datos"""
    print("🌳 ÁRBOL DE BASE DE DATOS - PROYECTO REASIS")
    print("=" * 70)
    
    db_path = "reasis_database.db"
    
    if not Path(db_path).exists():
        print(f"❌ Base de datos no encontrada: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        
        # Obtener lista de tablas
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tablas = cursor.fetchall()
        
        print(f"📁 BASE DE DATOS: reasis_database.db")
        print(f"📋 TOTAL DE TABLAS: {len(tablas)}")
        print("=" * 70)
        
        for i, tabla in enumerate(tablas, 1):
            nombre_tabla = tabla[0]
            print(f"\n📊 TABLA {i}: {nombre_tabla}")
            print("-" * 50)
            
            # Obtener información de columnas
            cursor.execute(f"PRAGMA table_info({nombre_tabla})")
            columnas = cursor.fetchall()
            
            # Contar registros
            cursor.execute(f"SELECT COUNT(*) FROM {nombre_tabla}")
            count = cursor.fetchone()[0]
            
            print(f"📈 Registros: {count}")
            print(f"📋 Columnas ({len(columnas)}):")
            
            for j, col in enumerate(columnas, 1):
                # col[0] = cid, col[1] = name, col[2] = type, col[3] = notnull, col[4] = dflt_value, col[5] = pk
                nombre_col = col[1]
                tipo_col = col[2]
                not_null = "NOT NULL" if col[3] else "NULL"
                primary_key = "PRIMARY KEY" if col[5] else ""
                default = f"DEFAULT {col[4]}" if col[4] else ""
                
                # Determinar si es clave foránea
                es_foreign_key = ""
                if nombre_col == "institucion_id":
                    es_foreign_key = " → instituciones_educativas(id)"
                
                # Formatear la línea
                linea = f"   {j:2d}. {nombre_col:<25} {tipo_col:<15} {not_null:<10}"
                if primary_key:
                    linea += f" {primary_key}"
                if default:
                    linea += f" {default}"
                if es_foreign_key:
                    linea += f" {es_foreign_key}"
                
                print(linea)
            
            # Mostrar índices si existen
            cursor.execute(f"PRAGMA index_list({nombre_tabla})")
            indices = cursor.fetchall()
            
            if indices:
                print(f"🔍 Índices ({len(indices)}):")
                for idx in indices:
                    print(f"   - {idx[1]}")
        
        # Mostrar relaciones entre tablas
        print(f"\n🔗 RELACIONES ENTRE TABLAS")
        print("=" * 50)
        
        print("📚 indicadores_academicos_base:")
        print("   └── institucion_id → instituciones_educativas(id)")
        
        print("💻 datos_competencia_digital:")
        print("   └── institucion_id → instituciones_educativas(id)")
        
        # Mostrar estadísticas de relaciones
        print(f"\n📊 ESTADÍSTICAS DE RELACIONES")
        print("=" * 50)
        
        # Verificar integridad referencial
        df_foreign_check = pd.read_sql_query("""
            SELECT 
                'indicadores_academicos_base' as tabla,
                COUNT(*) as total_registros,
                COUNT(CASE WHEN institucion_id IS NULL THEN 1 END) as registros_sin_institucion
            FROM indicadores_academicos_base
            UNION ALL
            SELECT 
                'datos_competencia_digital' as tabla,
                COUNT(*) as total_registros,
                COUNT(CASE WHEN institucion_id IS NULL THEN 1 END) as registros_sin_institucion
            FROM datos_competencia_digital
        """, conn)
        
        for _, row in df_foreign_check.iterrows():
            porcentaje = (row['registros_sin_institucion'] / row['total_registros']) * 100
            print(f"   {row['tabla']}:")
            print(f"      - Total registros: {row['total_registros']}")
            print(f"      - Sin institución: {row['registros_sin_institucion']} ({porcentaje:.1f}%)")
        
        # Mostrar tipos de datos únicos
        print(f"\n📋 TIPOS DE DATOS UTILIZADOS")
        print("=" * 50)
        
        tipos_unicos = set()
        for tabla in tablas:
            cursor.execute(f"PRAGMA table_info({tabla[0]})")
            columnas = cursor.fetchall()
            for col in columnas:
                tipos_unicos.add(col[2])
        
        for tipo in sorted(tipos_unicos):
            print(f"   - {tipo}")
        
        # Mostrar resumen de la estructura
        print(f"\n📋 RESUMEN DE LA ESTRUCTURA")
        print("=" * 50)
        
        total_columnas = 0
        for tabla in tablas:
            cursor.execute(f"PRAGMA table_info({tabla[0]})")
            columnas = cursor.fetchall()
            total_columnas += len(columnas)
        
        print(f"   📊 Tablas: {len(tablas)}")
        print(f"   📋 Columnas totales: {total_columnas}")
        print(f"   🔗 Relaciones: 2 (ambas hacia instituciones_educativas)")
        print(f"   🗄️ Tamaño de archivo: {Path(db_path).stat().st_size / (1024*1024):.2f} MB")
        
        conn.close()
        
        print(f"\n✅ ÁRBOL DE BASE DE DATOS COMPLETADO")
        print("=" * 70)
        
    except Exception as e:
        print(f"❌ Error mostrando árbol: {e}")

if __name__ == "__main__":
    mostrar_arbol_base_datos()
