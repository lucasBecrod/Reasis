import sqlite3
import pandas as pd
import re
import json

DB_PATH = 'reasis_database.db'

# --- Step 1: Read docentes_competencias_contexto and process ---
conn = sqlite3.connect(DB_PATH)
df_docentes_contexto = pd.read_sql_query('SELECT * FROM docentes_competencias_contexto', conn)
conn.close()

# Extract network number from 'nombre_de_la_iiee'
def extract_network_number(name):
    name = str(name).upper()
    match = re.search(r'FE Y ALEGRÍA (\d+)', name)
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
    docentes_mencionan_internet_red=pd.NamedAgg(column='cuenta_con_conectividad_de_internet_en_casa', aggfunc=lambda x: (x == 'Sí').sum())
).reset_index()

# Convert aggregated data to a dictionary for easy lookup
network_data_map = aggregated_data.set_index('red_number').to_dict('index')

# --- Step 2: Read instituciones_educativas and update ---
conn = sqlite3.connect(DB_PATH)
df_instituciones = pd.read_sql_query('SELECT rowid, numero_fya FROM instituciones_educativas', conn)

# Add new columns to instituciones_educativas if they don't exist
new_columns = ['competencia_digital_docente_promedio_red', 'docentes_mencionan_internet_red']
for col in new_columns:
    try:
        conn.execute(f'ALTER TABLE instituciones_educativas ADD COLUMN {col} REAL')
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            pass # Column already exists
        else:
            raise e

# Update the new columns in instituciones_educativas
for index, row in df_instituciones.iterrows():
    red_id = row['numero_fya']
    if red_id in network_data_map:
        avg_comp = network_data_map[red_id]['competencia_digital_docente_promedio_red']
        internet_count = network_data_map[red_id]['docentes_mencionan_internet_red']
        conn.execute(f'''
            UPDATE instituciones_educativas
            SET
                competencia_digital_docente_promedio_red = ?,
                docentes_mencionan_internet_red = ?
            WHERE rowid = ?
        ''', (avg_comp, internet_count, row['rowid']))
    else:
        # If no matching network data, set to NULL or default
        conn.execute(f'''
            UPDATE instituciones_educativas
            SET
                competencia_digital_docente_promedio_red = NULL,
                docentes_mencionan_internet_red = NULL
            WHERE rowid = ?
        ''', (row['rowid'],))

conn.commit()
conn.close()

print("¡Tarea completada! La tabla 'instituciones_educativas' ha sido actualizada con los datos de competencia digital docente y menciones de internet por red, utilizando numero_fya para la vinculación.")
