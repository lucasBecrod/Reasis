import sqlite3
import pandas as pd
import re

DB_PATH = 'reasis_database.db'

# Conexión a la base de datos
conn = sqlite3.connect(DB_PATH)
df_docentes_contexto = pd.read_sql_query('SELECT * FROM docentes_competencias_contexto', conn)
conn.close()

# Extract network number from 'nombre_de_la_iiee'
def extract_network_number(name):
    match = re.search(r'Fe y Alegría (\d+)', name)
    if match:
        return int(match.group(1))
    match = re.search(r'RER FA (\d+)', name)
    if match:
        return int(match.group(1))
    return None

df_docentes_contexto['red_number'] = df_docentes_contexto['nombre_de_la_iiee'].apply(extract_network_number)

# Convert 'puntuaci_n' to numeric, coercing errors to NaN
df_docentes_contexto['puntuaci_n'] = pd.to_numeric(df_docentes_contexto['puntuaci_n'], errors='coerce')

# Aggregate by red_number
aggregated_data = df_docentes_contexto.groupby('red_number').agg(
    competencia_digital_docente_promedio_red=pd.NamedAgg(column='puntuaci_n', aggfunc='mean'),
    competencia_profesional_empoderado_promedio_red=pd.NamedAgg(column='profesional_empoderado_num', aggfunc='mean'),
    competencia_catalizador_aprendizaje_promedio_red=pd.NamedAgg(column='catalizador_aprendizaje_num', aggfunc='mean'),
    docentes_mencionan_internet_red=pd.NamedAgg(column='cuenta_con_conectividad_de_internet_en_casa', aggfunc=lambda x: (x == 'Sí').sum())
).reset_index()

print("Datos agregados por red (número):")
print(aggregated_data.to_string())