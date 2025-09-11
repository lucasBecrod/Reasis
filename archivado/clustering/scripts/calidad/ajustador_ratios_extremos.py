#!/usr/bin/env python3
"""
FASE 2: Ajuste de Ratios Extremos
Identifica IIEE con X11_RED > 45 y ajusta número de docentes para mantener máximo realista
"""

import sqlite3
import pandas as pd
import numpy as np
from math import ceil

def main():
    print("=== FASE 2: AJUSTE DE RATIOS EXTREMOS ===")
    
    conn = sqlite3.connect('reasis_database.db')
    
    try:
        # 1. Identificar instituciones con ratios > 45
        print("\n1. IDENTIFICANDO INSTITUCIONES CON RATIOS > 45...")
        
        query = """
        SELECT 
            codigo_modular,
            nombre_institucion,
            total_alumnos,
            total_docentes,
            X11_RED,
            matric_siagie_2024,
            nombre_red_fya_matched as red_fya
        FROM instituciones_educativas 
        WHERE X11_RED > 45 AND total_alumnos > 0 AND total_docentes > 0
        ORDER BY X11_RED DESC
        """
        
        df_extremos = pd.read_sql_query(query, conn)
        
        print(f"   - Instituciones con ratio > 45: {len(df_extremos)}")
        
        if len(df_extremos) > 0:
            print(f"   CASOS EXTREMOS IDENTIFICADOS:")
            for idx, row in df_extremos.iterrows():
                print(f"   - {row['codigo_modular']}: {row['X11_RED']:.1f} estudiantes/docente ({row['total_alumnos']}/{row['total_docentes']})")
        
        # 2. Contrastar con datos SIAGIE 2024
        print(f"\n2. CONTRASTANDO CON DATOS SIAGIE 2024...")
        
        df_con_siagie = df_extremos[df_extremos['matric_siagie_2024'].notna()].copy()
        
        if len(df_con_siagie) > 0:
            print(f"   COMPARACIÓN ADMINISTRATIVO vs SIAGIE 2024:")
            for idx, row in df_con_siagie.iterrows():
                admin = row['total_alumnos']
                siagie = row['matric_siagie_2024']
                diff = admin - siagie
                print(f"   - {row['codigo_modular']}: Admin={admin}, SIAGIE={siagie} (diff: {diff})")
        
        # 3. Aplicar estrategia de ajuste
        print(f"\n3. APLICANDO ESTRATEGIA DE AJUSTE...")
        
        df_ajustes = []
        
        for idx, row in df_extremos.iterrows():
            codigo = row['codigo_modular']
            alumnos_admin = row['total_alumnos']
            alumnos_siagie = row['matric_siagie_2024'] if pd.notna(row['matric_siagie_2024']) else None
            docentes_actual = row['total_docentes']
            ratio_actual = row['X11_RED']
            
            # Estrategia: Usar el menor entre administrativo y SIAGIE si está disponible
            if alumnos_siagie is not None and alumnos_siagie < alumnos_admin:
                alumnos_para_calculo = int(alumnos_siagie)
                fuente_alumnos = "SIAGIE_2024"
            else:
                alumnos_para_calculo = alumnos_admin
                fuente_alumnos = "ADMIN"
            
            # Calcular docentes necesarios para mantener máximo 45 estudiantes/docente
            docentes_necesarios = max(1, ceil(alumnos_para_calculo / 45))
            
            # Nuevo ratio con docentes ajustados
            nuevo_ratio = alumnos_para_calculo / docentes_necesarios
            
            ajuste = {
                'codigo_modular': codigo,
                'nombre_institucion': row['nombre_institucion'][:40] + '...' if len(row['nombre_institucion']) > 40 else row['nombre_institucion'],
                'red_fya': row['red_fya'],
                'alumnos_admin': alumnos_admin,
                'alumnos_siagie': alumnos_siagie,
                'alumnos_para_calculo': alumnos_para_calculo,
                'fuente_alumnos': fuente_alumnos,
                'docentes_actual': docentes_actual,
                'docentes_necesarios': docentes_necesarios,
                'ratio_actual': ratio_actual,
                'nuevo_ratio': nuevo_ratio,
                'ajuste_aplicado': docentes_necesarios != docentes_actual
            }
            
            df_ajustes.append(ajuste)
        
        df_ajustes = pd.DataFrame(df_ajustes)
        
        # Mostrar ajustes propuestos
        print(f"   AJUSTES PROPUESTOS:")
        ajustes_reales = df_ajustes[df_ajustes['ajuste_aplicado']].copy()
        
        for idx, row in ajustes_reales.iterrows():
            print(f"   - {row['codigo_modular']}: {row['docentes_actual']}->{row['docentes_necesarios']} docentes, ratio {row['ratio_actual']:.1f}->{row['nuevo_ratio']:.1f}")
        
        # 4. Aplicar ajustes a la base de datos
        print(f"\n4. APLICANDO AJUSTES A LA BASE DE DATOS...")
        
        cursor = conn.cursor()
        
        # Crear columnas para trackear ajustes si no existen
        cursor.execute("PRAGMA table_info(instituciones_educativas)")
        columnas_existentes = [col[1] for col in cursor.fetchall()]
        
        if 'total_docentes_ajustado' not in columnas_existentes:
            cursor.execute("ALTER TABLE instituciones_educativas ADD COLUMN total_docentes_ajustado INTEGER")
            print("   - Columna total_docentes_ajustado creada")
            
        if 'X11_RED_ajustado' not in columnas_existentes:
            cursor.execute("ALTER TABLE instituciones_educativas ADD COLUMN X11_RED_ajustado REAL")
            print("   - Columna X11_RED_ajustado creada")
            
        if 'metodo_ajuste' not in columnas_existentes:
            cursor.execute("ALTER TABLE instituciones_educativas ADD COLUMN metodo_ajuste TEXT")
            print("   - Columna metodo_ajuste creada")
        
        # Aplicar ajustes
        ajustes_aplicados = 0
        
        for idx, row in df_ajustes.iterrows():
            codigo = row['codigo_modular']
            docentes_ajustado = row['docentes_necesarios']
            ratio_ajustado = row['nuevo_ratio']
            metodo = f"AJUSTE_MAX45_{row['fuente_alumnos']}"
            
            cursor.execute("""
                UPDATE instituciones_educativas 
                SET total_docentes_ajustado = ?,
                    X11_RED_ajustado = ?,
                    metodo_ajuste = ?
                WHERE codigo_modular = ?
            """, (docentes_ajustado, ratio_ajustado, metodo, codigo))
            
            ajustes_aplicados += 1
        
        conn.commit()
        print(f"   - {ajustes_aplicados} registros actualizados con ajustes")
        
        # 5. Actualizar todas las demás instituciones (sin ajuste)
        print(f"\n5. COMPLETANDO REGISTROS SIN AJUSTE...")
        
        # Para instituciones que no necesitaron ajuste
        cursor.execute("""
            UPDATE instituciones_educativas 
            SET total_docentes_ajustado = total_docentes,
                X11_RED_ajustado = X11_RED,
                metodo_ajuste = 'SIN_AJUSTE'
            WHERE metodo_ajuste IS NULL 
            AND total_docentes IS NOT NULL 
            AND X11_RED IS NOT NULL
        """)
        
        registros_sin_ajuste = cursor.rowcount
        conn.commit()
        
        print(f"   - {registros_sin_ajuste} registros completados sin ajuste")
        
        # 6. Validación final
        print(f"\n6. VALIDACIÓN FINAL...")
        
        query_validacion = """
        SELECT 
            COUNT(*) as total,
            AVG(X11_RED_ajustado) as promedio_ajustado,
            MIN(X11_RED_ajustado) as min_ajustado,
            MAX(X11_RED_ajustado) as max_ajustado,
            COUNT(CASE WHEN metodo_ajuste != 'SIN_AJUSTE' THEN 1 END) as con_ajuste
        FROM instituciones_educativas 
        WHERE X11_RED_ajustado IS NOT NULL
        """
        
        stats = pd.read_sql_query(query_validacion, conn).iloc[0]
        
        print(f"   ESTADÍSTICAS POST-AJUSTE:")
        print(f"   - Total instituciones: {int(stats['total'])}")
        print(f"   - Con ajuste aplicado: {int(stats['con_ajuste'])}")
        print(f"   - X11_RED promedio: {stats['promedio_ajustado']:.2f}")
        print(f"   - X11_RED rango: {stats['min_ajustado']:.2f} - {stats['max_ajustado']:.2f}")
        
        # Guardar log de ajustes
        if len(df_ajustes) > 0:
            df_ajustes.to_sql('log_ajustes_ratios', conn, if_exists='replace', index=False)
            print(f"   - Log de ajustes guardado en tabla 'log_ajustes_ratios'")
        
        print(f"\n=== FASE 2 COMPLETADA ===")
        print(f"Ratios ajustados: {len(ajustes_reales)} instituciones")
        print(f"Máximo ratio final: {stats['max_ajustado']:.2f} estudiantes/docente")
        
        return True
        
    except Exception as e:
        print(f"Error en Fase 2: {e}")
        conn.rollback()
        return False
    
    finally:
        conn.close()

if __name__ == "__main__":
    main()