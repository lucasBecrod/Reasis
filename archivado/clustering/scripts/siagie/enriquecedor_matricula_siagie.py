#!/usr/bin/env python3
"""
FASE 1: Enriquecimiento con Datos SIAGIE por Año
Crea columnas matric_siagie_2019 hasta matric_siagie_2024 en tabla instituciones_educativas
"""

import sqlite3
import pandas as pd
import numpy as np
from math import ceil

def main():
    print("=== FASE 1: ENRIQUECIMIENTO CON DATOS SIAGIE ===")
    
    conn = sqlite3.connect('reasis_database.db')
    
    try:
        # 1. Cargar tabla instituciones_educativas
        print("\n1. CARGANDO TABLA INSTITUCIONES_EDUCATIVAS...")
        
        df_ie = pd.read_sql_query("""
            SELECT codigo_modular, nombre_institucion, total_alumnos, total_docentes, X11_RED
            FROM instituciones_educativas 
            WHERE codigo_modular IS NOT NULL
        """, conn)
        
        print(f"   - Instituciones cargadas: {len(df_ie)}")
        
        # 2. Extraer matriculados por año desde SIAGIE
        print("\n2. EXTRAYENDO MATRICULADOS POR AÑO DESDE SIAGIE...")
        
        años = [2019, 2020, 2021, 2022, 2023, 2024]
        matriculas_por_año = {}
        
        for año in años:
            print(f"   - Procesando año {año}...")
            
            query_año = f"""
            SELECT 
                codigo_modular_norm as codigo_modular,
                SUM(total_alumnos_norm) as matriculados_{año}
            FROM matriculas_siagie 
            WHERE anio = {año}
            GROUP BY codigo_modular_norm
            """
            
            df_año = pd.read_sql_query(query_año, conn)
            matriculas_por_año[año] = df_año
            
            print(f"     * {len(df_año)} instituciones con datos")
        
        # 3. Consolidar todas las matriculas por año
        print("\n3. CONSOLIDANDO MATRICULAS POR AÑO...")
        
        # Empezar con la tabla base
        df_consolidado = df_ie[['codigo_modular', 'nombre_institucion']].copy()
        df_consolidado['codigo_modular_str'] = df_consolidado['codigo_modular'].astype(str)
        
        # Añadir cada año
        for año in años:
            df_año = matriculas_por_año[año].copy()
            df_año['codigo_modular_str'] = df_año['codigo_modular'].astype(str)
            
            # Merge con datos consolidados
            df_consolidado = df_consolidado.merge(
                df_año[['codigo_modular_str', f'matriculados_{año}']],
                on='codigo_modular_str',
                how='left'
            )
            
            # Renombrar columna
            df_consolidado = df_consolidado.rename(columns={f'matriculados_{año}': f'matric_siagie_{año}'})
        
        # Limpiar columna auxiliar
        df_consolidado = df_consolidado.drop('codigo_modular_str', axis=1)
        
        print("   RESUMEN DE COBERTURA POR AÑO:")
        for año in años:
            col_name = f'matric_siagie_{año}'
            no_nulos = df_consolidado[col_name].notna().sum()
            porcentaje = (no_nulos / len(df_consolidado)) * 100
            print(f"   - {año}: {no_nulos}/{len(df_consolidado)} instituciones ({porcentaje:.1f}%)")
        
        # 4. Añadir columnas a tabla instituciones_educativas
        print("\n4. AÑADIENDO COLUMNAS A TABLA INSTITUCIONES_EDUCATIVAS...")
        
        cursor = conn.cursor()
        
        # Verificar/crear columnas
        cursor.execute("PRAGMA table_info(instituciones_educativas)")
        columnas_existentes = [col[1] for col in cursor.fetchall()]
        
        for año in años:
            col_name = f'matric_siagie_{año}'
            if col_name not in columnas_existentes:
                cursor.execute(f"ALTER TABLE instituciones_educativas ADD COLUMN {col_name} INTEGER")
                print(f"   - Columna {col_name} creada")
        
        # 5. Actualizar valores en la tabla
        print("\n5. ACTUALIZANDO VALORES...")
        
        actualizaciones_totales = 0
        
        for idx, row in df_consolidado.iterrows():
            codigo = row['codigo_modular']
            
            # Construir query de actualización dinámicamente
            updates = []
            values = []
            
            for año in años:
                col_name = f'matric_siagie_{año}'
                valor = row[col_name]
                
                if pd.notna(valor):
                    updates.append(f"{col_name} = ?")
                    values.append(int(valor))
            
            if updates:
                values.append(codigo)
                query_update = f"""
                    UPDATE instituciones_educativas 
                    SET {', '.join(updates)}
                    WHERE codigo_modular = ?
                """
                cursor.execute(query_update, values)
                actualizaciones_totales += 1
        
        conn.commit()
        print(f"   - {actualizaciones_totales} instituciones actualizadas")
        
        # 6. Validación y estadísticas finales
        print("\n6. VALIDACIÓN FINAL...")
        
        # Recargar datos actualizados
        query_validacion = f"""
        SELECT 
            codigo_modular,
            total_alumnos,
            {', '.join([f'matric_siagie_{año}' for año in años])}
        FROM instituciones_educativas 
        WHERE codigo_modular IS NOT NULL
        """
        
        df_validacion = pd.read_sql_query(query_validacion, conn)
        
        # Comparar total_alumnos vs matricula más reciente
        df_validacion['matric_2024_vs_admin'] = df_validacion['matric_siagie_2024'] - df_validacion['total_alumnos']
        
        comparables = df_validacion[(df_validacion['total_alumnos'].notna()) & 
                                   (df_validacion['matric_siagie_2024'].notna())]
        
        if len(comparables) > 0:
            print(f"   COMPARACIÓN 2024 SIAGIE vs ADMINISTRATIVO:")
            print(f"   - Instituciones comparables: {len(comparables)}")
            print(f"   - Diferencia promedio: {comparables['matric_2024_vs_admin'].mean():.1f} estudiantes")
            print(f"   - Diferencia absoluta promedio: {abs(comparables['matric_2024_vs_admin']).mean():.1f} estudiantes")
            
            # Casos con grandes diferencias
            grandes_diff = comparables[abs(comparables['matric_2024_vs_admin']) > 20]
            print(f"   - Casos con diferencia >20: {len(grandes_diff)} instituciones")
        
        print(f"\n=== FASE 1 COMPLETADA ===")
        print(f"Columnas creadas: matric_siagie_2019 hasta matric_siagie_2024")
        print(f"Datos listos para siguiente fase (ajuste de ratios)")
        
        return True
        
    except Exception as e:
        print(f"Error en Fase 1: {e}")
        conn.rollback()
        return False
    
    finally:
        conn.close()

if __name__ == "__main__":
    main()