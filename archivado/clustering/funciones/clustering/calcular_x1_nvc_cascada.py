"""
Script para calcular X1_NVC - Vulnerabilidad Contextual con vinculación en cascada
Implementa conversión categórica según matriz de operacionalización

Autor: Proyecto Reasis
Fecha: 2025-08-10
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime

def calcular_x1_nvc_cascada():
    """
    Calcula X1_NVC usando vinculación en cascada:
    1. variables_eib_mejoradas_final (fuente principal)
    2. datos_eib_minedu (fuente complementaria)
    3. Resto = imputación contextual
    
    Conversión X1_NVC según quintil pobreza:
    - Quintil 1 (más pobre) → 5 (máxima vulnerabilidad)
    - Quintil 2 → 4
    - Quintil 3 → 3
    - Quintil 4 → 2
    - Quintil 5 (menos pobre) → 1 (mínima vulnerabilidad)
    - Sin datos → 3 (vulnerabilidad media - imputación contextual)
    """
    
    print("=== CALCULANDO X1_NVC VULNERABILIDAD CONTEXTUAL ===\n")
    
    conn = sqlite3.connect('reasis_database.db')
    
    # 1. Obtener instituciones target
    df_target = pd.read_sql_query("""
        SELECT CODIGO_MODULAR, NOMBRE_INSTITUCION
        FROM indices_metodologicos
    """, conn)
    
    print(f"1. INSTITUCIONES TARGET: {len(df_target)}")
    
    # 2. FUENTE 1: variables_eib_mejoradas_final
    print(f"\n2. FUENTE PRINCIPAL - variables_eib_mejoradas_final:")
    
    df_nvc_principal = pd.read_sql_query("""
        SELECT codigo_modular, quintil_pobreza
        FROM variables_eib_mejoradas_final
        WHERE quintil_pobreza IS NOT NULL
    """, conn)
    
    print(f"   Registros disponibles: {len(df_nvc_principal)}")
    
    # Conversión quintil pobreza a X1_NVC (inverso: más pobre = más vulnerable)
    df_nvc_principal['X1_NVC'] = df_nvc_principal['quintil_pobreza'].map({
        1: 5,  # Quintil 1 (más pobre) → máxima vulnerabilidad
        2: 4,  # Quintil 2 → alta vulnerabilidad
        3: 3,  # Quintil 3 → vulnerabilidad media
        4: 2,  # Quintil 4 → baja vulnerabilidad
        5: 1   # Quintil 5 (menos pobre) → mínima vulnerabilidad
    })
    
    print(f"   Conversiones aplicadas (Quintil -> X1_NVC):")
    for quintil in sorted(df_nvc_principal['quintil_pobreza'].unique()):
        x1_nvc_value = 6 - quintil  # Inversion: quintil 1->5, quintil 2->4, etc.
        count = (df_nvc_principal['quintil_pobreza'] == quintil).sum()
        print(f"     Quintil {quintil} -> X1_NVC {x1_nvc_value}: {count} instituciones")
    
    # 3. Vinculación con técnica cascada (directa + enteros)
    print(f"\n3. VINCULACION CASCADA FUENTE PRINCIPAL:")
    
    vinculaciones_principales = []
    
    # 3a. Matching directo con zfill
    df_nvc_principal['codigo_zfill'] = df_nvc_principal['codigo_modular'].astype(str).str.zfill(7)
    
    for _, row in df_nvc_principal.iterrows():
        codigo_zfill = row['codigo_zfill']
        if codigo_zfill in df_target['CODIGO_MODULAR'].values:
            vinculaciones_principales.append({
                'codigo_target': codigo_zfill,
                'X1_NVC': row['X1_NVC'],
                'quintil_original': row['quintil_pobreza'],
                'metodo': 'directo_zfill',
                'fuente': 'variables_eib_mejoradas_final'
            })
    
    codigos_vinculados = {v['codigo_target'] for v in vinculaciones_principales}
    
    # 3b. Matching por enteros para no vinculados
    df_target_pendientes = df_target[~df_target['CODIGO_MODULAR'].isin(codigos_vinculados)]
    df_target_pendientes['codigo_int'] = pd.to_numeric(df_target_pendientes['CODIGO_MODULAR'], errors='coerce')
    mapeo_int_str = dict(zip(df_target_pendientes['codigo_int'], df_target_pendientes['CODIGO_MODULAR']))
    
    for _, row in df_nvc_principal.iterrows():
        try:
            codigo_int = int(row['codigo_modular'])
            if codigo_int in mapeo_int_str:
                codigo_target = mapeo_int_str[codigo_int]
                if codigo_target not in codigos_vinculados:
                    vinculaciones_principales.append({
                        'codigo_target': codigo_target,
                        'X1_NVC': row['X1_NVC'],
                        'quintil_original': row['quintil_pobreza'],
                        'metodo': 'entero_matching',
                        'fuente': 'variables_eib_mejoradas_final'
                    })
                    codigos_vinculados.add(codigo_target)
        except:
            continue
    
    print(f"   Vinculaciones principales: {len(vinculaciones_principales)}")
    
    # 4. FUENTE 2: datos_eib_minedu (complementaria)
    print(f"\n4. FUENTE COMPLEMENTARIA - datos_eib_minedu:")
    
    df_nvc_complementaria = pd.read_sql_query("""
        SELECT codigo_modular, quintil_pobreza
        FROM datos_eib_minedu
        WHERE quintil_pobreza IS NOT NULL
    """, conn)
    
    print(f"   Registros disponibles: {len(df_nvc_complementaria)}")
    
    # Conversión similar
    df_nvc_complementaria['X1_NVC'] = df_nvc_complementaria['quintil_pobreza'].map({
        1: 5, 2: 4, 3: 3, 4: 2, 5: 1
    })
    
    # Vinculación para códigos no cubiertos
    vinculaciones_complementarias = []
    df_nvc_complementaria['codigo_zfill'] = df_nvc_complementaria['codigo_modular'].astype(str).str.zfill(7)
    
    # Matching directo
    for _, row in df_nvc_complementaria.iterrows():
        codigo_zfill = row['codigo_zfill']
        if codigo_zfill in df_target['CODIGO_MODULAR'].values and codigo_zfill not in codigos_vinculados:
            vinculaciones_complementarias.append({
                'codigo_target': codigo_zfill,
                'X1_NVC': row['X1_NVC'],
                'quintil_original': row['quintil_pobreza'],
                'metodo': 'directo_zfill',
                'fuente': 'datos_eib_minedu'
            })
            codigos_vinculados.add(codigo_zfill)
    
    # Matching por enteros
    for _, row in df_nvc_complementaria.iterrows():
        try:
            codigo_int = int(row['codigo_modular'])
            if codigo_int in mapeo_int_str:
                codigo_target = mapeo_int_str[codigo_int]
                if codigo_target not in codigos_vinculados:
                    vinculaciones_complementarias.append({
                        'codigo_target': codigo_target,
                        'X1_NVC': row['X1_NVC'],
                        'quintil_original': row['quintil_pobreza'],
                        'metodo': 'entero_matching',
                        'fuente': 'datos_eib_minedu'
                    })
                    codigos_vinculados.add(codigo_target)
        except:
            continue
    
    print(f"   Vinculaciones complementarias: {len(vinculaciones_complementarias)}")
    
    # 5. Imputación contextual para el resto
    print(f"\n5. IMPUTACION CONTEXTUAL:")
    
    instituciones_sin_nvc = df_target[~df_target['CODIGO_MODULAR'].isin(codigos_vinculados)]
    
    # Análisis de datos disponibles para imputación inteligente
    datos_disponibles = vinculaciones_principales + vinculaciones_complementarias
    if datos_disponibles:
        valores_nvc = [v['X1_NVC'] for v in datos_disponibles]
        nvc_promedio = round(np.mean(valores_nvc))
        nvc_moda = max(set(valores_nvc), key=valores_nvc.count)
        
        print(f"   Análisis datos existentes:")
        print(f"     X1_NVC promedio: {np.mean(valores_nvc):.1f}")
        print(f"     X1_NVC moda: {nvc_moda}")
        print(f"     X1_NVC para imputación: {nvc_promedio} (vulnerabilidad media)")
        
        valor_imputacion = nvc_promedio
    else:
        # Valor por defecto basado en contexto Fe y Alegría (instituciones en zonas vulnerables)
        valor_imputacion = 4  # Alta vulnerabilidad contextual
        print(f"   Sin datos disponibles - usando X1_NVC = {valor_imputacion} (alta vulnerabilidad)")
    
    vinculaciones_imputadas = []
    for _, row in instituciones_sin_nvc.iterrows():
        vinculaciones_imputadas.append({
            'codigo_target': row['CODIGO_MODULAR'],
            'X1_NVC': valor_imputacion,
            'quintil_original': None,
            'metodo': 'imputacion_contextual',
            'fuente': 'analisis_fe_y_alegria'
        })
    
    print(f"   Instituciones imputadas: {len(vinculaciones_imputadas)}")
    
    # 6. Consolidar todas las vinculaciones
    print(f"\n6. CONSOLIDACION FINAL:")
    
    todas_vinculaciones = vinculaciones_principales + vinculaciones_complementarias + vinculaciones_imputadas
    
    print(f"   Total vinculaciones: {len(todas_vinculaciones)}")
    print(f"   Cobertura: {len(todas_vinculaciones)}/{len(df_target)} ({len(todas_vinculaciones)/len(df_target)*100:.1f}%)")
    
    # Distribución final
    distribucion = {}
    for v in todas_vinculaciones:
        nvc_value = v['X1_NVC']
        distribucion[nvc_value] = distribucion.get(nvc_value, 0) + 1
    
    vulnerabilidad_nombres = {
        1: 'Vulnerabilidad Mínima', 
        2: 'Vulnerabilidad Baja',
        3: 'Vulnerabilidad Media',
        4: 'Vulnerabilidad Alta', 
        5: 'Vulnerabilidad Máxima'
    }
    
    print(f"\n   Distribución X1_NVC:")
    for codigo, count in sorted(distribucion.items()):
        nombre = vulnerabilidad_nombres.get(codigo, f'Nivel_{codigo}')
        porcentaje = count/len(todas_vinculaciones)*100
        print(f"     {codigo} ({nombre}): {count} instituciones ({porcentaje:.1f}%)")
    
    # Distribución por método
    metodos = {}
    for v in todas_vinculaciones:
        metodo = v['metodo']
        metodos[metodo] = metodos.get(metodo, 0) + 1
    
    print(f"\n   Distribución por método:")
    for metodo, count in metodos.items():
        print(f"     {metodo}: {count} instituciones")
    
    # 7. Guardar resultados
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = f"temp_data/x1_nvc_calculado_{timestamp}.csv"
    
    df_resultado = pd.DataFrame(todas_vinculaciones)
    df_resultado.to_csv(csv_path, index=False)
    
    print(f"\n7. RESULTADOS GUARDADOS: {csv_path}")
    
    conn.close()
    
    return csv_path, len(todas_vinculaciones), distribucion, metodos

if __name__ == "__main__":
    csv_file, total, dist, metodos_usados = calcular_x1_nvc_cascada()
    
    print(f"\n=== RESULTADO X1_NVC ===")
    print(f"Cobertura: {total}/184 instituciones")
    print(f"Con datos EIB: {metodos_usados.get('directo_zfill',0) + metodos_usados.get('entero_matching',0)} instituciones")
    print(f"Imputados: {metodos_usados.get('imputacion_contextual',0)} instituciones")
    print(f"Archivo: {csv_file}")
    
    if total == 184:
        print(f"\n[EXITO] X1_NVC calculado para todas las instituciones")
    else:
        print(f"\n[PARCIAL] X1_NVC calculado - verificar cobertura")