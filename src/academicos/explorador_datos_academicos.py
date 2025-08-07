#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Explorador de Datos Académicos - Proyecto Reasis
Script para explorar las tablas DATA de archivos de Matemática y Comunicación
"""

import pandas as pd
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

def explorar_datos_academicos():
    """Explora las tablas DATA de los archivos de datos académicos"""
    print("EXPLORADOR DE DATOS ACADEMICOS - TABLAS DATA")
    print("=" * 80)
    
    # Rutas de los archivos
    base_path = Path("assets/Consultoria/DatosLucas/Matematica y Comunicación")
    archivos = {
        "Matemática": base_path / "BD1- Matemática 2024.xlsx",
        "Comunicación": base_path / "BD2- Comunicación 2024.xlsx", 
        "Producción de textos": base_path / "BD3 - Producción de textos 2024.xlsx"
    }
    
    for materia, archivo in archivos.items():
        print(f"\n{'='*20} {materia.upper()} {'='*20}")
        print(f"Archivo: {archivo.name}")
        
        try:
            # Leer la hoja DATA
            df = pd.read_excel(archivo, sheet_name='DATA')
            
            print(f"\nINFORMACIÓN GENERAL:")
            print(f"  Total filas: {len(df)}")
            print(f"  Total columnas: {len(df.columns)}")
            
            print(f"\nCOLUMNAS DISPONIBLES:")
            for i, col in enumerate(df.columns, 1):
                print(f"  {i:2d}. {col}")
            
            print(f"\nPRIMERAS 10 FILAS:")
            print("-" * 80)
            
            # Mostrar las primeras 10 filas de manera detallada
            for i in range(min(10, len(df))):
                print(f"\n--- FILA {i+1} ---")
                for col in df.columns:
                    value = df.iloc[i][col]
                    # Truncar valores muy largos
                    if isinstance(value, str) and len(value) > 50:
                        value = value[:47] + "..."
                    print(f"  {col}: {value}")
            
            # Análisis específico de la columna de resultados
            print(f"\nANÁLISIS DE COLUMNA DE RESULTADOS:")
            print("-" * 50)
            
            # Buscar la columna de resultados según el patrón mencionado
            col_resultado = None
            patrones_resultado = [f'R {materia}', f'R{materia}', 'Resultado', 'Nivel de logro', 'Logro']
            
            for patron in patrones_resultado:
                cols_matches = [col for col in df.columns if patron.lower() in col.lower()]
                if cols_matches:
                    col_resultado = cols_matches[0]
                    break
            
            if col_resultado:
                print(f"Columna de resultados identificada: '{col_resultado}'")
                
                # Análisis de valores únicos
                valores_unicos = df[col_resultado].value_counts().sort_index()
                print(f"\nValores únicos en '{col_resultado}':")
                for valor, count in valores_unicos.items():
                    percentage = (count / len(df)) * 100
                    print(f"  '{valor}': {count} casos ({percentage:.1f}%)")
                
                # Propuesta de codificación numérica
                print(f"\nPROPUESTA DE CODIFICACIÓN NUMÉRICA:")
                codificacion_propuesta = {
                    'Inicio': 1,
                    'Proceso': 2, 
                    'Satisfactorio': 3,
                    'Destacado': 4
                }
                
                for nivel, codigo in codificacion_propuesta.items():
                    matches = [val for val in valores_unicos.index if nivel.lower() in str(val).lower()]
                    if matches:
                        print(f"  '{matches[0]}' → {codigo} ({nivel})")
                    else:
                        print(f"  [No encontrado: {nivel}]")
            
            else:
                print("No se pudo identificar la columna de resultados automáticamente")
                print("Columnas que podrían contener resultados:")
                for col in df.columns:
                    if any(word in col.lower() for word in ['resultado', 'logro', 'nivel', 'nota', 'calificacion']):
                        print(f"  - {col}")
            
            # Análisis de otros campos contextuales
            print(f"\nANÁLISIS DE CAMPOS CONTEXTUALES:")
            print("-" * 50)
            
            campos_contextuales = {
                'Sexo/Género': ['sexo', 'genero', 'género', 'sex'],
                'Grado': ['grado', 'grade', 'nivel'],
                'Sección': ['seccion', 'sección', 'section'],
                'Red': ['red', 'rer', 'network'],
                'Institución': ['institucion', 'institución', 'escuela', 'colegio', 'ie'],
                'Código': ['codigo', 'código', 'cod_mod', 'modular']
            }
            
            for contexto, patrones in campos_contextuales.items():
                cols_encontradas = []
                for patron in patrones:
                    cols_matches = [col for col in df.columns if patron.lower() in col.lower()]
                    cols_encontradas.extend(cols_matches)
                
                if cols_encontradas:
                    col_principal = cols_encontradas[0]
                    valores_sample = df[col_principal].value_counts().head(5)
                    print(f"  {contexto}: '{col_principal}'")
                    print(f"    Valores ejemplo: {list(valores_sample.index)}")
                else:
                    print(f"  {contexto}: [No identificado]")
            
        except Exception as e:
            print(f"Error al leer {archivo}: {e}")
    
    print(f"\n✅ EXPLORACIÓN DE DATOS ACADÉMICOS COMPLETADA")
    print("=" * 80)

if __name__ == "__main__":
    explorar_datos_academicos()