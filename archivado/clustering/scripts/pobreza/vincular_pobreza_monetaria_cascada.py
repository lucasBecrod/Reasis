import pandas as pd
import sqlite3
import numpy as np

# Rutas
EXCEL_PATH = r'C:\Users\lucas\Proyectos\Reasis\data\bases_de_datos\pobreza_monetaria\Pobreza monetaria por distrito.xlsx'
DB_PATH = 'reasis_database.db'

# Leer Anexo1 correctamente (datos desde fila 8, encabezados manuales)
columnas = ['ubigeo', 'departamento', 'provincia', 'distrito', 'poblacion_2020', 'confianza_inferior', 'confianza_superior', 'grupos_robustos', 'pobreza_monetaria_total']
df_pobreza = pd.read_excel(EXCEL_PATH, sheet_name='Anexo1', skiprows=7, names=columnas)

# Normalizar campos de texto
for campo in ['departamento', 'provincia', 'distrito']:
    df_pobreza[campo] = df_pobreza[campo].astype(str).str.strip().str.upper()

# Conexión a la base de datos
conn = sqlite3.connect(DB_PATH)
df_inst = pd.read_sql_query('SELECT rowid, * FROM instituciones_educativas', conn)
for campo in ['region', 'provincia', 'distrito']:
    if campo in df_inst.columns:
        df_inst[campo] = df_inst[campo].astype(str).str.strip().str.upper()

# Vinculación en cascada y registro del método
pobreza_asignada = []
metodo_asignado = []
for idx, inst in df_inst.iterrows():
    # 1. Región + Provincia + Distrito
    filtro = (
        (df_pobreza['departamento'] == inst.get('region', '')) &
        (df_pobreza['provincia'] == inst.get('provincia', '')) &
        (df_pobreza['distrito'] == inst.get('distrito', ''))
    )
    match = df_pobreza.loc[filtro]
    if not match.empty:
        pobreza = match.iloc[0]['pobreza_monetaria_total']
        metodo = 'region+provincia+distrito'
    else:
        # 2. Región + Provincia
        filtro = (
            (df_pobreza['departamento'] == inst.get('region', '')) &
            (df_pobreza['provincia'] == inst.get('provincia', ''))
        )
        match = df_pobreza.loc[filtro]
        if not match.empty:
            pobreza = match['pobreza_monetaria_total'].mean()
            metodo = 'region+provincia'
        else:
            # 3. Región
            filtro = (df_pobreza['departamento'] == inst.get('region', ''))
            match = df_pobreza.loc[filtro]
            if not match.empty:
                pobreza = match['pobreza_monetaria_total'].mean()
                metodo = 'region'
            else:
                pobreza = np.nan
                metodo = 'sin_vinculo'
    pobreza_asignada.append(pobreza)
    metodo_asignado.append(metodo)

# Actualizar la columna en la base de datos
for i, pobreza, metodo in zip(df_inst['rowid'], pobreza_asignada, metodo_asignado):
    conn.execute('UPDATE instituciones_educativas SET pobreza_monetaria_distrito = ? WHERE rowid = ?', (pobreza, i))
conn.commit()
conn.close()

# Guardar reporte de métodos aplicados
reporte = pd.DataFrame({
    'rowid': df_inst['rowid'],
    'codigo_modular': df_inst['codigo_modular'],
    'region': df_inst['region'],
    'provincia': df_inst['provincia'],
    'distrito': df_inst['distrito'],
    'pobreza_monetaria_distrito': pobreza_asignada,
    'metodo_vinculacion': metodo_asignado
})
reporte.to_csv('temp_data/reporte_vinculacion_pobreza_20250810.csv', index=False)
print('Vinculación en cascada completada. Reporte guardado en temp_data/reporte_vinculacion_pobreza_20250810.csv')
