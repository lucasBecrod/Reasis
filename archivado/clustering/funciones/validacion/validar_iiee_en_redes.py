#!/usr/bin/env python3
"""
Validar asignación de IIEE a redes Fe y Alegría
Proyecto Reasis - Verificación de coherencia entre datos

Fuente: assets/Consultoria/Redes.xlsx
- Hoja "colegiosRedConfiramadas": 330 IIEE validadas con sus redes
- Hoja "colegiosXred": Códigos IE organizados por columnas de red

Objetivo: Verificar que las IIEE estén correctamente asignadas en nuestra BD
"""

import pandas as pd
import sqlite3
import sys
import re

def limpiar_codigo_ie(codigo):
    """Limpia y normaliza códigos de IE"""
    if pd.isna(codigo):
        return None
    
    # Convertir a string y limpiar
    codigo_str = str(codigo).strip()
    
    # Extraer solo números (los primeros números encontrados)
    match = re.search(r'(\d+)', codigo_str)
    if match:
        return match.group(1)
    
    return codigo_str

def main():
    print("=== VALIDANDO IIEE EN REDES FE Y ALEGRÍA ===")
    
    # Archivos
    archivo_redes = r"C:\Users\lucas\Proyectos\Reasis\assets\Consultoria\Redes.xlsx"
    db_path = "reasis_database.db"
    
    # 1. Cargar datos del Excel
    print("1. Cargando datos de validación...")
    df_confirmadas = pd.read_excel(archivo_redes, sheet_name='colegiosRedConfiramadas')
    df_por_red = pd.read_excel(archivo_redes, sheet_name='colegiosXred')
    
    print(f"   IIEE confirmadas: {len(df_confirmadas)}")
    print(f"   Redes en colegiosXred: {len(df_por_red.columns)}")
    
    # 2. Procesar hoja colegiosXred para extraer todos los códigos
    print("\n2. Extrayendo códigos IE de colegiosXred...")
    codigos_por_red = {}
    
    for columna in df_por_red.columns:
        red_num = columna.replace('RER FA ', '')
        codigos_brutos = df_por_red[columna].dropna().tolist()
        codigos_limpios = []
        
        for codigo in codigos_brutos:
            codigo_limpio = limpiar_codigo_ie(codigo)
            if codigo_limpio:
                codigos_limpios.append(codigo_limpio)
        
        codigos_por_red[red_num] = codigos_limpios
        print(f"   Red {red_num}: {len(codigos_limpios)} códigos extraídos")
    
    # 3. Conectar a BD y verificar asignaciones actuales
    print("\n3. Verificando asignaciones en base de datos...")
    conn = sqlite3.connect(db_path)
    
    df_bd = pd.read_sql_query("""
        SELECT codigo_modular, nombre_red_fya_matched, nombre_institucion 
        FROM instituciones_educativas 
        WHERE nombre_red_fya_matched IS NOT NULL AND nombre_red_fya_matched != ''
        ORDER BY nombre_red_fya_matched, codigo_modular
    """, conn)
    
    print(f"   IIEE con red asignada en BD: {len(df_bd)}")
    
    # Agrupar por red
    asignaciones_bd = df_bd.groupby('nombre_red_fya_matched')['codigo_modular'].apply(list).to_dict()
    
    for red, codigos in asignaciones_bd.items():
        print(f"   {red}: {len(codigos)} IIEE asignadas")
    
    # 4. Validar coherencia
    print("\n4. Validando coherencia entre fuentes...")
    
    for red_num, codigos_excel in codigos_por_red.items():
        # Buscar la red correspondiente en BD
        red_key = f"Red Fe y Alegría {red_num}"
        codigos_bd = asignaciones_bd.get(red_key, [])
        
        print(f"\n--- RED {red_num} ---")
        print(f"Excel colegiosXred: {len(codigos_excel)} códigos")
        print(f"Base de datos ({red_key}): {len(codigos_bd)} códigos")
        
        # Encontrar coincidencias
        codigos_excel_set = set(codigos_excel)
        codigos_bd_set = set(codigos_bd)
        
        coincidencias = codigos_excel_set.intersection(codigos_bd_set)
        solo_excel = codigos_excel_set - codigos_bd_set
        solo_bd = codigos_bd_set - codigos_excel_set
        
        print(f"Coincidencias: {len(coincidencias)}")
        if solo_excel:
            print(f"Solo en Excel: {len(solo_excel)} - {list(solo_excel)[:5]}...")
        if solo_bd:
            print(f"Solo en BD: {len(solo_bd)} - {list(solo_bd)[:5]}...")
    
    # 5. Validar con hoja confirmadas
    print("\n5. Validando con hoja colegiosRedConfiramadas...")
    
    # Procesar códigos confirmados
    df_confirmadas['codigo_limpio'] = df_confirmadas['codigo_encontrado'].apply(limpiar_codigo_ie)
    confirmadas_por_red = df_confirmadas.groupby('codigo_red')['codigo_limpio'].apply(list).to_dict()
    
    for red_codigo, codigos_confirmados in confirmadas_por_red.items():
        red_num = str(int(red_codigo))
        red_key = f"Red Fe y Alegría {red_num}"
        codigos_bd = asignaciones_bd.get(red_key, [])
        
        print(f"\n--- RED {red_num} (Confirmadas) ---")
        print(f"Confirmadas: {len(codigos_confirmados)}")
        print(f"En BD ({red_key}): {len(codigos_bd)}")
        
        codigos_conf_set = set(filter(None, codigos_confirmados))
        codigos_bd_set = set(codigos_bd)
        
        coincidencias = codigos_conf_set.intersection(codigos_bd_set)
        if len(codigos_conf_set) > 0:
            print(f"Coincidencias: {len(coincidencias)} ({len(coincidencias)/len(codigos_conf_set)*100:.1f}%)")
        else:
            print(f"Coincidencias: {len(coincidencias)} (0.0%)")
    
    # 6. Resumen final
    print("\n6. RESUMEN DE VALIDACIÓN:")
    total_confirmadas = len(df_confirmadas)
    total_bd = len(df_bd)
    
    print(f"   - Total IIEE confirmadas (Excel): {total_confirmadas}")
    print(f"   - Total IIEE con red asignada (BD): {total_bd}")
    print(f"   - Cobertura: {total_bd/total_confirmadas*100:.1f}%")
    print(f"   - Redes validadas: {len(codigos_por_red)}")
    
    conn.close()
    print("\n¡VALIDACIÓN COMPLETADA!")

if __name__ == "__main__":
    main()