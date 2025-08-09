#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Corrector de Ruralidad - Proyecto Reasis
Script para corregir la clasificación rural/urbano usando la fuente primaria del INEI
"""

import sqlite3
import pandas as pd
from pathlib import Path

def corregir_clasificacion_rural():
    """Corrige la clasificación rural/urbano usando la fuente primaria"""
    print("CORRECTOR DE CLASIFICACION RURAL/URBANO")
    print("=" * 60)
    
    # 1. Cargar fuente primaria
    print("\n1. CARGANDO FUENTE PRIMARIA")
    print("-" * 40)
    
    fuente_path = "assets/Consultoria/Información actualizada/1. Ruralidad, EIB y TOE.xlsx"
    
    if not Path(fuente_path).exists():
        print(f"Error: Archivo fuente no encontrado: {fuente_path}")
        return
    
    try:
        # Cargar datos de la fuente primaria
        df_fuente = pd.read_excel(fuente_path, sheet_name='DatosGlobales')
        print(f"Registros cargados de fuente primaria: {len(df_fuente)}")
        
        # Seleccionar campos relevantes
        df_fuente_rural = df_fuente[['cod_mod', 'dareacenso']].copy()
        df_fuente_rural.columns = ['codigo_modular', 'area_censo_oficial']
        
        # Limpiar datos
        df_fuente_rural = df_fuente_rural.dropna()
        df_fuente_rural['codigo_modular'] = df_fuente_rural['codigo_modular'].astype(str)
        
        print(f"Registros válidos para corrección: {len(df_fuente_rural)}")
        
        # 2. Conectar a base de datos
        print("\n2. ANALIZANDO INCONSISTENCIAS ACTUALES")
        print("-" * 40)
        
        conn = sqlite3.connect('reasis_database.db')
        
        # Obtener datos actuales
        df_actual = pd.read_sql_query("""
            SELECT codigo_modular, area_censo, es_rural, nombre_institucion
            FROM instituciones_educativas_v2_mejorada
        """, conn)
        
        # Analizar inconsistencias actuales
        inconsistencias_antes = len(df_actual[
            ((df_actual['area_censo'] == 'Rural') & (df_actual['es_rural'] == 0)) |
            ((df_actual['area_censo'] == 'Urbana') & (df_actual['es_rural'] == 1))
        ])
        
        print(f"Inconsistencias encontradas: {inconsistencias_antes}")
        
        # 3. Preparar correcciones
        print("\n3. PREPARANDO CORRECCIONES")
        print("-" * 40)
        
        # Combinar datos
        df_correccion = df_actual.merge(
            df_fuente_rural, 
            on='codigo_modular', 
            how='left'
        )
        
        # Identificar qué necesita corrección
        df_correccion['necesita_correccion_area'] = (
            df_correccion['area_censo'] != df_correccion['area_censo_oficial']
        ) & df_correccion['area_censo_oficial'].notna()
        
        df_correccion['nueva_es_rural'] = df_correccion['area_censo_oficial'].apply(
            lambda x: 1 if x == 'Rural' else 0 if x == 'Urbana' else None
        )
        
        correcciones_area = df_correccion['necesita_correccion_area'].sum()
        correcciones_flag = (df_correccion['es_rural'] != df_correccion['nueva_es_rural']).sum()
        
        print(f"Registros que necesitan corrección de área_censo: {correcciones_area}")
        print(f"Registros que necesitan corrección de es_rural: {correcciones_flag}")
        
        # Mostrar algunos ejemplos de correcciones
        print("\nEjemplos de correcciones a realizar:")
        ejemplos = df_correccion[
            df_correccion['necesita_correccion_area'] | 
            (df_correccion['es_rural'] != df_correccion['nueva_es_rural'])
        ].head(10)
        
        for _, row in ejemplos.iterrows():
            if pd.notna(row['area_censo_oficial']):
                print(f"- {row['nombre_institucion'][:40]}...")
                print(f"  Código: {row['codigo_modular']}")
                print(f"  Actual: área_censo='{row['area_censo']}', es_rural={row['es_rural']}")
                print(f"  Oficial: área_censo='{row['area_censo_oficial']}', es_rural={row['nueva_es_rural']}")
                print()
        
        # 4. Aplicar correcciones
        print("\n4. APLICANDO CORRECCIONES")
        print("-" * 40)
        
        respuesta = input("¿Desea aplicar las correcciones? (s/n): ").lower()
        
        if respuesta == 's':
            cursor = conn.cursor()
            correcciones_aplicadas = 0
            
            for _, row in df_correccion.iterrows():
                if pd.notna(row['area_censo_oficial']):
                    # Actualizar ambos campos
                    cursor.execute("""
                        UPDATE instituciones_educativas_v2_mejorada 
                        SET area_censo = ?, es_rural = ?
                        WHERE codigo_modular = ?
                    """, (
                        row['area_censo_oficial'],
                        int(row['nueva_es_rural']),
                        row['codigo_modular']
                    ))
                    correcciones_aplicadas += 1
            
            conn.commit()
            print(f"Correcciones aplicadas: {correcciones_aplicadas}")
            
            # 5. Verificar resultado
            print("\n5. VERIFICANDO RESULTADO")
            print("-" * 40)
            
            df_verificacion = pd.read_sql_query("""
                SELECT codigo_modular, area_censo, es_rural
                FROM instituciones_educativas_v2_mejorada
            """, conn)
            
            inconsistencias_despues = len(df_verificacion[
                ((df_verificacion['area_censo'] == 'Rural') & (df_verificacion['es_rural'] == 0)) |
                ((df_verificacion['area_censo'] == 'Urbana') & (df_verificacion['es_rural'] == 1))
            ])
            
            print(f"Inconsistencias antes: {inconsistencias_antes}")
            print(f"Inconsistencias después: {inconsistencias_despues}")
            print(f"Inconsistencias corregidas: {inconsistencias_antes - inconsistencias_despues}")
            
            # Resumen final
            resumen = df_verificacion.groupby(['area_censo', 'es_rural']).size().reset_index(name='count')
            print("\nDistribución final:")
            for _, row in resumen.iterrows():
                tipo = "Rural" if row['es_rural'] == 1 else "Urbano"
                print(f"- Área censo '{row['area_censo']}' + Flag '{tipo}': {row['count']} instituciones")
            
        else:
            print("Correcciones canceladas por el usuario")
        
        conn.close()
        
        print(f"\n✓ PROCESO COMPLETADO")
        print("=" * 60)
        
    except Exception as e:
        print(f"Error durante la corrección: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    corregir_clasificacion_rural()