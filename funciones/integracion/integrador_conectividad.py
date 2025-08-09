#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
INTEGRADOR DE DATOS DE CONECTIVIDAD - Proyecto Reasis

Toma los matches exitosos de la tabla 'conectividad_progreso' y utiliza
esa información para poblar una nueva tabla 'conectividad_equipamiento'
con los datos completos del archivo Excel original.
"""

import pandas as pd
import sqlite3
import re
from pathlib import Path
import unidecode

def limpiar_nombre_columna(col_name):
    """Limpia un nombre de columna para que sea más corto y compatible con SQL."""
    # Convertir a string y quitar espacios extra
    s = str(col_name).strip()
    # Quitar acentos y caracteres especiales como '¿'
    s = unidecode.unidecode(s)
    # Reemplazar caracteres no alfanuméricos por guion bajo
    s = re.sub(r'[^a-zA-Z0-9]+', '_', s)
    # Quitar guiones bajos al principio y al final
    s = s.strip('_')
    # Convertir a minúsculas
    s = s.lower()
    # Truncar si es muy largo (64 es un límite seguro para muchos DBs)
    return s[:64]

def integrar_datos_conectividad():
    """Función principal para integrar los datos de conectividad."""
    print("=== INTEGRADOR DE DATOS DE CONECTIVIDAD Y EQUIPAMIENTO (V3) ===")
    
    db_path = Path("reasis_database.db")
    excel_path = Path("assets/Consultoria/Información actualizada/4. Conectividad y equipamiento.xlsx")

    if not db_path.exists() or not excel_path.exists():
        print(f"[ERROR] Error: No se encontró la base de datos o el archivo Excel.")
        print(f"  DB: {db_path.resolve()} (existe: {db_path.exists()})")
        print(f"  Excel: {excel_path.resolve()} (existe: {excel_path.exists()})")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 1. Leer los matches exitosos de la base de datos
        print("\n[1/5] Leyendo matches exitosos de 'conectividad_progreso'...")
        query_matches = """
        SELECT nombre_manual, codigo_modular_identificado 
        FROM conectividad_progreso 
        WHERE matching_status = 'MATCHED' AND codigo_modular_identificado != 'NO_MATCH'
        """
        df_matches = pd.read_sql_query(query_matches, conn)
        df_matches['nombre_manual'] = df_matches['nombre_manual'].astype(str).str.strip()
        print(f"[OK] Se encontraron {len(df_matches)} matches exitosos.")

        if df_matches.empty:
            print("No hay matches para integrar. Proceso terminado.")
            return

        # 2. Leer el archivo Excel original
        print("\n[2/5] Leyendo archivo Excel de conectividad...")
        df_excel = pd.read_excel(excel_path)
        print(f"[OK] Se leyeron {len(df_excel)} filas del archivo Excel.")

        columna_nombre_original = 'Si pertence a una Red Rural, indique el nombre de su IE'
        if columna_nombre_original not in df_excel.columns:
            print(f"[ERROR] Error: La columna '{columna_nombre_original}' no se encontró en el archivo Excel.")
            return
        df_excel[columna_nombre_original] = df_excel[columna_nombre_original].astype(str).str.strip()

        # 3. Unir datos del Excel con los matches
        print("\n[3/5] Uniendo datos del Excel con los matches...")
        df_integrado = pd.merge(
            df_excel,
            df_matches,
            left_on=columna_nombre_original,
            right_on='nombre_manual',
            how='left'
        )
        if 'nombre_manual' in df_integrado.columns:
            df_integrado = df_integrado.drop(columns=['nombre_manual'])
        print(f"[OK] DataFrame integrado creado con {len(df_integrado)} filas.")

        # 4. Crear la nueva tabla 'conectividad_equipamiento'
        print("\n[4/5] Creando la estructura de la tabla 'conectividad_equipamiento'...")
        nombre_tabla = 'conectividad_equipamiento'
        cursor.execute(f'DROP TABLE IF EXISTS {nombre_tabla}')

        columnas_excel_limpias = [limpiar_nombre_columna(col) for col in df_excel.columns]
        columnas_finales = ['codigo_modular'] + columnas_excel_limpias
        
        columnas_sql = ', '.join([f'"{col}" TEXT' for col in columnas_finales])
        create_table_sql = f'CREATE TABLE {nombre_tabla} ({columnas_sql})'
        cursor.execute(create_table_sql)
        print(f"[OK] Tabla '{nombre_tabla}' creada con {len(columnas_finales)} columnas.")

        # 5. Insertar los datos en la nueva tabla
        print(f"\n[5/5] Insertando {len(df_integrado)} registros en '{nombre_tabla}'...")
        
        # Preparar los datos para la inserción
        # El orden de las columnas debe coincidir con `columnas_finales`
        df_final = pd.DataFrame()
        df_final['codigo_modular'] = df_integrado['codigo_modular_identificado'].where(pd.notna(df_integrado['codigo_modular_identificado']), None)
        
        for col in df_excel.columns:
            df_final[limpiar_nombre_columna(col)] = df_integrado[col]

        # Convertir todas las columnas a string para evitar problemas de tipo con SQLite
        df_final = df_final.astype(str)
        # Convertir el DataFrame a una lista de tuplas para la inserción
        datos_para_insertar = [tuple(x) for x in df_final.to_numpy()]
        
        placeholders = ', '.join(['?'] * len(columnas_finales))
        insert_sql = f'INSERT INTO {nombre_tabla} VALUES ({placeholders})'
        
        cursor.executemany(insert_sql, datos_para_insertar)
        conn.commit()
        
        print(f"[OK] Se insertaron {cursor.rowcount} registros.")

        # Verificación final
        print(f"\nVerificando datos en '{nombre_tabla}'...")
        df_verificacion = pd.read_sql_query(f"SELECT * FROM {nombre_tabla} LIMIT 5", conn)
        print("Muestra de los datos integrados:")
        print(df_verificacion)
        
        count_linked = pd.read_sql_query(f"SELECT COUNT(*) FROM {nombre_tabla} WHERE codigo_modular IS NOT NULL", conn).iloc[0,0]
        count_unlinked = pd.read_sql_query(f"SELECT COUNT(*) FROM {nombre_tabla} WHERE codigo_modular IS NULL", conn).iloc[0,0]
        print(f"Resumen: {count_linked} vinculados, {count_unlinked} no vinculados.")

    except sqlite3.Error as e:
        print(f"[ERROR] Error de base de datos: {e}")
        conn.rollback()
    except Exception as e:
        print(f"[ERROR] Ocurrió un error inesperado: {e}")
    finally:
        conn.close()
        print("\n[FIN] Proceso de integración completado.")

if __name__ == "__main__":
    integrar_datos_conectividad()
