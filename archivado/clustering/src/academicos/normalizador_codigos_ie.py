#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Normalizador de Códigos IE - Proyecto Reasis
Script para obtener códigos modulares a partir de códigos de local + nivel educativo
"""

import sqlite3
import pandas as pd
import re
from difflib import SequenceMatcher

def analizar_estructura_codigos():
    """Analiza la estructura actual de códigos en los datos académicos"""
    print("ANÁLISIS DE ESTRUCTURA DE CÓDIGOS ACADÉMICOS")
    print("=" * 70)
    
    try:
        conn = sqlite3.connect('reasis_database.db')
        
        # Obtener muestra de datos académicos
        muestra = pd.read_sql_query("""
            SELECT codigo_ie, nombre_ie, nivel_educativo, materia, COUNT(*) as estudiantes
            FROM resultados_academicos 
            WHERE codigo_ie IS NOT NULL AND nombre_ie IS NOT NULL
            GROUP BY codigo_ie, nombre_ie, nivel_educativo, materia
            ORDER BY estudiantes DESC
            LIMIT 20
        """, conn)
        
        print("MUESTRA DE DATOS ACTUALES:")
        print("-" * 50)
        for idx, row in muestra.iterrows():
            print(f"Código Local: {row['codigo_ie']}")
            print(f"Nombre IE: {row['nombre_ie']}")
            print(f"Nivel: {row['nivel_educativo']}")
            print(f"Materia: {row['materia']}")
            print(f"Estudiantes: {row['estudiantes']}")
            print("-" * 30)
        
        # Obtener códigos únicos por nivel
        print("\nDISTRIBUCIÓN POR NIVEL EDUCATIVO:")
        print("-" * 50)
        
        por_nivel = pd.read_sql_query("""
            SELECT nivel_educativo, 
                   COUNT(DISTINCT codigo_ie) as codigos_locales,
                   COUNT(*) as total_estudiantes
            FROM resultados_academicos 
            WHERE codigo_ie IS NOT NULL
            GROUP BY nivel_educativo
        """, conn)
        
        for idx, row in por_nivel.iterrows():
            print(f"{row['nivel_educativo']}: {row['codigos_locales']} códigos locales, {row['total_estudiantes']} estudiantes")
        
        conn.close()
        
    except Exception as e:
        print(f"Error en análisis: {e}")

def buscar_codigo_modular(codigo_local, nivel, conn):
    """
    Busca el código modular correspondiente al código local + nivel
    """
    try:
        # Limpiar código local
        codigo_local_str = str(codigo_local).strip()
        
        # Determinar nivel normalizado
        nivel_normalizado = None
        if nivel and isinstance(nivel, str):
            nivel_lower = nivel.lower()
            if 'primaria' in nivel_lower:
                nivel_normalizado = 'Primaria'
            elif 'secundaria' in nivel_lower or 'secund' in nivel_lower:
                nivel_normalizado = 'Secundaria'
        
        # Buscar en tabla de instituciones
        # Primero buscar por código local exacto
        query_exacto = """
            SELECT codigo_modular, nombre_institucion, codigo_local, nivel_educativo
            FROM instituciones_educativas_v2_mejorada 
            WHERE codigo_local = ? OR codigo_modular LIKE ?
        """
        
        resultado = pd.read_sql_query(query_exacto, conn, params=[
            codigo_local_str,
            f"{codigo_local_str}%"
        ])
        
        if len(resultado) > 0:
            # Si hay coincidencias, filtrar por nivel si está disponible
            if nivel_normalizado:
                resultado_nivel = resultado[resultado['nivel_educativo'].str.contains(nivel_normalizado, na=False)]
                if len(resultado_nivel) > 0:
                    return resultado_nivel.iloc[0]['codigo_modular']
            
            # Si no hay filtro por nivel o no hay coincidencias, devolver el primer resultado
            return resultado.iloc[0]['codigo_modular']
        
        # Si no hay coincidencias exactas, buscar por similitud
        query_similar = """
            SELECT codigo_modular, nombre_institucion, codigo_local, nivel_educativo
            FROM instituciones_educativas_v2_mejorada 
            WHERE codigo_local LIKE ? OR codigo_modular LIKE ?
        """
        
        resultado_similar = pd.read_sql_query(query_similar, conn, params=[
            f"%{codigo_local_str[-4:]}%",  # Últimos 4 dígitos
            f"%{codigo_local_str}%"
        ])
        
        if len(resultado_similar) > 0:
            if nivel_normalizado:
                resultado_nivel = resultado_similar[resultado_similar['nivel_educativo'].str.contains(nivel_normalizado, na=False)]
                if len(resultado_nivel) > 0:
                    return resultado_nivel.iloc[0]['codigo_modular']
            return resultado_similar.iloc[0]['codigo_modular']
        
        return None
        
    except Exception as e:
        print(f"Error buscando código modular para {codigo_local}: {e}")
        return None

def normalizar_codigos_academicos():
    """
    Normaliza los códigos de los datos académicos obteniendo códigos modulares
    """
    print("\nNORMALIZACIÓN DE CÓDIGOS ACADÉMICOS")
    print("=" * 70)
    
    try:
        conn = sqlite3.connect('reasis_database.db')
        
        # Crear tabla temporal para mapeo de códigos
        print("Creando tabla de mapeo de códigos...")
        cursor = conn.cursor()
        cursor.execute("DROP TABLE IF EXISTS mapeo_codigos_ie")
        cursor.execute("""
            CREATE TABLE mapeo_codigos_ie (
                codigo_local TEXT,
                nivel_educativo TEXT,
                codigo_modular TEXT,
                nombre_ie_encontrado TEXT,
                metodo_encontrado TEXT,
                PRIMARY KEY (codigo_local, nivel_educativo)
            )
        """)
        
        # Obtener códigos únicos a normalizar
        codigos_normalizar = pd.read_sql_query("""
            SELECT DISTINCT codigo_ie, nivel_educativo, 
                   COUNT(*) as total_estudiantes
            FROM resultados_academicos 
            WHERE codigo_ie IS NOT NULL
            GROUP BY codigo_ie, nivel_educativo
            ORDER BY total_estudiantes DESC
        """, conn)
        
        print(f"Códigos únicos a procesar: {len(codigos_normalizar)}")
        print("\nProcesando códigos...")
        
        resultados_mapeo = []
        procesados = 0
        encontrados = 0
        
        for idx, row in codigos_normalizar.iterrows():
            codigo_local = row['codigo_ie']
            nivel = row['nivel_educativo']
            
            # Buscar código modular
            codigo_modular = buscar_codigo_modular(codigo_local, nivel, conn)
            
            if codigo_modular:
                # Obtener información adicional
                info_ie = pd.read_sql_query("""
                    SELECT nombre_institucion FROM instituciones_educativas_v2_mejorada 
                    WHERE codigo_modular = ?
                """, conn, params=[codigo_modular])
                
                nombre_encontrado = info_ie.iloc[0]['nombre_institucion'] if len(info_ie) > 0 else None
                
                resultados_mapeo.append({
                    'codigo_local': codigo_local,
                    'nivel_educativo': nivel,
                    'codigo_modular': codigo_modular,
                    'nombre_ie_encontrado': nombre_encontrado,
                    'metodo_encontrado': 'busqueda_directa'
                })
                
                encontrados += 1
                print(f"  {codigo_local} ({nivel}) -> {codigo_modular} ({nombre_encontrado})")
            else:
                # Si no se encuentra, agregar con NULL para revisión manual
                resultados_mapeo.append({
                    'codigo_local': codigo_local,
                    'nivel_educativo': nivel,
                    'codigo_modular': None,
                    'nombre_ie_encontrado': None,
                    'metodo_encontrado': 'no_encontrado'
                })
                print(f"  {codigo_local} ({nivel}) -> NO ENCONTRADO")
            
            procesados += 1
        
        # Insertar resultados en tabla de mapeo
        if resultados_mapeo:
            df_mapeo = pd.DataFrame(resultados_mapeo)
            df_mapeo.to_sql('mapeo_codigos_ie', conn, if_exists='append', index=False)
        
        print(f"\nRESULTADOS DEL MAPEO:")
        print(f"Total procesados: {procesados}")
        print(f"Códigos modulares encontrados: {encontrados}")
        print(f"Sin encontrar: {procesados - encontrados}")
        print(f"Tasa de éxito: {(encontrados/procesados)*100:.1f}%")
        
        conn.close()
        
    except Exception as e:
        print(f"Error en normalización: {e}")
        import traceback
        traceback.print_exc()

def actualizar_tabla_resultados():
    """
    Actualiza la tabla de resultados académicos con los códigos modulares encontrados
    """
    print("\nACTUALIZACIÓN DE TABLA RESULTADOS_ACADEMICOS")
    print("=" * 70)
    
    try:
        conn = sqlite3.connect('reasis_database.db')
        
        # Verificar si existe tabla de mapeo
        cursor = conn.cursor()
        resultado = cursor.execute("""
            SELECT COUNT(*) as total FROM mapeo_codigos_ie 
            WHERE codigo_modular IS NOT NULL
        """).fetchone()
        
        mapeos_disponibles = resultado[0] if resultado else 0
        print(f"Mapeos disponibles: {mapeos_disponibles}")
        
        if mapeos_disponibles > 0:
            # Agregar columna codigo_modular si no existe
            try:
                cursor.execute("ALTER TABLE resultados_academicos ADD COLUMN codigo_modular TEXT")
                print("Columna codigo_modular agregada")
            except:
                print("Columna codigo_modular ya existe")
            
            # Actualizar códigos modulares
            actualizar_query = """
                UPDATE resultados_academicos 
                SET codigo_modular = (
                    SELECT m.codigo_modular 
                    FROM mapeo_codigos_ie m 
                    WHERE m.codigo_local = resultados_academicos.codigo_ie 
                    AND m.nivel_educativo = resultados_academicos.nivel_educativo
                    AND m.codigo_modular IS NOT NULL
                )
                WHERE codigo_ie IS NOT NULL
            """
            
            cursor.execute(actualizar_query)
            filas_actualizadas = cursor.rowcount
            conn.commit()
            
            print(f"Filas actualizadas: {filas_actualizadas}")
            
            # Verificar resultados
            verificacion = pd.read_sql_query("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(codigo_modular) as con_codigo_modular,
                    COUNT(DISTINCT codigo_modular) as codigos_modulares_unicos
                FROM resultados_academicos
            """, conn)
            
            total = verificacion.iloc[0]['total']
            con_codigo = verificacion.iloc[0]['con_codigo_modular']
            unicos = verificacion.iloc[0]['codigos_modulares_unicos']
            
            print(f"\nVERIFICACIÓN:")
            print(f"Total registros: {total}")
            print(f"Con código modular: {con_codigo} ({(con_codigo/total)*100:.1f}%)")
            print(f"Códigos modulares únicos: {unicos}")
            
        conn.close()
        
    except Exception as e:
        print(f"Error en actualización: {e}")
        import traceback
        traceback.print_exc()

