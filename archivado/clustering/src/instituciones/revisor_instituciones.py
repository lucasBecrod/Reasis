#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Revisor de Instituciones Educativas - Proyecto Reasis
Script para revisar y analizar la calidad de datos en la tabla de instituciones educativas
"""

import sqlite3
import pandas as pd
from pathlib import Path

def revisar_tabla_instituciones():
    """Revisa la tabla de instituciones educativas más reciente"""
    print("REVISOR DE INSTITUCIONES EDUCATIVAS - TABLA V2 MEJORADA")
    print("=" * 80)
    
    db_path = "reasis_database.db"
    
    if not Path(db_path).exists():
        print(f"Error: Base de datos no encontrada: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        
        # Verificar estructura de la tabla
        print("\n1. ESTRUCTURA DE LA TABLA")
        print("=" * 50)
        
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(instituciones_educativas_v2_mejorada)")
        columns = cursor.fetchall()
        
        print("Columnas disponibles:")
        for col in columns:
            print(f"   - {col[1]} ({col[2]}) {'NOT NULL' if col[3] else 'NULL'}")
        
        # Contar registros totales
        cursor.execute("SELECT COUNT(*) FROM instituciones_educativas_v2_mejorada")
        total_registros = cursor.fetchone()[0]
        print(f"\nTotal de registros: {total_registros}")
        
        # Muestra de datos completos
        print("\n2. MUESTRA DE DATOS (primeras 15 filas)")
        print("=" * 80)
        
        df_muestra = pd.read_sql_query("""
            SELECT * FROM instituciones_educativas_v2_mejorada 
            ORDER BY id 
            LIMIT 15
        """, conn)
        
        for i, row in df_muestra.iterrows():
            print(f"\n--- FILA {i+1} ---")
            print(f"   ID: {row['id']}")
            print(f"   Codigo Modular: {row['codigo_modular']}")
            print(f"   Codigo Local: {row['codigo_local']}")
            print(f"   Nombre: {row['nombre_institucion']}")
            print(f"   Tipo: {row['tipo_institucion']}")
            print(f"   Region: {row['region']}")
            print(f"   Es FyA: {row['es_fya']}")
            print(f"   Es Rural: {row['es_rural']}")
            print(f"   Modalidad: {row.get('modalidad_especifica', 'N/A')}")
            print(f"   Area Censo: {row.get('area_censo', 'N/A')}")
            if 'latitud' in row and 'longitud' in row:
                print(f"   Coordenadas: ({row['latitud']}, {row['longitud']})")
        
        # Análisis de calidad de datos
        print("\n3. ANALISIS DE CALIDAD DE DATOS")
        print("=" * 50)
        
        # Campos obligatorios
        campos_check = [
            'codigo_modular', 'nombre_institucion', 'tipo_institucion', 
            'region', 'es_fya', 'es_rural'
        ]
        
        for campo in campos_check:
            if campo in df_muestra.columns:
                nulos = df_muestra[campo].isnull().sum()
                vacios = (df_muestra[campo] == '').sum() if df_muestra[campo].dtype == 'object' else 0
                print(f"   {campo}: {nulos} nulos, {vacios} vacios")
        
        # Distribución por región
        print("\n4. DISTRIBUCION POR REGION")
        print("=" * 50)
        
        df_regiones = pd.read_sql_query("""
            SELECT region, COUNT(*) as total
            FROM instituciones_educativas_v2_mejorada 
            GROUP BY region
            ORDER BY total DESC
            LIMIT 10
        """, conn)
        
        for _, row in df_regiones.iterrows():
            print(f"   - {row['region']}: {row['total']} instituciones")
        
        # Distribución rural/urbano
        print("\n5. DISTRIBUCION RURAL/URBANO")
        print("=" * 50)
        
        df_rural = pd.read_sql_query("""
            SELECT es_rural, COUNT(*) as total
            FROM instituciones_educativas_v2_mejorada 
            GROUP BY es_rural
        """, conn)
        
        for _, row in df_rural.iterrows():
            tipo = "Rural" if row['es_rural'] == 1 else "Urbano"
            print(f"   - {tipo}: {row['total']} instituciones")
        
        # Distribución Fe y Alegría
        print("\n6. DISTRIBUCION FE Y ALEGRIA")
        print("=" * 50)
        
        df_fya = pd.read_sql_query("""
            SELECT es_fya, COUNT(*) as total
            FROM instituciones_educativas_v2_mejorada 
            GROUP BY es_fya
        """, conn)
        
        for _, row in df_fya.iterrows():
            tipo = "Fe y Alegría" if row['es_fya'] == 1 else "No Fe y Alegría"
            print(f"   - {tipo}: {row['total']} instituciones")
        
        # Verificar duplicados por código modular
        print("\n7. VERIFICACION DE DUPLICADOS")
        print("=" * 50)
        
        df_duplicados = pd.read_sql_query("""
            SELECT codigo_modular, COUNT(*) as total
            FROM instituciones_educativas_v2_mejorada 
            GROUP BY codigo_modular
            HAVING COUNT(*) > 1
            ORDER BY total DESC
        """, conn)
        
        if len(df_duplicados) > 0:
            print(f"   ALERTA: {len(df_duplicados)} códigos modulares duplicados:")
            for _, row in df_duplicados.head(10).iterrows():
                print(f"   - Código {row['codigo_modular']}: {row['total']} repeticiones")
        else:
            print("   ✓ No se encontraron duplicados por código modular")
        
        conn.close()
        
        print(f"\n✓ REVISION COMPLETADA")
        print("=" * 80)
        
    except Exception as e:
        print(f"Error durante la revisión: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    revisar_tabla_instituciones()