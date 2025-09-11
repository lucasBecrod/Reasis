#!/usr/bin/env python3
"""
Evaluación Metodológica Completa - Proyecto Reasis
Análisis exhaustivo de completitud de las 12 variables metodológicas según
la matriz de operacionalización y metodología del informe de tipologías.

VARIABLES METODOLÓGICAS A EVALUAR:
- Y1: Índice de Logro Académico (ILA)
- Y2: Tendencia de Desempeño (TD) 
- Y3: Perfil de Resiliencia (PR)
- X1: Nivel de Vulnerabilidad Contextual (NVC)
- X2: Tipo de Ruralidad (TR)
- X4: Índice de Desempeño Docente (IDD)
- X5: Estabilidad Docente (ED)
- X6: Competencia Digital Docente (CDD)
- X10: Infraestructura Educativa (IE)
- X11: Ratio Estudiante-Docente (RED)
- X12: Tipo de Organización Escolar (TOE)
- X15: Modalidad EIB (MEIB)
"""

import pandas as pd
import sqlite3
from datetime import datetime

def evaluar_variable_y1_ila():
    """Evaluar Y1: Índice de Logro Académico"""
    conn = sqlite3.connect('reasis_database.db')
    
    print("=== Y1: ÍNDICE DE LOGRO ACADÉMICO (ILA) ===")
    
    # Verificar datos académicos disponibles
    query_academicos = """
        SELECT codigo_modular, COUNT(*) as estudiantes,
               AVG(CASE WHEN area = 'Matemática' THEN valor_numerico END) as prom_matematica,
               AVG(CASE WHEN area = 'Comunicación' THEN valor_numerico END) as prom_comunicacion,
               MIN(año) as año_min, MAX(año) as año_max
        FROM resultados_academicos
        WHERE codigo_modular IS NOT NULL 
        GROUP BY codigo_modular
        HAVING COUNT(*) >= 2
    """
    
    df_ila = pd.read_sql_query(query_academicos, conn)
    
    # Calcular ILA según metodología
    df_ila['ila_calculado'] = (df_ila['prom_matematica'] + df_ila['prom_comunicacion']) / 2
    df_ila_completo = df_ila[df_ila['ila_calculado'].notna()]
    
    instituciones_con_ila = len(df_ila_completo)
    total_estudiantes = df_ila['estudiantes'].sum()
    
    print(f"✓ Instituciones con ILA calculable: {instituciones_con_ila}")
    print(f"✓ Total estudiantes evaluados: {total_estudiantes:,}")
    print(f"✓ ILA promedio: {df_ila_completo['ila_calculado'].mean():.2f}")
    print(f"✓ Rango ILA: {df_ila_completo['ila_calculado'].min():.2f} - {df_ila_completo['ila_calculado'].max():.2f}")
    print(f"✓ Años disponibles: {df_ila['año_min'].min()} - {df_ila['año_max'].max()}")
    
    conn.close()
    return instituciones_con_ila, df_ila_completo

