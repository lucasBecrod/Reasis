#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROCESADOR PRODUCCIÓN - Completa procesamiento con API key de producción
Procesa solo los registros con status ERROR usando la nueva API key
"""
import pandas as pd
import sqlite3
import time
import json
from gemini_optimizer import GeminiOptimizer

def procesar_errores_produccion():
    """Procesa solo los registros con ERROR usando API de producción"""
    print("=== PROCESADOR PRODUCCION CONECTIVIDAD ===\n")
    
    db_path = 'reasis_database.db'
    
    # Usar API de producción
    optimizer = GeminiOptimizer(use_production=True)
    print(f"[OK] API Producción inicializada: {optimizer.api_key_primary[:20]}...")
    print(f"[OK] API Backup disponible: {optimizer.api_key_backup[:20]}...")
    
    # Cargar datos de referencia IE
    conn = sqlite3.connect(db_path)
    query_ie = """
    SELECT 
        codigo_modular,
        codigo_local,
        nombre_institucion,
        distrito,
        provincia,
        region,
        modalidad,
        nivel_educativo,
        es_fya,
        codigo_red
    FROM instituciones_educativas
    WHERE es_fya = 1
    ORDER BY codigo_modular
    """
    
    df_ie = pd.read_sql_query(query_ie, conn)
    print(f"[OK] Cargadas {len(df_ie)} instituciones de referencia")
    
    # Crear JSON de referencia
    ie_list = []
    for _, row in df_ie.iterrows():
        ie_dict = {
            "codigo_modular": row['codigo_modular'],
            "codigo_local": str(row['codigo_local']) if pd.notna(row['codigo_local']) else None,
            "nombre": row['nombre_institucion'],
            "distrito": row['distrito'],
            "provincia": row['provincia'],
            "region": row['region'],
            "modalidad": row['modalidad'],
            "nivel": row['nivel_educativo'],
            "red": row['codigo_red']
        }
        ie_list.append(ie_dict)
    
    ie_referencia = {
        "total_instituciones": len(ie_list),
        "instituciones": ie_list
    }
    
    # Obtener registros con ERROR
    query_errores = """
    SELECT id, indice_original, nombre_manual, red_fya 
    FROM conectividad_progreso 
    WHERE matching_status = 'ERROR'
    ORDER BY id
    """
    df_errores = pd.read_sql_query(query_errores, conn)
    
    print(f"\n=== CONFIGURACIÓN PROCESAMIENTO ===")
    print(f"Registros con ERROR a reprocesar: {len(df_errores)}")
    
    if len(df_errores) == 0:
        print("[OK] No hay registros con ERROR para procesar")
        return
    
    # Función para construir prompt
    def construir_prompt(nombre_manual, red_fya):
        ie_json = json.dumps(ie_referencia, indent=2, ensure_ascii=False)
        
        prompt = f"""
ROL: Eres un especialista en normalización de bases de datos educativas Fe y Alegría.

OBJETIVO: Identificar a qué institución educativa corresponde un nombre escrito manualmente.

DATOS DE REFERENCIA:
{ie_json}

NOMBRE MANUAL A IDENTIFICAR: "{nombre_manual}"
RED FE Y ALEGRÍA: "{red_fya}"

INSTRUCCIONES CRÍTICAS:
1. Analiza el nombre manual y encuentra la institución educativa más probable
2. Considera códigos modulares, códigos locales, nombres parciales, números
3. El nombre manual puede estar incompleto, tener errores de tipeo, o usar abreviaciones
4. Prioriza coincidencias que estén en la misma red Fe y Alegría si es posible
5. Responde ÚNICAMENTE con el código modular de la institución identificada
6. Si no encuentras coincidencia clara, responde "NO_MATCH"
7. NO agregues explicaciones, solo el código modular

EJEMPLOS DE FORMATO DE RESPUESTA:
- Si identificas la institución: "1234567"
- Si no hay coincidencia clara: "NO_MATCH"

