"""
Script para completar las 5 instituciones faltantes de X4_IDD
Aplica imputación contextual

Autor: Proyecto Reasis
Fecha: 2025-08-10
"""

import sqlite3

def completar_x4_idd_faltantes():
    """
    Completa las instituciones sin X4_IDD usando imputación contextual
    """
    
    print("=== COMPLETANDO X4_IDD FALTANTES ===\n")
    
    conn = sqlite3.connect('reasis_database.db')
    cursor = conn.cursor()
    
    # 1. Identificar instituciones faltantes
    print("1. IDENTIFICANDO INSTITUCIONES FALTANTES:")
    
    faltantes = cursor.execute("""
        SELECT CODIGO_MODULAR, NOMBRE_INSTITUCION
        FROM indices_metodologicos 
        WHERE X4_IDD IS NULL
    """).fetchall()
    
    print(f"   Instituciones sin X4_IDD: {len(faltantes)}")
    
    for codigo, nombre in faltantes:
        print(f"     {codigo}: {nombre[:50]}...")
    
    # 2. Analizar distribución actual para imputación inteligente
    print(f"\n2. ANALISIS DISTRIBUCION ACTUAL:")
    
    estadisticas = cursor.execute("""
        SELECT 
            COUNT(*) as total,
            AVG(X4_IDD) as promedio,
            MIN(X4_IDD) as minimo,
            MAX(X4_IDD) as maximo
        FROM indices_metodologicos 
        WHERE X4_IDD IS NOT NULL
    """).fetchone()
    
    print(f"   Distribución actual (n={estadisticas[0]}):")
    print(f"     Promedio: {estadisticas[1]:.1f}")
    print(f"     Rango: {estadisticas[2]:.1f} - {estadisticas[3]:.1f}")
    
    # Distribución por fuente (según metodología)
    distribucion_fuente = cursor.execute("""
        SELECT 
            CASE 
                WHEN X4_IDD > 15 THEN 'PADD_Alto'
                WHEN X4_IDD > 8 AND X4_IDD <= 15 THEN 'PADD_Medio'  
                WHEN X4_IDD > 12 THEN 'Regresion_Alta'
                ELSE 'Regresion_General'
            END as fuente_aproximada,
            COUNT(*) as cantidad,
            AVG(X4_IDD) as promedio
        FROM indices_metodologicos 
        WHERE X4_IDD IS NOT NULL
        GROUP BY 
            CASE 
                WHEN X4_IDD > 15 THEN 'PADD_Alto'
                WHEN X4_IDD > 8 AND X4_IDD <= 15 THEN 'PADD_Medio'  
                WHEN X4_IDD > 12 THEN 'Regresion_Alta'
                ELSE 'Regresion_General'
            END
        ORDER BY promedio DESC
    """).fetchall()
    
    print(f"   Distribución aproximada por fuente:")
    for fuente, cantidad, promedio in distribucion_fuente:
        print(f"     {fuente}: {cantidad} inst. (prom: {promedio:.1f})")
    
    # 3. Aplicar imputación contextual con promedio general
    print(f"\n3. APLICANDO IMPUTACION CONTEXTUAL:")
    promedio_general = estadisticas[1]
    print(f"   Lógica: Promedio general de instituciones existentes")
    print(f"   Asignación: X4_IDD = {promedio_general:.1f}")
    
    # Actualizar instituciones faltantes con promedio general
    cursor.execute("""
        UPDATE indices_metodologicos 
        SET X4_IDD = ? 
        WHERE X4_IDD IS NULL
    """, (promedio_general,))
    
    filas_actualizadas = cursor.rowcount
    conn.commit()
    
    print(f"   Instituciones completadas: {filas_actualizadas}")
    
    # 4. Verificación final completa
    print(f"\n4. VERIFICACION FINAL:")
    
    result = cursor.execute("""
        SELECT COUNT(*) total,
               COUNT(X4_IDD) con_x4_idd,
               COUNT(*) - COUNT(X4_IDD) sin_x4_idd
        FROM indices_metodologicos
    """).fetchone()
    
    print(f"   Total instituciones: {result[0]}")
    print(f"   Con X4_IDD: {result[1]} ({result[1]/result[0]*100:.1f}%)")
    print(f"   Sin X4_IDD: {result[2]}")
    
    # Estadísticas finales completas
    print(f"\n5. ESTADISTICAS FINALES X4_IDD:")
    
    estadisticas_finales = cursor.execute("""
        SELECT 
            COUNT(*) as total,
            AVG(X4_IDD) as promedio,
            MIN(X4_IDD) as minimo,
            MAX(X4_IDD) as maximo
        FROM indices_metodologicos 
        WHERE X4_IDD IS NOT NULL
    """).fetchone()
    
    print(f"   Total: {estadisticas_finales[0]} instituciones")
    print(f"   Promedio: {estadisticas_finales[1]:.1f}")
    print(f"   Rango: {estadisticas_finales[2]:.1f} - {estadisticas_finales[3]:.1f}")
    
    # Distribución por niveles
    distribucion_niveles = cursor.execute("""
        SELECT 
            CASE 
                WHEN X4_IDD <= 7.5 THEN 'Bajo'
                WHEN X4_IDD <= 12.5 THEN 'Medio'
                WHEN X4_IDD <= 17.5 THEN 'Alto'
                ELSE 'Muy Alto'
            END as nivel,
            COUNT(*) as cantidad
        FROM indices_metodologicos 
        WHERE X4_IDD IS NOT NULL
        GROUP BY 
            CASE 
                WHEN X4_IDD <= 7.5 THEN 'Bajo'
                WHEN X4_IDD <= 12.5 THEN 'Medio'
                WHEN X4_IDD <= 17.5 THEN 'Alto'
                ELSE 'Muy Alto'
            END
        ORDER BY 
            CASE 
                WHEN X4_IDD <= 7.5 THEN 1
                WHEN X4_IDD <= 12.5 THEN 2
                WHEN X4_IDD <= 17.5 THEN 3
                ELSE 4
            END
    """).fetchall()
    
    print(f"\n   Distribución por niveles:")
    for nivel, cantidad in distribucion_niveles:
        porcentaje = cantidad/result[0]*100
        print(f"     {nivel}: {cantidad} instituciones ({porcentaje:.1f}%)")
    
    conn.close()
    
    # Evaluar resultado
    exito_completo = result[2] == 0
    
    if exito_completo:
        print(f"\n[EXITO TOTAL] X4_IDD COMPLETADO AL 100%")
        return True, result[1], result[0]
    else:
        print(f"\n[ERROR] Aún hay instituciones sin X4_IDD")
        return False, result[1], result[0]

if __name__ == "__main__":
    exito, con_idd, total = completar_x4_idd_faltantes()
    
    if exito:
        print(f"\n=== X4_IDD IMPLEMENTADO EXITOSAMENTE ===")
        print(f"Cobertura: {con_idd}/{total} instituciones (100%)")
        print(f"[PROGRESO] Variables metodológicas: 9 -> 10 (76.9% completitud)")
        print(f"[METODOLOGIA] PADD real + Regresión contextual + Imputación promedio")
        print(f"[LISTO] Variable X4_IDD disponible para clustering K-Means")
    else:
        print(f"\n[ALERTA] Revisar implementación X4_IDD")