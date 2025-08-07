#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Explorador de Base de Datos - Proyecto Reasis
Script para explorar y mostrar el contenido de la base de datos SQLite
"""

import sqlite3
import pandas as pd
from pathlib import Path

def explorar_base_datos():
    """Explora la base de datos SQLite"""
    print("🔍 EXPLORADOR DE BASE DE DATOS - PROYECTO REASIS")
    print("=" * 60)
    
    db_path = "reasis_database.db"
    
    if not Path(db_path).exists():
        print(f"❌ Base de datos no encontrada: {db_path}")
        print("💡 Ejecuta primero el consolidador de datos")
        return
    
    # Mostrar información del archivo
    file_size = Path(db_path).stat().st_size / (1024 * 1024)  # MB
    print(f"📄 Base de datos: {db_path}")
    print(f"📊 Tamaño: {file_size:.2f} MB")
    
    try:
        conn = sqlite3.connect(db_path)
        
        # Obtener lista de tablas
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tablas = cursor.fetchall()
        
        print(f"\n📋 TABLAS ENCONTRADAS ({len(tablas)}):")
        print("-" * 50)
        
        for tabla in tablas:
            nombre_tabla = tabla[0]
            print(f"\n🏷️ Tabla: {nombre_tabla}")
            
            # Contar registros
            cursor.execute(f"SELECT COUNT(*) FROM {nombre_tabla}")
            count = cursor.fetchone()[0]
            print(f"   📊 Registros: {count}")
            
            # Mostrar estructura de columnas
            cursor.execute(f"PRAGMA table_info({nombre_tabla})")
            columnas = cursor.fetchall()
            print(f"   📋 Columnas ({len(columnas)}):")
            for col in columnas:
                print(f"      - {col[1]} ({col[2]})")
            
            # Mostrar algunos datos de ejemplo
            if count > 0:
                print(f"   📋 Ejemplos de datos:")
                df_ejemplo = pd.read_sql_query(f"SELECT * FROM {nombre_tabla} LIMIT 3", conn)
                for i, row in df_ejemplo.iterrows():
                    print(f"      Fila {i+1}: {dict(row)}")
        
        # Mostrar estadísticas generales
        print(f"\n📊 ESTADÍSTICAS GENERALES:")
        print("-" * 50)
        
        total_registros = 0
        for tabla in tablas:
            cursor.execute(f"SELECT COUNT(*) FROM {tabla[0]}")
            count = cursor.fetchone()[0]
            total_registros += count
            print(f"   {tabla[0]}: {count} registros")
        
        print(f"\n✅ Total de registros: {total_registros}")
        
        # Mostrar consultas útiles
        print(f"\n🔍 CONSULTAS ÚTILES:")
        print("-" * 50)
        
        # Consulta 1: Instituciones únicas
        cursor.execute("SELECT COUNT(DISTINCT nombre_rer) FROM instituciones_educativas WHERE nombre_rer IS NOT NULL")
        rer_count = cursor.fetchone()[0]
        print(f"   📚 RERs únicas: {rer_count}")
        
        # Consulta 2: Años disponibles
        cursor.execute("SELECT DISTINCT año FROM instituciones_educativas ORDER BY año")
        años = cursor.fetchall()
        print(f"   📅 Años disponibles: {[año[0] for año in años]}")
        
        # Consulta 3: Tipos de encuesta
        cursor.execute("SELECT DISTINCT tipo_encuesta FROM datos_competencia_digital")
        tipos = cursor.fetchall()
        print(f"   📝 Tipos de encuesta: {[tipo[0] for tipo in tipos]}")
        
        conn.close()
        
        print(f"\n✅ EXPLORACIÓN COMPLETADA")
        print("=" * 60)
        print("💡 Próximos pasos:")
        print("   1. Revisar la calidad de los datos")
        print("   2. Crear análisis estadístico")
        print("   3. Generar visualizaciones")
        print("   4. Crear informe automatizado")
        
    except Exception as e:
        print(f"❌ Error explorando base de datos: {e}")

if __name__ == "__main__":
    explorar_base_datos()
