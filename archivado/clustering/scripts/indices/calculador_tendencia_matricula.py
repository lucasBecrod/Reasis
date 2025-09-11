#!/usr/bin/env python3
"""
FASE 3: Calculador de Tendencia de Matrícula
Calcula la evolución de estudiantes matriculados 2019-2024 como nueva variable
"""

import sqlite3
import pandas as pd
import numpy as np
from scipy.stats import linregress

def main():
    print("=== FASE 3: TENDENCIA DE MATRÍCULA 2019-2024 ===")
    
    conn = sqlite3.connect('reasis_database.db')
    
    try:
        # 1. Cargar datos de matrícula por año
        print("\n1. CARGANDO DATOS DE MATRÍCULA POR AÑO...")
        
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
        print(f"   - Instituciones cargadas: {len(df)}")
        
        # 2. Análisis de completitud de datos
        print("\n2. ANÁLISIS DE COMPLETITUD...")
        
        años = [2019, 2020, 2021, 2022, 2024]  # Excluir 2023 que tiene 0% cobertura
        
        for año in años:
            col_name = f'matric_siagie_{año}'
            no_nulos = df[col_name].notna().sum()
            porcentaje = (no_nulos / len(df)) * 100
            print(f"   - {año}: {no_nulos}/{len(df)} instituciones ({porcentaje:.1f}%)")
        
        # 3. Calcular tendencias por institución
        print("\n3. CALCULANDO TENDENCIAS POR INSTITUCIÓN...")
        
        resultados_tendencias = []
        
        for idx, row in df.iterrows():
            codigo = row['codigo_modular']
            nombre = row['nombre_institucion']
            red = row['red_fya']
            
            # Recopilar datos disponibles por año
            datos_año = []
            for año in años:
                valor = row[f'matric_siagie_{año}']
                if pd.notna(valor) and valor > 0:
                    datos_año.append((año, int(valor)))
            
            # Calcular tendencia si hay al menos 3 puntos de datos
            if len(datos_año) >= 3:
                años_datos = [d[0] for d in datos_año]
                valores_datos = [d[1] for d in datos_año]
                
                # Regresión lineal
                slope, intercept, r_value, p_value, std_err = linregress(años_datos, valores_datos)
                
                # Categorización de tendencia
                if slope > 5:
                    categoria = 'CRECIMIENTO'
                elif slope < -5:
                    categoria = 'DECRECIMIENTO'  
                else:
                    categoria = 'ESTABLE'
                
                # Calcular cambio porcentual total
                valor_inicial = valores_datos[0]
                valor_final = valores_datos[-1]
                cambio_porcentual = ((valor_final - valor_inicial) / valor_inicial) * 100
                
                resultado = {
                    'codigo_modular': codigo,
                    'nombre_institucion': nombre[:50],
                    'red_fya': red,
                    'años_datos': len(datos_año),
                    'año_inicial': años_datos[0],
                    'año_final': años_datos[-1],
                    'matricula_inicial': valor_inicial,
                    'matricula_final': valor_final,
                    'tendencia_pendiente': slope,
                    'tendencia_r2': r_value**2,
                    'tendencia_p_valor': p_value,
                    'cambio_porcentual': cambio_porcentual,
                    'categoria_tendencia': categoria,
                    'datos_completos': ', '.join([f'{a}:{v}' for a, v in datos_año])
                }
                
                resultados_tendencias.append(resultado)
        
        df_tendencias = pd.DataFrame(resultados_tendencias)
        print(f"   - Tendencias calculadas: {len(df_tendencias)} instituciones")
        
        # 4. Estadísticas descriptivas de tendencias
        print("\n4. ESTADÍSTICAS DESCRIPTIVAS...")
        
        print(f"   DISTRIBUCIÓN POR CATEGORÍA:")
        conteo_categorias = df_tendencias['categoria_tendencia'].value_counts()
        for categoria, count in conteo_categorias.items():
            porcentaje = (count / len(df_tendencias)) * 100
            print(f"   - {categoria}: {count} instituciones ({porcentaje:.1f}%)")
        
        print(f"   ESTADÍSTICAS DE PENDIENTE:")
        print(f"   - Media: {df_tendencias['tendencia_pendiente'].mean():.2f} estudiantes/año")
        print(f"   - Mediana: {df_tendencias['tendencia_pendiente'].median():.2f} estudiantes/año")
        print(f"   - Desviación estándar: {df_tendencias['tendencia_pendiente'].std():.2f}")
        print(f"   - Rango: {df_tendencias['tendencia_pendiente'].min():.2f} a {df_tendencias['tendencia_pendiente'].max():.2f}")
        
        print(f"   ESTADÍSTICAS DE CAMBIO PORCENTUAL:")
        print(f"   - Media: {df_tendencias['cambio_porcentual'].mean():.1f}%")
        print(f"   - Mediana: {df_tendencias['cambio_porcentual'].median():.1f}%")
        
        # 5. Análisis por red Fe y Alegría
        print("\n5. ANÁLISIS POR RED FE Y ALEGRÍA...")
        
        red_stats = df_tendencias.groupby('red_fya').agg({
            'tendencia_pendiente': ['count', 'mean', 'median'],
            'cambio_porcentual': ['mean', 'median']
        }).round(2)
        
        red_stats.columns = ['count', 'pendiente_media', 'pendiente_mediana', 'cambio_pct_medio', 'cambio_pct_mediana']
        
        for red, row in red_stats.iterrows():
            print(f"   - {red}: {int(row['count'])} IIEE, Pendiente={row['pendiente_media']:.2f}, Cambio={row['cambio_pct_medio']:.1f}%")
        
        # 6. Casos extremos
        print("\n6. CASOS EXTREMOS...")
        
        # Mayor crecimiento
        mayor_crecimiento = df_tendencias.nlargest(3, 'tendencia_pendiente')
        print(f"   MAYOR CRECIMIENTO:")
        for idx, row in mayor_crecimiento.iterrows():
            print(f"   - {row['codigo_modular']}: +{row['tendencia_pendiente']:.1f} estudiantes/año ({row['cambio_porcentual']:.1f}%)")
        
        # Mayor decrecimiento
        mayor_decrecimiento = df_tendencias.nsmallest(3, 'tendencia_pendiente')
        print(f"   MAYOR DECRECIMIENTO:")
        for idx, row in mayor_decrecimiento.iterrows():
            print(f"   - {row['codigo_modular']}: {row['tendencia_pendiente']:.1f} estudiantes/año ({row['cambio_porcentual']:.1f}%)")
        
        # 7. Guardar resultados
        print("\n7. GUARDANDO RESULTADOS...")
        
        # Guardar tabla completa de tendencias
        df_tendencias.to_sql('tendencias_matricula', conn, if_exists='replace', index=False)
        print(f"   - Tabla 'tendencias_matricula' creada con {len(df_tendencias)} registros")
        
        # 8. Actualizar tabla instituciones_educativas
        print("\n8. ACTUALIZANDO TABLA INSTITUCIONES_EDUCATIVAS...")
        
        cursor = conn.cursor()
        
        # Crear columnas si no existen
        cursor.execute("PRAGMA table_info(instituciones_educativas)")
        columnas_existentes = [col[1] for col in cursor.fetchall()]
        
        nuevas_columnas = [
            ('TEND_MATRICULA', 'REAL'),
            ('TEND_MATRICULA_CATEGORIA', 'TEXT'),
            ('TEND_MATRICULA_R2', 'REAL'),
            ('TEND_CAMBIO_PORCENTUAL', 'REAL')
        ]
        
        for col_name, col_type in nuevas_columnas:
            if col_name not in columnas_existentes:
                cursor.execute(f"ALTER TABLE instituciones_educativas ADD COLUMN {col_name} {col_type}")
                print(f"   - Columna {col_name} creada")
        
        # Actualizar valores
        actualizaciones = 0
        
        for idx, row in df_tendencias.iterrows():
            cursor.execute("""
                UPDATE instituciones_educativas 
                SET TEND_MATRICULA = ?,
                    TEND_MATRICULA_CATEGORIA = ?,
                    TEND_MATRICULA_R2 = ?,
                    TEND_CAMBIO_PORCENTUAL = ?
                WHERE codigo_modular = ?
            """, (
                row['tendencia_pendiente'],
                row['categoria_tendencia'],
                row['tendencia_r2'],
                row['cambio_porcentual'],
                row['codigo_modular']
            ))
            actualizaciones += 1
        
        conn.commit()
        print(f"   - {actualizaciones} registros actualizados")
        
        # 9. Resumen final
        print(f"\n=== FASE 3 COMPLETADA ===")
        print(f"Variable TEND_MATRICULA calculada: {len(df_tendencias)} instituciones")
        print(f"Distribución: {conteo_categorias['CRECIMIENTO']} Crecimiento, {conteo_categorias['ESTABLE']} Estable, {conteo_categorias['DECRECIMIENTO']} Decrecimiento")
        print(f"Variable lista para clustering K-Means")
        
        return True
        
    except Exception as e:
        print(f"Error en Fase 3: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        return False
    
    finally:
        conn.close()

if __name__ == "__main__":
    main()