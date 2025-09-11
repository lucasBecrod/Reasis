"""
Script para aplicar Y3_PR columnas a tabla instituciones_educativas

Agrega tres columnas de Y3_PR por materia a la tabla principal instituciones_educativas

Autor: Proyecto Reasis
Fecha: 2025-08-10
"""

import sqlite3
import pandas as pd
from datetime import datetime

def aplicar_y3_pr_instituciones_educativas():
    """
    Aplica las tres columnas Y3_PR a la tabla instituciones_educativas
    """
    
    print("=== APLICANDO Y3_PR A TABLA INSTITUCIONES_EDUCATIVAS ===\n")
    
    conn = sqlite3.connect('reasis_database.db')
    cursor = conn.cursor()
    
    # 1. Cargar datos calculados
    csv_path = "temp_data/y3_pr_columnas_separadas_20250810_095349.csv"
    print(f"1. CARGANDO DATOS CALCULADOS: {csv_path}")
    
    try:
        df_y3pr = pd.read_csv(csv_path)
        print(f"   Registros cargados: {len(df_y3pr)}")
        
        # Estadísticas del archivo
        print(f"   Cobertura por columna:")
        for col in ['Y3_PR_Comunicacion', 'Y3_PR_Matematica', 'Y3_PR_Produccion_Textos']:
            count = df_y3pr[col].notna().sum()
            promedio = df_y3pr[col].mean()
            print(f"     {col}: {count} instituciones (promedio: {promedio:.2f}%)")
        
    except FileNotFoundError:
        print(f"   ERROR: Archivo no encontrado")
        return False
    
    # 2. Verificar/agregar columnas Y3_PR en tabla instituciones_educativas
    cursor.execute("PRAGMA table_info(instituciones_educativas)")
    columnas_existentes = [row[1] for row in cursor.fetchall()]
    
    columnas_y3pr = ['Y3_PR_Comunicacion', 'Y3_PR_Matematica', 'Y3_PR_Produccion_Textos']
    
    print(f"\n2. VERIFICANDO/AGREGANDO COLUMNAS:")
    for col in columnas_y3pr:
        if col not in columnas_existentes:
            print(f"   Agregando columna {col}...")
            cursor.execute(f"ALTER TABLE instituciones_educativas ADD COLUMN {col} REAL")
        else:
            print(f"   Columna {col} ya existe - actualizando...")
    
    conn.commit()
    
    # 3. Aplicar valores Y3_PR
    print(f"\n3. ACTUALIZANDO VALORES Y3_PR:")
    
    actualizaciones = {}
    for col in columnas_y3pr:
        actualizaciones[col] = 0
    
    for _, row in df_y3pr.iterrows():
        # Convertir código modular a string con formato apropiado
        codigo_original = row['codigo_modular']
        if pd.notna(codigo_original):
            # Convertir a entero primero (para eliminar decimales) luego a string
            codigo_modular = str(int(float(codigo_original)))
        else:
            continue
        
        for col in columnas_y3pr:
            valor = row[col]
            if pd.notna(valor):
                cursor.execute(f"""
                    UPDATE instituciones_educativas 
                    SET {col} = ? 
                    WHERE codigo_modular = ?
                """, (float(valor), codigo_modular))
                
                if cursor.rowcount > 0:
                    actualizaciones[col] += cursor.rowcount
    
    conn.commit()
    
    for col, count in actualizaciones.items():
        print(f"   {col}: {count} instituciones actualizadas")
    
    # 4. Verificación final
    print(f"\n4. VERIFICACIÓN FINAL:")
    
    for col in columnas_y3pr:
        result = cursor.execute(f"""
            SELECT COUNT(*) total,
                   COUNT({col}) con_datos,
                   COUNT(*) - COUNT({col}) sin_datos,
                   AVG({col}) promedio,
                   MIN({col}) minimo,
                   MAX({col}) maximo
            FROM instituciones_educativas
        """).fetchone()
        
        cobertura_pct = result[1]/result[0]*100 if result[0] > 0 else 0
        print(f"   {col}:")
        print(f"     Total instituciones: {result[0]}")
        print(f"     Con datos: {result[1]} ({cobertura_pct:.1f}%)")
        print(f"     Sin datos: {result[2]}")
        if result[1] > 0:
            print(f"     Promedio: {result[3]:.2f}%")
            print(f"     Rango: {result[4]:.2f}% - {result[5]:.2f}%")
        print()
    
    # 5. Distribución por niveles de desempeño
    print(f"5. DISTRIBUCIÓN POR NIVELES DE DESEMPEÑO:")
    
    for col in columnas_y3pr:
        print(f"\n   {col}:")
        
        niveles = cursor.execute(f"""
            SELECT 
                CASE 
                    WHEN {col} = 0 THEN 'Sin logro (0%)'
                    WHEN {col} < 3 THEN 'Muy bajo (0.1-3%)'
                    WHEN {col} < 6 THEN 'Bajo (3-6%)'
                    WHEN {col} < 10 THEN 'Medio-Bajo (6-10%)'
                    WHEN {col} < 15 THEN 'Medio (10-15%)'
                    ELSE 'Alto (>15%)'
                END as nivel_desempeno,
                COUNT(*) as cantidad,
                AVG({col}) as promedio_nivel
            FROM instituciones_educativas 
            WHERE {col} IS NOT NULL
            GROUP BY 
                CASE 
                    WHEN {col} = 0 THEN 'Sin logro (0%)'
                    WHEN {col} < 3 THEN 'Muy bajo (0.1-3%)'
                    WHEN {col} < 6 THEN 'Bajo (3-6%)'
                    WHEN {col} < 10 THEN 'Medio-Bajo (6-10%)'
                    WHEN {col} < 15 THEN 'Medio (10-15%)'
                    ELSE 'Alto (>15%)'
                END
            ORDER BY promedio_nivel
        """).fetchall()
        
        total_con_datos = cursor.execute(f"SELECT COUNT({col}) FROM instituciones_educativas WHERE {col} IS NOT NULL").fetchone()[0]
        
        for nivel, cantidad, promedio_nivel in niveles:
            porcentaje = cantidad/total_con_datos*100 if total_con_datos > 0 else 0
            print(f"     {nivel}: {cantidad} instituciones ({porcentaje:.1f}%) - prom: {promedio_nivel:.2f}%")
    
    # 6. Validación cruzada con datos académicos
    print(f"\n6. VALIDACIÓN CRUZADA:")
    
    # Verificar instituciones con datos académicos vs Y3_PR
    validacion = cursor.execute("""
        SELECT 
            i.codigo_modular,
            i.Y3_PR_Comunicacion,
            i.Y3_PR_Matematica, 
            i.Y3_PR_Produccion_Textos,
            COUNT(DISTINCT r.materia) as materias_en_resultados
        FROM instituciones_educativas i
        LEFT JOIN resultados_academicos r ON i.codigo_modular = r.codigo_modular
        WHERE i.Y3_PR_Comunicacion IS NOT NULL 
           OR i.Y3_PR_Matematica IS NOT NULL 
           OR i.Y3_PR_Produccion_Textos IS NOT NULL
        GROUP BY i.codigo_modular, i.Y3_PR_Comunicacion, i.Y3_PR_Matematica, i.Y3_PR_Produccion_Textos
        HAVING COUNT(DISTINCT r.materia) > 0
        LIMIT 5
    """).fetchall()
    
    print(f"   Muestra validación (5 instituciones):")
    for codigo, comm, math, prod, materias in validacion:
        print(f"     {codigo}: Comm={comm:.1f}% Math={math:.1f}% Prod={prod or 'N/A'} ({materias} materias)")
    
    # 7. Respaldo
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"data/backups/instituciones_educativas_con_y3pr_{timestamp}.csv"
    
    df_backup = pd.read_sql_query("SELECT * FROM instituciones_educativas", conn)
    df_backup.to_csv(backup_path, index=False)
    print(f"\n7. RESPALDO CREADO: {backup_path}")
    
    conn.close()
    
    # 8. Evaluar éxito
    total_actualizaciones = sum(actualizaciones.values())
    
    if total_actualizaciones > 0:
        print(f"\n[ÉXITO] Y3_PR aplicado a tabla instituciones_educativas")
        print(f"[COLUMNAS] {columnas_y3pr}")
        print(f"[ACTUALIZACIONES] {total_actualizaciones} registros actualizados")
    else:
        print(f"\n[ERROR] No se aplicaron actualizaciones")
    
    return total_actualizaciones > 0, actualizaciones

if __name__ == "__main__":
    exito, stats = aplicar_y3_pr_instituciones_educativas()
    
    print(f"\n=== RESULTADO FINAL ===")
    if exito:
        print(f"[OK] Y3_PR aplicado exitosamente a instituciones_educativas")
        print(f"[OK] Tres columnas creadas por materia")
        print(f"[OK] Datos validados y respaldados")
        for col, count in stats.items():
            materia = col.replace('Y3_PR_', '').replace('_', ' ')
            print(f"[OK] {materia}: {count} instituciones")
    else:
        print(f"X Error en aplicación de Y3_PR")