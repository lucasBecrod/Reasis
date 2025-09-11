import sqlite3
import pandas as pd

DB_PATH = 'reasis_database.db'

# Conexión a la base de datos
conn = sqlite3.connect(DB_PATH)
df = pd.read_sql_query('SELECT * FROM competencia_digital_docentes', conn)
conn.close()

# Palabras clave
keywords = ['internet', 'conectividad', 'wifi', 'datos']

# Función para buscar palabras clave
def buscar_keywords(row):
    texto_a_buscar = f"{row['profesional_empoderado_texto']} {row['catalizador_aprendizaje_texto']} {row['nota_global_relativa_texto']}".lower()
    for keyword in keywords:
        if keyword in texto_a_buscar:
            return True
    return False

# Aplicar la función
df['menciona_internet'] = df.apply(buscar_keywords, axis=1)

# Agrupar y contar
resultado = df.groupby(['codigo_red', 'nombre_rer'])['menciona_internet'].value_counts().unstack(fill_value=0)

print("Análisis de menciones de internet por red:")
print(resultado)
