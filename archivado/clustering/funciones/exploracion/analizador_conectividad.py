#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ANALIZADOR DE CONECTIVIDAD - Proyecto Reasis

Analiza los datos de la tabla 'conectividad_equipamiento' para
obtener insights sobre la velocidad de internet y su distribución por red.
"""

import pandas as pd
import sqlite3

def analizar_velocidad_internet():
    """Analiza la velocidad de internet por institución y por red."""
    print("=== ANÁLISIS DE VELOCIDAD DE INTERNET POR RED ===\n")
    
    conn = sqlite3.connect('reasis_database.db')
    
    # Query para obtener datos de velocidad, uniéndolos con nombres de institución y red
    query = """
    SELECT
        rf.lugar as red,
        ce.cul_es_la_velocidad_de_internet_de_bajada_en_mbps as velocidad_bajada
    FROM conectividad_equipamiento ce
    LEFT JOIN instituciones_educativas ie ON ce.codigo_modular = ie.codigo_modular
    LEFT JOIN redes_fe_y_alegria rf ON ie.codigo_red = rf.codigo_red
    WHERE ce.cul_es_la_velocidad_de_internet_de_bajada_en_mbps IS NOT NULL
    AND rf.lugar IS NOT NULL
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    # Limpieza de datos: convertir a numérico, manejar errores y eliminar nulos
    df['velocidad_bajada'] = pd.to_numeric(df['velocidad_bajada'], errors='coerce')
    df.dropna(subset=['velocidad_bajada'], inplace=True)
    
    # Calcular y mostrar el promedio de velocidad de bajada por red
    promedio_por_red = df.groupby('red')['velocidad_bajada'].mean().sort_values(ascending=False).reset_index()
    promedio_por_red.rename(columns={'velocidad_bajada': 'velocidad_promedio_bajada_mbps'}, inplace=True)
    
    print("Velocidad de bajada promedio por Red (Mbps):")
    print(promedio_por_red.to_string(index=False))

if __name__ == "__main__":
    analizar_velocidad_internet()

