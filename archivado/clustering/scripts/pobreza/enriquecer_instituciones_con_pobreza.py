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
pobreza_cols_map = dict(zip(original_cols, df_pobreza.columns))


# Conexión a la base de datos
conn = sqlite3.connect(DB_PATH)
df_inst = pd.read_sql_query('SELECT rowid, * FROM instituciones_educativas', conn)

# Normalizar campos de ubicación
for campo in ['distrito', 'provincia', 'departamento']:
    if campo in df_inst.columns:
        df_inst[campo] = df_inst[campo].astype(str).str.strip().str.upper().str.normalize('NFKD').str.encode('ascii', 'ignore').str.decode('utf-8')
    if campo in df_pobreza.columns:
        df_pobreza[campo] = df_pobreza[campo].astype(str).str.strip().str.upper().str.normalize('NFKD').str.encode('ascii', 'ignore').str.decode('utf-8')


# Columnas a extraer
columnas_a_extraer = {
    'ubigeo': 'ubigeo_distrito',
    'poblacion_proyectada_2020_': 'poblacion_proyectada_2020_distrito',
    'intervalo_de_confianza_al_95%_(inferior)': 'intervalo_confianza_inferior_pobreza_distrito',
    'intervalo_de_confianza_al_95%_(superior)': 'intervalo_confianza_superior_pobreza_distrito',
    'ubicacion_pobreza_monetaria_total_': 'ubicacion_pobreza_monetaria_total_distrito'
}

# Crear mapas para cada columna
mapas = {}
for col_orig, _ in columnas_a_extraer.items():
    mapa = {}
    for _, row in df_pobreza.iterrows():
        key = (row.get('distrito', ''), row.get('provincia', ''), row.get('departamento', ''))
        mapa[key] = row.get(col_orig, np.nan)
    mapas[col_orig] = mapa


# Añadir y actualizar columnas
for col_orig, col_db in columnas_a_extraer.items():
    # Añadir la nueva columna a la base de datos
    try:
        # Determinar el tipo de dato
        tipo_dato = 'TEXT' if col_orig == 'ubigeo' else 'REAL'
        conn.execute(f'ALTER TABLE instituciones_educativas ADD COLUMN {col_db} {tipo_dato}')
    except Exception as e:
        print(f"No se pudo añadir la columna {col_db}: {e}")
        pass

    # Asignar valores
    valores_asignados = []
    for idx, inst in df_inst.iterrows():
        key = (inst.get('distrito', ''), inst.get('provincia', ''), inst.get('departamento', ''))
        valor = mapas[col_orig].get(key, np.nan)
        valores_asignados.append(valor)

    # Actualizar la columna en la base de datos
    for i, valor in zip(df_inst['rowid'], valores_asignados):
        conn.execute(f'UPDATE instituciones_educativas SET {col_db} = ? WHERE rowid = ?', (valor, i))

conn.commit()
conn.close()

print("Se han añadido las siguientes columnas a la tabla 'instituciones_educativas':")
for col_db in columnas_a_extraer.values():
    print(f"- {col_db}")

print("\nProceso de enriquecimiento completado.")
