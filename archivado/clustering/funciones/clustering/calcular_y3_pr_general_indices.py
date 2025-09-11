"""
Script para calcular Y3_PR general para indices_metodologicos

Calcula Y3_PR promedio omitiendo valores 0% según la regla establecida

Autor: Proyecto Reasis
Fecha: 2025-08-10
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime

def calcular_y3_pr_general():
    """
    Calcula Y3_PR general omitiendo valores 0%
    
    REGLA DE CÁLCULO:
    - Promedio de las 3 materias OMITIENDO valores 0%
    - Solo incluir instituciones con al menos 1 materia > 0%
    - Si todas las materias son 0%, Y3_PR = NULL
    """
    
    print("=== CALCULANDO Y3_PR GENERAL PARA INDICES_METODOLOGICOS ===\n")
    
    conn = sqlite3.connect('reasis_database.db')
    
    # 1. Obtener datos de Y3_PR por materias desde instituciones_educativas
    print("1. OBTENIENDO DATOS Y3_PR POR MATERIAS:")
    
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
    
    print(f"   Instituciones con datos Y3_PR: {len(df_y3pr)}")
    
    # Estadísticas por materia
    materias = ['Y3_PR_Comunicacion', 'Y3_PR_Matematica', 'Y3_PR_Produccion_Textos']
    print(f"\n   Estadísticas por materia:")
    for materia in materias:
        count = df_y3pr[materia].notna().sum()
        promedio = df_y3pr[materia].mean()
        print(f"   {materia}: {count} instituciones - promedio {promedio:.2f}%")
    
    # 2. Aplicar regla de cálculo (omitir 0%)
    print(f"\n2. APLICANDO REGLA DE CÁLCULO:")
    print(f"   REGLA: Promedio de materias > 0% únicamente")
    
    def calcular_y3pr_omitiendo_ceros(row):
        """Calcula promedio omitiendo valores 0% y NULL"""
        valores_validos = []
        
        for materia in materias:
            valor = row[materia]
            if pd.notna(valor) and valor > 0:
                valores_validos.append(valor)
        
        if len(valores_validos) > 0:
            return np.mean(valores_validos)
        else:
            return np.nan
    
    # Calcular número de materias con datos > 0
    df_y3pr['materias_con_datos'] = 0
    df_y3pr['materias_mayor_cero'] = 0
    
    for materia in materias:
        df_y3pr['materias_con_datos'] += df_y3pr[materia].notna().astype(int)
        df_y3pr['materias_mayor_cero'] += ((df_y3pr[materia].notna()) & (df_y3pr[materia] > 0)).astype(int)
    
    # Calcular Y3_PR general
    df_y3pr['Y3_PR'] = df_y3pr.apply(calcular_y3pr_omitiendo_ceros, axis=1)
    
    # Filtrar solo instituciones con Y3_PR válido
    df_resultado = df_y3pr[df_y3pr['Y3_PR'].notna()].copy()
    
    print(f"   Instituciones con Y3_PR general: {len(df_resultado)}")
    print(f"   Instituciones excluidas (todas materias 0% o NULL): {len(df_y3pr) - len(df_resultado)}")
    
    if len(df_resultado) > 0:
        print(f"   Rango Y3_PR general: {df_resultado['Y3_PR'].min():.2f}% - {df_resultado['Y3_PR'].max():.2f}%")
        print(f"   Promedio Y3_PR general: {df_resultado['Y3_PR'].mean():.2f}%")
    
    # 3. Análisis de eficacia
    print(f"\n3. ANÁLISIS DE EFICACIA:")
    
    total_instituciones_estudio = pd.read_sql_query("SELECT COUNT(*) as total FROM indices_metodologicos", conn).iloc[0]['total']
    
    eficacia_cobertura = len(df_resultado) / total_instituciones_estudio * 100
    
    print(f"   COBERTURA:")
    print(f"   - Total instituciones estudio: {total_instituciones_estudio}")
    print(f"   - Con Y3_PR general: {len(df_resultado)}")
    print(f"   - Cobertura: {eficacia_cobertura:.1f}%")
    
    if len(df_resultado) > 0:
        # Distribución por número de materias usadas
        print(f"\n   DISTRIBUCIÓN POR MATERIAS INCLUIDAS:")
        for n_materias in [1, 2, 3]:
            count = len(df_resultado[df_resultado['materias_mayor_cero'] == n_materias])
            if count > 0:
                promedio = df_resultado[df_resultado['materias_mayor_cero'] == n_materias]['Y3_PR'].mean()
                pct = count / len(df_resultado) * 100
                print(f"   - {n_materias} materias: {count} instituciones ({pct:.1f}%) - promedio {promedio:.2f}%")
        
        # Nivel de desempeño general
        print(f"\n   DISTRIBUCIÓN POR NIVEL DE DESEMPEÑO GENERAL:")
        rangos = [
            (0, 2.99, "Muy Bajo"),
            (3, 5.99, "Bajo"), 
            (6, 9.99, "Medio-Bajo"),
            (10, 14.99, "Medio"),
            (15, 100, "Alto")
        ]
        
        for min_val, max_val, nombre in rangos:
            count = len(df_resultado[
                (df_resultado['Y3_PR'] >= min_val) & 
                (df_resultado['Y3_PR'] < max_val)
            ])
            pct = count / len(df_resultado) * 100
            if count > 0:
                promedio = df_resultado[
                    (df_resultado['Y3_PR'] >= min_val) & 
                    (df_resultado['Y3_PR'] < max_val)
                ]['Y3_PR'].mean()
                print(f"   - {nombre} ({min_val:.0f}-{max_val:.0f}%): {count} instituciones ({pct:.1f}%) - prom: {promedio:.2f}%")
    
    # 4. Evaluación de viabilidad
    print(f"\n4. EVALUACIÓN DE VIABILIDAD:")
    
    # Criterios de evaluación
    criterios_eficacia = {
        "Cobertura alta (>50%)": eficacia_cobertura > 50,
        "Cobertura media (30-50%)": 30 <= eficacia_cobertura <= 50,
        "Cobertura baja (<30%)": eficacia_cobertura < 30,
        "Datos suficientes (>40 inst)": len(df_resultado) > 40,
        "Variabilidad adecuada": len(df_resultado) > 0 and df_resultado['Y3_PR'].std() > 2.0
    }
    
    print(f"   CRITERIOS DE EVALUACIÓN:")
    for criterio, cumple in criterios_eficacia.items():
        status = "[CUMPLE]" if cumple else "[NO CUMPLE]"
        print(f"   {status} {criterio}")
    
    # Recomendación
    if eficacia_cobertura >= 50 and len(df_resultado) > 40:
        recomendacion = "ALTA - Implementar Y3_PR en clustering"
        nivel_eficacia = "ALTA"
    elif eficacia_cobertura >= 30 and len(df_resultado) > 25:
        recomendacion = "MEDIA - Evaluar implementación con reservas"
        nivel_eficacia = "MEDIA"
    else:
        recomendacion = "BAJA - Considerar estrategia alternativa"
        nivel_eficacia = "BAJA"
    
    print(f"\n   NIVEL DE EFICACIA: {nivel_eficacia}")
    print(f"   RECOMENDACIÓN: {recomendacion}")
    
    # 5. Guardar resultados si es viable
    if len(df_resultado) > 0:
        print(f"\n5. GUARDANDO RESULTADOS:")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_path = f"temp_data/y3_pr_general_{timestamp}.csv"
        
        df_export = df_resultado[['codigo_modular', 'Y3_PR', 'materias_mayor_cero']].copy()
        df_export.to_csv(csv_path, index=False)
        
        print(f"   Archivo guardado: {csv_path}")
        print(f"   Registros: {len(df_export)}")
        
        # Muestra de resultados
        print(f"\n   MUESTRA RESULTADOS (10 primeros):")
        muestra = df_resultado[['codigo_modular', 'Y3_PR_Comunicacion', 'Y3_PR_Matematica', 
                              'Y3_PR_Produccion_Textos', 'Y3_PR', 'materias_mayor_cero']].head(10)
        print(muestra.to_string(index=False))
    
    conn.close()
    
    return len(df_resultado), eficacia_cobertura, nivel_eficacia, df_resultado if len(df_resultado) > 0 else None

if __name__ == "__main__":
    instituciones_con_y3pr, cobertura_pct, eficacia, df_final = calcular_y3_pr_general()
    
    print(f"\n=== RESULTADO FINAL Y3_PR GENERAL ===")
    print(f"Instituciones con Y3_PR: {instituciones_con_y3pr}")
    print(f"Cobertura: {cobertura_pct:.1f}%")
    print(f"Nivel de eficacia: {eficacia}")
    
    if eficacia == "ALTA":
        print(f"\n[RECOMENDACIÓN] Implementar Y3_PR en indices_metodologicos")
        print(f"[ACCIÓN] Proceder con aplicación a clustering")
    elif eficacia == "MEDIA":
        print(f"\n[RECOMENDACIÓN] Evaluar implementación con reservas")
        print(f"[ACCIÓN] Considerar si la cobertura es suficiente para el análisis")
    else:
        print(f"\n[RECOMENDACIÓN] Buscar estrategia alternativa")
        print(f"[ACCIÓN] Explorar otras fuentes de datos académicos")
        
    if df_final is not None and eficacia in ["ALTA", "MEDIA"]:
        promedio_final = df_final['Y3_PR'].mean()
        print(f"\n[ESTADÍSTICA CLAVE] Promedio Y3_PR: {promedio_final:.2f}%")