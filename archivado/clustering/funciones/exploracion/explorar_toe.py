import sqlite3
import pandas as pd

def explorar_toe():
    conn = sqlite3.connect('reasis_database.db')
    
    # Consultar datos TOE
    print("\n=== ANÁLISIS DE DATOS TOE ===")
    
    # 1. Conteo de registros
    query_count = """
    SELECT 
        COUNT(*) as total,
        SUM(CASE WHEN tipo_organizacion_normalizado IS NOT NULL AND tipo_organizacion_normalizado != '' THEN 1 ELSE 0 END) as con_toe,
        SUM(CASE WHEN tipo_organizacion_normalizado IS NULL OR tipo_organizacion_normalizado = '' THEN 1 ELSE 0 END) as sin_toe
    FROM datos_toe_servicios_2024
    """
    counts = pd.read_sql_query(query_count, conn)
    print("\nCompletitud de datos:")
    print(f"Total registros: {counts['total'][0]}")
    print(f"Con TOE: {counts['con_toe'][0]}")
    print(f"Sin TOE: {counts['sin_toe'][0]}")
    
    # 2. Valores únicos
    query_unique = """
    SELECT DISTINCT tipo_organizacion_normalizado, COUNT(*) as cantidad
    FROM datos_toe_servicios_2024
    WHERE tipo_organizacion_normalizado IS NOT NULL 
    AND tipo_organizacion_normalizado != ''
    GROUP BY tipo_organizacion_normalizado
    ORDER BY cantidad DESC
    """
    unique_values = pd.read_sql_query(query_unique, conn)
    print("\nValores únicos de TOE:")
    print(unique_values.to_string())
    
    conn.close()

if __name__ == "__main__":
    explorar_toe()
