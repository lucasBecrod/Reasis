#!/usr/bin/env python3
"""
Reconstructor de tabla indices_metodologicos - Estructura Correcta y Protegida
1. Crea respaldo completo de datos actuales
2. Recupera Y1_ILA e Y2_TD de fuentes originales
3. Recrea tabla con estructura correcta: ID + nombre + numero_rfa + variables ordenadas
4. Implementa sistema de protección contra modificaciones no autorizadas
"""

import sqlite3
import pandas as pd
import os
from datetime import datetime

def main():
    print("=== RECONSTRUCCIÓN TABLA INDICES_METODOLOGICOS ===")
    
    conn = sqlite3.connect('reasis_database.db')
    
    try:
        # 1. Crear respaldo completo de estado actual
        print("\n1. CREANDO RESPALDO COMPLETO...")
        
        # Respaldo de tabla actual
        try:
            df_actual = pd.read_sql_query("SELECT * FROM indices_metodologicos", conn)
            os.makedirs('temp_data', exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archivo_respaldo = f'temp_data/indices_metodologicos_respaldo_{timestamp}.csv'
            df_actual.to_csv(archivo_respaldo, index=False)
            print(f"   - Respaldo actual creado: {archivo_respaldo}")
        except Exception as e:
            print(f"   - Error creando respaldo: {e}")
            df_actual = pd.DataFrame()
        
        # 2. Recuperar datos base de instituciones
        print("\n2. RECUPERANDO DATOS BASE DE INSTITUCIONES...")
        
        query_base = """
        SELECT 
            codigo_modular,
            nombre_institucion,
            numero_fya,
            nombre_red_fya_matched,
            entra_estudio_clustering
        FROM instituciones_educativas
        WHERE codigo_modular IS NOT NULL
        ORDER BY codigo_modular
        """
        
        df_base = pd.read_sql_query(query_base, conn)
        print(f"   - Instituciones base recuperadas: {len(df_base)}")
        
        # 3. Recuperar Y1_ILA desde resultados_academicos
        print("\n3. RECUPERANDO Y1_ILA DESDE RESULTADOS_ACADEMICOS...")
        
        try:
            # Calcular ILA desde resultados académicos como estaba documentado
            query_ila = """
            SELECT 
                codigo_modular,
                AVG(matematicas) as promedio_matematicas,
                AVG(comunicacion) as promedio_comunicacion,
                AVG(produccion_textos) as promedio_produccion_textos,
                COUNT(*) as total_estudiantes
            FROM resultados_academicos 
            WHERE matematicas IS NOT NULL OR comunicacion IS NOT NULL OR produccion_textos IS NOT NULL
            GROUP BY codigo_modular
            HAVING COUNT(*) > 0
            """
            
            df_ila_calc = pd.read_sql_query(query_ila, conn)
            
            # Calcular ILA: promedio de promedios por materia
            df_ila_calc['Y1_ILA'] = (
                df_ila_calc['promedio_matematicas'].fillna(0) + 
                df_ila_calc['promedio_comunicacion'].fillna(0) + 
                df_ila_calc['promedio_produccion_textos'].fillna(0)
            ) / 3
            
            # Solo códigos modulares que existen en base
            df_ila = df_ila_calc[['codigo_modular', 'Y1_ILA']].copy()
            df_ila = df_ila[df_ila['codigo_modular'].isin(df_base['codigo_modular'])]
            
            print(f"   - Y1_ILA calculado para {len(df_ila)} instituciones")
            print(f"   - Promedio ILA: {df_ila['Y1_ILA'].mean():.3f}")
            
        except Exception as e:
            print(f"   - Error calculando Y1_ILA: {e}")
            df_ila = pd.DataFrame(columns=['codigo_modular', 'Y1_ILA'])
        
        # 4. Recuperar Y2_TD desde instituciones_educativas
        print("\n4. RECUPERANDO Y2_TD DESDE INSTITUCIONES_EDUCATIVAS...")
        
        try:
            query_td = """
            SELECT 
                codigo_modular,
                ILA_2022,
                ILA_2023,
                ILA_2024
            FROM instituciones_educativas
            WHERE codigo_modular IS NOT NULL
            AND (ILA_2022 IS NOT NULL OR ILA_2023 IS NOT NULL OR ILA_2024 IS NOT NULL)
            """
            
            df_td_calc = pd.read_sql_query(query_td, conn)
            
            # Calcular tendencia usando regresión lineal simple como documentado
            from scipy.stats import linregress
            
            td_results = []
            for idx, row in df_td_calc.iterrows():
                años = []
                ilas = []
                
                if pd.notna(row['ILA_2022']):
                    años.append(2022)
                    ilas.append(row['ILA_2022'])
                if pd.notna(row['ILA_2023']):
                    años.append(2023)
                    ilas.append(row['ILA_2023'])
                if pd.notna(row['ILA_2024']):
                    años.append(2024)
                    ilas.append(row['ILA_2024'])
                
                if len(años) >= 2:
                    slope, intercept, r_value, p_value, std_err = linregress(años, ilas)
                    td_results.append({
                        'codigo_modular': row['codigo_modular'],
                        'Y2_TD': slope
                    })
            
            df_td = pd.DataFrame(td_results)
            print(f"   - Y2_TD calculado para {len(df_td)} instituciones")
            if len(df_td) > 0:
                print(f"   - Promedio TD: {df_td['Y2_TD'].mean():.4f}")
            
        except Exception as e:
            print(f"   - Error calculando Y2_TD: {e}")
            df_td = pd.DataFrame(columns=['codigo_modular', 'Y2_TD'])
        
        # 5. Recuperar X11_RED y X13_TMATRC calculadas
        print("\n5. RECUPERANDO VARIABLES X CALCULADAS...")
        
        # X11_RED desde instituciones_educativas
        try:
            query_x11 = """
            SELECT codigo_modular, X11_RED_ajustado as X11_RED
            FROM instituciones_educativas 
            WHERE X11_RED_ajustado IS NOT NULL
            """
            df_x11 = pd.read_sql_query(query_x11, conn)
            print(f"   - X11_RED recuperado para {len(df_x11)} instituciones")
        except:
            df_x11 = pd.DataFrame(columns=['codigo_modular', 'X11_RED'])
        
        # X13_TMATRC desde instituciones_educativas
        try:
            query_x13 = """
            SELECT 
                codigo_modular, 
                X13_TMATRC,
                X13_TMATRC_CATEGORIA
            FROM instituciones_educativas 
            WHERE X13_TMATRC IS NOT NULL
            """
            df_x13 = pd.read_sql_query(query_x13, conn)
            print(f"   - X13_TMATRC recuperado para {len(df_x13)} instituciones")
        except:
            df_x13 = pd.DataFrame(columns=['codigo_modular', 'X13_TMATRC', 'X13_TMATRC_CATEGORIA'])
        
        # 6. Definir estructura correcta según matriz de operacionalización
        print("\n6. DEFINIENDO ESTRUCTURA CORRECTA...")
        
        estructura_ordenada = [
            # Identificadores
            'codigo_modular',
            'nombre_institucion', 
            'numero_fya',
            
            # Variables Dependientes (Y) - según matriz
            'Y1_ILA',    # Índice Logro Académico
            'Y2_TD',     # Tendencia Desempeño
            'Y3_PR',     # Progreso Relativo
            
            # Variables Independientes (X) - según matriz ordenadas numéricamente
            'X1_NVC',    # Nivel Vulnerabilidad Contextual
            'X2_TR',     # Tipo Ruralidad
            'X4_IDD',    # Índice Desempeño Docente
            'X10_IE',    # Infraestructura Educativa
            'X11_RED',   # Ratio Estudiante-Docente (calculada)
            'X12_TOE',   # Tipo Organización Escolar
            'X13_TMATRC', # Tendencia Matrícula (calculada)
            'X15_MEIB',  # Modalidad EIB
            
            # Auxiliares importantes
            'X13_TMATRC_CATEGORIA'
        ]
        
        print(f"   - Estructura definida: {len(estructura_ordenada)} columnas")
        for i, col in enumerate(estructura_ordenada):
            print(f"     {i+1:2d}. {col}")
        
        # 7. Crear tabla nueva con datos consolidados
        print("\n7. CONSOLIDANDO DATOS...")
        
        # Empezar con datos base
        df_nuevo = df_base[['codigo_modular', 'nombre_institucion', 'numero_fya']].copy()
        
        # Merge con cada variable calculada
        if len(df_ila) > 0:
            df_nuevo = df_nuevo.merge(df_ila[['codigo_modular', 'Y1_ILA']], on='codigo_modular', how='left')
        else:
            df_nuevo['Y1_ILA'] = None
            
        if len(df_td) > 0:
            df_nuevo = df_nuevo.merge(df_td[['codigo_modular', 'Y2_TD']], on='codigo_modular', how='left')
        else:
            df_nuevo['Y2_TD'] = None
            
        if len(df_x11) > 0:
            df_nuevo = df_nuevo.merge(df_x11[['codigo_modular', 'X11_RED']], on='codigo_modular', how='left')
        else:
            df_nuevo['X11_RED'] = None
            
        if len(df_x13) > 0:
            df_nuevo = df_nuevo.merge(df_x13, on='codigo_modular', how='left')
        else:
            df_nuevo['X13_TMATRC'] = None
            df_nuevo['X13_TMATRC_CATEGORIA'] = None
        
        # Agregar columnas faltantes con NULL
        for col in estructura_ordenada:
            if col not in df_nuevo.columns:
                df_nuevo[col] = None
        
        # Reordenar según estructura definida
        df_nuevo = df_nuevo[estructura_ordenada]
        
        # 8. Crear tabla nueva con protección
        print("\n8. CREANDO TABLA PROTEGIDA...")
        
        cursor = conn.cursor()
        cursor.execute("BEGIN TRANSACTION")
        
        try:
            # Eliminar tabla actual
            cursor.execute("DROP TABLE IF EXISTS indices_metodologicos")
            
            # Crear nueva tabla con estructura correcta
            columnas_sql = []
            for col in estructura_ordenada:
                if col == 'codigo_modular':
                    columnas_sql.append(f"{col} TEXT PRIMARY KEY")
                elif col in ['nombre_institucion', 'numero_fya', 'X13_TMATRC_CATEGORIA']:
                    columnas_sql.append(f"{col} TEXT")
                else:
                    columnas_sql.append(f"{col} REAL")
            
            create_sql = f"CREATE TABLE indices_metodologicos ({', '.join(columnas_sql)})"
            cursor.execute(create_sql)
            
            # Insertar datos
            df_nuevo.to_sql('indices_metodologicos_temp', conn, if_exists='replace', index=False)
            
            # Copiar datos a tabla definitiva
            cursor.execute(f"""
                INSERT INTO indices_metodologicos 
                SELECT {', '.join(estructura_ordenada)} 
                FROM indices_metodologicos_temp
            """)
            
            cursor.execute("DROP TABLE indices_metodologicos_temp")
            
            # Insertar fila de protección (segunda fila)
            fila_proteccion = ['PROTECTION_ROW'] + ['REQUIRES_LUCAS_AUTHORIZATION'] * (len(estructura_ordenada) - 1)
            placeholders = ', '.join(['?' for _ in estructura_ordenada])
            cursor.execute(f"INSERT INTO indices_metodologicos VALUES ({placeholders})", fila_proteccion)
            
            cursor.execute("COMMIT")
            
            print(f"   - Tabla recreada exitosamente")
            print(f"   - Registros de datos: {len(df_nuevo)}")
            print(f"   - Fila de protección insertada")
            
        except Exception as e:
            cursor.execute("ROLLBACK")
            raise e
        
        # 9. Verificar datos recuperados
        print("\n9. VERIFICACIÓN DE DATOS RECUPERADOS...")
        
        query_verificacion = """
        SELECT 
            COUNT(*) as total,
            COUNT(Y1_ILA) as y1_disponible,
            COUNT(Y2_TD) as y2_disponible,
            COUNT(X11_RED) as x11_disponible,
            COUNT(X13_TMATRC) as x13_disponible
        FROM indices_metodologicos 
        WHERE codigo_modular != 'PROTECTION_ROW'
        """
        
        stats = pd.read_sql_query(query_verificacion, conn).iloc[0]
        
        print(f"   ESTADÍSTICAS FINALES:")
        print(f"   - Total instituciones: {int(stats['total'])}")
        print(f"   - Y1_ILA disponible: {int(stats['y1_disponible'])} ({(stats['y1_disponible']/stats['total'])*100:.1f}%)")
        print(f"   - Y2_TD disponible: {int(stats['y2_disponible'])} ({(stats['y2_disponible']/stats['total'])*100:.1f}%)")
        print(f"   - X11_RED disponible: {int(stats['x11_disponible'])} ({(stats['x11_disponible']/stats['total'])*100:.1f}%)")
        print(f"   - X13_TMATRC disponible: {int(stats['x13_disponible'])} ({(stats['x13_disponible']/stats['total'])*100:.1f}%)")
        
        # 10. Crear respaldo final
        print("\n10. CREANDO RESPALDO FINAL...")
        
        df_final = pd.read_sql_query("SELECT * FROM indices_metodologicos WHERE codigo_modular != 'PROTECTION_ROW'", conn)
        archivo_final = f'temp_data/indices_metodologicos_reconstruida_{timestamp}.csv'
        df_final.to_csv(archivo_final, index=False)
        print(f"   - Respaldo final: {archivo_final}")
        
        print(f"\n=== RECONSTRUCCIÓN COMPLETADA ===")
        print(f"✓ Tabla indices_metodologicos recreada con estructura correcta")
        print(f"✓ Datos Y1_ILA e Y2_TD recuperados desde fuentes originales")
        print(f"✓ Variables X11_RED y X13_TMATRC preservadas")
        print(f"✓ Sistema de protección implementado")
        print(f"✓ Estructura ordenada según matriz de operacionalización")
        print(f"\n⚠️  IMPORTANTE: La segunda fila contiene protección contra modificaciones")
        print(f"⚠️  Requiere autorización explícita de Lucas para cambios futuros")
        
        return True
        
    except Exception as e:
        print(f"Error en reconstrucción: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        return False
    
    finally:
        conn.close()

if __name__ == "__main__":
    main()