import sqlite3
import pandas as pd

# Mapeo de valores TOE a códigos numéricos
MAPEO_TOE = {
    'UNIDOCENTE': 1,
    'BIDOCENTE': 2,
    'MULTIGRADO': 3,
    'POLIDOCENTE': 4
}

def calcular_x12_toe():
    """
    Calcula y puebla la variable X12_TOE en indices_metodologicos
    basado en los datos de la tabla datos_toe_servicios_2024
    """
    conn = sqlite3.connect('reasis_database.db')
    
    # 1. Obtener datos TOE y hacer el mapeo
    query = """
    SELECT 
        i.CODIGO_MODULAR,
        t.tipo_organizacion_normalizado
    FROM indices_metodologicos i
    LEFT JOIN datos_toe_servicios_2024 t ON i.CODIGO_MODULAR = t.codigo_modular
    """
    
    df = pd.read_sql_query(query, conn)
    
    # 2. Aplicar mapeo
    df['X12_TOE'] = df['tipo_organizacion_normalizado'].map(MAPEO_TOE)
    
    # 3. Actualizar la tabla indices_metodologicos
    updated = 0
    cur = conn.cursor()
    
    for index, row in df.iterrows():
        if pd.notna(row['X12_TOE']):
            cur.execute("""
                UPDATE indices_metodologicos 
                SET X12_TOE = ? 
                WHERE CODIGO_MODULAR = ?
            """, (int(row['X12_TOE']), row['CODIGO_MODULAR']))
            updated += 1
    
    conn.commit()
    
    # 4. Validación y reporte
    print("\n=== ACTUALIZACIÓN X12_TOE ===")
    print(f"Total registros procesados: {len(df)}")
    print(f"Registros actualizados: {updated}")
    
    # 5. Mostrar distribución final
    query_validation = """
    SELECT 
        X12_TOE,
        COUNT(*) as cantidad
    FROM indices_metodologicos
    WHERE X12_TOE IS NOT NULL
    GROUP BY X12_TOE
    ORDER BY X12_TOE
    """
    
    df_validation = pd.read_sql_query(query_validation, conn)
    print("\nDistribución final X12_TOE:")
    print("1=UNIDOCENTE, 2=BIDOCENTE, 3=MULTIGRADO, 4=POLIDOCENTE")
    print(df_validation.to_string(index=False))
    
    conn.close()

if __name__ == "__main__":
    calcular_x12_toe()
