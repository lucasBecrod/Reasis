#!/usr/bin/env python3
"""
Consolidador SIAGIE - Combina todos los archivos anuales en uno solo
"""

import pandas as pd
import os
from datetime import datetime

def consolidar_todos_los_años():
    """Consolida todos los archivos anuales generados"""
    print(f"[CONSOLIDANDO] TODOS LOS AÑOS SIAGIE FYA")
    print(f"Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    output_dir = "data/siagie_procesado"
    años = [2019, 2020, 2021, 2022, 2023, 2024]
    
    todos_dataframes = []
    archivos_encontrados = []
    
    # Buscar archivos de cada año
    for año in años:
        archivo = os.path.join(output_dir, f'siagie_fya_{año}_completo.csv')
        
        if os.path.exists(archivo):
            print(f"[OK] Encontrado: {archivo}")
            df = pd.read_csv(archivo)
            todos_dataframes.append(df)
            archivos_encontrados.append(año)
        else:
            print(f"[INFO] No encontrado: {archivo}")
    
    if not todos_dataframes:
        print("[ERROR] No se encontraron archivos para consolidar")
        return None
    
    # Consolidar todos los dataframes
    print(f"\\n[PROCESANDO] Consolidando {len(todos_dataframes)} archivos...")
    df_consolidado = pd.concat(todos_dataframes, ignore_index=True)
    
    # Archivo consolidado
    archivo_consolidado = os.path.join(output_dir, 'siagie_fya_historico_2019_2024_completo.csv')
    df_consolidado.to_csv(archivo_consolidado, index=False, encoding='utf-8')
    
    # Estadísticas finales
    total_registros = len(df_consolidado)
    instituciones_totales = df_consolidado['COD_MOD'].nunique()
    alumnos_totales = df_consolidado['TALUMNOS'].sum() if 'TALUMNOS' in df_consolidado.columns else 0
    
    print(f"\\n[CONSOLIDACION COMPLETADA]:")
    print(f"   Años procesados: {archivos_encontrados}")
    print(f"   Total registros históricos: {total_registros:,}")
    print(f"   Instituciones únicas: {instituciones_totales}")
    print(f"   Total alumnos históricos: {int(alumnos_totales):,}")
    print(f"   Archivo consolidado: {archivo_consolidado}")
    
    # Resumen por año
    if 'ID_ANIO' in df_consolidado.columns:
        print(f"\\nRESUMEN POR AÑO:")
        resumen_años = df_consolidado.groupby('ID_ANIO').agg({
            'COD_MOD': 'nunique',
            'TALUMNOS': 'sum'
        }).reset_index()
        
        for _, row in resumen_años.iterrows():
            alumnos = int(row['TALUMNOS']) if pd.notna(row['TALUMNOS']) else 0
            print(f"   {int(row['ID_ANIO'])}: {row['COD_MOD']} instituciones, {alumnos} alumnos")
    
    # Resumen por red
    print(f"\\nRESUMEN POR RED:")
    resumen_redes = df_consolidado.groupby('RED_FYA').agg({
        'COD_MOD': 'nunique',
        'TALUMNOS': 'sum'
    }).reset_index()
    
    for _, row in resumen_redes.iterrows():
        alumnos = int(row['TALUMNOS']) if pd.notna(row['TALUMNOS']) else 0
        print(f"   Red {row['RED_FYA']}: {row['COD_MOD']} instituciones, {alumnos} alumnos")
    
    print(f"\\nFin: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return {
        'archivo_consolidado': archivo_consolidado,
        'total_registros': total_registros,
        'instituciones_unicas': instituciones_totales,
        'total_alumnos': int(alumnos_totales),
        'años_procesados': archivos_encontrados
    }

if __name__ == "__main__":
    consolidar_todos_los_años()