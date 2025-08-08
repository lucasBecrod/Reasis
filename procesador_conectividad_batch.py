#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROCESADOR CONECTIVIDAD BATCH - Procesamiento en bloques de 50
Procesa el archivo completo de conectividad en bloques para optimizar uso de API
"""
import pandas as pd
import time
from normalizador_ie_conectividad import NormalizadorIEConectividad
import os

def procesar_conectividad_batch(batch_size: int = 50):
    """Procesa archivo de conectividad en bloques"""
    
    print("=== PROCESADOR CONECTIVIDAD EN BLOQUES ===\n")
    
    # Inicializar normalizador
    normalizador = NormalizadorIEConectividad()
    
    # Archivo de conectividad
    archivo_path = r"C:\Users\lucas\Proyectos\Reasis\assets\Consultoria\Información actualizada\4. Conectividad y equipamiento.xlsx"
    
    print("Cargando archivo de conectividad...")
    df = pd.read_excel(archivo_path, sheet_name='hoja1', engine='openpyxl')
    print(f"[OK] Archivo cargado: {len(df)} registros")
    
    # Cargar datos de referencia
    normalizador.cargar_referencia_ie()
    
    # Identificar columnas
    col_ie_nombre = 'Si pertence a una Red Rural, indique el nombre de su IE'
    col_fya = 'Fe y Alegría Nro. ....'
    
    # Crear columnas de resultado
    df['codigo_modular_normalizado'] = None
    df['matching_status'] = 'PENDING'
    df['batch_procesado'] = None
    
    # Filtrar registros con nombres IE
    registros_procesar = df[df[col_ie_nombre].notna()].copy()
    
    print(f"\n=== CONFIGURACIÓN PROCESAMIENTO ===")
    print(f"Total registros en archivo: {len(df)}")
    print(f"Registros con nombres IE: {len(registros_procesar)}")
    print(f"Tamaño de bloque: {batch_size}")
    print(f"Bloques necesarios: {(len(registros_procesar) + batch_size - 1) // batch_size}")
    
    # Procesar en bloques
    total_procesados = 0
    total_matches = 0
    total_errores = 0
    
    for batch_num in range(0, len(registros_procesar), batch_size):
        batch_end = min(batch_num + batch_size, len(registros_procesar))
        batch_actual = registros_procesar.iloc[batch_num:batch_end]
        
        print(f"\n=== BLOQUE {(batch_num // batch_size) + 1} ===")
        print(f"Procesando registros {batch_num + 1}-{batch_end} de {len(registros_procesar)}")
        
        # Procesar cada registro del bloque
        batch_matches = 0
        batch_errores = 0
        
        for idx, (df_idx, row) in enumerate(batch_actual.iterrows()):
            nombre_manual = str(row[col_ie_nombre]).strip()
            red_fya = str(row[col_fya]) if pd.notna(row[col_fya]) else ""
            
            print(f"  [{idx + 1}/{len(batch_actual)}] '{nombre_manual[:30]}...'", end=" ")
            
            # Identificar con Gemini
            codigo_identificado = normalizador.identificar_ie_con_gemini(nombre_manual, red_fya)
            
            if codigo_identificado == "NO_MATCH":
                df.loc[df_idx, 'matching_status'] = 'NO_MATCH'
                df.loc[df_idx, 'batch_procesado'] = (batch_num // batch_size) + 1
                print("-> NO_MATCH")
                
            elif codigo_identificado and len(codigo_identificado) == 7 and codigo_identificado.isdigit():
                df.loc[df_idx, 'codigo_modular_normalizado'] = codigo_identificado
                df.loc[df_idx, 'matching_status'] = 'MATCHED'
                df.loc[df_idx, 'batch_procesado'] = (batch_num // batch_size) + 1
                batch_matches += 1
                print(f"-> {codigo_identificado}")
                
            else:
                df.loc[df_idx, 'matching_status'] = 'ERROR'
                df.loc[df_idx, 'batch_procesado'] = (batch_num // batch_size) + 1
                batch_errores += 1
                print(f"-> ERROR ({codigo_identificado})")
            
            # Pausa pequeña entre requests
            time.sleep(0.5)
        
        # Estadísticas del bloque
        total_procesados += len(batch_actual)
        total_matches += batch_matches
        total_errores += batch_errores
        
        print(f"\n  BLOQUE COMPLETADO:")
        print(f"  - Procesados: {len(batch_actual)}")
        print(f"  - Matches: {batch_matches}")
        print(f"  - Errores: {batch_errores}")
        print(f"  - Tasa éxito: {(batch_matches/len(batch_actual)*100):.1f}%")
        
        # Pausa entre bloques
        if batch_end < len(registros_procesar):
            print(f"  Pausa de 2 segundos antes del siguiente bloque...")
            time.sleep(2)
        
        # Guardar progreso cada bloque
        output_path = f"conectividad_procesado_bloque_{(batch_num // batch_size) + 1}.xlsx"
        df.to_excel(output_path, index=False, engine='openpyxl')
        print(f"  [OK] Progreso guardado en: {output_path}")
    
    # Estadísticas finales
    print(f"\n=== PROCESAMIENTO COMPLETADO ===")
    print(f"Total procesados: {total_procesados}")
    print(f"Total matches: {total_matches}")
    print(f"Total errores: {total_errores}")
    print(f"Total no-match: {total_procesados - total_matches - total_errores}")
    print(f"Tasa éxito global: {(total_matches/total_procesados*100):.1f}%")
    
    # Guardar resultado final
    output_final = "conectividad_normalizado_FINAL.xlsx"
    df.to_excel(output_final, index=False, engine='openpyxl')
    print(f"\n[OK] RESULTADO FINAL guardado en: {output_final}")
    
    # Mostrar estadísticas detalladas
    mostrar_estadisticas_finales(df)
    
    return df

def mostrar_estadisticas_finales(df: pd.DataFrame):
    """Muestra estadísticas detalladas del procesamiento"""
    
    print(f"\n=== ESTADÍSTICAS DETALLADAS ===")
    
    # Por estado
    status_counts = df['matching_status'].value_counts()
    print("\nPor estado:")
    for status, count in status_counts.items():
        if status != 'PENDING':
            print(f"  {status}: {count}")
    
    # Por bloque procesado
    batch_counts = df['batch_procesado'].value_counts().sort_index()
    print("\nPor bloque:")
    for batch, count in batch_counts.items():
        if pd.notna(batch):
            print(f"  Bloque {int(batch)}: {count} registros")
    
    # Matches exitosos por red
    matches_exitosos = df[df['matching_status'] == 'MATCHED']
    if len(matches_exitosos) > 0:
        col_fya = 'Fe y Alegría Nro. ....'
        red_counts = matches_exitosos[col_fya].value_counts()
        print("\nMatches por red Fe y Alegría:")
        for red, count in red_counts.items():
            print(f"  {red}: {count} matches")
    
    # Muestra de matches exitosos
    print(f"\n=== MUESTRA MATCHES EXITOSOS ===")
    col_ie_nombre = 'Si pertence a una Red Rural, indique el nombre de su IE'
    
    for idx, (_, row) in enumerate(matches_exitosos.head(10).iterrows()):
        nombre_orig = row[col_ie_nombre]
        codigo_norm = row['codigo_modular_normalizado']
        print(f"{idx+1:2d}. '{nombre_orig[:30]}...' → {codigo_norm}")

def validar_progreso():
    """Valida archivos de progreso existentes"""
    
    print("=== VALIDADOR DE PROGRESO ===\n")
    
    archivos_batch = []
    batch_num = 1
    
    while True:
        archivo = f"conectividad_procesado_bloque_{batch_num}.xlsx"
        if os.path.exists(archivo):
            archivos_batch.append((batch_num, archivo))
            batch_num += 1
        else:
            break
    
    if archivos_batch:
        print(f"Archivos de progreso encontrados: {len(archivos_batch)}")
        for batch_num, archivo in archivos_batch:
            try:
                df = pd.read_excel(archivo, engine='openpyxl')
                procesados = df[df['batch_procesado'] == batch_num]
                matches = len(procesados[procesados['matching_status'] == 'MATCHED'])
                print(f"  Bloque {batch_num}: {len(procesados)} procesados, {matches} matches")
            except Exception as e:
                print(f"  Bloque {batch_num}: ERROR leyendo archivo - {e}")
        
        # Verificar archivo final
        if os.path.exists("conectividad_normalizado_FINAL.xlsx"):
            print(f"\n[OK] Archivo final encontrado: conectividad_normalizado_FINAL.xlsx")
        else:
            print(f"\n[WARNING] Archivo final no encontrado")
    else:
        print("No se encontraron archivos de progreso previos")

if __name__ == "__main__":
    print("PROCESADOR BATCH CONECTIVIDAD\n")
    
    # Validar progreso previo
    validar_progreso()
    
    # Confirmar procesamiento
    respuesta = input("\n¿Proceder con procesamiento en bloques de 50? (s/n): ").lower()
    
    if respuesta in ['s', 'si', 'yes', 'y']:
        print("\nIniciando procesamiento...")
        df_resultado = procesar_conectividad_batch(batch_size=50)
        print(f"\n[OK] PROCESAMIENTO COMPLETADO EXITOSAMENTE")
    else:
        print("Procesamiento cancelado por el usuario")