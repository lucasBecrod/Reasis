#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Resumen de Estructura Académica - Proyecto Reasis
Análisis limpio de la estructura de datos académicos encontrados
"""

import pandas as pd
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

def resumir_estructura_academica():
    """Resume la estructura de los datos académicos encontrados"""
    print("RESUMEN DE ESTRUCTURA DE DATOS ACADEMICOS")
    print("=" * 60)
    
    # Rutas de los archivos
    base_path = Path("assets/Consultoria/DatosLucas/Matematica y Comunicación")
    archivos = {
        "Matemática": base_path / "BD1- Matemática 2024.xlsx",
        "Comunicación": base_path / "BD2- Comunicación 2024.xlsx", 
        "Producción de textos": base_path / "BD3 - Producción de textos 2024.xlsx"
    }
    
    resumen_general = {}
    
    for materia, archivo in archivos.items():
        print(f"\n{materia.upper()}:")
        print("-" * 30)
        
        try:
            # Leer la hoja DATA
            df = pd.read_excel(archivo, sheet_name='DATA')
            
            # Información básica
            print(f"Total estudiantes: {len(df)}")
            print(f"Total columnas: {len(df.columns)}")
            
            # Identificar columna de resultados
            col_resultado = None
            patron_resultado = f'R {materia}'
            for col in df.columns:
                if patron_resultado.lower() in col.lower():
                    col_resultado = col
                    break
            
            if col_resultado:
                # Análisis de niveles de logro
                valores_logro = df[col_resultado].value_counts()
                print(f"Niveles de logro en '{col_resultado}':")
                for nivel, count in valores_logro.items():
                    porcentaje = (count / len(df)) * 100
                    print(f"  {nivel}: {count} ({porcentaje:.1f}%)")
                
                # Codificación propuesta
                codificacion = {
                    'Inicio': 1,
                    'Proceso': 2,
                    'Satisfactorio': 3,
                    'Destacado': 4
                }
                
                print("Codificación propuesta:")
                for nivel_original in valores_logro.index:
                    for nivel_estandar, codigo in codificacion.items():
                        if nivel_estandar.lower() in str(nivel_original).lower():
                            print(f"  '{nivel_original}' -> {codigo}")
                            break
            
            # Campos identificados importantes
            print("Campos contextuales identificados:")
            campos_importantes = {
                'Estudiante': 'ID del estudiante',
                'Región': 'Región educativa', 
                'Nivel': 'Nivel educativo (Primaria/Secundaria)',
                'Grado': 'Grado específico',
                'Institución Educativa': 'Código o nombre de IE',
                'Ambito': 'Rural/Urbano',
                'Sexo': 'Género del estudiante',
                'Año': 'Año de evaluación',
                'ID. IE': 'Identificador de IE con nombre'
            }
            
            for campo, descripcion in campos_importantes.items():
                if campo in df.columns:
                    # Mostrar algunos valores únicos
                    valores_unicos = df[campo].value_counts().head(3)
                    ejemplos = list(valores_unicos.index)
                    print(f"  {campo}: {descripcion}")
                    print(f"    Ejemplos: {ejemplos}")
            
            # Guardar resumen para análisis final
            resumen_general[materia] = {
                'total_estudiantes': len(df),
                'columnas': len(df.columns),
                'col_resultado': col_resultado,
                'niveles_logro': valores_logro.to_dict() if col_resultado else {},
                'año': df['Año'].iloc[0] if 'Año' in df.columns else 'No identificado'
            }
            
        except Exception as e:
            print(f"Error al procesar {archivo}: {e}")
    
    # RESUMEN CONSOLIDADO
    print(f"\nRESUMEN CONSOLIDADO")
    print("=" * 30)
    
    total_estudiantes = sum(r['total_estudiantes'] for r in resumen_general.values())
    print(f"Total estudiantes en todas las materias: {total_estudiantes}")
    
    for materia, info in resumen_general.items():
        print(f"{materia}: {info['total_estudiantes']} estudiantes")
    
    print(f"\nESTRUCTURA PROPUESTA PARA BASE DE DATOS:")
    print("-" * 40)
    
    estructura_bd = """
    CREATE TABLE resultados_academicos (
        id INTEGER PRIMARY KEY,
        estudiante_id INTEGER,
        codigo_ie TEXT,
        nombre_ie TEXT,
        region TEXT,
        nivel_educativo TEXT,
        grado TEXT,
        ambito TEXT,
        sexo TEXT,
        materia TEXT,
        nivel_logro_texto TEXT,
        nivel_logro_numerico INTEGER,
        año INTEGER,
        fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (codigo_ie) REFERENCES instituciones_educativas_v2_mejorada(codigo_modular)
    );
    
    -- Codificación de niveles de logro:
    -- 1: Inicio
    -- 2: Proceso  
    -- 3: Satisfactorio
    -- 4: Destacado
    """
    
    print(estructura_bd)
    
    print("PROXIMOS PASOS:")
    print("1. Crear script de migración de datos académicos")
    print("2. Limpiar y normalizar campos (códigos IE, nombres, etc.)")
    print("3. Aplicar codificación numérica de niveles de logro")
    print("4. Relacionar con tabla de instituciones educativas")
    print("5. Calcular ILA (Índice de Logro Académico) por institución")

if __name__ == "__main__":
    resumir_estructura_academica()