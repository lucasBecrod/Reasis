#!/usr/bin/env python3
"""
Normalizador de Valores - Datos Docentes
Estandariza valores con diferentes formatos para consistencia
"""

import pandas as pd
import sqlite3

def normalizar_genero():
    """Normalizar valores de género a formato estándar"""
    print("NORMALIZANDO GÉNERO")
    print("=" * 30)
    
    conn = sqlite3.connect('reasis_database.db')
    
    # Mostrar distribución actual
    dist_actual = pd.read_sql_query('''
        SELECT genero_personal, COUNT(*) as cantidad
        FROM docentes_data
        WHERE genero_personal IS NOT NULL
        GROUP BY genero_personal
        ORDER BY cantidad DESC
    ''', conn)
    
    print("Distribución actual:")
    print(dist_actual.to_string(index=False))
    
    # Normalizar a valores estándar
    cursor = conn.cursor()
    
    # Femenino -> Femenino
    cursor.execute('''
        UPDATE docentes_data 
        SET genero_personal = 'Femenino'
        WHERE UPPER(genero_personal) IN ('FEMENINO', 'F')
    ''')
    fem_actualizados = cursor.rowcount
    
    # Masculino -> Masculino  
    cursor.execute('''
        UPDATE docentes_data 
        SET genero_personal = 'Masculino'
        WHERE UPPER(genero_personal) IN ('MASCULINO', 'M')
    ''')
    masc_actualizados = cursor.rowcount
    
    conn.commit()
    
    print(f"Normalizaciones realizadas:")
    print(f"  Femenino: {fem_actualizados}")
    print(f"  Masculino: {masc_actualizados}")
    
    # Mostrar distribución final
    dist_final = pd.read_sql_query('''
        SELECT genero_personal, COUNT(*) as cantidad
        FROM docentes_data
        WHERE genero_personal IS NOT NULL
        GROUP BY genero_personal
        ORDER BY cantidad DESC
    ''', conn)
    
    print("\nDistribución normalizada:")
    print(dist_final.to_string(index=False))
    
    conn.close()
    return fem_actualizados + masc_actualizados

def normalizar_nivel_educativo():
    """Normalizar valores de nivel educativo"""
    print("\nNORMALIZANDO NIVEL EDUCATIVO")
    print("=" * 40)
    
    conn = sqlite3.connect('reasis_database.db')
    
    # Mostrar distribución actual
    dist_actual = pd.read_sql_query('''
        SELECT nivel_educativo, COUNT(*) as cantidad
        FROM docentes_data
        WHERE nivel_educativo IS NOT NULL
        GROUP BY nivel_educativo
        ORDER BY cantidad DESC
    ''', conn)
    
    print("Distribución actual:")
    print(dist_actual.to_string(index=False))
    
    cursor = conn.cursor()
    
    # Primaria -> Primaria
    cursor.execute('''
        UPDATE docentes_data 
        SET nivel_educativo = 'Primaria'
        WHERE UPPER(nivel_educativo) IN ('PRIMARIA', 'primaria')
    ''')
    prim_actualizados = cursor.rowcount
    
    # Secundaria -> Secundaria
    cursor.execute('''
        UPDATE docentes_data 
        SET nivel_educativo = 'Secundaria'  
        WHERE UPPER(nivel_educativo) IN ('SECUNDARIA')
    ''')
    sec_actualizados = cursor.rowcount
    
    # Inicial -> Inicial
    cursor.execute('''
        UPDATE docentes_data 
        SET nivel_educativo = 'Inicial'
        WHERE UPPER(nivel_educativo) IN ('INICIAL', 'inicial')
    ''')
    ini_actualizados = cursor.rowcount
    
    conn.commit()
    
    print(f"Normalizaciones realizadas:")
    print(f"  Primaria: {prim_actualizados}")
    print(f"  Secundaria: {sec_actualizados}")
    print(f"  Inicial: {ini_actualizados}")
    
    # Mostrar distribución final
    dist_final = pd.read_sql_query('''
        SELECT nivel_educativo, COUNT(*) as cantidad
        FROM docentes_data
        WHERE nivel_educativo IS NOT NULL
        GROUP BY nivel_educativo
        ORDER BY cantidad DESC
    ''', conn)
    
    print("\nDistribución normalizada:")
    print(dist_final.to_string(index=False))
    
    conn.close()
    return prim_actualizados + sec_actualizados + ini_actualizados

def main():
    """Función principal de normalización"""
    print("NORMALIZADOR DE VALORES DOCENTES")
    print("=" * 50)
    
    total_normalizados = 0
    total_normalizados += normalizar_genero()
    total_normalizados += normalizar_nivel_educativo()
    
    print(f"\nNORMALIZACIÓN COMPLETADA")
    print(f"Total valores normalizados: {total_normalizados}")
    
    return total_normalizados

if __name__ == "__main__":
    main()