#!/usr/bin/env python3
"""
Paso 2: Mejora de Vinculación de Redes con Homologación Manual - Proyecto Reasis
Utiliza el archivo homologacionManualLucas.xlsx para completar vinculaciones de RER.
"""

import pandas as pd
import sqlite3
from pathlib import Path

DB_PATH = 'reasis_database.db'
EXCEL_PATH = Path("assets/Consultoria/DatosLucas/homologacionManualLucas.xlsx")

def mejorar_vinculacion_con_homologacion():
    """Lee el archivo de homologación y actualiza las instituciones sin red asignada."""
    print("--- INICIANDO PASO 2: MEJORA DE VINCULACIÓN CON DATOS MANUALES ---")
    print("=" * 70)

    if not EXCEL_PATH.exists():
        print(f"⚠️  Archivo de homologación no encontrado en: {EXCEL_PATH}")
        print("   Se omitirá este paso.")
        return 0

    try:
        df_colegios = pd.read_excel(EXCEL_PATH, sheet_name='colegios')
        print(f"  Leyendo {len(df_colegios)} registros desde '{EXCEL_PATH.name}'.")
    except Exception as e:
        print(f"❌ Error al leer el archivo Excel: {e}")
        return 0

    # Identificar columnas relevantes (código y rer)
    col_codigo = next((col for col in df_colegios.columns if 'codigo_local' in col.lower()), None)
    col_rer = next((col for col in df_colegios.columns if 'rer' in col.lower()), None)

    if not col_codigo or not col_rer:
        print("❌ No se encontraron las columnas 'codigo_local' y 'rer' en el Excel.")
        return 0

    # Preparar datos para la actualización
    df_mapeo = df_colegios[[col_codigo, col_rer]].copy()
    df_mapeo.columns = ['codigo_local', 'rer']
    df_mapeo = df_mapeo.dropna().astype({'codigo_local': str, 'rer': str})
    df_mapeo = df_mapeo[df_mapeo['rer'].str.match(r'^\d+$')] # Asegurar que RER sea numérico

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    instituciones_mejoradas = 0
    
    for _, row in df_mapeo.iterrows():
        codigo_local = row['codigo_local']
        codigo_red = f"RER FA {row['rer']}"
        
        # Actualizar solo si la institución existe y NO tiene un codigo_red asignado
        cursor.execute('''
            UPDATE instituciones_educativas
            SET codigo_red = ?
            WHERE codigo_local = ? AND (codigo_red IS NULL OR codigo_red = '')
        ''', (codigo_red, codigo_local))
        
        if cursor.rowcount > 0:
            instituciones_mejoradas += cursor.rowcount

    conn.commit()

    print(f"  ✅ Proceso de mejora finalizado.")
    print(f"  Se vincularon {instituciones_mejoradas} instituciones adicionales.")

    # Reporte final
    vinculadas_antes = pd.read_sql_query('SELECT COUNT(*) FROM instituciones_educativas WHERE codigo_red IS NOT NULL', conn).iloc[0,0] - instituciones_mejoradas
    vinculadas_ahora = pd.read_sql_query('SELECT COUNT(*) FROM instituciones_educativas WHERE codigo_red IS NOT NULL', conn).iloc[0,0]
    total_instituciones = pd.read_sql_query('SELECT COUNT(*) FROM instituciones_educativas', conn).iloc[0,0]

    print("\n--- REPORTE DE MEJORA ---")
    print(f"Instituciones vinculadas antes: {vinculadas_antes}")
    print(f"Instituciones vinculadas ahora: {vinculadas_ahora}")
    if total_instituciones > 0:
        print(f"Nueva cobertura: {vinculadas_ahora / total_instituciones * 100:.1f}%")

    conn.close()
    return instituciones_mejoradas

def main():
    mejoradas = mejorar_vinculacion_con_homologacion()
    print("\n" + "=" * 70)
    if mejoradas > 0:
        print("✅ PASO 2 COMPLETADO EXITOSAMENTE.")
    else:
        print("PASO 2 COMPLETADO. No se encontraron nuevas instituciones para vincular.")
    print("=" * 70)

if __name__ == "__main__":
    main()