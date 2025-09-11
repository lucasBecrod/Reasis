import os
import glob
import json
from datetime import datetime
import sqlite3
import pandas as pd
import numpy as np


def imputar_x11_por_red():
    db_path = 'reasis_database.db'
    os.makedirs('temp_data', exist_ok=True)
    os.makedirs('data/intermedios', exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    print(f"Conectando a la base de datos: {db_path}")
    conn = sqlite3.connect(db_path)

    try:
        # X11_RED disponibles con su red
        q_disp = """
        SELECT 
            i.CODIGO_MODULAR as codigo_modular,
            i.NOMBRE_INSTITUCION as nombre_institucion,
            i.X11_RED as x11_red,
            ie.nombre_red_fya_matched as red_fya
        FROM indices_metodologicos i
        LEFT JOIN instituciones_educativas ie
            ON ie.codigo_modular = i.CODIGO_MODULAR
        WHERE i.X11_RED IS NOT NULL
        """
        df_disp = pd.read_sql_query(q_disp, conn)

        # Faltantes con su red
        q_null = """
        SELECT 
            i.CODIGO_MODULAR as codigo_modular,
            i.NOMBRE_INSTITUCION as nombre_institucion,
            ie.nombre_red_fya_matched as red_fya,
            ie.total_alumnos,
            ie.total_docentes
        FROM indices_metodologicos i
        LEFT JOIN instituciones_educativas ie
            ON ie.codigo_modular = i.CODIGO_MODULAR
        WHERE i.X11_RED IS NULL
        """
        df_null = pd.read_sql_query(q_null, conn)

        print(f"X11_RED disponibles: {len(df_disp)} | Faltantes: {len(df_null)}")
        if df_null.empty:
            print("No hay faltantes para imputar.")
            return

        # Medianas por red
        mediana_por_red = (
            df_disp.dropna(subset=['red_fya'])
                  .groupby('red_fya')['x11_red']
                  .median()
        )
        mediana_global = df_disp['x11_red'].median() if not df_disp.empty else np.nan
        print(f"Mediana global X11_RED: {mediana_global:.4f}" if not np.isnan(mediana_global) else "Mediana global no disponible")

        imputaciones = []
        for _, r in df_null.iterrows():
            red = r['red_fya']
            metodo = None
            valor = None

            # Si existen ambos totales positivos, calcular directamente (caso borde)
            ta, td = r['total_alumnos'], r['total_docentes']
            if pd.notna(ta) and pd.notna(td) and ta > 0 and td > 0:
                valor = float(ta) / float(td)
                metodo = 'calculo_directo_total_alumnos_docentes'
            else:
                if pd.notna(red) and red in mediana_por_red.index:
                    valor = float(mediana_por_red.loc[red])
                    metodo = 'imputacion_mediana_red'
                else:
                    valor = float(mediana_global) if pd.notna(mediana_global) else None
                    metodo = 'imputacion_mediana_global'

            imputaciones.append({
                'codigo_modular': r['codigo_modular'],
                'nombre_institucion': r['nombre_institucion'],
                'red_fya': red,
                'X11_RED_imputado': valor,
                'metodo': metodo
            })

        df_imp = pd.DataFrame(imputaciones)
        df_imp_valid = df_imp[df_imp['X11_RED_imputado'].notna()].copy()

        csv_path = f"temp_data/x11_red_imputado_{timestamp}.csv"
        df_imp_valid.to_csv(csv_path, index=False, encoding='utf-8')
        print(f"CSV imputación generado: {csv_path} ({len(df_imp_valid)}/{len(df_imp)} filas con valor)")

        resumen = {
            'timestamp': timestamp,
            'faltantes_iniciales': int(len(df_null)),
            'imputados': int(len(df_imp_valid)),
            'no_imputados': int(len(df_imp) - len(df_imp_valid)),
            'mediana_global': None if np.isnan(mediana_global) else float(mediana_global),
            'metrica_por_red_disponible': int(mediana_por_red.size),
            'metodo': 'mediana_por_red -> mediana_global; cálculo directo si totales disponibles'
        }
        json_path = f"data/intermedios/x11_red_imputacion_resumen_{timestamp}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(resumen, f, ensure_ascii=False, indent=2)
        print(f"JSON resumen: {json_path}")

        # Mostrar caso solicitado si existe
        muestra_253 = df_imp_valid[df_imp_valid['codigo_modular'].astype(str) == '2533906']
        if not muestra_253.empty:
            print("\nImputación 2533906:")
            print(muestra_253)

    finally:
        conn.close()


if __name__ == '__main__':
    imputar_x11_por_red()


