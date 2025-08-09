#!/usr/bin/env python3
"""
Análisis detallado de redundancias en instituciones_educativas
Proyecto Reasis - Identificación específica de columnas a eliminar
"""

import sqlite3
import pandas as pd

def main():
    print("=== ANÁLISIS DETALLADO DE REDUNDANCIAS ===")
    
    conn = sqlite3.connect('reasis_database.db')
    
    # 1. Analizar redundancias específicas entre columnas de redes
    print("1. Analizando redundancias entre columnas de redes:")
    
    df_redes = pd.read_sql_query("""
        SELECT numero_fya, nombre_red_fya_matched, id_red_fya, codigo_red, codigo_rer
        FROM instituciones_educativas
        LIMIT 10
    """, conn)
    
    print("   Muestra de columnas relacionadas con redes:")
    print(df_redes.to_string())
    
    # Verificar si codigo_red y codigo_rer contienen la misma información
    df_comparacion = pd.read_sql_query("""
        SELECT 
            codigo_red, 
            codigo_rer,
            numero_fya,
            COUNT(*) as cantidad
        FROM instituciones_educativas
        WHERE codigo_red IS NOT NULL AND codigo_rer IS NOT NULL
        GROUP BY codigo_red, codigo_rer, numero_fya
        ORDER BY cantidad DESC
    """, conn)
    
    print(f"\n   Comparación codigo_red vs codigo_rer:")
    print(df_comparacion.to_string())
    
    # 2. Verificar si hay diferencias entre region y departamento
    print("\n2. Analizando region vs departamento:")
    
    df_geo = pd.read_sql_query("""
        SELECT DISTINCT region, departamento
        FROM instituciones_educativas
        ORDER BY region
        LIMIT 15
    """, conn)
    
    print("   Muestra region vs departamento:")
    print(df_geo.to_string())
    
    # Verificar si son iguales
    df_geo_diferencias = pd.read_sql_query("""
        SELECT COUNT(*) as total,
               COUNT(CASE WHEN region = departamento THEN 1 END) as iguales,
               COUNT(CASE WHEN region != departamento THEN 1 END) as diferentes
        FROM instituciones_educativas
    """, conn)
    
    print(f"   Estadísticas region vs departamento:")
    print(df_geo_diferencias.to_string())
    
    # 3. Analizar si total_docentes es igual a docentes_total
    print("\n3. Analizando total_docentes vs docentes_total:")
    
    df_docentes = pd.read_sql_query("""
        SELECT total_docentes, docentes_total, COUNT(*) as cantidad
        FROM instituciones_educativas
        GROUP BY total_docentes, docentes_total
        ORDER BY cantidad DESC
        LIMIT 10
    """, conn)
    
    print("   Comparación total_docentes vs docentes_total:")
    print(df_docentes.to_string())
    
    # 4. Verificar valores únicos en columnas sospechosas
    print("\n4. Verificando valores únicos en columnas con pocos valores:")
    
    columnas_verificar = ['cuadro_datos', 'tipo_institucion', 'fuente_datos', 'es_toe', 
                         'estado_validacion', 'es_fya', 'identificador', 'pagina_web']
    
    for columna in columnas_verificar:
        df_valores = pd.read_sql_query(f"""
            SELECT DISTINCT {columna}, COUNT(*) as cantidad
            FROM instituciones_educativas
            GROUP BY {columna}
            ORDER BY cantidad DESC
        """, conn)
        
        print(f"\n   Valores únicos en {columna}:")
        print(df_valores.to_string())
    
    # 5. Propuesta final de columnas a eliminar
    print("\n5. PROPUESTA FINAL DE LIMPIEZA:")
    
    # Columnas completamente vacías
    vacias = ['nombre_corto', 'codigo_rie', 'usuario_actualizacion']
    
    # Columnas con un solo valor (constantes inútiles)
    constantes = ['cuadro_datos', 'tipo_institucion', 'fuente_datos', 'es_toe', 
                 'estado_validacion', 'fecha_actualizacion', 'es_fya', 'identificador']
    
    # Columnas redundantes (mantenemos la mejor versión)
    redundantes = []
    
    # Verificar si region y departamento son iguales
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) FROM instituciones_educativas 
        WHERE region != departamento
    """)
    diferencias_geo = cursor.fetchone()[0]
    
    if diferencias_geo == 0:
        redundantes.append('departamento')  # Eliminar departamento, mantener region
        print("   - region y departamento son iguales → ELIMINAR departamento")
    else:
        print(f"   - region y departamento tienen {diferencias_geo} diferencias → MANTENER ambas")
    
    # Verificar si total_docentes y docentes_total son iguales
    cursor.execute("""
        SELECT COUNT(*) FROM instituciones_educativas 
        WHERE total_docentes != docentes_total
    """)
    diferencias_docentes = cursor.fetchone()[0]
    
    if diferencias_docentes == 0:
        redundantes.append('total_docentes')  # Eliminar total_docentes, mantener docentes_total
        print("   - total_docentes y docentes_total son iguales → ELIMINAR total_docentes")
    else:
        print(f"   - total_docentes y docentes_total tienen {diferencias_docentes} diferencias → MANTENER ambas")
    
    # Columnas con baja completitud y específicas del estudio
    baja_completitud = ['codigo_red', 'codigo_rer']  # Solo 30% completitud, redundante con numero_fya
    
    # Columnas de poco valor para el estudio
    poco_valor = ['pagina_web']  # Solo 3 valores únicos, no relevante para clustering
    
    # Resumen final
    eliminar_total = vacias + constantes + redundantes + baja_completitud + poco_valor
    eliminar_total = list(set(eliminar_total))  # Eliminar duplicados
    
    print(f"\n   COLUMNAS A ELIMINAR ({len(eliminar_total)} total):")
    print("   Vacías:", vacias)
    print("   Constantes:", constantes)
    print("   Redundantes:", redundantes)
    print("   Baja completitud:", baja_completitud)
    print("   Poco valor:", poco_valor)
    
    print(f"\n   Lista completa a eliminar:")
    for col in sorted(eliminar_total):
        print(f"     - {col}")
    
    print(f"\n   RESULTADO: De 61 columnas actuales → {61 - len(eliminar_total)} columnas finales")
    print(f"   Reducción: {len(eliminar_total)} columnas ({len(eliminar_total)/61*100:.1f}%)")
    
    conn.close()
    print("\n¡ANÁLISIS DE REDUNDANCIAS COMPLETADO!")

if __name__ == "__main__":
    main()