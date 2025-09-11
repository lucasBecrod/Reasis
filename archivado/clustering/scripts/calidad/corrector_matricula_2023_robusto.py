#!/usr/bin/env python3
"""
Corrector de matrícula 2023 + Método estadístico robusto para tendencia
1. Corrige matric_siagie_2023 usando CSV específico
2. Implementa método Mann-Kendall + Sen's slope para tendencia robusta
"""

import sqlite3
import pandas as pd
import numpy as np
from scipy import stats
from scipy.stats import linregress
import warnings
warnings.filterwarnings('ignore')

def mann_kendall_test(data):
    """
    Implementa el test de Mann-Kendall para detectar tendencias monotónicas
    Más robusto que regresión lineal para datos con outliers
    """
    n = len(data)
    if n < 3:
        return None, None, None
    
    # Calcular estadístico S
    s = 0
    for i in range(n-1):
        for j in range(i+1, n):
            if data[j] > data[i]:
                s += 1
            elif data[j] < data[i]:
                s -= 1
    
    # Calcular varianza
    var_s = n * (n - 1) * (2 * n + 5) / 18
    
    # Estadístico Z normalizado
    if s > 0:
        z = (s - 1) / np.sqrt(var_s)
    elif s < 0:
        z = (s + 1) / np.sqrt(var_s)
    else:
        z = 0
    
    # p-valor (bilateral)
    p_value = 2 * (1 - stats.norm.cdf(abs(z)))
    
    return s, z, p_value

def sens_slope_estimator(años, valores):
    """
    Estimador de pendiente de Sen - robusto contra outliers
    Calcula la mediana de todas las pendientes posibles entre pares de puntos
    """
    n = len(años)
    if n < 2:
        return None
    
    slopes = []
    for i in range(n-1):
        for j in range(i+1, n):
            if años[j] != años[i]:
                slope = (valores[j] - valores[i]) / (años[j] - años[i])
                slopes.append(slope)
    
    if slopes:
        return np.median(slopes)
    else:
        return None

def theil_sen_regression(años, valores):
    """
    Regresión Theil-Sen completa - muy robusta contra outliers
    """
    try:
        from scipy.stats import theilslopes
        slope, intercept, low_slope, high_slope = theilslopes(valores, años)
        return slope, intercept
    except:
        # Fallback a implementación manual
        slope = sens_slope_estimator(años, valores)
        if slope is not None:
            # Calcular intercept usando mediana de residuos
            años_median = np.median(años)
            valores_median = np.median(valores)
            intercept = valores_median - slope * años_median
            return slope, intercept
        return None, None

