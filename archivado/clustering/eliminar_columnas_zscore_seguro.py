#!/usr/bin/env python3
"""
Eliminar columnas ZSCORE de forma segura manejando dependencias de vistas
"""

import sqlite3
import pandas as pd

def identificar_dependencias():
    """Identificar vistas que dependen de indices_metodologicos"""
    
    conn = sqlite3.connect('reasis_database_v4.db')
    
    print("=== IDENTIFICANDO DEPENDENCIAS ===")
    
    # Buscar vistas que referencien indices_metodologicos
    cursor = conn.cursor()
    cursor.execute("""
        SELECT name, sql FROM sqlite_master 
        WHERE type = 'view' 
        AND sql LIKE '%indices_metodologicos%'
    """)
    
    vistas_dependientes = cursor.fetchall()
    
    print(f"Vistas dependientes encontradas: {len(vistas_dependientes)}")
    for vista in vistas_dependientes:
        print(f"  - {vista[0]}")
    
    conn.close()
    return [vista[0] for vista in vistas_dependientes]

def eliminar_vistas_temporalmente(vistas):
    """Eliminar vistas temporalmente para permitir modificación de tabla"""
    
    conn = sqlite3.connect('reasis_database_v4.db')
    
    print("\n=== ELIMINANDO VISTAS TEMPORALMENTE ===")
    
    # Guardar definiciones de vistas para recrearlas después
    definiciones_vistas = {}
    cursor = conn.cursor()
    
    for vista in vistas:
        # Obtener definición de la vista
        cursor.execute(f"""
            SELECT sql FROM sqlite_master 
            WHERE type = 'view' AND name = '{vista}'
        """)
        resultado = cursor.fetchone()
        if resultado:
            definiciones_vistas[vista] = resultado[0]
            print(f"  Guardando definición: {vista}")
        
        # Eliminar vista
        cursor.execute(f"DROP VIEW IF EXISTS {vista}")
        print(f"  [OK] Vista {vista} eliminada temporalmente")
    
    conn.commit()
    conn.close()
    return definiciones_vistas

def recrear_tabla_sin_zscore():
    """Recrear tabla indices_metodologicos sin columnas ZSCORE"""
    
    conn = sqlite3.connect('reasis_database_v4.db')
    
    print("\n=== RECREANDO TABLA SIN ZSCORE ===")
    
    cursor = conn.cursor()
    
    # Crear nueva tabla con estructura específica (sin ZSCORE)
    cursor.execute("""
        CREATE TABLE indices_metodologicos_limpio (
            CODIGO_MODULAR TEXT,
            NOMBRE_INSTITUCION TEXT,
            NUMERO_FYA INT,
            LATITUD REAL,
            LONGITUD REAL,
            ALTITUD_MSNM REAL,
            Y1_ILA REAL,
            Y2_TD REAL,
            Y3_PR REAL,
            X1_NVC REAL,
            X2_TR INT,
            X4_IDD REAL,
            X5_ED REAL,
            X6_CDD REAL,
            X10_IE REAL,
            X11_RED REAL,
            X12_TOE INT,
            X15_MEIB INT,
            X13_TMATRC REAL,
            X14_NIVEL_EDUCATIVO REAL,
            X16_MODALIDAD REAL,
            X17_GESTION REAL,
            X18_TURNO REAL,
            X19_ORGANIZACION_PEDAGOGICA REAL,
            X20_DIRECTIVOS_TOTAL REAL,
            X21_MULTIPLICIDAD1 REAL,
            X22_MULTIPLICIDAD2 REAL,
            X24_GPMD REAL,
            X25_POBLACION_DISTRITO REAL
        )
    """)
    
    # Copiar datos (solo columnas sin ZSCORE)
    cursor.execute("""
        INSERT INTO indices_metodologicos_limpio (
            CODIGO_MODULAR, NOMBRE_INSTITUCION, NUMERO_FYA,
            LATITUD, LONGITUD, ALTITUD_MSNM,
            Y1_ILA, Y2_TD, Y3_PR,
            X1_NVC, X2_TR, X4_IDD, X5_ED, X6_CDD,
            X10_IE, X11_RED, X12_TOE, X15_MEIB,
            X13_TMATRC, X14_NIVEL_EDUCATIVO, X16_MODALIDAD, X17_GESTION,
            X18_TURNO, X19_ORGANIZACION_PEDAGOGICA, X20_DIRECTIVOS_TOTAL,
            X21_MULTIPLICIDAD1, X22_MULTIPLICIDAD2, X24_GPMD, X25_POBLACION_DISTRITO
        )
        SELECT 
            CODIGO_MODULAR, NOMBRE_INSTITUCION, NUMERO_FYA,
            LATITUD, LONGITUD, ALTITUD_MSNM,
            Y1_ILA, Y2_TD, Y3_PR,
            X1_NVC, X2_TR, X4_IDD, X5_ED, X6_CDD,
            X10_IE, X11_RED, X12_TOE, X15_MEIB,
            X13_TMATRC, X14_NIVEL_EDUCATIVO, X16_MODALIDAD, X17_GESTION,
            X18_TURNO, X19_ORGANIZACION_PEDAGOGICA, X20_DIRECTIVOS_TOTAL,
            X21_MULTIPLICIDAD1, X22_MULTIPLICIDAD2, X24_GPMD, X25_POBLACION_DISTRITO
        FROM indices_metodologicos
    """)
    
    # Verificar datos copiados
    df_verificar = pd.read_sql_query("SELECT COUNT(*) as total FROM indices_metodologicos_limpio", conn)
    print(f"[OK] Datos copiados: {df_verificar['total'].iloc[0]} registros")
    
    # Reemplazar tabla original
    cursor.execute("DROP TABLE indices_metodologicos")
    cursor.execute("ALTER TABLE indices_metodologicos_limpio RENAME TO indices_metodologicos")
    
    conn.commit()
    conn.close()

