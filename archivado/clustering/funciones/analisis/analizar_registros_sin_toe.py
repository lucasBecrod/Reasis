import sqlite3
import pandas as pd

def analizar_registros_sin_toe():
    """
    Analiza los registros que no tienen X12_TOE para determinar
    si necesitan imputación y qué método usar.
    """
    conn = sqlite3.connect('reasis_database.db')
    
    # 1. Identificar registros sin TOE
    query = """
    SELECT 
        i.CODIGO_MODULAR,
        i.NOMBRE_INSTITUCION,
        ie.es_rural,
        ie.total_docentes,
        ie.total_alumnos,
        ie.nivel_educativo,
        i.X11_RED,
        t.tipo_organizacion_normalizado as toe_actual,
        r.red_fya
    FROM indices_metodologicos i
    LEFT JOIN instituciones_educativas ie ON i.CODIGO_MODULAR = ie.codigo_modular
    LEFT JOIN datos_toe_servicios_2024 t ON i.CODIGO_MODULAR = t.codigo_modular
    LEFT JOIN (
        SELECT DISTINCT codigo_modular, red_fya 
        FROM datos_toe_servicios_2024
    ) r ON i.CODIGO_MODULAR = r.codigo_modular
    WHERE i.X12_TOE IS NULL
    """
    
    df = pd.read_sql_query(query, conn)
    
    # 2. Analizar características de los registros sin TOE
    print("\n=== ANÁLISIS DE REGISTROS SIN X12_TOE ===")
    print(f"Total registros sin TOE: {len(df)}\n")
    
    # 2.1 Por red FyA
    print("Distribución por red FyA:")
    print(df['red_fya'].value_counts(dropna=False))
    print()
    
    # 2.2 Por nivel educativo
    print("\nDistribución por nivel educativo:")
    print(df['nivel_educativo'].value_counts(dropna=False))
    print()
    
    # 2.3 Por ruralidad
    print("\nDistribución por ruralidad:")
    print(df['es_rural'].value_counts(dropna=False))
    print()
    
    # 3. Analizar posible método de imputación
    print("\nAnálisis para imputación:")
    
    # 3.1 Obtener distribución de TOE por red para casos similares
    query_ref = """
    SELECT 
        d.red_fya,
        d.tipo_organizacion_normalizado,
        COUNT(*) as cantidad
    FROM datos_toe_servicios_2024 d
    WHERE d.tipo_organizacion_normalizado IS NOT NULL
    GROUP BY d.red_fya, d.tipo_organizacion_normalizado
    ORDER BY d.red_fya, cantidad DESC
    """
    
    df_ref = pd.read_sql_query(query_ref, conn)
    print("\nDistribución de TOE por red (referencia):")
    for red in df_ref['red_fya'].unique():
        print(f"\nRed {red}:")
        print(df_ref[df_ref['red_fya'] == red].to_string(index=False))
    
    # 4. Mostrar detalles de cada registro sin TOE
    print("\nDetalles de registros sin TOE:")
    print(df[['CODIGO_MODULAR', 'NOMBRE_INSTITUCION', 'red_fya', 'nivel_educativo', 'total_docentes', 'X11_RED']].to_string(index=False))
    
    conn.close()

if __name__ == "__main__":
    analizar_registros_sin_toe()
