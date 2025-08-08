#!/usr/bin/env python3
"""
Paso 8: Importador de Competencias Digitales Docentes - Proyecto Reasis
Crea y puebla la tabla 'competencia_digital_docentes' desde el archivo Excel.
"""

import pandas as pd
import sqlite3
from pathlib import Path

# --- CONFIGURACIÓN ---
DB_PATH = 'reasis_database.db'
EXCEL_PATH = Path("assets/Consultoria/Información actualizada/3. BD Comp Digitales Docentes 2025.xlsx")
NUEVA_TABLA = 'competencia_digital_docentes'

# Mapeo de niveles a valores numéricos
MAPEO_NIVELES = {
    'Nivel básico': 1,
    'En proceso': 2,
    'Logro esperado': 3,
    'Logro destacado': 4
}

def importar_competencias_digitales():
    """
    Procesa el archivo Excel de competencias digitales y lo importa a una nueva tabla SQL.
    """
    print(f"--- INICIANDO PASO 8: IMPORTACIÓN DE COMPETENCIAS DIGITALES A '{NUEVA_TABLA}' ---")
    print("=" * 80)

    # 1. Leer el archivo Excel
    try:
        df = pd.read_excel(EXCEL_PATH, sheet_name='DATA')
        print(f"✅ Archivo Excel leído con {len(df)} filas.")
    except Exception as e:
        print(f"❌ Error fatal al leer el archivo Excel: {e}")
        return

    # 2. Seleccionar y renombrar columnas
    columnas_a_usar = {
        'Marca temporal': 'marca_temporal',
        'Año': 'año',
        'Ambito': 'ambito',
        'Puntuación': 'puntuacion_texto',
        'Nombre de la RER': 'nombre_rer',
        'Edad': 'edad',
        'Rango edad': 'rango_edad',
        'Sexo': 'sexo',
        'Profesional empoderado': 'profesional_empoderado_texto',
        'Catalizador del aprendizaje': 'catalizador_aprendizaje_texto',
        'Nota Global Relativa': 'nota_global_relativa_texto'
    }
    df_procesado = df[list(columnas_a_usar.keys())].copy()
    df_procesado.rename(columns=columnas_a_usar, inplace=True)
    print("✅ Columnas seleccionadas y renombradas.")

    # 3. Transformar las dimensiones a valores numéricos
    df_procesado['profesional_empoderado_num'] = df_procesado['profesional_empoderado_texto'].map(MAPEO_NIVELES)
    df_procesado['catalizador_aprendizaje_num'] = df_procesado['catalizador_aprendizaje_texto'].map(MAPEO_NIVELES)
    df_procesado['nota_global_relativa_num'] = df_procesado['nota_global_relativa_texto'].map(MAPEO_NIVELES)
    print("✅ Dimensiones de texto convertidas a valores numéricos.")

    # 4. Vincular con la tabla de redes para obtener 'codigo_red'
    conn = sqlite3.connect(DB_PATH)
    try:
        df_redes = pd.read_sql_query("SELECT codigo_red, nombre_completo FROM redes_fe_y_alegria", conn)
        mapa_redes = df_redes.set_index('nombre_completo')['codigo_red'].to_dict()
        
        df_procesado['codigo_red'] = df_procesado['nombre_rer'].map(mapa_redes)
        
        vinculados = df_procesado['codigo_red'].notna().sum()
        print(f"✅ Vinculación con redes completada: {vinculados} de {len(df_procesado)} filas vinculadas.")

    except Exception as e:
        print(f"❌ Error durante la vinculación con la tabla de redes: {e}")
        df_procesado['codigo_red'] = None # Asegurarse que la columna exista
    
    # 5. Guardar en la base de datos
    try:
        print(f"💾 Guardando {len(df_procesado)} registros en la tabla '{NUEVA_TABLA}'...")
        df_procesado.to_sql(NUEVA_TABLA, conn, if_exists='replace', index=False, index_label='id')
        
        # Crear índices para optimizar consultas
        cursor = conn.cursor()
        cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{NUEVA_TABLA}_codigo_red ON {NUEVA_TABLA}(codigo_red)")
        cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{NUEVA_TABLA}_año ON {NUEVA_TABLA}(año)")
        conn.commit()

        print("\n--- REPORTE FINAL ---")
        print(f"✅ Tabla '{NUEVA_TABLA}' creada/reemplazada exitosamente.")
        print(f"   - Total de filas insertadas: {len(df_procesado)}")
        
        no_vinculados = df_procesado['codigo_red'].isna().sum()
        if no_vinculados > 0:
            print(f"   - Filas no vinculadas a una red: {no_vinculados}")
        else:
            print("   - Todas las filas fueron vinculadas a una red exitosamente.")

    except Exception as e:
        print(f"❌ Error al guardar en la base de datos: {e}")
    finally:
        conn.close()

    print("\n" + "=" * 80)
    print("✅ PROCESO DE IMPORTACIÓN FINALIZADO.")
    print("=" * 80)

if __name__ == "__main__":
    importar_competencias_digitales()