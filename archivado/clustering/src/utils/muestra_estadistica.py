#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Muestra Estadística - Proyecto Reasis
Script para calcular y mostrar una muestra aleatoria significativa de datos
"""

import sqlite3
import pandas as pd
import numpy as np
import math
from pathlib import Path

def calcular_tamaño_muestra(poblacion_total, nivel_confianza=0.95, margen_error=0.05, proporcion_esperada=0.5):
    """
    Calcula el tamaño de muestra usando la fórmula estadística
    
    Parámetros:
    - poblacion_total: Tamaño total de la población
    - nivel_confianza: Nivel de confianza (0.95 = 95%)
    - margen_error: Margen de error aceptable (0.05 = 5%)
    - proporcion_esperada: Proporción esperada (0.5 = 50% si no se conoce)
    
    Retorna:
    - Tamaño de muestra calculado
    """
    
    # Valor Z para el nivel de confianza
    if nivel_confianza == 0.95:
        Z = 1.96
    elif nivel_confianza == 0.99:
        Z = 2.576
    elif nivel_confianza == 0.90:
        Z = 1.645
    else:
        Z = 1.96  # Por defecto 95%
    
    # Fórmula: n = (Z^2 * p * (1-p)) / E^2
    numerador = (Z ** 2) * proporcion_esperada * (1 - proporcion_esperada)
    denominador = margen_error ** 2
    n = numerador / denominador
    
    # Corrección para población finita
    if poblacion_total < 100000:  # Si la población es relativamente pequeña
        n_corregida = n / (1 + (n - 1) / poblacion_total)
        n = n_corregida
    
    # Agregar margen de seguridad (10%)
    n_con_seguridad = n * 1.1
    
    return int(round(n_con_seguridad))

def mostrar_muestra_instituciones():
    """Muestra una muestra aleatoria significativa de instituciones_educativas"""
    print("📊 MUESTRA ESTADÍSTICA - INSTITUCIONES EDUCATIVAS")
    print("=" * 70)
    
    db_path = "reasis_database.db"
    
    if not Path(db_path).exists():
        print(f"❌ Base de datos no encontrada: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        
        # 1. OBTENER POBLACIÓN TOTAL
        df_poblacion = pd.read_sql_query("SELECT COUNT(*) as total FROM instituciones_educativas", conn)
        poblacion_total = df_poblacion.iloc[0]['total']
        
        print(f"📈 POBLACIÓN TOTAL: {poblacion_total} instituciones")
        print("=" * 50)
        
        # 2. CALCULAR TAMAÑO DE MUESTRA
        print("\n🧮 CÁLCULO DE TAMAÑO DE MUESTRA")
        print("-" * 40)
        
        # Parámetros de la muestra
        nivel_confianza = 0.95  # 95%
        margen_error = 0.05     # 5%
        proporcion_esperada = 0.5  # 50%
        
        tamaño_muestra = calcular_tamaño_muestra(
            poblacion_total=poblacion_total,
            nivel_confianza=nivel_confianza,
            margen_error=margen_error,
            proporcion_esperada=proporcion_esperada
        )
        
        print(f"   📊 Parámetros utilizados:")
        print(f"      - Nivel de confianza: {nivel_confianza*100}%")
        print(f"      - Margen de error: {margen_error*100}%")
        print(f"      - Proporción esperada: {proporcion_esperada*100}%")
        print(f"      - Población total: {poblacion_total}")
        print(f"   🎯 Tamaño de muestra calculado: {tamaño_muestra}")
        print(f"   📈 Porcentaje de la población: {(tamaño_muestra/poblacion_total)*100:.1f}%")
        
        # 3. OBTENER MUESTRA ALEATORIA
        print(f"\n🎲 OBTENIENDO MUESTRA ALEATORIA")
        print("-" * 40)
        
        # Usar RANDOM() de SQLite para obtener muestra aleatoria
        query_muestra = f"""
            SELECT * FROM instituciones_educativas 
            ORDER BY RANDOM() 
            LIMIT {tamaño_muestra}
        """
        
        df_muestra = pd.read_sql_query(query_muestra, conn)
        
        print(f"   ✅ Muestra obtenida: {len(df_muestra)} registros")
        
        # 4. MOSTRAR MUESTRA
        print(f"\n📋 MUESTRA ALEATORIA DE INSTITUCIONES")
        print("=" * 70)
        
        for i, (index, row) in enumerate(df_muestra.iterrows(), 1):
            nombre = row['nombre_institucion'] if row['nombre_institucion'] else row['nombre_rer']
            print(f"{i:3d}. ID: {row['id']:3d} | Nombre: {nombre:<50} | Año: {row['año']} | Ámbito: {row['ambito']}")
        
        # 5. ANÁLISIS DE LA MUESTRA
        print(f"\n📊 ANÁLISIS DE LA MUESTRA")
        print("=" * 50)
        
        # Distribución por año
        print(f"\n📅 Distribución por año:")
        df_años = df_muestra.groupby('año').size().reset_index(name='cantidad')
        for _, row in df_años.iterrows():
            porcentaje = (row['cantidad'] / len(df_muestra)) * 100
            print(f"   - {row['año']}: {row['cantidad']} instituciones ({porcentaje:.1f}%)")
        
        # Distribución por ámbito
        print(f"\n🌍 Distribución por ámbito:")
        df_ambitos = df_muestra.groupby('ambito').size().reset_index(name='cantidad')
        for _, row in df_ambitos.iterrows():
            porcentaje = (row['cantidad'] / len(df_muestra)) * 100
            print(f"   - {row['ambito']}: {row['cantidad']} instituciones ({porcentaje:.1f}%)")
        
        # Tipos de instituciones
        print(f"\n🏫 Tipos de instituciones:")
        instituciones_con_nombre = df_muestra[df_muestra['nombre_institucion'].notna() & (df_muestra['nombre_institucion'] != '')]
        instituciones_con_rer = df_muestra[df_muestra['nombre_rer'].notna() & (df_muestra['nombre_rer'] != '')]
        
        print(f"   - Con nombre_institucion: {len(instituciones_con_nombre)} ({len(instituciones_con_nombre)/len(df_muestra)*100:.1f}%)")
        print(f"   - Con nombre_rer: {len(instituciones_con_rer)} ({len(instituciones_con_rer)/len(df_muestra)*100:.1f}%)")
        
        # 6. EVALUACIÓN DE LA ESTRUCTURA ACTUAL
        print(f"\n🔍 EVALUACIÓN DE LA ESTRUCTURA ACTUAL")
        print("=" * 50)
        
        print(f"📋 PROBLEMAS IDENTIFICADOS:")
        print(f"   1. Campo 'nombre_institucion' vacío en {(len(df_muestra) - len(instituciones_con_nombre))/len(df_muestra)*100:.1f}% de casos")
        print(f"   2. Campo 'nombre_rer' vacío en {(len(df_muestra) - len(instituciones_con_rer))/len(df_muestra)*100:.1f}% de casos")
        print(f"   3. Campo 'ambito' vacío en {df_muestra['ambito'].isna().sum()/len(df_muestra)*100:.1f}% de casos")
        
        # 7. SUGERENCIAS PARA VERSIÓN 2.0
        print(f"\n💡 SUGERENCIAS PARA VERSIÓN 2.0")
        print("=" * 50)
        
        print(f"🏗️ MEJORAS EN LA ESTRUCTURA:")
        print(f"   1. Unificar campos de nombre:")
        print(f"      - Crear campo 'nombre' único")
        print(f"      - Agregar campo 'tipo_institucion' (RER, IE, etc.)")
        print(f"      - Agregar campo 'codigo_institucion'")
        
        print(f"   2. Mejorar geografía:")
        print(f"      - Agregar campos: 'region', 'provincia', 'distrito'")
        print(f"      - Agregar campo 'coordenadas' (latitud, longitud)")
        
        print(f"   3. Mejorar temporalidad:")
        print(f"      - Agregar campo 'fecha_inicio_operaciones'")
        print(f"      - Agregar campo 'estado' (activa, inactiva, etc.)")
        
        print(f"   4. Agregar metadatos:")
        print(f"      - Campo 'fuente_datos'")
        print(f"      - Campo 'ultima_actualizacion'")
        print(f"      - Campo 'usuario_actualizacion'")
        
        # 8. NUEVA ESTRUCTURA SUGERIDA
        print(f"\n📋 NUEVA ESTRUCTURA SUGERIDA (V2.0)")
        print("=" * 50)
        
        print(f"""
