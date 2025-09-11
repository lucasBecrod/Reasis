'''
Temporal script to inspect the schema of the national database.
'''
from simpledbf import Dbf5

def inspect_padron_schema():
    padron_path = 'data/bases_de_datos/Padron_web_20250731/Padron_web.dbf'
    print(f"Leyendo el padrón nacional desde: {padron_path}")
    try:
        dbf = Dbf5(padron_path, codec='latin-1')
        df_padron = dbf.to_dataframe()
        print("Columnas del padrón:")
        print(df_padron.columns)
    except Exception as e:
        print(f"Error al leer el archivo DBF: {e}")

if __name__ == "__main__":
    inspect_padron_schema()
