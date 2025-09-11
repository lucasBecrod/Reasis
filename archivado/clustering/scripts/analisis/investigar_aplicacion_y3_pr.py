import sqlite3
import pandas as pd
import os

# Configuración
DB_PATH = 'reasis_database.db'
TABLE = 'indices_metodologicos'
CSV_PATH = os.path.join(os.getcwd(), 'temp_data', 'y3_pr_imputacion_20250810.csv')

# Cargar imputaciones y datos actuales
imputaciones = pd.read_csv(CSV_PATH)
conn = sqlite3.connect(DB_PATH)
df_db = pd.read_sql_query(f'SELECT CODIGO_MODULAR, Y3_PR FROM {TABLE}', conn)
conn.close()

# Normalizar códigos modulares a string y zfill(7)
imputaciones['CODIGO_MODULAR'] = imputaciones['CODIGO_MODULAR'].astype(str).str.zfill(7)
df_db['CODIGO_MODULAR'] = df_db['CODIGO_MODULAR'].astype(str).str.zfill(7)

# Buscar coincidencias y diferencias
no_en_db = imputaciones[~imputaciones['CODIGO_MODULAR'].isin(df_db['CODIGO_MODULAR'])]
no_en_csv = df_db[~df_db['CODIGO_MODULAR'].isin(imputaciones['CODIGO_MODULAR'])]
coinciden = imputaciones[imputaciones['CODIGO_MODULAR'].isin(df_db['CODIGO_MODULAR'])]

# Comparar valores actuales vs imputados
comparacion = pd.merge(coinciden, df_db, on='CODIGO_MODULAR', how='left')
comparacion['diferente'] = comparacion['Y3_PR_IMPUTADO'] != comparacion['Y3_PR']
modificables = comparacion[comparacion['diferente']]

# Reporte
print(f"Total en CSV: {len(imputaciones)}")
print(f"Total en BD: {len(df_db)}")
print(f"Coincidencias: {len(coinciden)}")
print(f"No están en BD: {len(no_en_db)}")
print(f"No están en CSV: {len(no_en_csv)}")
print(f"Registros con valor diferente (modificables): {len(modificables)}")
print("Ejemplo de registros no modificados:")
print(comparacion.head())
print("Ejemplo de registros modificables:")
print(modificables.head())
