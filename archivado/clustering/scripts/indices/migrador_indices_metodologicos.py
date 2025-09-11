#!/usr/bin/env python3
"""
Migrador de Variables a Tabla Única indices_metodologicos
1. Migra X11_RED_ajustado y X13_TMATRC a tabla indices_metodologicos
2. Elimina tablas temporales innecesarias
3. Establece metodología de tabla única para futuras variables
"""

import sqlite3
import pandas as pd
import numpy as np
import os

def main():
    print("=== MIGRACIÓN A TABLA ÍNDICES METODOLÓGICOS ===")
    
    conn = sqlite3.connect('reasis_database.db')
    
    try:
        # 1. Verificar estructura actual de indices_metodologicos
        print("\n1. VERIFICANDO TABLA INDICES_METODOLOGICOS...")
        
        try:
            df_indices = pd.read_sql_query("SELECT * FROM indices_metodologicos LIMIT 5", conn)
            print(f"   - Tabla existe con {len(df_indices)} registros (muestra)")
            print(f"   - Columnas existentes: {list(df_indices.columns)}")
        except:
            print("   - Tabla indices_metodologicos no existe, se creará")
            df_indices = None
        
        # 2. Cargar datos X11_RED_ajustado
        print("\n2. CARGANDO X11_RED_AJUSTADO...")
        
        query_x11 = """
        SELECT 
            codigo_modular,
            X11_RED_ajustado,
            total_docentes_ajustado,
            metodo_ajuste
        FROM instituciones_educativas 
        WHERE X11_RED_ajustado IS NOT NULL
        """
        
        df_x11 = pd.read_sql_query(query_x11, conn)
        print(f"   - X11_RED_ajustado cargado: {len(df_x11)} registros")
        
        # 3. Cargar datos X13_TMATRC  
        print("\n3. CARGANDO X13_TMATRC...")
        
        query_x13 = """
        SELECT 
            codigo_modular,
            X13_TMATRC,
            X13_TMATRC_CATEGORIA,
            X13_TMATRC_MANN_KENDALL_P,
            X13_TMATRC_COEF_VARIACION
        FROM instituciones_educativas 
        WHERE X13_TMATRC IS NOT NULL
        """
        
        df_x13 = pd.read_sql_query(query_x13, conn)
        print(f"   - X13_TMATRC cargado: {len(df_x13)} registros")
        
        # 4. Cargar datos base de instituciones
        print("\n4. CARGANDO DATOS BASE...")
        
        query_base = """
        SELECT 
            codigo_modular,
            nombre_institucion,
            nombre_red_fya_matched as red_fya,
            entra_estudio_clustering
        FROM instituciones_educativas
        WHERE codigo_modular IS NOT NULL
        """
        
        df_base = pd.read_sql_query(query_base, conn)
        print(f"   - Instituciones base: {len(df_base)} registros")
        
        # 5. Crear/actualizar tabla indices_metodologicos
        print("\n5. CREANDO/ACTUALIZANDO TABLA INDICES_METODOLOGICOS...")
        
        # Merge de todos los datos
        df_consolidado = df_base.copy()
        
        # Merge X11_RED_ajustado
        df_consolidado = df_consolidado.merge(df_x11, on='codigo_modular', how='left')
        
        # Merge X13_TMATRC
        df_consolidado = df_consolidado.merge(df_x13, on='codigo_modular', how='left')
        
        # Si tabla indices_metodologicos existe, intentar preservar datos existentes
        if df_indices is not None:
            print("   - Preservando datos existentes de indices_metodologicos...")
            
            # Identificar columnas existentes que no están en el consolidado
            columnas_preservar = [col for col in df_indices.columns 
                                if col not in df_consolidado.columns and col != 'codigo_modular']
            
            if columnas_preservar:
                df_existente = df_indices[['codigo_modular'] + columnas_preservar]
                df_consolidado = df_consolidado.merge(df_existente, on='codigo_modular', how='left')
                print(f"   - Columnas preservadas: {columnas_preservar}")
        
        # Reordenar columnas por convención
        columnas_ordenadas = ['codigo_modular', 'nombre_institucion', 'red_fya', 'entra_estudio_clustering']
        
        # Variables Y (dependientes)
        cols_y = [col for col in df_consolidado.columns if col.startswith('Y') or col.startswith('ILA') or col.startswith('TD')]
        
        # Variables X (independientes) - ordenar por número
        cols_x = [col for col in df_consolidado.columns if col.startswith('X')]
        cols_x_sorted = sorted(cols_x, key=lambda x: int(''.join(filter(str.isdigit, x.split('_')[0]))) if any(char.isdigit() for char in x.split('_')[0]) else 999)
        
        # Otras columnas
        otras_cols = [col for col in df_consolidado.columns 
                     if col not in columnas_ordenadas + cols_y + cols_x_sorted]
        
        columnas_finales = columnas_ordenadas + cols_y + cols_x_sorted + otras_cols
        columnas_finales = [col for col in columnas_finales if col in df_consolidado.columns]
        
        df_final = df_consolidado[columnas_finales]
        
        # Guardar tabla indices_metodologicos
        df_final.to_sql('indices_metodologicos', conn, if_exists='replace', index=False)
        
        print(f"   - Tabla indices_metodologicos actualizada: {len(df_final)} registros")
        print(f"   - Columnas totales: {len(df_final.columns)}")
        
        # 6. Crear CSV temporal para respaldo
        print("\n6. CREANDO RESPALDO CSV...")
        
        os.makedirs('temp_data', exist_ok=True)
        archivo_respaldo = f'temp_data/indices_metodologicos_backup_{pd.Timestamp.now().strftime("%Y%m%d_%H%M")}.csv'
        df_final.to_csv(archivo_respaldo, index=False)
        print(f"   - Respaldo creado: {archivo_respaldo}")
        
        # 7. Eliminar tablas temporales
        print("\n7. ELIMINANDO TABLAS TEMPORALES...")
        
        cursor = conn.cursor()
        
        tablas_a_eliminar = [
            'x11_red_calculado',
            'log_ajustes_ratios', 
            'imputaciones_docentes_log',
            'tendencias_matricula',
            'tendencias_matricula_robustas'
        ]
        
        for tabla in tablas_a_eliminar:
            try:
                cursor.execute(f"DROP TABLE IF EXISTS {tabla}")
                print(f"   - Tabla {tabla} eliminada")
            except Exception as e:
                print(f"   - Error eliminando {tabla}: {e}")
        
        conn.commit()
        
        # 8. Verificar estructura final
        print("\n8. VERIFICACIÓN FINAL...")
        
        query_verificacion = """
        SELECT 
            COUNT(*) as total_registros,
            COUNT(X11_RED_ajustado) as x11_disponible,
            COUNT(X13_TMATRC) as x13_disponible
        FROM indices_metodologicos
        """
        
        stats = pd.read_sql_query(query_verificacion, conn).iloc[0]
        
        print(f"   ESTADÍSTICAS FINALES:")
        print(f"   - Total registros: {int(stats['total_registros'])}")
        print(f"   - X11_RED_ajustado: {int(stats['x11_disponible'])} ({(stats['x11_disponible']/stats['total_registros'])*100:.1f}%)")
        print(f"   - X13_TMATRC: {int(stats['x13_disponible'])} ({(stats['x13_disponible']/stats['total_registros'])*100:.1f}%)")
        
        # 9. Mostrar muestra de datos migrados
        print("\n9. MUESTRA DE DATOS MIGRADOS:")
        
        muestra = pd.read_sql_query("""
            SELECT 
                codigo_modular, 
                nombre_institucion, 
                X11_RED_ajustado, 
                X13_TMATRC,
                X13_TMATRC_CATEGORIA
            FROM indices_metodologicos 
            WHERE X11_RED_ajustado IS NOT NULL AND X13_TMATRC IS NOT NULL
            LIMIT 5
        """, conn)
        
        for idx, row in muestra.iterrows():
            print(f"   - {row['codigo_modular']}: X11={row['X11_RED_ajustado']:.2f}, X13={row['X13_TMATRC']:.3f} ({row['X13_TMATRC_CATEGORIA']})")
        
        print(f"\n=== MIGRACIÓN COMPLETADA EXITOSAMENTE ===")
        print(f"✓ Tabla única indices_metodologicos establecida")
        print(f"✓ X11_RED_ajustado y X13_TMATRC migrados")
        print(f"✓ Tablas temporales eliminadas")
        print(f"✓ Metodología estandarizada para futuras variables")
        
        return True
        
    except Exception as e:
        print(f"Error en migración: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        return False
    
    finally:
        conn.close()

if __name__ == "__main__":
    main()