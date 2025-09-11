"""
Script para corregir Y3_PR a escala 0-1 en lugar de 0-100%

Convierte todas las variables Y3_PR de porcentajes (0-100) a decimales (0-1)

Autor: Proyecto Reasis
Fecha: 2025-08-10
"""

import sqlite3
import pandas as pd
from datetime import datetime

def corregir_escala_y3_pr():
    """
    Convierte Y3_PR de escala 0-100% a escala 0-1
    """
    
    print("=== CORRIGIENDO Y3_PR DE ESCALA 0-100% A 0-1 ===\n")
    
    conn = sqlite3.connect('reasis_database.db')
    cursor = conn.cursor()
    
    # 1. Verificar estado actual en instituciones_educativas
    print("1. ESTADO ACTUAL EN INSTITUCIONES_EDUCATIVAS:")
    
    columnas_y3pr = ['Y3_PR_Comunicacion', 'Y3_PR_Matematica', 'Y3_PR_Produccion_Textos']
    
    for col in columnas_y3pr:
        stats = cursor.execute(f"""
            SELECT 
                COUNT({col}) as con_datos,
                MIN({col}) as minimo,
                MAX({col}) as maximo,
                AVG({col}) as promedio
            FROM instituciones_educativas
            WHERE {col} IS NOT NULL
        """).fetchone()
        
        if stats[0] > 0:
            print(f"   {col}:")
            print(f"     Con datos: {stats[0]} instituciones")
            print(f"     Rango actual: {stats[1]:.2f} - {stats[2]:.2f}")
            print(f"     Promedio actual: {stats[3]:.2f}")
        else:
            print(f"   {col}: Sin datos")
    
    # 2. Aplicar corrección (dividir por 100)
    print(f"\n2. APLICANDO CORRECCIÓN (÷ 100):")
    
    actualizaciones = {}
    
    for col in columnas_y3pr:
        # Actualizar dividiendo por 100
        cursor.execute(f"""
            UPDATE instituciones_educativas 
            SET {col} = {col} / 100.0
            WHERE {col} IS NOT NULL
        """)
        
        actualizaciones[col] = cursor.rowcount
        print(f"   {col}: {cursor.rowcount} registros corregidos")
    
    conn.commit()
    
    # 3. Verificar corrección
    print(f"\n3. VERIFICACIÓN POST-CORRECCIÓN:")
    
    for col in columnas_y3pr:
        stats = cursor.execute(f"""
            SELECT 
                COUNT({col}) as con_datos,
                MIN({col}) as minimo,
                MAX({col}) as maximo,
                AVG({col}) as promedio
            FROM instituciones_educativas
            WHERE {col} IS NOT NULL
        """).fetchone()
        
        if stats[0] > 0:
            print(f"   {col}:")
            print(f"     Rango corregido: {stats[1]:.4f} - {stats[2]:.4f}")
            print(f"     Promedio corregido: {stats[3]:.4f}")
            
            # Validar que está en rango [0,1]
            if stats[1] >= 0 and stats[2] <= 1:
                print(f"     [OK] Escala correcta [0-1]")
            else:
                print(f"     [ERROR] Escala incorrecta")
        else:
            print(f"   {col}: Sin datos")
    
    # 4. Recalcular Y3_PR general con nueva escala
    print(f"\n4. RECALCULANDO Y3_PR GENERAL:")
    
    # Obtener datos corregidos
    df_y3pr = pd.read_sql_query("""
        SELECT 
            codigo_modular,
            Y3_PR_Comunicacion,
            Y3_PR_Matematica, 
            Y3_PR_Produccion_Textos
        FROM instituciones_educativas
        WHERE Y3_PR_Comunicacion IS NOT NULL 
           OR Y3_PR_Matematica IS NOT NULL 
           OR Y3_PR_Produccion_Textos IS NOT NULL
    """, conn)
    
    import numpy as np
    
    def calcular_y3pr_general_corregido(row):
        """Calcula promedio omitiendo valores 0 y NULL"""
        valores_validos = []
        
        for materia in columnas_y3pr:
            valor = row[materia]
            if pd.notna(valor) and valor > 0:
                valores_validos.append(valor)
        
        if len(valores_validos) > 0:
            return np.mean(valores_validos)
        else:
            return np.nan
    
    # Calcular Y3_PR general corregido
    df_y3pr['Y3_PR_general'] = df_y3pr.apply(calcular_y3pr_general_corregido, axis=1)
    
    # Filtrar solo válidos
    df_resultado = df_y3pr[df_y3pr['Y3_PR_general'].notna()].copy()
    
    print(f"   Instituciones with Y3_PR general: {len(df_resultado)}")
    if len(df_resultado) > 0:
        print(f"   Rango Y3_PR general: {df_resultado['Y3_PR_general'].min():.4f} - {df_resultado['Y3_PR_general'].max():.4f}")
        print(f"   Promedio Y3_PR general: {df_resultado['Y3_PR_general'].mean():.4f}")
    
    # 5. Guardar Y3_PR general corregido
    print(f"\n5. GUARDANDO Y3_PR GENERAL CORREGIDO:")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = f"temp_data/y3_pr_general_corregido_{timestamp}.csv"
    
    df_export = df_resultado[['codigo_modular', 'Y3_PR_general']].copy()
    df_export.to_csv(csv_path, index=False)
    
    print(f"   Archivo guardado: {csv_path}")
    
    # Muestra de datos corregidos
    print(f"\n   MUESTRA DATOS CORREGIDOS (10 primeros):")
    muestra = df_resultado[['codigo_modular', 'Y3_PR_Comunicacion', 'Y3_PR_Matematica', 
                          'Y3_PR_Produccion_Textos', 'Y3_PR_general']].head(10)
    print(muestra.to_string(index=False))
    
    # 6. Respaldo
    backup_path = f"data/backups/instituciones_educativas_y3pr_corregido_{timestamp}.csv"
    df_backup = pd.read_sql_query("SELECT * FROM instituciones_educativas", conn)
    df_backup.to_csv(backup_path, index=False)
    print(f"\n6. RESPALDO CREADO: {backup_path}")
    
    conn.close()
    
    return len(df_resultado), df_resultado['Y3_PR_general'].mean() if len(df_resultado) > 0 else 0, csv_path

if __name__ == "__main__":
    instituciones_corregidas, promedio_corregido, archivo_csv = corregir_escala_y3_pr()
    
    print(f"\n=== RESULTADO CORRECCIÓN Y3_PR ===")
    print(f"Instituciones corregidas: {instituciones_corregidas}")
    print(f"Promedio Y3_PR corregido: {promedio_corregido:.4f}")
    print(f"Archivo Y3_PR general: {archivo_csv}")
    
    print(f"\n[OK] Y3_PR corregido a escala 0-1")
    print(f"[OK] Coherencia metodológica restaurada") 
    print(f"[OK] Listo para aplicar a indices_metodologicos")