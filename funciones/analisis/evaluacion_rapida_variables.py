#!/usr/bin/env python3
"""
Evaluación rápida de variables metodológicas con nombres correctos
"""
import sqlite3
import pandas as pd

def evaluacion_rapida():
    print("=== EVALUACION RAPIDA VARIABLES METODOLOGICAS ===")
    
    conn = sqlite3.connect('reasis_database.db')
    
    # Y1: ILA - Usando nombres correctos
    print("\n1. Y1: ILA")
    query = "SELECT COUNT(DISTINCT codigo_modular) as total FROM resultados_academicos WHERE codigo_modular IS NOT NULL"
    ila_instituciones = pd.read_sql_query(query, conn).iloc[0]['total']
    
    query_estudiantes = "SELECT COUNT(*) as total FROM resultados_academicos WHERE codigo_modular IS NOT NULL"
    ila_estudiantes = pd.read_sql_query(query_estudiantes, conn).iloc[0]['total']
    
    print(f"   Instituciones: {ila_instituciones}")
    print(f"   Estudiantes: {ila_estudiantes:,}")
    
    # Y2: TD - Verificar años disponibles
    print("\n2. Y2: TD")
    query = "SELECT DISTINCT año FROM resultados_academicos ORDER BY año"
    años = pd.read_sql_query(query, conn)['año'].tolist()
    print(f"   Años disponibles: {años}")
    
    if 2022 in años and 2024 in años:
        query = """
            SELECT COUNT(DISTINCT codigo_modular) as total 
            FROM resultados_academicos 
            WHERE año IN (2022, 2024) AND codigo_modular IS NOT NULL
        """
        td_instituciones = pd.read_sql_query(query, conn).iloc[0]['total']
        print(f"   Instituciones con datos 2022-2024: {td_instituciones}")
    else:
        print("   No hay datos suficientes para TD")
    
    # Y3: PR
    print("\n3. Y3: PR - Calculable con regresion")
    
    # X1: NVC
    print("\n4. X1: NVC")
    query = "SELECT COUNT(*) as total FROM datos_eib_minedu WHERE quintil_pobreza IS NOT NULL"
    nvc = pd.read_sql_query(query, conn).iloc[0]['total']
    print(f"   Instituciones con quintil: {nvc}")
    
    # X2: TR  
    print("\n5. X2: TR")
    query = "SELECT COUNT(*) as total FROM instituciones_educativas WHERE area_censo IS NOT NULL"
    tr = pd.read_sql_query(query, conn).iloc[0]['total']
    print(f"   Instituciones con ruralidad: {tr}")
    
    # X4: IDD
    print("\n6. X4: IDD") 
    query = "SELECT COUNT(DISTINCT codigo_modular_vinculado) as total FROM docentes_data WHERE codigo_modular_vinculado IS NOT NULL"
    idd = pd.read_sql_query(query, conn).iloc[0]['total']
    print(f"   Instituciones con docentes: {idd}")
    
    # X5: ED
    print("\n7. X5: ED")
    query = "SELECT COUNT(*) as total FROM x5_ed_estabilidad_docente"
    ed = pd.read_sql_query(query, conn).iloc[0]['total']
    print(f"   Instituciones con estabilidad: {ed}")
    
    # X6: CDD
    print("\n8. X6: CDD")
    query = "SELECT COUNT(DISTINCT codigo_red) as total FROM competencia_digital_docentes"
    cdd = pd.read_sql_query(query, conn).iloc[0]['total']
    print(f"   Redes con comp digital: {cdd}")
    
    # X10: IE
    print("\n9. X10: IE")
    query1 = "SELECT COUNT(*) as total FROM datos_eib_minedu WHERE servicios_agua IS NOT NULL OR servicios_internet IS NOT NULL"
    query2 = "SELECT COUNT(DISTINCT codigo_modular) as total FROM conectividad_equipamiento"
    
    servicios = pd.read_sql_query(query1, conn).iloc[0]['total']
    conectividad = pd.read_sql_query(query2, conn).iloc[0]['total']
    ie_total = max(servicios, conectividad)
    print(f"   Servicios básicos: {servicios}")
    print(f"   Conectividad: {conectividad}")
    print(f"   Total IE: {ie_total}")
    
    # X11: RED
    print("\n10. X11: RED")
    query = "SELECT COUNT(*) as total FROM datos_toe_servicios_2024 WHERE estudiantes_2024 IS NOT NULL"
    red = pd.read_sql_query(query, conn).iloc[0]['total']
    print(f"   Instituciones con estudiantes: {red}")
    
    # X12: TOE  
    print("\n11. X12: TOE")
    query = "SELECT COUNT(*) as total FROM datos_toe_servicios_2024 WHERE tipo_organizacion_normalizado IS NOT NULL"
    toe = pd.read_sql_query(query, conn).iloc[0]['total']
    print(f"   Instituciones con TOE: {toe}")
    
    # X15: MEIB
    print("\n12. X15: MEIB")
    query = "SELECT COUNT(*) as total FROM datos_eib_minedu WHERE modalidad_eib IS NOT NULL"
    meib = pd.read_sql_query(query, conn).iloc[0]['total']
    print(f"   Instituciones con modalidad EIB: {meib}")
    
    conn.close()
    
    # RESUMEN
    print("\n" + "="*50)
    print("RESUMEN EVALUACION METODOLOGICA")
    print("="*50)
    
    variables = {
        'Y1_ILA': ila_instituciones,
        'Y2_TD': td_instituciones if 'td_instituciones' in locals() else 0,
        'Y3_PR': 'calculable',
        'X1_NVC': nvc,
        'X2_TR': tr, 
        'X4_IDD': idd,
        'X5_ED': ed,
        'X6_CDD': cdd,
        'X10_IE': ie_total,
        'X11_RED': red,
        'X12_TOE': toe,
        'X15_MEIB': meib
    }
    
    print("\nCOMPLETITUD POR VARIABLE:")
    print("-" * 30)
    
    completas = 0
    for var, valor in variables.items():
        if isinstance(valor, str):
            status = "[OK]" if 'calculable' in valor else "[NO]"
            if 'calculable' in valor:
                completas += 1
        elif valor >= 50:
            status = "[OK]"
            completas += 1
        elif valor > 0:
            status = "[PARCIAL]"
            completas += 0.5
        else:
            status = "[NO]"
        
        print(f"{var:8}: {str(valor):>10} {status}")
    
    completitud = (completas / 12) * 100
    print(f"\nCOMPLETITUD TOTAL: {completitud:.1f}%")
    print(f"Variables completas: {completas}/12")
    
    if completitud >= 75:
        print("ESTADO: [OK] CLUSTERING VIABLE")
    elif completitud >= 50:
        print("ESTADO: [PARCIAL] NECESITA MEJORAS")
    else:
        print("ESTADO: [NO] REQUIERE TRABAJO ADICIONAL")
    
    return completitud

if __name__ == "__main__":
    evaluacion_rapida()