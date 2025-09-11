
import pandas as pd
import sqlite3
import numpy as np

# Rutas
EXCEL_PATH = r'C:\Users\lucas\Proyectos\Reasis\data\bases_de_datos\pobreza_monetaria\Pobreza monetaria por distrito.xlsx'
DB_PATH = 'reasis_database.db'

# Leer Anexo1 (asumiendo que contiene Ubigeo, distrito, provincia, region y pobreza)
df_pobreza = pd.read_excel(EXCEL_PATH, sheet_name='Anexo1', header=3)

# Normalizar nombres de columnas
df_pobreza.columns = [c.lower().replace('\n', ' ').replace(' ', '_').replace('.', '').replace('á','a').replace('é','e').replace('í','i').replace('ó','o').replace('ú','u').replace('2/','').replace('3/','').replace('_/_','_') for c in df_pobreza.columns]


# Conexión a la base de datos
conn = sqlite3.connect(DB_PATH)
df_inst = pd.read_sql_query('SELECT rowid, * FROM instituciones_educativas', conn)

# Normalizar campos de ubicación
for campo in ['distrito', 'provincia', 'departamento']:
    if campo in df_inst.columns:
        df_inst[campo] = df_inst[campo].astype(str).str.strip().str.upper().str.normalize('NFKD').str.encode('ascii', 'ignore').str.decode('utf-8')
    if campo in df_pobreza.columns:
        df_pobreza[campo] = df_pobreza[campo].astype(str).str.strip().str.upper().str.normalize('NFKD').str.encode('ascii', 'ignore').str.decode('utf-8')

# Vinculación directa por distrito, provincia y departamento
pobreza_map = {}
for _, row in df_pobreza.iterrows():
    key = (row.get('distrito', ''), row.get('provincia', ''), row.get('departamento', ''))
    pobreza_map[key] = row.get('grupos_robustos_', np.nan)

# Asignar pobreza monetaria a cada institución
pobreza_asignada = []
for idx, inst in df_inst.iterrows():
    key = (inst.get('distrito', ''), inst.get('provincia', ''), inst.get('departamento', ''))
    valor = pobreza_map.get(key, np.nan)
    pobreza_asignada.append(valor)

# Añadir la nueva columna a la base de datos
try:
    conn.execute('ALTER TABLE instituciones_educativas ADD COLUMN grupo_pobreza_monetaria_distrito REAL')
except:
    pass

# Actualizar la columna en la base de datos
for i, valor in zip(df_inst['rowid'], pobreza_asignada):
    conn.execute('UPDATE instituciones_educativas SET grupo_pobreza_monetaria_distrito = ? WHERE rowid = ?', (valor, i))
conn.commit()
conn.close()
print('Vinculación de grupos de pobreza monetaria por distrito completada.')