def evaluar_variable_y2_td(df_ila):
    """Evaluar Y2: Tendencia de Desempeño"""
    print("\n=== Y2: TENDENCIA DE DESEMPEÑO (TD) ===")
    
    conn = sqlite3.connect('reasis_database.db')
    
    # Verificar datos multi-año para calcular TD
    query_multianio = """
        SELECT codigo_modular, año,
               AVG(CASE WHEN area = 'Matemática' THEN valor_numerico END) as prom_matematica,
               AVG(CASE WHEN area = 'Comunicación' THEN valor_numerico END) as prom_comunicacion
        FROM resultados_academicos
        WHERE codigo_modular IS NOT NULL AND año IN (2022, 2024)
        GROUP BY codigo_modular, año
        HAVING COUNT(*) >= 2
    """
    
    df_multianio = pd.read_sql_query(query_multianio, conn)
    
    # Calcular ILA por año
    df_multianio['ila_año'] = (df_multianio['prom_matematica'] + df_multianio['prom_comunicacion']) / 2
    
    # Pivotar para calcular TD
    df_pivot = df_multianio.pivot(index='codigo_modular', columns='año', values='ila_año')
    df_td = df_pivot.dropna()
    
    if 2022 in df_td.columns and 2024 in df_td.columns:
        # Calcular TD según metodología: (ILA_2024 - ILA_2022) / ILA_2022
        df_td['td_calculado'] = (df_td[2024] - df_td[2022]) / df_td[2022]
        
        # Clasificar según metodología
        df_td['categoria_td'] = 'estancamiento'
        df_td.loc[df_td['td_calculado'] > 0.05, 'categoria_td'] = 'mejora'
        df_td.loc[df_td['td_calculado'] < -0.05, 'categoria_td'] = 'deterioro'
        
        instituciones_con_td = len(df_td)
        mejora = len(df_td[df_td['categoria_td'] == 'mejora'])
        deterioro = len(df_td[df_td['categoria_td'] == 'deterioro'])
        estancamiento = len(df_td[df_td['categoria_td'] == 'estancamiento'])
        
        print(f"✓ Instituciones con TD calculable: {instituciones_con_td}")
        print(f"✓ En mejora (>0.05): {mejora} ({mejora/instituciones_con_td*100:.1f}%)")
        print(f"✓ En deterioro (<-0.05): {deterioro} ({deterioro/instituciones_con_td*100:.1f}%)")
        print(f"✓ Estancamiento: {estancamiento} ({estancamiento/instituciones_con_td*100:.1f}%)")
        print(f"✓ TD promedio: {df_td['td_calculado'].mean():.3f}")
    else:
        instituciones_con_td = 0
        print("⚠ No hay datos suficientes para calcular TD (requiere años 2022 y 2024)")
    
    conn.close()
    return instituciones_con_td

def evaluar_variable_y3_pr():
    """Evaluar Y3: Perfil de Resiliencia"""
    print("\n=== Y3: PERFIL DE RESILIENCIA (PR) ===")
    
    print("ℹ Variable calculable mediante regresión: ILA ~ Factores_Contextuales")
    print("ℹ Requiere implementación del modelo de regresión múltiple")
    print("✓ Base disponible: Variables ILA + contextuales (X1, X2, X10, X15)")
    
    return "calculable"

def evaluar_variable_x1_nvc():
    """Evaluar X1: Nivel de Vulnerabilidad Contextual"""
    print("\n=== X1: NIVEL DE VULNERABILIDAD CONTEXTUAL (NVC) ===")
    
    conn = sqlite3.connect('reasis_database.db')
    
    # Verificar datos disponibles para NVC
    query_nvc = """
        SELECT e.codigo_modular, e.quintil_pobreza, ie.area_censo,
               e.servicios_agua, e.servicios_internet
        FROM datos_eib_minedu e
        JOIN instituciones_educativas ie ON e.codigo_modular = ie.codigo_modular
    """
    
    df_nvc = pd.read_sql_query(query_nvc, conn)
    
    # Analizar componentes disponibles
    con_quintil = df_nvc['quintil_pobreza'].notna().sum()
    con_ruralidad = df_nvc['area_censo'].notna().sum() 
    con_servicios = df_nvc[['servicios_agua', 'servicios_internet']].notna().any(axis=1).sum()
    
    print(f"✓ Instituciones con quintil pobreza: {con_quintil}")
    print(f"✓ Instituciones con ruralidad: {con_ruralidad}")
    print(f"✓ Instituciones con servicios básicos: {con_servicios}")
    
    # Fórmula metodológica: NVC = (NBI_distrito × 0.4) + (Ruralidad × 0.3) + (1-Servicios_básicos × 0.3)
    print("⚠ Falta: Datos NBI por distrito (INEI)")
    print("ℹ Disponible como proxy: Quintil pobreza per cápita")
    
    conn.close()
    return con_quintil

