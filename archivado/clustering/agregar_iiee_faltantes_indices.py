#!/usr/bin/env python3
"""
Agregar las 2 instituciones faltantes (3040177, 1678861) a la tabla indices_metodologicos
con valores imputados contextualmente basados en RER 54, Ancash
"""

import sqlite3
import pandas as pd
import numpy as np

def obtener_contexto_rer54():
    """Obtener valores promedio de instituciones RER 54 similares para imputación"""
    
    conn = sqlite3.connect('reasis_database_v4.db')
    
    print("=== ANALISIS CONTEXTUAL RER 54 ===")
    
    # Buscar instituciones RER 54 en indices_metodologicos para contexto
    df_rer54 = pd.read_sql_query("""
        SELECT * FROM indices_metodologicos 
        WHERE NUMERO_FYA = '54'
    """, conn)
    
    print(f"Instituciones RER 54 encontradas: {len(df_rer54)}")
    
    if len(df_rer54) > 0:
        # Calcular promedios para variables numéricas
        contexto = {
            'Y1_ILA': df_rer54['Y1_ILA'].mean() if df_rer54['Y1_ILA'].notna().any() else None,
            'X1_NVC': df_rer54['X1_NVC'].mode().iloc[0] if df_rer54['X1_NVC'].notna().any() else 4,  # Alta vulnerabilidad
            'X2_TR': 2,  # Rural (RER es rural por definición)
            'X4_IDD': df_rer54['X4_IDD'].mean() if 'X4_IDD' in df_rer54.columns and df_rer54['X4_IDD'].notna().any() else None,
            'X11_RED': df_rer54['X11_RED_ajustado'].mean() if 'X11_RED_ajustado' in df_rer54.columns and df_rer54['X11_RED_ajustado'].notna().any() else None,
            'ALTITUD_MSNM': df_rer54['ALTITUD_MSNM'].mean() if df_rer54['ALTITUD_MSNM'].notna().any() else 3500.0
        }
        
        print("Contexto RER 54 calculado:")
        for var, val in contexto.items():
            if val is not None:
                print(f"  {var}: {val:.3f}" if isinstance(val, float) else f"  {var}: {val}")
    else:
        # Valores por defecto basados en conocimiento de Ancash rural
        contexto = {
            'Y1_ILA': None,  # Se calculará específicamente
            'X1_NVC': 4,  # Alta vulnerabilidad (común en zona rural)
            'X2_TR': 2,  # Rural
            'X4_IDD': None,  # No disponible
            'X11_RED': 15.0,  # Ratio promedio rural
            'ALTITUD_MSNM': 3500.0  # Altitud Ancash
        }
        print("Usando contexto por defecto (no hay RER 54 en indices)")
    
    conn.close()
    return contexto

