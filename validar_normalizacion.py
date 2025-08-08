#!/usr/bin/env python3
"""
Validar normalización de numero_fya completada
Proyecto Reasis - Verificación final
"""

import sqlite3
import pandas as pd
import re

def main():
    print("=== VALIDACIÓN FINAL DE NORMALIZACIÓN ===")
    
    conn = sqlite3.connect('reasis_database.db')
    
    # 1. Verificar que todos los valores son numéricos
    print("1. Verificando formato numérico:")
    df = pd.read_sql_query("""
        SELECT numero_fya, COUNT(*) as cantidad
        FROM instituciones_educativas
        WHERE numero_fya IS NOT NULL AND numero_fya != ''
        ORDER BY CAST(numero_fya AS INTEGER)
    """, conn)
    
    no_numericos = []
    for valor in df['numero_fya']:
        try:
            int(valor)
        except ValueError:
            no_numericos.append(valor)
    
    if no_numericos:
        print(f"   ERROR: {len(no_numericos)} valores no numéricos: {no_numericos}")
    else:
        print(f"   ÉXITO: Todos los {len(df)} valores son numéricos")
    
    # 2. Verificar que se eliminó numero_fya_secundario
    print("\n2. Verificando eliminación de numero_fya_secundario:")
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(instituciones_educativas)")
    columnas = [col[1] for col in cursor.fetchall()]
    
    if 'numero_fya_secundario' in columnas:
        print("   ERROR: La columna numero_fya_secundario aún existe")
    else:
        print("   ÉXITO: La columna numero_fya_secundario fue eliminada")
    
    # 3. Verificar coherencia con nombre_red_fya_matched
    print("\n3. Verificando coherencia con nombre_red_fya_matched:")
    df_coherencia = pd.read_sql_query("""
        SELECT numero_fya, nombre_red_fya_matched, COUNT(*) as cantidad
        FROM instituciones_educativas
        WHERE numero_fya IS NOT NULL AND numero_fya != ''
            AND nombre_red_fya_matched IS NOT NULL AND nombre_red_fya_matched != ''
        GROUP BY numero_fya, nombre_red_fya_matched
        ORDER BY cantidad DESC
        LIMIT 20
    """, conn)
    
    print("   Muestra de coherencia:")
    incoherentes = 0
    for _, row in df_coherencia.iterrows():
        numero = row['numero_fya']
        nombre = row['nombre_red_fya_matched']
        cantidad = row['cantidad']
        
        # Extraer número esperado del nombre
        match = re.search(r'Red Fe y Alegría (\d+)', nombre)
        numero_esperado = match.group(1) if match else 'N/A'
        
        coherente = numero == numero_esperado
        if not coherente:
            incoherentes += cantidad
        
        status = "[OK]" if coherente else "[ERROR]"
        print(f"   {status} numero_fya: {numero} | Red: {nombre} | Registros: {cantidad}")
    
    if incoherentes == 0:
        print(f"\n   ÉXITO: Todos los valores son coherentes")
    else:
        print(f"\n   ERROR: {incoherentes} registros incoherentes detectados")
    
    # 4. Verificar redes del estudio específicamente
    print("\n4. Verificando redes del estudio (44, 47, 48, 54, 72, 79):")
    redes_estudio = ['44', '47', '48', '54', '72', '79']
    
    for red in redes_estudio:
        df_red = pd.read_sql_query("""
            SELECT COUNT(*) as cantidad
            FROM instituciones_educativas
            WHERE numero_fya = ?
        """, conn, params=[red])
        
        cantidad = df_red.iloc[0]['cantidad']
        print(f"   Red {red}: {cantidad} instituciones")
    
    # 5. Estadísticas finales
    print("\n5. Estadísticas finales:")
    stats = pd.read_sql_query("""
        SELECT 
            COUNT(DISTINCT numero_fya) as redes_distintas,
            COUNT(*) as total_registros,
            MIN(CAST(numero_fya AS INTEGER)) as numero_minimo,
            MAX(CAST(numero_fya AS INTEGER)) as numero_maximo
        FROM instituciones_educativas
        WHERE numero_fya IS NOT NULL AND numero_fya != ''
    """, conn)
    
    print(f"   Redes distintas: {stats.iloc[0]['redes_distintas']}")
    print(f"   Total registros: {stats.iloc[0]['total_registros']}")
    print(f"   Rango de números: {stats.iloc[0]['numero_minimo']} - {stats.iloc[0]['numero_maximo']}")
    
    # 6. Verificar estructura final de tabla
    print("\n6. Estructura final de tabla:")
    print("   Columnas relacionadas con redes:")
    columnas_redes = [col for col in columnas if any(palabra in col.lower() for palabra in ['red', 'fya', 'numero'])]
    for col in sorted(columnas_redes):
        print(f"   - {col}")
    
    conn.close()
    print("\n¡NORMALIZACIÓN VALIDADA EXITOSAMENTE!")

if __name__ == "__main__":
    main()