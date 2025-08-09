#!/usr/bin/env python3
"""
Auditoría completa de columnas en tabla instituciones_educativas
Proyecto Reasis - Identificación de redundancias y columnas innecesarias

Objetivo: Reducir columnas manteniendo solo las útiles y completas
"""

import sqlite3
import pandas as pd

def main():
    print("=== AUDITORÍA DE COLUMNAS instituciones_educativas ===")
    
    conn = sqlite3.connect('reasis_database.db')
    
    # 1. Obtener esquema completo
    print("1. Analizando esquema completo...")
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(instituciones_educativas)")
    schema = cursor.fetchall()
    
    print(f"   Total columnas actuales: {len(schema)}")
    
    # 2. Analizar completitud de datos por columna
    print("\n2. Analizando completitud de datos por columna:")
    
    # Obtener conteo total
    cursor.execute("SELECT COUNT(*) FROM instituciones_educativas")
    total_registros = cursor.fetchone()[0]
    
    completitud_datos = []
    
    for col_info in schema:
        col_name = col_info[1]
        col_type = col_info[2]
        
        # Contar valores no nulos y no vacíos
        cursor.execute(f"""
            SELECT COUNT(*) FROM instituciones_educativas 
            WHERE {col_name} IS NOT NULL 
            AND CAST({col_name} AS TEXT) != ''
        """)
        valores_completos = cursor.fetchone()[0]
        
        # Contar valores únicos
        cursor.execute(f"""
            SELECT COUNT(DISTINCT {col_name}) FROM instituciones_educativas 
            WHERE {col_name} IS NOT NULL 
            AND CAST({col_name} AS TEXT) != ''
        """)
        valores_unicos = cursor.fetchone()[0]
        
        porcentaje_completitud = (valores_completos / total_registros) * 100
        
        completitud_datos.append({
            'columna': col_name,
            'tipo': col_type,
            'valores_completos': valores_completos,
            'valores_unicos': valores_unicos,
            'porcentaje_completitud': porcentaje_completitud
        })
    
    # Crear DataFrame para análisis
    df_completitud = pd.DataFrame(completitud_datos)
    df_completitud = df_completitud.sort_values('porcentaje_completitud', ascending=False)
    
    print(f"   Análisis de {len(df_completitud)} columnas:")
    print(df_completitud.to_string(index=False))
    
    # 3. Identificar columnas problemáticas
    print("\n3. Identificando columnas problemáticas:")
    
    # Columnas completamente vacías (0% completitud)
    vacias = df_completitud[df_completitud['porcentaje_completitud'] == 0]
    print(f"   Columnas completamente vacías: {len(vacias)}")
    if len(vacias) > 0:
        print(f"   {list(vacias['columna'])}")
    
    # Columnas con muy baja completitud (<5%)
    baja_completitud = df_completitud[
        (df_completitud['porcentaje_completitud'] > 0) & 
        (df_completitud['porcentaje_completitud'] < 5)
    ]
    print(f"   Columnas con <5% completitud: {len(baja_completitud)}")
    if len(baja_completitud) > 0:
        print(f"   {list(baja_completitud['columna'])}")
    
    # Columnas con un solo valor único (potencialmente inútiles)
    un_solo_valor = df_completitud[df_completitud['valores_unicos'] == 1]
    print(f"   Columnas con un solo valor: {len(un_solo_valor)}")
    if len(un_solo_valor) > 0:
        print(f"   {list(un_solo_valor['columna'])}")
    
    # 4. Analizar posibles redundancias específicas
    print("\n4. Analizando redundancias específicas:")
    
    # Columnas de códigos/identificadores
    columnas_codigo = [col for col in df_completitud['columna'] if 'codigo' in col.lower()]
    print(f"   Columnas con 'codigo': {len(columnas_codigo)}")
    for col in columnas_codigo:
        completitud = df_completitud[df_completitud['columna'] == col]['porcentaje_completitud'].iloc[0]
        unicos = df_completitud[df_completitud['columna'] == col]['valores_unicos'].iloc[0]
        print(f"     {col}: {completitud:.1f}% completitud, {unicos} valores únicos")
    
    # Columnas relacionadas con redes
    columnas_red = [col for col in df_completitud['columna'] if any(palabra in col.lower() for palabra in ['red', 'fya', 'rer'])]
    print(f"\n   Columnas relacionadas con redes: {len(columnas_red)}")
    for col in columnas_red:
        completitud = df_completitud[df_completitud['columna'] == col]['porcentaje_completitud'].iloc[0]
        unicos = df_completitud[df_completitud['columna'] == col]['valores_unicos'].iloc[0]
        print(f"     {col}: {completitud:.1f}% completitud, {unicos} valores únicos")
    
    # 5. Analizar duplicación de información geográfica
    print("\n5. Analizando información geográfica:")
    columnas_geo = ['region', 'provincia', 'distrito', 'departamento', 'localidad', 'centro_poblado', 'direccion']
    for col in columnas_geo:
        if col in df_completitud['columna'].values:
            completitud = df_completitud[df_completitud['columna'] == col]['porcentaje_completitud'].iloc[0]
            unicos = df_completitud[df_completitud['columna'] == col]['valores_unicos'].iloc[0]
            print(f"     {col}: {completitud:.1f}% completitud, {unicos} valores únicos")
    
    # 6. Analizar campos de contacto/metadata
    print("\n6. Analizando campos de contacto/metadata:")
    columnas_meta = ['director', 'telefono', 'email', 'pagina_web', 'fecha_actualizacion', 'usuario_actualizacion', 'fuente_datos']
    for col in columnas_meta:
        if col in df_completitud['columna'].values:
            completitud = df_completitud[df_completitud['columna'] == col]['porcentaje_completitud'].iloc[0]
            unicos = df_completitud[df_completitud['columna'] == col]['valores_unicos'].iloc[0]
            print(f"     {col}: {completitud:.1f}% completitud, {unicos} valores únicos")
    
    # 7. Recomendaciones
    print("\n7. RECOMENDACIONES PARA LIMPIEZA:")
    
    print("\n   ELIMINAR (Columnas vacías o inútiles):")
    candidatos_eliminar = df_completitud[
        (df_completitud['porcentaje_completitud'] == 0) | 
        (df_completitud['valores_unicos'] == 1)
    ]
    for _, row in candidatos_eliminar.iterrows():
        print(f"     - {row['columna']}: {row['porcentaje_completitud']:.1f}% completitud, {row['valores_unicos']} valor único")
    
    print("\n   REVISAR (Baja completitud):")
    candidatos_revisar = df_completitud[
        (df_completitud['porcentaje_completitud'] > 0) & 
        (df_completitud['porcentaje_completitud'] < 10) &
        (df_completitud['valores_unicos'] > 1)
    ]
    for _, row in candidatos_revisar.iterrows():
        print(f"     - {row['columna']}: {row['porcentaje_completitud']:.1f}% completitud")
    
    print("\n   MANTENER (Buena completitud y útiles):")
    candidatos_mantener = df_completitud[df_completitud['porcentaje_completitud'] >= 50]
    print(f"     Total columnas recomendadas: {len(candidatos_mantener)}")
    
    conn.close()
    print("\n¡AUDITORÍA COMPLETADA!")

if __name__ == "__main__":
    main()