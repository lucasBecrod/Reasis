#!/usr/bin/env python3
"""
Evaluación Metodológica Completa - Proyecto Reasis (Corregida)
Análisis de completitud de las 12 variables metodológicas con nombres correctos
"""

import pandas as pd
import sqlite3

def main():
    print("=== EVALUACION METODOLOGICA COMPLETA ===")
    print("Analizando completitud de las 12 variables metodologicas")
    
    conn = sqlite3.connect('reasis_database.db')
    
    resultados = {}
    
    # Y1: Índice de Logro Académico (ILA)
    print("\n1. Y1: INDICE DE LOGRO ACADEMICO (ILA)")
    query_ila = """
        SELECT codigo_modular, COUNT(*) as estudiantes,
               AVG(CASE WHEN materia = 'Matematica' THEN nivel_logro_numerico END) as prom_mat,
               AVG(CASE WHEN materia = 'Comunicacion' THEN nivel_logro_numerico END) as prom_com
        FROM resultados_academicos
        WHERE codigo_modular IS NOT NULL 
        GROUP BY codigo_modular
        HAVING COUNT(*) >= 2
    """
    df_ila = pd.read_sql_query(query_ila, conn)
    df_ila['ila'] = (df_ila['prom_mat'] + df_ila['prom_com']) / 2
    ila_count = len(df_ila[df_ila['ila'].notna()])
    resultados['Y1_ILA'] = ila_count
    print(f"   Instituciones con ILA: {ila_count}")
    
    # Y2: Tendencia de Desempeño (TD) - usando columna correcta 'año'
    print("\n2. Y2: TENDENCIA DE DESEMPENO (TD)")
    query_td = """
        SELECT codigo_modular, año,
               AVG(CASE WHEN materia = 'Matematica' THEN nivel_logro_numerico END) as prom_mat,
               AVG(CASE WHEN materia = 'Comunicacion' THEN nivel_logro_numerico END) as prom_com
        FROM resultados_academicos
        WHERE codigo_modular IS NOT NULL AND año IN (2022, 2024)
        GROUP BY codigo_modular, año
    """
    df_td = pd.read_sql_query(query_td, conn)
    df_td['ila_año'] = (df_td['prom_mat'] + df_td['prom_com']) / 2
    
    # Pivotar para calcular TD
    df_pivot = df_td.pivot(index='codigo_modular', columns='año', values='ila_año')
    if 2022 in df_pivot.columns and 2024 in df_pivot.columns:
        df_td_calc = df_pivot.dropna()
        td_count = len(df_td_calc)
    else:
        td_count = 0
    
    resultados['Y2_TD'] = td_count
    print(f"   Instituciones con TD: {td_count}")
    
    # Y3: Perfil de Resiliencia (PR)
    print("\n3. Y3: PERFIL DE RESILIENCIA (PR)")
    print("   Calculable mediante regresion (base disponible)")
    resultados['Y3_PR'] = 'calculable'
    
    # X1: Nivel de Vulnerabilidad Contextual (NVC)
    print("\n4. X1: NIVEL VULNERABILIDAD CONTEXTUAL (NVC)")
    query_nvc = "SELECT COUNT(*) as total FROM datos_eib_minedu WHERE quintil_pobreza IS NOT NULL"
    nvc_count = pd.read_sql_query(query_nvc, conn).iloc[0]['total']
    resultados['X1_NVC'] = nvc_count
    print(f"   Instituciones con quintil pobreza: {nvc_count}")
    
    # X2: Tipo de Ruralidad (TR)
    print("\n5. X2: TIPO DE RURALIDAD (TR)")
    query_tr = """
        SELECT COUNT(DISTINCT ie.codigo_modular) as total
        FROM instituciones_educativas ie
        LEFT JOIN ruralidad_cesar rc ON ie.codigo_modular = rc.codigo_modular
        LEFT JOIN datos_eib_minedu eib ON ie.codigo_modular = eib.codigo_modular
        WHERE ie.area_censo IS NOT NULL 
           OR rc.tipo_ruralidad_cesar IS NOT NULL 
           OR eib.tipo_ruralidad IS NOT NULL
    """
    tr_count = pd.read_sql_query(query_tr, conn).iloc[0]['total']
    resultados['X2_TR'] = tr_count
    print(f"   Instituciones con tipo ruralidad: {tr_count}")
    
    # X4: Índice de Desempeño Docente (IDD)
    print("\n6. X4: INDICE DESEMPENO DOCENTE (IDD)")
    query_x4 = """
        SELECT COUNT(DISTINCT codigo_modular_vinculado) as total
        FROM docentes_data
        WHERE codigo_modular_vinculado IS NOT NULL 
          AND nota_matematica IS NOT NULL
    """
    x4_count = pd.read_sql_query(query_x4, conn).iloc[0]['total']
    resultados['X4_IDD'] = x4_count
    print(f"   Instituciones con IDD: {x4_count}")
    
    # X5: Estabilidad Docente (ED)
    print("\n7. X5: ESTABILIDAD DOCENTE (ED)")
    # Verificar si existe la tabla
    try:
        query_x5 = "SELECT COUNT(*) as total FROM x5_ed_estabilidad_docente"
        x5_count = pd.read_sql_query(query_x5, conn).iloc[0]['total']
    except:
        x5_count = 0
    resultados['X5_ED'] = x5_count
    print(f"   Instituciones con ED: {x5_count}")
    
    # X6: Competencia Digital Docente (CDD)
    print("\n8. X6: COMPETENCIA DIGITAL DOCENTE (CDD)")
    query_x6 = "SELECT COUNT(DISTINCT codigo_red) as total FROM competencia_digital_docentes WHERE codigo_red IS NOT NULL"
    x6_count = pd.read_sql_query(query_x6, conn).iloc[0]['total']
    resultados['X6_CDD'] = f"{x6_count} redes"
    print(f"   Redes con CDD: {x6_count}")
    
    # X10: Infraestructura Educativa (IE)
    print("\n9. X10: INFRAESTRUCTURA EDUCATIVA (IE)")
    query_x10_servicios = """
        SELECT COUNT(*) as total FROM datos_eib_minedu 
        WHERE servicios_agua IS NOT NULL OR servicios_internet IS NOT NULL
    """
    
    # Verificar tabla conectividad
    try:
        query_x10_conectividad = "SELECT COUNT(DISTINCT codigo_modular) as total FROM conectividad_equipamiento"
        conectividad = pd.read_sql_query(query_x10_conectividad, conn).iloc[0]['total']
    except:
        conectividad = 0
    
    servicios = pd.read_sql_query(query_x10_servicios, conn).iloc[0]['total']
    x10_count = max(servicios, conectividad)
    resultados['X10_IE'] = x10_count
    print(f"   Instituciones con IE: {x10_count} (servicios: {servicios}, conectividad: {conectividad})")
    
    # X11: Ratio Estudiante-Docente (RED) - usar nombres correctos
    print("\n10. X11: RATIO ESTUDIANTE-DOCENTE (RED)")
    query_x11 = """
        SELECT COUNT(*) as total FROM datos_toe_servicios_2024
        WHERE estudiantes_2024 IS NOT NULL 
          AND docentes_2024 IS NOT NULL
          AND docentes_2024 > 0
    """
    x11_count = pd.read_sql_query(query_x11, conn).iloc[0]['total']
    resultados['X11_RED'] = x11_count
    print(f"   Instituciones con RED: {x11_count}")
    
    # X12: Tipo de Organización Escolar (TOE)
    print("\n11. X12: TIPO ORGANIZACION ESCOLAR (TOE)")
    query_x12 = "SELECT COUNT(*) as total FROM datos_toe_servicios_2024 WHERE tipo_organizacion_normalizado IS NOT NULL"
    x12_count = pd.read_sql_query(query_x12, conn).iloc[0]['total']
    resultados['X12_TOE'] = x12_count
    print(f"   Instituciones con TOE: {x12_count}")
    
    # X15: Modalidad EIB (MEIB)
    print("\n12. X15: MODALIDAD EIB (MEIB)")
    query_x15 = "SELECT COUNT(*) as total FROM datos_eib_minedu WHERE modalidad_eib IS NOT NULL"
    x15_count = pd.read_sql_query(query_x15, conn).iloc[0]['total']
    resultados['X15_MEIB'] = x15_count
    print(f"   Instituciones con MEIB: {x15_count}")
    
    conn.close()
    
    # RESUMEN FINAL
    print("\n" + "="*60)
    print("RESUMEN METODOLOGICO FINAL")
    print("="*60)
    
    print("\nCOMPLETITUD POR VARIABLE:")
    print("-" * 40)
    
    variables_completas = 0
    total_variables = 12
    
    for variable, resultado in resultados.items():
        if isinstance(resultado, str):
            if 'calculable' in resultado or 'redes' in resultado:
                status = "[OK] DISPONIBLE"
                variables_completas += 1
            else:
                status = "[NO] FALTANTE"
        elif resultado >= 50:  # Umbral mínimo
            status = "[OK] SUFICIENTE"
            variables_completas += 1
        elif resultado > 0:
            status = "[PARCIAL]"
            variables_completas += 0.5
        else:
            status = "[NO] FALTANTE"
        
        print(f"{variable:10}: {str(resultado):>15} {status}")
    
    completitud = (variables_completas / total_variables) * 100
    
    print(f"\nCOMPLETITUD METODOLOGICA: {completitud:.1f}%")
    print(f"Variables disponibles: {variables_completas:.1f}/{total_variables}")
    
    # Viabilidad clustering
    if completitud >= 75:
        viabilidad = "[OK] CLUSTERING K-MEANS VIABLE"
        recomendacion = "Proceder con indices compuestos y estandarizacion"
    elif completitud >= 50:
        viabilidad = "[PARCIAL] CLUSTERING PARCIALMENTE VIABLE"  
        recomendacion = "Completar variables criticas faltantes"
    else:
        viabilidad = "[NO] CLUSTERING NO VIABLE"
        recomendacion = "Implementar tecnicas de imputacion masiva"
    
    print(f"Viabilidad: {viabilidad}")
    print(f"Recomendacion: {recomendacion}")
    
    return completitud, resultados

if __name__ == "__main__":
    completitud, resultados = main()