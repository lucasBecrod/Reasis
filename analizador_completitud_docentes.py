#!/usr/bin/env python3
"""
Analizador de Completitud - Datos Docentes
Analiza columnas con valores NULL y evalúa viabilidad de completado automático
"""

import pandas as pd
import sqlite3

def analizar_completitud_general():
    """Análisis general de completitud por columna"""
    print("ANÁLISIS DE COMPLETITUD - TABLA DOCENTES")
    print("=" * 60)
    
    conn = sqlite3.connect('reasis_database.db')
    
    # Obtener estructura de tabla
    campos = pd.read_sql_query("PRAGMA table_info(docentes_data)", conn)
    
    # Análisis de completitud por campo
    completitud_data = []
    
    for _, campo in campos.iterrows():
        nombre_campo = campo['name']
        if nombre_campo == 'id':  # Saltar ID autoincremental
            continue
            
        stats = pd.read_sql_query(f'''
            SELECT 
                COUNT(*) as total,
                COUNT({nombre_campo}) as completos,
                COUNT(*) - COUNT({nombre_campo}) as nulos,
                ROUND((COUNT({nombre_campo}) * 100.0 / COUNT(*)), 1) as porcentaje_completo,
                ROUND(((COUNT(*) - COUNT({nombre_campo})) * 100.0 / COUNT(*)), 1) as porcentaje_nulo
            FROM docentes_data
        ''', conn).iloc[0]
        
        completitud_data.append({
            'campo': nombre_campo,
            'tipo': campo['type'],
            'total': int(stats['total']),
            'completos': int(stats['completos']),
            'nulos': int(stats['nulos']),
            'pct_completo': stats['porcentaje_completo'],
            'pct_nulo': stats['porcentaje_nulo']
        })
    
    df_completitud = pd.DataFrame(completitud_data)
    
    print("COMPLETITUD POR CAMPO:")
    print("-" * 60)
    print(df_completitud.to_string(index=False))
    
    # Identificar campos con oportunidades de mejora
    print(f"\nCAMPOS CON VALORES NULL (>0%):")
    print("-" * 40)
    campos_null = df_completitud[df_completitud['pct_nulo'] > 0].sort_values('nulos', ascending=False)
    
    for _, row in campos_null.iterrows():
        print(f"  {row['campo']:25} - {row['nulos']:3} NULL ({row['pct_nulo']:5.1f}%)")
    
    conn.close()
    return campos_null

def evaluar_completado_por_institucion(campo, descripcion):
    """Evaluar viabilidad de completado usando datos de la misma institución"""
    print(f"\nEVALUACIÓN COMPLETADO POR INSTITUCIÓN: {campo}")
    print(f"{'=' * (45 + len(campo))}")
    print(f"Descripción: {descripcion}")
    
    conn = sqlite3.connect('reasis_database.db')
    
    # Análisis por institución
    analisis = pd.read_sql_query(f'''
        SELECT 
            codigo_modular_actual,
            institucion_actual,
            COUNT(*) as total_docentes,
            COUNT({campo}) as con_valor,
            COUNT(*) - COUNT({campo}) as sin_valor,
            ROUND((COUNT({campo}) * 100.0 / COUNT(*)), 1) as pct_completo
        FROM docentes_data
        WHERE codigo_modular_actual IS NOT NULL
        GROUP BY codigo_modular_actual, institucion_actual
        HAVING COUNT(*) > 1  -- Solo instituciones con múltiples docentes
        ORDER BY sin_valor DESC, total_docentes DESC
    ''', conn)
    
    print(f"\nInstituciones con múltiples docentes (oportunidades de completado):")
    print(f"Total instituciones analizadas: {len(analisis)}")
    
    # Instituciones con oportunidades de completado
    oportunidades = analisis[(analisis['sin_valor'] > 0) & (analisis['con_valor'] > 0)]
    
    if len(oportunidades) > 0:
        print(f"\nInstituciones con oportunidades de completado: {len(oportunidades)}")
        print("Top 10 por registros afectados:")
        print(oportunidades[['codigo_modular_actual', 'institucion_actual', 'total_docentes', 'con_valor', 'sin_valor']].head(10).to_string(index=False))
        
        # Calcular impacto potencial
        registros_completables = oportunidades['sin_valor'].sum()
        total_nulos = analisis['sin_valor'].sum()
        
        print(f"\nIMPACTO POTENCIAL:")
        print(f"  Registros NULL completables: {registros_completables}")
        print(f"  Total registros NULL: {total_nulos}")
        print(f"  Porcentaje completable: {(registros_completables/total_nulos*100):.1f}%")
        
    else:
        print("No hay oportunidades de completado por institución para este campo")
    
    conn.close()
    return oportunidades if len(oportunidades) > 0 else None

def evaluar_completado_por_rer(campo, descripcion):
    """Evaluar viabilidad de completado usando datos de la misma RER"""
    print(f"\nEVALUACIÓN COMPLETADO POR RER: {campo}")
    print(f"{'=' * (35 + len(campo))}")
    
    conn = sqlite3.connect('reasis_database.db')
    
    analisis_rer = pd.read_sql_query(f'''
        SELECT 
            rer,
            COUNT(*) as total_docentes,
            COUNT({campo}) as con_valor,
            COUNT(*) - COUNT({campo}) as sin_valor,
            ROUND((COUNT({campo}) * 100.0 / COUNT(*)), 1) as pct_completo
        FROM docentes_data
        WHERE rer IS NOT NULL
        GROUP BY rer
        HAVING COUNT(*) > 1
        ORDER BY sin_valor DESC, total_docentes DESC
    ''', conn)
    
    oportunidades_rer = analisis_rer[(analisis_rer['sin_valor'] > 0) & (analisis_rer['con_valor'] > 0)]
    
    if len(oportunidades_rer) > 0:
        print(f"RER con oportunidades de completado: {len(oportunidades_rer)}")
        print(oportunidades_rer.head(10).to_string(index=False))
        
        registros_completables_rer = oportunidades_rer['sin_valor'].sum()
        print(f"\nRegistros completables por RER: {registros_completables_rer}")
    else:
        print("No hay oportunidades de completado por RER")
    
    conn.close()
    return oportunidades_rer if len(oportunidades_rer) > 0 else None

