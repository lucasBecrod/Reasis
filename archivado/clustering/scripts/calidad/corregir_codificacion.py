#!/usr/bin/env python3
"""
Script para corregir problemas menores de codificación identificados
"""

import sqlite3

def corregir_codificacion():
    """
    Corrige problemas específicos de codificación
    """
    
    print("=== CORRECCION PROBLEMAS DE CODIFICACION ===\n")
    
    conn = sqlite3.connect('reasis_database.db')
    cursor = conn.cursor()
    
    # 1. Corregir X14_NIVEL_EDUCATIVO para 'Inicial - Jardin' (sin tilde)
    print("1. CORRIGIENDO X14_NIVEL_EDUCATIVO:")
    
    # Buscar el caso específico
    cursor.execute("""
    SELECT CODIGO_MODULAR, NOMBRE_INSTITUCION 
    FROM indices_metodologicos 
    WHERE X14_NIVEL_EDUCATIVO IS NULL
    """)
    casos_null = cursor.fetchall()
    
    print(f"   Casos NULL encontrados: {len(casos_null)}")
    for codigo, nombre in casos_null:
        print(f"   - {codigo}: {nombre}")
        
        # Obtener el valor original de nivel_educativo
        cursor.execute("""
        SELECT nivel_educativo 
        FROM instituciones_educativas 
        WHERE codigo_modular = ?
        """, (codigo,))
        nivel_original = cursor.fetchone()
        
        if nivel_original:
            nivel_valor = nivel_original[0]
            print(f"     Valor original: '{nivel_valor}'")
            
            # Aplicar codificación manual para casos no reconocidos
            if nivel_valor == 'Inicial - Jardin':  # Sin tilde
                nuevo_valor = 2  # Inicial - Jardín
                cursor.execute("""
                UPDATE indices_metodologicos 
                SET X14_NIVEL_EDUCATIVO = ?
                WHERE CODIGO_MODULAR = ?
                """, (nuevo_valor, codigo))
                print(f"     [CORREGIDO] Asignado valor {nuevo_valor}")
    
    # 2. Corregir X17_GESTION para casos con caracteres especiales
    print(f"\n2. CORRIGIENDO X17_GESTION:")
    
    cursor.execute("""
    SELECT CODIGO_MODULAR, NOMBRE_INSTITUCION 
    FROM indices_metodologicos 
    WHERE X17_GESTION IS NULL
    """)
    casos_gestion_null = cursor.fetchall()
    
    print(f"   Casos NULL encontrados: {len(casos_gestion_null)}")
    
    correcciones_gestion = 0
    for codigo, nombre in casos_gestion_null:
        # Obtener valor original
        cursor.execute("""
        SELECT gestion 
        FROM instituciones_educativas 
        WHERE codigo_modular = ?
        """, (codigo,))
        gestion_original = cursor.fetchone()
        
        if gestion_original:
            gestion_valor = gestion_original[0]
            
            # Codificación manual para variantes
            if 'Pública de gestión directa' in str(gestion_valor) or 'Publica de gestion directa' in str(gestion_valor):
                nuevo_valor = 1
                cursor.execute("""
                UPDATE indices_metodologicos 
                SET X17_GESTION = ?
                WHERE CODIGO_MODULAR = ?
                """, (nuevo_valor, codigo))
                correcciones_gestion += 1
                print(f"   [CORREGIDO] {codigo}: '{gestion_valor}' -> {nuevo_valor}")
    
    print(f"   Total correcciones aplicadas: {correcciones_gestion}")
    
    # 3. Verificar resultados finales
    print(f"\n3. VERIFICACION POST-CORRECCION:")
    
    variables_verificar = ['X14_NIVEL_EDUCATIVO', 'X17_GESTION']
    
    for variable in variables_verificar:
        cursor.execute(f"""
        SELECT 
            COUNT(*) as total,
            COUNT({variable}) as con_datos,
            COUNT(*) - COUNT({variable}) as nulls
        FROM indices_metodologicos
        """)
        stats = cursor.fetchone()
        completitud = (stats[1] / stats[0]) * 100 if stats[0] > 0 else 0
        
        print(f"   {variable}:")
        print(f"     Total: {stats[0]}, Con datos: {stats[1]}, NULLs: {stats[2]}")
        print(f"     Completitud: {completitud:.1f}%")
        
        if stats[2] > 0:
            print(f"     [ATENCION] Aún hay {stats[2]} valores NULL")
        else:
            print(f"     [OK] 100% completitud lograda")
    
    # Commit cambios
    conn.commit()
    conn.close()
    
    print(f"\n[EXITO] Correcciones de codificación aplicadas")
    return True

if __name__ == "__main__":
    resultado = corregir_codificacion()
    
    if resultado:
        print(f"\n=== CORRECCION COMPLETADA ===")
        print(f"Problemas de codificación solucionados")
        print(f"Variables contextuales listas para clustering")
    else:
        print(f"\n=== CORRECCION CON PROBLEMAS ===")
        print(f"Revisar errores reportados")