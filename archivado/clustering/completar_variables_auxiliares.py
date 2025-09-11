#!/usr/bin/env python3
"""
Completar variables que requieren tablas auxiliares:
Y2_TD, Y3_PR, X5_ED, X6_CDD, X10_IE, X12_TOE, X15_MEIB, X19_ORGANIZACION_PEDAGOGICA
"""

import sqlite3
import pandas as pd
import numpy as np

def completar_x5_ed():
    """Completar X5_ED desde tabla x5_ed_estabilidad_docente"""
    
    conn = sqlite3.connect('reasis_database_v4.db')
    
    print("=== COMPLETANDO X5_ED (Estabilidad Docente) ===")
    
    # Verificar datos disponibles en tabla auxiliar
    df_disponibles = pd.read_sql_query("""
        SELECT COUNT(*) as disponibles
        FROM x5_ed_estabilidad_docente
    """, conn)
    
    print(f"Registros disponibles en x5_ed_estabilidad_docente: {df_disponibles['disponibles'].iloc[0]}")
    
    # Actualizar desde tabla auxiliar
    query_update = """
    UPDATE indices_metodologicos 
    SET X5_ED = (
        SELECT x5.ratio_nombrados
        FROM x5_ed_estabilidad_docente x5
        WHERE x5.codigo_modular = indices_metodologicos.CODIGO_MODULAR
    )
    WHERE EXISTS (
        SELECT 1 FROM x5_ed_estabilidad_docente x5
        WHERE x5.codigo_modular = indices_metodologicos.CODIGO_MODULAR
    )
    """
    
    cursor = conn.cursor()
    cursor.execute(query_update)
    actualizados = cursor.rowcount
    conn.commit()
    
    print(f"[OK] {actualizados} registros actualizados con X5_ED")
    
    # Imputar faltantes por RER
    df_faltantes = pd.read_sql_query("""
        SELECT CODIGO_MODULAR, NUMERO_FYA 
        FROM indices_metodologicos 
        WHERE X5_ED IS NULL
    """, conn)
    
    imputados = 0
    for _, row in df_faltantes.iterrows():
        df_promedio = pd.read_sql_query(f"""
            SELECT AVG(X5_ED) as promedio_rer
            FROM indices_metodologicos 
            WHERE NUMERO_FYA = {row['NUMERO_FYA']} AND X5_ED IS NOT NULL
        """, conn)
        
        if len(df_promedio) > 0 and pd.notna(df_promedio['promedio_rer'].iloc[0]):
            promedio = df_promedio['promedio_rer'].iloc[0]
            cursor.execute(f"""
                UPDATE indices_metodologicos 
                SET X5_ED = {promedio:.3f}
                WHERE CODIGO_MODULAR = '{row['CODIGO_MODULAR']}'
            """)
            imputados += 1
    
    conn.commit()
    print(f"[OK] {imputados} registros imputados por promedio RER")
    
    conn.close()
    return actualizados + imputados

def completar_x15_meib():
    """Completar X15_MEIB desde tabla datos_eib_minedu"""
    
    conn = sqlite3.connect('reasis_database_v4.db')
    
    print("\n=== COMPLETANDO X15_MEIB (Modalidad EIB) ===")
    
    # Codificación modalidad EIB
    codificacion_eib = {
        'EIB de fortalecimiento': 1,
        'EIB de revitalización': 2
    }
    
    # Actualizar desde datos_eib_minedu
    df_eib = pd.read_sql_query("""
        SELECT codigo_modular, modalidad_eib
        FROM datos_eib_minedu
        WHERE modalidad_eib IS NOT NULL
    """, conn)
    
    actualizados = 0
    for _, row in df_eib.iterrows():
        if row['modalidad_eib'] in codificacion_eib:
            codigo_eib = codificacion_eib[row['modalidad_eib']]
            cursor = conn.cursor()
            cursor.execute(f"""
                UPDATE indices_metodologicos 
                SET X15_MEIB = {codigo_eib}
                WHERE CODIGO_MODULAR = '{row['codigo_modular']}'
            """)
            actualizados += 1
    
    conn.commit()
    
    # Asignar 0 (No EIB) a las instituciones restantes
    cursor.execute("""
        UPDATE indices_metodologicos 
        SET X15_MEIB = 0
        WHERE X15_MEIB IS NULL
    """)
    no_eib = cursor.rowcount
    conn.commit()
    
    print(f"[OK] {actualizados} instituciones EIB codificadas")
    print(f"[OK] {no_eib} instituciones marcadas como No EIB")
    
    conn.close()
    return actualizados + no_eib

