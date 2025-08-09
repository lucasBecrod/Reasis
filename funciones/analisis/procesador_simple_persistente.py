#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROCESADOR SIMPLE PERSISTENTE - Sin caracteres unicode problemáticos
"""
import pandas as pd
import sqlite3
import time
from normalizador_ie_conectividad import NormalizadorIEConectividad

def inicializar_tabla_progreso(db_path):
    """Crea la tabla de progreso"""
    conn = sqlite3.connect(db_path)
    
    query = """
    CREATE TABLE IF NOT EXISTS conectividad_progreso (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        indice_original INTEGER,
        nombre_manual TEXT,
        red_fya TEXT,
        codigo_modular_identificado TEXT,
        matching_status TEXT,
        fecha_procesamiento TEXT DEFAULT CURRENT_TIMESTAMP,
        numero_batch INTEGER,
        observaciones TEXT
    )
    """
    
    conn.execute(query)
    conn.commit()
    conn.close()
    print("[OK] Tabla conectividad_progreso creada")

def verificar_progreso(db_path):
    """Verifica progreso existente"""
    conn = sqlite3.connect(db_path)
    
    try:
        query = "SELECT indice_original FROM conectividad_progreso"
        df = pd.read_sql_query(query, conn)
        indices_procesados = set(df['indice_original'].tolist())
        print(f"[OK] Encontrados {len(indices_procesados)} registros ya procesados")
        return indices_procesados
    except:
        print("[INFO] No hay progreso previo")
        return set()
    finally:
        conn.close()

def guardar_resultado(db_path, indice, nombre, red, codigo, status, batch_num):
    """Guarda un resultado inmediatamente"""
    conn = sqlite3.connect(db_path)
    
    query = """
    INSERT OR REPLACE INTO conectividad_progreso 
    (indice_original, nombre_manual, red_fya, codigo_modular_identificado, 
     matching_status, numero_batch)
    VALUES (?, ?, ?, ?, ?, ?)
    """
    
    cursor = conn.cursor()
    cursor.execute(query, (indice, nombre, red, codigo, status, batch_num))
    conn.commit()
    conn.close()
    
    print(f"    -> [{status}] {codigo} guardado en BD")

def procesar_con_persistencia():
    """Procesa archivo con guardado inmediato"""
    print("=== PROCESADOR SIMPLE PERSISTENTE ===")
    
    db_path = 'reasis_database.db'
    
    # Inicializar
    inicializar_tabla_progreso(db_path)
    normalizador = NormalizadorIEConectividad(db_path)
    
    # Cargar archivo
    archivo = r"C:\Users\lucas\Proyectos\Reasis\assets\Consultoria\Información actualizada\4. Conectividad y equipamiento.xlsx"
    df = pd.read_excel(archivo, sheet_name='hoja1', engine='openpyxl')
    normalizador.cargar_referencia_ie()
    
    # Columnas
    col_ie_nombre = 'Si pertence a una Red Rural, indique el nombre de su IE'
    col_fya = 'Fe y Alegría Nro. ....'
    
    # Registros a procesar
    registros = df[df[col_ie_nombre].notna()].copy().reset_index()
    
    # Verificar progreso
    procesados = verificar_progreso(db_path)
    pendientes = [(idx, row) for idx, row in registros.iterrows() 
                  if row['index'] not in procesados]
    
    print(f"Total registros: {len(registros)}")
    print(f"Ya procesados: {len(procesados)}")
    print(f"Pendientes: {len(pendientes)}")
    
    if len(pendientes) == 0:
        print("[OK] Todos los registros ya estan procesados")
        return
    
    # Procesar pendientes
    matches = 0
    errores = 0
    
    for i, (idx, row) in enumerate(pendientes, 1):
        indice_orig = row['index']
        nombre = str(row[col_ie_nombre]).strip()
        red = str(row[col_fya]) if pd.notna(row[col_fya]) else ""
        
        print(f"[{i}/{len(pendientes)}] '{nombre[:40]}...'")
        
        try:
            # Llamar a Gemini
            codigo = normalizador.identificar_ie_con_gemini(nombre, red)
            
            if codigo == "NO_MATCH":
                guardar_resultado(db_path, indice_orig, nombre, red, "NO_MATCH", "NO_MATCH", 1)
                
            elif codigo and len(codigo) == 7 and codigo.isdigit():
                guardar_resultado(db_path, indice_orig, nombre, red, codigo, "MATCHED", 1)
                matches += 1
                
            else:
                guardar_resultado(db_path, indice_orig, nombre, red, str(codigo), "ERROR", 1)
                errores += 1
        
        except Exception as e:
            print(f"    -> ERROR: {str(e)}")
            guardar_resultado(db_path, indice_orig, nombre, red, "ERROR", "ERROR", 1)
            errores += 1
        
        # Pausa
        time.sleep(0.5)
        
        # Reporte cada 10
        if i % 10 == 0:
            print(f"  Progreso: {i}/{len(pendientes)} | Matches: {matches} | Errores: {errores}")
    
    print(f"\n=== PROCESAMIENTO COMPLETO ===")
    print(f"Procesados: {len(pendientes)}")
    print(f"Matches: {matches}")
    print(f"Errores: {errores}")
    print(f"Tasa exito: {(matches/len(pendientes)*100):.1f}%")
    print(f"[OK] Todo guardado en tabla conectividad_progreso")

if __name__ == "__main__":
    procesar_con_persistencia()