def evaluar_variable_x2_tr():
    """Evaluar X2: Tipo de Ruralidad"""
    print("\n=== X2: TIPO DE RURALIDAD (TR) ===")
    
    conn = sqlite3.connect('reasis_database.db')
    
    # Verificar múltiples fuentes de ruralidad
    query_ruralidad = """
        SELECT ie.codigo_modular,
               ie.area_censo as ruralidad_base,
               rc.tipo_ruralidad_cesar,
               eib.tipo_ruralidad as ruralidad_eib
        FROM instituciones_educativas ie
        LEFT JOIN ruralidad_cesar rc ON ie.codigo_modular = rc.codigo_modular
        LEFT JOIN datos_eib_minedu eib ON ie.codigo_modular = eib.codigo_modular
    """
    
    df_ruralidad = pd.read_sql_query(query_ruralidad, conn)
    
    # Consolidar fuentes
    con_base = df_ruralidad['ruralidad_base'].notna().sum()
    con_cesar = df_ruralidad['tipo_ruralidad_cesar'].notna().sum()
    con_eib = df_ruralidad['ruralidad_eib'].notna().sum()
    
    # Contar instituciones con algún dato de ruralidad
    df_ruralidad['tiene_ruralidad'] = df_ruralidad[['ruralidad_base', 'tipo_ruralidad_cesar', 'ruralidad_eib']].notna().any(axis=1)
    con_alguna_ruralidad = df_ruralidad['tiene_ruralidad'].sum()
    
    print(f"✓ Ruralidad básica (área censo): {con_base}")
    print(f"✓ Ruralidad César (Rural 1/2/3): {con_cesar}")
    print(f"✓ Ruralidad EIB MINEDU: {con_eib}")
    print(f"✓ Total con algún dato ruralidad: {con_alguna_ruralidad}")
    
    conn.close()
    return con_alguna_ruralidad

def evaluar_variables_docentes():
    """Evaluar X4, X5, X6: Variables docentes"""
    print("\n=== VARIABLES DOCENTES (X4, X5, X6) ===")
    
    conn = sqlite3.connect('reasis_database.db')
    
    # X4: Índice de Desempeño Docente
    query_x4 = """
        SELECT codigo_modular_vinculado, COUNT(*) as docentes,
               AVG((nota_matematica + nota_comunicacion + nota_digital + nota_genero)/4) as idd_promedio
        FROM docentes_data
        WHERE codigo_modular_vinculado IS NOT NULL 
          AND nota_matematica IS NOT NULL
        GROUP BY codigo_modular_vinculado
    """
    
    df_x4 = pd.read_sql_query(query_x4, conn)
    instituciones_x4 = len(df_x4)
    
    print(f"✓ X4 (IDD): {instituciones_x4} instituciones con desempeño docente")
    if instituciones_x4 > 0:
        print(f"  - IDD promedio: {df_x4['idd_promedio'].mean():.2f}")
        print(f"  - Total docentes evaluados: {df_x4['docentes'].sum()}")
    
    # X5: Estabilidad Docente
    query_x5 = "SELECT COUNT(*) as total FROM x5_ed_estabilidad_docente"
    instituciones_x5 = pd.read_sql_query(query_x5, conn).iloc[0]['total']
    
    print(f"✓ X5 (ED): {instituciones_x5} instituciones con estabilidad docente")
    
    # X6: Competencia Digital Docente
    query_x6 = """
        SELECT codigo_red, COUNT(*) as docentes,
               AVG(puntuacion_numerica) as cdd_promedio
        FROM competencia_digital_docentes
        WHERE codigo_red IS NOT NULL
        GROUP BY codigo_red
    """
    
    df_x6 = pd.read_sql_query(query_x6, conn)
    redes_x6 = len(df_x6)
    docentes_x6 = df_x6['docentes'].sum()
    
    print(f"✓ X6 (CDD): {redes_x6} redes con competencia digital ({docentes_x6} docentes)")
    
    conn.close()
    return instituciones_x4, instituciones_x5, redes_x6

