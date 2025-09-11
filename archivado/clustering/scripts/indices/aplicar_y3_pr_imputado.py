import sqlite3
import pandas as pd
import os

# Configuración
DB_PATH = 'reasis_database.db'
TABLE = 'indices_metodologicos'
CSV_PATH = os.path.join(os.getcwd(), 'temp_data', 'y3_pr_imputacion_20250810.csv')

# Cargar imputaciones
imputaciones = pd.read_csv(CSV_PATH)

# Conexión a la base de datos
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Actualizar Y3_PR en la tabla oficial
actualizados = 0
for _, row in imputaciones.iterrows():
    cursor.execute(f"UPDATE {TABLE} SET Y3_PR = ? WHERE CODIGO_MODULAR = ?", (row['Y3_PR_IMPUTADO'], row['CODIGO_MODULAR']))
    actualizados += cursor.rowcount
conn.commit()
conn.close()

print(f"Actualización completada: {actualizados} registros modificados en Y3_PR.")
