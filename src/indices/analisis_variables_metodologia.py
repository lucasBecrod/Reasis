#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Análisis de Variables según Metodología - Proyecto Reasis
Mapeo de variables disponibles vs requeridas según matriz de operacionalización
"""

import sqlite3
import pandas as pd
from pathlib import Path

def mapear_variables_disponibles():
    """Mapea variables disponibles vs requeridas según metodología del estudio"""
    print("MAPEO DE VARIABLES DISPONIBLES VS METODOLOGIA DEL ESTUDIO")
    print("=" * 80)
    
    # MATRIZ DE OPERACIONALIZACIÓN - VARIABLES REQUERIDAS
    print("\n1. VARIABLES REQUERIDAS SEGÚN MATRIZ DE OPERACIONALIZACIÓN")
    print("-" * 60)
    
    variables_metodologia = {
        "DEPENDIENTES": {
            "Y1_ILA": {
                "nombre": "Índice de Logro Académico",
                "formula": "(Promedio_Notas_Matemática + Promedio_Notas_Comunicación) / 2",
                "fuente_requerida": "RER - Datos de 3 años",
                "responsable": "Lucas"
            },
            "Y2_TD": {
                "nombre": "Tendencia de Desempeño",
                "formula": "(ILA_2024 - ILA_2022) / ILA_2022",
                "fuente_requerida": "RER - Cálculo derivado",
                "responsable": "Lucas"
            },
            "Y3_PR": {
                "nombre": "Perfil de Resiliencia",
                "formula": "Residuo estandarizado del modelo ILA ~ Contexto",
                "fuente_requerida": "Cálculo estadístico",
                "responsable": "Lucas"
            }
        },
        "INDEPENDIENTES_CONTEXTO": {
            "X1_NVC": {
                "nombre": "Nivel de Vulnerabilidad Contextual",
                "formula": "(NBI_distrito × 0.4) + (Ruralidad × 0.3) + (1-Servicios_básicos × 0.3)",
                "fuente_requerida": "INEI, ESCALE, Censo Infraestructura",
                "responsable": "Lucas"
            },
            "X2_TR": {
                "nombre": "Tipo de Ruralidad",
                "valores": "1=Urbano, 2=Rural accesible, 3=Rural disperso",
                "fuente_requerida": "ESCALE",
                "responsable": "Gloria"
            }
        },
        "INDEPENDIENTES_DOCENTE": {
            "X4_IDD": {
                "nombre": "Índice de Desempeño Docente",
                "formula": "Promedio_PAAD_IIEE",
                "fuente_requerida": "Listado de formación",
                "responsable": "Gloria"
            },
            "X5_ED": {
                "nombre": "Estabilidad Docente",
                "formula": "(Docentes_nombrados/Total_docentes × 0.5) + (Promedio_años_servicio_red/10 × 0.5)",
                "fuente_requerida": "Info de la red, Censo educativo",
                "responsable": "Gloria"
            },
            "X6_CDD": {
                "nombre": "Competencia Digital Docente",
                "formula": "Promedio_puntaje_evaluación_competencias_digitales",
                "fuente_requerida": "Eval. competencias digitales PAAD 2024",
                "responsable": "Gloria, con información de Escuela Digital"
            }
        },
        "INDEPENDIENTES_RECURSOS": {
            "X10_IE": {
                "nombre": "Infraestructura Educativa",
                "formula": "(Servicios_básicos × 0.4) + (Estado_mobiliario × 0.3) + (Tiene_biblioteca × 0.3)",
                "fuente_requerida": "Censo infraestructura educativa",
                "responsable": "Gloria"
            },
            "X11_RED": {
                "nombre": "Ratio Estudiante-Docente",
                "formula": "Total_estudiantes / Total_docentes",
                "fuente_requerida": "ESCALE",
                "responsable": "Lucas"
            },
            "X12_TOE": {
                "nombre": "Tipo de Organización Escolar",
                "valores": "1=Polidocente completo, 2=Multigrado, 3=Unidocente",
                "fuente_requerida": "ESCALE, Censo",
                "responsable": "Gloria"
            }
        },
        "INDEPENDIENTES_ESTUDIANTES": {
            "X15_MEIB": {
                "nombre": "Modalidad EIB",
                "valores": "0=No EIB, 1=EIB de fortalecimiento, 2=EIB de revitalización",
                "fuente_requerida": "ESCALE",
                "responsable": "Gloria"
            }
        }
    }
    
    for categoria, variables in variables_metodologia.items():
        print(f"\n{categoria.replace('_', ' ')}:")
        for codigo, var in variables.items():
            print(f"  {codigo}: {var['nombre']}")
            if 'formula' in var:
                print(f"      Fórmula: {var['formula']}")
            if 'valores' in var:
                print(f"      Valores: {var['valores']}")
            print(f"      Fuente requerida: {var['fuente_requerida']}")
            print(f"      Responsable: {var['responsable']}")
            print()
    
    # ANÁLISIS DE DISPONIBILIDAD EN BASE DE DATOS ACTUAL
    print("\n2. ANÁLISIS DE DISPONIBILIDAD EN BASE DE DATOS ACTUAL")
    print("-" * 60)
    
    try:
        conn = sqlite3.connect('reasis_database.db')
        
        # Obtener estructura de cada tabla
        print("ESTRUCTURA DE TABLAS ACTUALES:")
        tablas = ['instituciones_educativas_v2_mejorada', 'indicadores_academicos_base', 'datos_competencia_digital']
        
        estructura_bd = {}
        for tabla in tablas:
            try:
                df = pd.read_sql_query(f"SELECT * FROM {tabla} LIMIT 1", conn)
                estructura_bd[tabla] = list(df.columns)
                print(f"\n{tabla}: {len(df.columns)} columnas")
                print(f"  Campos: {', '.join(df.columns[:10])}{'...' if len(df.columns) > 10 else ''}")
            except Exception as e:
                print(f"  Error al leer {tabla}: {e}")
        
        # MAPEO DETALLADO VARIABLE POR VARIABLE
        print(f"\n3. MAPEO DETALLADO VARIABLE POR VARIABLE")
        print("-" * 60)
        
        # Función para evaluar disponibilidad
        def evaluar_disponibilidad(codigo_var, info_var, estructura):
            evaluacion = {
                "codigo": codigo_var,
                "nombre": info_var["nombre"],
                "disponible": False,
                "parcial": False,
                "campos_disponibles": [],
                "campos_faltantes": [],
                "tabla_origen": None,
                "accion_requerida": ""
            }
            
            # Variables dependientes (requieren datos académicos)
            if codigo_var.startswith('Y'):
                if 'indicadores_academicos_base' in estructura:
                    campos_acad = estructura['indicadores_academicos_base']
                    if any(campo in campos_acad for campo in ['materia', 'promedio_notas', 'año']):
                        evaluacion["disponible"] = True
                        evaluacion["tabla_origen"] = "indicadores_academicos_base"
                        evaluacion["campos_disponibles"] = ['materia', 'promedio_notas', 'año']
                        evaluacion["accion_requerida"] = "Aplicar fórmula de cálculo"
                    else:
                        evaluacion["campos_faltantes"] = ['datos_academicos_completos']
                        evaluacion["accion_requerida"] = "Completar datos académicos"
            
            # Variables de contexto
            elif codigo_var in ['X1_NVC']:
                if 'instituciones_educativas_v2_mejorada' in estructura:
                    campos_inst = estructura['instituciones_educativas_v2_mejorada']
                    disponibles = []
                    faltantes = []
                    
                    if any(campo in campos_inst for campo in ['es_rural', 'area_censo']):
                        disponibles.append('ruralidad')
                    if any(campo in campos_inst for campo in ['latitud', 'longitud']):
                        disponibles.append('coordenadas_para_georreferenciacion')
                    
                    faltantes = ['nbi_distrito', 'servicios_basicos_detallados']
                    
                    evaluacion["parcial"] = True
                    evaluacion["campos_disponibles"] = disponibles
                    evaluacion["campos_faltantes"] = faltantes
                    evaluacion["tabla_origen"] = "instituciones_educativas_v2_mejorada + datos_externos"
                    evaluacion["accion_requerida"] = "Integrar datos NBI distrito + servicios básicos"
            
            elif codigo_var in ['X2_TR']:
                if 'instituciones_educativas_v2_mejorada' in estructura:
                    campos_inst = estructura['instituciones_educativas_v2_mejorada']
                    if any(campo in campos_inst for campo in ['area_censo', 'es_rural']):
                        evaluacion["disponible"] = True
                        evaluacion["tabla_origen"] = "instituciones_educativas_v2_mejorada"
                        evaluacion["campos_disponibles"] = ['area_censo', 'es_rural']
                        evaluacion["accion_requerida"] = "Transformar a escala ordinal 1-3"
            
            # Variables docentes
            elif codigo_var in ['X4_IDD', 'X6_CDD']:
                if 'datos_competencia_digital' in estructura:
                    evaluacion["disponible"] = True
                    evaluacion["tabla_origen"] = "datos_competencia_digital"
                    evaluacion["campos_disponibles"] = ['tipo_encuesta', 'respuesta']
                    evaluacion["accion_requerida"] = "Calcular promedios por institución"
            
            elif codigo_var in ['X5_ED']:
                if 'instituciones_educativas_v2_mejorada' in estructura:
                    campos_inst = estructura['instituciones_educativas_v2_mejorada']
                    disponibles = []
                    faltantes = []
                    
                    if any(campo in campos_inst for campo in ['total_docentes', 'docentes_hombres', 'docentes_mujeres']):
                        disponibles.append('total_docentes')
                    
                    faltantes = ['docentes_nombrados', 'años_servicio_promedio']
                    
                    evaluacion["parcial"] = True
                    evaluacion["campos_disponibles"] = disponibles
                    evaluacion["campos_faltantes"] = faltantes
                    evaluacion["tabla_origen"] = "instituciones_educativas_v2_mejorada + datos_adicionales"
                    evaluacion["accion_requerida"] = "Obtener datos de estabilidad docente"
            
            # Variables de recursos
            elif codigo_var in ['X11_RED']:
                if 'instituciones_educativas_v2_mejorada' in estructura:
                    campos_inst = estructura['instituciones_educativas_v2_mejorada']
                    if all(campo in campos_inst for campo in ['total_alumnos', 'total_docentes']):
                        evaluacion["disponible"] = True
                        evaluacion["tabla_origen"] = "instituciones_educativas_v2_mejorada"
                        evaluacion["campos_disponibles"] = ['total_alumnos', 'total_docentes']
                        evaluacion["accion_requerida"] = "Aplicar fórmula simple"
            
            elif codigo_var in ['X10_IE', 'X12_TOE', 'X15_MEIB']:
                evaluacion["campos_faltantes"] = ['datos_infraestructura_detallados']
                evaluacion["accion_requerida"] = "Integrar datos de ESCALE/Censo Infraestructura"
            
            return evaluacion
        
        # Evaluar cada variable
        evaluaciones = {}
        for categoria, variables in variables_metodologia.items():
            evaluaciones[categoria] = {}
            for codigo, info in variables.items():
                evaluaciones[categoria][codigo] = evaluar_disponibilidad(codigo, info, estructura_bd)
        
        # Mostrar resultados del mapeo
        for categoria, variables in evaluaciones.items():
            print(f"\n{categoria.replace('_', ' ')}:")
            for codigo, eval_var in variables.items():
                if eval_var["disponible"]:
                    estado = "✓ DISPONIBLE"
                elif eval_var["parcial"]:
                    estado = "◐ PARCIAL"
                else:
                    estado = "✗ FALTANTE"
                
                print(f"  {codigo}: {eval_var['nombre']} - {estado}")
                if eval_var["tabla_origen"]:
                    print(f"      Fuente: {eval_var['tabla_origen']}")
                if eval_var["campos_disponibles"]:
                    print(f"      Disponibles: {', '.join(eval_var['campos_disponibles'])}")
                if eval_var["campos_faltantes"]:
                    print(f"      Faltantes: {', '.join(eval_var['campos_faltantes'])}")
                print(f"      Acción requerida: {eval_var['accion_requerida']}")
                print()
        
        # RESUMEN EJECUTIVO
        print(f"\n4. RESUMEN EJECUTIVO DE DISPONIBILIDAD")
        print("-" * 60)
        
        total_variables = sum(len(vars) for vars in variables_metodologia.values())
        disponibles = sum(1 for cat in evaluaciones.values() for eval_var in cat.values() if eval_var["disponible"])
        parciales = sum(1 for cat in evaluaciones.values() for eval_var in cat.values() if eval_var["parcial"])
        faltantes = total_variables - disponibles - parciales
        
        print(f"Total variables requeridas: {total_variables}")
        print(f"✓ Completamente disponibles: {disponibles} ({disponibles/total_variables*100:.1f}%)")
        print(f"◐ Parcialmente disponibles: {parciales} ({parciales/total_variables*100:.1f}%)")
        print(f"✗ Faltantes: {faltantes} ({faltantes/total_variables*100:.1f}%)")
        
        # VIABILIDAD DEL ESTUDIO
        print(f"\n5. EVALUACIÓN DE VIABILIDAD DEL ESTUDIO")
        print("-" * 60)
        
        viabilidad_variables = {
            "VARIABLES_DEPENDIENTES": disponibles >= 1,  # Al menos ILA debe ser calculable
            "VARIABLES_CONTEXTO": parciales >= 1,        # Al menos ruralidad disponible
            "VARIABLES_DOCENTES": disponibles >= 1,      # Al menos datos PADD disponibles  
            "VARIABLES_RECURSOS": disponibles >= 1       # Al menos ratio estudiante-docente
        }
        
        viabilidad_general = sum(viabilidad_variables.values()) >= 3
        
        print("Evaluación por dimensión:")
        for dimension, viable in viabilidad_variables.items():
            estado = "✓ VIABLE" if viable else "✗ NO VIABLE"
            print(f"  {dimension.replace('_', ' ')}: {estado}")
        
        print(f"\nVIABILIDAD GENERAL DEL ESTUDIO: {'✓ VIABLE' if viabilidad_general else '✗ NO VIABLE'}")
        
        if viabilidad_general:
            print("\nEL ESTUDIO ES VIABLE CON LOS DATOS ACTUALES")
            print("Se puede proceder con limitaciones y adaptaciones metodológicas")
        else:
            print("\nEL ESTUDIO REQUIERE DATOS ADICIONALES CRÍTICOS")
            print("Se recomienda completar variables faltantes antes de proceder")
        
        conn.close()
        
        print(f"\n✓ MAPEO DE VARIABLES COMPLETADO")
        print("=" * 80)
        
    except Exception as e:
        print(f"Error durante análisis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    mapear_variables_disponibles()