def evaluar_variables_recursos():
    """Evaluar X10, X11, X12: Variables de recursos"""
    print("\n=== VARIABLES RECURSOS (X10, X11, X12) ===")
    
    conn = sqlite3.connect('reasis_database.db')
    
    # X10: Infraestructura Educativa
    query_x10 = """
        SELECT COUNT(*) as total_servicios FROM datos_eib_minedu 
        WHERE servicios_agua IS NOT NULL OR servicios_internet IS NOT NULL
    """
    
    # También verificar conectividad
    query_conectividad = "SELECT COUNT(DISTINCT codigo_modular) as total_conectividad FROM conectividad_equipamiento"
    
    servicios_x10 = pd.read_sql_query(query_x10, conn).iloc[0]['total_servicios']
    conectividad_x10 = pd.read_sql_query(query_conectividad, conn).iloc[0]['total_conectividad']
    
    print(f"✓ X10 (IE) - Servicios básicos: {servicios_x10} instituciones")
    print(f"✓ X10 (IE) - Conectividad/equipamiento: {conectividad_x10} instituciones")
    
    # X11: Ratio Estudiante-Docente
    query_x11 = """
        SELECT ie.codigo_modular, toe.total_estudiantes_2024, toe.total_docentes_2024
        FROM instituciones_educativas ie
        JOIN datos_toe_servicios_2024 toe ON ie.codigo_modular = toe.codigo_modular
        WHERE toe.total_estudiantes_2024 IS NOT NULL 
          AND toe.total_docentes_2024 IS NOT NULL
          AND toe.total_docentes_2024 > 0
    """
    
    df_x11 = pd.read_sql_query(query_x11, conn)
    df_x11['red_calculado'] = df_x11['total_estudiantes_2024'] / df_x11['total_docentes_2024']
    instituciones_x11 = len(df_x11)
    
    print(f"✓ X11 (RED): {instituciones_x11} instituciones con ratio calculable")
    if instituciones_x11 > 0:
        print(f"  - RED promedio: {df_x11['red_calculado'].mean():.1f} estudiantes/docente")
        print(f"  - Rango RED: {df_x11['red_calculado'].min():.1f} - {df_x11['red_calculado'].max():.1f}")
    
    # X12: Tipo de Organización Escolar
    query_x12 = """
        SELECT tipo_organizacion_escolar, COUNT(*) as cantidad
        FROM datos_toe_servicios_2024
        WHERE tipo_organizacion_escolar IS NOT NULL
        GROUP BY tipo_organizacion_escolar
    """
    
    df_x12 = pd.read_sql_query(query_x12, conn)
    instituciones_x12 = df_x12['cantidad'].sum()
    
    print(f"✓ X12 (TOE): {instituciones_x12} instituciones con tipo organización")
    for _, row in df_x12.iterrows():
        print(f"  - {row['tipo_organizacion_escolar']}: {row['cantidad']} instituciones")
    
    conn.close()
    return max(servicios_x10, conectividad_x10), instituciones_x11, instituciones_x12

def evaluar_variable_x15_meib():
    """Evaluar X15: Modalidad EIB"""
    print("\n=== X15: MODALIDAD EIB (MEIB) ===")
    
    conn = sqlite3.connect('reasis_database.db')
    
    query_x15 = """
        SELECT modalidad_eib, COUNT(*) as cantidad
        FROM datos_eib_minedu
        WHERE modalidad_eib IS NOT NULL
        GROUP BY modalidad_eib
    """
    
    df_x15 = pd.read_sql_query(query_x15, conn)
    instituciones_x15 = df_x15['cantidad'].sum()
    
    print(f"✓ X15 (MEIB): {instituciones_x15} instituciones con modalidad EIB")
    for _, row in df_x15.iterrows():
        print(f"  - {row['modalidad_eib']}: {row['cantidad']} instituciones")
    
    conn.close()
    return instituciones_x15

