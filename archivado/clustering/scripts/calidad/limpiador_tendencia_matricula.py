#!/usr/bin/env python3
"""
Limpiador de variables de tendencia - Mantener solo versión robusta
1. Identifica todas las variables de tendencia
2. Mantiene solo X13_TMATRC (versión robusta Theil-Sen)
3. Elimina variables redundantes/menos robustas
"""

import sqlite3
import pandas as pd
import os

def main():
    print("=== LIMPIEZA VARIABLES TENDENCIA ===")
    
    conn = sqlite3.connect('reasis_database.db')
    
    try:
        # 1. Verificar columnas de tendencia actuales
        print("\n1. IDENTIFICANDO VARIABLES DE TENDENCIA...")
        
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(indices_metodologicos)")
        columnas = cursor.fetchall()
        
        # Buscar todas las variantes de tendencia
        columnas_tendencia = []
        for col in columnas:
            col_name = col[1]
            if any(keyword in col_name.upper() for keyword in ['TEND', 'TMATRC', 'MATRICULA']):
                columnas_tendencia.append(col_name)
        
        print(f"   - Variables de tendencia encontradas: {columnas_tendencia}")
        
        # 2. Analizar cobertura de cada variable
        print("\n2. ANALIZANDO COBERTURA...")
        
        for col in columnas_tendencia:
            query_cobertura = f"SELECT COUNT({col}) as disponible FROM indices_metodologicos WHERE {col} IS NOT NULL"
            try:
                count = pd.read_sql_query(query_cobertura, conn).iloc[0]['disponible']
                print(f"   - {col}: {count} registros")
            except:
                print(f"   - {col}: Error al consultar")
        
        # 3. Identificar variable principal a mantener (X13_TMATRC)
        print("\n3. DEFINIENDO VARIABLE PRINCIPAL...")
        
        variable_principal = 'X13_TMATRC'
        variables_auxiliares = ['X13_TMATRC_CATEGORIA', 'X13_TMATRC_MANN_KENDALL_P', 'X13_TMATRC_COEF_VARIACION']
        variables_eliminar = []
        
        for col in columnas_tendencia:
            if col != variable_principal and col not in variables_auxiliares:
                variables_eliminar.append(col)
        
        print(f"   - Variable principal: {variable_principal}")
        print(f"   - Variables auxiliares: {variables_auxiliares}")
        print(f"   - Variables a eliminar: {variables_eliminar}")
        
        if not variables_eliminar:
            print("   - No hay variables redundantes para eliminar")
            return True
        
        # 4. Crear respaldo antes de modificar
        print("\n4. CREANDO RESPALDO...")
        
        df_respaldo = pd.read_sql_query("SELECT * FROM indices_metodologicos", conn)
        
        os.makedirs('temp_data', exist_ok=True)
        archivo_respaldo = f'temp_data/indices_metodologicos_pre_tendencia_cleanup_{pd.Timestamp.now().strftime("%Y%m%d_%H%M")}.csv'
        df_respaldo.to_csv(archivo_respaldo, index=False)
        print(f"   - Respaldo creado: {archivo_respaldo}")
        
        # 5. Eliminar variables redundantes
        print("\n5. ELIMINANDO VARIABLES REDUNDANTES...")
        
        cursor.execute("BEGIN TRANSACTION")
        
        try:
            # Obtener todas las columnas excepto las que vamos a eliminar
            todas_columnas = [col[1] for col in columnas]
            columnas_mantener = [col for col in todas_columnas if col not in variables_eliminar]
            
            print(f"   - Columnas originales: {len(todas_columnas)}")
            print(f"   - Columnas a mantener: {len(columnas_mantener)}")
            
            # Crear tabla temporal sin las columnas redundantes
            cursor.execute("DROP TABLE IF EXISTS indices_metodologicos_clean")
            
            # Definir tipos de columnas
            columnas_sql = []
            for col in columnas_mantener:
                if col in ['codigo_modular', 'nombre_institucion', 'red_fya', 'entra_estudio_clustering', 'X13_TMATRC_CATEGORIA']:
                    columnas_sql.append(f"{col} TEXT")
                else:
                    columnas_sql.append(f"{col} REAL")
            
            create_sql = f"CREATE TABLE indices_metodologicos_clean ({', '.join(columnas_sql)})"
            cursor.execute(create_sql)
            
            # Copiar datos
            columnas_select = ', '.join(columnas_mantener)
            cursor.execute(f"INSERT INTO indices_metodologicos_clean SELECT {columnas_select} FROM indices_metodologicos")
            
            # Reemplazar tabla original
            cursor.execute("DROP TABLE indices_metodologicos")
            cursor.execute("ALTER TABLE indices_metodologicos_clean RENAME TO indices_metodologicos")
            
            cursor.execute("COMMIT")
            
            for var in variables_eliminar:
                print(f"   - Eliminada: {var}")
            
        except Exception as e:
            cursor.execute("ROLLBACK")
            raise e
        
        # 6. Verificar resultado final
        print("\n6. VERIFICACIÓN FINAL...")
        
        cursor.execute("PRAGMA table_info(indices_metodologicos)")
        columnas_final = cursor.fetchall()
        
        columnas_tendencia_final = []
        for col in columnas_final:
            col_name = col[1]
            if any(keyword in col_name.upper() for keyword in ['TEND', 'TMATRC', 'MATRICULA']):
                columnas_tendencia_final.append(col_name)
        
        print(f"   - Variables de tendencia finales: {columnas_tendencia_final}")
        
        # Estadísticas finales
        if variable_principal in [col[1] for col in columnas_final]:
            query_stats = f"""
            SELECT 
                COUNT(*) as total,
                COUNT({variable_principal}) as disponible,
                AVG({variable_principal}) as promedio,
                MIN({variable_principal}) as minimo,
                MAX({variable_principal}) as maximo
            FROM indices_metodologicos
            """
            
            stats = pd.read_sql_query(query_stats, conn).iloc[0]
            
            print(f"   ESTADÍSTICAS {variable_principal}:")
            print(f"   - Total registros: {int(stats['total'])}")
            print(f"   - Disponible: {int(stats['disponible'])} ({(stats['disponible']/stats['total'])*100:.1f}%)")
            promedio = stats['promedio'] if stats['promedio'] is not None else 0
            minimo = stats['minimo'] if stats['minimo'] is not None else 0
            maximo = stats['maximo'] if stats['maximo'] is not None else 0
            print(f"   - Promedio: {promedio:.3f} estudiantes/año")
            print(f"   - Rango: {minimo:.3f} a {maximo:.3f}")
        
        # 7. Verificar categorías si existen
        if 'X13_TMATRC_CATEGORIA' in [col[1] for col in columnas_final]:
            print("\n7. VERIFICANDO CATEGORÍAS...")
            
            query_categorias = """
            SELECT 
                X13_TMATRC_CATEGORIA,
                COUNT(*) as cantidad
            FROM indices_metodologicos 
            WHERE X13_TMATRC_CATEGORIA IS NOT NULL
            GROUP BY X13_TMATRC_CATEGORIA
            ORDER BY cantidad DESC
            """
            
            df_categorias = pd.read_sql_query(query_categorias, conn)
            
            print(f"   DISTRIBUCIÓN CATEGORÍAS:")
            for idx, row in df_categorias.iterrows():
                print(f"   - {row['X13_TMATRC_CATEGORIA']}: {row['cantidad']} instituciones")
        
        # 8. Crear respaldo final
        print("\n8. CREANDO RESPALDO FINAL...")
        
        df_final = pd.read_sql_query("SELECT * FROM indices_metodologicos", conn)
        archivo_final = f'temp_data/indices_metodologicos_post_tendencia_cleanup_{pd.Timestamp.now().strftime("%Y%m%d_%H%M")}.csv'
        df_final.to_csv(archivo_final, index=False)
        print(f"   - Respaldo final: {archivo_final}")
        
        print(f"\n=== LIMPIEZA TENDENCIA COMPLETADA ===")
        print(f"Variable principal mantenida: {variable_principal}")
        print(f"Variables eliminadas: {len(variables_eliminar)}")
        print(f"Tabla optimizada y sin redundancias")
        
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