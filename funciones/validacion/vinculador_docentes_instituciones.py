#!/usr/bin/env python3
"""
Vinculador Docentes-Instituciones - Proyecto Reasis
Vincula datos de docentes con tabla instituciones_educativas usando codigo_modular
"""

import pandas as pd
import sqlite3
from pathlib import Path

def analizar_vinculacion_posible():
    """Analizar qué códigos modulares de docentes existen en la tabla instituciones"""
    print("ANÁLISIS DE VINCULACIÓN DOCENTES-INSTITUCIONES")
    print("=" * 70)
    
    conn = sqlite3.connect('reasis_database.db')
    
    # 1. Códigos modulares únicos en docentes
    codigos_docentes = pd.read_sql_query('''
        SELECT DISTINCT codigo_modular_actual
        FROM docentes_data
        WHERE codigo_modular_actual IS NOT NULL AND codigo_modular_actual != ''
        ORDER BY codigo_modular_actual
    ''', conn)
    
    print(f"\n1. CÓDIGOS MODULARES EN DATOS DOCENTES")
    print("-" * 50)
    print(f"Códigos únicos en docentes: {len(codigos_docentes)}")
    
    # 2. Códigos modulares en instituciones
    codigos_instituciones = pd.read_sql_query('''
        SELECT DISTINCT codigo_modular
        FROM instituciones_educativas
        WHERE codigo_modular IS NOT NULL AND codigo_modular != ''
        ORDER BY codigo_modular
    ''', conn)
    
    print(f"Códigos únicos en instituciones: {len(codigos_instituciones)}")
    
    # 3. Análisis de coincidencias
    set_docentes = set(codigos_docentes['codigo_modular_actual'].astype(str))
    set_instituciones = set(codigos_instituciones['codigo_modular'].astype(str))
    
    coincidencias = set_docentes.intersection(set_instituciones)
    solo_docentes = set_docentes - set_instituciones
    solo_instituciones = set_instituciones - set_docentes
    
    print(f"\n2. ANÁLISIS DE COINCIDENCIAS")
    print("-" * 50)
    print(f"Códigos que coinciden: {len(coincidencias)}")
    print(f"Solo en docentes: {len(solo_docentes)}")  
    print(f"Solo en instituciones: {len(solo_instituciones)}")
    
    porcentaje_vinculable = len(coincidencias) / len(set_docentes) * 100 if len(set_docentes) > 0 else 0
    print(f"Porcentaje vinculable: {porcentaje_vinculable:.1f}%")
    
    # 4. Mostrar algunos códigos que NO coinciden
    print(f"\n3. CÓDIGOS NO ENCONTRADOS EN INSTITUCIONES (MUESTRA)")
    print("-" * 60)
    if solo_docentes:
        # Contar registros afectados por código
        codigos_problematicos = pd.read_sql_query('''
            SELECT 
                codigo_modular_actual,
                COUNT(*) as registros_afectados
            FROM docentes_data
            WHERE codigo_modular_actual IS NOT NULL 
            AND codigo_modular_actual != ''
            GROUP BY codigo_modular_actual
            ORDER BY registros_afectados DESC
        ''', conn)
        
        codigos_problematicos = codigos_problematicos[
            codigos_problematicos['codigo_modular_actual'].astype(str).isin(solo_docentes)
        ]
        
        print("Top códigos no vinculables (más registros afectados):")
        print(codigos_problematicos.head(10).to_string(index=False))
    
    # 5. Verificar si hay coincidencias usando otros campos
    print(f"\n4. BÚSQUEDA ALTERNATIVA POR NOMBRES DE INSTITUCIONES")
    print("-" * 60)
    
    # Obtener nombres de instituciones desde docentes
    nombres_docentes = pd.read_sql_query('''
        SELECT DISTINCT 
            codigo_modular_actual,
            institucion_actual,
            COUNT(*) as registros
        FROM docentes_data
        WHERE institucion_actual IS NOT NULL 
        AND institucion_actual != ''
        AND codigo_modular_actual NOT IN (
            SELECT DISTINCT codigo_modular 
            FROM instituciones_educativas 
            WHERE codigo_modular IS NOT NULL
        )
        GROUP BY codigo_modular_actual, institucion_actual
        ORDER BY registros DESC
        LIMIT 20
    ''', conn)
    
    if len(nombres_docentes) > 0:
        print("Instituciones sin vincular - búsqueda por nombre posible:")
        print(nombres_docentes.to_string(index=False))
        
        # Intentar buscar por nombre
        encontradas_por_nombre = []
        for _, row in nombres_docentes.head(5).iterrows():
            nombre_buscar = row['institucion_actual']
            busqueda = pd.read_sql_query('''
                SELECT codigo_modular, nombre_institucion
                FROM instituciones_educativas
                WHERE UPPER(nombre_institucion) LIKE UPPER(?)
                LIMIT 5
            ''', conn, params=(f'%{nombre_buscar}%',))
            
            if len(busqueda) > 0:
                encontradas_por_nombre.append({
                    'codigo_docente': row['codigo_modular_actual'],
                    'nombre_docente': nombre_buscar,
                    'coincidencias': busqueda.to_dict('records')
                })
        
        if encontradas_por_nombre:
            print(f"\nPosibles coincidencias por nombre encontradas:")
            for item in encontradas_por_nombre:
                print(f"  Código docentes: {item['codigo_docente']} - {item['nombre_docente']}")
                for coincidencia in item['coincidencias']:
                    print(f"    -> {coincidencia['codigo_modular']}: {coincidencia['nombre_institucion']}")
    
    conn.close()
    
    return {
        'total_codigos_docentes': len(set_docentes),
        'coincidencias': len(coincidencias),
        'porcentaje_vinculable': porcentaje_vinculable,
        'codigos_coincidentes': list(coincidencias)
    }

