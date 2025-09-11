import sqlite3
import pandas as pd

DB_PATH = 'reasis_database.db'

# Conexión a la base de datos
conn = sqlite3.connect(DB_PATH)
try:
    df = pd.read_sql_query('SELECT * FROM docentes_data LIMIT 5', conn)
    print("Columns of docentes_data:")
    print(df.columns.tolist())
    print("\nFirst 5 rows of docentes_data:")
    print(df.to_string())
except Exception as e:
    print(f"Error: {e}")
finally:
    conn.close()

