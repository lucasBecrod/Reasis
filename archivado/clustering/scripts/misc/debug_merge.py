import sqlite3
import pandas as pd
import re

DB_PATH = 'reasis_database.db'

# Conexión a la base de datos
conn = sqlite3.connect(DB_PATH)

# Read instituciones_educativas table
df_instituciones = pd.read_sql_query('SELECT id_red_fya FROM instituciones_educativas', conn)

# Read aggregated data (from previous step)
df_docentes_contexto = pd.read_sql_query('SELECT nombre_de_la_iiee FROM docentes_competencias_contexto', conn)

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

conn.close()

print("Unique values of id_red_fya in instituciones_educativas:")
print(df_instituciones['id_red_fya'].unique())

print("\nUnique values of red_number in aggregated_data:")
print(df_docentes_contexto['red_number'].unique())
