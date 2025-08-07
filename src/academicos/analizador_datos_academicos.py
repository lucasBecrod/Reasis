#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analizador de Datos Académicos Migrados - Proyecto Reasis
Script para analizar y validar la calidad de los datos académicos migrados
"""

import sqlite3
import pandas as pd
import re

def analizar_codigos_ie():
    """Analiza los códigos IE en los datos académicos migrados"""
    print("ANÁLISIS DE CÓDIGOS IE EN DATOS ACADÉMICOS")
    print("=" * 60)
    
    try:
        conn = sqlite3.connect('reasis_database.db')
        
        # 1. Códigos únicos en datos académicos
        print("\n1. CÓDIGOS IE EN DATOS ACADÉMICOS:")
        print("-" * 40)
        
        codigos_academicos = pd.read_sql_query("""
            SELECT codigo_ie, COUNT(*) as estudiantes, 
                   COUNT(DISTINCT materia) as materias
            FROM resultados_academicos 
            WHERE codigo_ie IS NOT NULL
            GROUP BY codigo_ie
            ORDER BY estudiantes DESC
        """, conn)
        
        print(f"Total códigos IE únicos: {len(codigos_academicos)}")
        print("\nCódigos IE más frecuentes:")
        for idx, row in codigos_academicos.head(10).iterrows():
            print(f"  {row['codigo_ie']}: {row['estudiantes']} estudiantes, {row['materias']} materias")
        
        # 2. Verificar coincidencias con tabla de instituciones
        print("\n2. VERIFICACIÓN DE COINCIDENCIAS:")
        print("-" * 40)
        
        coincidencias = pd.read_sql_query("""
            SELECT r.codigo_ie, 
                   COUNT(r.id) as estudiantes_total,
                   i.nombre,
                   i.area_censo
            FROM resultados_academicos r
            LEFT JOIN instituciones_educativas_v2_mejorada i 
                ON r.codigo_ie = i.codigo_modular
            WHERE r.codigo_ie IS NOT NULL
            GROUP BY r.codigo_ie, i.nombre, i.area_censo
            ORDER BY estudiantes_total DESC
        """, conn)
        
        coinciden = sum(1 for _, row in coincidencias.iterrows() if pd.notna(row['nombre']))
        no_coinciden = len(coincidencias) - coinciden
        
        print(f"Códigos que coinciden con instituciones: {coinciden}")
        print(f"Códigos sin coincidencia: {no_coinciden}")
        
        if no_coinciden > 0:
            print("\nCódigos sin coincidencia (primeros 10):")
            sin_coincidencia = coincidencias[coincidencias['nombre'].isna()]
            for idx, row in sin_coincidencia.head(10).iterrows():
                print(f"  {row['codigo_ie']}: {row['estudiantes_total']} estudiantes")
        
        # 3. Analizar formato de códigos IE
        print("\n3. ANÁLISIS DE FORMATO DE CÓDIGOS:")
        print("-" * 40)
        
        codigos_raw = pd.read_sql_query("""
            SELECT DISTINCT codigo_ie
            FROM resultados_academicos 
            WHERE codigo_ie IS NOT NULL
        """, conn)['codigo_ie'].tolist()
        
        patrones = {
            'numerico_7_8_digitos': 0,
            'numerico_menos_7': 0,
            'numerico_mas_8': 0,
            'con_letras': 0,
            'formato_invalido': 0
        }
        
        codigos_problematicos = []
        
        for codigo in codigos_raw:
            codigo_str = str(codigo).strip()
            
            if re.match(r'^\d{7,8}$', codigo_str):
                patrones['numerico_7_8_digitos'] += 1
            elif re.match(r'^\d{1,6}$', codigo_str):
                patrones['numerico_menos_7'] += 1
                codigos_problematicos.append(codigo)
            elif re.match(r'^\d{9,}$', codigo_str):
                patrones['numerico_mas_8'] += 1
                codigos_problematicos.append(codigo)
            elif re.search(r'[a-zA-Z]', codigo_str):
                patrones['con_letras'] += 1
                codigos_problematicos.append(codigo)
            else:
                patrones['formato_invalido'] += 1
                codigos_problematicos.append(codigo)
        
        print("Distribución de formatos:")
        for patron, count in patrones.items():
            print(f"  {patron.replace('_', ' ')}: {count}")
        
        if codigos_problematicos:
            print(f"\nCódigos problemáticos detectados: {len(codigos_problematicos)}")
            print("Ejemplos:", codigos_problematicos[:5])
        
        conn.close()
        
    except Exception as e:
        print(f"Error en análisis: {e}")

def analizar_nombres_ie():
    """Analiza los nombres de instituciones educativas"""
    print("\n4. ANÁLISIS DE NOMBRES DE INSTITUCIONES:")
    print("-" * 40)
    
    try:
        conn = sqlite3.connect('reasis_database.db')
        
        nombres_ie = pd.read_sql_query("""
            SELECT nombre_ie, COUNT(*) as estudiantes,
                   COUNT(DISTINCT codigo_ie) as codigos_diferentes
            FROM resultados_academicos 
            WHERE nombre_ie IS NOT NULL
            GROUP BY nombre_ie
            ORDER BY estudiantes DESC
            LIMIT 15
        """, conn)
        
        print("Instituciones con más estudiantes evaluados:")
        for idx, row in nombres_ie.iterrows():
            print(f"  {row['nombre_ie']}: {row['estudiantes']} estudiantes ({row['codigos_diferentes']} códigos)")
        
        # Verificar si hay nombres duplicados con códigos diferentes
        duplicados = nombres_ie[nombres_ie['codigos_diferentes'] > 1]
        if len(duplicados) > 0:
            print(f"\nALERTA: {len(duplicados)} instituciones con múltiples códigos IE")
            for idx, row in duplicados.iterrows():
                print(f"  {row['nombre_ie']}: {row['codigos_diferentes']} códigos diferentes")
        
        conn.close()
        
    except Exception as e:
        print(f"Error en análisis de nombres: {e}")

def analizar_distribucion_logros():
    """Analiza la distribución de logros académicos"""
    print("\n5. ANÁLISIS DE DISTRIBUCIÓN DE LOGROS:")
    print("-" * 40)
    
    try:
        conn = sqlite3.connect('reasis_database.db')
        
        # Por materia
        logros_materia = pd.read_sql_query("""
            SELECT materia, nivel_logro_texto, nivel_logro_numerico,
                   COUNT(*) as estudiantes
            FROM resultados_academicos
            GROUP BY materia, nivel_logro_texto, nivel_logro_numerico
            ORDER BY materia, nivel_logro_numerico
        """, conn)
        
        materias = logros_materia['materia'].unique()
        
        for materia in materias:
            print(f"\n{materia}:")
            datos_materia = logros_materia[logros_materia['materia'] == materia]
            total_estudiantes = datos_materia['estudiantes'].sum()
            
            for idx, row in datos_materia.iterrows():
                porcentaje = (row['estudiantes'] / total_estudiantes) * 100
                print(f"  {row['nivel_logro_numerico']} - {row['nivel_logro_texto']}: {row['estudiantes']} ({porcentaje:.1f}%)")
        
        # Por ámbito (rural/urbano)
        print(f"\nPor ámbito:")
        logros_ambito = pd.read_sql_query("""
            SELECT ambito, nivel_logro_numerico,
                   COUNT(*) as estudiantes
            FROM resultados_academicos
            WHERE ambito IS NOT NULL
            GROUP BY ambito, nivel_logro_numerico
            ORDER BY ambito, nivel_logro_numerico
        """, conn)
        
        ambitos = logros_ambito['ambito'].unique()
        
        for ambito in ambitos:
            print(f"\n  {ambito}:")
            datos_ambito = logros_ambito[logros_ambito['ambito'] == ambito]
            total_estudiantes = datos_ambito['estudiantes'].sum()
            
            for idx, row in datos_ambito.iterrows():
                porcentaje = (row['estudiantes'] / total_estudiantes) * 100
                print(f"    Nivel {row['nivel_logro_numerico']}: {row['estudiantes']} ({porcentaje:.1f}%)")
        
        conn.close()
        
    except Exception as e:
        print(f"Error en análisis de logros: {e}")

def generar_plan_limpieza():
    """Genera plan de limpieza basado en el análisis"""
    print("\n6. PLAN DE LIMPIEZA Y MEJORA:")
    print("-" * 40)
    
    print("ACCIONES RECOMENDADAS:")
    print("1. Normalizar códigos IE problemáticos:")
    print("   - Identificar códigos con menos de 7 dígitos")
    print("   - Buscar coincidencias parciales en tabla de instituciones")
    print("   - Crear tabla de mapeo manual si es necesario")
    
    print("\n2. Mejorar vinculación con instituciones:")
    print("   - Implementar búsqueda por nombre aproximado")
    print("   - Verificar coincidencias por código modular + nombre")
    print("   - Resolver discrepancias de múltiples códigos por nombre")
    
    print("\n3. Validar consistencia de datos contextuales:")
    print("   - Verificar coherencia ámbito rural/urbano")
    print("   - Validar distribución por grados y niveles")
    print("   - Revisar años de evaluación")
    
    print("\n4. Optimizar estructura de datos:")
    print("   - Crear tabla de instituciones académicas normalizada")
    print("   - Implementar índices adicionales para consultas frecuentes")
    print("   - Documentar relaciones entre tablas")

def main():
    """Función principal del análisis"""
    print("ANALIZADOR DE CALIDAD - DATOS ACADÉMICOS MIGRADOS")
    print("=" * 80)
    
    analizar_codigos_ie()
    analizar_nombres_ie()  
    analizar_distribucion_logros()
    generar_plan_limpieza()
    
    print(f"\nANÁLISIS DE CALIDAD COMPLETADO")
    print("=" * 80)

if __name__ == "__main__":
    main()