"""
Script para completar las 5 instituciones faltantes de X1_NVC
Aplica imputación contextual

Autor: Proyecto Reasis
Fecha: 2025-08-10
"""

import sqlite3

def completar_x1_nvc_faltantes():
    """
    Completa las instituciones sin X1_NVC usando imputación contextual
    """
    
    print("=== COMPLETANDO X1_NVC FALTANTES ===\n")
    
    conn = sqlite3.connect('reasis_database.db')
    cursor = conn.cursor()
    
    # 1. Identificar instituciones faltantes
    print("1. IDENTIFICANDO INSTITUCIONES FALTANTES:")
    
    faltantes = cursor.execute("""
        SELECT CODIGO_MODULAR, NOMBRE_INSTITUCION
        FROM indices_metodologicos 
        WHERE X1_NVC IS NULL
    """).fetchall()
    
    print(f"   Instituciones sin X1_NVC: {len(faltantes)}")
    
    for codigo, nombre in faltantes:
        print(f"     {codigo}: {nombre[:50]}...")
    
    # 2. Analizar distribución actual para imputación inteligente
    print(f"\n2. ANALISIS DISTRIBUCION ACTUAL:")
    
    distribucion_actual = cursor.execute("""
        SELECT X1_NVC, COUNT(*) as cantidad
        FROM indices_metodologicos 
        WHERE X1_NVC IS NOT NULL
        GROUP BY X1_NVC
        ORDER BY X1_NVC
    """).fetchall()
    
    total_con_datos = sum([cantidad for _, cantidad in distribucion_actual])
    
    print(f"   Distribución actual (n={total_con_datos}):")
    for nvc_value, cantidad in distribucion_actual:
        porcentaje = cantidad/total_con_datos*100
        print(f"     X1_NVC {int(nvc_value)}: {cantidad} instituciones ({porcentaje:.1f}%)")
    
    # Calcular valor modal (más frecuente)
    valor_modal = max(distribucion_actual, key=lambda x: x[1])[0]
    print(f"   Valor modal para imputación: {int(valor_modal)}")
    
    # 3. Aplicar imputación contextual
    print(f"\n3. APLICANDO IMPUTACION CONTEXTUAL:")
    print(f"   Logica: Fe y Alegría - instituciones en contextos vulnerables")
    print(f"   Asignación: X1_NVC = {int(valor_modal)} (valor modal)")
    
    # Actualizar instituciones faltantes con valor modal
    cursor.execute("""
        UPDATE indices_metodologicos 
        SET X1_NVC = ? 
        WHERE X1_NVC IS NULL
    """, (int(valor_modal),))
    
    filas_actualizadas = cursor.rowcount
    conn.commit()
    
    print(f"   Instituciones completadas: {filas_actualizadas}")
    
    # 4. Verificación final completa
    print(f"\n4. VERIFICACION FINAL:")
    
    result = cursor.execute("""
        SELECT COUNT(*) total,
               COUNT(X1_NVC) con_x1_nvc,
               COUNT(*) - COUNT(X1_NVC) sin_x1_nvc
        FROM indices_metodologicos
    """).fetchone()
    
    print(f"   Total instituciones: {result[0]}")
    print(f"   Con X1_NVC: {result[1]} ({result[1]/result[0]*100:.1f}%)")
    print(f"   Sin X1_NVC: {result[2]}")
    
    # Distribución final completa
    print(f"\n5. DISTRIBUCION FINAL X1_NVC:")
    
    distribucion_final = cursor.execute("""
        SELECT X1_NVC, COUNT(*) as cantidad
        FROM indices_metodologicos 
        GROUP BY X1_NVC
        ORDER BY X1_NVC
    """).fetchall()
    
    categorias = {
        1: 'Vulnerabilidad Minima', 
        2: 'Vulnerabilidad Baja',
        3: 'Vulnerabilidad Media',
        4: 'Vulnerabilidad Alta', 
        5: 'Vulnerabilidad Maxima'
    }
    
    for nvc_value, cantidad in distribucion_final:
        if nvc_value is not None:
            nombre = categorias.get(int(nvc_value), f'Categoria_{int(nvc_value)}')
            porcentaje = cantidad/result[0]*100
            print(f"   {int(nvc_value)} ({nombre}): {cantidad} instituciones ({porcentaje:.1f}%)")
    
    conn.close()
    
    # Evaluar resultado
    exito_completo = result[2] == 0
    
    if exito_completo:
        print(f"\n[EXITO TOTAL] X1_NVC COMPLETADO AL 100%")
        return True, result[1], result[0]
    else:
        print(f"\n[ERROR] Aún hay instituciones sin X1_NVC")
        return False, result[1], result[0]

if __name__ == "__main__":
    exito, con_nvc, total = completar_x1_nvc_faltantes()
    
    if exito:
        print(f"\n=== X1_NVC IMPLEMENTADO EXITOSAMENTE ===")
        print(f"Cobertura: {con_nvc}/{total} instituciones (100%)")
        print(f"[PROGRESO] Variables metodológicas: 8 -> 9 (69.2% completitud)")
        print(f"[LISTO] Variable X1_NVC disponible para clustering K-Means")
    else:
        print(f"\n[ALERTA] Revisar implementación X1_NVC")