CREATE TABLE instituciones_educativas_v2 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo_institucion TEXT UNIQUE NOT NULL,
    nombre TEXT NOT NULL,
    tipo_institucion TEXT NOT NULL,  -- 'RER', 'IE', 'CEBA', etc.
    ambito TEXT NOT NULL,           -- 'Rural', 'Urbano'
    region TEXT,
    provincia TEXT,
    distrito TEXT,
    latitud REAL,
    longitud REAL,
    fecha_inicio_operaciones DATE,
    estado TEXT DEFAULT 'Activa',   -- 'Activa', 'Inactiva', 'En construcción'
    fuente_datos TEXT,
    ultima_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    usuario_actualizacion TEXT
);
        """)
        
        conn.close()
        
        print(f"\n✅ ANÁLISIS DE MUESTRA COMPLETADO")
        print("=" * 70)
        print(f"💡 La muestra de {tamaño_muestra} instituciones representa")
        print(f"   el {(tamaño_muestra/poblacion_total)*100:.1f}% de la población total")
        print(f"   con un nivel de confianza del {nivel_confianza*100}%")
        print(f"   y un margen de error del {margen_error*100}%")
        
    except Exception as e:
        print(f"❌ Error en análisis de muestra: {e}")

if __name__ == "__main__":
    mostrar_muestra_instituciones()
