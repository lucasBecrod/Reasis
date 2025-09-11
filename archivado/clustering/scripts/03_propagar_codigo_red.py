#!/usr/bin/env python3
"""
Paso 3: Propagación de Código de Red - Proyecto Reasis
Añade y puebla la columna 'codigo_red' en las tablas de datos.
"""

import sqlite3

DB_PATH = 'reasis_database.db'

def agregar_y_poblar_columna(tabla, columna_fk, columna_join):
    """Función genérica para añadir y poblar la columna codigo_red."""
    print(f"\nProcesando tabla: '{tabla}'...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Agregar columna si no existe
    try:
        cursor.execute(f"ALTER TABLE {tabla} ADD COLUMN codigo_red TEXT")
        print(f"  ✅ Columna 'codigo_red' agregada a '{tabla}'.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print(f"  ⚠️  La columna 'codigo_red' ya existe en '{tabla}'.")
        else:
            raise e

    # 2. Poblar la columna usando un UPDATE con subconsulta
    print(f"  Poblando 'codigo_red' en '{tabla}'...")
    update_sql = f'''
        UPDATE {tabla}
        SET codigo_red = (
            SELECT ie.codigo_red
            FROM instituciones_educativas ie
            WHERE ie.{columna_join} = {tabla}.{columna_fk}
        )
        WHERE {columna_fk} IS NOT NULL;
    '''
    
    cursor.execute(update_sql)
    registros_actualizados = cursor.rowcount
    conn.commit()
    
    print(f"  ✅ {registros_actualizados} registros fueron actualizados en '{tabla}'.")

    # 3. Verificar la propagación
    total_registros = cursor.execute(f'SELECT COUNT(*) FROM {tabla}').fetchone()[0]
    con_red = cursor.execute(f"SELECT COUNT(*) FROM {tabla} WHERE codigo_red IS NOT NULL").fetchone()[0]
    
    print(f"  Verificación: {con_red} de {total_registros} registros ahora tienen 'codigo_red'.")
    if total_registros > 0:
        print(f"  Cobertura en '{tabla}': {con_red / total_registros * 100:.1f}%")

    conn.close()
    return registros_actualizados

def main():
    """Función principal para ejecutar la propagación a todas las tablas."""
    print("--- INICIANDO PASO 3: PROPAGACIÓN DE CÓDIGO DE RED ---")
    print("=" * 60)
    
    total_actualizados = 0
    
    try:
        # Propagar a resultados_academicos
        # La vinculación es: resultados_academicos.codigo_modular -> instituciones_educativas.codigo_modular
        total_actualizados += agregar_y_poblar_columna(
            tabla='resultados_academicos',
            columna_fk='codigo_modular',
            columna_join='codigo_modular'
        )
        
        # Propagar a docentes_data
        # La vinculación es: docentes_data.codigo_modular_vinculado -> instituciones_educativas.codigo_modular
        total_actualizados += agregar_y_poblar_columna(
            tabla='docentes_data',
            columna_fk='codigo_modular_vinculado',
            columna_join='codigo_modular'
        )
        
        print("\n" + "=" * 60)
        if total_actualizados > 0:
            print("✅ PASO 3 COMPLETADO EXITOSAMENTE.")
            print("Las tablas de datos ahora están enriquecidas con la información de la red.")
        else:
            print("PASO 3 COMPLETADO, pero no se actualizaron registros.")
            print("Esto puede ser normal si ya se había ejecutado antes.")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Ocurrió un error en el Paso 3: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()