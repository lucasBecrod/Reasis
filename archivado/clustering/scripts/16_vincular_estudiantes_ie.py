#!/usr/bin/env python3
"""
Paso 16: Vinculador de Estudiantes a Instituciones - Proyecto Reasis
Añade y puebla la columna 'codigo_modular_vinculado' en la tabla
'competencia_digital_estudiantes'.
"""

import sqlite3

DB_PATH = 'reasis_database.db'

def agregar_columna_vinculacion():
    """Añade la columna para la clave foránea si no existe."""
    print("--- 1. Preparando la tabla de estudiantes ---")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE competencia_digital_estudiantes ADD COLUMN codigo_modular_vinculado TEXT")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_estudiantes_vinculado ON competencia_digital_estudiantes(codigo_modular_vinculado)")
        print("✅ Columna 'codigo_modular_vinculado' y su índice agregados.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("⚠️ La columna 'codigo_modular_vinculado' ya existe.")
        else:
            raise e
    finally:
        conn.close()

def ejecutar_vinculacion():
    """Ejecuta la consulta de actualización para vincular los registros."""
    print("\n--- 2. Ejecutando vinculación masiva ---")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Esta consulta compleja realiza la vinculación en un solo paso
    update_query = """
    UPDATE competencia_digital_estudiantes
    SET codigo_modular_vinculado = (
        SELECT ie.codigo_modular
        FROM instituciones_educativas AS ie
        WHERE
            -- Condición 1: El 'codigo_local' de la institución coincide con la parte numérica del 'codigo_local' del estudiante.
            -- SUBSTR extrae la parte del string antes del primer espacio.
            -- Se añade ' ' para que INSTR siempre encuentre un espacio.
            TRIM(CAST(ie.codigo_local AS TEXT)) = SUBSTR(TRIM(competencia_digital_estudiantes.codigo_local), 1, INSTR(TRIM(competencia_digital_estudiantes.codigo_local) || ' ', ' ') - 1)
            AND
            -- Condición 2: El 'nivel' del estudiante está contenido en el 'nivel_educativo' de la institución
            INSTR(UPPER(ie.nivel_educativo), UPPER(competencia_digital_estudiantes.nivel)) > 0
        -- Nos aseguramos de tomar solo un resultado si hubiera múltiples coincidencias
        LIMIT 1
    )
    WHERE competencia_digital_estudiantes.codigo_local IS NOT NULL AND competencia_digital_estudiantes.codigo_local != '';
    """

    try:
        cursor.execute(update_query)
        conn.commit()
        print(f"✅ Consulta de actualización ejecutada. {cursor.rowcount} filas potencialmente afectadas.")

        # 3. Generar reporte de resultados
        print("\n--- 3. Reporte de Vinculación ---")
        total_registros = cursor.execute("SELECT COUNT(*) FROM competencia_digital_estudiantes").fetchone()[0]
        vinculados = cursor.execute("SELECT COUNT(*) FROM competencia_digital_estudiantes WHERE codigo_modular_vinculado IS NOT NULL").fetchone()[0]
        tasa_exito = (vinculados / total_registros) * 100 if total_registros > 0 else 0

        print(f"Total de registros de estudiantes: {total_registros}")
        print(f"Registros vinculados a una institución: {vinculados}")
        print(f"Tasa de vinculación final: {tasa_exito:.1f}%")

    except Exception as e:
        print(f"❌ Error durante la ejecución de la consulta de vinculación: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    agregar_columna_vinculacion()
    ejecutar_vinculacion()
    print("\n" + "="*40 + "\n✅ Proceso de vinculación finalizado.\n" + "="*40)