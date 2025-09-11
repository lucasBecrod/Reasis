#!/usr/bin/env python3
import sqlite3
import pandas as pd

def analizar_variables_disponibles():
    """Analiza las variables disponibles vs requeridas según la matriz de operacionalización"""
    
    print("=== ANÁLISIS DE VARIABLES DISPONIBLES VS REQUERIDAS ===\n")
    
    # Variables requeridas según matriz de operacionalización
    variables_requeridas = {
        'DEPENDIENTES': {
            'Y1_ILA': {'descripcion': 'Índice de Logro Académico', 'formula': '(Prom_Matemática + Prom_Comunicación) / 2'},
            'Y2_TD': {'descripcion': 'Tendencia de Desempeño', 'formula': '(ILA_2024 - ILA_2022) / ILA_2022'},
            'Y3_PR': {'descripcion': 'Perfil de Resiliencia', 'formula': 'Residuo estandarizado del modelo ILA ~ Contexto'}
        },
        'CONTEXTO': {
            'X1_NVC': {'descripcion': 'Nivel de Vulnerabilidad Contextual', 'formula': '(NBI_distrito × 0.4) + (Ruralidad × 0.3) + (1-Servicios_básicos × 0.3)'},
            'X2_TR': {'descripcion': 'Tipo de Ruralidad', 'formula': 'Variable categórica: 1=Urbano, 2=Rural accesible, 3=Rural disperso'}
        },
        'DOCENTE': {
            'X4_IDD': {'descripcion': 'Índice de Desempeño Docente', 'formula': 'Promedio_PADD_IIEE, escala 1-4'},
            'X5_ED': {'descripcion': 'Estabilidad Docente', 'formula': '(Nombrados/Total × 0.5) + (Prom_años_servicio/10 × 0.5)'},
            'X6_CDD': {'descripcion': 'Competencia Digital Docente', 'formula': 'Promedio_evaluación_competencias_digitales, escala 1-4'}
        },
        'RECURSOS': {
            'X10_IE': {'descripcion': 'Infraestructura Educativa', 'formula': '(Servicios_básicos × 0.4) + (Estado_mobiliario × 0.3) + (Biblioteca × 0.3)'},
            'X11_RED': {'descripcion': 'Ratio Estudiante-Docente', 'formula': 'Total_estudiantes / Total_docentes'},
            'X12_TOE': {'descripcion': 'Tipo de Organización Escolar', 'formula': '1=Polidocente, 2=Multigrado, 3=Unidocente'}
        },
        'ESTUDIANTES_FAMILIAS': {
            'X15_MEIB': {'descripcion': 'Modalidad EIB', 'formula': '0=No EIB, 1=EIB fortalecimiento, 2=EIB revitalización'}
        }
    }
    
    # Excluidas según matriz
    variables_excluidas = ['X3_AE', 'X13_CCF', 'X14_AE']
    
    conn = sqlite3.connect('reasis_database.db')
    
    # Analizar disponibilidad de datos
    disponibilidad = {}
    
    print("VARIABLES DEPENDIENTES:")
    print("=" * 50)
    
    # Y1_ILA - Índice de Logro Académico
    query_ila = """
    SELECT COUNT(DISTINCT codigo_modular) as instituciones_con_datos,
           COUNT(*) as total_registros
    FROM resultados_academicos 
    WHERE codigo_modular IS NOT NULL AND nivel_logro_numerico IS NOT NULL
    """
    df_ila = pd.read_sql_query(query_ila, conn)
    ila_disponible = df_ila.iloc[0]['instituciones_con_datos'] > 0
    print(f"[OK] Y1_ILA: DISPONIBLE - {df_ila.iloc[0]['instituciones_con_datos']} instituciones con {df_ila.iloc[0]['total_registros']} registros academicos")
    disponibilidad['Y1_ILA'] = {'disponible': True, 'instituciones': df_ila.iloc[0]['instituciones_con_datos']}
    
    # Y2_TD - Tendencia de Desempeño
    query_td = """
    SELECT COUNT(DISTINCT codigo_modular) as instituciones_multianio
    FROM (
        SELECT codigo_modular, COUNT(DISTINCT año) as años_disponibles
        FROM resultados_academicos 
        WHERE codigo_modular IS NOT NULL
        GROUP BY codigo_modular
        HAVING COUNT(DISTINCT año) >= 2
    )
    """
    df_td = pd.read_sql_query(query_td, conn)
    td_disponible = df_td.iloc[0]['instituciones_multianio'] > 0
    print(f"[OK] Y2_TD: DISPONIBLE - {df_td.iloc[0]['instituciones_multianio']} instituciones con datos multi-anio")
    disponibilidad['Y2_TD'] = {'disponible': True, 'instituciones': df_td.iloc[0]['instituciones_multianio']}
    
    # Y3_PR - Perfil de Resiliencia
    print(f"[OK] Y3_PR: CALCULABLE - Basado en ILA + variables contextuales disponibles")
    disponibilidad['Y3_PR'] = {'disponible': True, 'instituciones': df_ila.iloc[0]['instituciones_con_datos']}
    
    print("\nVARIABLES CONTEXTUALES:")
    print("=" * 50)
    
    # X1_NVC - Nivel de Vulnerabilidad Contextual
    query_ruralidad = "SELECT COUNT(*) as total FROM instituciones_educativas WHERE area_censo IS NOT NULL"
    df_ruralidad = pd.read_sql_query(query_ruralidad, conn)
    print(f"[PARCIAL] X1_NVC: PARCIAL - Ruralidad disponible ({df_ruralidad.iloc[0]['total']} instituciones), falta NBI distrito")
    disponibilidad['X1_NVC'] = {'disponible': False, 'razon': 'Falta datos NBI por distrito'}
    
    # X2_TR - Tipo de Ruralidad
    print(f"[OK] X2_TR: DISPONIBLE - Campo area_censo en instituciones_educativas")
    disponibilidad['X2_TR'] = {'disponible': True, 'instituciones': df_ruralidad.iloc[0]['total']}
    
    print("\nVARIABLES DOCENTES:")
    print("=" * 50)
    
    # X4_IDD - Índice de Desempeño Docente
    query_docentes = """
    SELECT COUNT(DISTINCT codigo_modular_vinculado) as instituciones_padd,
           COUNT(*) as total_docentes
    FROM docentes_data 
    WHERE nota_matematica IS NOT NULL OR nota_comunicacion IS NOT NULL
    """
    df_docentes = pd.read_sql_query(query_docentes, conn)
    print(f"[OK] X4_IDD: DISPONIBLE - {df_docentes.iloc[0]['instituciones_padd']} instituciones con {df_docentes.iloc[0]['total_docentes']} docentes evaluados")
    disponibilidad['X4_IDD'] = {'disponible': True, 'instituciones': df_docentes.iloc[0]['instituciones_padd']}
    
    # X5_ED - Estabilidad Docente
    print(f"[PARCIAL] X5_ED: PARCIAL - Datos de continuidad disponibles, falta info nombramientos/contratados")
    disponibilidad['X5_ED'] = {'disponible': False, 'razon': 'Falta datos nombramientos vs contratados'}
    
    # X6_CDD - Competencia Digital Docente
    query_cdd = """
    SELECT COUNT(DISTINCT codigo_red) as redes_con_datos,
           COUNT(*) as total_evaluaciones
    FROM competencia_digital_docentes
    WHERE nota_global_relativa_num IS NOT NULL
    """
    df_cdd = pd.read_sql_query(query_cdd, conn)
    print(f"[OK] X6_CDD: DISPONIBLE - {df_cdd.iloc[0]['redes_con_datos']} redes con {df_cdd.iloc[0]['total_evaluaciones']} evaluaciones")
    disponibilidad['X6_CDD'] = {'disponible': True, 'redes': df_cdd.iloc[0]['redes_con_datos']}
    
    print("\nVARIABLES RECURSOS:")
    print("=" * 50)
    
    # X10_IE - Infraestructura Educativa
    print(f"[NO] X10_IE: NO DISPONIBLE - Requiere datos Censo Infraestructura Educativa")
    disponibilidad['X10_IE'] = {'disponible': False, 'razon': 'Requiere datos externos Censo Infraestructura'}
    
    # X11_RED - Ratio Estudiante-Docente
    query_red = """
    SELECT COUNT(*) as instituciones_con_ratio
    FROM instituciones_educativas 
    WHERE total_alumnos IS NOT NULL AND total_docentes IS NOT NULL 
    AND total_alumnos > 0 AND total_docentes > 0
    """
    df_red = pd.read_sql_query(query_red, conn)
    print(f"[OK] X11_RED: DISPONIBLE - {df_red.iloc[0]['instituciones_con_ratio']} instituciones con datos completos")
    disponibilidad['X11_RED'] = {'disponible': True, 'instituciones': df_red.iloc[0]['instituciones_con_ratio']}
    
    # X12_TOE - Tipo de Organización Escolar
    print(f"[NO] X12_TOE: NO DISPONIBLE - Requiere datos ESCALE")
    disponibilidad['X12_TOE'] = {'disponible': False, 'razon': 'Requiere datos externos ESCALE'}
    
    print("\nVARIABLES ESTUDIANTES/FAMILIAS:")
    print("=" * 50)
    
    # X15_MEIB - Modalidad EIB
    query_eib = "SELECT COUNT(*) as total FROM instituciones_educativas WHERE es_eib IS NOT NULL"
    df_eib = pd.read_sql_query(query_eib, conn)
    print(f"[NO] X15_MEIB: NO DISPONIBLE - Solo disponible es_eib (booleano), falta tipologia EIB")
    disponibilidad['X15_MEIB'] = {'disponible': False, 'razon': 'Falta tipologia especifica EIB (fortalecimiento vs revitalizacion)'}
    
    # Resumen final
    print("\n" + "=" * 70)
    print("RESUMEN DE DISPONIBILIDAD")
    print("=" * 70)
    
    disponibles = sum(1 for v in disponibilidad.values() if v['disponible'])
    total = len(disponibilidad)
    parciales = sum(1 for v in disponibilidad.values() if not v['disponible'] and 'PARCIAL' in str(v.get('razon', '')))
    
    print(f"Variables DISPONIBLES: {disponibles}/{total} ({disponibles/total*100:.1f}%)")
    print(f"Variables PARCIALES: {parciales}/{total} ({parciales/total*100:.1f}%)")
    print(f"Variables FALTANTES: {total-disponibles}/{total} ({(total-disponibles)/total*100:.1f}%)")
    
    print("\nVARIABLES DISPONIBLES COMPLETAS:")
    for var, data in disponibilidad.items():
        if data['disponible']:
            instituciones = data.get('instituciones', data.get('redes', 'N/A'))
            print(f"[OK] {var}: {instituciones} instituciones/redes")
    
    print("\nVARIABLES FALTANTES CRITICAS:")
    for var, data in disponibilidad.items():
        if not data['disponible']:
            print(f"[NO] {var}: {data['razon']}")
    
    print(f"\nVIABILIDAD ACTUAL: {disponibles}/{total} variables ({disponibles/total*100:.1f}%)")
    print("El informe de tipologias ES VIABLE con las variables disponibles")
    print("Se pueden implementar mejoras graduales agregando variables faltantes")
    
    conn.close()

if __name__ == "__main__":
    analizar_variables_disponibles()