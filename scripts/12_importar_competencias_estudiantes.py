#!/usr/bin/env python3
"""
Paso 12: Importador de Competencias Digitales de Estudiantes - Proyecto Reasis
Crea y puebla la tabla 'competencia_digital_estudiantes' desde el archivo Excel.
"""

import pandas as pd
import sqlite3
from pathlib import Path

# --- CONFIGURACIÓN ---
DB_PATH = 'reasis_database.db'
EXCEL_PATH = Path("assets/Consultoria/Información actualizada/3. BD Comp Digitales Estudiantes 2024.xlsx")
NUEVA_TABLA = 'competencia_digital_estudiantes'

# Mapeo de niveles a valores numéricos (basado en la exploración)
MAPEO_NIVELES = {
    'Inicio': 1,
    'En proceso': 2,
    'Logrado': 3
    # Si la exploración muestra 'Destacado', se añadirá aquí: 'Destacado': 4
}

def importar_competencias_estudiantes():
    """
    Procesa el archivo Excel de competencias de estudiantes y lo importa a SQL.
    """
    print(f"--- INICIANDO PASO 12: IMPORTACIÓN DE COMPETENCIAS DE ESTUDIANTES A '{NUEVA_TABLA}' ---")
    print("=" * 85)

    # 1. Leer el archivo Excel
    try:
        df = pd.read_excel(EXCEL_PATH, sheet_name='DATA')
        print(f"✅ Archivo Excel leído con {len(df)} filas.")
    except Exception as e:
        print(f"❌ Error fatal al leer el archivo Excel: {e}")
        return

    # 2. Seleccionar y renombrar columnas clave
    columnas_a_usar = {
        'Marca temporal': 'marca_temporal', 'URL Encuesta PDF': 'url_encuesta_pdf', 'RED': 'red_texto',
        'Colegio': 'codigo_local', 'Año': 'año', 'Ambito': 'ambito', 'Grado y nivel': 'grado_nivel_texto',
        'Nivel': 'nivel', 'Grado': 'grado', 'Nombres y apellidos': 'nombre_completo', 'Sexo': 'sexo',
        'Edad': 'edad', '¿Cuentas con internet en casa?': 'tiene_internet_casa',
        '¿Con qué tipo de dispositivo te conectas a Internet desde casa?': 'tipo_dispositivo',
        'Tu Institución Educativa cuenta con Aulas de Innovación': 'ie_tiene_aula_innovacion',
        '¿Cada cuánto tiempo ingresas al aula de Innovación?': 'frecuencia_uso_aula_innovacion',
        '¿Cada cuánto tiempo haces uso de dispositivos (Chromebook) en aula?': 'frecuencia_uso_dispositivos_aula',
        '¿Estudias computación e informática como opción técnica?': 'estudia_opcion_tecnica',
        'Temáticas aprendidas en computación e informática': 'tematicas_aprendidas',
        'NOTA GLOBAL': 'nota_global_texto',
        'COMPETENCIAS DIGITALES': 'competencia_digital_texto',
        'PENSAMIENTO COMPUTACIONAL': 'pensamiento_computacional_texto',
        'CIUDADANÍA DIGITAL': 'ciudadania_digital_texto'
    }
    
    # Filtrar solo las columnas que existen en el DataFrame
    columnas_existentes = {k: v for k, v in columnas_a_usar.items() if k in df.columns}
    df_procesado = df[list(columnas_existentes.keys())].copy()
    df_procesado.rename(columns=columnas_existentes, inplace=True)
    print("✅ Columnas seleccionadas y renombradas.")

    # Normalizar la columna 'nivel' a formato Título (ej: "SECUNDARIA" -> "Secundaria")
    if 'nivel' in df_procesado.columns:
        df_procesado['nivel'] = df_procesado['nivel'].str.title()
        print("✅ Columna 'nivel' normalizada a formato Título.")

    # Unificar 'grado' y 'nivel' en la columna 'grado' y eliminar la redundante 'grado_nivel_texto'
    if 'grado' in df_procesado.columns and 'nivel' in df_procesado.columns:
        # Asegurarse de que no haya valores nulos que rompan la concatenación y limpiar '.0' si son floats
        grado_str = df_procesado['grado'].astype(str).str.replace(r'\.0$', '', regex=True)
        nivel_str = df_procesado['nivel'].fillna('')
        # Sobrescribir la columna 'grado' con el formato unificado
        df_procesado['grado'] = grado_str + ' ' + nivel_str
        print("✅ Columna 'grado' actualizada al formato '4 Secundaria'.")
        # Eliminar la columna 'grado_nivel_texto' para evitar redundancia
        df_procesado.drop(columns=['grado_nivel_texto'], inplace=True)
        print("✅ Columna 'grado_nivel_texto' eliminada para simplificar.")

    # 3. Transformar las dimensiones a valores numéricos
    df_procesado['nota_global_num'] = df_procesado['nota_global_texto'].map(MAPEO_NIVELES)
    df_procesado['competencia_digital_num'] = df_procesado['competencia_digital_texto'].map(MAPEO_NIVELES)
    df_procesado['pensamiento_computacional_num'] = df_procesado['pensamiento_computacional_texto'].map(MAPEO_NIVELES)
    df_procesado['ciudadania_digital_num'] = df_procesado['ciudadania_digital_texto'].map(MAPEO_NIVELES)
    print("✅ Dimensiones de texto convertidas a valores numéricos.")

    # 4. Vincular con la tabla de redes para obtener 'codigo_red'
    conn = sqlite3.connect(DB_PATH)
    try:
        # Usamos 'red_lugar' porque coincide con el formato 'RER FA 44 CUSCO'
        df_redes = pd.read_sql_query("SELECT codigo_red, red_lugar FROM redes_fe_y_alegria", conn)
        mapa_redes = df_redes.set_index('red_lugar')['codigo_red'].to_dict()
        
        df_procesado['codigo_red'] = df_procesado['red_texto'].map(mapa_redes)
        
        vinculados = df_procesado['codigo_red'].notna().sum()
        print(f"✅ Vinculación con redes completada: {vinculados} de {len(df_procesado)} filas vinculadas.")

    except Exception as e:
        print(f"❌ Error durante la vinculación con la tabla de redes: {e}")
        df_procesado['codigo_red'] = None
    
    # 5. Guardar en la base de datos
    try:
        print(f"💾 Guardando {len(df_procesado)} registros en la tabla '{NUEVA_TABLA}'...")
        df_procesado.to_sql(NUEVA_TABLA, conn, if_exists='replace', index=False, index_label='id')
        
        cursor = conn.cursor()
        cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{NUEVA_TABLA}_codigo_red ON {NUEVA_TABLA}(codigo_red)")
        cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{NUEVA_TABLA}_año ON {NUEVA_TABLA}(año)")
        cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{NUEVA_TABLA}_codigo_local ON {NUEVA_TABLA}(codigo_local)")
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

    print("\n" + "=" * 85)
    print("✅ PROCESO DE IMPORTACIÓN FINALIZADO.")
    print("=" * 85)

if __name__ == "__main__":
    importar_competencias_estudiantes()