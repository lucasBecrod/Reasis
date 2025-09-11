#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Explorador Simple de Datos - Proyecto Reasis
Versión simplificada que muestra resultados sin problemas de JSON
"""

import os
import pandas as pd
from pathlib import Path

def explorar_datos():
    """Explora todos los archivos Excel y muestra un resumen"""
    print("🚀 EXPLORADOR SIMPLE DE DATOS - PROYECTO REASIS")
    print("=" * 70)
    
    base_path = Path("assets/Consultoria")
    excel_files = []
    
    # Buscar archivos Excel
    for root, dirs, files in os.walk(base_path):
        for file in files:
            if file.endswith(('.xlsx', '.xls')):
                full_path = Path(root) / file
                excel_files.append(full_path)
    
    print(f"📁 Encontrados {len(excel_files)} archivos Excel:")
    print("-" * 50)
    
    # Agrupar por carpetas
    archivos_por_carpeta = {}
    for file in excel_files:
        carpeta = file.parent.name
        if carpeta not in archivos_por_carpeta:
            archivos_por_carpeta[carpeta] = []
        archivos_por_carpeta[carpeta].append(file.name)
    
    for carpeta, archivos in archivos_por_carpeta.items():
        print(f"\n📂 {carpeta}:")
        for archivo in archivos:
            print(f"   - {archivo}")
    
    # Analizar archivos principales
    print(f"\n🔍 ANALIZANDO ARCHIVOS PRINCIPALES:")
    print("=" * 50)
    
    archivos_principales = [
        "DatosLucas/Matematica y Comunicación/BD1- Matemática 2024.xlsx",
        "DatosLucas/Matematica y Comunicación/BD2- Comunicación 2024.xlsx", 
        "DatosLucas/Matematica y Comunicación/BD3 - Producción de textos 2024.xlsx",
        "DatosLucas/Competencias Digitales Estudiantes/BD1 - 2024 Competencias Digitales - Estudiantes.xlsx",
        "DatosLucas/Competencias Digitales Docentes/02 Base de datos Informe Docentes Digital  2025 - RER Rural.xlsx",
        "Información actualizada/1. Ruralidad, EIB y TOE.xlsx",
        "Información actualizada/4. Conectividad y equipamiento.xlsx"
    ]
    
    todas_las_columnas = set()
    
    for archivo_relativo in archivos_principales:
        archivo_path = base_path / archivo_relativo
        if archivo_path.exists():
            try:
                print(f"\n📊 {archivo_path.name}:")
                excel_file = pd.ExcelFile(archivo_path)
                
                for hoja in excel_file.sheet_names:
                    try:
                        df = pd.read_excel(archivo_path, sheet_name=hoja, nrows=3)
                        columnas = [str(col) for col in df.columns]
                        todas_las_columnas.update(columnas)
                        
                        print(f"   📋 {hoja}: {len(columnas)} columnas")
                        if len(columnas) <= 10:  # Mostrar columnas si son pocas
                            print(f"      Columnas: {', '.join(columnas[:5])}{'...' if len(columnas) > 5 else ''}")
                            
                    except Exception as e:
                        print(f"   ❌ Error en hoja '{hoja}': {e}")
                        
            except Exception as e:
                print(f"❌ Error analizando {archivo_path.name}: {e}")
    
    # Mostrar columnas importantes
    print(f"\n🎯 COLUMNAS IMPORTANTES ENCONTRADAS:")
    print("=" * 50)
    
    palabras_clave = [
        'institucion', 'escuela', 'colegio', 'codigo', 'nombre',
        'docente', 'estudiante', 'alumno', 'profesor',
        'rural', 'urbano', 'eib', 'intercultural',
        'conectividad', 'internet', 'equipamiento', 'computadora',
        'rendimiento', 'academico', 'nota', 'calificacion',
        'red', 'region', 'provincia', 'distrito',
        'padd', 'competencia', 'digital', 'matematica', 'comunicacion'
    ]
    
    columnas_importantes = []
    for columna in todas_las_columnas:
        columna_lower = columna.lower()
        for palabra in palabras_clave:
            if palabra in columna_lower:
                columnas_importantes.append(columna)
                break
    
    print(f"Total de columnas únicas encontradas: {len(todas_las_columnas)}")
    print(f"Columnas relevantes identificadas: {len(set(columnas_importantes))}")
    print("\nColumnas más importantes:")
    for col in sorted(set(columnas_importantes))[:20]:  # Mostrar solo las primeras 20
        print(f"   - {col}")
    
    print(f"\n✅ EXPLORACIÓN COMPLETADA")
    print("=" * 70)
    print("📝 PRÓXIMOS PASOS:")
    print("   1. Revisar las columnas identificadas")
    print("   2. Crear mapeo a la estructura de base de datos")
    print("   3. Crear script de consolidación")
    print("   4. Generar base de datos SQLite")

if __name__ == "__main__":
    explorar_datos()
