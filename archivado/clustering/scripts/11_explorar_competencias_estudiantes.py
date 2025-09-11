#!/usr/bin/env python3
"""
Paso 11: Explorador de Competencias Digitales de Estudiantes - Proyecto Reasis
Analiza la estructura del archivo '3. BD Comp Digitales Estudiantes 2024.xlsx'.
"""

import pandas as pd
from pathlib import Path

EXCEL_PATH = Path("assets/Consultoria/Información actualizada/3. BD Comp Digitales Estudiantes 2024.xlsx")

def explorar_competencias_estudiantes():
    """
    Lee el archivo de competencias de estudiantes, analiza las columnas de
    dimensiones para identificar todos los niveles de logro existentes.
    """
    print("--- INICIANDO PASO 11: ANÁLISIS EXPLORATORIO DE COMPETENCIAS DE ESTUDIANTES ---")
    print("=" * 80)

    if not EXCEL_PATH.exists():
        print(f"❌ ERROR: Archivo no encontrado en la ruta esperada:\n   {EXCEL_PATH}")
        return

    print(f"📖 Leyendo archivo: {EXCEL_PATH.name}, hoja: 'DATA'")
    try:
        df = pd.read_excel(EXCEL_PATH, sheet_name='DATA')
    except Exception as e:
        print(f"❌ Error al leer el archivo Excel: {e}")
        return

    # Columnas de dimensiones clave a investigar
    columnas_dimensiones = [
        'NOTA GLOBAL',
        'COMPETENCIAS DIGITALES',
        'PENSAMIENTO COMPUTACIONAL',
        'CIUDADANÍA DIGITAL'
    ]

    print("\n--- ANÁLISIS DE NIVELES DE LOGRO ENCONTRADOS ---")
    print("Buscando todos los valores únicos para confirmar la escala (Inicio, En Proceso, Logrado, ¿Destacado?)...")

    for col in columnas_dimensiones:
        if col in df.columns:
            print(f"\nValores únicos en la columna '{col}':")
            # value_counts() nos muestra todos los valores y su frecuencia
            print(df[col].value_counts().to_string())
        else:
            print(f"\n⚠️  ADVERTENCIA: La columna '{col}' no se encontró.")

    print("\n\n--- ANÁLISIS DE VINCULACIÓN ---")
    if 'RED' in df.columns:
        print("La columna 'RED' se usará para vincular con la tabla 'redes_fe_y_alegria'.")
        # El formato 'RER FA 44 CUSCO' coincide con la columna 'red_lugar' de la tabla de redes.
        print("Ejemplo de valor:", df['RED'].dropna().iloc[0])

    print("\n" + "=" * 80)
    print("✅ ANÁLISIS EXPLORATORIO COMPLETADO.")
    print("   Revisa los niveles de logro para confirmar el mapeo numérico.")
    print("=" * 80)

if __name__ == "__main__":
    explorar_competencias_estudiantes()