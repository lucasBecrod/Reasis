#!/usr/bin/env python3
"""
Completar los últimos registros faltantes (3040177, 1678861) 
para alcanzar 100% completitud en todas las variables
"""

import sqlite3
import pandas as pd

def completar_registros_faltantes():
    """Completar las 4 variables faltantes para códigos 3040177 y 1678861"""
    
    conn = sqlite3.connect('reasis_database_v4.db')
    
    print("=== COMPLETANDO ULTIMOS REGISTROS FALTANTES ===")
    print("Códigos: 3040177, 1678861 (RER 54)")
    
    codigos_faltantes = ['3040177', '1678861']
    variables_completar = ['Y2_TD', 'X6_CDD', 'X13_TMATRC', 'X19_ORGANIZACION_PEDAGOGICA']
    
    # Obtener promedios de RER 54 para imputación
    print("\nCalculando promedios RER 54:")
    
    promedios_rer54 = {}
    for variable in variables_completar:
        df_promedio = pd.read_sql_query(f"""
            SELECT AVG({variable}) as promedio_rer54
            FROM indices_metodologicos 
            WHERE NUMERO_FYA = 54 AND {variable} IS NOT NULL
        """, conn)
        
        if len(df_promedio) > 0 and pd.notna(df_promedio['promedio_rer54'].iloc[0]):
            promedios_rer54[variable] = df_promedio['promedio_rer54'].iloc[0]
            print(f"  {variable}: {promedios_rer54[variable]:.3f}")
        else:
            # Valores por defecto si no hay datos en RER 54
            valores_defecto = {
                'Y2_TD': 1.0,  # Tendencia estable
                'X6_CDD': 3.0,  # Competencia digital media
                'X13_TMATRC': 0.0,  # Sin tendencia matrícula
                'X19_ORGANIZACION_PEDAGOGICA': 2  # Multigrado (común en rural)
            }
            promedios_rer54[variable] = valores_defecto[variable]
            print(f"  {variable}: {promedios_rer54[variable]:.3f} (defecto)")
    
    # Completar cada código
    total_actualizados = 0
    
    for codigo in codigos_faltantes:
        print(f"\nCompletando CODIGO {codigo}:")
        
        for variable in variables_completar:
            valor = promedios_rer54[variable]
            
            # Usar valor entero para variables categóricas
            if variable in ['Y2_TD', 'X19_ORGANIZACION_PEDAGOGICA']:
                valor = int(round(valor))
            
            cursor = conn.cursor()
            cursor.execute(f"""
                UPDATE indices_metodologicos 
                SET {variable} = {valor}
                WHERE CODIGO_MODULAR = '{codigo}'
            """)
            
            print(f"  {variable}: {valor}")
            total_actualizados += 1
    
    conn.commit()
    print(f"\n[OK] {total_actualizados} valores actualizados")
    
    conn.close()
    return total_actualizados

def verificar_completitud_100():
    """Verificar que todas las variables están al 100%"""
    
    conn = sqlite3.connect('reasis_database_v4.db')
    
    print("\n=== VERIFICACION COMPLETITUD 100% ===")
    
    variables_verificar = [
        'Y1_ILA', 'Y2_TD', 'Y3_PR', 
        'X1_NVC', 'X2_TR', 'X4_IDD', 'X5_ED', 'X6_CDD', 
        'X10_IE', 'X11_RED', 'X12_TOE', 'X13_TMATRC',
        'X14_NIVEL_EDUCATIVO', 'X15_MEIB', 'X16_MODALIDAD', 'X17_GESTION',
        'X18_TURNO', 'X19_ORGANIZACION_PEDAGOGICA', 'X20_DIRECTIVOS_TOTAL',
        'X21_MULTIPLICIDAD1', 'X22_MULTIPLICIDAD2', 'X24_GPMD', 'X25_POBLACION_DISTRITO'
    ]
    
    df_total = pd.read_sql_query("SELECT COUNT(*) as total FROM indices_metodologicos", conn)
    total = df_total['total'].iloc[0]
    
    variables_100 = 0
    variables_problematicas = []
    
    print(f"Total instituciones: {total}")
    print("\nEstado final:")
    
    for variable in variables_verificar:
        df_completos = pd.read_sql_query(f"""
            SELECT COUNT(*) as completos 
            FROM indices_metodologicos 
            WHERE {variable} IS NOT NULL
        """, conn)
        completos = df_completos['completos'].iloc[0]
        
        if completos == total:
            variables_100 += 1
            print(f"  [100%] {variable}")
        else:
            variables_problematicas.append(variable)
            completitud = (completos / total) * 100
            print(f"  [{completitud:.1f}%] {variable}: {completos}/{total}")
    
    print(f"\n[RESULTADO FINAL]")
    print(f"  Variables completas al 100%: {variables_100}/{len(variables_verificar)}")
    print(f"  Completitud total: {(variables_100/len(variables_verificar))*100:.1f}%")
    
    if len(variables_problematicas) == 0:
        print(f"  [EXITO] Todas las variables están completas al 100%")
        print(f"  [LISTO] Base de datos preparada para clustering final")
    else:
        print(f"  [PENDIENTE] Variables incompletas: {variables_problematicas}")
    
    conn.close()
    
    return variables_100 == len(variables_verificar)

def main():
    """Función principal"""
    
    print("COMPLETAR ULTIMOS REGISTROS FALTANTES")
    print("=" * 50)
    print("Objetivo: Alcanzar 100% completitud en todas las variables")
    
    try:
        # Completar registros faltantes
        total_actualizados = completar_registros_faltantes()
        
        # Verificar completitud final
        completitud_100 = verificar_completitud_100()
        
        print("\n" + "=" * 50)
        if completitud_100:
            print("[EXITO TOTAL] 100% COMPLETITUD ALCANZADA")
            print("[OBJETIVO LOGRADO] 163 instituciones RER con todas las variables")
            print("[LISTO] Base de datos preparada para clustering definitivo")
        else:
            print("[PROGRESO] Completitud mejorada significativamente")
            print("[ACCION] Revisar variables restantes")
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()