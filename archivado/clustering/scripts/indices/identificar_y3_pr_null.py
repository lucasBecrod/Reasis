import sqlite3
import pandas as pd

# Configuración
DB_PATH = 'reasis_database.db'
TABLE = 'indices_metodologicos'

# Conexión y carga de datos
conn = sqlite3.connect(DB_PATH)
df = pd.read_sql_query(f'SELECT CODIGO_MODULAR, NOMBRE_INSTITUCION, Y3_PR FROM {TABLE}', conn)
conn.close()

# Identificar instituciones con Y3_PR nulo
faltantes = df[df['Y3_PR'].isnull()]
print(f"Total instituciones con Y3_PR NULL: {len(faltantes)}")
print(faltantes[['CODIGO_MODULAR', 'NOMBRE_INSTITUCION']])

# Guardar listado en CSV para referencia
faltantes.to_csv('temp_data/y3_pr_faltantes_20250810.csv', index=False)
print("Listado guardado en temp_data/y3_pr_faltantes_20250810.csv")
