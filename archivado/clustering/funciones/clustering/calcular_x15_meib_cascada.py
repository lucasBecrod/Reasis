"""
Script para calcular X15_MEIB - Modalidad EIB con vinculación en cascada
Implementa conversión categórica según matriz de operacionalización

Autor: Proyecto Reasis
Fecha: 2025-08-10
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime

def calcular_x15_meib_cascada():
    """
    Calcula X15_MEIB usando vinculación en cascada:
    1. datos_eib_minedu (fuente principal)
    2. variables_eib_mejoradas_final (complementaria)  
    3. Resto = No EIB (valor 0)
    
    Conversión:
    - "EIB de fortalecimiento" → 1
    - "EIB de revitalización" → 2
    - Sin modalidad EIB → 0
    """
    
    print("=== CALCULANDO X15_MEIB MODALIDAD EIB ===\n")
    
    conn = sqlite3.connect('reasis_database.db')
    
    # 1. Obtener instituciones target
    df_target = pd.read_sql_query("""
        SELECT CODIGO_MODULAR, NOMBRE_INSTITUCION
        FROM indices_metodologicos
    """, conn)
    
    print(f"1. INSTITUCIONES TARGET: {len(df_target)}")
    
    # 2. FUENTE 1: datos_eib_minedu
    print(f"\n2. FUENTE PRINCIPAL - datos_eib_minedu:")
    
    df_eib_principal = pd.read_sql_query("""
        SELECT codigo_modular, modalidad_eib
        FROM datos_eib_minedu
        WHERE modalidad_eib IS NOT NULL
    """, conn)
    
    print(f"   Registros disponibles: {len(df_eib_principal)}")
    
    # Conversión modalidad EIB a código numérico
    df_eib_principal['X15_MEIB'] = df_eib_principal['modalidad_eib'].map({
        'EIB de fortalecimiento': 1,
        'EIB de revitalización': 2
    })
    
    print(f"   Conversiones aplicadas:")
    for modalidad, codigo in [('EIB de fortalecimiento', 1), ('EIB de revitalización', 2)]:
        count = (df_eib_principal['X15_MEIB'] == codigo).sum()
        print(f"     {modalidad} -> {codigo}: {count} instituciones")
    
    # 3. Vinculación con técnica cascada (directa + enteros)
    print(f"\n3. VINCULACION CASCADA FUENTE PRINCIPAL:")
    
    vinculaciones_principales = []
    
    # 3a. Matching directo con zfill
    df_eib_principal['codigo_zfill'] = df_eib_principal['codigo_modular'].astype(str).str.zfill(7)
    
    for _, row in df_eib_principal.iterrows():
        codigo_zfill = row['codigo_zfill']
        if codigo_zfill in df_target['CODIGO_MODULAR'].values:
            vinculaciones_principales.append({
                'codigo_target': codigo_zfill,
                'X15_MEIB': row['X15_MEIB'],
                'modalidad_original': row['modalidad_eib'],
                'metodo': 'directo_zfill',
                'fuente': 'datos_eib_minedu'
            })
    
    codigos_vinculados = {v['codigo_target'] for v in vinculaciones_principales}
    
    # 3b. Matching por enteros para no vinculados
    df_target_pendientes = df_target[~df_target['CODIGO_MODULAR'].isin(codigos_vinculados)]
    df_target_pendientes['codigo_int'] = pd.to_numeric(df_target_pendientes['CODIGO_MODULAR'], errors='coerce')
    mapeo_int_str = dict(zip(df_target_pendientes['codigo_int'], df_target_pendientes['CODIGO_MODULAR']))
    
    for _, row in df_eib_principal.iterrows():
        try:
            codigo_int = int(row['codigo_modular'])
            if codigo_int in mapeo_int_str:
                codigo_target = mapeo_int_str[codigo_int]
                if codigo_target not in codigos_vinculados:
                    vinculaciones_principales.append({
                        'codigo_target': codigo_target,
                        'X15_MEIB': row['X15_MEIB'],
                        'modalidad_original': row['modalidad_eib'],
                        'metodo': 'entero_matching',
                        'fuente': 'datos_eib_minedu'
                    })
                    codigos_vinculados.add(codigo_target)
        except:
            continue
    
    print(f"   Vinculaciones principales: {len(vinculaciones_principales)}")
    
    # 4. FUENTE 2: variables_eib_mejoradas_final (complementaria)
    print(f"\n4. FUENTE COMPLEMENTARIA - variables_eib_mejoradas_final:")
    
    df_eib_complementaria = pd.read_sql_query("""
        SELECT codigo_modular, modalidad_eib
        FROM variables_eib_mejoradas_final
        WHERE modalidad_eib IS NOT NULL
    """, conn)
    
    print(f"   Registros disponibles: {len(df_eib_complementaria)}")
    
    # Conversión similar
    df_eib_complementaria['X15_MEIB'] = df_eib_complementaria['modalidad_eib'].map({
        'EIB de fortalecimiento': 1,
        'EIB de revitalización': 2
    })
    
    # Vinculación para códigos no cubiertos
    vinculaciones_complementarias = []
    df_eib_complementaria['codigo_zfill'] = df_eib_complementaria['codigo_modular'].astype(str).str.zfill(7)
    
    # Matching directo
    for _, row in df_eib_complementaria.iterrows():
        codigo_zfill = row['codigo_zfill']
        if codigo_zfill in df_target['CODIGO_MODULAR'].values and codigo_zfill not in codigos_vinculados:
            vinculaciones_complementarias.append({
                'codigo_target': codigo_zfill,
                'X15_MEIB': row['X15_MEIB'],
                'modalidad_original': row['modalidad_eib'],
                'metodo': 'directo_zfill',
                'fuente': 'variables_eib_mejoradas_final'
            })
            codigos_vinculados.add(codigo_zfill)
    
    # Matching por enteros
    for _, row in df_eib_complementaria.iterrows():
        try:
            codigo_int = int(row['codigo_modular'])
            if codigo_int in mapeo_int_str:
                codigo_target = mapeo_int_str[codigo_int]
                if codigo_target not in codigos_vinculados:
                    vinculaciones_complementarias.append({
                        'codigo_target': codigo_target,
                        'X15_MEIB': row['X15_MEIB'],
                        'modalidad_original': row['modalidad_eib'],
                        'metodo': 'entero_matching',
                        'fuente': 'variables_eib_mejoradas_final'
                    })
                    codigos_vinculados.add(codigo_target)
        except:
            continue
    
    print(f"   Vinculaciones complementarias: {len(vinculaciones_complementarias)}")
    
    # 5. Asignar No-EIB al resto
    print(f"\n5. ASIGNACION NO-EIB:")
    
    instituciones_sin_eib = df_target[~df_target['CODIGO_MODULAR'].isin(codigos_vinculados)]
    
    vinculaciones_no_eib = []
    for _, row in instituciones_sin_eib.iterrows():
        vinculaciones_no_eib.append({
            'codigo_target': row['CODIGO_MODULAR'],
            'X15_MEIB': 0,
            'modalidad_original': 'No EIB',
            'metodo': 'inferencia_no_eib',
            'fuente': 'asignacion_resto'
        })
    
    print(f"   Instituciones No-EIB: {len(vinculaciones_no_eib)}")
    
    # 6. Consolidar todas las vinculaciones
    print(f"\n6. CONSOLIDACION FINAL:")
    
    todas_vinculaciones = vinculaciones_principales + vinculaciones_complementarias + vinculaciones_no_eib
    
    print(f"   Total vinculaciones: {len(todas_vinculaciones)}")
    print(f"   Cobertura: {len(todas_vinculaciones)}/{len(df_target)} ({len(todas_vinculaciones)/len(df_target)*100:.1f}%)")
    
    # Distribución final
    distribucion = {}
    for v in todas_vinculaciones:
        meib_value = v['X15_MEIB']
        distribucion[meib_value] = distribucion.get(meib_value, 0) + 1
    
    categorias_nombres = {0: 'No EIB', 1: 'EIB Fortalecimiento', 2: 'EIB Revitalización'}
    
    print(f"\n   Distribución X15_MEIB:")
    for codigo, count in sorted(distribucion.items()):
        nombre = categorias_nombres.get(codigo, f'Categoria_{codigo}')
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
    csv_path = f"temp_data/x15_meib_calculado_{timestamp}.csv"
    
    df_resultado = pd.DataFrame(todas_vinculaciones)
    df_resultado.to_csv(csv_path, index=False)
    
    print(f"\n7. RESULTADOS GUARDADOS: {csv_path}")
    
    conn.close()
    
    return csv_path, len(todas_vinculaciones), distribucion, metodos

if __name__ == "__main__":
    csv_file, total, dist, metodos_usados = calcular_x15_meib_cascada()
    
    print(f"\n=== RESULTADO X15_MEIB ===")
    print(f"Cobertura: {total}/184 instituciones")
    print(f"EIB (1+2): {dist.get(1,0) + dist.get(2,0)} instituciones")
    print(f"No EIB (0): {dist.get(0,0)} instituciones")
    print(f"Archivo: {csv_file}")
    
    if total == 184:
        print(f"\n[EXITO] X15_MEIB calculado para todas las instituciones")
    else:
        print(f"\n[PARCIAL] X15_MEIB calculado - verificar cobertura")