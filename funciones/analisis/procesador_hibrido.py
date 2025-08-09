#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROCESADOR HÍBRIDO V2 - Combina Fuzzy Matching local con IA Gemini de forma optimizada
1. Usa FuzzyWuzzy para encontrar candidatos locales.
2. Si hay un match de alta confianza (>90%), lo acepta.
3. Si no, envía solo los 5 mejores candidatos a Gemini para la decisión final.
"""
import pandas as pd
import sqlite3
import time
import json
from gemini_optimizer import GeminiOptimizer
from fuzzywuzzy import process

def procesar_hibrido_optimizado():
    """Procesa registros con ERROR usando una estrategia híbrida optimizada."""
    print("=== PROCESADOR HÍBRIDO OPTIMIZADO DE CONECTIVIDAD ===\n")
    
    db_path = 'reasis_database.db'
    conn = sqlite3.connect(db_path)
    
    # 1. Cargar datos de referencia de instituciones
    query_ie = "SELECT codigo_modular, nombre_institucion FROM instituciones_educativas"
    df_ie = pd.read_sql_query(query_ie, conn)
    # Crear un diccionario para búsqueda rápida: {nombre: codigo_modular}
    choices = {row['nombre_institucion']: row['codigo_modular'] for _, row in df_ie.iterrows()}
    print(f"[OK] Cargadas {len(choices)} instituciones de referencia para matching local.")

    # 2. Obtener registros con ERROR a procesar
    query_errores = "SELECT id, nombre_manual FROM conectividad_progreso WHERE matching_status = 'ERROR' ORDER BY id"
    df_errores = pd.read_sql_query(query_errores, conn)
    print(f"[INFO] Se encontraron {len(df_errores)} registros con ERROR para reprocesar.")

    if len(df_errores) == 0:
        print("[OK] No hay registros con ERROR para procesar.")
        conn.close()
        return

    # 3. Inicializar la IA (para el último recurso)
    optimizer = GeminiOptimizer(use_production=True)
    print(f"[OK] IA Gemini inicializada como último recurso.")

    # Contadores
    resueltos_local = 0
    resueltos_ia = 0
    no_resueltos = 0

    # 4. Procesar cada registro con error
    for _, row in df_errores.iterrows():
        id_reg = row['id']
        nombre_manual = str(row['nombre_manual'] or '').strip()
        if not nombre_manual:
            continue
        print(f"\nProcesando [{id_reg}] '{nombre_manual}':")

        # --- FILTRO 1: FUZZY MATCHING LOCAL ---
        candidatos = process.extract(nombre_manual, choices.keys(), limit=5)
        
        if not candidatos:
            print("  -> [LOCAL FAIL] No se encontraron candidatos locales.")
            actualizar_resultado(conn, id_reg, "NO_MATCH", "NO_MATCH", "Fuzzy: Sin candidatos")
            no_resueltos += 1
            continue

        best_match_local = candidatos[0]
        nombre_encontrado, score = best_match_local

        # Decisión basada en el score
        if score >= 90: # Umbral de alta confianza
            codigo_encontrado = choices[nombre_encontrado]
            print(f"  -> [LOCAL MATCH] Confianza: {score}%. Match: '{nombre_encontrado}'")
            actualizar_resultado(conn, id_reg, codigo_encontrado, "MATCHED", f"Local Fuzzy Match ({score}%)")
            resueltos_local += 1
            continue
        
        if score < 70:
            print(f"  -> [LOCAL FAIL] Confianza muy baja ({score}%). Descartado.")
            actualizar_resultado(conn, id_reg, "NO_MATCH", "NO_MATCH", f"Fuzzy: Confianza baja ({score}%)")
            no_resueltos += 1
            continue

        print(f"  -> [LOCAL INFO] Mejor match ({score}%) no es suficiente. Pasando a IA con {len(candidatos)} candidatos.")

        # --- FILTRO 2: IA GEMINI (ÚLTIMO RECURSO CON CANDIDATOS) ---
        try:
            prompt = construir_prompt_con_candidatos(nombre_manual, candidatos, choices)
            respuesta = optimizer.call_gemini(prompt, temperature=0.0)
            
            if not respuesta:
                actualizar_resultado(conn, id_reg, "ERROR", "ERROR", "IA no respondió")
                no_resueltos += 1
                continue

            respuesta_clean = respuesta.strip().strip('"').strip("'")
            
            if respuesta_clean == "NO_MATCH":
                actualizar_resultado(conn, id_reg, "NO_MATCH", "NO_MATCH", "IA no encontró match")
                no_resueltos += 1
            elif respuesta_clean.isdigit() and len(respuesta_clean) == 7:
                actualizar_resultado(conn, id_reg, respuesta_clean, "MATCHED", f"IA Match (Fuzzy {score}%)")
                resueltos_ia += 1
            else:
                actualizar_resultado(conn, id_reg, str(respuesta_clean), "ERROR", f"IA respuesta inesperada: {respuesta_clean}")
                no_resueltos += 1

        except Exception as e:
            print(f"  -> [ERROR] Excepción en IA: {e}")
            actualizar_resultado(conn, id_reg, "ERROR", "ERROR", f"Excepción IA: {e}")
            no_resueltos += 1
        
        time.sleep(0.5)

    conn.close()
    print("\n=== PROCESAMIENTO HÍBRIDO COMPLETADO ===")
    print(f"Total procesados: {len(df_errores)}")
    print(f"✅ Resueltos localmente (Fuzzy >90%): {resueltos_local}")
    print(f"✅ Resueltos con IA Gemini (Fuzzy 70-90%): {resueltos_ia}")
    print(f"❌ No resueltos / Descartados: {no_resueltos}")

def construir_prompt_con_candidatos(nombre_manual, candidatos, choices_dict):
    candidatos_str = "\n".join([f"- {choices_dict[nombre]} ({score}%): {nombre}" for nombre, score in candidatos])
    prompt = f"""
    OBJETIVO: Eres un asistente experto en normalización de datos. Debes elegir el código modular correcto para un nombre de institución escrito a mano.

    NOMBRE MANUAL A IDENTIFICAR: "{nombre_manual}"
    
    CANDIDATOS PRE-SELECCIONADOS (con su puntaje de similitud):
    {candidatos_str}
    
    INSTRUCCIONES CRÍTICAS:
    1. Analiza el NOMBRE MANUAL y compáralo con la lista de CANDIDATOS.
    2. Elige el candidato que sea la coincidencia más lógica y correcta.
    3. Responde ÚNICAMENTE con el código modular de 7 dígitos del candidato elegido.
    4. Si NINGUNO de los candidatos es una coincidencia correcta, responde EXACTAMENTE "NO_MATCH".
    5. No agregues explicaciones, solo el código o "NO_MATCH".
    
    RESPUESTA:"""
    return prompt

def actualizar_resultado(conn, id_registro, codigo, status, observacion):
    query_update = """
    UPDATE conectividad_progreso 
    SET codigo_modular_identificado = ?, matching_status = ?, fecha_procesamiento = CURRENT_TIMESTAMP, observaciones = ?
    WHERE id = ?
    """
    cursor = conn.cursor()
    cursor.execute(query_update, (codigo, status, observacion, id_registro))
    conn.commit()
    print(f"    -> [{status}] {codigo} actualizado en BD. Obs: {observacion}")

if __name__ == "__main__":
    # Asegúrate de haber instalado la librería: pip install "fuzzywuzzy[speedup]"
    procesar_hibrido_optimizado()

