#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Explorador de Fuentes de Datos - Proyecto Reasis
Script para explorar archivos Excel con información completa de instituciones
"""

import pandas as pd
import numpy as np
from pathlib import Path

def explorar_fuente_primaria():
    """Explora la fuente primaria de datos: Ruralidad, EIB y TOE.xlsx"""
    print("🔍 EXPLORADOR DE FUENTE PRIMARIA DE DATOS")
    print("=" * 70)
    
    archivo_path = Path("assets/Consultoria/Información actualizada/1. Ruralidad, EIB y TOE.xlsx")
    
    if not archivo_path.exists():
        print(f"❌ Archivo no encontrado: {archivo_path}")
        return
    
    try:
        # 1. EXPLORAR HOJA "DatosGlobales"
        print(f"\n📊 HOJA: DatosGlobales")
        print("-" * 50)
        
        df_datos_globales = pd.read_excel(archivo_path, sheet_name='DatosGlobales')
        
        print(f"📋 Información general:")
        print(f"   - Filas: {len(df_datos_globales)}")
        print(f"   - Columnas: {len(df_datos_globales.columns)}")
        print(f"   - Columnas disponibles: A hasta {chr(65 + len(df_datos_globales.columns) - 1)}")
        
        # Mostrar todas las columnas
        print(f"\n📋 COLUMNAS DISPONIBLES:")
        for i, col in enumerate(df_datos_globales.columns):
            print(f"   {i+1:2d}. {col}")
        
        # Mostrar primeras 10 filas con todas las columnas
        print(f"\n📋 PRIMERAS 10 FILAS (TODAS LAS COLUMNAS):")
        print("=" * 100)
        
        for i in range(min(10, len(df_datos_globales))):
            print(f"\n--- FILA {i+1} ---")
            row = df_datos_globales.iloc[i]
            for col in df_datos_globales.columns:
                valor = str(row[col]) if pd.notna(row[col]) else "N/A"
                print(f"   {col}: {valor}")
        
        # 2. EXPLORAR HOJA "Escuelas confirmadas FyA a Juli"
        print(f"\n📊 HOJA: Escuelas confirmadas FyA a Juli")
        print("-" * 50)
        
        df_escuelas_fya = pd.read_excel(archivo_path, sheet_name='Escuelas confirmadas FyA a Juli')
        
        print(f"📋 Información general:")
        print(f"   - Filas: {len(df_escuelas_fya)}")
        print(f"   - Columnas: {len(df_escuelas_fya.columns)}")
        print(f"   - Columnas disponibles: A hasta {chr(65 + len(df_escuelas_fya.columns) - 1)}")
        
        # Mostrar todas las columnas
        print(f"\n📋 COLUMNAS DISPONIBLES:")
        for i, col in enumerate(df_escuelas_fya.columns):
            print(f"   {i+1:2d}. {col}")
        
        # Mostrar primeras 10 filas con todas las columnas
        print(f"\n📋 PRIMERAS 10 FILAS (TODAS LAS COLUMNAS):")
        print("=" * 100)
        
        for i in range(min(10, len(df_escuelas_fya))):
            print(f"\n--- FILA {i+1} ---")
            row = df_escuelas_fya.iloc[i]
            for col in df_escuelas_fya.columns:
                valor = str(row[col]) if pd.notna(row[col]) else "N/A"
                print(f"   {col}: {valor}")
        
        # 3. ANÁLISIS DE CÓDIGOS
        print(f"\n🔍 ANÁLISIS DE CÓDIGOS IDENTIFICADOS")
        print("=" * 50)
        
        # Buscar columnas que contengan códigos
        columnas_codigo_datos_globales = [col for col in df_datos_globales.columns if 'cod' in col.lower()]
        columnas_codigo_escuelas_fya = [col for col in df_escuelas_fya.columns if 'cod' in col.lower()]
        
        print(f"📋 Columnas con códigos en DatosGlobales:")
        for col in columnas_codigo_datos_globales:
            print(f"   - {col}")
        
        print(f"\n📋 Columnas con códigos en Escuelas confirmadas FyA a Juli:")
        for col in columnas_codigo_escuelas_fya:
            print(f"   - {col}")
        
        # Verificar si hay códigos modulares
        if 'cod_mod' in df_datos_globales.columns:
            print(f"\n📊 Códigos modulares únicos en DatosGlobales: {df_datos_globales['cod_mod'].nunique()}")
            print(f"   Ejemplos: {df_datos_globales['cod_mod'].dropna().head().tolist()}")
        
        if 'codlocal' in df_datos_globales.columns:
            print(f"\n📊 Códigos locales únicos en DatosGlobales: {df_datos_globales['codlocal'].nunique()}")
            print(f"   Ejemplos: {df_datos_globales['codlocal'].dropna().head().tolist()}")
        
    except Exception as e:
        print(f"❌ Error explorando fuente primaria: {e}")

def explorar_fuente_secundaria():
    """Explora la fuente secundaria de datos: Código y Nombres de colegios.xlsx"""
    print("\n🔍 EXPLORADOR DE FUENTE SECUNDARIA DE DATOS")
    print("=" * 70)
    
    archivo_path = Path("assets/Consultoria/DatosLucas/Codigo y Nombres de colegios usados en los informes de matematica y comunicción y comeptentecias digitales.xlsx")
    
    if not archivo_path.exists():
        print(f"❌ Archivo no encontrado: {archivo_path}")
        return
    
    try:
        # EXPLORAR HOJA "colegios"
        print(f"\n📊 HOJA: colegios")
        print("-" * 50)
        
        df_colegios = pd.read_excel(archivo_path, sheet_name='colegios')
        
        print(f"📋 Información general:")
        print(f"   - Filas: {len(df_colegios)}")
        print(f"   - Columnas: {len(df_colegios.columns)}")
        
        # Mostrar todas las columnas
        print(f"\n📋 COLUMNAS DISPONIBLES:")
        for i, col in enumerate(df_colegios.columns):
            print(f"   {i+1:2d}. {col}")
        
        # Mostrar primeras 10 filas con todas las columnas
        print(f"\n📋 PRIMERAS 10 FILAS (TODAS LAS COLUMNAS):")
        print("=" * 100)
        
        for i in range(min(10, len(df_colegios))):
            print(f"\n--- FILA {i+1} ---")
            row = df_colegios.iloc[i]
            for col in df_colegios.columns:
                valor = str(row[col]) if pd.notna(row[col]) else "N/A"
                print(f"   {col}: {valor}")
        
        # Buscar columnas específicas mencionadas
        print(f"\n🔍 ANÁLISIS DE COLUMNAS ESPECÍFICAS")
        print("=" * 50)
        
        # Buscar columna "codigo local corregido"
        columnas_codigo_local = [col for col in df_colegios.columns if 'codigo' in col.lower() and 'local' in col.lower()]
        print(f"📋 Columnas con 'codigo local': {columnas_codigo_local}")
        
        # Buscar columna "Región a la que pertenece"
        columnas_region = [col for col in df_colegios.columns if 'region' in col.lower() or 'región' in col.lower()]
        print(f"📋 Columnas con 'región': {columnas_region}")
        
        # Mostrar valores únicos de regiones si existe
        if columnas_region:
            regiones_unicas = df_colegios[columnas_region[0]].dropna().unique()
            print(f"\n📊 Regiones únicas encontradas: {len(regiones_unicas)}")
            for region in regiones_unicas:
                print(f"   - {region}")
        
    except Exception as e:
        print(f"❌ Error explorando fuente secundaria: {e}")

def comparar_fuentes():
    """Compara las fuentes de datos para identificar la mejor"""
    print("\n🔍 COMPARACIÓN DE FUENTES DE DATOS")
    print("=" * 70)
    
    print(f"📊 EVALUACIÓN DE FUENTES:")
    print(f"   1. Fuente Primaria (Ruralidad, EIB y TOE.xlsx):")
    print(f"      ✅ Datos oficiales del MINEDU")
    print(f"      ✅ Códigos modulares y locales")
    print(f"      ✅ Información geográfica completa")
    print(f"      ✅ Datos de ruralidad y EIB")
    
    print(f"\n   2. Fuente Secundaria (Código y Nombres de colegios.xlsx):")
    print(f"      ⚠️ Datos procesados manualmente")
    print(f"      ✅ Códigos locales corregidos")
    print(f"      ✅ Información de regiones")
    print(f"      ⚠️ Posible duplicación de datos")
    
    print(f"\n💡 RECOMENDACIÓN:")
    print(f"   Usar la Fuente Primaria como 'fuente de verdad'")
    print(f"   y la Fuente Secundaria como validación/complemento")

def main():
    """Función principal"""
    print("🚀 EXPLORADOR DE FUENTES DE DATOS - PROYECTO REASIS")
    print("=" * 70)
    
    # Explorar fuente primaria
    explorar_fuente_primaria()
    
    # Explorar fuente secundaria
    explorar_fuente_secundaria()
    
    # Comparar fuentes
    comparar_fuentes()
    
    print(f"\n✅ EXPLORACIÓN DE FUENTES COMPLETADA")
    print("=" * 70)

if __name__ == "__main__":
    main()
