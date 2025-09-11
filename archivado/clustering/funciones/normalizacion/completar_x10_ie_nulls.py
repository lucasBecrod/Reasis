"""
Script para completar los 5 valores NULL restantes en X10_IE
Aplicando imputación por ruralidad para alcanzar 100% completitud

Autor: Proyecto Reasis
Fecha: 2025-08-10
"""

import sqlite3
import pandas as pd
from datetime import datetime

def completar_x10_ie_nulls():
    """
    Completa los 5 valores NULL en X10_IE usando promedios por ruralidad
    """
    
    print("=== COMPLETANDO X10_IE NULL PARA 100% COMPLETITUD ===\n")
    
    conn = sqlite3.connect('reasis_database.db')
    cursor = conn.cursor()
    
    # 1. Identificar instituciones con X10_IE NULL
    print("1. IDENTIFICANDO INSTITUCIONES CON X10_IE NULL:")
    
    df_nulls = pd.read_sql_query("""
        SELECT CODIGO_MODULAR, NOMBRE_INSTITUCION, NUMERO_FYA, X2_TR 
        FROM indices_metodologicos 
        WHERE X10_IE IS NULL
    """, conn)
    
    print(f"   Instituciones con X10_IE NULL: {len(df_nulls)}")
    
    for _, row in df_nulls.iterrows():
        red = row['NUMERO_FYA'] if pd.notna(row['NUMERO_FYA']) else 'Sin Red'
        ruralidad = "Urbano" if row['X2_TR'] == 1 else "Rural" if row['X2_TR'] == 2 else "Otro"
        print(f"   - {row['CODIGO_MODULAR']}: {row['NOMBRE_INSTITUCION']}")
        print(f"     Red: {red}, Ruralidad: {ruralidad} (X2_TR={row['X2_TR']})")
    
    # 2. Calcular promedios de imputación por ruralidad
    print(f"\n2. CALCULANDO PROMEDIOS POR RURALIDAD:")
    
    promedios = pd.read_sql_query("""
        SELECT 
            X2_TR,
            COUNT(*) as instituciones,
            AVG(X10_IE) as promedio_x10ie,
            MIN(X10_IE) as min_x10ie,
            MAX(X10_IE) as max_x10ie,
            CASE X2_TR 
                WHEN 1 THEN 'Urbano'
                WHEN 2 THEN 'Rural'
                ELSE 'Otro'
            END as tipo_ruralidad
        FROM indices_metodologicos 
        WHERE X10_IE IS NOT NULL AND X2_TR IS NOT NULL
        GROUP BY X2_TR
        ORDER BY X2_TR
    """, conn)
    
    print(f"   Promedios calculados:")
    valores_imputacion = {}
    
    for _, row in promedios.iterrows():
        valores_imputacion[row['X2_TR']] = row['promedio_x10ie']
        print(f"   - {row['tipo_ruralidad']} (X2_TR={row['X2_TR']}): {row['promedio_x10ie']:.4f}")
        print(f"     Basado en {row['instituciones']} instituciones")
        print(f"     Rango: {row['min_x10ie']:.4f} - {row['max_x10ie']:.4f}")
    
    # 3. Crear respaldo antes de actualización
    print(f"\n3. CREANDO RESPALDO:")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"data/backups/indices_metodologicos_pre_x10ie_complete_{timestamp}.csv"
    
    df_backup = pd.read_sql_query("SELECT * FROM indices_metodologicos", conn)
    df_backup.to_csv(backup_path, index=False)
    
    print(f"   Respaldo creado: {backup_path}")
    
    # 4. Aplicar imputación
    print(f"\n4. APLICANDO IMPUTACIÓN:")
    
    actualizaciones_exitosas = 0
    
    for _, row in df_nulls.iterrows():
        codigo_modular = row['CODIGO_MODULAR']
        ruralidad = row['X2_TR']
        
        if ruralidad in valores_imputacion:
            valor_imputado = valores_imputacion[ruralidad]
            tipo_ruralidad = "Urbano" if ruralidad == 1 else "Rural"
            
            try:
                cursor.execute("""
                    UPDATE indices_metodologicos 
                    SET X10_IE = ?
                    WHERE CODIGO_MODULAR = ? AND X10_IE IS NULL
                """, (valor_imputado, codigo_modular))
                
                if cursor.rowcount > 0:
                    actualizaciones_exitosas += 1
                    print(f"   [OK] {codigo_modular}: X10_IE = {valor_imputado:.4f} ({tipo_ruralidad})")
                else:
                    print(f"   [ERROR] {codigo_modular}: No se pudo actualizar")
                    
            except Exception as e:
                print(f"   [ERROR] {codigo_modular}: Error - {str(e)}")
        else:
            print(f"   [WARN] {codigo_modular}: Ruralidad {ruralidad} no encontrada en promedios")
    
    conn.commit()
    
    print(f"\n   Actualizaciones exitosas: {actualizaciones_exitosas}/{len(df_nulls)}")
    
    # 5. Verificar resultado final
    print(f"\n5. VERIFICACIÓN FINAL:")
    
    result = cursor.execute("""
        SELECT COUNT(*) total,
               COUNT(X10_IE) con_x10_ie,
               COUNT(*) - COUNT(X10_IE) sin_x10_ie
        FROM indices_metodologicos
    """).fetchone()
    
    print(f"   Total instituciones: {result[0]}")
    print(f"   Con X10_IE: {result[1]} ({result[1]/result[0]*100:.1f}%)")
    print(f"   Sin X10_IE: {result[2]}")
    
    # 6. Estadísticas finales X10_IE
    if result[2] == 0:  # Sin NULL
        print(f"\n6. ESTADÍSTICAS X10_IE COMPLETAS:")
        
        stats = cursor.execute("""
            SELECT 
                MIN(X10_IE) as minimo,
                MAX(X10_IE) as maximo,
                AVG(X10_IE) as promedio,
                COUNT(X10_IE) as total_con_datos
            FROM indices_metodologicos
        """).fetchone()
        
        print(f"   Mínimo: {stats[0]:.4f}")
        print(f"   Máximo: {stats[1]:.4f}")
        print(f"   Promedio: {stats[2]:.4f}")
        print(f"   Instituciones: {stats[3]}/184 (100%)")
        
        # Verificar coherencia por ruralidad final
        print(f"\n7. COHERENCIA FINAL POR RURALIDAD:")
        
        coherencia_final = cursor.execute("""
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
        
        for x2_tr, instituciones, x10_prom, tipo in coherencia_final:
            print(f"   {tipo} (X2_TR={x2_tr}): {instituciones} inst., X10_IE prom = {x10_prom:.4f}")
    
    # 7. Verificación completitud metodológica total
    print(f"\n8. COMPLETITUD METODOLÓGICA TOTAL:")
    
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
    
    df_completitud_final = pd.read_sql_query(completitud_query, conn)
    
    variables_completas = 0
    total_variables = 12
    
    print(f"   Variables metodológicas (% completitud):")
    for col in df_completitud_final.columns:
        if col != 'total_registros':
            completitud_pct = df_completitud_final[col].iloc[0]
            if completitud_pct == 100.0:
                variables_completas += 1
                status = "COMPLETA"
            elif completitud_pct >= 95.0:
                variables_completas += 0.9
                status = "CASI COMPLETA"
            else:
                variables_completas += completitud_pct / 100.0
                status = "PARCIAL"
            
            marca = "*" if col == 'X10_IE' else " "
            print(f"   {marca} {col}: {completitud_pct:.1f}% {status}")
    
    completitud_general = (variables_completas / total_variables) * 100
    
    print(f"\n   COMPLETITUD METODOLÓGICA FINAL: {completitud_general:.1f}%")
    print(f"   VARIABLES COMPLETAS: {variables_completas:.1f} / {total_variables}")
    
    if completitud_general >= 99.5:
        print(f"   [PERFECTO] Metodología 100% completa")
        estado_final = "PERFECTO"
    elif completitud_general >= 95.0:
        print(f"   [EXCELENTE] Metodología casi completa")
        estado_final = "EXCELENTE"
    else:
        print(f"   [BUENO] Metodología suficiente")
        estado_final = "BUENO"
    
    # 8. Respaldo final
    print(f"\n9. RESPALDO FINAL:")
    
    backup_final_path = f"data/backups/indices_metodologicos_x10ie_100_completo_{timestamp}.csv"
    df_backup_final = pd.read_sql_query("SELECT * FROM indices_metodologicos", conn)
    df_backup_final.to_csv(backup_final_path, index=False)
    
    print(f"   Respaldo final: {backup_final_path}")
    
    conn.close()
    
    exito_total = result[2] == 0  # Sin NULL restantes
    
    print(f"\n[{estado_final}] X10_IE COMPLETITUD ALCANZADA")
    print(f"[RESULTADO] {result[1]}/{result[0]} instituciones con X10_IE")
    
    return exito_total, actualizaciones_exitosas, completitud_general

if __name__ == "__main__":
    exito, actualizados, completitud = completar_x10_ie_nulls()
    
    print(f"\n=== RESULTADO FINAL COMPLETITUD X10_IE ===")
    print(f"Instituciones completadas: {actualizados}")
    print(f"Completitud metodológica: {completitud:.1f}%")
    
    if exito and completitud >= 99.5:
        print(f"\n[MILESTONE] COMPLETITUD 100% ALCANZADA")
        print(f"[ÉXITO] X10_IE completamente sin NULL")
        print(f"[CLUSTERING] Metodología perfecta para análisis avanzado")
    else:
        print(f"\n[PARCIAL] Completitud mejorada significativamente")
        print(f"[ESTADO] X10_IE con mínimos NULL restantes")