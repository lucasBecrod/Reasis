#!/usr/bin/env python3
"""
Paso 7: Explorador de Competencias Digitales Docentes - Proyecto Reasis
Analiza la estructura del archivo '3. BD Comp Digitales Docentes 2025.xlsx'.
"""

import pandas as pd
from pathlib import Path

EXCEL_PATH = Path("assets/Consultoria/Información actualizada/3. BD Comp Digitales Docentes 2025.xlsx")

def explorar_competencias_digitales():
    """
    Lee el archivo de competencias digitales, analiza las columnas clave
    y muestra un resumen para validar la estructura.
    """
    print("--- INICIANDO PASO 7: ANÁLISIS EXPLORATORIO DE COMPETENCIAS DIGITALES ---")
    print("=" * 75)

    if not EXCEL_PATH.exists():
        print(f"❌ ERROR: Archivo no encontrado en la ruta esperada:")
        print(f"   {EXCEL_PATH}")
        return

    print(f"📖 Leyendo archivo: {EXCEL_PATH.name}, hoja: 'DATA'")
    try:
        df = pd.read_excel(EXCEL_PATH, sheet_name='DATA')
    except Exception as e:
        print(f"❌ Error al leer el archivo Excel: {e}")
        return

    # Columnas de interés especificadas por el usuario
    columnas_demograficas = ['Marca temporal', 'Año', 'Ambito', 'Puntuación', 'Nombre de la RER', 'Edad', 'Rango edad', 'Sexo']
    columnas_dimensiones = ['Profesional empoderado', 'Catalizador del aprendizaje', 'Nota Global Relativa']
    columnas_a_explorar = columnas_demograficas + columnas_dimensiones

    # Verificar si las columnas existen
    columnas_existentes = [col for col in columnas_a_explorar if col in df.columns]
    columnas_faltantes = [col for col in columnas_a_explorar if col not in df.columns]

    if columnas_faltantes:
        print(f"\n⚠️  ADVERTENCIA: Las siguientes columnas no se encontraron: {columnas_faltantes}")

    print(f"\n✅ Columnas de interés encontradas: {len(columnas_existentes)}")
    df_filtrado = df[columnas_existentes]

    print("\n--- MUESTRA DE LOS DATOS (PRIMERAS 5 FILAS) ---")
    print(df_filtrado.head().to_string())

    print("\n\n--- ANÁLISIS DE LAS DIMENSIONES (NIVELES DE LOGRO) ---")
    for col in columnas_dimensiones:
        if col in df_filtrado.columns:
            print(f"\nValores en la columna '{col}':")
            print(df_filtrado[col].value_counts().to_string())

    print("\n\n--- ANÁLISIS DE VINCULACIÓN ---")
    if 'Nombre de la RER' in df_filtrado.columns:
        print("La columna 'Nombre de la RER' se usará para vincular con la tabla 'redes_fe_y_alegria'.")
        print("Ejemplo de valor:", df_filtrado['Nombre de la RER'].iloc[0])

    print("\n" + "=" * 75)
    print("✅ ANÁLISIS EXPLORATORIO COMPLETADO.")
    print("   La estructura parece correcta para proceder con la importación.")
    print("=" * 75)

if __name__ == "__main__":
    explorar_competencias_digitales()