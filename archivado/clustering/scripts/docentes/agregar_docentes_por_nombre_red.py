import sqlite3
import pandas as pd
import re

DB_PATH = 'reasis_database.db'

# Conexión a la base de datos
conn = sqlite3.connect(DB_PATH)
df_docentes_contexto = pd.read_sql_query('SELECT * FROM docentes_competencias_contexto', conn)
conn.close()

# Convert 'puntuaci_n' to numeric, coercing errors to NaN
df_docentes_contexto['puntuaci_n'] = pd.to_numeric(df_docentes_contexto['puntuaci_n'], errors='coerce')

# Aggregate by nombre_de_la_iiee
aggregated_data = df_docentes_contexto.groupby('nombre_de_la_iiee').agg(
    competencia_digital_docente_promedio_red=pd.NamedAgg(column='puntuaci_n', aggfunc='mean'),
    docentes_mencionan_internet_red=pd.NamedAgg(column='cuenta_con_conectividad_de_internet_en_casa', aggfunc=lambda x: (x == 'Sí').sum())
).reset_index()

print("Datos agregados por nombre de red:")
print(aggregated_data.to_string())
