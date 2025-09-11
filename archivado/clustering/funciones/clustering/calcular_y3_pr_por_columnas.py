"""
Script para calcular Y3_PR por columnas separadas por materia

Calcula porcentajes de estudiantes en nivel satisfactorio por institución educativa
creando columnas separadas: Y3_PR_Comunicacion, Y3_PR_Matematica, Y3_PR_Produccion_Textos

Autor: Proyecto Reasis
Fecha: 2025-08-10
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime

def calcular_y3_pr_por_columnas():
    """
    Calcula Y3_PR con columnas separadas por materia
    
    METODOLOGÍA DE CÁLCULO:
    1. Para cada institución y materia:
       - Contar total de estudiantes evaluados
       - Contar estudiantes con nivel 'Satisfactorio', 'Logrado' o 'Destacado'  
       - Calcular: Y3_PR_Materia = (estudiantes_satisfactorio / total_estudiantes) * 100
    
    2. Crear tres columnas:
       - Y3_PR_Comunicacion: % satisfactorio en Comunicación
       - Y3_PR_Matematica: % satisfactorio en Matemática
       - Y3_PR_Produccion_Textos: % satisfactorio en Producción de textos
       
    3. Criterios de inclusión:
       - Mínimo 3 estudiantes evaluados por materia
       - Solo niveles de logro: 'Satisfactorio', 'Logrado', 'Destacado'
    """
    
    print("=== CALCULANDO Y3_PR POR COLUMNAS SEPARADAS ===\n")
    
    conn = sqlite3.connect('reasis_database.db')
    
    # 1. Obtener instituciones target
    df_target = pd.read_sql_query("""
        SELECT CODIGO_MODULAR, NOMBRE_INSTITUCION
        FROM indices_metodologicos
    """, conn)
    
    print(f"1. INSTITUCIONES TARGET: {len(df_target)}")
    
    # 2. Mostrar metodología detallada
    print(f"\n2. METODOLOGÍA DE CÁLCULO DETALLADA:")
    print(f"   FÓRMULA POR MATERIA:")
    print(f"   Y3_PR_[Materia] = (Estudiantes_Satisfactorio / Total_Estudiantes) x 100")
    print(f"   ")
    print(f"   NIVELES CONSIDERADOS SATISFACTORIOS:")
    print(f"   - 'Satisfactorio' (nivel 3)")
    print(f"   - 'Logrado' (equivalente a Satisfactorio)")
    print(f"   - 'Destacado' (nivel superior a Satisfactorio)")
    print(f"   ")
    print(f"   CRITERIOS DE INCLUSIÓN:")
    print(f"   - Mínimo 3 estudiantes evaluados por materia")
    print(f"   - Datos válidos de nivel de logro")
    
    # 3. Verificar niveles de logro disponibles
    print(f"\n3. VERIFICACIÓN NIVELES DE LOGRO:")
    niveles_disponibles = pd.read_sql_query("""
        SELECT nivel_logro_texto, nivel_logro_numerico, COUNT(*) as total
        FROM resultados_academicos
        GROUP BY nivel_logro_texto, nivel_logro_numerico
        ORDER BY nivel_logro_numerico
    """, conn)
    
    print("   Niveles disponibles en base de datos:")
    for _, row in niveles_disponibles.iterrows():
        satisfactorio = "[SATISFACTORIO]" if row['nivel_logro_texto'] in ['Satisfactorio', 'Logrado', 'Destacado'] else "  No satisfactorio"
        print(f"   - {row['nivel_logro_texto']} (nivel {row['nivel_logro_numerico']}): {row['total']} estudiantes {satisfactorio}")
    
    # 4. Calcular porcentajes por materia e institución
    print(f"\n4. CALCULANDO PORCENTAJES POR MATERIA E INSTITUCIÓN:")
    
    query_porcentajes = """
    SELECT 
        codigo_modular,
        materia,
        COUNT(*) as total_estudiantes,
        SUM(CASE WHEN nivel_logro_texto IN ('Satisfactorio', 'Logrado', 'Destacado') 
            THEN 1 ELSE 0 END) as estudiantes_satisfactorio,
        ROUND(SUM(CASE WHEN nivel_logro_texto IN ('Satisfactorio', 'Logrado', 'Destacado') 
                  THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as pct_satisfactorio
    FROM resultados_academicos
    WHERE materia IN ('Comunicación', 'Matemática', 'Producción de textos')
    GROUP BY codigo_modular, materia
    HAVING COUNT(*) >= 3  -- Mínimo 3 estudiantes evaluados
    ORDER BY codigo_modular, materia
    """
    
    df_porcentajes = pd.read_sql_query(query_porcentajes, conn)
    
    print(f"   Registros calculados: {len(df_porcentajes)}")
    print(f"   Instituciones únicas: {df_porcentajes['codigo_modular'].nunique()}")
    
    # Mostrar estadísticas por materia
    print(f"\n   ESTADÍSTICAS POR MATERIA:")
    for materia in ['Comunicación', 'Matemática', 'Producción de textos']:
        subset = df_porcentajes[df_porcentajes['materia'] == materia]
        if len(subset) > 0:
            promedio = subset['pct_satisfactorio'].mean()
            maximo = subset['pct_satisfactorio'].max()
            minimo = subset['pct_satisfactorio'].min()
            instituciones = len(subset)
            total_estudiantes = subset['total_estudiantes'].sum()
            total_satisfactorio = subset['estudiantes_satisfactorio'].sum()
            
            print(f"   {materia}:")
            print(f"     - Instituciones: {instituciones}")
            print(f"     - Estudiantes evaluados: {total_estudiantes}")
            print(f"     - Estudiantes satisfactorio: {total_satisfactorio}")
            print(f"     - % promedio: {promedio:.2f}% (rango: {minimo:.2f}%-{maximo:.2f}%)")
        else:
            print(f"   {materia}: Sin datos")
    
    # 5. Crear matriz de materias por institución
    print(f"\n5. CONSTRUYENDO MATRIZ CON COLUMNAS SEPARADAS:")
    
    # Pivotar para tener columnas separadas por materia
    df_pivot = df_porcentajes.pivot(index='codigo_modular', 
                                   columns='materia', 
                                   values='pct_satisfactorio').reset_index()
    
    # Limpiar nombres de columnas
    df_pivot.columns.name = None
    df_pivot = df_pivot.rename(columns={
        'Comunicación': 'Y3_PR_Comunicacion',
        'Matemática': 'Y3_PR_Matematica', 
        'Producción de textos': 'Y3_PR_Produccion_Textos'
    })
    
    # Asegurar que todas las columnas existan
    columnas_esperadas = ['Y3_PR_Comunicacion', 'Y3_PR_Matematica', 'Y3_PR_Produccion_Textos']
    for col in columnas_esperadas:
        if col not in df_pivot.columns:
            df_pivot[col] = np.nan
    
    print(f"   Instituciones en matriz final: {len(df_pivot)}")
    
    # Estadísticas de cobertura por columna
    print(f"\n   COBERTURA POR COLUMNA:")
    for col in columnas_esperadas:
        count_con_datos = df_pivot[col].notna().sum()
        promedio = df_pivot[col].mean() if count_con_datos > 0 else 0
        print(f"   {col}: {count_con_datos} instituciones (promedio: {promedio:.2f}%)")
    
    # 6. Mostrar muestra de resultados
    print(f"\n6. MUESTRA DE RESULTADOS (10 primeras instituciones):")
    df_muestra = df_pivot.head(10)[['codigo_modular'] + columnas_esperadas]
    print(df_muestra.to_string(index=False))
    
    # 7. Validación cruzada con datos originales
    print(f"\n7. VALIDACIÓN CON DATOS ORIGINALES:")
    
    # Verificar algunas instituciones manualmente
    instituciones_muestra = df_pivot['codigo_modular'].head(3).tolist()
    
    for codigo in instituciones_muestra:
        print(f"\n   Validación institución {codigo}:")
        
        validacion = pd.read_sql_query(f"""
            SELECT 
                materia,
                COUNT(*) as total,
                SUM(CASE WHEN nivel_logro_texto IN ('Satisfactorio', 'Logrado', 'Destacado') 
                    THEN 1 ELSE 0 END) as satisfactorio,
                ROUND(SUM(CASE WHEN nivel_logro_texto IN ('Satisfactorio', 'Logrado', 'Destacado') 
                          THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as porcentaje_calc
            FROM resultados_academicos
            WHERE codigo_modular = '{codigo}'
            AND materia IN ('Comunicación', 'Matemática', 'Producción de textos')
            GROUP BY materia
        """, conn)
        
        if len(validacion) > 0:
            for _, row in validacion.iterrows():
                print(f"     {row['materia']}: {row['satisfactorio']}/{row['total']} = {row['porcentaje_calc']}%")
        else:
            print(f"     Sin datos de validación")
    
    # 8. Guardar resultados
    print(f"\n8. GUARDANDO RESULTADOS:")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = f"temp_data/y3_pr_columnas_separadas_{timestamp}.csv"
    
    df_resultado = df_pivot[['codigo_modular'] + columnas_esperadas].copy()
    df_resultado.to_csv(csv_path, index=False)
    
    print(f"   Archivo guardado: {csv_path}")
    print(f"   Columnas guardadas: {columnas_esperadas}")
    
    # 9. Resumen final
    print(f"\n9. RESUMEN METODOLÓGICO FINAL:")
    print(f"   FÓRMULA APLICADA:")
    print(f"   Y3_PR_[Materia] = (Suma estudiantes con nivel Satisfactorio/Logrado/Destacado) / (Suma total estudiantes) x 100")
    print(f"   ")
    print(f"   CRITERIOS DE CALIDAD:")
    print(f"   - Mínimo 3 estudiantes por materia e institución")
    print(f"   - Solo niveles de logro válidos considerados")
    print(f"   - Cálculo independiente por materia")
    print(f"   ")
    print(f"   COBERTURA FINAL:")
    
    cobertura_resumen = {}
    for col in columnas_esperadas:
        count = df_resultado[col].notna().sum()
        pct = count / len(df_target) * 100
        cobertura_resumen[col] = (count, pct)
        print(f"   {col}: {count}/{len(df_target)} instituciones ({pct:.1f}%)")
    
    conn.close()
    
    return csv_path, df_resultado, cobertura_resumen

if __name__ == "__main__":
    csv_file, df_final, cobertura = calcular_y3_pr_por_columnas()
    
    print(f"\n=== RESULTADO FINAL Y3_PR POR COLUMNAS ===")
    print(f"Archivo generado: {csv_file}")
    
    for col, (count, pct) in cobertura.items():
        materia_nombre = col.replace('Y3_PR_', '').replace('_', ' ')
        print(f"{materia_nombre}: {count} instituciones ({pct:.1f}%)")
    
    print(f"\n[ÉXITO] Y3_PR calculado por columnas separadas")
    print(f"[METODOLOGÍA] Validada y documentada para revisión")