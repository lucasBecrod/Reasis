'''
Script para corregir un código modular en 'resultados_academicos' y luego
integrar la IIEE en 'instituciones_educativas' si no existe.
'''
import sqlite3
import pandas as pd
from simpledbf import Dbf5

def corregir_e_integrar_ie():
    db_path = 'reasis_database.db'
    padron_path = 'data/bases_de_datos/Padron_web_20250731/Padron_web.dbf'
    codigo_modular_antiguo = '658427'
    codigo_modular_nuevo = '0600692'
    codigo_red_asociado = '79' # Obtenido del análisis previo

    print(f"Conectando a la base de datos: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Paso 1: Corregir el código modular en resultados_academicos
        print(f"Actualizando código modular de {codigo_modular_antiguo} a {codigo_modular_nuevo} en 'resultados_academicos'...")
        update_query = "UPDATE resultados_academicos SET codigo_modular = ? WHERE codigo_modular = ?"
        cursor.execute(update_query, (codigo_modular_nuevo, codigo_modular_antiguo))
        conn.commit()
        print(f"{cursor.rowcount} filas fueron actualizadas.")

        # Paso 2: Verificar si la IIEE ya existe en instituciones_educativas
        print(f"Verificando si la IIEE con código modular {codigo_modular_nuevo} ya existe...")
        cursor.execute("SELECT 1 FROM instituciones_educativas WHERE codigo_modular = ?", (codigo_modular_nuevo,))
        if cursor.fetchone():
            print(f"La IIEE con código modular {codigo_modular_nuevo} ya existe en la tabla. No se necesita integración.")
            return

        # Paso 3: Integrar si no existe
        print(f"La IIEE no existe. Procediendo con la integración...")
        
        # Cargar datos necesarios
        df_redes = pd.read_sql_query("SELECT * FROM redes_fe_y_alegria WHERE codigo_red = ?", conn, params=(codigo_red_asociado,))
        dbf = Dbf5(padron_path, codec='latin-1')
        df_padron = dbf.to_dataframe()
        df_padron['COD_MOD'] = df_padron['COD_MOD'].astype(str)

        # Obtener datos del padrón
        datos_padron = df_padron[df_padron['COD_MOD'] == codigo_modular_nuevo]
        if datos_padron.empty:
            print(f"FATAL: No se encontraron datos en el padrón para el código modular corregido: {codigo_modular_nuevo}")
            return
        ie = datos_padron.iloc[0].to_dict()

        # Obtener datos de la red
        id_red, nombre_red = (df_redes.iloc[0]['id'], df_redes.iloc[0]['nombre_completo']) if not df_redes.empty else (None, None)
        print(f"Información de la red encontrada: {nombre_red}")

        # Mapeo y preparación de datos
        data_to_insert = {
            'codigo_modular': ie.get('COD_MOD'), 'codigo_local': ie.get('CODLOCAL'), 'nombre_institucion': ie.get('CEN_EDU'),
            'region': ie.get('D_REGION'), 'provincia': ie.get('D_PROV'), 'distrito': ie.get('D_DIST'),
            'departamento': ie.get('D_DPTO'), 'direccion': ie.get('DIR_CEN'), 'localidad': ie.get('LOCALIDAD'),
            'centro_poblado': ie.get('CEN_POB'), 'area_censo': ie.get('DAREACENSO'), 'latitud': ie.get('NLAT_IE'),
            'longitud': ie.get('NLONG_IE'), 'nivel_educativo': ie.get('D_NIV_MOD'), 'gestion': ie.get('D_GESTION'),
            'tipo_sexo': ie.get('D_TIPSSEXO'), 'total_alumnos': ie.get('TALUMNO'), 'alumnos_hombres': ie.get('TALUM_HOM'),
            'alumnos_mujeres': ie.get('TALUM_MUJ'), 'total_docentes': ie.get('TDOCENTE'), 'total_secciones': ie.get('TSECCION'),
            'director': ie.get('DIRECTOR'), 'telefono': ie.get('TELEFONO'), 'email': ie.get('EMAIL'),
            'id_red_fya': id_red, 'nombre_red_fya_matched': nombre_red
        }

        # Inserción en la base de datos
        columns = ', '.join(data_to_insert.keys())
        placeholders = ', '.join(['?' for _ in data_to_insert.values()])
        sql = f"INSERT INTO instituciones_educativas ({columns}) VALUES ({placeholders})"
        
        cursor.execute(sql, tuple(data_to_insert.values()))
        conn.commit()
        print(f"Integración completada. Se insertó la IIEE con código modular {codigo_modular_nuevo}.")

    finally:
        conn.close()

if __name__ == "__main__":
    corregir_e_integrar_ie()