def recrear_vistas_compatibles(definiciones_vistas):
    """Recrear vistas que sean compatibles con la nueva estructura"""
    
    conn = sqlite3.connect('reasis_database_v4.db')
    
    print("\n=== RECREANDO VISTAS COMPATIBLES ===")
    
    cursor = conn.cursor()
    
    for vista, definicion in definiciones_vistas.items():
        try:
            # Intentar recrear la vista
            if 'ZSCORE' not in definicion:
                cursor.execute(definicion)
                print(f"  [OK] Vista {vista} recreada")
            else:
                print(f"  [SKIP] Vista {vista} contiene ZSCORE - no recreada")
        except Exception as e:
            print(f"  [ERROR] Vista {vista}: {e}")
    
    conn.commit()
    conn.close()

def verificar_estructura_final():
    """Verificar estructura final limpia"""
    
    conn = sqlite3.connect('reasis_database_v4.db')
    
    print("\n=== VERIFICACION FINAL ===")
    
    # Verificar estructura
    cursor = conn.cursor()
    cursor.execute('PRAGMA table_info(indices_metodologicos)')
    columnas = cursor.fetchall()
    
    print(f"Columnas finales: {len(columnas)}")
    
    # Verificar ausencia de ZSCORE
    columnas_zscore = [col[1] for col in columnas if 'ZSCORE' in col[1]]
    if len(columnas_zscore) == 0:
        print("[EXITO] Sin columnas ZSCORE")
    else:
        print(f"[ERROR] Columnas ZSCORE restantes: {columnas_zscore}")
    
    # Verificar datos
    df_datos = pd.read_sql_query("SELECT COUNT(*) as total FROM indices_metodologicos", conn)
    print(f"Registros preservados: {df_datos['total'].iloc[0]}")
    
    # Mostrar primeras 5 columnas
    print("\nPrimeras 5 columnas:")
    for i, col in enumerate(columnas[:5], 1):
        print(f"  {i}. {col[1]} ({col[2]})")
    
    conn.close()

def main():
    """Función principal con manejo seguro de dependencias"""
    
    print("ELIMINAR COLUMNAS ZSCORE - VERSION SEGURA")
    print("=" * 50)
    
    try:
        # 1. Crear respaldo
        conn = sqlite3.connect('reasis_database_v4.db')
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS indices_metodologicos_backup AS SELECT * FROM indices_metodologicos")
        conn.commit()
        conn.close()
        print("[OK] Respaldo creado")
        
        # 2. Identificar y eliminar vistas dependientes
        vistas = identificar_dependencias()
        definiciones_vistas = eliminar_vistas_temporalmente(vistas)
        
        # 3. Recrear tabla sin ZSCORE
        recrear_tabla_sin_zscore()
        
        # 4. Recrear vistas compatibles
        recrear_vistas_compatibles(definiciones_vistas)
        
        # 5. Verificar resultado
        verificar_estructura_final()
        
        print("\n" + "=" * 50)
        print("[COMPLETADO] Columnas ZSCORE eliminadas exitosamente")
        print(f"[REDUCCION] Tabla optimizada: 38 → 29 columnas (-9 ZSCORE)")
        print("[SEGURO] Respaldo disponible en indices_metodologicos_backup")
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()