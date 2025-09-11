#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Migrador Final Normalizado - Proyecto Reasis
Script para migrar datos académicos normalizados con máxima calidad y consistencia
"""

import pandas as pd
import sqlite3
from pathlib import Path
import re

def limpiar_codigo_ie_avanzado(codigo_raw):
    """Limpia y extrae código IE con lógica avanzada"""
    if pd.isna(codigo_raw) or codigo_raw == "":
        return None
    
    codigo_str = str(codigo_raw).strip()
    
    # Estrategia 1: Extraer números de 4-8 dígitos al inicio
    match = re.match(r'^(\d{4,8})', codigo_str)
    if match:
        return match.group(1)
    
    # Estrategia 2: Buscar números de 4-8 dígitos en cualquier parte
    match = re.search(r'\b(\d{4,8})\b', codigo_str)
    if match:
        return match.group(1)
    
    # Estrategia 3: Conservar solo como nombre si no hay código numérico
    return None

def extraer_nombre_ie(nombre_raw, codigo_ie):
    """Extrae nombre limpio de institución educativa"""
    if pd.isna(nombre_raw) or nombre_raw == "":
        return None
    
    nombre_str = str(nombre_raw).strip()
    
    # Si el nombre empieza con el código, extraer solo la parte del nombre
    if codigo_ie and nombre_str.startswith(codigo_ie):
        nombre_limpio = nombre_str[len(codigo_ie):].strip()
        # Remover separadores comunes
        nombre_limpio = re.sub(r'^[-\s]+', '', nombre_limpio)
        return nombre_limpio if nombre_limpio else nombre_str
    
    return nombre_str

def codificar_nivel_logro(nivel_texto):
    """Convierte niveles de logro a códigos numéricos estándar"""
    if pd.isna(nivel_texto):
        return None
        
    nivel_str = str(nivel_texto).lower().strip()
    
    if 'inicio' in nivel_str:
        return 1
    elif 'proceso' in nivel_str:
        return 2
    elif 'satisfactorio' in nivel_str:
        return 3
    elif 'destacado' in nivel_str:
        return 4
    
    return None

def mapear_codigo_modular_mejorado(codigo_local, nivel, conn):
    """Mapeo mejorado de código local a código modular"""
    if not codigo_local:
        return None
    
    try:
        # Estrategia 1: Búsqueda exacta por código local
        query = """
            SELECT codigo_modular FROM instituciones_educativas_v2_mejorada 
            WHERE codigo_local = ? OR codigo_modular = ?
        """
        resultado = pd.read_sql_query(query, conn, params=[codigo_local, codigo_local])
        
        if len(resultado) > 0:
            return resultado.iloc[0]['codigo_modular']
        
        # Estrategia 2: Búsqueda parcial por similitud
        query_similar = """
            SELECT codigo_modular FROM instituciones_educativas_v2_mejorada 
            WHERE codigo_local LIKE ? OR codigo_modular LIKE ?
        """
        resultado_similar = pd.read_sql_query(query_similar, conn, params=[
            f"%{codigo_local}%", f"%{codigo_local}%"
        ])
        
        if len(resultado_similar) > 0:
            return resultado_similar.iloc[0]['codigo_modular']
        
        # Estrategia 3: El código local podría ya ser el modular
        return codigo_local
        
    except Exception as e:
        print(f"Error en mapeo de código {codigo_local}: {e}")
        return codigo_local  # Conservar el original

def migrar_archivo_normalizado(archivo_path, materia, conn):
    """Migra archivo normalizado con calidad máxima"""
    print(f"\nMigrando {materia} (normalizado)...")
    
    try:
        # Leer archivo Excel
        df = pd.read_excel(archivo_path, sheet_name='DATA')
        print(f"Total filas: {len(df)}")
        
        # Detectar columna de resultado
        col_resultado = None
        patrones_resultado = [f'R {materia}', f'R Matemática', f'R Comunicación', f'R Producción de textos']
        
        for patron in patrones_resultado:
            if patron in df.columns:
                col_resultado = patron
                break
        
        if not col_resultado:
            print(f"ERROR: No se encontró columna de resultado para {materia}")
            return 0
        
        registros_insertados = 0
        registros_con_errores = 0
        
        print("Procesando registros...")
        for idx, row in df.iterrows():
            try:
                # Extraer datos básicos
                estudiante_id = str(row.get('Estudiante', '')).strip() or None
                region = str(row.get('Región', '')).strip() or None
                nivel = str(row.get('Nivel', '')).strip() or None
                grado = str(row.get('Grado', '')).strip() or None
                ambito = str(row.get('Ambito', '')).strip() or None
                sexo = str(row.get('Sexo', '')).strip() or None
                
                # Procesar código y nombre IE
                codigo_ie_raw = row.get('Institución Educativa')
                nombre_ie_raw = row.get('ID. IE') or row.get('IE. ID') or row.get('ID IE')
                
                codigo_ie_local = limpiar_codigo_ie_avanzado(codigo_ie_raw)
                nombre_ie = extraer_nombre_ie(nombre_ie_raw, codigo_ie_local)
                
                # Mapear a código modular
                codigo_modular = mapear_codigo_modular_mejorado(codigo_ie_local, nivel, conn)
                
                # Procesar resultado académico
                resultado_texto = str(row.get(col_resultado, '')).strip() or None
                resultado_numerico = codificar_nivel_logro(resultado_texto)
                
                # Procesar año
                año = 2024  # Valor por defecto basado en archivos
                if 'Año' in df.columns:
                    año_raw = row.get('Año')
                    if pd.notna(año_raw):
                        try:
                            año = int(float(año_raw))
                        except:
                            pass
                
                # Campos adicionales
                analisis = str(row.get('ANALISIS', '')).strip() or None
                padd_r = str(row.get('PADD-R', '')).strip() or None
                
                # Validar datos críticos
                if not resultado_texto or not resultado_numerico:
                    registros_con_errores += 1
                    continue
                
                # Insertar en base de datos
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO resultados_academicos_normalized (
                        estudiante_id, region, nivel_educativo, grado, 
                        codigo_ie, nombre_ie, ambito, sexo, materia,
                        resultado_texto, resultado_numerico, año,
                        analisis_cobertura, padd_participacion
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    estudiante_id, region, nivel, grado, codigo_ie_local,
                    nombre_ie, ambito, sexo, materia, resultado_texto,
                    resultado_numerico, año, analisis, padd_r
                ))
                
                registros_insertados += 1
                
                # Commit periódico para mejor rendimiento
                if registros_insertados % 1000 == 0:
                    conn.commit()
                    print(f"  Procesados {registros_insertados}...")
                
            except Exception as e:
                registros_con_errores += 1
                if registros_con_errores <= 3:  # Mostrar primeros errores
                    print(f"  Error fila {idx}: {e}")
        
        conn.commit()
        
        print(f"Migración {materia} completada:")
        print(f"  ✓ Insertados: {registros_insertados}")
        print(f"  ✗ Errores: {registros_con_errores}")
        
        return registros_insertados
        
    except Exception as e:
        print(f"ERROR migrando {materia}: {e}")
        return 0

def generar_reporte_calidad():
    """Genera reporte completo de calidad de datos migrados"""
    print("\nREPORTE DE CALIDAD DE MIGRACIÓN")
    print("=" * 70)
    
    try:
        conn = sqlite3.connect('reasis_database.db')
        
        # Estadísticas generales
        stats = pd.read_sql_query("""
            SELECT 
                COUNT(*) as total_registros,
                COUNT(DISTINCT estudiante_id) as estudiantes_unicos,
                COUNT(DISTINCT codigo_ie) as codigos_ie_unicos,
                COUNT(DISTINCT materia) as materias,
                COUNT(DISTINCT año) as años
            FROM resultados_academicos_normalized
        """, conn).iloc[0]
        
        print("ESTADÍSTICAS GENERALES:")
        print(f"  Total registros: {stats['total_registros']}")
        print(f"  Estudiantes únicos: {stats['estudiantes_unicos']}")
        print(f"  Códigos IE únicos: {stats['codigos_ie_unicos']}")  
        print(f"  Materias: {stats['materias']}")
        print(f"  Años: {stats['años']}")
        
        # Por materia
        print(f"\nDISTRIBUCIÓN POR MATERIA:")
        por_materia = pd.read_sql_query("""
            SELECT materia, COUNT(*) as registros, 
                   COUNT(DISTINCT codigo_ie) as instituciones
            FROM resultados_academicos_normalized 
            GROUP BY materia
        """, conn)
        
        for _, row in por_materia.iterrows():
            print(f"  {row['materia']}: {row['registros']} registros, {row['instituciones']} instituciones")
        
        # Por nivel de logro
        print(f"\nDISTRIBUCIÓN POR NIVEL DE LOGRO:")
        por_logro = pd.read_sql_query("""
            SELECT resultado_numerico, resultado_texto, COUNT(*) as total
            FROM resultados_academicos_normalized 
            GROUP BY resultado_numerico, resultado_texto
            ORDER BY resultado_numerico
        """, conn)
        
        total_reg = stats['total_registros']
        for _, row in por_logro.iterrows():
            porcentaje = (row['total'] / total_reg) * 100
            print(f"  {row['resultado_numerico']} ({row['resultado_texto']}): {row['total']} ({porcentaje:.1f}%)")
        
        # Verificar relación con instituciones
        print(f"\nVERIFICACIÓN DE CÓDIGOS IE:")
        verificacion = pd.read_sql_query("""
            SELECT 
                COUNT(DISTINCT r.codigo_ie) as codigos_academicos,
                COUNT(DISTINCT i.codigo_modular) as codigos_instituciones,
                COUNT(DISTINCT CASE WHEN i.codigo_modular IS NOT NULL THEN r.codigo_ie END) as codigos_vinculados
            FROM resultados_academicos_normalized r
            LEFT JOIN instituciones_educativas_v2_mejorada i ON r.codigo_ie = i.codigo_modular OR r.codigo_ie = i.codigo_local
        """, conn).iloc[0]
        
        tasa_vinculacion = (verificacion['codigos_vinculados'] / verificacion['codigos_academicos']) * 100
        print(f"  Códigos académicos: {verificacion['codigos_academicos']}")
        print(f"  Códigos instituciones: {verificacion['codigos_instituciones']}")
        print(f"  Códigos vinculados: {verificacion['codigos_vinculados']}")
        print(f"  Tasa de vinculación: {tasa_vinculacion:.1f}%")
        
        conn.close()
        
    except Exception as e:
        print(f"Error generando reporte: {e}")

def main():
    """Función principal de migración final"""
    print("MIGRADOR FINAL NORMALIZADO - PROYECTO REASIS")
    print("=" * 80)
    
    try:
        conn = sqlite3.connect('reasis_database.db')
        
        # Verificar/crear tabla normalizada
        try:
            pd.read_sql_query("SELECT COUNT(*) FROM resultados_academicos_normalized", conn)
            print("Tabla normalizada existe - limpiando datos previos...")
            conn.execute("DELETE FROM resultados_academicos_normalized")
            conn.commit()
        except:
            print("Creando tabla normalizada...")
            # La tabla ya fue creada por el normalizador anterior
            pass
        
        # Archivos a procesar
        base_path = Path("assets/Consultoria/DatosLucas/Matematica y Comunicación")
        archivos = {
            "Matemática": base_path / "BD1- Matemática 2024.xlsx",
            "Comunicación": base_path / "BD2- Comunicación 2024.xlsx",
            "Producción de textos": base_path / "BD3 - Producción de textos 2024.xlsx"
        }
        
        total_registros = 0
        
        # Migrar cada archivo
        for materia, archivo_path in archivos.items():
            if archivo_path.exists():
                registros = migrar_archivo_normalizado(archivo_path, materia, conn)
                total_registros += registros
            else:
                print(f"ADVERTENCIA: Archivo no encontrado - {archivo_path}")
        
        conn.close()
        
        print(f"\nMIGRACIÓN COMPLETADA")
        print(f"Total registros migrados: {total_registros}")
        
        # Generar reporte final
        generar_reporte_calidad()
        
        print(f"\n✓ MIGRACIÓN FINAL EXITOSA")
        print("=" * 80)
        
    except Exception as e:
        print(f"ERROR CRÍTICO: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()