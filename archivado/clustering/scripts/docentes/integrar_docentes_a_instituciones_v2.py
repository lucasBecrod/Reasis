import sqlite3
import pandas as pd
import re

DB_PATH = 'reasis_database.db'

# Conexión a la base de datos
conn = sqlite3.connect(DB_PATH)

# Read aggregated data (from previous step)
df_docentes_contexto = pd.read_sql_query('SELECT * FROM docentes_competencias_contexto', conn)

# Normalize network names in docentes_competencias_contexto
def normalize_network_name_docentes(name):
    name = str(name).upper() # Ensure name is string and convert to upper
    match = re.search(r'FE Y ALEGRÍA (\d+)', name)
    if match:
        return f'FE Y ALEGRIA {int(match.group(1))}'
    match = re.search(r'RER FA (\d+)', name)
    if match:
        return f'FE Y ALEGRIA {int(match.group(1))}'
    return name # Return original if no match

df_docentes_contexto['normalized_network_name'] = df_docentes_contexto['nombre_de_la_iiee'].apply(normalize_network_name_docentes)

# Convert 'puntuaci_n' to numeric, coercing errors to NaN
df_docentes_contexto['puntuaci_n'] = pd.to_numeric(df_docentes_contexto['puntuaci_n'], errors='coerce')

# Aggregate by normalized_network_name
aggregated_data = df_docentes_contexto.groupby('normalized_network_name').agg(
    competencia_digital_docente_promedio_red=pd.NamedAgg(column='puntuaci_n', aggfunc='mean'),
    docentes_mencionan_internet_red=pd.NamedAgg(column='cuenta_con_conectividad_de_internet_en_casa', aggfunc=lambda x: (x == 'Sí').sum())
).reset_index()


# Read instituciones_educativas table
df_instituciones = pd.read_sql_query('SELECT rowid, * FROM instituciones_educativas', conn)

# Normalize network names in instituciones_educativas
def normalize_network_name_instituciones(name):
    name = str(name).upper() # Ensure name is string and convert to upper
    match = re.search(r'FE Y ALEGRÍA (\d+)', name)
    if match:
        return f'FE Y ALEGRIA {int(match.group(1))}'
    match = re.search(r'RER FE Y ALEGRÍA (\d+)', name)
    if match:
        return f'FE Y ALEGRIA {int(match.group(1))}'
    return name # Return original if no match

df_instituciones['normalized_network_name'] = df_instituciones['nombre_red_fya_matched'].apply(normalize_network_name_instituciones)


# Merge dataframes
df_merged = pd.merge(df_instituciones, aggregated_data, left_on='normalized_network_name', right_on='normalized_network_name', how='left')

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
for index, row in df_merged.iterrows():
    conn.execute(f'''
        UPDATE instituciones_educativas
        SET
            competencia_digital_docente_promedio_red = ?,
            docentes_mencionan_internet_red = ?
        WHERE rowid = ?
    ''', (row['competencia_digital_docente_promedio_red'], row['docentes_mencionan_internet_red'], row['rowid']))

conn.commit()
conn.close()

print("La tabla 'instituciones_educativas' ha sido actualizada con los datos de competencia digital docente y menciones de internet por red.")