def completar_x12_toe():
    """Completar X12_TOE desde tabla datos_toe_servicios_2024"""
    
    conn = sqlite3.connect('reasis_database_v4.db')
    
    print("\n=== COMPLETANDO X12_TOE (Tipo Organización Escolar) ===")
    
    # Verificar datos disponibles
    df_toe_disponibles = pd.read_sql_query("""
        SELECT COUNT(*) as disponibles
        FROM datos_toe_servicios_2024
    """, conn)
    
    print(f"Registros en datos_toe_servicios_2024: {df_toe_disponibles['disponibles'].iloc[0]}")
    
    # Codificación TOE
    codificacion_toe = {
        'UNIDOCENTE': 1,
        'BIDOCENTE': 2, 
        'MULTIGRADO': 3,
        'POLIDOCENTE': 4
    }
    
    # Intentar actualizar desde tabla TOE
    df_toe = pd.read_sql_query("""
        SELECT codigo_modular, tipo_organizacion_escolar
        FROM datos_toe_servicios_2024
        WHERE tipo_organizacion_escolar IS NOT NULL
    """, conn)
    
    actualizados = 0
    for _, row in df_toe.iterrows():
        toe_upper = str(row['tipo_organizacion_escolar']).upper()
        if toe_upper in codificacion_toe:
            codigo_toe = codificacion_toe[toe_upper]
            cursor = conn.cursor()
            cursor.execute(f"""
                UPDATE indices_metodologicos 
                SET X12_TOE = {codigo_toe}
                WHERE CODIGO_MODULAR = '{row['codigo_modular']}'
            """)
            actualizados += 1
    
    conn.commit()
    
    # Imputar por RER para faltantes
    df_faltantes = pd.read_sql_query("""
        SELECT CODIGO_MODULAR, NUMERO_FYA
        FROM indices_metodologicos 
        WHERE X12_TOE IS NULL
    """, conn)
    
    imputados = 0
    for _, row in df_faltantes.iterrows():
        # Buscar modo más común en la RER
        df_modo = pd.read_sql_query(f"""
            SELECT X12_TOE, COUNT(*) as freq
            FROM indices_metodologicos 
            WHERE NUMERO_FYA = {row['NUMERO_FYA']} AND X12_TOE IS NOT NULL
            GROUP BY X12_TOE
            ORDER BY freq DESC
            LIMIT 1
        """, conn)
        
        if len(df_modo) > 0:
            modo_toe = df_modo['X12_TOE'].iloc[0]
            cursor = conn.cursor()
            cursor.execute(f"""
                UPDATE indices_metodologicos 
                SET X12_TOE = {modo_toe}
                WHERE CODIGO_MODULAR = '{row['CODIGO_MODULAR']}'
            """)
            imputados += 1
        else:
            # Valor por defecto: MULTIGRADO (común en rural)
            cursor = conn.cursor()
            cursor.execute(f"""
                UPDATE indices_metodologicos 
                SET X12_TOE = 3
                WHERE CODIGO_MODULAR = '{row['CODIGO_MODULAR']}'
            """)
            imputados += 1
    
    conn.commit()
    print(f"[OK] {actualizados} registros desde tabla TOE")
    print(f"[OK] {imputados} registros imputados por RER/defecto")
    
    conn.close()
    return actualizados + imputados

