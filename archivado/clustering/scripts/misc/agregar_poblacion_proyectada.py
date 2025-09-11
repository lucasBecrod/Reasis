#!/usr/bin/env python3
"""
Script para agregar variable poblacion_proyectada_2024_distrito
y renombrar grupo_pobreza_monetaria_distrito a X24_GPMD
"""

import sqlite3
import pandas as pd

def agregar_poblacion_proyectada():
    """
    Agrega población proyectada y renombra variables según nomenclatura solicitada
    """
    
    print("=== AGREGANDO POBLACION PROYECTADA Y RENOMBRANDO ===\n")
    
    conn = sqlite3.connect('reasis_database.db')
    cursor = conn.cursor()
    
    # 1. Verificar si existe poblacion_proyectada_2024_distrito
    print("1. VERIFICANDO VARIABLE POBLACION PROYECTADA:")
    
    df_instituciones = pd.read_sql_query("SELECT * FROM instituciones_educativas LIMIT 1", conn)
    cols_disponibles = df_instituciones.columns.tolist()
    
    variables_poblacion = [col for col in cols_disponibles if 'poblacion' in col.lower() and '2024' in col]
    print(f"   Variables de población 2024 encontradas: {len(variables_poblacion)}")
    for var in variables_poblacion:
        print(f"   - {var}")
    
    if not variables_poblacion:
        print(f"   [ADVERTENCIA] No se encontró poblacion_proyectada_2024_distrito")
        variables_poblacion_alternativas = [col for col in cols_disponibles if 'poblacion' in col.lower()]
        print(f"   Variables de población alternativas: {variables_poblacion_alternativas}")
    
    # 2. Renombrar X23_POBREZA_DISTRITO a X24_GPMD  
    print(f"\n2. RENOMBRANDO VARIABLES SEGUN NOMENCLATURA:")
    
    try:
        cursor.execute("ALTER TABLE indices_metodologicos RENAME COLUMN X23_POBREZA_DISTRITO TO X24_GPMD")
        print(f"   [OK] X23_POBREZA_DISTRITO -> X24_GPMD")
    except sqlite3.Error as e:
        if "no such column" in str(e).lower():
            print(f"   [INFO] X23_POBREZA_DISTRITO ya podría haberse renombrado")
        else:
            print(f"   [ERROR] No se pudo renombrar: {str(e)}")
    
    # 3. Agregar población proyectada si existe
    if variables_poblacion:
        variable_poblacion = variables_poblacion[0]  # Usar la primera encontrada
        print(f"\n3. AGREGANDO {variable_poblacion} COMO X25_POBLACION_DISTRITO:")
        
        # Cargar datos de población
        df_poblacion = pd.read_sql_query(f"""
        SELECT codigo_modular, {variable_poblacion}
        FROM instituciones_educativas
        WHERE {variable_poblacion} IS NOT NULL
        """, conn)
        
        print(f"   Registros con datos de población: {len(df_poblacion)}")
        
        if len(df_poblacion) > 0:
            # Estadísticas de la variable
            poblacion_stats = df_poblacion[variable_poblacion].describe()
            print(f"   Estadísticas población:")
            print(f"     Min: {poblacion_stats['min']:,.0f} habitantes")
            print(f"     Max: {poblacion_stats['max']:,.0f} habitantes") 
            print(f"     Media: {poblacion_stats['mean']:,.0f} habitantes")
            print(f"     Mediana: {poblacion_stats['50%']:,.0f} habitantes")
            
            # Agregar columna
            try:
                cursor.execute("ALTER TABLE indices_metodologicos ADD COLUMN X25_POBLACION_DISTRITO REAL")
                print(f"   [OK] Columna X25_POBLACION_DISTRITO agregada")
            except sqlite3.Error as e:
                if "duplicate column name" in str(e).lower():
                    print(f"   [EXISTE] Columna X25_POBLACION_DISTRITO ya existe")
                else:
                    print(f"   [ERROR] No se pudo agregar columna: {str(e)}")
            
            # Actualizar valores
            actualizaciones = 0
            for _, row in df_poblacion.iterrows():
                codigo = row['codigo_modular']
                poblacion = row[variable_poblacion]
                
                try:
                    cursor.execute("""
                    UPDATE indices_metodologicos 
                    SET X25_POBLACION_DISTRITO = ?
                    WHERE CODIGO_MODULAR = ?
                    """, (float(poblacion), codigo))
                    actualizaciones += 1
                except sqlite3.Error as e:
                    print(f"   [ERROR] No se pudo actualizar {codigo}: {str(e)}")
            
            print(f"   [RESULTADO] {actualizaciones} instituciones actualizadas con datos de población")
        
        else:
            print(f"   [ADVERTENCIA] No hay datos válidos de población para agregar")
    
    else:
        print(f"\n3. POBLACION PROYECTADA NO DISPONIBLE")
        print(f"   No se pudo agregar X25_POBLACION_DISTRITO")
    
    # 4. Verificar estructura final
    print(f"\n4. VERIFICACION ESTRUCTURA FINAL:")
    
    cursor.execute('PRAGMA table_info(indices_metodologicos)')
    columns_info = cursor.fetchall()
    
    # Buscar variables X24 y X25
    variables_finales = []
    for col_info in columns_info:
        col_name = col_info[1]
        if col_name.startswith('X24') or col_name.startswith('X25'):
            variables_finales.append(col_name)
    
    print(f"   Variables X24-X25 en la tabla:")
    for var in sorted(variables_finales):
        # Estadísticas de completitud
        cursor.execute(f"""
        SELECT 
            COUNT(*) as total,
            COUNT({var}) as con_datos,
            COUNT(*) - COUNT({var}) as nulls
        FROM indices_metodologicos
        """)
        stats = cursor.fetchone()
        completitud = (stats[1] / stats[0]) * 100 if stats[0] > 0 else 0
        print(f"     {var}: {stats[1]}/{stats[0]} ({completitud:.1f}% completitud)")
    
    # 5. Crear documentación para variables
    documentacion = {
        'X24_GPMD': {
            'nombre_completo': 'Grupo Pobreza Monetaria Distrito',
            'descripcion': 'Ranking de grupo de pobreza monetaria del distrito (1=menor pobreza, 22=mayor pobreza)',
            'fuente': 'INEI - Mapa de Pobreza Provincial y Distrital',
            'tipo': 'Numérica ordinal',
            'rango': '4-22',
            'interpretacion': 'Menor valor = menor pobreza distrital'
        }
    }
    
    if variables_poblacion:
        documentacion['X25_POBLACION_DISTRITO'] = {
            'nombre_completo': 'Población Proyectada 2024 Distrito',
            'descripcion': 'Población proyectada del distrito para el año 2024',
            'fuente': 'INEI - Proyecciones Poblacionales',
            'tipo': 'Numérica continua',
            'rango': 'Variable según distrito',
            'interpretacion': 'Número total de habitantes del distrito donde se ubica la institución educativa'
        }
    
    # Commit cambios
    conn.commit()
    conn.close()
    
    print(f"\n[EXITO] Variables agregadas y renombradas exitosamente")
    return documentacion

if __name__ == "__main__":
    doc = agregar_poblacion_proyectada()
    
    print(f"\n=== VARIABLES FINALES AGREGADAS ===")
    for var_code, info in doc.items():
        print(f"{var_code}: {info['nombre_completo']}")
        print(f"  Descripción: {info['descripcion']}")
        print(f"  Tipo: {info['tipo']}")
        print()
    
    print(f"[SIGUIENTE PASO] Documentar en CALCULOS_MATEMATICOS y AGENTS.md")