#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Normalizador de Columnas Académicas - Proyecto Reasis
Script para normalizar todos los campos de las tablas académicas garantizando consistencia
"""

import sqlite3
import pandas as pd
import re
from pathlib import Path

def crear_reglas_normalizacion():
    """Define todas las reglas de normalización por columna"""
    
    reglas = {
        'region': {
            'tipo': 'texto_numerico',
            'transformaciones': {
                # Mantener formato "XX. Nombre"
                r'^(\d+)\.\s*(.+)$': r'\1. \2',  # Normalizar espaciado
                r'^(\d+)\.(.+)$': r'\1. \2',     # Agregar espacio faltante
            },
            'validaciones': [
                r'^\d+\.\s.+$'  # Debe tener formato "XX. Nombre"
            ]
        },
        'nivel': {
            'tipo': 'categorico',
            'valores_estandar': ['Primaria', 'Secundaria'],
            'transformaciones': {
                r'primaria': 'Primaria',
                r'secundaria': 'Secundaria',
                r'secund': 'Secundaria'
            }
        },
        'grado': {
            'tipo': 'texto_nivel',
            'transformaciones': {
                # Normalizar formato "X Nivel"
                r'^(\d+)\s*(primaria|secundaria)$': r'\1 \2',
                r'^(\d+)\s*(Primaria|Secundaria)$': r'\1 \2',
                r'^(\d+)(primaria|secundaria)$': r'\1 \2',
                r'^(\d+)(Primaria|Secundaria)$': r'\1 \2'
            },
            'capitalizacion': 'titulo'
        },
        'institucion_educativa': {
            'tipo': 'codigo_nombre',
            'limpiezas': [
                'strip',  # Eliminar espacios inicio/fin
                'espacios_multiples',  # Normalizar espacios múltiples
                'caracteres_especiales'  # Limpiar caracteres raros
            ]
        },
        'ambito': {
            'tipo': 'categorico',
            'valores_estandar': ['Rural', 'Urbano'],
            'transformaciones': {
                r'rural': 'Rural',
                r'urbano': 'Urbano',
                r'urbana': 'Urbano'
            }
        },
        'sexo': {
            'tipo': 'categorico',
            'valores_estandar': ['Masculino', 'Femenino'],
            'transformaciones': {
                r'masculino': 'Masculino',
                r'femenino': 'Femenino',
                r'hombre': 'Masculino',
                r'mujer': 'Femenino',
                r'varon': 'Masculino',
                r'varón': 'Masculino',
                r'male': 'Masculino',
                r'female': 'Femenino',
                r'm': 'Masculino',
                r'f': 'Femenino'
            }
        },
        'resultado_academico': {
            'tipo': 'categorico',
            'valores_estandar': ['Inicio', 'Proceso', 'Satisfactorio', 'Destacado'],
            'transformaciones': {
                r'inicio': 'Inicio',
                r'proceso': 'Proceso', 
                r'satisfactorio': 'Satisfactorio',
                r'destacado': 'Destacado'
            },
            'codificacion_numerica': {
                'Inicio': 1,
                'Proceso': 2,
                'Satisfactorio': 3,
                'Destacado': 4
            }
        },
        'año': {
            'tipo': 'numerico',
            'rango_valido': (2020, 2025),
            'valor_defecto': 2024
        },
        'analisis': {
            'tipo': 'categorico_multiple',
            'valores_estandar': [
                'SOLO 2024', 'SOLO 2022 Y 2024', 'LOS 3 AÑOS', 
                '2023 Y 2024', 'SOLO 2023'
            ],
            'transformaciones': {
                r'solo 2024': 'SOLO 2024',
                r'los 3 años': 'LOS 3 AÑOS',
                r'2023 y 2024': '2023 Y 2024'
            }
        },
        'padd_r': {
            'tipo': 'categorico_multiple',
            'limpiezas': ['strip', 'espacios_multiples']
        }
    }
    
    return reglas

def aplicar_transformacion_texto(valor, transformaciones):
    """Aplica transformaciones de texto basadas en regex"""
    if pd.isna(valor) or valor == "":
        return None
        
    valor_str = str(valor).strip()
    
    for patron, reemplazo in transformaciones.items():
        if re.search(patron, valor_str, re.IGNORECASE):
            valor_str = re.sub(patron, reemplazo, valor_str, flags=re.IGNORECASE)
            break  # Solo aplicar la primera coincidencia
    
    return valor_str

def normalizar_campo(valor, reglas_campo):
    """Normaliza un campo individual según sus reglas"""
    if pd.isna(valor) or valor == "":
        return None
    
    valor_original = str(valor)
    valor_normalizado = valor_original.strip()
    
    # Aplicar transformaciones específicas
    if 'transformaciones' in reglas_campo:
        valor_normalizado = aplicar_transformacion_texto(
            valor_normalizado, reglas_campo['transformaciones']
        )
    
    # Aplicar limpiezas generales
    if 'limpiezas' in reglas_campo:
        for limpieza in reglas_campo['limpiezas']:
            if limpieza == 'strip':
                valor_normalizado = valor_normalizado.strip()
            elif limpieza == 'espacios_multiples':
                valor_normalizado = re.sub(r'\s+', ' ', valor_normalizado)
            elif limpieza == 'caracteres_especiales':
                # Conservar letras, números, espacios y algunos especiales
                valor_normalizado = re.sub(r'[^\w\s\-\.\,\(\)\"\']+', '', valor_normalizado)
    
    # Aplicar capitalización
    if 'capitalizacion' in reglas_campo:
        if reglas_campo['capitalizacion'] == 'titulo':
            valor_normalizado = valor_normalizado.title()
        elif reglas_campo['capitalizacion'] == 'mayusculas':
            valor_normalizado = valor_normalizado.upper()
        elif reglas_campo['capitalizacion'] == 'minusculas':
            valor_normalizado = valor_normalizado.lower()
    
    # Validar contra valores estándar
    if 'valores_estandar' in reglas_campo:
        if valor_normalizado not in reglas_campo['valores_estandar']:
            # Buscar coincidencia aproximada
            valor_lower = valor_normalizado.lower()
            for estandar in reglas_campo['valores_estandar']:
                if estandar.lower() in valor_lower or valor_lower in estandar.lower():
                    valor_normalizado = estandar
                    break
    
    return valor_normalizado

def normalizar_tabla_academica(df, materia, reglas):
    """Normaliza una tabla académica completa"""
    print(f"Normalizando tabla de {materia}...")
    
    df_normalizada = df.copy()
    cambios_por_columna = {}
    
    # Mapear columnas de la tabla a reglas de normalización
    mapeo_columnas = {
        'Región': 'region',
        'Nivel': 'nivel', 
        'Grado': 'grado',
        'Institución Educativa': 'institucion_educativa',
        'Ambito': 'ambito',
        'Sexo': 'sexo',
        'Año': 'año',
        'ANALISIS': 'analisis',
        'PADD-R': 'padd_r'
    }
    
    # Detectar columna de resultado según materia
    col_resultado = None
    patrones_resultado = [f'R {materia}', f'R Matemática', f'R Comunicación', f'R Producción de textos']
    for patron in patrones_resultado:
        if patron in df.columns:
            col_resultado = patron
            break
    
    if col_resultado:
        mapeo_columnas[col_resultado] = 'resultado_academico'
    
    # Aplicar normalizaciones
    for col_original, regla_key in mapeo_columnas.items():
        if col_original in df.columns and regla_key in reglas:
            regla = reglas[regla_key]
            
            print(f"  Normalizando columna: {col_original}")
            
            # Contar cambios
            cambios = 0
            valores_originales = df_normalizada[col_original].copy()
            
            # Aplicar normalización a cada valor
            df_normalizada[col_original] = df_normalizada[col_original].apply(
                lambda x: normalizar_campo(x, regla)
            )
            
            # Contar cambios realizados
            cambios = sum(valores_originales.astype(str) != df_normalizada[col_original].astype(str))
            cambios_por_columna[col_original] = cambios
            
            print(f"    Cambios realizados: {cambios}")
    
    return df_normalizada, cambios_por_columna

def generar_reporte_normalizacion(cambios_por_tabla):
    """Genera reporte detallado de normalización"""
    print("\nREPORTE DE NORMALIZACIÓN")
    print("=" * 60)
    
    total_cambios = 0
    
    for tabla, cambios_columnas in cambios_por_tabla.items():
        print(f"\n{tabla.upper()}:")
        print("-" * 30)
        
        cambios_tabla = sum(cambios_columnas.values())
        total_cambios += cambios_tabla
        
        print(f"Total cambios en tabla: {cambios_tabla}")
        
        for columna, cambios in cambios_columnas.items():
            if cambios > 0:
                print(f"  {columna}: {cambios} cambios")
    
    print(f"\nTOTAL CAMBIOS REALIZADOS: {total_cambios}")
    
    return total_cambios

def crear_tabla_normalizada():
    """Crea nueva tabla con datos académicos normalizados"""
    print("\nCreando tabla normalizada...")
    
    try:
        conn = sqlite3.connect('reasis_database.db')
        cursor = conn.cursor()
        
        # Crear tabla normalizada
        cursor.execute("DROP TABLE IF EXISTS resultados_academicos_normalized")
        
        create_table_sql = """
        CREATE TABLE resultados_academicos_normalized (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            estudiante_id TEXT,
            region TEXT,
            nivel_educativo TEXT,
            grado TEXT,
            codigo_ie TEXT,
            nombre_ie TEXT,
            ambito TEXT,
            sexo TEXT,
            materia TEXT,
            resultado_texto TEXT,
            resultado_numerico INTEGER,
            año INTEGER,
            analisis_cobertura TEXT,
            padd_participacion TEXT,
            fecha_normalizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (codigo_ie) REFERENCES instituciones_educativas_v2_mejorada(codigo_modular)
        );
        """
        
        cursor.execute(create_table_sql)
        
        # Crear índices
        indices = [
            "CREATE INDEX idx_norm_codigo_ie ON resultados_academicos_normalized(codigo_ie);",
            "CREATE INDEX idx_norm_materia ON resultados_academicos_normalized(materia);", 
            "CREATE INDEX idx_norm_año ON resultados_academicos_normalized(año);",
            "CREATE INDEX idx_norm_resultado ON resultados_academicos_normalized(resultado_numerico);"
        ]
        
        for indice in indices:
            cursor.execute(indice)
        
        conn.commit()
        conn.close()
        
        print("Tabla normalizada creada exitosamente")
        
    except Exception as e:
        print(f"Error creando tabla normalizada: {e}")

def main():
    """Función principal de normalización"""
    print("NORMALIZADOR DE COLUMNAS ACADÉMICAS - PROYECTO REASIS")
    print("=" * 80)
    
    # Cargar reglas de normalización
    reglas = crear_reglas_normalizacion()
    
    # Definir archivos a procesar
    base_path = Path("assets/Consultoria/DatosLucas/Matematica y Comunicación")
    archivos_academicos = {
        "Matemática": base_path / "BD1- Matemática 2024.xlsx",
        "Comunicación": base_path / "BD2- Comunicación 2024.xlsx",
        "Producción de textos": base_path / "BD3 - Producción de textos 2024.xlsx"
    }
    
    cambios_por_tabla = {}
    tablas_normalizadas = {}
    
    # Procesar cada archivo
    for materia, archivo_path in archivos_academicos.items():
        if archivo_path.exists():
            print(f"\nProcesando {materia}...")
            
            try:
                # Leer datos originales
                df_original = pd.read_excel(archivo_path, sheet_name='DATA')
                print(f"Filas originales: {len(df_original)}")
                
                # Aplicar normalización
                df_normalizada, cambios = normalizar_tabla_academica(df_original, materia, reglas)
                
                # Guardar resultados
                cambios_por_tabla[materia] = cambios
                tablas_normalizadas[materia] = df_normalizada
                
                # Guardar tabla normalizada en CSV para revisión
                output_path = f"data_normalizadas_{materia.lower().replace(' ', '_')}.csv"
                df_normalizada.to_csv(output_path, index=False, encoding='utf-8')
                print(f"  Tabla normalizada guardada en: {output_path}")
                
            except Exception as e:
                print(f"Error procesando {materia}: {e}")
        else:
            print(f"Archivo no encontrado: {archivo_path}")
    
    # Generar reporte final
    total_cambios = generar_reporte_normalizacion(cambios_por_tabla)
    
    # Crear tabla SQL normalizada
    if total_cambios > 0:
        crear_tabla_normalizada()
        print("\n¡Normalización completada!")
        print("Revisa los archivos CSV generados antes de proceder con la migración SQL.")
    else:
        print("\nNo se realizaron cambios. Los datos ya están normalizados.")
    
    print("=" * 80)

if __name__ == "__main__":
    main()