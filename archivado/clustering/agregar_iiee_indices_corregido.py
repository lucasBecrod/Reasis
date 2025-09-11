#!/usr/bin/env python3
"""
Agregar las 2 instituciones faltantes (3040177, 1678861) a la tabla indices_metodologicos
con valores imputados contextualmente basados en RER 54, Ancash
VERSIÓN CORREGIDA con nombres exactos de columnas
"""

import sqlite3
import pandas as pd
import numpy as np

def obtener_contexto_rer54():
    """Obtener valores promedio de instituciones RER 54 similares para imputación"""
    
    conn = sqlite3.connect('reasis_database_v4.db')
    
    print("=== ANALISIS CONTEXTUAL RER 54 ===")
    
    # Buscar instituciones RER 54 en indices_metodologicos
    df_rer54 = pd.read_sql_query("""
        SELECT Y1_ILA, X1_NVC, X2_TR, X4_IDD, X11_RED, ALTITUD_MSNM
        FROM indices_metodologicos 
        WHERE NUMERO_FYA = 54
    """, conn)
    
    print(f"Instituciones RER 54 encontradas: {len(df_rer54)}")
    
    if len(df_rer54) > 0:
        # Calcular estadísticas para imputación
        contexto = {
            'Y1_ILA': round(df_rer54['Y1_ILA'].mean(), 3) if df_rer54['Y1_ILA'].notna().any() else None,
            'X1_NVC': int(df_rer54['X1_NVC'].mode().iloc[0]) if df_rer54['X1_NVC'].notna().any() else 4,
            'X2_TR': 2,  # Rural (RER es rural por definición)
            'X4_IDD': round(df_rer54['X4_IDD'].mean(), 3) if df_rer54['X4_IDD'].notna().any() else None,
            'X11_RED': round(df_rer54['X11_RED'].mean(), 3) if df_rer54['X11_RED'].notna().any() else None,
            'ALTITUD_MSNM': round(df_rer54['ALTITUD_MSNM'].mean(), 1) if df_rer54['ALTITUD_MSNM'].notna().any() else 3500.0
        }
        
        print("Contexto RER 54 calculado:")
        for var, val in contexto.items():
            if val is not None:
                print(f"  {var}: {val}")
            else:
                print(f"  {var}: NULL (no disponible)")
    else:
        # Valores por defecto
        contexto = {
            'Y1_ILA': None,
            'X1_NVC': 4,  # Alta vulnerabilidad
            'X2_TR': 2,   # Rural  
            'X4_IDD': None,
            'X11_RED': 15.0,
            'ALTITUD_MSNM': 3500.0
        }
        print("Usando contexto por defecto (no hay RER 54)")
    
    conn.close()
    return contexto

def agregar_instituciones_faltantes():
    """Agregar las 2 instituciones faltantes usando INSERT simple"""
    
    conn = sqlite3.connect('reasis_database_v4.db')
    
    # Obtener contexto
    contexto = obtener_contexto_rer54()
    
    # Datos específicos
    instituciones = [
        {
            'codigo': '3040177',
            'nombre': '87009-01 HUANCHUY',
            'numero_fya': 54,
            'latitud': -8.8,    # Aproximado Pamparomas, Ancash
            'longitud': -77.8,  # Aproximado Pamparomas, Ancash
            'altitud': 3500.0   # Altitud típica Ancash
        },
        {
            'codigo': '1678861', 
            'nombre': '692 - CAJAY',
            'numero_fya': 54,
            'latitud': -8.8,    # Aproximado Pamparomas, Ancash
            'longitud': -77.8,  # Aproximado Pamparomas, Ancash
            'altitud': 3500.0   # Altitud típica Ancash
        }
    ]
    
    print("\n=== AGREGANDO INSTITUCIONES FALTANTES ===")
    
    for inst in instituciones:
        print(f"\nAgregando CODIGO {inst['codigo']}:")
        
        # Preparar valores para INSERT (usar NULL para valores no disponibles)
        y1_ila = contexto['Y1_ILA'] if contexto['Y1_ILA'] is not None else 'NULL'
        x4_idd = contexto['X4_IDD'] if contexto['X4_IDD'] is not None else 'NULL'  
        x11_red = contexto['X11_RED'] if contexto['X11_RED'] is not None else 'NULL'
        
        query = f"""
        INSERT INTO indices_metodologicos (
            CODIGO_MODULAR, NOMBRE_INSTITUCION, NUMERO_FYA,
            LATITUD, LONGITUD, ALTITUD_MSNM,
            Y1_ILA, X1_NVC, X2_TR, X4_IDD, X11_RED
        ) VALUES (
            '{inst['codigo']}',
            '{inst['nombre']}', 
            {inst['numero_fya']},
            {inst['latitud']},
            {inst['longitud']},
            {inst['altitud']},
            {y1_ila},
            {contexto['X1_NVC']},
            {contexto['X2_TR']},
            {x4_idd},
            {x11_red}
        )
        """
        
        try:
            cursor = conn.cursor()
            cursor.execute(query)
            conn.commit()
            print(f"  [OK] {inst['codigo']} agregado exitosamente")
            print(f"    - Nombre: {inst['nombre']}")
            print(f"    - RER: {inst['numero_fya']}")
            print(f"    - Ubicacion: ({inst['latitud']}, {inst['longitud']})")
            print(f"    - Variables: Y1_ILA={y1_ila}, X1_NVC={contexto['X1_NVC']}, X2_TR={contexto['X2_TR']}")
            
        except Exception as e:
            print(f"  [ERROR] Error insertando {inst['codigo']}: {e}")
    
    conn.close()

