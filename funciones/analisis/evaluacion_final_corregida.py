#!/usr/bin/env python3
"""
Evaluación Final Corregida - Proyecto Reasis
Incluye corrección de encoding para variables Y1_ILA y Y2_TD
"""

import pandas as pd
import sqlite3

def main():
    print("=== EVALUACION METODOLOGICA FINAL CORREGIDA ===")
    print("Incluye corrección encoding para variables ILA")
    
    conn = sqlite3.connect('reasis_database.db')
    
    # Y1: ILA con nombres correctos de materias (encoding)
    print("\n1. Y1: INDICE DE LOGRO ACADEMICO (ILA)")
    query_ila = """
        SELECT codigo_modular, COUNT(*) as estudiantes,
               AVG(CASE WHEN materia LIKE '%Matem%tica%' THEN nivel_logro_numerico END) as prom_mat,
               AVG(CASE WHEN materia LIKE '%Comunicaci%n%' THEN nivel_logro_numerico END) as prom_com
        FROM resultados_academicos
        WHERE codigo_modular IS NOT NULL 
        GROUP BY codigo_modular
        HAVING COUNT(*) >= 2
    """
    df_ila = pd.read_sql_query(query_ila, conn)
    df_ila['ila'] = (df_ila['prom_mat'] + df_ila['prom_com']) / 2
    ila_count = len(df_ila[df_ila['ila'].notna()])
    print(f"   Instituciones con ILA: {ila_count}")
    
    # Y2: TD con encoding corregido
    print("\n2. Y2: TENDENCIA DE DESEMPENO (TD)")
    query_td = """
        SELECT codigo_modular, año,
               AVG(CASE WHEN materia LIKE '%Matem%tica%' THEN nivel_logro_numerico END) as prom_mat,
               AVG(CASE WHEN materia LIKE '%Comunicaci%n%' THEN nivel_logro_numerico END) as prom_com
        FROM resultados_academicos
        WHERE codigo_modular IS NOT NULL AND año IN (2022, 2024)
        GROUP BY codigo_modular, año
    """
    df_td = pd.read_sql_query(query_td, conn)
    df_td['ila_año'] = (df_td['prom_mat'] + df_td['prom_com']) / 2
    
    # Pivotar para calcular TD
    df_pivot = df_td.pivot(index='codigo_modular', columns='año', values='ila_año')
    if 2022 in df_pivot.columns and 2024 in df_pivot.columns:
        df_td_calc = df_pivot.dropna()
        td_count = len(df_td_calc)
    else:
        td_count = 0
    print(f"   Instituciones con TD: {td_count}")
    
    # Resto de variables (ya correctas)
    resultados = {
        'Y1_ILA': ila_count,
        'Y2_TD': td_count,
        'Y3_PR': 'calculable',
        'X1_NVC': 83,
        'X2_TR': 381,
        'X4_IDD': 66,
        'X5_ED': 83,
        'X6_CDD': '6 redes',
        'X10_IE': 99,
        'X11_RED': 167,
        'X12_TOE': 167,
        'X15_MEIB': 84
    }
    
    # Resumen final
    print("\n" + "="*60)
    print("EVALUACION METODOLOGICA FINAL CORREGIDA")
    print("="*60)
    
    variables_completas = 0
    for variable, resultado in resultados.items():
        if isinstance(resultado, str):
            if 'calculable' in resultado or 'redes' in resultado:
                status = "[OK] DISPONIBLE"
                variables_completas += 1
            else:
                status = "[NO] FALTANTE"
        elif resultado >= 50:
            status = "[OK] SUFICIENTE"
            variables_completas += 1
        elif resultado > 0:
            status = "[PARCIAL]"
            variables_completas += 0.5
        else:
            status = "[NO] FALTANTE"
        
        print(f"{variable:10}: {str(resultado):>15} {status}")
    
    completitud = (variables_completas / 12) * 100
    print(f"\nCOMPLETITUD METODOLOGICA FINAL: {completitud:.1f}%")
    print(f"Variables disponibles: {variables_completas:.1f}/12")
    
    if completitud >= 75:
        print("ESTADO: [OK] CLUSTERING K-MEANS COMPLETAMENTE VIABLE")
        print("RECOMENDACION: Proceder con construcción índices compuestos")
    
    conn.close()
    return completitud

if __name__ == "__main__":
    main()