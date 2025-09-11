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
instituciones_no_encontradas = []
for idx, inst in df_inst.iterrows():
    key = (inst.get('distrito', ''), inst.get('provincia', ''), inst.get('departamento', ''))
    valor = pobreza_map.get(key, np.nan)
    pobreza_asignada.append(valor)
    if pd.isna(valor):
        instituciones_no_encontradas.append(inst)


# Métricas de éxito
total_instituciones = len(df_inst)
instituciones_vinculadas = total_instituciones - len(instituciones_no_encontradas)
tasa_exito = (instituciones_vinculadas / total_instituciones) * 100

print("Análisis del método de vinculación:")
print("===================================")
print("El método utilizado es una vinculación por coincidencia exacta (exact match).")
print("Se construye una clave única a partir de la combinación de los campos 'distrito', 'provincia' y 'departamento'.")
print("No se utilizó ninguna técnica de coincidencia difusa (fuzzy matching).")
print()

print("Métricas de la vinculación:")
print("--------------------------")
print(f"Total de instituciones educativas: {total_instituciones}")
print(f"Instituciones vinculadas con exito: {instituciones_vinculadas}")
print(f"Tasa de exito: {tasa_exito:.2f}%")
print()

if instituciones_no_encontradas:
    print("Instituciones que no pudieron ser vinculadas:")
    df_no_encontradas = pd.DataFrame(instituciones_no_encontradas)
    print(df_no_encontradas[['codigo_modular', 'nombre_institucion', 'distrito', 'provincia', 'departamento']].head())


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
print('\nVinculación de grupos de pobreza monetaria por distrito completada.')