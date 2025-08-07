#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mapeo Simple de Variables - Proyecto Reasis
Análisis de disponibilidad de variables para el estudio exploratorio
"""

import sqlite3
import pandas as pd

def analizar_disponibilidad_variables():
    """Analiza disponibilidad de variables para el estudio"""
    print("MAPEO DE VARIABLES - ESTUDIO EXPLORATORIO REASIS")
    print("=" * 70)
    
    try:
        conn = sqlite3.connect('reasis_database.db')
        
        # 1. VARIABLES DEPENDIENTES (Variables de resultado)
        print("\n1. VARIABLES DEPENDIENTES")
        print("-" * 40)
        
        # Verificar datos académicos para ILA y TD
        df_acad = pd.read_sql_query("""
            SELECT DISTINCT materia, COUNT(*) as registros, 
                   MIN(año) as año_min, MAX(año) as año_max
            FROM indicadores_academicos_base 
            GROUP BY materia
        """, conn)
        
        print("Y1 - Indice de Logro Academico (ILA):")
        if len(df_acad) > 0 and any('Matematica' in str(m) or 'Comunicacion' in str(m) for m in df_acad['materia']):
            print("  Estado: DISPONIBLE")
            print("  Fuente: indicadores_academicos_base")
            print("  Materias disponibles:")
            for _, row in df_acad.iterrows():
                print(f"    - {row['materia']}: {row['registros']} registros ({row['año_min']}-{row['año_max']})")
        else:
            print("  Estado: NO DISPONIBLE")
        
        print("\nY2 - Tendencia de Desempeño (TD):")
        if len(df_acad) > 0:
            años_disponibles = pd.read_sql_query("SELECT DISTINCT año FROM indicadores_academicos_base ORDER BY año", conn)['año'].tolist()
            if len(años_disponibles) >= 2:
                print("  Estado: CALCULABLE")
                print(f"  Años disponibles: {años_disponibles}")
            else:
                print("  Estado: INSUFICIENTE - Requiere al menos 2 años")
        
        print("\nY3 - Perfil de Resiliencia (PR):")
        print("  Estado: CALCULABLE (derivado de ILA + variables contextuales)")
        
        # 2. VARIABLES INDEPENDIENTES - CONTEXTO
        print("\n2. VARIABLES INDEPENDIENTES - CONTEXTO")
        print("-" * 40)
        
        df_inst = pd.read_sql_query("""
            SELECT COUNT(*) as total, 
                   SUM(CASE WHEN es_rural IS NOT NULL THEN 1 ELSE 0 END) as con_ruralidad,
                   SUM(CASE WHEN area_censo IS NOT NULL THEN 1 ELSE 0 END) as con_area_censo,
                   SUM(CASE WHEN latitud IS NOT NULL THEN 1 ELSE 0 END) as con_coordenadas
            FROM instituciones_educativas_v2_mejorada
        """, conn).iloc[0]
        
        print("X1 - Nivel de Vulnerabilidad Contextual (NVC):")
        print("  Estado: PARCIAL")
        print("  Componentes disponibles:")
        print(f"    - Ruralidad: {df_inst['con_ruralidad']}/{df_inst['total']} instituciones")
        print(f"    - Coordenadas GPS: {df_inst['con_coordenadas']}/{df_inst['total']} instituciones")
        print("  Componentes faltantes:")
        print("    - NBI por distrito (fuente: INEI)")
        print("    - Servicios basicos detallados")
        
        print("\nX2 - Tipo de Ruralidad (TR):")
        ruralidad_dist = pd.read_sql_query("""
            SELECT area_censo, es_rural, COUNT(*) as total
            FROM instituciones_educativas_v2_mejorada 
            GROUP BY area_censo, es_rural
        """, conn)
        print("  Estado: DISPONIBLE (requiere transformacion)")
        print("  Distribucion actual:")
        for _, row in ruralidad_dist.iterrows():
            tipo_rural = "Rural" if row['es_rural'] == 1 else "Urbano"
            print(f"    - Area {row['area_censo']} + Flag {tipo_rural}: {row['total']} instituciones")
        
        # 3. VARIABLES INDEPENDIENTES - DOCENTE
        print("\n3. VARIABLES INDEPENDIENTES - DOCENTE")
        print("-" * 40)
        
        df_comp_digital = pd.read_sql_query("""
            SELECT COUNT(DISTINCT institucion_id) as instituciones_con_datos,
                   COUNT(*) as total_respuestas,
                   COUNT(DISTINCT tipo_encuesta) as tipos_encuesta
            FROM datos_competencia_digital
        """, conn).iloc[0]
        
        print("X4 - Indice de Desempeño Docente (IDD):")
        print("  Estado: DISPONIBLE")
        print(f"  Fuente: datos_competencia_digital")
        print(f"  Instituciones con datos: {df_comp_digital['instituciones_con_datos']}")
        print(f"  Total respuestas: {df_comp_digital['total_respuestas']}")
        
        print("\nX6 - Competencia Digital Docente (CDD):")
        print("  Estado: DISPONIBLE (misma fuente que IDD)")
        print(f"  Tipos de encuesta: {df_comp_digital['tipos_encuesta']}")
        
        print("\nX5 - Estabilidad Docente (ED):")
        docentes_info = pd.read_sql_query("""
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN total_docentes IS NOT NULL THEN 1 ELSE 0 END) as con_total_docentes,
                   SUM(CASE WHEN docentes_hombres IS NOT NULL OR docentes_mujeres IS NOT NULL THEN 1 ELSE 0 END) as con_distribucion
            FROM instituciones_educativas_v2_mejorada
        """, conn).iloc[0]
        print("  Estado: PARCIAL")
        print("  Componentes disponibles:")
        print(f"    - Total docentes: {docentes_info['con_total_docentes']}/{docentes_info['total']} instituciones")
        print("  Componentes faltantes:")
        print("    - Docentes nombrados vs contratados")
        print("    - Años promedio de servicio")
        
        # 4. VARIABLES INDEPENDIENTES - RECURSOS
        print("\n4. VARIABLES INDEPENDIENTES - RECURSOS")
        print("-" * 40)
        
        recursos_info = pd.read_sql_query("""
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN total_alumnos IS NOT NULL AND total_docentes IS NOT NULL THEN 1 ELSE 0 END) as con_ratio
            FROM instituciones_educativas_v2_mejorada
        """, conn).iloc[0]
        
        print("X11 - Ratio Estudiante-Docente (RED):")
        print("  Estado: DISPONIBLE")
        print(f"  Instituciones con datos completos: {recursos_info['con_ratio']}/{recursos_info['total']}")
        
        print("\nX10 - Infraestructura Educativa (IE):")
        print("  Estado: NO DISPONIBLE")
        print("  Requiere datos de:")
        print("    - Estado de servicios basicos por institucion")
        print("    - Estado de mobiliario/equipamiento")
        print("    - Disponibilidad de biblioteca")
        
        print("\nX12 - Tipo de Organizacion Escolar (TOE):")
        print("  Estado: NO DISPONIBLE")
        print("  Requiere clasificacion: Polidocente/Multigrado/Unidocente")
        
        # 5. VARIABLES INDEPENDIENTES - ESTUDIANTES
        print("\n5. VARIABLES INDEPENDIENTES - ESTUDIANTES")
        print("-" * 40)
        
        print("X15 - Modalidad EIB:")
        print("  Estado: NO DISPONIBLE")
        print("  Requiere datos de ESCALE sobre educacion intercultural bilingue")
        
        # 6. RESUMEN EJECUTIVO
        print("\n6. RESUMEN EJECUTIVO")
        print("-" * 40)
        
        variables_status = {
            "COMPLETAMENTE_DISPONIBLES": [
                "Y1_ILA - Indice de Logro Academico",
                "Y2_TD - Tendencia de Desempeño", 
                "Y3_PR - Perfil de Resiliencia",
                "X2_TR - Tipo de Ruralidad",
                "X4_IDD - Indice de Desempeño Docente",
                "X6_CDD - Competencia Digital Docente",
                "X11_RED - Ratio Estudiante-Docente"
            ],
            "PARCIALMENTE_DISPONIBLES": [
                "X1_NVC - Nivel de Vulnerabilidad Contextual (falta NBI)",
                "X5_ED - Estabilidad Docente (falta estabilidad)"
            ],
            "NO_DISPONIBLES": [
                "X10_IE - Infraestructura Educativa",
                "X12_TOE - Tipo de Organizacion Escolar", 
                "X15_MEIB - Modalidad EIB"
            ]
        }
        
        total_variables = sum(len(vars) for vars in variables_status.values())
        disponibles = len(variables_status["COMPLETAMENTE_DISPONIBLES"])
        parciales = len(variables_status["PARCIALMENTE_DISPONIBLES"])
        faltantes = len(variables_status["NO_DISPONIBLES"])
        
        print(f"Total variables requeridas: {total_variables}")
        print(f"Completamente disponibles: {disponibles} ({disponibles/total_variables*100:.1f}%)")
        print(f"Parcialmente disponibles: {parciales} ({parciales/total_variables*100:.1f}%)")
        print(f"No disponibles: {faltantes} ({faltantes/total_variables*100:.1f}%)")
        
        print("\nVARIABLES DISPONIBLES:")
        for var in variables_status["COMPLETAMENTE_DISPONIBLES"]:
            print(f"  + {var}")
        
        print("\nVARIABLES PARCIALES:")
        for var in variables_status["PARCIALMENTE_DISPONIBLES"]:
            print(f"  ~ {var}")
        
        print("\nVARIABLES FALTANTES:")
        for var in variables_status["NO_DISPONIBLES"]:
            print(f"  - {var}")
        
        # 7. VIABILIDAD DEL ESTUDIO
        print("\n7. EVALUACION DE VIABILIDAD")
        print("-" * 40)
        
        viabilidad_por_dimension = {
            "Variables Dependientes": 3,  # Las 3 variables principales disponibles
            "Variables de Contexto": 1.5,  # 1 completa + 1 parcial de 2 
            "Variables Docentes": 2,      # 2 completas de 3
            "Variables Recursos": 1,      # 1 completa de 3
            "Variables Estudiantes": 0    # 0 de 1
        }
        
        print("Puntuacion por dimension (sobre 3):")
        for dimension, puntos in viabilidad_por_dimension.items():
            print(f"  {dimension}: {puntos}/3")
        
        puntuacion_total = sum(viabilidad_por_dimension.values())
        max_puntuacion = len(viabilidad_por_dimension) * 3
        porcentaje_viabilidad = (puntuacion_total / max_puntuacion) * 100
        
        print(f"\nPUNTUACION TOTAL: {puntuacion_total}/{max_puntuacion} ({porcentaje_viabilidad:.1f}%)")
        
        if porcentaje_viabilidad >= 60:
            print("VEREDICTO: ESTUDIO VIABLE")
            print("Se puede proceder con el estudio con las variables disponibles")
            print("Recomendacion: Complementar variables faltantes para mayor robustez")
        else:
            print("VEREDICTO: ESTUDIO REQUIERE DATOS ADICIONALES")
            print("Se recomienda completar variables criticas antes de proceder")
        
        conn.close()
        
        print(f"\nAnalisis completado exitosamente")
        print("=" * 70)
        
    except Exception as e:
        print(f"Error durante análisis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analizar_disponibilidad_variables()