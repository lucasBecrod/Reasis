#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Explorador de Estructura - Proyecto Reasis
Script para explorar la estructura real de los archivos Excel
"""

import pandas as pd
from pathlib import Path

def explorar_estructura():
    """Explora la estructura real de los archivos Excel"""
    print("🔍 EXPLORADOR DE ESTRUCTURA - PROYECTO REASIS")
    print("=" * 60)
    
    base_path = Path("assets/Consultoria")
    
    # Archivos principales a explorar
    archivos_principales = [
        "DatosLucas/Matematica y Comunicación/BD1- Matemática 2024.xlsx",
        "DatosLucas/Matematica y Comunicación/BD2- Comunicación 2024.xlsx",
        "DatosLucas/Matematica y Comunicación/BD3 - Producción de textos 2024.xlsx",
        "DatosLucas/Competencias Digitales Estudiantes/BD1 - 2024 Competencias Digitales - Estudiantes.xlsx",
        "DatosLucas/Competencias Digitales Docentes/02 Base de datos Informe Docentes Digital  2025 - RER Rural.xlsx"
    ]
    
    for archivo_relativo in archivos_principales:
        archivo_path = base_path / archivo_relativo
        if not archivo_path.exists():
            continue
            
        print(f"\n📊 ANALIZANDO: {archivo_path.name}")
        print("-" * 50)
        
        try:
            # Leer todas las hojas del archivo
            excel_file = pd.ExcelFile(archivo_path)
            
            for hoja in excel_file.sheet_names:
                print(f"\n📋 Hoja: {hoja}")
                
                # Leer las primeras filas para ver la estructura
                df = pd.read_excel(archivo_path, sheet_name=hoja, nrows=3)
                
                print(f"   Columnas encontradas ({len(df.columns)}):")
                for i, col in enumerate(df.columns):
                    print(f"   {i+1:2d}. {col}")
                
                # Mostrar algunas filas de ejemplo
                print(f"\n   Primeras filas de datos:")
                for i in range(min(2, len(df))):
                    print(f"   Fila {i+1}: {dict(df.iloc[i].head(5))}")
                    
        except Exception as e:
            print(f"❌ Error analizando {archivo_path.name}: {e}")
    
    print(f"\n✅ EXPLORACIÓN DE ESTRUCTURA COMPLETADA")
    print("=" * 60)

if __name__ == "__main__":
    explorar_estructura()
