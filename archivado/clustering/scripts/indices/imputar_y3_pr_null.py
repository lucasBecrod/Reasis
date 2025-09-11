import sqlite3
import pandas as pd

# Configuración
DB_PATH = 'reasis_database.db'
TABLE = 'indices_metodologicos'

# Conexión y carga de datos
conn = sqlite3.connect(DB_PATH)
df = pd.read_sql_query(f'SELECT CODIGO_MODULAR, Y3_PR FROM {TABLE}', conn)

# Calcular mediana global de Y3_PR (excluyendo nulos y ceros)
mediana_global = df.loc[(df['Y3_PR'].notnull()) & (df['Y3_PR'] != 0), 'Y3_PR'].median()
print(f"Mediana global Y3_PR a imputar: {mediana_global}")

# Identificar instituciones con Y3_PR nulo
faltantes = df[df['Y3_PR'].isnull()]['CODIGO_MODULAR'].astype(str).str.zfill(7).tolist()
print(f"Instituciones a imputar: {faltantes}")

# Imputar mediana global en la base de datos
cursor = conn.cursor()
for codigo in faltantes:
    cursor.execute(f"UPDATE {TABLE} SET Y3_PR = ? WHERE CODIGO_MODULAR = ?", (mediana_global, codigo))
conn.commit()
conn.close()
print(f"Imputación completada para {len(faltantes)} instituciones.")