def evaluar_completado_por_año(campo, descripcion):
    """Evaluar completado usando datos del mismo docente en diferentes años"""
    print(f"\nEVALUACIÓN COMPLETADO POR DNI (MISMO DOCENTE): {campo}")
    print(f"{'=' * (50 + len(campo))}")
    
    conn = sqlite3.connect('reasis_database.db')
    
    # Docentes que aparecen en múltiples años
    docentes_multianuales = pd.read_sql_query(f'''
        SELECT 
            dni,
            COUNT(*) as años_registrado,
            COUNT({campo}) as años_con_valor,
            COUNT(*) - COUNT({campo}) as años_sin_valor
        FROM docentes_data
        GROUP BY dni
        HAVING COUNT(*) > 1
        ORDER BY años_sin_valor DESC
    ''', conn)
    
    oportunidades_dni = docentes_multianuales[(docentes_multianuales['años_sin_valor'] > 0) & (docentes_multianuales['años_con_valor'] > 0)]
    
    if len(oportunidades_dni) > 0:
        print(f"Docentes con oportunidades de completado: {len(oportunidades_dni)}")
        print(oportunidades_dni.head(10).to_string(index=False))
        
        registros_completables_dni = oportunidades_dni['años_sin_valor'].sum()
        print(f"\nRegistros completables por DNI: {registros_completables_dni}")
    else:
        print("No hay oportunidades de completado por DNI")
    
    conn.close()
    return oportunidades_dni if len(oportunidades_dni) > 0 else None

def generar_recomendaciones(campo, descripcion, oport_inst, oport_rer, oport_dni):
    """Generar recomendaciones de completado"""
    print(f"\nRECOMENDACIONES PARA {campo}:")
    print("-" * 50)
    
    if oport_inst is not None:
        registros_inst = oport_inst['sin_valor'].sum()
        print(f"- INSTITUCION: {registros_inst} registros completables")
        print(f"  Estrategia: Usar valor de otros docentes de la misma institucion")
    
    if oport_rer is not None:
        registros_rer = oport_rer['sin_valor'].sum()
        print(f"- RER: {registros_rer} registros completables")
        print(f"  Estrategia: Usar valor modal de la misma RER")
    
    if oport_dni is not None:
        registros_dni = oport_dni['años_sin_valor'].sum()
        print(f"- MISMO DOCENTE: {registros_dni} registros completables")
        print(f"  Estrategia: Usar valor del mismo docente en otro año")
    
    total_potencial = 0
    if oport_inst is not None:
        total_potencial += oport_inst['sin_valor'].sum()
    if oport_rer is not None:
        total_potencial += oport_rer['sin_valor'].sum()
    if oport_dni is not None:
        total_potencial += oport_dni['años_sin_valor'].sum()
    
    if total_potencial > 0:
        print(f"\nPOTENCIAL TOTAL COMBINADO: {total_potencial} registros")
        print(f"PRIORIDAD DE IMPLEMENTACIÓN: {'ALTA' if total_potencial > 50 else 'MEDIA' if total_potencial > 20 else 'BAJA'}")
    else:
        print(f"No se identificaron oportunidades de completado automático")

def main():
    """Función principal de análisis"""
    print("ANALIZADOR DE COMPLETITUD Y OPORTUNIDADES DE COMPLETADO")
    print("=" * 70)
    
    # Paso 1: Análisis general
    campos_null = analizar_completitud_general()
    
    # Paso 2: Evaluar campos con mayor potencial
    campos_evaluar = [
        ('genero_personal', 'Género/sexo del docente'),
        ('nivel_educativo', 'Nivel donde enseña (Primaria/Secundaria)'),
        ('institucion_continua', 'Institución donde continúa'),
        ('codigo_modular_continua', 'Código de institución destino'),
        ('codigo_modular_vinculado', 'Vinculación con tabla instituciones'),
        ('metodo_vinculacion', 'Método usado para vinculación')
    ]
    
    print(f"\n\n{'='*70}")
    print("EVALUACIÓN DETALLADA DE OPORTUNIDADES DE COMPLETADO")
    print("="*70)
    
    for campo, descripcion in campos_evaluar:
        # Solo evaluar si el campo tiene NULLs
        campo_stats = campos_null[campos_null['campo'] == campo]
        if len(campo_stats) > 0 and campo_stats.iloc[0]['nulos'] > 0:
            print(f"\n{'='*70}")
            
            # Evaluar múltiples estrategias
            oport_inst = evaluar_completado_por_institucion(campo, descripcion)
            oport_rer = evaluar_completado_por_rer(campo, descripcion) 
            oport_dni = evaluar_completado_por_año(campo, descripcion)
            
            # Generar recomendaciones
            generar_recomendaciones(campo, descripcion, oport_inst, oport_rer, oport_dni)
    
    print(f"\n{'='*70}")
    print("ANÁLISIS COMPLETADO")
    print("Use las recomendaciones anteriores para priorizar completado automático")
    print("="*70)

if __name__ == "__main__":
    main()