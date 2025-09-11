import sqlite3
import pandas as pd
import re

DB_PATH = 'reasis_database.db'

# Conexión a la base de datos
conn = sqlite3.connect(DB_PATH)
df_docentes_contexto = pd.read_sql_query('SELECT * FROM docentes_competencias_contexto', conn)
conn.close()

# Convert 'puntuacion' to numeric, coercing errors to NaN
df_docentes_contexto['puntuacion'] = pd.to_numeric(df_docentes_contexto['puntuacion'], errors='coerce')

# Aggregate by codigo_red
aggregated_data = df_docentes_contexto.groupby('codigo_red').agg(
    competencia_digital_docente_promedio_red=pd.NamedAgg(column='puntuacion', aggfunc='mean'),
    competencia_profesional_empoderado_promedio_red=pd.NamedAgg(column='profesional_empoderado_num', aggfunc='mean'),
    competencia_catalizador_aprendizaje_promedio_red=pd.NamedAgg(column='catalizador_aprendizaje_num', aggfunc='mean'),
    docentes_mencionan_internet_red=pd.NamedAgg(column='cuenta_con_conectividad_de_internet_en_casa', aggfunc=lambda x: (x == 'Sí').sum())
).reset_index()

print("Datos agregados por red:")
print(aggregated_data.to_string())