def agregar_instituciones_faltantes():
    """Agregar las 2 instituciones faltantes a indices_metodologicos"""
    
    conn = sqlite3.connect('reasis_database_v4.db')
    
    # Obtener contexto para imputación
    contexto = obtener_contexto_rer54()
    
    # Datos específicos de las instituciones
    instituciones_faltantes = {
        '3040177': {
            'NOMBRE_INSTITUCION': '87009-01 HUANCHUY',
            'NUMERO_FYA': '54',
            'NIVEL_EDUCATIVO': 'Secundaria'
        },
        '1678861': {
            'NOMBRE_INSTITUCION': '692 - CAJAY',
            'NUMERO_FYA': '54', 
            'NIVEL_EDUCATIVO': 'Inicial'
        }
    }
    
    print("\n=== AGREGANDO INSTITUCIONES FALTANTES ===")
    
    for codigo, datos in instituciones_faltantes.items():
        print(f"\nAgregando CODIGO {codigo}:")
        
        # Obtener datos adicionales de instituciones_educativas
        df_ie = pd.read_sql_query(f"""
            SELECT latitud, longitud, altitud, distrito, provincia
            FROM instituciones_educativas 
            WHERE codigo_modular = '{codigo}'
        """, conn)
        
        if len(df_ie) > 0:
            ie_data = df_ie.iloc[0]
            latitud = ie_data['latitud'] if pd.notna(ie_data['latitud']) else -9.0  # Ancash aprox
            longitud = ie_data['longitud'] if pd.notna(ie_data['longitud']) else -77.5  # Ancash aprox  
            altitud = ie_data['altitud'] if pd.notna(ie_data['altitud']) else contexto['ALTITUD_MSNM']
        else:
            latitud, longitud, altitud = -9.0, -77.5, contexto['ALTITUD_MSNM']
        
        # Preparar INSERT con valores contextuales
        query_insert = f"""
        INSERT INTO indices_metodologicos (
            CODIGO_MODULAR, NOMBRE_INSTITUCION, NUMERO_FYA,
            LATITUD, LONGITUD, ALTITUD_MSNM,
            Y1_ILA, X1_NVC, X2_TR, X11_RED_ajustado
        ) VALUES (
            '{codigo}',
            '{datos["NOMBRE_INSTITUCION"]}',
            '{datos["NUMERO_FYA"]}',
            {latitud},
            {longitud}, 
            {altitud},
            {contexto['Y1_ILA'] if contexto['Y1_ILA'] is not None else 'NULL'},
            {contexto['X1_NVC']},
            {contexto['X2_TR']},
            {contexto['X11_RED'] if contexto['X11_RED'] is not None else 'NULL'}
        )
        """
        
        try:
            cursor = conn.cursor()
            cursor.execute(query_insert)
            conn.commit()
            print(f"  [OK] {codigo} agregado exitosamente")
            print(f"    - Nombre: {datos['NOMBRE_INSTITUCION']}")
            print(f"    - RER: {datos['NUMERO_FYA']}")
            print(f"    - X1_NVC: {contexto['X1_NVC']} (vulnerabilidad)")
            print(f"    - X2_TR: {contexto['X2_TR']} (rural)")
            
        except Exception as e:
            print(f"  [ERROR] Error insertando {codigo}: {e}")
    
    conn.close()

def verificar_insercion_final():
    """Verificar que las instituciones se agregaron correctamente"""
    
    conn = sqlite3.connect('reasis_database_v4.db')
    
    print("\n=== VERIFICACION FINAL ===")
    
    # Verificar instituciones agregadas
    df_agregadas = pd.read_sql_query("""
        SELECT CODIGO_MODULAR, NOMBRE_INSTITUCION, NUMERO_FYA, 
               Y1_ILA, X1_NVC, X2_TR, X11_RED_ajustado
        FROM indices_metodologicos 
        WHERE CODIGO_MODULAR IN ('3040177', '1678861')
    """, conn)
    
    if len(df_agregadas) == 2:
        print("[OK] Ambas instituciones agregadas correctamente:")
        for _, row in df_agregadas.iterrows():
            print(f"  CODIGO {row['CODIGO_MODULAR']}:")
            print(f"    - Nombre: {row['NOMBRE_INSTITUCION']}")
            print(f"    - RER: {row['NUMERO_FYA']}")
            print(f"    - Variables: Y1_ILA={row['Y1_ILA']}, X1_NVC={row['X1_NVC']}, X2_TR={row['X2_TR']}")
    else:
        print(f"[ERROR] Solo {len(df_agregadas)} de 2 instituciones agregadas")
    
    # Verificar total final
    df_total = pd.read_sql_query("SELECT COUNT(*) as total FROM indices_metodologicos", conn)
    total_final = df_total['total'].iloc[0]
    print(f"\n[RESUMEN] Total instituciones en indices_metodologicos: {total_final}")
    
    if total_final == 163:
        print("[EXITO] Se alcanzó el objetivo de 163 instituciones RER oficiales")
    else:
        print(f"[PENDIENTE] Objetivo 163, actual {total_final}")
    
    conn.close()

def main():
    """Función principal"""
    
    print("AGREGAR IIEE FALTANTES A TABLA INDICES_METODOLOGICOS")
    print("=" * 60)
    print("Objetivo: Completar 163 instituciones RER oficiales")
    print("Faltantes: 3040177, 1678861 (RER 54 - Ancash)")
    
    try:
        # 1. Analizar contexto RER 54
        contexto = obtener_contexto_rer54()
        
        # 2. Agregar instituciones faltantes
        agregar_instituciones_faltantes()
        
        # 3. Verificar inserción
        verificar_insercion_final()
        
        print("\n" + "=" * 60)
        print("[COMPLETADO] PROCESO EXITOSO")
        print("[OK] Tabla indices_metodologicos actualizada")
        print("[OK] Lista para regenerar clustering con 163 IIEE")
        
    except Exception as e:
        print(f"\n[ERROR] ERROR EN EL PROCESO: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()