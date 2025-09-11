import sqlite3
import pandas as pd

# Conexión a la base de datos
conn = sqlite3.connect('reasis_database.db')

# Inspeccionar columnas de instituciones_educativas
cursor = conn.cursor()
cursor.execute('PRAGMA table_info(instituciones_educativas)')
columnas = [row[1] for row in cursor.fetchall()]
print(f"Columnas en instituciones_educativas: {columnas}")

# Extraer una muestra de 10 filas para revisar posibles campos útiles
query = 'SELECT * FROM instituciones_educativas LIMIT 10'
df_muestra = pd.read_sql_query(query, conn)
print("\nMuestra de datos:")
print(df_muestra)

conn.close()
