#!/usr/bin/env python3
"""
Imputación inteligente de total_docentes usando ratio docentes/estudiantes por red FyA
"""

import sqlite3
import pandas as pd
import numpy as np

def main():
    print("=== IMPUTACIÓN TOTAL_DOCENTES POR RATIO RED FyA ===")
    
    conn = sqlite3.connect('reasis_database.db')
    
    try:
        # 1. Cargar datos de instituciones educativas
        print("\n1. CARGANDO DATOS...")
        query = """
        SELECT 
            codigo_modular,
            nombre_institucion,
            total_docentes,
            total_alumnos,
            nombre_red_fya_matched as red_fya,
            entra_estudio_clustering
        FROM instituciones_educativas
        WHERE total_alumnos IS NOT NULL AND total_alumnos > 0
        """
        
        df = pd.read_sql_query(query, conn)
        print(f"   - Total instituciones cargadas: {len(df)}")
        print(f"   - Con total_docentes: {df['total_docentes'].notna().sum()}")
        print(f"   - Sin total_docentes (NULL): {df['total_docentes'].isna().sum()}")
        
        # 2. Calcular ratios promedio por red FyA
        print("\n2. CALCULANDO RATIOS DOCENTES/ESTUDIANTES POR RED...")
        
        # Solo usar instituciones con ambos datos para calcular ratios
        df_completos = df[(df['total_docentes'].notna()) & (df['total_docentes'] > 0)]
        df_completos['ratio_doc_est'] = df_completos['total_docentes'] / df_completos['total_alumnos']
        
        # Calcular estadísticas por red
        ratios_por_red = df_completos.groupby('red_fya').agg({
            'ratio_doc_est': ['mean', 'median', 'std', 'count'],
            'total_alumnos': ['mean', 'min', 'max'],
            'total_docentes': ['mean', 'min', 'max']
        }).round(4)
        
        # Aplanar nombres de columnas
        ratios_por_red.columns = ['_'.join(col).strip() for col in ratios_por_red.columns]
        ratios_por_red = ratios_por_red.reset_index()
        
        print("   RATIOS DOCENTES/ESTUDIANTES POR RED:")
        for idx, row in ratios_por_red.iterrows():
            red = row['red_fya']
            ratio_mean = row['ratio_doc_est_mean']
            count = int(row['ratio_doc_est_count'])
            print(f"   - {red}: Ratio promedio = {ratio_mean:.4f} ({count} instituciones)")
        
        # 3. Identificar instituciones que necesitan imputación
        print("\n3. IDENTIFICANDO INSTITUCIONES PARA IMPUTACIÓN...")
        
        df_imputar = df[df['total_docentes'].isna()]
        print(f"   - Instituciones que necesitan imputación: {len(df_imputar)}")
        
        if len(df_imputar) > 0:
            print("   DESGLOSE POR RED:")
            desglose = df_imputar.groupby('red_fya').size()
            for red, count in desglose.items():
                print(f"   - {red}: {count} instituciones")
        
        # 4. Aplicar imputación
        print("\n4. APLICANDO IMPUTACIÓN...")
        
        df_resultado = df.copy()
        imputaciones_realizadas = []
        
        # Crear diccionario de ratios por red para lookup rápido
        ratios_dict = dict(zip(ratios_por_red['red_fya'], ratios_por_red['ratio_doc_est_mean']))
        
        for idx, row in df_imputar.iterrows():
            red = row['red_fya']
            total_alumnos = row['total_alumnos']
            
            if red in ratios_dict:
                ratio_red = ratios_dict[red]
                docentes_estimados = max(1, round(total_alumnos * ratio_red))  # Mínimo 1 docente
                
                # Actualizar el DataFrame resultado
                df_resultado.loc[idx, 'total_docentes'] = docentes_estimados
                
                imputaciones_realizadas.append({
                    'codigo_modular': row['codigo_modular'],
                    'nombre_institucion': row['nombre_institucion'][:30] + '...' if len(row['nombre_institucion']) > 30 else row['nombre_institucion'],
                    'red_fya': red,
                    'total_alumnos': total_alumnos,
                    'ratio_usado': ratio_red,
                    'docentes_estimados': docentes_estimados
                })
        
        print(f"   - Imputaciones realizadas: {len(imputaciones_realizadas)}")
        
        if len(imputaciones_realizadas) > 0:
            print(f"\n   MUESTRA DE IMPUTACIONES:")
            for i, imp in enumerate(imputaciones_realizadas[:5]):
                print(f"   {imp['codigo_modular']}: {imp['total_alumnos']} alumnos × {imp['ratio_usado']:.4f} = {imp['docentes_estimados']} docentes")
        
        # 5. Validar resultados finales
        print("\n5. VALIDACIÓN FINAL...")
        
        antes_completos = df['total_docentes'].notna().sum()
        despues_completos = df_resultado['total_docentes'].notna().sum()
        mejora = despues_completos - antes_completos
        
        print(f"   - Antes: {antes_completos} instituciones con total_docentes ({(antes_completos/len(df))*100:.1f}%)")
        print(f"   - Después: {despues_completos} instituciones con total_docentes ({(despues_completos/len(df))*100:.1f}%)")
        print(f"   - Mejora: +{mejora} instituciones (+{(mejora/len(df))*100:.1f} puntos porcentuales)")
        
        # 6. Guardar resultados en la base de datos
        print("\n6. GUARDANDO RESULTADOS...")
        
        # Actualizar solo las filas que se imputaron
        cursor = conn.cursor()
        actualizaciones = 0
        
        for imp in imputaciones_realizadas:
            cursor.execute("""
                UPDATE instituciones_educativas 
                SET total_docentes = ?
                WHERE codigo_modular = ?
            """, (imp['docentes_estimados'], imp['codigo_modular']))
            actualizaciones += 1
        
        conn.commit()
        print(f"   - Registros actualizados en BD: {actualizaciones}")
        
        # 7. Crear tabla de respaldo con detalles de imputación
        if len(imputaciones_realizadas) > 0:
            df_imputaciones = pd.DataFrame(imputaciones_realizadas)
            df_imputaciones.to_sql('imputaciones_docentes_log', conn, if_exists='replace', index=False)
            print(f"   - Log de imputaciones guardado en tabla 'imputaciones_docentes_log'")
        
        print(f"\n=== IMPUTACIÓN COMPLETADA EXITOSAMENTE ===")
        print(f"Cobertura final: {despues_completos}/{len(df)} instituciones ({(despues_completos/len(df))*100:.1f}%)")
        
    except Exception as e:
        print(f"Error en la imputación: {e}")
        conn.rollback()
    
    finally:
        conn.close()

if __name__ == "__main__":
    main()