"""
Script para completar las 5 instituciones faltantes de X15_MEIB
Aplica imputación contextual

Autor: Proyecto Reasis
Fecha: 2025-08-10
"""

import sqlite3

def completar_x15_meib_faltantes():
    """
    Completa las instituciones sin X15_MEIB usando imputación contextual
    """
    
    print("=== COMPLETANDO X15_MEIB FALTANTES ===\n")
    
    conn = sqlite3.connect('reasis_database.db')
    cursor = conn.cursor()
    
    # 1. Identificar instituciones faltantes
    print("1. IDENTIFICANDO INSTITUCIONES FALTANTES:")
    
    faltantes = cursor.execute("""
        SELECT CODIGO_MODULAR, NOMBRE_INSTITUCION
        FROM indices_metodologicos 
        WHERE X15_MEIB IS NULL
    """).fetchall()
    
    print(f"   Instituciones sin X15_MEIB: {len(faltantes)}")
    
    for codigo, nombre in faltantes:
        print(f"     {codigo}: {nombre[:50]}...")
    
    # 2. Aplicar imputación contextual
    print(f"\n2. APLICANDO IMPUTACION CONTEXTUAL:")
    print(f"   Lógica: Fe y Alegría mayoritariamente No-EIB")
    print(f"   Asignación: X15_MEIB = 0 (No EIB)")
    
    # Actualizar instituciones faltantes a No-EIB
    cursor.execute("""
        UPDATE indices_metodologicos 
        SET X15_MEIB = 0 
        WHERE X15_MEIB IS NULL
    """)
    
    filas_actualizadas = cursor.rowcount
    conn.commit()
    
    print(f"   Instituciones completadas: {filas_actualizadas}")
    
    # 3. Verificación final completa
    print(f"\n3. VERIFICACION FINAL:")
    
    result = cursor.execute("""
        SELECT COUNT(*) total,
               COUNT(X15_MEIB) con_x15_meib,
               COUNT(*) - COUNT(X15_MEIB) sin_x15_meib
        FROM indices_metodologicos
    """).fetchone()
    
    print(f"   Total instituciones: {result[0]}")
    print(f"   Con X15_MEIB: {result[1]} ({result[1]/result[0]*100:.1f}%)")
    print(f"   Sin X15_MEIB: {result[2]}")
    
    # Distribución final completa
    print(f"\n4. DISTRIBUCION FINAL X15_MEIB:")
    
    distribucion_final = cursor.execute("""
        SELECT X15_MEIB, COUNT(*) as cantidad
        FROM indices_metodologicos 
        GROUP BY X15_MEIB
        ORDER BY X15_MEIB
    """).fetchall()
    
    categorias = {0: 'No EIB', 1: 'EIB Fortalecimiento', 2: 'EIB Revitalización'}
    
    for meib_value, cantidad in distribucion_final:
        if meib_value is not None:
            nombre = categorias.get(meib_value, f'Categoria_{meib_value}')
            porcentaje = cantidad/result[0]*100
            print(f"   {meib_value} ({nombre}): {cantidad} instituciones ({porcentaje:.1f}%)")
    
    conn.close()
    
    # Evaluar resultado
    exito_completo = result[2] == 0
    
    if exito_completo:
        print(f"\n[EXITO TOTAL] X15_MEIB COMPLETADO AL 100%")
        return True, result[1], result[0]
    else:
        print(f"\n[ERROR] Aún hay instituciones sin X15_MEIB")
        return False, result[1], result[0]

if __name__ == "__main__":
    exito, con_meib, total = completar_x15_meib_faltantes()
    
    if exito:
        print(f"\n=== X15_MEIB IMPLEMENTADO EXITOSAMENTE ===")
        print(f"Cobertura: {con_meib}/{total} instituciones (100%)")
        print(f"[PROGRESO] Variables metodológicas: 7 -> 8 (61.5% completitud)")
        print(f"[LISTO] Variable X15_MEIB disponible para clustering K-Means")
    else:
        print(f"\n[ALERTA] Revisar implementación X15_MEIB")