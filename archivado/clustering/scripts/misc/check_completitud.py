#!/usr/bin/env python3
"""
Script temporal para verificar completitud de variables metodológicas
"""

import sqlite3
import pandas as pd

def check_completitud():
    conn = sqlite3.connect('reasis_database.db')
    
    # Query para completitud
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
    
    print("COMPLETITUD VARIABLES METODOLOGICAS (% datos disponibles):")
    print("=" * 60)
    
    variables_disponibles = 0
    total_variables = 12
    
    for col in df_completitud.columns:
        if col != 'total_registros':
            completitud_pct = df_completitud[col].iloc[0]
            if completitud_pct >= 50:
                status = "[OK] SUFICIENTE"
                variables_disponibles += 1
            elif completitud_pct > 0:
                status = "[PARCIAL]"
                variables_disponibles += 0.5
            else:
                status = "[NO] FALTANTE"
            
            print(f"{col}: {completitud_pct:.1f}% {status}")
    
    total_registros = df_completitud['total_registros'].iloc[0]
    completitud_general = (variables_disponibles / total_variables) * 100
    
    print("=" * 60)
    print(f"TOTAL REGISTROS: {total_registros}")
    print(f"VARIABLES DISPONIBLES: {variables_disponibles:.1f} / {total_variables}")
    print(f"COMPLETITUD GENERAL: {completitud_general:.1f}%")
    
    if completitud_general >= 75:
        print("VIABILIDAD CLUSTERING: [OK] VIABLE")
    elif completitud_general >= 50:
        print("VIABILIDAD CLUSTERING: [PARCIAL] LIMITADA")
    else:
        print("VIABILIDAD CLUSTERING: [NO] INSUFICIENTE")
    
    conn.close()
    return completitud_general, variables_disponibles

if __name__ == "__main__":
    check_completitud()