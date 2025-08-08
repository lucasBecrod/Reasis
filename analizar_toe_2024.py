#!/usr/bin/env python3
"""
Análisis detallado de datos TOE (Tipo Organización Escolar) 2024
Proyecto Reasis - Variable X12_TOE para clustering

Enfoque: Analizar hoja "Actualización del 2024" que contiene:
- Columna clave: "Tipo (unidocente, bidocente, multigrado, polidocente)"
- Corresponde a variable X12_TOE faltante en metodología clustering
"""

import pandas as pd
import sys

def main():
    print("=== ANÁLISIS DATOS TOE 2024 ===")
    
    archivo = r"C:\Users\lucas\Proyectos\Reasis\assets\Consultoria\Información de referencia\Estadista IIEE Estudiantes RER FyA 2024 y 2025\Identificador_Servicios Educativos FyA RER 2025 (3).xlsx"
    
    # 1. Cargar hoja específica con datos TOE
    print("1. Cargando hoja 'Actualización del 2024'...")
    
    try:
        df_toe = pd.read_excel(archivo, sheet_name='Actualización del 2024')
        print(f"   Registros cargados: {len(df_toe)}")
        print(f"   Columnas: {len(df_toe.columns)}")
        
        # Renombrar columna para facilidad
        df_toe = df_toe.rename(columns={
            'Tipo (unidocente, bidocente, multigrado, polidocente)': 'tipo_organizacion_escolar'
        })
        
    except Exception as e:
        print(f"   Error al cargar: {e}")
        return
    
    # 2. Análisis de completitud TOE
    print("\n2. Análisis de completitud de datos TOE...")
    
    toe_disponible = df_toe['tipo_organizacion_escolar'].notna().sum()
    print(f"   Registros con TOE: {toe_disponible}/{len(df_toe)} ({toe_disponible/len(df_toe)*100:.1f}%)")
    
    # Distribución de tipos
    print("\n   Distribución de tipos de organización escolar:")
    distribucion_toe = df_toe['tipo_organizacion_escolar'].value_counts(dropna=False)
    print(distribucion_toe.to_string())
    
    # 3. Análisis de códigos modulares
    print("\n3. Análisis de códigos modulares para vinculación...")
    
    codigos_validos = df_toe['codigo modular'].notna().sum()
    print(f"   Códigos modulares válidos: {codigos_validos}/{len(df_toe)} ({codigos_validos/len(df_toe)*100:.1f}%)")
    
    # Verificar formato numérico
    try:
        df_toe['codigo_modular_num'] = pd.to_numeric(df_toe['codigo modular'], errors='coerce')
        numericos_validos = df_toe['codigo_modular_num'].notna().sum()
        print(f"   Códigos numéricos válidos: {numericos_validos}/{len(df_toe)}")
    except:
        print("   Error al convertir códigos a numéricos")
    
    # 4. Análisis por redes del estudio
    print("\n4. Análisis por redes del estudio (44, 47, 48, 54, 72, 79)...")
    
    redes_estudio = ['RER FA 44', 'RER FA 47', 'RER FA 48', 'RER FA 54', 'RER FA 72', 'RER FA 79']
    
    for red in redes_estudio:
        df_red = df_toe[df_toe['iiee'] == red]
        if len(df_red) > 0:
            toe_red = df_red['tipo_organizacion_escolar'].notna().sum()
            print(f"   {red}: {len(df_red)} IIEE, {toe_red} con TOE ({toe_red/len(df_red)*100:.1f}%)")
            
            # Distribución TOE por red
            if toe_red > 0:
                dist_red = df_red['tipo_organizacion_escolar'].value_counts(dropna=False)
                print(f"     Distribución: {dict(dist_red)}")
    
    # 5. Análisis de datos adicionales disponibles
    print("\n5. Análisis de datos adicionales...")
    
    # Estudiantes y docentes
    estudiantes_disponibles = df_toe['Estudiantes'].notna().sum()
    docentes_disponibles = df_toe['Docentes'].notna().sum()
    
    print(f"   Datos de estudiantes: {estudiantes_disponibles}/{len(df_toe)} ({estudiantes_disponibles/len(df_toe)*100:.1f}%)")
    print(f"   Datos de docentes: {docentes_disponibles}/{len(df_toe)} ({docentes_disponibles/len(df_toe)*100:.1f}%)")
    
    if estudiantes_disponibles > 0:
        print(f"   Rango estudiantes: {df_toe['Estudiantes'].min():.0f} - {df_toe['Estudiantes'].max():.0f}")
    
    if docentes_disponibles > 0:
        print(f"   Rango docentes: {df_toe['Docentes'].min():.0f} - {df_toe['Docentes'].max():.0f}")
    
    # 6. Preparar datos para integración
    print("\n6. Preparando datos para integración...")
    
    # Filtrar registros con TOE y código modular válidos
    df_validos = df_toe[
        (df_toe['tipo_organizacion_escolar'].notna()) & 
        (df_toe['codigo_modular_num'].notna())
    ].copy()
    
    print(f"   Registros válidos para integración: {len(df_validos)}")
    
    # Mostrar muestra de datos válidos
    print("\n   Muestra de registros válidos:")
    columnas_mostrar = ['codigo modular', 'iiee', 'tipo_organizacion_escolar', 'Estudiantes', 'Docentes']
    print(df_validos[columnas_mostrar].head(10).to_string())
    
    # 7. Verificar coincidencias con BD actual
    print("\n7. Verificando potencial de vinculación con BD actual...")
    
    # Cargar códigos de BD para comparar
    import sqlite3
    conn = sqlite3.connect('reasis_database.db')
    
    df_bd = pd.read_sql_query("""
        SELECT codigo_modular, nombre_institucion, numero_fya, entra_estudio_clustering
        FROM instituciones_educativas 
        WHERE entra_estudio_clustering = 'Sí'
    """, conn)
    
    codigos_bd = set(df_bd['codigo_modular'].astype(str))
    codigos_toe = set(df_validos['codigo_modular_num'].astype(int).astype(str))
    
    coincidencias = codigos_bd.intersection(codigos_toe)
    
    print(f"   Códigos en BD (estudio): {len(codigos_bd)}")
    print(f"   Códigos en archivo TOE: {len(codigos_toe)}")
    print(f"   Coincidencias: {len(coincidencias)} ({len(coincidencias)/len(codigos_bd)*100:.1f}%)")
    
    if len(coincidencias) > 0:
        print(f"   Primeras coincidencias: {list(coincidencias)[:10]}")
    
    # 8. Impacto en variable X12_TOE
    print("\n8. IMPACTO EN VARIABLE METODOLÓGICA X12_TOE:")
    
    print(f"   ANTES: X12_TOE no disponible (0 instituciones)")
    print(f"   DESPUÉS: X12_TOE disponible para {len(coincidencias)} instituciones")
    print(f"   Variable completada: {len(coincidencias)/len(codigos_bd)*100:.1f}% del estudio")
    
    if len(coincidencias) > 0:
        print(f"   AVANCE METODOLÓGICO: Variable X12_TOE desbloqueada")
        print(f"   CLUSTERING: Mejora significativa en análisis K-Means")
    
    conn.close()
    print("\n¡ANÁLISIS TOE COMPLETADO!")

if __name__ == "__main__":
    main()