def ejecutar_vinculacion():
    """Ejecutar vinculación de docentes con instituciones"""
    print(f"\n5. EJECUTANDO VINCULACIÓN")
    print("-" * 50)
    
    conn = sqlite3.connect('reasis_database.db')
    
    # Actualizar campo codigo_modular_vinculado usando JOIN
    update_sql = '''
        UPDATE docentes_data 
        SET 
            codigo_modular_vinculado = (
                SELECT ie.codigo_modular
                FROM instituciones_educativas ie
                WHERE ie.codigo_modular = docentes_data.codigo_modular_actual
                LIMIT 1
            ),
            metodo_vinculacion = 'codigo_modular_exacto'
        WHERE codigo_modular_actual IN (
            SELECT DISTINCT codigo_modular
            FROM instituciones_educativas
            WHERE codigo_modular IS NOT NULL
        )
    '''
    
    cursor = conn.cursor()
    cursor.execute(update_sql)
    registros_vinculados = cursor.rowcount
    
    conn.commit()
    conn.close()
    
    print(f"Registros vinculados exitosamente: {registros_vinculados}")
    
    return registros_vinculados

def generar_reporte_vinculacion():
    """Generar reporte de resultados de vinculación"""
    print(f"\n6. REPORTE DE VINCULACIÓN FINAL")
    print("-" * 50)
    
    conn = sqlite3.connect('reasis_database.db')
    
    # Estadísticas finales
    total = pd.read_sql_query('SELECT COUNT(*) as count FROM docentes_data', conn).iloc[0, 0]
    vinculados = pd.read_sql_query('''
        SELECT COUNT(*) as count 
        FROM docentes_data 
        WHERE codigo_modular_vinculado IS NOT NULL
    ''', conn).iloc[0, 0]
    
    porcentaje = vinculados / total * 100 if total > 0 else 0
    
    print(f"Total registros docentes: {total:,}")
    print(f"Registros vinculados: {vinculados:,}")
    print(f"Porcentaje de vinculación: {porcentaje:.1f}%")
    print(f"Registros sin vincular: {total - vinculados:,}")
    
    # Vinculación por año
    por_año = pd.read_sql_query('''
        SELECT 
            año,
            COUNT(*) as total,
            COUNT(codigo_modular_vinculado) as vinculados,
            ROUND(COUNT(codigo_modular_vinculado) * 100.0 / COUNT(*), 1) as porcentaje
        FROM docentes_data
        GROUP BY año
        ORDER BY año
    ''', conn)
    
    print(f"\nVinculación por año:")
    print(por_año.to_string(index=False))
    
    # Top instituciones por cantidad de docentes
    top_instituciones = pd.read_sql_query('''
        SELECT 
            d.codigo_modular_vinculado,
            ie.nombre_institucion,
            ie.area_censo,
            COUNT(*) as total_docentes,
            COUNT(DISTINCT d.dni) as docentes_unicos,
            COUNT(DISTINCT d.año) as años_con_datos
        FROM docentes_data d
        INNER JOIN instituciones_educativas ie ON d.codigo_modular_vinculado = ie.codigo_modular
        GROUP BY d.codigo_modular_vinculado, ie.nombre_institucion, ie.area_censo
        ORDER BY total_docentes DESC
        LIMIT 15
    ''', conn)
    
    if len(top_instituciones) > 0:
        print(f"\nTop 15 instituciones por cantidad de docentes:")
        print(top_instituciones.to_string(index=False))
    
    conn.close()
    
    return {
        'total': total,
        'vinculados': vinculados,
        'porcentaje': porcentaje
    }

def main():
    """Función principal"""
    print("VINCULADOR DOCENTES-INSTITUCIONES - PROYECTO REASIS")
    print("=" * 70)
    
    # Paso 1: Análisis
    stats_analisis = analizar_vinculacion_posible()
    
    # Paso 2: Vinculación
    registros_vinculados = ejecutar_vinculacion()
    
    # Paso 3: Reporte final
    stats_final = generar_reporte_vinculacion()
    
    print(f"\nPROCESO COMPLETADO")
    print("=" * 50)
    print(f"Vinculación exitosa: {stats_final['porcentaje']:.1f}%")
    print(f"Docentes ahora vinculados con instituciones educativas")
    print(f"Listos para calcular variables X4 (IDD), X5 (ED), X6 (CDD)")
    
    return stats_final

if __name__ == "__main__":
    results = main()