def completar_x6_cdd():
    """Completar X6_CDD desde competencia digital por red"""
    
    conn = sqlite3.connect('reasis_database_v4.db')
    
    print("\n=== COMPLETANDO X6_CDD (Competencia Digital Docente) ===")
    
    # Verificar si ya existe competencia_digital_docente_promedio_red en instituciones_educativas
    df_disponible = pd.read_sql_query("""
        SELECT COUNT(*) as con_cdd
        FROM instituciones_educativas
        WHERE competencia_digital_docente_promedio_red IS NOT NULL
    """, conn)
    
    print(f"Registros con CDD en instituciones_educativas: {df_disponible['con_cdd'].iloc[0]}")
    
    # Actualizar desde instituciones_educativas
    query_update = """
    UPDATE indices_metodologicos 
    SET X6_CDD = (
        SELECT ie.competencia_digital_docente_promedio_red
        FROM instituciones_educativas ie
        WHERE ie.codigo_modular = indices_metodologicos.CODIGO_MODULAR
        AND ie.competencia_digital_docente_promedio_red IS NOT NULL
    )
    WHERE EXISTS (
        SELECT 1 FROM instituciones_educativas ie
        WHERE ie.codigo_modular = indices_metodologicos.CODIGO_MODULAR
        AND ie.competencia_digital_docente_promedio_red IS NOT NULL
    )
    """
    
    cursor = conn.cursor()
    cursor.execute(query_update)
    actualizados = cursor.rowcount
    conn.commit()
    
    print(f"[OK] {actualizados} registros actualizados con X6_CDD")
    
    conn.close()
    return actualizados

def completar_x19_organizacion():
    """Completar X19_ORGANIZACION_PEDAGOGICA basado en X12_TOE"""
    
    conn = sqlite3.connect('reasis_database_v4.db')
    
    print("\n=== COMPLETANDO X19_ORGANIZACION_PEDAGOGICA ===")
    
    # Mapeo TOE -> Organización Pedagógica
    # 1=UNIDOCENTE->1, 2=BIDOCENTE->2, 3=MULTIGRADO->2, 4=POLIDOCENTE->3
    query_update = """
    UPDATE indices_metodologicos 
    SET X19_ORGANIZACION_PEDAGOGICA = (
        CASE 
            WHEN X12_TOE = 1 THEN 1  -- Unidocente
            WHEN X12_TOE IN (2, 3) THEN 2  -- Bidocente/Multigrado  
            WHEN X12_TOE = 4 THEN 3  -- Polidocente
            ELSE 2  -- Por defecto multigrado
        END
    )
    WHERE X12_TOE IS NOT NULL
    """
    
    cursor = conn.cursor()
    cursor.execute(query_update)
    actualizados = cursor.rowcount
    conn.commit()
    
    print(f"[OK] {actualizados} registros calculados desde X12_TOE")
    
    conn.close()
    return actualizados

def verificar_progreso_auxiliares():
    """Verificar progreso de variables auxiliares"""
    
    conn = sqlite3.connect('reasis_database_v4.db')
    
    print("\n=== VERIFICACION VARIABLES AUXILIARES ===")
    
    variables_auxiliares = ['X5_ED', 'X6_CDD', 'X12_TOE', 'X15_MEIB', 'X19_ORGANIZACION_PEDAGOGICA']
    
    df_total = pd.read_sql_query("SELECT COUNT(*) as total FROM indices_metodologicos", conn)
    total = df_total['total'].iloc[0]
    
    for variable in variables_auxiliares:
        df_completos = pd.read_sql_query(f"""
            SELECT COUNT(*) as completos 
            FROM indices_metodologicos 
            WHERE {variable} IS NOT NULL
        """, conn)
        completos = df_completos['completos'].iloc[0]
        completitud = (completos / total) * 100
        
        status = "[COMPLETO]" if completitud == 100 else f"[{completitud:.1f}%]"
        print(f"  {status} {variable}: {completos}/{total}")
    
    conn.close()

def main():
    """Función principal"""
    
    print("COMPLETAR VARIABLES QUE REQUIEREN TABLAS AUXILIARES")
    print("=" * 65)
    
    try:
        # Completar variables auxiliares una por una
        print("Procesando variables auxiliares:")
        
        completar_x5_ed()
        completar_x15_meib() 
        completar_x12_toe()
        completar_x6_cdd()
        completar_x19_organizacion()
        
        # Verificar progreso
        verificar_progreso_auxiliares()
        
        print("\n" + "=" * 65)
        print("[PROGRESO] Variables auxiliares procesadas")
        print("Pendientes: Y2_TD, Y3_PR, X10_IE (requieren cálculo especial)")
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()