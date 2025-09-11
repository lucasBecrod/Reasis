'''
Script para integrar IIEE faltantes usando el 'codigo_red' actualizado.

Pasos:
1. Identifica IIEE en 'resultados_academicos' que no están en 'instituciones_educativas'.
2. Obtiene el 'codigo_red' de estas IIEE desde 'resultados_academicos'.
3. Busca la información de la red correspondiente en 'redes_fe_y_alegria'.
4. Obtiene los datos completos de la IIEE desde el padrón nacional.
5. Inserta las nuevas IIEE en la tabla 'instituciones_educativas'.
'''
import sqlite3
import pandas as pd
from simpledbf import Dbf5

def integrar_iiee_con_codigo_red():
    db_path = 'reasis_database.db'
    padron_path = 'data/bases_de_datos/Padron_web_20250731/Padron_web.dbf'
    print(f"Conectando a la base de datos: {db_path}")
    conn = sqlite3.connect(db_path)

    try:
        # Cargar tablas necesarias
        df_resultados = pd.read_sql_query("SELECT DISTINCT codigo_modular, codigo_red FROM resultados_academicos", conn)
        df_instituciones = pd.read_sql_query("SELECT DISTINCT codigo_modular FROM instituciones_educativas", conn)
        df_redes = pd.read_sql_query("SELECT * FROM redes_fe_y_alegria", conn)
        
        print("Identificando IIEE faltantes...")
        codigos_existentes = set(df_instituciones['codigo_modular'])
        df_faltantes = df_resultados[~df_resultados['codigo_modular'].isin(codigos_existentes)].drop_duplicates(subset=['codigo_modular'])

        if df_faltantes.empty:
            print("No hay IIEE nuevas para integrar.")
            return

        print(f"Se encontraron {len(df_faltantes)} IIEE para integrar.")

        # Cargar padrón nacional
        print(f"Leyendo el padrón nacional desde: {padron_path}")
        dbf = Dbf5(padron_path, codec='latin-1')
        df_padron = dbf.to_dataframe()
        df_padron['COD_MOD'] = df_padron['COD_MOD'].astype(str)

        # Integrar cada IIEE faltante
        instituciones_insertadas = 0
        for _, row in df_faltantes.iterrows():
            codigo_modular_faltante = row['codigo_modular']
            codigo_red_faltante = row['codigo_red']

            # Obtener datos del padrón
            datos_padron = df_padron[df_padron['COD_MOD'] == codigo_modular_faltante]
            if datos_padron.empty:
                print(f"No se encontraron datos en el padrón para el código modular: {codigo_modular_faltante}")
                continue
            ie = datos_padron.iloc[0].to_dict()

            # Obtener datos de la red
            red_info = df_redes[df_redes['codigo_red'] == codigo_red_faltante]
            id_red = None
            nombre_red = None
            if not red_info.empty:
                id_red = red_info.iloc[0]['id']
                nombre_red = red_info.iloc[0]['nombre_completo']
                print(f"Red encontrada para {ie.get('CEN_EDU')}: {nombre_red}")
            else:
                print(f"No se encontró red para el código de red: {codigo_red_faltante}")

            # Mapeo y preparación de datos
            data_to_insert = {
                'codigo_modular': ie.get('COD_MOD'),
                'codigo_local': ie.get('CODLOCAL'),
                'nombre_institucion': ie.get('CEN_EDU'),
                'region': ie.get('D_REGION'),
                'provincia': ie.get('D_PROV'),
                'distrito': ie.get('D_DIST'),
                'departamento': ie.get('D_DPTO'),
                'direccion': ie.get('DIR_CEN'),
                'localidad': ie.get('LOCALIDAD'),
                'centro_poblado': ie.get('CEN_POB'),
                'area_censo': ie.get('DAREACENSO'),
                'latitud': ie.get('NLAT_IE'),
                'longitud': ie.get('NLONG_IE'),
                'nivel_educativo': ie.get('D_NIV_MOD'),
                'gestion': ie.get('D_GESTION'),
                'tipo_sexo': ie.get('D_TIPSSEXO'),
                'total_alumnos': ie.get('TALUMNO'),
                'alumnos_hombres': ie.get('TALUM_HOM'),
                'alumnos_mujeres': ie.get('TALUM_MUJ'),
                'total_docentes': ie.get('TDOCENTE'),
                'total_secciones': ie.get('TSECCION'),
                'director': ie.get('DIRECTOR'),
                'telefono': ie.get('TELEFONO'),
                'email': ie.get('EMAIL'),
                'id_red_fya': id_red,
                'nombre_red_fya_matched': nombre_red
            }

            # Inserción en la base de datos
            cursor = conn.cursor()
            columns = ', '.join(data_to_insert.keys())
            placeholders = ', '.join(['?' for _ in data_to_insert.values()])
            sql = f"INSERT INTO instituciones_educativas ({columns}) VALUES ({placeholders})"
            
            try:
                cursor.execute(sql, tuple(data_to_insert.values()))
                instituciones_insertadas += 1
            except sqlite3.IntegrityError:
                print(f"La IIEE con código modular {codigo_modular_faltante} ya existe (error de integridad). Omitiendo.")
            except Exception as e:
                print(f"Error inesperado al insertar {codigo_modular_faltante}: {e}")

        conn.commit()
        print(f"\nIntegración completada. Se insertaron {instituciones_insertadas} nuevas IIEE.")

    finally:
        conn.close()

if __name__ == "__main__":
    integrar_iiee_con_codigo_red()
