#!/usr/bin/env python3
"""
Script para integrar variables contextuales aprobadas a indices_metodologicos
con codificación numérica lógica
"""

import sqlite3
import pandas as pd

def integrar_variables_contextuales():
    """
    Integra variables contextuales con codificación numérica
    """
    
    print("=== INTEGRACION VARIABLES CONTEXTUALES ===\n")
    
    conn = sqlite3.connect('reasis_database.db')
    cursor = conn.cursor()
    
    # 1. Crear backup antes de modificar
    print("1. CREANDO BACKUP DE SEGURIDAD...")
    df_backup = pd.read_sql_query("SELECT * FROM indices_metodologicos", conn)
    backup_filename = "backup_indices_antes_variables_contextuales.csv"
    df_backup.to_csv(backup_filename, index=False, encoding='utf-8')
    print(f"   [OK] Backup creado: {backup_filename}")
    print(f"   [OK] {len(df_backup)} registros respaldados")
    
    # 2. Cargar datos de ambas tablas
    df_indices = pd.read_sql_query("SELECT * FROM indices_metodologicos", conn)
    df_instituciones = pd.read_sql_query("SELECT * FROM instituciones_educativas", conn)
    
    print(f"\n2. DATOS CARGADOS:")
    print(f"   indices_metodologicos: {len(df_indices)} registros")
    print(f"   instituciones_educativas: {len(df_instituciones)} registros")
    
    # 3. Definir variables a integrar con codificación
    variables_integracion = {
        'nivel_educativo': {
            'nombre_final': 'X14_NIVEL_EDUCATIVO',
            'codificacion': {
                'Inicial - Programa no escolarizado': 1,
                'Inicial - Jardín': 2,
                'Inicial - Cuna-jardín': 3,
                'Primaria': 4,
                'Secundaria': 5,
                'Básica Alternativa-Inicial e Intermedio': 6,
                'Básica Alternativa-Avanzado': 7,
                'Técnico Productiva': 8,
                'Instituto Superior Tecnológico': 9,
                'Instituto Superior Tecnologico': 9  # Variante sin tilde
            }
        },
        'modalidad': {
            'nombre_final': 'X16_MODALIDAD',
            'codificacion': {
                'No escolarizada': 1,
                'Escolarizada': 2,
                'No aplica': 2
            },
            'null_value': 2  # NULL = Escolarizada
        },
        'gestion': {
            'nombre_final': 'X17_GESTION',
            'codificacion': {
                'Pública de gestión directa': 1,
                'Pública de gestión privada': 2,
                'Privada': 3
            }
        },
        'turno': {
            'nombre_final': 'X18_TURNO',
            'codificacion': {
                'Mañana': 1,
                'Manana': 1,  # Sin tilde
                'Tarde': 2,
                'Noche': 3,
                'Mañana-Tarde': 4,
                'Manana-Tarde': 4,  # Sin tilde
                'Tarde-Noche': 5,
                'Mañana-Tarde-Noche': 6,
                'Manana-Noche': 7
            }
        },
        'codigo_carrera': {
            'nombre_final': 'X19_ORGANIZACION_PEDAGOGICA',
            'codificacion': {
                'No aplica': 0,
                'Unidocente multigrado': 1,
                'Polidocente multigrado': 2,
                'Polidocente Completo': 3
            }
        },
        'directivos_total': {
            'nombre_final': 'X20_DIRECTIVOS_TOTAL',
            'tipo': 'numerico'  # Mantener valores numéricos
        },
        'multiplicidad1': {
            'nombre_final': 'X21_MULTIPLICIDAD1',
            'tipo': 'numerico'
        },
        'multiplicidad2': {
            'nombre_final': 'X22_MULTIPLICIDAD2',
            'tipo': 'numerico'
        },
        'grupo_pobreza_monetaria_distrito': {
            'nombre_final': 'X23_POBREZA_DISTRITO',
            'tipo': 'numerico'  # Es un ranking de grupos de pobreza
        }
    }
    
    print(f"\n3. PROCESANDO VARIABLES PARA INTEGRACION:")
    
    # 4. Preparar DataFrame merged
    df_merged = df_indices.merge(
        df_instituciones[['codigo_modular'] + list(variables_integracion.keys())],
        left_on='CODIGO_MODULAR',
        right_on='codigo_modular',
        how='left'
    )
    
    # 5. Aplicar codificaciones y crear nuevas columnas
    for var_original, config in variables_integracion.items():
        nombre_final = config['nombre_final']
        print(f"\n   Procesando {var_original} -> {nombre_final}")
        
        if config.get('tipo') == 'numerico':
            # Mantener valores numéricos, manejar NULLs
            df_merged[nombre_final] = df_merged[var_original].astype(float)
            nulls_count = df_merged[nombre_final].isna().sum()
            print(f"     [NUMERICO] {len(df_merged) - nulls_count} valores, {nulls_count} NULLs")
            
        else:
            # Aplicar codificación categórica
            codificacion = config['codificacion']
            df_merged[nombre_final] = df_merged[var_original].map(codificacion)
            
            # Manejar NULLs si hay valor por defecto
            if 'null_value' in config:
                null_value = config['null_value']
                df_merged[nombre_final] = df_merged[nombre_final].fillna(null_value)
                print(f"     [CATEGORICO] NULLs asignados a valor {null_value}")
            
            # Estadísticas de codificación
            valores_originales = df_merged[var_original].value_counts()
            valores_codificados = df_merged[nombre_final].value_counts()
            
            print(f"     [CATEGORICO] Codificación aplicada:")
            for valor_orig, codigo in codificacion.items():
                count_orig = valores_originales.get(valor_orig, 0)
                if count_orig > 0:
                    print(f"       '{valor_orig}' -> {codigo}: {count_orig} instituciones")
            
            nulls_finales = df_merged[nombre_final].isna().sum()
            if nulls_finales > 0:
                print(f"     [ATENCION] {nulls_finales} valores no pudieron ser codificados")
    
    # 6. Preparar DataFrame final para actualizar tabla
    columnas_nuevas = [config['nombre_final'] for config in variables_integracion.values()]
    df_final = df_merged[['CODIGO_MODULAR'] + columnas_nuevas].copy()
    
    print(f"\n4. INTEGRANDO A BASE DE DATOS:")
    print(f"   Nuevas columnas a agregar: {len(columnas_nuevas)}")
    
    # 7. Agregar columnas a la tabla existente
    for columna in columnas_nuevas:
        try:
            alter_query = f"ALTER TABLE indices_metodologicos ADD COLUMN {columna} REAL"
            cursor.execute(alter_query)
            print(f"   [OK] Columna {columna} agregada")
        except sqlite3.Error as e:
            if "duplicate column name" in str(e).lower():
                print(f"   [EXISTE] Columna {columna} ya existe")
            else:
                print(f"   [ERROR] No se pudo agregar {columna}: {str(e)}")
    
    # 8. Actualizar valores en la tabla
    print(f"\n5. ACTUALIZANDO VALORES EN LA TABLA:")
    
    actualizaciones_exitosas = 0
    actualizaciones_fallidas = 0
    
    for _, row in df_final.iterrows():
        codigo_modular = row['CODIGO_MODULAR']
        
        # Construir query de actualización
        set_clauses = []
        values = []
        
        for columna in columnas_nuevas:
            valor = row[columna]
            if pd.notna(valor):  # Solo actualizar valores no nulos
                set_clauses.append(f"{columna} = ?")
                values.append(float(valor))
        
        if set_clauses:  # Solo ejecutar si hay algo que actualizar
            update_query = f"""
            UPDATE indices_metodologicos 
            SET {', '.join(set_clauses)}
            WHERE CODIGO_MODULAR = ?
            """
            values.append(codigo_modular)
            
            try:
                cursor.execute(update_query, values)
                actualizaciones_exitosas += 1
            except sqlite3.Error as e:
                actualizaciones_fallidas += 1
                if actualizaciones_fallidas <= 3:  # Solo mostrar primeros errores
                    print(f"   [ERROR] Institución {codigo_modular}: {str(e)}")
    
    print(f"   [RESULTADO] {actualizaciones_exitosas} instituciones actualizadas exitosamente")
    print(f"   [RESULTADO] {actualizaciones_fallidas} instituciones con errores")
    
    # 9. Verificar resultados finales
    print(f"\n6. VERIFICACION FINAL:")
    
    cursor.execute('PRAGMA table_info(indices_metodologicos)')
    columns_after = cursor.fetchall()
    print(f"   Total columnas después: {len(columns_after)}")
    
    # Verificar completitud de nuevas variables
    for columna in columnas_nuevas:
        cursor.execute(f"""
        SELECT 
            COUNT(*) as total,
            COUNT({columna}) as con_datos,
            COUNT(*) - COUNT({columna}) as nulls
        FROM indices_metodologicos
        """)
        stats = cursor.fetchone()
        completitud = (stats[1] / stats[0]) * 100 if stats[0] > 0 else 0
        print(f"   {columna}: {stats[1]}/{stats[0]} registros ({completitud:.1f}% completitud)")
    
    # Commit cambios
    conn.commit()
    conn.close()
    
    print(f"\n[EXITO] Variables contextuales integradas exitosamente")
    print(f"Base de datos actualizada con {len(columnas_nuevas)} nuevas variables")
    
    return True

if __name__ == "__main__":
    resultado = integrar_variables_contextuales()
    
    if resultado:
        print(f"\n=== INTEGRACION COMPLETADA ===")
        print(f"Variables contextuales agregadas a indices_metodologicos")
        print(f"Listo para clustering K-Means optimizado")
    else:
        print(f"\n=== INTEGRACION CON PROBLEMAS ===")
        print(f"Revisar errores reportados arriba")