
Script para integrar nuevas instituciones educativas desde un archivo JSON a la base de datos.

Este script realiza las siguientes acciones:
1. Lee el archivo JSON 'lib/iiee_faltantes.json' que contiene los datos de las IIEE faltantes.
2. Se conecta a la base de datos SQLite 'reasis_database.db'.
3. Carga la tabla 'redes_fe_y_alegria' para buscar la red correspondiente a cada IIEE.
4. Itera sobre cada IIEE en el archivo JSON:
    a. Busca una red compatible comparando la ubicación de la IIEE (distrito, provincia, departamento) con el campo 'lugar' de la tabla de redes.
    b. Prepara un diccionario con los datos de la IIEE, mapeando las columnas del JSON a las de la tabla 'instituciones_educativas'.
    c. Inserta el nuevo registro en la tabla 'instituciones_educativas', evitando duplicados.

import sqlite3
import json
import os
import pandas as pd

def integrar_nuevas_iiee():
    json_path = 'lib/iiee_faltantes.json'
    db_path = 'reasis_database.db'

    if not os.path.exists(json_path):
        print(f"El archivo {json_path} no fue encontrado. Ejecute primero el script de identificación.")
        return

    print("Iniciando la integración de nuevas IIEE...")
    with open(json_path, 'r', encoding='utf-8') as f:
        iiee_faltantes = json.load(f)

    print(f"Conectando a la base de datos: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        print("Cargando la tabla de redes de Fe y Alegría...")
        df_redes = pd.read_sql_query("SELECT * FROM redes_fe_y_alegria", conn)

        instituciones_insertadas = 0
        for ie in iiee_faltantes:
            # Evitar inserción si el código modular ya existe
            cursor.execute("SELECT 1 FROM instituciones_educativas WHERE codigo_modular = ?", (ie.get('COD_MOD'),))
            if cursor.fetchone():
                print(f"La IIEE con código modular {ie.get('COD_MOD')} ya existe. Omitiendo.")
                continue

            # Buscar la red de Fe y Alegría
            id_red = None
            nombre_red = None
            # Búsqueda por distrito, provincia y departamento
            for campo_ubicacion in ['D_DIST', 'D_PROV', 'D_DPTO']:
                ubicacion = ie.get(campo_ubicacion, '').strip().upper()
                if not ubicacion:
                    continue
                
                # Búsqueda más flexible (contains)
                red_match = df_redes[df_redes['lugar'].str.upper().str.contains(ubicacion, na=False)]
                if not red_match.empty:
                    id_red = red_match.iloc[0]['id']
                    nombre_red = red_match.iloc[0]['nombre_completo']
                    print(f"Red encontrada para {ie.get('CEN_EDU')}: {nombre_red} (basado en {campo_ubicacion}: {ubicacion})")
                    break
            
            if not nombre_red:
                 print(f"No se encontró red para {ie.get('CEN_EDU')}")

            # Mapeo de datos
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

            # Construcción de la consulta de inserción
            columns = ', '.join(data_to_insert.keys())
            placeholders = ', '.join(['?' for _ in data_to_insert.values()])
            sql = f"INSERT INTO instituciones_educativas ({columns}) VALUES ({placeholders})"

            try:
                cursor.execute(sql, tuple(data_to_insert.values()))
                instituciones_insertadas += 1
            except sqlite3.IntegrityError as e:
                print(f"Error de integridad al insertar {ie.get('COD_MOD')}: {e}")
            except Exception as e:
                print(f"Error inesperado al insertar {ie.get('COD_MOD')}: {e}")

        conn.commit()
        print(f"\nIntegración completada. Se insertaron {instituciones_insertadas} nuevas IIEE.")

    finally:
        conn.close()

if __name__ == "__main__":
    integrar_nuevas_iiee()