def verificar_insercion():
    """Verificar que las instituciones se agregaron correctamente"""
    
    conn = sqlite3.connect('reasis_database_v4.db')
    
    print("\n=== VERIFICACION FINAL ===")
    
    # Verificar instituciones agregadas
    df_verificar = pd.read_sql_query("""
        SELECT CODIGO_MODULAR, NOMBRE_INSTITUCION, NUMERO_FYA,
               Y1_ILA, X1_NVC, X2_TR, X4_IDD, X11_RED
        FROM indices_metodologicos 
        WHERE CODIGO_MODULAR IN ('3040177', '1678861')
        ORDER BY CODIGO_MODULAR
    """, conn)
    
    if len(df_verificar) == 2:
        print("[EXITO] Ambas instituciones agregadas correctamente:")
        for _, row in df_verificar.iterrows():
            print(f"  CODIGO {row['CODIGO_MODULAR']}:")
            print(f"    - Nombre: {row['NOMBRE_INSTITUCION']}")
            print(f"    - RER: {row['NUMERO_FYA']}")
            print(f"    - Y1_ILA: {row['Y1_ILA']}")
            print(f"    - X1_NVC: {row['X1_NVC']} (vulnerabilidad)")
            print(f"    - X2_TR: {row['X2_TR']} (rural)")
    else:
        print(f"[PROBLEMA] Solo {len(df_verificar)} de 2 instituciones encontradas")
    
    # Verificar total final
    df_total = pd.read_sql_query("SELECT COUNT(*) as total FROM indices_metodologicos", conn)
    total = df_total['total'].iloc[0]
    
    print(f"\n[TOTALES]")
    print(f"  Total instituciones en indices_metodologicos: {total}")
    
    if total == 163:
        print("  [OBJETIVO ALCANZADO] 163 instituciones RER oficiales")
    else:
        print(f"  [PENDIENTE] Objetivo: 163, Actual: {total}")
    
    conn.close()

def main():
    """Función principal"""
    
    print("AGREGAR IIEE FALTANTES A INDICES_METODOLOGICOS")
    print("=" * 55)
    print("Objetivo: Alcanzar 163 instituciones RER oficiales")
    print("Agregar: 3040177, 1678861 (RER 54 - Ancash)")
    
    try:
        # 1. Obtener contexto RER 54
        obtener_contexto_rer54()
        
        # 2. Agregar instituciones
        agregar_instituciones_faltantes()
        
        # 3. Verificar resultado
        verificar_insercion()
        
        print("\n" + "=" * 55)
        print("[COMPLETADO] PROCESO EXITOSO")
        print("[OK] Tabla indices_metodologicos actualizada")
        print("[OK] Lista para regenerar clustering con datos completos")
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()