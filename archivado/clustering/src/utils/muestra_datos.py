#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Muestra de Datos - Proyecto Reasis
Script para mostrar una muestra de los datos de cada tabla
"""

import sqlite3
import pandas as pd
from pathlib import Path

def mostrar_muestra_datos():
    """Muestra una muestra de los datos de cada tabla"""
    print("📊 MUESTRA DE DATOS - PROYECTO REASIS")
    print("=" * 70)
    
    db_path = "reasis_database.db"
    
    if not Path(db_path).exists():
        print(f"❌ Base de datos no encontrada: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        
        # 1. MUESTRA DE INSTITUCIONES EDUCATIVAS
        print("\n🏫 TABLA: instituciones_educativas")
        print("=" * 50)
        
        df_instituciones = pd.read_sql_query("""
            SELECT * FROM instituciones_educativas 
            ORDER BY id 
            LIMIT 10
        """, conn)
        
        print(f"📋 Total de registros: {len(df_instituciones)} (mostrando 10)")
        print("\n📊 Muestra de datos:")
        for i, row in df_instituciones.iterrows():
            nombre = row['nombre_institucion'] if row['nombre_institucion'] else row['nombre_rer']
            print(f"   {i+1:2d}. ID: {row['id']:3d} | Nombre: {nombre} | Año: {row['año']} | Ámbito: {row['ambito']}")
        
        # 2. MUESTRA DE DATOS ACADÉMICOS
        print("\n📚 TABLA: indicadores_academicos_base")
        print("=" * 50)
        
        df_academicos = pd.read_sql_query("""
            SELECT iab.*, ie.nombre_institucion, ie.nombre_rer 
            FROM indicadores_academicos_base iab
            LEFT JOIN instituciones_educativas ie ON iab.institucion_id = ie.id
            ORDER BY iab.id 
            LIMIT 10
        """, conn)
        
        print(f"📋 Total de registros: {len(df_academicos)} (mostrando 10)")
        print("\n📊 Muestra de datos:")
        for i, row in df_academicos.iterrows():
            nombre = row['nombre_institucion'] if row['nombre_institucion'] else row['nombre_rer']
            print(f"   {i+1:2d}. ID: {row['id']:3d} | Institución: {nombre} | Materia: {row['materia']} | Nivel: {row['nivel_educativo']} | Grado: {row['grado']}")
        
        # 3. MUESTRA DE DATOS DE COMPETENCIA DIGITAL
        print("\n💻 TABLA: datos_competencia_digital")
        print("=" * 50)
        
        df_competencia = pd.read_sql_query("""
            SELECT dcd.*, ie.nombre_institucion, ie.nombre_rer 
            FROM datos_competencia_digital dcd
            LEFT JOIN instituciones_educativas ie ON dcd.institucion_id = ie.id
            ORDER BY dcd.id 
            LIMIT 10
        """, conn)
        
        print(f"📋 Total de registros: {len(df_competencia)} (mostrando 10)")
        print("\n📊 Muestra de datos:")
        for i, row in df_competencia.iterrows():
            nombre = row['nombre_institucion'] if row['nombre_institucion'] else row['nombre_rer']
            pregunta_corta = row['pregunta'][:50] + "..." if len(row['pregunta']) > 50 else row['pregunta']
            respuesta_corta = row['respuesta'][:30] + "..." if len(str(row['respuesta'])) > 30 else str(row['respuesta'])
            print(f"   {i+1:2d}. ID: {row['id']:3d} | Institución: {nombre} | Tipo: {row['tipo_encuesta']} | Pregunta: {pregunta_corta} | Respuesta: {respuesta_corta}")
        
        # 4. ESTADÍSTICAS DETALLADAS
        print("\n📈 ESTADÍSTICAS DETALLADAS")
        print("=" * 50)
        
        # Estadísticas por materia
        print("\n📚 Datos académicos por materia:")
        df_materias = pd.read_sql_query("""
            SELECT materia, COUNT(*) as total
            FROM indicadores_academicos_base 
            GROUP BY materia
            ORDER BY total DESC
        """, conn)
        
        for _, row in df_materias.iterrows():
            print(f"   - {row['materia']}: {row['total']} registros")
        
        # Estadísticas por tipo de encuesta
        print("\n💻 Datos de competencia digital por tipo:")
        df_tipos = pd.read_sql_query("""
            SELECT tipo_encuesta, COUNT(*) as total
            FROM datos_competencia_digital 
            GROUP BY tipo_encuesta
            ORDER BY total DESC
        """, conn)
        
        for _, row in df_tipos.iterrows():
            print(f"   - {row['tipo_encuesta']}: {row['total']} registros")
        
        # Instituciones únicas
        print("\n🏫 Instituciones únicas:")
        df_inst_unicas = pd.read_sql_query("""
            SELECT COUNT(DISTINCT COALESCE(nombre_institucion, nombre_rer)) as total_instituciones
            FROM instituciones_educativas
        """, conn)
        
        print(f"   - Total instituciones únicas: {df_inst_unicas.iloc[0]['total_instituciones']}")
        
        # Años disponibles
        print("\n📅 Años disponibles:")
        df_años = pd.read_sql_query("""
            SELECT DISTINCT año 
            FROM instituciones_educativas 
            ORDER BY año
        """, conn)
        
        años = [str(row['año']) for _, row in df_años.iterrows()]
        print(f"   - Años: {', '.join(años)}")
        
        conn.close()
        
        print(f"\n✅ MUESTRA DE DATOS COMPLETADA")
        print("=" * 70)
        print("💡 Los datos están listos para análisis estadístico")
        
    except Exception as e:
        print(f"❌ Error mostrando datos: {e}")

if __name__ == "__main__":
    mostrar_muestra_datos()