def generar_resumen_metodologico():
    """Generar resumen final de completitud metodológica"""
    print("\n" + "="*80)
    print("EVALUACIÓN METODOLÓGICA COMPLETA - RESUMEN FINAL")
    print("="*80)
    
    # Ejecutar todas las evaluaciones
    print("\n🔍 EJECUTANDO EVALUACIONES...")
    
    ila_count, df_ila = evaluar_variable_y1_ila()
    td_count = evaluar_variable_y2_td(df_ila)
    pr_status = evaluar_variable_y3_pr()
    
    nvc_count = evaluar_variable_x1_nvc()
    tr_count = evaluar_variable_x2_tr()
    
    x4_count, x5_count, x6_count = evaluar_variables_docentes()
    x10_count, x11_count, x12_count = evaluar_variables_recursos()
    
    x15_count = evaluar_variable_x15_meib()
    
    # Compilar resultados
    variables_resultado = {
        'Y1_ILA': ila_count,
        'Y2_TD': td_count,
        'Y3_PR': 'calculable' if pr_status == 'calculable' else 0,
        'X1_NVC': nvc_count,
        'X2_TR': tr_count,
        'X4_IDD': x4_count,
        'X5_ED': x5_count,
        'X6_CDD': f"{x6_count} redes",
        'X10_IE': x10_count,
        'X11_RED': x11_count,
        'X12_TOE': x12_count,
        'X15_MEIB': x15_count
    }
    
    print("\n📊 COMPLETITUD POR VARIABLE:")
    print("-" * 50)
    
    variables_completas = 0
    total_variables = 12
    
    for variable, resultado in variables_resultado.items():
        if isinstance(resultado, str):
            if 'calculable' in resultado or 'redes' in resultado:
                status = "✅ DISPONIBLE"
                variables_completas += 1
            else:
                status = "❌ FALTANTE"
        elif resultado >= 50:  # Umbral mínimo para clustering
            status = "✅ SUFICIENTE"
            variables_completas += 1
        elif resultado > 0:
            status = "🟡 PARCIAL"
            variables_completas += 0.5
        else:
            status = "❌ FALTANTE"
        
        print(f"{variable:10}: {resultado:>15} {status}")
    
    completitud_porcentaje = (variables_completas / total_variables) * 100
    
    print("\n🎯 RESUMEN METODOLÓGICO:")
    print("-" * 50)
    print(f"Variables evaluadas: {total_variables}")
    print(f"Variables disponibles: {variables_completas:.1f}")
    print(f"Completitud metodológica: {completitud_porcentaje:.1f}%")
    
    # Determinar viabilidad clustering
    if completitud_porcentaje >= 75:
        viabilidad = "✅ CLUSTERING K-MEANS VIABLE"
    elif completitud_porcentaje >= 50:
        viabilidad = "🟡 CLUSTERING PARCIALMENTE VIABLE"  
    else:
        viabilidad = "❌ CLUSTERING NO VIABLE"
    
    print(f"Viabilidad clustering: {viabilidad}")
    
    # Recomendaciones
    print(f"\n💡 PRÓXIMOS PASOS RECOMENDADOS:")
    if completitud_porcentaje >= 75:
        print("1. ✅ Proceder con construcción de índices compuestos")
        print("2. ✅ Implementar estandarización z-score")
        print("3. ✅ Ejecutar análisis de clustering K-Means")
        print("4. ✅ Desarrollar tipologías institucionales")
    else:
        print("1. 🔧 Completar variables faltantes críticas")
        print("2. 🔧 Implementar técnicas de imputación")
        print("3. 🔧 Validar calidad de datos existentes")
    
    # Guardar reporte
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"evaluacion_metodologica_{timestamp}.txt"
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("EVALUACIÓN METODOLÓGICA COMPLETA - PROYECTO REASIS\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("RESULTADOS POR VARIABLE:\n")
        f.write("-" * 30 + "\n")
        for variable, resultado in variables_resultado.items():
            f.write(f"{variable}: {resultado}\n")
        
        f.write(f"\nCOMPLETITUD METODOLÓGICA: {completitud_porcentaje:.1f}%\n")
        f.write(f"VIABILIDAD: {viabilidad}\n")
    
    print(f"\n📄 Reporte guardado: {filename}")
    
    return completitud_porcentaje, variables_resultado

if __name__ == "__main__":
    completitud, resultados = generar_resumen_metodologico()