#!/usr/bin/env python3
"""
Limpiador de tabla indices_metodologicos - Solo Variables del Estudio
1. Identifica todas las columnas actuales
2. Mantiene SOLO: codigo_modular + variables metodológicas Y/X
3. Elimina columnas auxiliares, duplicadas o no metodológicas
4. Crea tabla limpia con estructura definitiva
"""

import sqlite3
import pandas as pd
import os

def main():
    print("=== LIMPIEZA TOTAL TABLA INDICES_METODOLOGICOS ===")
    
    conn = sqlite3.connect('reasis_database.db')
    
    try:
        # 1. Identificar todas las columnas actuales
        print("\n1. IDENTIFICANDO COLUMNAS ACTUALES...")
        
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(indices_metodologicos)")
        columnas_info = cursor.fetchall()
        
        todas_columnas = [col[1] for col in columnas_info]
        print(f"   - Total columnas actuales: {len(todas_columnas)}")
        print(f"   - Columnas: {todas_columnas}")
        
        # 2. Definir variables metodológicas a mantener
        print("\n2. DEFINIENDO VARIABLES METODOLÓGICAS A MANTENER...")
        
        # Identificador único obligatorio
        columna_id = 'codigo_modular'
        
        # Variables dependientes (Y) del estudio
        variables_y = []
        for col in todas_columnas:
            if col.startswith('Y') and ('_' not in col or col in ['Y1_ILA', 'Y2_TD', 'Y3_PR']):
                variables_y.append(col)
        
        # Variables independientes (X) del estudio - solo principales
        variables_x_principales = []
        variables_x_auxiliares = []
        
        for col in todas_columnas:
            if col.startswith('X'):
                # Variables principales (números base como X1, X2, X11, X13)
                if any(col.startswith(f'X{num}_') or col == f'X{num}' for num in [1, 2, 4, 10, 11, 12, 13, 15]):
                    if '_zscore' in col:
                        continue  # Saltar z-scores, no son variables principales
                    elif col in ['X11_RED', 'X13_TMATRC']:  # Variables principales ya calculadas
                        variables_x_principales.append(col)
                    elif col.startswith('X13_TMATRC_'):  # Auxiliares de X13
                        variables_x_auxiliares.append(col)
                    elif not any(suffix in col for suffix in ['_zscore', '_categoria', '_p', '_coef']):
                        variables_x_principales.append(col)
        
        # Solo incluir auxiliares específicas que son importantes
        auxiliares_importantes = ['X13_TMATRC_CATEGORIA']  # Solo la categoría, resto se puede eliminar
        variables_x_auxiliares_filtradas = [col for col in variables_x_auxiliares if col in auxiliares_importantes]
        
        # Lista final de columnas a mantener
        columnas_mantener = [columna_id] + variables_y + variables_x_principales + variables_x_auxiliares_filtradas
        
        print(f"   - Columna ID: {columna_id}")
        print(f"   - Variables Y: {variables_y}")
        print(f"   - Variables X principales: {variables_x_principales}")
        print(f"   - Variables X auxiliares: {variables_x_auxiliares_filtradas}")
        print(f"   - TOTAL A MANTENER: {len(columnas_mantener)} columnas")
        
        # Columnas a eliminar
        columnas_eliminar = [col for col in todas_columnas if col not in columnas_mantener]
        print(f"   - COLUMNAS A ELIMINAR: {len(columnas_eliminar)}")
        for col in columnas_eliminar:
            print(f"     * {col}")
        
        # 3. Crear respaldo completo
        print("\n3. CREANDO RESPALDO COMPLETO...")
        
        df_respaldo = pd.read_sql_query("SELECT * FROM indices_metodologicos", conn)
        
        os.makedirs('temp_data', exist_ok=True)
        archivo_respaldo = f'temp_data/indices_metodologicos_backup_completo_{pd.Timestamp.now().strftime("%Y%m%d_%H%M")}.csv'
        df_respaldo.to_csv(archivo_respaldo, index=False)
        print(f"   - Respaldo completo: {archivo_respaldo}")
        
        # 4. Verificar datos en columnas a mantener
        print("\n4. VERIFICANDO DATOS EN COLUMNAS A MANTENER...")
        
        for col in columnas_mantener:
            if col != columna_id:
                try:
                    query_datos = f"SELECT COUNT({col}) as disponible FROM indices_metodologicos WHERE {col} IS NOT NULL"
                    count = pd.read_sql_query(query_datos, conn).iloc[0]['disponible']
                    print(f"   - {col}: {count} registros con datos")
                except Exception as e:
                    print(f"   - {col}: Error al verificar - {e}")
        
        # 5. Crear tabla limpia
        print("\n5. CREANDO TABLA LIMPIA...")
        
        cursor.execute("BEGIN TRANSACTION")
        
        try:
            # Crear tabla nueva con solo las columnas necesarias
            cursor.execute("DROP TABLE IF EXISTS indices_metodologicos_limpia")
            
            # Definir tipos de columnas optimizados
            columnas_sql = []
            for col in columnas_mantener:
                if col == 'codigo_modular':
                    columnas_sql.append(f"{col} TEXT PRIMARY KEY")
                elif col in ['X13_TMATRC_CATEGORIA'] or '_categoria' in col.lower():
                    columnas_sql.append(f"{col} TEXT")
                else:
                    columnas_sql.append(f"{col} REAL")
            
            create_sql = f"CREATE TABLE indices_metodologicos_limpia ({', '.join(columnas_sql)})"
            cursor.execute(create_sql)
            
            # Copiar solo las columnas necesarias
            columnas_select = ', '.join(columnas_mantener)
            cursor.execute(f"INSERT INTO indices_metodologicos_limpia SELECT {columnas_select} FROM indices_metodologicos")
            
            # Verificar cantidad de registros copiados
            cursor.execute("SELECT COUNT(*) FROM indices_metodologicos_limpia")
            registros_copiados = cursor.fetchone()[0]
            
            # Reemplazar tabla original
            cursor.execute("DROP TABLE indices_metodologicos")
            cursor.execute("ALTER TABLE indices_metodologicos_limpia RENAME TO indices_metodologicos")
            
            cursor.execute("COMMIT")
            
            print(f"   - Tabla limpia creada: {registros_copiados} registros")
            print(f"   - Columnas eliminadas: {len(columnas_eliminar)}")
            print(f"   - Columnas mantenidas: {len(columnas_mantener)}")
            
        except Exception as e:
            cursor.execute("ROLLBACK")
            raise e
        
        # 6. Verificar estructura final
        print("\n6. VERIFICACIÓN ESTRUCTURA FINAL...")
        
        cursor.execute("PRAGMA table_info(indices_metodologicos)")
        columnas_final = cursor.fetchall()
        
        print(f"   ESTRUCTURA FINAL:")
        for col_info in columnas_final:
            col_name = col_info[1]
            col_type = col_info[2]
            print(f"   - {col_name} ({col_type})")
        
        # 7. Estadísticas finales por variable
        print("\n7. ESTADÍSTICAS FINALES POR VARIABLE...")
        
        query_total = "SELECT COUNT(*) as total FROM indices_metodologicos"
        total_registros = pd.read_sql_query(query_total, conn).iloc[0]['total']
        
        print(f"   Total registros: {total_registros}")
        print(f"   COBERTURA POR VARIABLE:")
        
        for col in columnas_mantener:
            if col != columna_id:
                try:
                    query_stats = f"SELECT COUNT({col}) as disponible FROM indices_metodologicos WHERE {col} IS NOT NULL"
                    disponible = pd.read_sql_query(query_stats, conn).iloc[0]['disponible']
                    porcentaje = (disponible / total_registros) * 100
                    print(f"   - {col}: {disponible}/{total_registros} ({porcentaje:.1f}%)")
                except:
                    print(f"   - {col}: Error en estadísticas")
        
        # 8. Crear respaldo final
        print("\n8. CREANDO RESPALDO FINAL...")
        
        df_final = pd.read_sql_query("SELECT * FROM indices_metodologicos", conn)
        archivo_final = f'temp_data/indices_metodologicos_limpia_final_{pd.Timestamp.now().strftime("%Y%m%d_%H%M")}.csv'
        df_final.to_csv(archivo_final, index=False)
        print(f"   - Respaldo final: {archivo_final}")
        
        # 9. Mostrar muestra de tabla final
        print("\n9. MUESTRA DE TABLA FINAL:")
        
        muestra = pd.read_sql_query("SELECT * FROM indices_metodologicos LIMIT 3", conn)
        print(f"   Columnas finales: {list(muestra.columns)}")
        print(f"   Registros de muestra:")
        for idx, row in muestra.iterrows():
            print(f"   - {row['codigo_modular']}: {len([v for v in row.values if pd.notna(v) and v != ''])} campos con datos")
        
        print(f"\n=== LIMPIEZA TOTAL COMPLETADA ===")
        print(f"Tabla indices_metodologicos optimizada:")
        print(f"- {len(columnas_mantener)} columnas (solo variables metodológicas)")
        print(f"- {total_registros} registros")
        print(f"- {len(columnas_eliminar)} columnas eliminadas")
        print(f"- Estructura definitiva para variables del estudio")
        
        return True
        
    except Exception as e:
        print(f"Error en limpieza: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        return False
    
    finally:
        conn.close()

if __name__ == "__main__":
    main()