RESPUESTA:"""
        
        return prompt
    
    # Función para actualizar resultado
    def actualizar_resultado(conn, id_registro, codigo, status):
        query_update = """
        UPDATE conectividad_progreso 
        SET codigo_modular_identificado = ?, 
            matching_status = ?,
            fecha_procesamiento = CURRENT_TIMESTAMP,
            observaciones = 'Reprocesado con API producción'
        WHERE id = ?
        """
        
        cursor = conn.cursor()
        cursor.execute(query_update, (codigo, status, id_registro))
        conn.commit()
        
        print(f"    -> [{status}] {codigo} actualizado en BD")
    
    # Procesar registros con ERROR
    matches_nuevos = 0
    no_matches = 0
    errores_nuevos = 0
    
    print(f"\nIniciando reprocesamiento de {len(df_errores)} registros...")
    
    for i, (_, row) in enumerate(df_errores.iterrows(), 1):
        id_reg = row['id']
        nombre = row['nombre_manual']
        red = row['red_fya'] if pd.notna(row['red_fya']) else ""
        
        print(f"[{i}/{len(df_errores)}] '{nombre[:40]}...'", end=" ")
        
        try:
            # Construir prompt y llamar a Gemini
            prompt = construir_prompt(nombre, red)
            respuesta = optimizer.call_gemini(prompt, temperature=0.0)
            
            if not respuesta:
                actualizar_resultado(conn, id_reg, "ERROR", "ERROR")
                errores_nuevos += 1
                continue
                
            # Limpiar respuesta
            respuesta_clean = respuesta.strip().strip('"').strip("'")
            
            if respuesta_clean == "NO_MATCH":
                actualizar_resultado(conn, id_reg, "NO_MATCH", "NO_MATCH")
                no_matches += 1
                
            elif respuesta_clean.isdigit() and len(respuesta_clean) == 7:
                actualizar_resultado(conn, id_reg, respuesta_clean, "MATCHED")
                matches_nuevos += 1
                
            else:
                actualizar_resultado(conn, id_reg, str(respuesta_clean), "ERROR")
                errores_nuevos += 1
                print(f" [WARNING] Respuesta inesperada: {respuesta_clean}")
        
        except Exception as e:
            actualizar_resultado(conn, id_reg, "ERROR", "ERROR")
            errores_nuevos += 1
            print(f" [ERROR] Excepción: {str(e)}")
        
        # Pausa pequeña
        time.sleep(0.5)
        
        # Reporte cada 20
        if i % 20 == 0:
            print(f"\n  Progreso: {i}/{len(df_errores)} | Nuevos matches: {matches_nuevos} | No-matches: {no_matches} | Errores: {errores_nuevos}")
    
    # Cerrar la conexión al final
    conn.close()
    
    # Estadísticas finales
    print(f"\n=== REPROCESAMIENTO COMPLETADO ===")
    print(f"Registros reprocesados: {len(df_errores)}")
    print(f"Nuevos matches: {matches_nuevos}")
    print(f"No-matches: {no_matches}")
    print(f"Errores nuevos: {errores_nuevos}")
    print(f"Tasa éxito: {(matches_nuevos/(matches_nuevos + no_matches)*100) if (matches_nuevos + no_matches) > 0 else 0:.1f}%")
    
    # Mostrar estadísticas finales globales
    mostrar_estadisticas_finales()

def mostrar_estadisticas_finales():
    """Muestra estadísticas finales de todo el procesamiento"""
    
    conn = sqlite3.connect('reasis_database.db')
    
    print(f"\n=== ESTADÍSTICAS FINALES GLOBALES ===")
    
    # Estadísticas generales
    query_stats = """
    SELECT 
        matching_status,
        COUNT(*) as count,
        COUNT(*) * 100.0 / (SELECT COUNT(*) FROM conectividad_progreso) as porcentaje
    FROM conectividad_progreso 
    GROUP BY matching_status
    ORDER BY count DESC
    """
    
    df_stats = pd.read_sql_query(query_stats, conn)
    
    print("Estado final de procesamiento:")
    for _, row in df_stats.iterrows():
        print(f"  {row['matching_status']}: {row['count']} ({row['porcentaje']:.1f}%)")
    
    # Total de matches exitosos
    query_matches = """
    SELECT nombre_manual, codigo_modular_identificado, red_fya
    FROM conectividad_progreso 
    WHERE matching_status = 'MATCHED'
    ORDER BY fecha_procesamiento
    """
    
    df_matches = pd.read_sql_query(query_matches, conn)
    
    print(f"\n=== TODOS LOS MATCHES EXITOSOS ({len(df_matches)}) ===")
    for i, (_, row) in enumerate(df_matches.iterrows(), 1):
        nombre = row['nombre_manual'][:35] + "..." if len(row['nombre_manual']) > 35 else row['nombre_manual']
        print(f"  {i:2d}. \"{nombre}\" -> {row['codigo_modular_identificado']}")
    
    # Exportar matches a Excel
    if len(df_matches) > 0:
        output_path = "conectividad_matches_FINAL.xlsx"
        df_matches.to_excel(output_path, index=False, engine='openpyxl')
        print(f"\n[OK] {len(df_matches)} matches exportados a: {output_path}")
    
    conn.close()
    
    print(f"\n=== PROCESAMIENTO COMPLETO ===")
    print(f"Variable X13_CON lista para integrar con {len(df_matches)} instituciones")

if __name__ == "__main__":
    print("PROCESADOR PRODUCCION - API KEY NUEVA")
    print("=====================================\n")
    
    # Auto-ejecutar sin input
    procesar_errores_produccion()
    print("\n[OK] PROCESAMIENTO DE PRODUCCIÓN COMPLETADO")