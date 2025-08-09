#!/usr/bin/env python3
"""
Creador de Tabla Redes Fe y Alegría - Proyecto Reasis
Crea tabla redes_fe_y_alegria y vincula con instituciones_educativas
"""

import pandas as pd
import sqlite3

def crear_tabla_redes():
    """Crear tabla redes_fe_y_alegria con datos proporcionados"""
    print("CREANDO TABLA REDES FE Y ALEGRÍA")
    print("=" * 50)
    
    conn = sqlite3.connect('reasis_database.db')
    
    # Eliminar tabla anterior si existe
    conn.execute('DROP TABLE IF EXISTS redes_fe_y_alegria')
    
    # Crear nueva tabla
    create_sql = """
    CREATE TABLE redes_fe_y_alegria (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo_red TEXT NOT NULL UNIQUE,           -- RER FA 44, RER FA 47, etc.
        nombre_completo TEXT NOT NULL,             -- RER Fe y Alegría 44 - Cusco
        numero_region TEXT NOT NULL,               -- 44. Cusco, 47. Loreto
        lugar TEXT NOT NULL,                       -- Cusco, Iquitos, Malingas
        ambito TEXT NOT NULL,                      -- Rural (todos son Rural)
        red_lugar TEXT NOT NULL,                   -- RER FA 44 CUSCO
        fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
    
    conn.execute(create_sql)
    
    # Datos de las redes
    redes_data = [
        {
            'codigo_red': 'RER FA 44',
            'nombre_completo': 'RER Fe y Alegría 44 - Cusco',
            'numero_region': '44. Cusco',
            'lugar': 'Cusco',
            'ambito': 'Rural',
            'red_lugar': 'RER FA 44 CUSCO'
        },
        {
            'codigo_red': 'RER FA 47',
            'nombre_completo': 'RER Fe y Alegría 47 - Iquitos',
            'numero_region': '47. Loreto',
            'lugar': 'Iquitos',
            'ambito': 'Rural',
            'red_lugar': 'RER FA 47 IQUITOS'
        },
        {
            'codigo_red': 'RER FA 48',
            'nombre_completo': 'RER Fe y Alegría 48 - Malingas',
            'numero_region': '48. Piura',
            'lugar': 'Malingas',
            'ambito': 'Rural',
            'red_lugar': 'RER FA 48 MALINGAS'
        },
        {
            'codigo_red': 'RER FA 54',
            'nombre_completo': 'RER Fe y Alegría 54 - Moro',
            'numero_region': '54. Ancash',
            'lugar': 'Moro',
            'ambito': 'Rural',
            'red_lugar': 'RER FA 54 MORO'
        },
        {
            'codigo_red': 'RER FA 72',
            'nombre_completo': 'RER Fe y Alegría 72 - Pucallpa',
            'numero_region': '72. Ucayali',
            'lugar': 'Pucallpa',
            'ambito': 'Rural',
            'red_lugar': 'RER FA 72 PUCALLPA'
        },
        {
            'codigo_red': 'RER FA 79',
            'nombre_completo': 'RER Fe y Alegría 79 - Acobamba',
            'numero_region': '79. Huancavelica',
            'lugar': 'Acobamba',
            'ambito': 'Rural',
            'red_lugar': 'RER FA 79 ACOBAMBA'
        }
    ]
    
    # Insertar datos
    df_redes = pd.DataFrame(redes_data)
    df_redes.to_sql('redes_fe_y_alegria', conn, if_exists='append', index=False)
    
    print(f"- Tabla redes_fe_y_alegria creada exitosamente")
    print(f"- {len(redes_data)} redes insertadas")
    
    # Mostrar datos insertados
    redes_insertadas = pd.read_sql_query('SELECT * FROM redes_fe_y_alegria ORDER BY codigo_red', conn)
    print(f"\nRedes Fe y Alegría creadas:")
    print("-" * 60)
    print(redes_insertadas[['codigo_red', 'nombre_completo', 'lugar']].to_string(index=False))
    
    conn.commit()
    conn.close()
    
    return len(redes_data)

def agregar_columna_red_instituciones():
    """Agregar columna codigo_red a tabla instituciones_educativas"""
    print(f"\nAGREGANDO COLUMNA RED A INSTITUCIONES")
    print("=" * 50)
    
    conn = sqlite3.connect('reasis_database.db')
    
    # Verificar si la columna ya existe
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(instituciones_educativas)")
    columnas_existentes = [col[1] for col in cursor.fetchall()]
    
    if 'codigo_red' not in columnas_existentes:
        # Agregar columna
        conn.execute('ALTER TABLE instituciones_educativas ADD COLUMN codigo_red TEXT')
        print("- Columna codigo_red agregada a instituciones_educativas")
        
        # Crear índice para optimización
        conn.execute('CREATE INDEX idx_instituciones_codigo_red ON instituciones_educativas(codigo_red)')
        print("- Indice creado para codigo_red")
    else:
        print("- Columna codigo_red ya existe en instituciones_educativas")
    
    conn.commit()
    conn.close()

def vincular_instituciones_con_redes():
    """Vincular instituciones educativas con sus redes usando los datos docentes"""
    print(f"\nVINCULANDO INSTITUCIONES CON REDES")
    print("=" * 50)
    
    conn = sqlite3.connect('reasis_database.db')
    
    # Obtener mapeo de códigos modulares a RER desde datos docentes
    mapeo_rer = pd.read_sql_query('''
        SELECT DISTINCT 
            codigo_modular_actual as codigo_modular,
            rer,
            COUNT(*) as docentes_count
        FROM docentes_data 
        WHERE codigo_modular_actual IS NOT NULL 
        AND rer IS NOT NULL
        AND codigo_modular_actual IN (
            SELECT DISTINCT codigo_modular 
            FROM instituciones_educativas 
            WHERE codigo_modular IS NOT NULL
        )
        GROUP BY codigo_modular_actual, rer
        ORDER BY codigo_modular_actual, docentes_count DESC
    ''', conn)
    
    print(f"Códigos modulares con RER identificados: {len(mapeo_rer)}")
    
    # Actualizar instituciones con su código de red
    actualizaciones_exitosas = 0
    
    cursor = conn.cursor()
    
    for _, row in mapeo_rer.iterrows():
        codigo_modular = row['codigo_modular']
        rer_numero = str(row['rer']).strip()
        
        # Mapear número RER a código de red
        codigo_red = None
        if rer_numero == '44':
            codigo_red = 'RER FA 44'
        elif rer_numero == '47':
            codigo_red = 'RER FA 47'
        elif rer_numero == '48':
            codigo_red = 'RER FA 48'
        elif rer_numero == '54':
            codigo_red = 'RER FA 54'
        elif rer_numero == '72':
            codigo_red = 'RER FA 72'
        elif rer_numero == '79':
            codigo_red = 'RER FA 79'
        
        if codigo_red:
            # Actualizar institución
            cursor.execute('''
                UPDATE instituciones_educativas 
                SET codigo_red = ?
                WHERE codigo_modular = ?
            ''', [codigo_red, codigo_modular])
            
            if cursor.rowcount > 0:
                actualizaciones_exitosas += 1
    
    conn.commit()
    
    print(f"- {actualizaciones_exitosas} instituciones vinculadas con redes")
    
    # Verificar resultado
    resultado_vinculacion = pd.read_sql_query('''
        SELECT 
            ie.codigo_red,
            r.nombre_completo,
            r.lugar,
            COUNT(*) as instituciones_vinculadas
        FROM instituciones_educativas ie
        INNER JOIN redes_fe_y_alegria r ON ie.codigo_red = r.codigo_red
        GROUP BY ie.codigo_red, r.nombre_completo, r.lugar
        ORDER BY instituciones_vinculadas DESC
    ''', conn)
    
    print(f"\nRESULTADO DE VINCULACIÓN:")
    print("-" * 60)
    print(resultado_vinculacion.to_string(index=False))
    
    # Estadísticas generales
    total_instituciones = pd.read_sql_query('SELECT COUNT(*) as count FROM instituciones_educativas', conn).iloc[0, 0]
    vinculadas_red = pd.read_sql_query('SELECT COUNT(*) as count FROM instituciones_educativas WHERE codigo_red IS NOT NULL', conn).iloc[0, 0]
    
    print(f"\nESTADÍSTICAS DE VINCULACIÓN:")
    print(f"Total instituciones: {total_instituciones}")
    print(f"Vinculadas con red: {vinculadas_red}")
    print(f"Porcentaje vinculado: {vinculadas_red/total_instituciones*100:.1f}%")
    
    conn.close()
    
    return actualizaciones_exitosas

def verificar_consistencia_datos():
    """Verificar consistencia entre datos docentes y vinculación de redes"""
    print(f"\nVERIFICANDO CONSISTENCIA DE DATOS")
    print("=" * 50)
    
    conn = sqlite3.connect('reasis_database.db')
    
    # Verificar que docentes y instituciones coincidan en RER
    consistencia = pd.read_sql_query('''
        SELECT 
            d.rer as rer_docente,
            ie.codigo_red as red_institucion,
            r.lugar,
            COUNT(*) as registros
        FROM docentes_data d
        INNER JOIN instituciones_educativas ie ON d.codigo_modular_vinculado = ie.codigo_modular
        LEFT JOIN redes_fe_y_alegria r ON ie.codigo_red = r.codigo_red
        WHERE d.rer IS NOT NULL
        GROUP BY d.rer, ie.codigo_red, r.lugar
        ORDER BY registros DESC
    ''', conn)
    
    print("Consistencia RER docentes vs Red instituciones:")
    print(consistencia.to_string(index=False))
    
    # Verificar docentes sin institución vinculada
    sin_vincular = pd.read_sql_query('''
        SELECT 
            rer,
            COUNT(*) as docentes_sin_vincular
        FROM docentes_data
        WHERE codigo_modular_vinculado IS NULL
        GROUP BY rer
        ORDER BY docentes_sin_vincular DESC
    ''', conn)
    
    if len(sin_vincular) > 0:
        print(f"\nDocentes sin vinculación institucional:")
        print(sin_vincular.to_string(index=False))
    
    conn.close()

def generar_reporte_redes():
    """Generar reporte final de la estructura de redes"""
    print(f"\nREPORTE FINAL - ESTRUCTURA DE REDES")
    print("=" * 60)
    
    conn = sqlite3.connect('reasis_database.db')
    
    # Reporte completo por red
    reporte_completo = pd.read_sql_query('''
        SELECT 
            r.codigo_red,
            r.nombre_completo,
            r.lugar,
            COUNT(DISTINCT ie.codigo_modular) as instituciones_educativas,
            COUNT(DISTINCT d.dni) as docentes_unicos,
            COUNT(d.dni) as total_registros_docentes
        FROM redes_fe_y_alegria r
        LEFT JOIN instituciones_educativas ie ON r.codigo_red = ie.codigo_red
        LEFT JOIN docentes_data d ON ie.codigo_modular = d.codigo_modular_vinculado
        GROUP BY r.codigo_red, r.nombre_completo, r.lugar
        ORDER BY docentes_unicos DESC, instituciones_educativas DESC
    ''', conn)
    
    print("Reporte por Red Educativa Rural:")
    print(reporte_completo.to_string(index=False))
    
    # Totales
    totales = pd.read_sql_query('''
        SELECT 
            COUNT(DISTINCT r.codigo_red) as total_redes,
            COUNT(DISTINCT ie.codigo_modular) as instituciones_vinculadas,
            COUNT(DISTINCT d.dni) as docentes_vinculados_red
        FROM redes_fe_y_alegria r
        LEFT JOIN instituciones_educativas ie ON r.codigo_red = ie.codigo_red
        LEFT JOIN docentes_data d ON ie.codigo_modular = d.codigo_modular_vinculado
    ''', conn).iloc[0]
    
    print(f"\nTOTALES:")
    print(f"Redes Fe y Alegría: {totales['total_redes']}")
    print(f"Instituciones vinculadas: {totales['instituciones_vinculadas']}")
    print(f"Docentes con red identificada: {totales['docentes_vinculados_red']}")
    
    conn.close()
    
    return reporte_completo

def main():
    """Función principal"""
    print("CREADOR DE ESTRUCTURA DE REDES FE Y ALEGRÍA")
    print("=" * 70)
    
    # Paso 1: Crear tabla de redes
    redes_creadas = crear_tabla_redes()
    
    # Paso 2: Agregar columna a instituciones
    agregar_columna_red_instituciones()
    
    # Paso 3: Vincular instituciones con redes
    vinculaciones = vincular_instituciones_con_redes()
    
    # Paso 4: Verificar consistencia
    verificar_consistencia_datos()
    
    # Paso 5: Generar reporte final
    reporte = generar_reporte_redes()
    
    print(f"\n{'='*70}")
    print("ESTRUCTURA DE REDES FE Y ALEGRÍA COMPLETADA")
    print(f"- {redes_creadas} redes creadas")
    print(f"- {vinculaciones} instituciones vinculadas")
    print(f"- Estructura lista para analisis por RER")
    print("="*70)
    
    return {
        'redes_creadas': redes_creadas,
        'vinculaciones': vinculaciones,
        'reporte': reporte
    }

if __name__ == "__main__":
    main()