import sqlite3
import pandas as pd

DB_PATH = 'reasis_database.db'

# Conexión a la base de datos
conn = sqlite3.connect(DB_PATH)

# Leer los datos de los estudiantes
df_estudiantes = pd.read_sql_query('SELECT codigo_modular_vinculado, ie_tiene_aula_innovacion FROM competencia_digital_estudiantes', conn)

# Filtrar datos nulos y respuestas positivas
df_estudiantes.dropna(subset=['codigo_modular_vinculado'], inplace=True)
df_con_aula = df_estudiantes[df_estudiantes['ie_tiene_aula_innovacion'] == 'Sí']

# Contar respuestas por escuela
conteo_por_escuela = df_con_aula.groupby('codigo_modular_vinculado').size().reset_index(name='conteo_si')

# Filtrar escuelas que cumplen la condición (al menos 1 respuesta afirmativa)
escuelas_con_aula_confirmada = conteo_por_escuela[conteo_por_escuela['conteo_si'] >= 1]

# Obtener la lista de códigos modulares
codigos_modulares_con_aula = escuelas_con_aula_confirmada['codigo_modular_vinculado'].tolist()

print(f"Se identificaron {len(codigos_modulares_con_aula)} instituciones que cumplen con el criterio (al menos 1 estudiante confirma tener aula de innovación).")

# Añadir y actualizar la columna
try:
    conn.execute('ALTER TABLE instituciones_educativas ADD COLUMN tiene_aula_innovacion BOOLEAN DEFAULT FALSE')
except:
    pass # La columna ya existe

conn.execute('UPDATE instituciones_educativas SET tiene_aula_innovacion = FALSE')
conn.commit()

if codigos_modulares_con_aula:
    placeholders = ', '.join('?' for _ in codigos_modulares_con_aula)
    query = f'UPDATE instituciones_educativas SET tiene_aula_innovacion = TRUE WHERE codigo_modular IN ({placeholders})'
    conn.execute(query, codigos_modulares_con_aula)
    conn.commit()

conn.close()

print("La tabla 'instituciones_educativas' ha sido actualizada con la nueva lógica.")