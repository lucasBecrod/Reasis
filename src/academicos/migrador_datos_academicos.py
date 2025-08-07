#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Migrador de Datos Académicos - Proyecto Reasis
Script para migrar los datos académicos de Excel a la base de datos SQLite
"""

import pandas as pd
import sqlite3
from pathlib import Path
import warnings
import re
warnings.filterwarnings('ignore')

def crear_tabla_resultados_academicos(conn):
    """Crea la tabla de resultados académicos con estructura optimizada"""
    print("Creando tabla resultados_academicos...")
    
    cursor = conn.cursor()
    
    # Eliminar tabla existente si existe
    cursor.execute("DROP TABLE IF EXISTS resultados_academicos")
    
    # Crear nueva tabla
    create_table_sql = """
    CREATE TABLE resultados_academicos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        estudiante_id TEXT,
        codigo_ie TEXT,
        nombre_ie TEXT,
        region TEXT,
        nivel_educativo TEXT,
        grado TEXT,
        ambito TEXT,
        sexo TEXT,
        materia TEXT,
        nivel_logro_texto TEXT,
        nivel_logro_numerico INTEGER,
        año INTEGER,
        fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (codigo_ie) REFERENCES instituciones_educativas_v2_mejorada(codigo_modular)
    );
    """
    
    cursor.execute(create_table_sql)
    
    # Crear índices para optimizar consultas
    indices = [
        "CREATE INDEX idx_resultados_codigo_ie ON resultados_academicos(codigo_ie);",
        "CREATE INDEX idx_resultados_materia ON resultados_academicos(materia);",
        "CREATE INDEX idx_resultados_año ON resultados_academicos(año);",
        "CREATE INDEX idx_resultados_nivel_logro ON resultados_academicos(nivel_logro_numerico);"
    ]
    
    for indice in indices:
        cursor.execute(indice)
    
    conn.commit()
    print("Tabla e índices creados exitosamente")

def limpiar_codigo_ie(codigo_raw):
    """Limpia y normaliza códigos de institución educativa"""
    if pd.isna(codigo_raw) or codigo_raw == "":
        return None
    
    codigo_str = str(codigo_raw)
    
    # Extraer solo números de 7-8 dígitos (códigos modulares típicos)
    match = re.search(r'\b(\d{7,8})\b', codigo_str)
    if match:
        return match.group(1)
    
    return None

def codificar_nivel_logro(nivel_texto):
    """Convierte niveles de logro a códigos numéricos"""
    if pd.isna(nivel_texto):
        return None
        
    nivel_str = str(nivel_texto).lower()
    
    if 'inicio' in nivel_str:
        return 1
    elif 'proceso' in nivel_str:
        return 2
    elif 'satisfactorio' in nivel_str:
        return 3
    elif 'destacado' in nivel_str:
        return 4
    
    return None

def normalizar_campo(valor):
    """Normaliza campos de texto eliminando espacios y caracteres especiales"""
    if pd.isna(valor):
        return None
    
    valor_str = str(valor).strip()
    if valor_str == "" or valor_str.lower() in ['nan', 'null', 'none']:
        return None
        
    return valor_str

def migrar_archivo_academico(archivo_path, materia, conn):
    """Migra un archivo específico de datos académicos"""
    print(f"\nMigrando datos de {materia}...")
    print(f"Archivo: {archivo_path}")
    
    try:
        # Leer archivo Excel
        df = pd.read_excel(archivo_path, sheet_name='DATA')
        print(f"Filas originales: {len(df)}")
        
        # Identificar columnas clave
        columnas_mapeo = {
            'estudiante_id': None,
            'codigo_ie': None,
            'nombre_ie': None,
            'region': None,
            'nivel': None,
            'grado': None,
            'ambito': None,
            'sexo': None,
            'resultado': None,
            'año': None
        }
        
        # Mapeo automático de columnas
        for col in df.columns:
            col_lower = col.lower()
            
            if 'estudiante' in col_lower and columnas_mapeo['estudiante_id'] is None:
                columnas_mapeo['estudiante_id'] = col
            elif ('institucion educativa' in col_lower or 'institución educativa' in col_lower) and columnas_mapeo['codigo_ie'] is None:
                columnas_mapeo['codigo_ie'] = col  # Esta es la columna con códigos modulares
            elif ('id. ie' in col_lower or 'ie. id' in col_lower or 'id ie' in col_lower) and columnas_mapeo['nombre_ie'] is None:
                columnas_mapeo['nombre_ie'] = col  # Esta es la columna con nombres
            elif 'region' in col_lower and columnas_mapeo['region'] is None:
                columnas_mapeo['region'] = col
            elif 'nivel' in col_lower and columnas_mapeo['nivel'] is None:
                columnas_mapeo['nivel'] = col
            elif 'grado' in col_lower and columnas_mapeo['grado'] is None:
                columnas_mapeo['grado'] = col
            elif 'ambito' in col_lower and columnas_mapeo['ambito'] is None:
                columnas_mapeo['ambito'] = col
            elif 'sexo' in col_lower and columnas_mapeo['sexo'] is None:
                columnas_mapeo['sexo'] = col
            elif f'r {materia.lower()}' in col_lower and columnas_mapeo['resultado'] is None:
                columnas_mapeo['resultado'] = col
            elif 'año' in col_lower and columnas_mapeo['año'] is None:
                columnas_mapeo['año'] = col
        
        print("Mapeo de columnas identificado:")
        for campo, columna in columnas_mapeo.items():
            print(f"  {campo}: {columna}")
        
        # Verificar columnas esenciales
        if not columnas_mapeo['resultado']:
            print(f"ERROR: No se encontró columna de resultados para {materia}")
            return 0
        
        # Preparar datos para inserción
        registros_insertados = 0
        registros_con_errores = 0
        
        for idx, row in df.iterrows():
            try:
                # Extraer y limpiar datos
                estudiante_id = normalizar_campo(row.get(columnas_mapeo['estudiante_id']))
                codigo_ie = limpiar_codigo_ie(row.get(columnas_mapeo['codigo_ie']))
                nombre_ie = normalizar_campo(row.get(columnas_mapeo['nombre_ie']))
                region = normalizar_campo(row.get(columnas_mapeo['region']))
                nivel = normalizar_campo(row.get(columnas_mapeo['nivel']))
                grado = normalizar_campo(row.get(columnas_mapeo['grado']))
                ambito = normalizar_campo(row.get(columnas_mapeo['ambito']))
                sexo = normalizar_campo(row.get(columnas_mapeo['sexo']))
                
                resultado_texto = normalizar_campo(row.get(columnas_mapeo['resultado']))
                resultado_numerico = codificar_nivel_logro(resultado_texto)
                
                año = None
                if columnas_mapeo['año']:
                    año_raw = row.get(columnas_mapeo['año'])
                    if pd.notna(año_raw):
                        try:
                            año = int(float(año_raw))
                        except:
                            año = 2024  # Valor por defecto basado en archivos
                else:
                    año = 2024  # Valor por defecto
                
                # Validar datos esenciales
                if not resultado_texto or not resultado_numerico:
                    registros_con_errores += 1
                    continue
                
                # Insertar registro
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO resultados_academicos (
                        estudiante_id, codigo_ie, nombre_ie, region, nivel_educativo, 
                        grado, ambito, sexo, materia, nivel_logro_texto, 
                        nivel_logro_numerico, año
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    estudiante_id, codigo_ie, nombre_ie, region, nivel, 
                    grado, ambito, sexo, materia, resultado_texto,
                    resultado_numerico, año
                ))
                
                registros_insertados += 1
                
                # Commit cada 1000 registros para mejor performance
                if registros_insertados % 1000 == 0:
                    conn.commit()
                    print(f"  Procesados {registros_insertados} registros...")
                
            except Exception as e:
                registros_con_errores += 1
                if registros_con_errores <= 5:  # Mostrar solo los primeros 5 errores
                    print(f"  Error en fila {idx}: {e}")
        
        conn.commit()
        
        print(f"Migración de {materia} completada:")
        print(f"  Registros insertados: {registros_insertados}")
        print(f"  Registros con errores: {registros_con_errores}")
        
        return registros_insertados
        
    except Exception as e:
        print(f"Error al migrar {materia}: {e}")
        return 0

def migrar_datos_academicos():
    """Función principal para migrar todos los datos académicos"""
    print("MIGRADOR DE DATOS ACADEMICOS - PROYECTO REASIS")
    print("=" * 80)
    
    # Conectar a la base de datos
    try:
        conn = sqlite3.connect('reasis_database.db')
        print("Conexión a base de datos establecida")
        
        # Crear tabla de resultados académicos
        crear_tabla_resultados_academicos(conn)
        
        # Definir archivos a procesar
        base_path = Path("assets/Consultoria/DatosLucas/Matematica y Comunicación")
        archivos_academicos = {
            "Matemática": base_path / "BD1- Matemática 2024.xlsx",
            "Comunicación": base_path / "BD2- Comunicación 2024.xlsx", 
            "Producción de textos": base_path / "BD3 - Producción de textos 2024.xlsx"
        }
        
        # Verificar existencia de archivos
        print(f"\nVerificando archivos fuente:")
        for materia, archivo in archivos_academicos.items():
            existe = archivo.exists()
            print(f"  {materia}: {'OK' if existe else 'NO'} {archivo}")
        
        # Migrar cada archivo
        total_registros = 0
        for materia, archivo in archivos_academicos.items():
            if archivo.exists():
                registros = migrar_archivo_academico(archivo, materia, conn)
                total_registros += registros
            else:
                print(f"ADVERTENCIA: Archivo {archivo} no encontrado")
        
        # Resumen final
        print(f"\nRESUMEN DE MIGRACIÓN:")
        print(f"Total registros migrados: {total_registros}")
        
        # Verificar datos insertados
        cursor = conn.cursor()
        
        # Estadísticas por materia
        print(f"\nESTADÍSTICAS POR MATERIA:")
        stats_materia = cursor.execute("""
            SELECT materia, COUNT(*) as total, 
                   COUNT(DISTINCT codigo_ie) as instituciones_unicas
            FROM resultados_academicos 
            GROUP BY materia
        """).fetchall()
        
        for materia, total, inst_unicas in stats_materia:
            print(f"  {materia}: {total} estudiantes, {inst_unicas} instituciones")
        
        # Estadísticas por nivel de logro
        print(f"\nESTADÍSTICAS POR NIVEL DE LOGRO:")
        stats_logro = cursor.execute("""
            SELECT nivel_logro_texto, nivel_logro_numerico, COUNT(*) as total
            FROM resultados_academicos 
            GROUP BY nivel_logro_texto, nivel_logro_numerico
            ORDER BY nivel_logro_numerico
        """).fetchall()
        
        for nivel_texto, nivel_num, total in stats_logro:
            porcentaje = (total / total_registros) * 100 if total_registros > 0 else 0
            print(f"  {nivel_num} - {nivel_texto}: {total} ({porcentaje:.1f}%)")
        
        # Verificar códigos IE únicos vs instituciones disponibles
        print(f"\nVERIFICACIÓN DE CÓDIGOS MODULARES:")
        codigos_academicos = cursor.execute("""
            SELECT COUNT(DISTINCT codigo_ie) as codigos_unicos
            FROM resultados_academicos 
            WHERE codigo_ie IS NOT NULL
        """).fetchone()[0]
        
        codigos_instituciones = cursor.execute("""
            SELECT COUNT(DISTINCT codigo_modular) as codigos_instituciones
            FROM instituciones_educativas_v2_mejorada
        """).fetchone()[0]
        
        print(f"  Códigos únicos en datos académicos: {codigos_academicos}")
        print(f"  Códigos en tabla instituciones: {codigos_instituciones}")
        
        # Verificar coincidencias
        coincidencias = cursor.execute("""
            SELECT COUNT(DISTINCT r.codigo_ie) as coincidencias
            FROM resultados_academicos r
            INNER JOIN instituciones_educativas_v2_mejorada i 
                ON r.codigo_ie = i.codigo_modular
            WHERE r.codigo_ie IS NOT NULL
        """).fetchone()[0]
        
        print(f"  Códigos que coinciden: {coincidencias}")
        tasa_coincidencia = (coincidencias / codigos_academicos) * 100 if codigos_academicos > 0 else 0
        print(f"  Tasa de coincidencia: {tasa_coincidencia:.1f}%")
        
        conn.close()
        print(f"\nMIGRACION DE DATOS ACADEMICOS COMPLETADA")
        print("=" * 80)
        
    except Exception as e:
        print(f"Error durante migración: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    migrar_datos_academicos()