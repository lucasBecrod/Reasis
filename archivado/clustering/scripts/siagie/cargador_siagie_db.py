#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cargador de Datos SIAGIE a Base de Datos SQLite

Carga el archivo CSV consolidado de SIAGIE a la tabla matriculas_siagie.
Este script asume que el archivo consolidado ya contiene la vinculación
con los datos de las instituciones de Fe y Alegría.

Uso:
  python cargador_siagie_db.py
"""
import pandas as pd
import sqlite3
import os
import glob

def encontrar_archivo_consolidado_reciente(directorio, patron):
    """Encuentra el archivo más reciente que coincide con un patrón."""
    ruta_busqueda = os.path.join(directorio, patron)
    archivos = glob.glob(ruta_busqueda)
    if not archivos:
        return None
    # Encuentra el archivo más reciente basándose en la fecha de modificación
    archivo_mas_reciente = max(archivos, key=os.path.getmtime)
    return archivo_mas_reciente

def cargar_datos_a_db(db_path, csv_path):
    """
    Carga los datos desde un archivo CSV a una tabla en la base de datos SQLite.
    """
    if not os.path.exists(csv_path):
        print(f"[ERROR] No se encontró el archivo CSV: {csv_path}")
        return

    print(f"1. Leyendo datos desde: {os.path.basename(csv_path)}")
    try:
        # --- CORRECCIÓN: Forzar lectura de todas las columnas como texto (string) ---
        # Esto es la medida de seguridad final para garantizar que pandas no elimine
        # ceros a la izquierda de los códigos al inferir tipos de datos numéricos.
        df = pd.read_csv(csv_path, low_memory=False, dtype=str)
        print(f"   - Se leyeron {len(df):,} registros.")
    except Exception as e:
        print(f"[ERROR] Ocurrió un error al leer el archivo CSV: {e}")
        return

    # Limpieza de datos antes de cargar a la BD
    print("   - Limpiando y estandarizando tipos de datos...")
    cols_texto = ['codigo_local', 'codigo_modular', 'codigo_local_norm', 'codigo_modular_norm']
    for col in cols_texto:
        if col in df.columns:
            # Asegurar que los códigos sean tratados como texto para preservar ceros a la izquierda
            df[col] = df[col].astype(str).replace({'<NA>': None, 'nan': None, 'None': None})

    cols_numericas = ['anio', 'cod_dre', 'cod_ugel', 'ubigeo', 'anexo', 'total_alumnos', 'total_alumnos_norm', 'red_fya']
    for col in cols_numericas:
        if col in df.columns:
            # Convertir a numérico, forzando errores a NaN, y luego a Int64 que soporta nulos (pd.NA).
            df[col] = pd.to_numeric(df[col], errors='coerce').astype('Int64')

    print(f"\n2. Conectando a la base de datos SQLite en '{db_path}'...")
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        print("   - Conexión establecida.")

        table_name = 'matriculas_siagie'
        print(f"\n3. Cargando {len(df):,} registros a la tabla '{table_name}'...")
        print("   (Si la tabla ya existe, será reemplazada. Esto puede tardar unos segundos)")

        df.to_sql(table_name, conn, if_exists='replace', index=False)

        print(f"\n[ÉXITO] Se cargaron los datos correctamente.")

        # Verificación
        count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        print(f"   - Verificación: La tabla '{table_name}' ahora contiene {count:,} registros.")

    except sqlite3.Error as e:
        print(f"[ERROR] Ocurrió un error con la base de datos: {e}")
    finally:
        if conn:
            conn.close()
            print("\n4. Conexión a la base de datos cerrada.")

def main():
    """Función principal del script."""
    db_path = 'reasis_database.db'
    directorio_datos = "data/siagie_procesado"
    patron_consolidado = "siagie_fya_consolidado_*.csv"

    print("=== CARGADOR DE DATOS SIAGIE CONSOLIDADOS A SQLITE ===")
    
    archivo_consolidado = encontrar_archivo_consolidado_reciente(directorio_datos, patron_consolidado)

    if not archivo_consolidado:
        print(f"\n[ERROR] No se encontró ningún archivo consolidado en '{directorio_datos}' con el patrón '{patron_consolidado}'.")
        print("Asegúrate de haber ejecutado 'consolidador_siagie.py' primero.")
        return

    cargar_datos_a_db(db_path, archivo_consolidado)

if __name__ == "__main__":
    main()