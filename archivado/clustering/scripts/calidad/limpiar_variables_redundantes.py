#!/usr/bin/env python3
"""
Script para eliminar variables redundantes de la tabla indices_metodologicos
Variables a eliminar:
- X13_TMATRC_CATEGORIA (redundante con X13_TMATRC)
- X13_TMATRC_MANN_KENDALL_P (redundante con X13_TMATRC)
- FECHA_CALCULO (columna administrativa innecesaria)
"""

import sqlite3
import pandas as pd

def limpiar_variables_redundantes():
    """
    Elimina variables redundantes de la tabla indices_metodologicos
    """
    
    print("=== LIMPIEZA DE VARIABLES REDUNDANTES ===\n")
    
    conn = sqlite3.connect('reasis_database.db')
    cursor = conn.cursor()
    
    # 1. Verificar estructura actual
    cursor.execute('PRAGMA table_info(indices_metodologicos)')
    columns_before = cursor.fetchall()
    print(f"1. ESTRUCTURA ANTES DE LA LIMPIEZA:")
    print(f"   Total columnas: {len(columns_before)}")
    
    variables_a_eliminar = ['X13_TMATRC_CATEGORIA', 'X13_TMATRC_MANN_KENDALL_P', 'FECHA_CALCULO']
    columnas_existentes = [col[1] for col in columns_before]
    
    print(f"\n2. VARIABLES PROGRAMADAS PARA ELIMINACION:")
    for var in variables_a_eliminar:
        if var in columnas_existentes:
            print(f"   [OK] {var} - Encontrada, sera eliminada")
        else:
            print(f"   [ERROR] {var} - No encontrada en la tabla")
    
    # 2. Crear backup de datos antes de modificar
    print(f"\n3. CREANDO BACKUP DE SEGURIDAD...")
    df_backup = pd.read_sql_query("SELECT * FROM indices_metodologicos", conn)
    backup_filename = "backup_indices_metodologicos_antes_limpieza.csv"
    df_backup.to_csv(backup_filename, index=False, encoding='utf-8')
    print(f"   [OK] Backup creado: {backup_filename}")
    print(f"   [OK] {len(df_backup)} registros respaldados")
    
    # 3. Verificar contenido de las variables antes de eliminar
    print(f"\n4. VERIFICACION FINAL VARIABLES A ELIMINAR:")
    
    for var in variables_a_eliminar:
        if var in columnas_existentes:
            try:
                # Estadisticas basicas
                query_stats = f"""
                SELECT 
                    COUNT(*) as total,
                    COUNT({var}) as con_datos,
                    COUNT(*) - COUNT({var}) as nulls
                FROM indices_metodologicos
                """
                stats = cursor.execute(query_stats).fetchone()
                print(f"   {var}:")
                print(f"     Total: {stats[0]}, Con datos: {stats[1]}, NULLs: {stats[2]}")
                
            except Exception as e:
                print(f"     ERROR analizando {var}: {str(e)}")
    
    # 4. Eliminar columnas (SQLite no soporta DROP COLUMN directamente)
    print(f"\n5. ELIMINANDO VARIABLES REDUNDANTES...")
    
    # Obtener lista de columnas a mantener
    columnas_a_mantener = [col[1] for col in columns_before if col[1] not in variables_a_eliminar]
    columnas_select = ', '.join(columnas_a_mantener)
    
    print(f"   Columnas a mantener: {len(columnas_a_mantener)}")
    print(f"   Columnas eliminadas: {len(variables_a_eliminar)}")
    
    try:
        # Crear tabla temporal con estructura limpia
        cursor.execute("DROP TABLE IF EXISTS indices_metodologicos_temp")
        
        # Crear tabla temporal solo con columnas necesarias
        create_temp_query = f"""
        CREATE TABLE indices_metodologicos_temp AS
        SELECT {columnas_select}
        FROM indices_metodologicos
        """
        cursor.execute(create_temp_query)
        
        # Verificar que los datos se copiaron correctamente
        cursor.execute("SELECT COUNT(*) FROM indices_metodologicos_temp")
        temp_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM indices_metodologicos")
        original_count = cursor.fetchone()[0]
        
        if temp_count == original_count:
            print(f"   [OK] Datos copiados correctamente: {temp_count} registros")
            
            # Eliminar tabla original y renombrar temporal
            cursor.execute("DROP TABLE indices_metodologicos")
            cursor.execute("ALTER TABLE indices_metodologicos_temp RENAME TO indices_metodologicos")
            
            print(f"   [OK] Tabla actualizada exitosamente")
            
        else:
            print(f"   [ERROR] Problema en copia: Original {original_count}, Temp {temp_count}")
            raise Exception("Error en copia de datos")
    
    except Exception as e:
        print(f"   [ERROR] Fallo la limpieza: {str(e)}")
        conn.rollback()
        return False
    
    # 6. Verificar resultado final
    cursor.execute('PRAGMA table_info(indices_metodologicos)')
    columns_after = cursor.fetchall()
    
    print(f"\n6. ESTRUCTURA DESPUES DE LA LIMPIEZA:")
    print(f"   Columnas antes: {len(columns_before)}")
    print(f"   Columnas despues: {len(columns_after)}")
    print(f"   Columnas eliminadas: {len(columns_before) - len(columns_after)}")
    
    # Verificar que variables eliminadas ya no existen
    columnas_actuales = [col[1] for col in columns_after]
    variables_eliminadas_confirmadas = []
    variables_no_eliminadas = []
    
    for var in variables_a_eliminar:
        if var not in columnas_actuales:
            variables_eliminadas_confirmadas.append(var)
        else:
            variables_no_eliminadas.append(var)
    
    print(f"\n7. CONFIRMACION DE ELIMINACION:")
    print(f"   [OK] Variables eliminadas exitosamente:")
    for var in variables_eliminadas_confirmadas:
        print(f"        - {var}")
    
    if variables_no_eliminadas:
        print(f"   [ERROR] Variables que NO se pudieron eliminar:")
        for var in variables_no_eliminadas:
            print(f"        - {var}")
    
    # 8. Estadisticas finales
    cursor.execute("SELECT COUNT(*) FROM indices_metodologicos")
    final_count = cursor.fetchone()[0]
    
    print(f"\n8. ESTADISTICAS FINALES:")
    print(f"   Total registros: {final_count}")
    print(f"   Estructura optimizada: {len(columns_after)} columnas")
    print(f"   Reduccion: {len(columns_before) - len(columns_after)} columnas eliminadas")
    print(f"   Porcentaje reduccion: {((len(columns_before) - len(columns_after)) / len(columns_before) * 100):.1f}%")
    
    # Commit y cerrar
    conn.commit()
    conn.close()
    
    if len(variables_eliminadas_confirmadas) == len(variables_a_eliminar):
        print(f"\n[EXITO] Limpieza completada exitosamente")
        return True
    else:
        print(f"\n[ERROR] Limpieza parcialmente exitosa")
        return False

if __name__ == "__main__":
    resultado = limpiar_variables_redundantes()
    
    if resultado:
        print(f"\n=== LIMPIEZA FINALIZADA EXITOSAMENTE ===")
        print(f"Variables redundantes eliminadas correctamente")
        print(f"Tabla indices_metodologicos optimizada")
    else:
        print(f"\n=== LIMPIEZA CON PROBLEMAS ===")
        print(f"Revisar errores reportados arriba")