def main():
    print("=== CORRECCIÓN 2023 + TENDENCIA ROBUSTA ===")
    
    conn = sqlite3.connect('reasis_database.db')
    
    try:
        # 1. Corregir matrícula 2023 desde CSV
        print("\n1. CORRIGIENDO MATRÍCULA 2023 DESDE CSV...")
        
        # Leer CSV 2023
        df_2023 = pd.read_csv('data/siagie_procesado/siagie_fya_2023_completo.csv')
        print(f"   - Registros en CSV 2023: {len(df_2023)}")
        
        # Agrupar por código modular normalizado
        matricula_2023 = df_2023.groupby('codigo_modular_norm')['total_alumnos_norm'].sum().reset_index()
        matricula_2023.columns = ['codigo_modular', 'matric_siagie_2023']
        
        print(f"   - Instituciones únicas en 2023: {len(matricula_2023)}")
        
        # Actualizar base de datos
        cursor = conn.cursor()
        actualizaciones_2023 = 0
        
        for idx, row in matricula_2023.iterrows():
            codigo = str(row['codigo_modular'])
            matricula = int(row['matric_siagie_2023'])
            
            cursor.execute("""
                UPDATE instituciones_educativas 
                SET matric_siagie_2023 = ?
                WHERE codigo_modular = ?
            """, (matricula, codigo))
            
            if cursor.rowcount > 0:
                actualizaciones_2023 += 1
        
        conn.commit()
        print(f"   - Registros 2023 actualizados: {actualizaciones_2023}")
        
        # 2. Recargar datos completos para tendencia robusta
        print("\n2. RECARGANDO DATOS COMPLETOS (6 AÑOS)...")
        
        query = """
        SELECT 
            codigo_modular,
            nombre_institucion,
            matric_siagie_2019,
            matric_siagie_2020,
            matric_siagie_2021,
            matric_siagie_2022,
            matric_siagie_2023,
            matric_siagie_2024,
            nombre_red_fya_matched as red_fya
        FROM instituciones_educativas 
        WHERE codigo_modular IS NOT NULL
        """
        
        df = pd.read_sql_query(query, conn)
        
        # Verificar cobertura 2023 actualizada
        cobertura_2023 = df['matric_siagie_2023'].notna().sum()
        print(f"   - Cobertura 2023 actualizada: {cobertura_2023}/{len(df)} ({(cobertura_2023/len(df))*100:.1f}%)")
        
        # 3. Calcular tendencias robustas
        print("\n3. CALCULANDO TENDENCIAS ROBUSTAS (MÉTODO THEIL-SEN + MANN-KENDALL)...")
        
        años = [2019, 2020, 2021, 2022, 2023, 2024]
        resultados_robustos = []
        
        for idx, row in df.iterrows():
            codigo = row['codigo_modular']
            nombre = row['nombre_institucion']
            red = row['red_fya']
            
            # Recopilar datos disponibles
            datos_disponibles = []
            for año in años:
                valor = row[f'matric_siagie_{año}']
                if pd.notna(valor) and valor > 0:
                    datos_disponibles.append((año, int(valor)))
            
            # Calcular tendencia robusta si hay al menos 4 puntos
            if len(datos_disponibles) >= 4:
                años_datos = np.array([d[0] for d in datos_disponibles])
                valores_datos = np.array([d[1] for d in datos_disponibles])
                
                # MÉTODO 1: Theil-Sen regression (robusto)
                slope_theil, intercept_theil = theil_sen_regression(años_datos, valores_datos)
                
                # MÉTODO 2: Mann-Kendall test para significancia
                s_mk, z_mk, p_mk = mann_kendall_test(valores_datos)
                
                # MÉTODO 3: Regresión lineal tradicional (para comparación)
                slope_ols, intercept_ols, r_ols, p_ols, stderr_ols = linregress(años_datos, valores_datos)
                
                # Categorización robusta usando Theil-Sen + Mann-Kendall
                if p_mk is not None and p_mk < 0.05:  # Significativo
                    if slope_theil > 2:
                        categoria_robusta = 'CRECIMIENTO_SIGNIFICATIVO'
                    elif slope_theil < -2:
                        categoria_robusta = 'DECRECIMIENTO_SIGNIFICATIVO'
                    else:
                        categoria_robusta = 'CAMBIO_LEVE_SIGNIFICATIVO'
                else:  # No significativo
                    categoria_robusta = 'ESTABLE'
                
                # Calcular métricas adicionales
                valor_inicial = valores_datos[0]
                valor_final = valores_datos[-1]
                cambio_total = valor_final - valor_inicial
                cambio_porcentual = (cambio_total / valor_inicial) * 100 if valor_inicial > 0 else 0
                
                # Calcular variabilidad (coeficiente de variación)
                cv = np.std(valores_datos) / np.mean(valores_datos) * 100
                
                resultado = {
                    'codigo_modular': codigo,
                    'nombre_institucion': nombre[:50],
                    'red_fya': red,
                    'años_datos': len(datos_disponibles),
                    'período': f"{min(años_datos)}-{max(años_datos)}",
                    'matricula_inicial': valor_inicial,
                    'matricula_final': valor_final,
                    'cambio_total': cambio_total,
                    'cambio_porcentual': cambio_porcentual,
                    
                    # Métrica robusta principal
                    'tendencia_theil_sen': slope_theil,
                    'intercept_theil_sen': intercept_theil,
                    
                    # Test Mann-Kendall
                    'mann_kendall_s': s_mk,
                    'mann_kendall_z': z_mk,
                    'mann_kendall_p': p_mk,
                    
                    # Comparación con OLS
                    'tendencia_ols': slope_ols,
                    'r2_ols': r_ols**2,
                    'p_valor_ols': p_ols,
                    
                    # Categorización final
                    'categoria_robusta': categoria_robusta,
                    
                    # Métricas de calidad
                    'coef_variacion': cv,
                    'datos_completos': ', '.join([f'{a}:{v}' for a, v in datos_disponibles])
                }
                
                resultados_robustos.append(resultado)
        
        df_robustos = pd.DataFrame(resultados_robustos)
        print(f"   - Tendencias robustas calculadas: {len(df_robustos)} instituciones")
        
        # 4. Estadísticas comparativas
        print("\n4. ESTADÍSTICAS MÉTODO ROBUSTO vs TRADICIONAL...")
        
        print(f"   DISTRIBUCIÓN CATEGORÍAS ROBUSTAS:")
        conteo_robustas = df_robustos['categoria_robusta'].value_counts()
        for categoria, count in conteo_robustas.items():
            porcentaje = (count / len(df_robustos)) * 100
            print(f"   - {categoria}: {count} ({porcentaje:.1f}%)")
        
        print(f"\n   COMPARACIÓN PENDIENTES:")
        print(f"   - Theil-Sen media: {df_robustos['tendencia_theil_sen'].mean():.3f}")
        print(f"   - OLS media: {df_robustos['tendencia_ols'].mean():.3f}")
        print(f"   - Diferencia media: {abs(df_robustos['tendencia_theil_sen'] - df_robustos['tendencia_ols']).mean():.3f}")
        
        # Correlación entre métodos
        correlacion = df_robustos['tendencia_theil_sen'].corr(df_robustos['tendencia_ols'])
        print(f"   - Correlación Theil-Sen vs OLS: {correlacion:.3f}")
        
        # 5. Casos donde los métodos difieren significativamente
        print("\n5. CASOS CON DIFERENCIAS SIGNIFICATIVAS ENTRE MÉTODOS...")
        
        df_robustos['diferencia_metodos'] = abs(df_robustos['tendencia_theil_sen'] - df_robustos['tendencia_ols'])
        casos_diferentes = df_robustos.nlargest(5, 'diferencia_metodos')
        
        for idx, row in casos_diferentes.iterrows():
            print(f"   - {row['codigo_modular']}: Theil-Sen={row['tendencia_theil_sen']:.2f}, OLS={row['tendencia_ols']:.2f} (diff: {row['diferencia_metodos']:.2f})")
        
        # 6. Guardar resultados
        print("\n6. GUARDANDO RESULTADOS ROBUSTOS...")
        
        # Guardar tabla completa
        df_robustos.to_sql('tendencias_matricula_robustas', conn, if_exists='replace', index=False)
        print(f"   - Tabla 'tendencias_matricula_robustas' creada")
        
        # 7. Actualizar tabla principal con método robusto
        print("\n7. ACTUALIZANDO CON MÉTODO ROBUSTO...")
        
        # Crear nuevas columnas robustas
        cursor.execute("PRAGMA table_info(instituciones_educativas)")
        columnas_existentes = [col[1] for col in cursor.fetchall()]
        
        nuevas_columnas_robustas = [
            ('X13_TMATRC', 'REAL'),
            ('X13_TMATRC_CATEGORIA', 'TEXT'),
            ('X13_TMATRC_MANN_KENDALL_P', 'REAL'),
            ('X13_TMATRC_COEF_VARIACION', 'REAL')
        ]
        
        for col_name, col_type in nuevas_columnas_robustas:
            if col_name not in columnas_existentes:
                cursor.execute(f"ALTER TABLE instituciones_educativas ADD COLUMN {col_name} {col_type}")
                print(f"   - Columna {col_name} creada")
        
        # Actualizar valores robustos
        actualizaciones_robustas = 0
        
        for idx, row in df_robustos.iterrows():
            cursor.execute("""
                UPDATE instituciones_educativas 
                SET X13_TMATRC = ?,
                    X13_TMATRC_CATEGORIA = ?,
                    X13_TMATRC_MANN_KENDALL_P = ?,
                    X13_TMATRC_COEF_VARIACION = ?
                WHERE codigo_modular = ?
            """, (
                row['tendencia_theil_sen'],
                row['categoria_robusta'], 
                row['mann_kendall_p'],
                row['coef_variacion'],
                row['codigo_modular']
            ))
            actualizaciones_robustas += 1
        
        conn.commit()
        print(f"   - {actualizaciones_robustas} registros actualizados con método robusto")
        
        # 8. Resumen final
        print(f"\n=== CORRECCIÓN Y MEJORA COMPLETADA ===")
        print(f"✅ Matrícula 2023 corregida: {actualizaciones_2023} instituciones")
        print(f"✅ Tendencias robustas: {len(df_robustos)} instituciones")
        print(f"✅ Método: Theil-Sen + Mann-Kendall (robusto contra outliers)")
        print(f"✅ Variables disponibles: X13_TMATRC, X13_TMATRC_CATEGORIA")
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        return False
    
    finally:
        conn.close()

if __name__ == "__main__":
    main()