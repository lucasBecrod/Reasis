import sqlite3
import pandas as pd

DB_PATH = 'reasis_database.db'

# Conexión a la base de datos
conn = sqlite3.connect(DB_PATH)

# Leer los datos de los estudiantes
df_estudiantes = pd.read_sql_query('SELECT ie_tiene_aula_innovacion FROM competencia_digital_estudiantes', conn)

print("Valores únicos en la columna 'ie_tiene_aula_innovacion':")
print(df_estudiantes['ie_tiene_aula_innovacion'].unique())

conn.close()