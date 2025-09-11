#!/usr/bin/env python3
"""
Paso 1: Creación y Vinculación de Redes Fe y Alegría - Proyecto Reasis
Crea la tabla de redes, la vincula con instituciones y genera un reporte.
"""

import pandas as pd
import sqlite3

DB_PATH = 'reasis_database.db'

def crear_tabla_redes():
    """Crear tabla redes_fe_y_alegria con datos de las 6 redes"""
    print("PASO 1.1: Creando tabla 'redes_fe_y_alegria'...")
    conn = sqlite3.connect(DB_PATH)
    conn.execute('DROP TABLE IF EXISTS redes_fe_y_alegria')
    
    create_sql = """
    CREATE TABLE redes_fe_y_alegria (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo_red TEXT NOT NULL UNIQUE,
        nombre_completo TEXT NOT NULL,
        numero_region TEXT NOT NULL,
        lugar TEXT NOT NULL,
        ambito TEXT NOT NULL,
        red_lugar TEXT NOT NULL
    )
    """
    conn.execute(create_sql)
    
    redes_data = [
        {'codigo_red': 'RER FA 44', 'nombre_completo': 'RER Fe y Alegría 44 - Cusco', 'numero_region': '44. Cusco', 'lugar': 'Cusco', 'ambito': 'Rural', 'red_lugar': 'RER FA 44 CUSCO'},
        {'codigo_red': 'RER FA 47', 'nombre_completo': 'RER Fe y Alegría 47 - Iquitos', 'numero_region': '47. Loreto', 'lugar': 'Iquitos', 'ambito': 'Rural', 'red_lugar': 'RER FA 47 IQUITOS'},
        {'codigo_red': 'RER FA 48', 'nombre_completo': 'RER Fe y Alegría 48 - Malingas', 'numero_region': '48. Piura', 'lugar': 'Malingas', 'ambito': 'Rural', 'red_lugar': 'RER FA 48 MALINGAS'},
        {'codigo_red': 'RER FA 54', 'nombre_completo': 'RER Fe y Alegría 54 - Moro', 'numero_region': '54. Ancash', 'lugar': 'Moro', 'ambito': 'Rural', 'red_lugar': 'RER FA 54 MORO'},
        {'codigo_red': 'RER FA 72', 'nombre_completo': 'RER Fe y Alegría 72 - Pucallpa', 'numero_region': '72. Ucayali', 'lugar': 'Pucallpa', 'ambito': 'Rural', 'red_lugar': 'RER FA 72 PUCALLPA'},
        {'codigo_red': 'RER FA 79', 'nombre_completo': 'RER Fe y Alegría 79 - Acobamba', 'numero_region': '79. Huancavelica', 'lugar': 'Acobamba', 'ambito': 'Rural', 'red_lugar': 'RER FA 79 ACOBAMBA'}
    ]
    
    df_redes = pd.DataFrame(redes_data)
    df_redes.to_sql('redes_fe_y_alegria', conn, if_exists='append', index=False)
    
    print(f"  ✅ Tabla creada y poblada con {len(redes_data)} redes.")
    conn.commit()
    conn.close()

def agregar_columna_red_instituciones():
    """Agregar columna codigo_red a tabla instituciones_educativas"""
    print("\nPASO 1.2: Agregando columna 'codigo_red' a 'instituciones_educativas'...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("ALTER TABLE instituciones_educativas ADD COLUMN codigo_red TEXT")
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_instituciones_codigo_red ON instituciones_educativas(codigo_red)')
        print("  ✅ Columna 'codigo_red' y su índice agregados.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("  ⚠️ La columna 'codigo_red' ya existe. No se realizan cambios.")
        else:
            raise e
            
    conn.commit()
    conn.close()

def vincular_instituciones_con_redes():
    """Vincular instituciones con sus redes usando los datos de los docentes como puente"""
    print("\nPASO 1.3: Vinculando instituciones con redes usando 'docentes_data'...")
    conn = sqlite3.connect(DB_PATH)
    
    mapeo_rer = pd.read_sql_query('''
        SELECT DISTINCT 
            codigo_modular_vinculado as codigo_modular,
            rer
        FROM docentes_data 
        WHERE codigo_modular_vinculado IS NOT NULL AND rer IS NOT NULL
    ''', conn)
    
    print(f"  Se encontraron {len(mapeo_rer)} mapeos únicos de Institución-RER en los datos de docentes.")
    
    actualizaciones_exitosas = 0
    cursor = conn.cursor()
    
    for _, row in mapeo_rer.iterrows():
        codigo_modular = row['codigo_modular']
        rer_numero = str(row['rer']).strip()
        
        codigo_red = f'RER FA {rer_numero}'
        
        cursor.execute('''
            UPDATE instituciones_educativas 
            SET codigo_red = ?
            WHERE codigo_modular = ?
        ''', (codigo_red, codigo_modular))
        
        if cursor.rowcount > 0:
            actualizaciones_exitosas += cursor.rowcount
    
    conn.commit()
    print(f"  ✅ {actualizaciones_exitosas} registros de instituciones fueron vinculados con una red.")
    
    # Verificar resultado
    resultado_vinculacion = pd.read_sql_query('''
        SELECT 
            r.nombre_completo,
            COUNT(ie.codigo_modular) as instituciones_vinculadas
        FROM redes_fe_y_alegria r
        LEFT JOIN instituciones_educativas ie ON r.codigo_red = ie.codigo_red
        GROUP BY r.nombre_completo
        ORDER BY instituciones_vinculadas DESC
    ''', conn)
    
    print("\n--- REPORTE DE VINCULACIÓN ---")
    print(resultado_vinculacion.to_string(index=False))
    
    total_instituciones = pd.read_sql_query('SELECT COUNT(*) as count FROM instituciones_educativas', conn).iloc[0, 0]
    vinculadas_red = pd.read_sql_query('SELECT COUNT(*) as count FROM instituciones_educativas WHERE codigo_red IS NOT NULL', conn).iloc[0, 0]
    
    print(f"\nTotal de instituciones en la BD: {total_instituciones}")
    print(f"Total de instituciones vinculadas a una red: {vinculadas_red}")
    if total_instituciones > 0:
        print(f"Porcentaje de cobertura: {vinculadas_red/total_instituciones*100:.1f}%")
    
    conn.close()
    return vinculadas_red

def main():
    """Función principal para ejecutar todo el proceso del Paso 1."""
    print("--- INICIANDO PASO 1: CREACIÓN Y VINCULACIÓN DE REDES ---")
    print("=" * 60)
    
    try:
        crear_tabla_redes()
        agregar_columna_red_instituciones()
        vinculadas = vincular_instituciones_con_redes()
        
        print("\n" + "=" * 60)
        if vinculadas > 0:
            print("✅ PASO 1 COMPLETADO EXITOSAMENTE.")
            print("La tabla 'instituciones_educativas' ha sido enriquecida con los códigos de red.")
        else:
            print("⚠️ PASO 1 COMPLETADO, PERO NO SE LOGRARON VINCULACIONES.")
            print("Revisa que la tabla 'docentes_data' tenga datos en 'codigo_modular_vinculado' y 'rer'.")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Ocurrió un error en el Paso 1: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()