import pandas as pd
import sqlite3
import numpy as np

# Rutas
EXCEL_PATH = r'C:\Users\lucas\Proyectos\Reasis\data\bases_de_datos\pobreza_monetaria\Pobreza monetaria por distrito.xlsx'
DB_PATH = 'reasis_database.db'

# Leer Anexo1
df_pobreza = pd.read_excel(EXCEL_PATH, sheet_name='Anexo1', header=3)

# Normalizar nombres de columnas
original_cols = df_pobreza.columns
df_pobreza.columns = [c.lower().replace('\n', ' ').replace(' ', '_').replace('.', '').replace('á','a').replace('é','e').replace('í','i').replace('ó','o').replace('ú','u').replace('1/','').replace('2/','').replace('3/','').replace('_/_','_') for c in df_pobreza.columns]
pobreza_cols_map = dict(zip(df_pobreza.columns, original_cols))


# Conexión a la base de datos
conn = sqlite3.connect(DB_PATH)
df_inst = pd.read_sql_query('SELECT rowid, * FROM instituciones_educativas', conn)

# Normalizar campos de ubicación
for campo in ['distrito', 'provincia', 'departamento']:
    if campo in df_inst.columns:
        df_inst[campo] = df_inst[campo].astype(str).str.strip().str.upper().str.normalize('NFKD').str.encode('ascii', 'ignore').str.decode('utf-8')
    if campo in df_pobreza.columns:
        df_pobreza[campo] = df_pobreza[campo].astype(str).str.strip().str.upper().str.normalize('NFKD').str.encode('ascii', 'ignore').str.decode('utf-8')


# Columnas a añadir
columnas_a_extraer = {
    'ubigeo': 'ubigeo_distrito',
    'poblacion_proyectada_2020_': 'poblacion_proyectada_2020_distrito',
    'intervalo_de_confianza_al_95%_(inferior)': 'confianza_inferior_pobreza_distrito',
    'intervalo_de_confianza_al_95%_(superior)': 'confianza_superior_pobreza_distrito'
}

# Crear mapas para cada columna
mapas = {}
for col_origen, _ in columnas_a_extraer.items():
    mapas[col_origen] = {}

for _, row in df_pobreza.iterrows():
    key = (row.get('distrito', ''), row.get('provincia', ''), row.get('departamento', ''))
    for col_origen, _ in columnas_a_extraer.items():
        mapas[col_origen][key] = row.get(col_origen, np.nan)


# Añadir y actualizar columnas
for col_origen, col_destino in columnas_a_extraer.items():
    print(f"Procesando y añadiendo columna: {col_destino}")
    
    # Añadir la nueva columna (si no existe)
    try:
        # Determinar el tipo de dato
        tipo_dato = 'TEXT' if 'ubigeo' in col_origen else 'REAL'
        conn.execute(f'ALTER TABLE instituciones_educativas ADD COLUMN {col_destino} {tipo_dato}')
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            pass # La columna ya existe
        else:
            raise e

    # Asignar valores
    valores_asignados = []
    for idx, inst in df_inst.iterrows():
        key = (inst.get('distrito', ''), inst.get('provincia', ''), inst.get('departamento', ''))
        valor = mapas[col_origen].get(key, np.nan)
        valores_asignados.append(valor)

    # Actualizar en la base de datos
    for i, valor in zip(df_inst['rowid'], valores_asignados):
        # Asegurarse de que los valores NaN de pandas se conviertan a NULL de SQL
        if pd.isna(valor):
            valor_sql = None
        else:
            valor_sql = valor
        conn.execute(f'UPDATE instituciones_educativas SET {col_destino} = ? WHERE rowid = ?', (valor_sql, i))

conn.commit()
conn.close()

print("\n¡Proceso completado! Se han añadido las siguientes columnas a la tabla 'instituciones_educativas':")
for col in columnas_a_extraer.values():
    print(f"- {col}")