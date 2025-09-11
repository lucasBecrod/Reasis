def buscar_mediana(row, df, estratos):
    # Estrato completo
    filtro = (df['Y3_PR'].notnull()) & (df['Y3_PR'] != 0)
    for n in range(len(estratos), 0, -1):
        condiciones = [df[e] == row[e] for e in estratos[:n]]
        filtro_estrato = filtro & np.logical_and.reduce(condiciones)
        valores = df.loc[filtro_estrato, 'Y3_PR']
        if len(valores) >= 2:
            return valores.median(), f"{'-'.join([str(row[e]) for e in estratos[:n]])}"
    # Mediana global
    valores = df.loc[filtro, 'Y3_PR']
    if len(valores) >= 2:
        return valores.median(), 'global'
    return None, 'sin_datos'

import sqlite3
import pandas as pd
import numpy as np
import os

# Configuración
DB_PATH = 'reasis_database.db'
TABLE = 'indices_metodologicos'

# Conexión y carga de datos
conn = sqlite3.connect(DB_PATH)
df = pd.read_sql_query(f'SELECT * FROM {TABLE}', conn)
conn.close()

# Definir los estratos disponibles en la tabla
estratos = ['NUMERO_FYA', 'X2_TR']

 # Identificar registros a imputar (NULL o 0)
mask_null = df['Y3_PR'].isnull() | (df['Y3_PR'] == 0)
df_imputar = df[mask_null].copy()

# Asegurar que todos los códigos modulares faltantes estén en el CSV
faltantes = df[mask_null]['CODIGO_MODULAR'].astype(str).str.zfill(7).tolist()
print(f"Total instituciones a imputar: {len(faltantes)}")

# Función para buscar mediana por estrato
def buscar_mediana(row, df, estratos):
    filtro = (df['Y3_PR'].notnull()) & (df['Y3_PR'] != 0)
    for n in range(len(estratos), 0, -1):
        condiciones = [df[e] == row[e] for e in estratos[:n]]
        filtro_estrato = filtro & np.logical_and.reduce(condiciones)
        valores = df.loc[filtro_estrato, 'Y3_PR']
        if len(valores) >= 2:
            return valores.median(), f"{'-'.join([str(row[e]) for e in estratos[:n]])}"
    valores = df.loc[filtro, 'Y3_PR']
    if len(valores) >= 2:
        return valores.median(), 'global'
    return None, 'sin_datos'

# Imputación y registro en CSV
imputaciones = []
# Calcular mediana global para casos sin imputación
mediana_global = df.loc[(df['Y3_PR'].notnull()) & (df['Y3_PR'] != 0), 'Y3_PR'].median()
for idx, row in df_imputar.iterrows():
    valor, metodo = buscar_mediana(row, df, estratos)
    if valor is None:
        valor = mediana_global
        metodo = 'global_forzada'
    imputaciones.append({
        'CODIGO_MODULAR': row['CODIGO_MODULAR'],
        'Y3_PR_IMPUTADO': valor,
        'METODO_IMPUTACION': metodo
    })

# Guardar resultados en CSV
output_path = os.path.join(os.getcwd(), 'temp_data', 'y3_pr_imputacion_20250810.csv')
os.makedirs(os.path.dirname(output_path), exist_ok=True)
df_out = pd.DataFrame(imputaciones)
df_out.to_csv(output_path, index=False)
print(f'Archivo de imputación generado: {output_path}')
