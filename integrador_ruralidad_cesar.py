#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pandas as pd
import sqlite3
import numpy as np

def integrar_ruralidad_cesar():
    """Integra datos de ruralidad del archivo de César con la base de datos principal"""
    print("=== INTEGRADOR RURALIDAD CÉSAR ===\n")
    
    # Conectar a la base de datos
    conn = sqlite3.connect('reasis_database.db')
    
    # Cargar archivo César
    archivo_cesar = r"C:\Users\lucas\Proyectos\Reasis\assets\Consultoria\Información actualizada\Extras\Información solicitada a César.xlsx"
    
    try:
        print("Cargando archivo César...")
        df_cesar = pd.read_excel(archivo_cesar, engine='openpyxl')
        print(f"[OK] Archivo cargado: {len(df_cesar):,} registros")
        
        # Normalizar códigos modulares
        df_cesar['cod_mod_norm'] = df_cesar['cod_mod'].astype(str).str.zfill(7)
        
        # Obtener instituciones de nuestra base de datos
        query_bd = "SELECT codigo_modular, nombre_institucion FROM instituciones_educativas"
        df_bd = pd.read_sql_query(query_bd, conn)
        
        # Encontrar instituciones compatibles
        codigos_bd = set(df_bd['codigo_modular'].tolist())
        df_compatibles = df_cesar[df_cesar['cod_mod_norm'].isin(codigos_bd)].copy()
        
        print(f"[OK] Instituciones compatibles encontradas: {len(df_compatibles)}")
        
        # Filtrar solo las que tienen ruralidad definida
        df_con_ruralidad = df_compatibles[df_compatibles['ruralidad'].notna()].copy()
        print(f"[OK] Instituciones con ruralidad definida: {len(df_con_ruralidad)}")
        
        # Mostrar distribución de ruralidad
        print(f"\n=== DISTRIBUCIÓN RURALIDAD ===")
        ruralidad_dist = df_con_ruralidad['ruralidad'].value_counts()
        for categoria, count in ruralidad_dist.items():
            print(f"  {categoria}: {count} instituciones")
        
        # Crear tabla de ruralidad César si no existe
        query_crear_tabla = """
        CREATE TABLE IF NOT EXISTS ruralidad_cesar (
            codigo_modular TEXT PRIMARY KEY,
            tipo_ruralidad_cesar TEXT,
            centro_educativo TEXT,
            nivel_educativo TEXT,
            red_fya TEXT,
            modalidad TEXT,
            codigo_local TEXT,
            fecha_integracion TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (codigo_modular) REFERENCES instituciones_educativas(codigo_modular)
        )
        """
        
        conn.execute(query_crear_tabla)
        print(f"[OK] Tabla ruralidad_cesar creada/verificada")
        
        # Preparar datos para inserción
        datos_insertar = []
        
        for idx, row in df_con_ruralidad.iterrows():
            datos = {
                'codigo_modular': row['cod_mod_norm'],
                'tipo_ruralidad_cesar': str(row['ruralidad']),
                'centro_educativo': str(row['cen_edu']) if pd.notna(row['cen_edu']) else None,
                'nivel_educativo': str(row['d_niv_mod']) if pd.notna(row['d_niv_mod']) else None,
                'red_fya': str(row['nfya']) if pd.notna(row['nfya']) else None,
                'modalidad': str(row['modal']) if pd.notna(row['modal']) else None,
                'codigo_local': str(int(row['codlocal'])) if pd.notna(row['codlocal']) else None
            }
            datos_insertar.append(datos)
        
        # Insertar datos
        query_insertar = """
        INSERT OR REPLACE INTO ruralidad_cesar 
        (codigo_modular, tipo_ruralidad_cesar, centro_educativo, nivel_educativo, 
         red_fya, modalidad, codigo_local)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        
        cursor = conn.cursor()
        for datos in datos_insertar:
            cursor.execute(query_insertar, (
                datos['codigo_modular'],
                datos['tipo_ruralidad_cesar'],
                datos['centro_educativo'],
                datos['nivel_educativo'],
                datos['red_fya'],
                datos['modalidad'],
                datos['codigo_local']
            ))
        
        conn.commit()
        print(f"[OK] Insertados {len(datos_insertar)} registros en tabla ruralidad_cesar")
        
        # Verificar inserción
        query_verificar = "SELECT COUNT(*) as total FROM ruralidad_cesar"
        resultado = pd.read_sql_query(query_verificar, conn)
        print(f"[OK] Total registros en tabla ruralidad: {resultado.iloc[0]['total']}")
        
        # Mostrar muestra de datos integrados
        print("\n=== MUESTRA DE DATOS INTEGRADOS ===")
        query_muestra = """
        SELECT rc.codigo_modular, ie.nombre_institucion, rc.tipo_ruralidad_cesar, rc.red_fya
        FROM ruralidad_cesar rc
        LEFT JOIN instituciones_educativas ie ON rc.codigo_modular = ie.codigo_modular
        LIMIT 5
        """
        muestra = pd.read_sql_query(query_muestra, conn)
        print(muestra.to_string())
        
        # Estadísticas finales por tipo de ruralidad
        print("\n=== ESTADÍSTICAS FINALES ===")
        query_stats = """
        SELECT tipo_ruralidad_cesar, COUNT(*) as count 
        FROM ruralidad_cesar 
        GROUP BY tipo_ruralidad_cesar 
        ORDER BY count DESC
        """
        stats = pd.read_sql_query(query_stats, conn)
        print("Distribución final por tipo ruralidad:")
        for _, row in stats.iterrows():
            print(f"  {row['tipo_ruralidad_cesar']}: {row['count']} instituciones")
        
        # Comparar con datos existentes de ruralidad
        print(f"\n=== COMPARACIÓN CON DATOS EXISTENTES ===")
        query_existente = """
        SELECT ie.area_censo, COUNT(*) as count 
        FROM instituciones_educativas ie
        WHERE ie.codigo_modular IN (SELECT codigo_modular FROM ruralidad_cesar)
        GROUP BY ie.area_censo
        """
        existente = pd.read_sql_query(query_existente, conn)
        print("Clasificación existente en BD:")
        for _, row in existente.iterrows():
            print(f"  {row['area_censo']}: {row['count']} instituciones")
        
        # Ver casos donde hay diferencias
        print(f"\n=== ANÁLISIS DE DIFERENCIAS ===")
        query_diferencias = """
        SELECT 
            ie.codigo_modular,
            ie.nombre_institucion,
            ie.area_censo as zona_actual,
            rc.tipo_ruralidad_cesar as zona_cesar
        FROM instituciones_educativas ie
        INNER JOIN ruralidad_cesar rc ON ie.codigo_modular = rc.codigo_modular
        WHERE ie.area_censo != rc.tipo_ruralidad_cesar
        LIMIT 10
        """
        diferencias = pd.read_sql_query(query_diferencias, conn)
        if len(diferencias) > 0:
            print(f"Instituciones con clasificación diferente ({len(diferencias)} casos):")
            print(diferencias.to_string())
        else:
            print("No hay diferencias entre clasificaciones existentes y César")
        
        # Mostrar resumen final
        print(f"\n=== RESUMEN INTEGRACIÓN ===")
        print(f"Instituciones con ruralidad César: {len(datos_insertar)}")
        print(f"Tipos de ruralidad disponibles: {len(stats)}")
        print(f"Cobertura de redes FyA: {df_con_ruralidad['nfya'].nunique()} redes")
        
        # Impacto en variable X2_TR
        print(f"\n=== IMPACTO EN VARIABLE X2_TR ===")
        print(f"ANTES: Clasificación básica rural/urbano")
        print(f"AHORA: {len(datos_insertar)} instituciones con clasificación Rural 1/2/3 específica")
        print(f"MEJORA: Granularidad detallada para clustering K-Means")
        
    except Exception as e:
        print(f"[ERROR] Error durante la integración: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    integrar_ruralidad_cesar()