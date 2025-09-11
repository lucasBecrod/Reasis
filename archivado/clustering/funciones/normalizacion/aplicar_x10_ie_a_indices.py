"""
Script para aplicar X10_IE - Infraestructura Educativa a indices_metodologicos
Integra datos desde CSV preliminar generado

Autor: Proyecto Reasis
Fecha: 2025-08-10
"""

import sqlite3
import pandas as pd
from datetime import datetime
import os

def aplicar_x10_ie_a_indices():
    """
    Aplica X10_IE desde CSV preliminar a tabla indices_metodologicos
    """
    
    print("=== APLICANDO X10_IE A INDICES_METODOLOGICOS ===\n")
    
    # 1. Buscar CSV preliminar más reciente
    print("1. LOCALIZANDO CSV PRELIMINAR:")
    
    csv_files = [f for f in os.listdir('temp_data') if f.startswith('x10_ie_preliminar_') and f.endswith('.csv')]
    
    if not csv_files:
        print("   ERROR: No se encontró archivo CSV preliminar")
        print("   Ejecutar primero: calcular_x10_ie_preliminar.py")
        return False, 0, 0
    
    # Tomar el más reciente (por timestamp en nombre)
    csv_file = sorted(csv_files)[-1]
    csv_path = os.path.join('temp_data', csv_file)
    
    print(f"   Archivo encontrado: {csv_path}")
    
    # 2. Cargar datos del CSV
    print(f"\n2. CARGANDO DATOS DEL CSV:")
    
    df_x10_ie = pd.read_csv(csv_path)
    
    print(f"   Registros en CSV: {len(df_x10_ie)}")
    print(f"   Columnas: {list(df_x10_ie.columns)}")
    
    # Verificar completitud
    registros_con_x10ie = df_x10_ie['X10_IE'].notna().sum()
    print(f"   Registros con X10_IE: {registros_con_x10ie}")
    
    if registros_con_x10ie != len(df_x10_ie):
        print(f"   ADVERTENCIA: Faltan {len(df_x10_ie) - registros_con_x10ie} valores X10_IE")
    
    # 3. Conectar a base de datos
    conn = sqlite3.connect('reasis_database.db')
    cursor = conn.cursor()
    
    # 4. Verificar/agregar columna X10_IE
    print(f"\n3. VERIFICANDO COLUMNA X10_IE:")
    
    cursor.execute("PRAGMA table_info(indices_metodologicos)")
    columnas = [row[1] for row in cursor.fetchall()]
    
    if 'X10_IE' not in columnas:
        print("   Agregando columna X10_IE...")
        cursor.execute("ALTER TABLE indices_metodologicos ADD COLUMN X10_IE REAL")
        conn.commit()
        print("   Columna X10_IE agregada exitosamente")
    else:
        print("   Columna X10_IE ya existe")
    
    # 5. Crear respaldo antes de la actualización
    print(f"\n4. CREANDO RESPALDO DE SEGURIDAD:")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"data/backups/indices_metodologicos_pre_x10ie_{timestamp}.csv"
    
    # Crear directorio si no existe
    os.makedirs(os.path.dirname(backup_path), exist_ok=True)
    
    df_backup = pd.read_sql_query("SELECT * FROM indices_metodologicos", conn)
    df_backup.to_csv(backup_path, index=False)
    
    print(f"   Respaldo creado: {backup_path}")
    
    # 6. Aplicar actualizaciones X10_IE
    print(f"\n5. APLICANDO ACTUALIZACIONES X10_IE:")
    
    actualizaciones_exitosas = 0
    errores = 0
    
    for idx, row in df_x10_ie.iterrows():
        codigo_modular = row['CODIGO_MODULAR']
        x10_ie_valor = row['X10_IE']
        
        if pd.notna(x10_ie_valor):
            try:
                cursor.execute("""
                    UPDATE indices_metodologicos 
                    SET X10_IE = ?
                    WHERE CODIGO_MODULAR = ?
                """, (float(x10_ie_valor), str(codigo_modular)))
                
                if cursor.rowcount > 0:
                    actualizaciones_exitosas += 1
                else:
                    print(f"   ADVERTENCIA: Código {codigo_modular} no encontrado en indices_metodologicos")
                    errores += 1
                    
            except Exception as e:
                print(f"   ERROR actualizando {codigo_modular}: {str(e)}")
                errores += 1
    
    conn.commit()
    
    print(f"   Actualizaciones exitosas: {actualizaciones_exitosas}")
    print(f"   Errores: {errores}")
    
    # 7. Verificar resultado
    print(f"\n6. VERIFICANDO RESULTADO:")
    
    result = cursor.execute("""
        SELECT COUNT(*) total,
               COUNT(X10_IE) con_x10_ie,
               COUNT(*) - COUNT(X10_IE) sin_x10_ie
        FROM indices_metodologicos
    """).fetchone()
    
    print(f"   Total instituciones: {result[0]}")
    print(f"   Con X10_IE: {result[1]} ({result[1]/result[0]*100:.1f}%)")
    print(f"   Sin X10_IE: {result[2]}")
    
    # 8. Estadísticas X10_IE
    print(f"\n7. ESTADÍSTICAS X10_IE:")
    
    stats = cursor.execute("""
        SELECT 
            MIN(X10_IE) as minimo,
            MAX(X10_IE) as maximo,
            AVG(X10_IE) as promedio,
            COUNT(X10_IE) as total_con_datos
        FROM indices_metodologicos 
        WHERE X10_IE IS NOT NULL
    """).fetchone()
    
    if stats[3] > 0:
        print(f"   Mínimo: {stats[0]:.4f}")
        print(f"   Máximo: {stats[1]:.4f}")
        print(f"   Promedio: {stats[2]:.4f}")
        print(f"   Instituciones con datos: {stats[3]}")
        
        # Distribución por rangos
        print(f"\n8. DISTRIBUCIÓN POR NIVELES:")
        
        rangos = cursor.execute("""
            SELECT 
                CASE 
                    WHEN X10_IE < 0.2 THEN 'Muy Baja (0-0.2)'
                    WHEN X10_IE < 0.4 THEN 'Baja (0.2-0.4)'
                    WHEN X10_IE < 0.6 THEN 'Media (0.4-0.6)'
                    WHEN X10_IE < 0.8 THEN 'Alta (0.6-0.8)'
                    ELSE 'Muy Alta (0.8-1.0)'
                END as rango,
                COUNT(*) as cantidad
            FROM indices_metodologicos 
            WHERE X10_IE IS NOT NULL
            GROUP BY 
                CASE 
                    WHEN X10_IE < 0.2 THEN 'Muy Baja (0-0.2)'
                    WHEN X10_IE < 0.4 THEN 'Baja (0.2-0.4)'
                    WHEN X10_IE < 0.6 THEN 'Media (0.4-0.6)'
                    WHEN X10_IE < 0.8 THEN 'Alta (0.6-0.8)'
                    ELSE 'Muy Alta (0.8-1.0)'
                END
            ORDER BY cantidad DESC
        """).fetchall()
        
        for rango, cantidad in rangos:
            porcentaje = cantidad/stats[3]*100
            print(f"   {rango}: {cantidad} instituciones ({porcentaje:.1f}%)")
        
        # Coherencia por ruralidad
        print(f"\n9. COHERENCIA POR RURALIDAD:")
        coherencia = cursor.execute("""
            SELECT 
                X2_TR,
                COUNT(*) as instituciones,
                AVG(X10_IE) as x10_ie_promedio,
                CASE X2_TR 
                    WHEN 1 THEN 'Urbano'
                    WHEN 2 THEN 'Rural'
                    ELSE 'Otro'
                END as tipo
            FROM indices_metodologicos 
            WHERE X10_IE IS NOT NULL AND X2_TR IS NOT NULL
            GROUP BY X2_TR
            ORDER BY X2_TR
        """).fetchall()
        
        for x2_tr, instituciones, x10_prom, tipo in coherencia:
            print(f"   {tipo} (X2_TR={x2_tr}): {instituciones} instituciones, X10_IE promedio = {x10_prom:.3f}")
    
    # 10. Validación final de completitud metodológica
    print(f"\n10. ACTUALIZACIÓN COMPLETITUD METODOLÓGICA:")
    
    completitud_query = '''
    SELECT 
        COUNT(CASE WHEN Y1_ILA IS NOT NULL THEN 1 END) * 100.0 / COUNT(*) as Y1_ILA,
        COUNT(CASE WHEN Y2_TD IS NOT NULL THEN 1 END) * 100.0 / COUNT(*) as Y2_TD,
        COUNT(CASE WHEN Y3_PR IS NOT NULL THEN 1 END) * 100.0 / COUNT(*) as Y3_PR,
        COUNT(CASE WHEN X1_NVC IS NOT NULL THEN 1 END) * 100.0 / COUNT(*) as X1_NVC,
        COUNT(CASE WHEN X2_TR IS NOT NULL THEN 1 END) * 100.0 / COUNT(*) as X2_TR,
        COUNT(CASE WHEN X4_IDD IS NOT NULL THEN 1 END) * 100.0 / COUNT(*) as X4_IDD,
        COUNT(CASE WHEN X5_ED IS NOT NULL THEN 1 END) * 100.0 / COUNT(*) as X5_ED,
        COUNT(CASE WHEN X6_CDD IS NOT NULL THEN 1 END) * 100.0 / COUNT(*) as X6_CDD,
        COUNT(CASE WHEN X10_IE IS NOT NULL THEN 1 END) * 100.0 / COUNT(*) as X10_IE,
        COUNT(CASE WHEN X11_RED IS NOT NULL THEN 1 END) * 100.0 / COUNT(*) as X11_RED,
        COUNT(CASE WHEN X12_TOE IS NOT NULL THEN 1 END) * 100.0 / COUNT(*) as X12_TOE,
        COUNT(CASE WHEN X15_MEIB IS NOT NULL THEN 1 END) * 100.0 / COUNT(*) as X15_MEIB,
        COUNT(*) as total_registros
    FROM indices_metodologicos
    '''
    
    df_completitud = pd.read_sql_query(completitud_query, conn)
    
    variables_completas = 0
    total_variables = 12
    
    print(f"   COMPLETITUD ACTUALIZADA (% datos disponibles):")
    for col in df_completitud.columns:
        if col != 'total_registros':
            completitud_pct = df_completitud[col].iloc[0]
            if completitud_pct >= 50:
                status = "[OK] COMPLETA"
                variables_completas += 1
            elif completitud_pct > 0:
                status = "[PARCIAL]"
                variables_completas += 0.5
            else:
                status = "[NO] FALTANTE"
            
            marca = "*" if col == 'X10_IE' else " "
            print(f"   {marca} {col}: {completitud_pct:.1f}% {status}")
    
    completitud_general = (variables_completas / total_variables) * 100
    print(f"\n   COMPLETITUD METODOLÓGICA TOTAL: {completitud_general:.1f}%")
    print(f"   VARIABLES DISPONIBLES: {variables_completas:.1f} / {total_variables}")
    
    if completitud_general >= 95:
        print(f"   [EXCELENTE] Metodología completa para clustering robusto")
    elif completitud_general >= 90:
        print(f"   [MUY BUENA] Metodología casi completa")
    elif completitud_general >= 75:
        print(f"   [BUENA] Metodología suficiente")
    else:
        print(f"   [LIMITADA] Metodología con restricciones")
    
    # 11. Crear respaldo final
    print(f"\n11. RESPALDO FINAL:")
    
    backup_final_path = f"data/backups/indices_metodologicos_con_x10ie_{timestamp}.csv"
    df_backup_final = pd.read_sql_query("SELECT * FROM indices_metodologicos", conn)
    df_backup_final.to_csv(backup_final_path, index=False)
    
    print(f"   Respaldo final creado: {backup_final_path}")
    
    conn.close()
    
    # Evaluar éxito
    exito_integracion = result[1] == result[0]  # Todas las instituciones tienen X10_IE
    
    print(f"\n[{'EXITO COMPLETO' if exito_integracion else 'EXITO PARCIAL'}] X10_IE INTEGRADO")
    print(f"[INFO] Cobertura: {result[1]}/{result[0]} instituciones ({result[1]/result[0]*100:.1f}%)")
    
    return exito_integracion, actualizaciones_exitosas, completitud_general

if __name__ == "__main__":
    exito, actualizados, completitud = aplicar_x10_ie_a_indices()
    
    print(f"\n=== RESULTADO INTEGRACIÓN X10_IE ===")
    print(f"Instituciones actualizadas: {actualizados}")
    print(f"Completitud metodológica: {completitud:.1f}%")
    
    if exito and completitud >= 90:
        print(f"\n[MILESTONE] VARIABLE X10_IE INTEGRADA EXITOSAMENTE")
        print(f"[IMPACTO] Completitud metodológica alcanzada: {completitud:.1f}%")
        print(f"[SIGUIENTE] Clustering K-Means con 12/12 variables disponibles")
    else:
        print(f"\n[PARCIAL] X10_IE integrada con {actualizados} instituciones")
        print(f"[ESTADO] Completitud metodológica: {completitud:.1f}%")