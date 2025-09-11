#!/usr/bin/env python3
"""
Generador de Reportes a partir de Datos SIAGIE Consolidados

Este script realiza dos funciones principales:
1.  Limpia y unifica el archivo CSV consolidado que tiene columnas inconsistentes
    debido a las diferencias en los archivos DBF originales de cada año.
2.  Genera un reporte de ejemplo (total de alumnos por año) para demostrar
    el uso de los datos limpios.

Uso:
  python generador_reportes.py
"""

import pandas as pd
import numpy as np
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

def limpiar_y_unificar_datos(df_bruto):
    """
    Toma el DataFrame consolidado y lo limpia, unificando columnas.
    """
    print("2. Unificando columnas de diferentes años...")
    
    # Crear columnas unificadas usando .fillna() para combinar datos
    # La primera columna que no sea nula (NaN) será la que aporte el dato.
    df_limpio = pd.DataFrame()
    df_limpio['año_reporte'] = df_bruto['id_anio'].fillna(df_bruto['anio']).astype(int)
    df_limpio['total_alumnos'] = df_bruto['total_alumnos_norm'].fillna(df_bruto['total']).fillna(df_bruto['talumnos']).astype(int)
    
    # Columnas que ya fueron normalizadas o son consistentes
    df_limpio['codigo_modular'] = df_bruto['codigo_modular_norm']
    df_limpio['nombre_fya_bd'] = df_bruto['nombre_fya_bd']
    df_limpio['red_fya'] = df_bruto['red_fya']
    
    # Unificar columnas de ubicación y de la IE
    df_limpio['nombre_ie_siagie'] = df_bruto['nombre_iie'].fillna(df_bruto['nombre_ie'])
    df_limpio['departamento_siagie'] = df_bruto['dpto'].fillna(df_bruto['departamen'])
    df_limpio['provincia_siagie'] = df_bruto['prov'].fillna(df_bruto['provincia'])
    df_limpio['distrito_siagie'] = df_bruto['dist'].fillna(df_bruto['distrito'])
    df_limpio['nivel_siagie'] = df_bruto['nivel'].fillna(df_bruto['dsc_nivel'])
    
    print("   Limpieza completada.")
    return df_limpio

def generar_reporte_alumnos_por_año(df):
    """
    Calcula y muestra un resumen del total de alumnos por año.
    """
    print("\n3. Generando reporte: Total de Alumnos de Fe y Alegría por Año")
    
    # Agrupar por año y sumar el total de alumnos
    reporte = df.groupby('año_reporte')['total_alumnos'].sum().reset_index()
    reporte = reporte.sort_values('año_reporte')
    
    print("\n" + "="*40)
    print("   REPORTE ANUAL DE ALUMNOS (SIAGIE)")
    print("="*40)
    for _, row in reporte.iterrows():
        print(f"   Año {row['año_reporte']}: {row['total_alumnos']:,} alumnos")
    print("="*40)

def main():
    """Función principal del script."""
    directorio_datos = "data/siagie_procesado"
    archivo_consolidado = encontrar_archivo_consolidado_reciente(directorio_datos, "siagie_fya_consolidado_*.csv")
    
    if not archivo_consolidado:
        print(f"[ERROR] No se encontró ningún archivo consolidado en '{directorio_datos}'")
        return

    print(f"1. Cargando datos desde: {archivo_consolidado}")
    df_bruto = pd.read_csv(archivo_consolidado, low_memory=False)
    
    df_limpio = limpiar_y_unificar_datos(df_bruto)
    
    generar_reporte_alumnos_por_año(df_limpio)
    
    # Opcional: Guardar el DataFrame limpio para usarlo en otras herramientas (Excel, Power BI, etc.)
    archivo_limpio_path = os.path.join(directorio_datos, 'siagie_fya_consolidado_LIMPIO.csv')
    df_limpio.to_csv(archivo_limpio_path, index=False, encoding='utf-8')
    print(f"\n[INFO] Se ha guardado una versión limpia de los datos en:\n       {archivo_limpio_path}")

if __name__ == "__main__":
    main()