def generar_reporte_normalizacion():
    """Genera reporte final de la normalización"""
    print("\nREPORTE FINAL DE NORMALIZACIÓN")
    print("=" * 70)
    
    try:
        conn = sqlite3.connect('reasis_database.db')
        
        # Estadísticas finales
        estadisticas = pd.read_sql_query("""
            SELECT 
                COUNT(*) as total_estudiantes,
                COUNT(codigo_modular) as con_codigo_modular,
                COUNT(DISTINCT codigo_modular) as iiee_identificadas,
                COUNT(DISTINCT codigo_ie) as codigos_locales_unicos
            FROM resultados_academicos
        """, conn)
        
        stats = estadisticas.iloc[0]
        print(f"ESTADÍSTICAS FINALES:")
        print(f"Total estudiantes: {stats['total_estudiantes']}")
        print(f"Con código modular: {stats['con_codigo_modular']} ({(stats['con_codigo_modular']/stats['total_estudiantes'])*100:.1f}%)")
        print(f"Instituciones identificadas: {stats['iiee_identificadas']}")
        print(f"Códigos locales únicos: {stats['codigos_locales_unicos']}")
        
        # Top instituciones por estudiantes
        print(f"\nTOP 10 INSTITUCIONES POR ESTUDIANTES:")
        top_iiee = pd.read_sql_query("""
            SELECT r.codigo_modular, i.nombre_institucion, COUNT(*) as estudiantes,
                   COUNT(DISTINCT r.materia) as materias
            FROM resultados_academicos r
            LEFT JOIN instituciones_educativas_v2_mejorada i 
                ON r.codigo_modular = i.codigo_modular
            WHERE r.codigo_modular IS NOT NULL
            GROUP BY r.codigo_modular, i.nombre_institucion
            ORDER BY estudiantes DESC
            LIMIT 10
        """, conn)
        
        for idx, row in top_iiee.iterrows():
            print(f"  {row['codigo_modular']}: {row['nombre_institucion']} - {row['estudiantes']} estudiantes ({row['materias']} materias)")
        
        conn.close()
        
    except Exception as e:
        print(f"Error en reporte: {e}")

def main():
    """Función principal"""
    print("NORMALIZADOR DE CÓDIGOS IE - PROYECTO REASIS")
    print("=" * 80)
    
    analizar_estructura_codigos()
    normalizar_codigos_academicos()
    actualizar_tabla_resultados()
    generar_reporte_normalizacion()
    
    print(f"\nNORMALIZACIÓN COMPLETADA")
    print("=" * 80)

if __name__ == "__main__":
    main()