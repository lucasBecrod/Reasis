#!/usr/bin/env python3
"""
Validar consistencia de redes y analizar datos académicos 2023
Proyecto Reasis - FASE 1 y 2 del plan de integración

Objetivos específicos:
1. Analizar datos académicos 2023 (estudiantes H/M, secciones, docentes)
2. Validar consistencia asignaciones de redes vs BD actual
3. Identificar discrepancias y oportunidades de mejora
4. Preparar integración de datos 2023
"""

import pandas as pd
import sqlite3
import numpy as np

def limpiar_estudiantes_2023(valor):
    """Limpia y convierte datos de estudiantes a numérico"""
    if pd.isna(valor):
        return None
    
    # Convertir a string y limpiar
    valor_str = str(valor).strip()
    
    # Si es 'H', 'M', 'Total' (headers), retornar None
    if valor_str in ['H', 'M', 'Total', 'h', 'm', 'total']:
        return None
    
    try:
        return int(float(valor_str))
    except:
        return None

def main():
    print("=== VALIDACIÓN CONSISTENCIA REDES Y ANÁLISIS DATOS 2023 ===")
    
    archivo = r"C:\Users\lucas\Proyectos\Reasis\assets\Consultoria\Información de referencia\Estadista IIEE Estudiantes RER FyA 2024 y 2025\Redes Rurales FyA - Lista de instituciones educativas (v25012024) v22022024 (2) (1).xlsx"
    
    # 1. Cargar datos del archivo Excel
    print("1. Cargando datos de instituciones educativas 2023...")
    
    try:
        df_iiee_2023 = pd.read_excel(archivo, sheet_name='Redes Educativas Rurales 2023')
        print(f"   Registros cargados: {len(df_iiee_2023)}")
        
        # Limpiar primera fila si contiene headers
        if df_iiee_2023.iloc[0]['Código Modular'] != df_iiee_2023.iloc[0]['Código Modular']:  # NaN check
            df_iiee_2023 = df_iiee_2023.iloc[1:].reset_index(drop=True)
            print(f"   Registros después de limpiar headers: {len(df_iiee_2023)}")
            
    except Exception as e:
        print(f"   Error al cargar archivo: {e}")
        return
    
    # 2. Limpiar y normalizar datos
    print("\\n2. Limpiando y normalizando datos académicos 2023...")
    
    # Renombrar columnas para facilidad
    df_clean = df_iiee_2023.rename(columns={
        'Código Modular': 'codigo_modular',
        'Código de local': 'codigo_local',
        'RED RURAL FYA': 'red_rural_fya',
        'Institución Educativa': 'nombre_institucion',
        'Nivel de Modalidad': 'nivel_modalidad',
        'Centro Poblado': 'centro_poblado',
        'Distrito': 'distrito',
        'Provincia': 'provincia', 
        'Departamento': 'departamento',
        'Número de Estudiantes 2023 *': 'estudiantes_2023',
        'Número de Docentes': 'docentes_2023',
        'Número de secciones': 'secciones_2023',
        'Acumulado Estudiantes 2023': 'estudiantes_total_2023'
    }).copy()
    
    # Limpiar código modular
    df_clean['codigo_modular'] = pd.to_numeric(df_clean['codigo_modular'], errors='coerce')
    df_clean = df_clean[df_clean['codigo_modular'].notna()].copy()
    df_clean['codigo_modular'] = df_clean['codigo_modular'].astype(int).astype(str)
    
    # Limpiar datos académicos
    df_clean['estudiantes_2023'] = df_clean['estudiantes_2023'].apply(limpiar_estudiantes_2023)
    df_clean['docentes_2023'] = pd.to_numeric(df_clean['docentes_2023'], errors='coerce')
    df_clean['secciones_2023'] = pd.to_numeric(df_clean['secciones_2023'], errors='coerce')
    df_clean['estudiantes_total_2023'] = pd.to_numeric(df_clean['estudiantes_total_2023'], errors='coerce')
    
    print(f"   Registros válidos después de limpieza: {len(df_clean)}")
    
    # 3. Análisis de datos académicos 2023
    print("\\n3. ANÁLISIS DE DATOS ACADÉMICOS 2023...")
    
    estudiantes_disponibles = df_clean['estudiantes_2023'].notna().sum()
    docentes_disponibles = df_clean['docentes_2023'].notna().sum()
    secciones_disponibles = df_clean['secciones_2023'].notna().sum()
    
    print(f"   Estudiantes 2023: {estudiantes_disponibles}/{len(df_clean)} ({estudiantes_disponibles/len(df_clean)*100:.1f}%)")
    print(f"   Docentes 2023: {docentes_disponibles}/{len(df_clean)} ({docentes_disponibles/len(df_clean)*100:.1f}%)")
    print(f"   Secciones 2023: {secciones_disponibles}/{len(df_clean)} ({secciones_disponibles/len(df_clean)*100:.1f}%)")
    
    if estudiantes_disponibles > 0:
        est_stats = df_clean['estudiantes_2023'].describe()
        print(f"   Estudiantes - Min: {est_stats['min']:.0f}, Max: {est_stats['max']:.0f}, Promedio: {est_stats['mean']:.1f}")
    
    if docentes_disponibles > 0:
        doc_stats = df_clean['docentes_2023'].describe()
        print(f"   Docentes - Min: {doc_stats['min']:.0f}, Max: {doc_stats['max']:.0f}, Promedio: {doc_stats['mean']:.1f}")
    
    # 4. Análisis por redes del estudio
    print("\\n4. ANÁLISIS POR REDES DEL ESTUDIO...")
    
    redes_estudio = ['RER FA 44', 'RER FA 47', 'RER FA 48', 'RER FA 54', 'RER FA 72', 'RER FA 79']
    
    for red in redes_estudio:
        df_red = df_clean[df_clean['red_rural_fya'] == red]
        if len(df_red) > 0:
            est_red = df_red['estudiantes_2023'].notna().sum()
            doc_red = df_red['docentes_2023'].notna().sum()
            sec_red = df_red['secciones_2023'].notna().sum()
            
            print(f"\\n   {red}:")
            print(f"     Total IIEE: {len(df_red)}")
            print(f"     Con datos estudiantes: {est_red} ({est_red/len(df_red)*100:.1f}%)")
            print(f"     Con datos docentes: {doc_red} ({doc_red/len(df_red)*100:.1f}%)")
            print(f"     Con datos secciones: {sec_red} ({sec_red/len(df_red)*100:.1f}%)")
            
            if est_red > 0:
                total_estudiantes = df_red['estudiantes_2023'].sum()
                print(f"     Total estudiantes: {total_estudiantes:.0f}")
    
    # 5. Conectar a base de datos para validación
    print("\\n5. VALIDANDO CONSISTENCIA CON BASE DE DATOS ACTUAL...")
    
    conn = sqlite3.connect('reasis_database.db')
    
    df_bd = pd.read_sql_query("""
        SELECT codigo_modular, nombre_institucion, numero_fya, nombre_red_fya_matched, 
               total_alumnos, docentes_total, total_secciones, entra_estudio_clustering
        FROM instituciones_educativas 
    """, conn)
    
    df_bd['codigo_modular'] = df_bd['codigo_modular'].astype(str)
    
    print(f"   Instituciones en BD actual: {len(df_bd)}")
    print(f"   Instituciones del estudio en BD: {len(df_bd[df_bd['entra_estudio_clustering'] == 'Sí'])}")
    
    # 6. Comparar asignaciones de redes
    print("\\n6. COMPARANDO ASIGNACIONES DE REDES...")
    
    # Merge para encontrar coincidencias
    df_merged = df_bd.merge(
        df_clean,
        on='codigo_modular',
        how='inner',
        suffixes=('_bd', '_excel')
    )
    
    coincidencias = len(df_merged)
    print(f"   Coincidencias por código modular: {coincidencias}")
    
    # Verificar consistencia de redes
    if coincidencias > 0:
        # Extraer número de red del excel para comparar
        df_merged['numero_red_excel'] = df_merged['red_rural_fya'].str.extract(r'RER FA (\\d+)')[0]
        
        # Comparar asignaciones
        consistencias = (df_merged['numero_fya'] == df_merged['numero_red_excel']).sum()
        inconsistencias = coincidencias - consistencias
        
        print(f"   Asignaciones consistentes: {consistencias} ({consistencias/coincidencias*100:.1f}%)")
        print(f"   Asignaciones inconsistentes: {inconsistencias}")
        
        if inconsistencias > 0:
            print("\\n   INCONSISTENCIAS DETECTADAS:")
            inconsistentes = df_merged[df_merged['numero_fya'] != df_merged['numero_red_excel']]
            for _, row in inconsistentes.head(10).iterrows():
                print(f"     {row['codigo_modular']}: BD dice Red {row['numero_fya']}, Excel dice {row['red_rural_fya']}")
    
    # 7. Identificar instituciones no encontradas en BD
    print("\\n7. IDENTIFICANDO INSTITUCIONES FALTANTES...")
    
    codigos_bd = set(df_bd['codigo_modular'])
    codigos_excel = set(df_clean['codigo_modular'])
    
    codigos_faltantes = codigos_excel - codigos_bd
    codigos_sobrantes = codigos_bd - codigos_excel
    
    print(f"   En Excel pero NO en BD: {len(codigos_faltantes)} instituciones")
    print(f"   En BD pero NO en Excel: {len(codigos_sobrantes)} instituciones")
    
    if len(codigos_faltantes) > 0:
        df_faltantes = df_clean[df_clean['codigo_modular'].isin(codigos_faltantes)]
        print("\\n   INSTITUCIONES FALTANTES EN BD (Top 10):")
        faltantes_muestra = df_faltantes[['codigo_modular', 'red_rural_fya', 'nombre_institucion', 'estudiantes_2023']].head(10)
        print(faltantes_muestra.to_string())
    
    # 8. Comparar datos académicos actuales vs 2023
    print("\\n8. COMPARANDO DATOS ACADÉMICOS BD ACTUAL vs 2023...")
    
    if coincidencias > 0:
        # Estudiantes
        estudiantes_comparables = df_merged[
            (df_merged['total_alumnos'].notna()) & 
            (df_merged['estudiantes_2023'].notna())
        ]
        
        if len(estudiantes_comparables) > 0:
            diferencia_est = estudiantes_comparables['estudiantes_2023'] - estudiantes_comparables['total_alumnos']
            print(f"   Comparación estudiantes ({len(estudiantes_comparables)} instituciones):")
            print(f"     Diferencia promedio 2023 vs actual: {diferencia_est.mean():.1f}")
            print(f"     Diferencia máxima: {diferencia_est.max():.0f}")
            print(f"     Diferencia mínima: {diferencia_est.min():.0f}")
        
        # Docentes
        docentes_comparables = df_merged[
            (df_merged['docentes_total'].notna()) & 
            (df_merged['docentes_2023'].notna())
        ]
        
        if len(docentes_comparables) > 0:
            diferencia_doc = docentes_comparables['docentes_2023'] - docentes_comparables['docentes_total']
            print(f"   Comparación docentes ({len(docentes_comparables)} instituciones):")
            print(f"     Diferencia promedio 2023 vs actual: {diferencia_doc.mean():.1f}")
    
    # 9. Resumen de oportunidades
    print("\\n9. RESUMEN DE OPORTUNIDADES DE INTEGRACIÓN...")
    
    print(f"\\n   DATOS 2023 DISPONIBLES:")
    print(f"   - Estudiantes: {estudiantes_disponibles} instituciones")
    print(f"   - Docentes: {docentes_disponibles} instituciones")
    print(f"   - Secciones: {secciones_disponibles} instituciones")
    
    print(f"\\n   MEJORAS POSIBLES:")
    print(f"   - Agregar {len(codigos_faltantes)} instituciones nuevas a BD")
    print(f"   - Actualizar datos académicos 2023 para {coincidencias} instituciones")
    print(f"   - Resolver {inconsistencias} inconsistencias de asignación de redes")
    
    # Variables metodológicas que se pueden mejorar
    redes_estudio_nums = ['44', '47', '48', '54', '72', '79']
    instituciones_estudio_excel = 0
    
    for red_num in redes_estudio_nums:
        red_full = f'RER FA {red_num}'
        count = len(df_clean[df_clean['red_rural_fya'] == red_full])
        instituciones_estudio_excel += count
    
    print(f"\\n   IMPACTO EN VARIABLES METODOLÓGICAS:")
    print(f"   - Instituciones del estudio en Excel: {instituciones_estudio_excel}")
    print(f"   - Potencial mejora en cobertura de datos 2023")
    print(f"   - Robustecimiento de asignaciones de red")
    
    conn.close()
    print("\\n¡VALIDACIÓN Y ANÁLISIS COMPLETADOS!")

if __name__ == "__main__":
    main()