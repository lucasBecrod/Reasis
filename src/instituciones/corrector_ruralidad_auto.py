#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Corrector Automático de Ruralidad - Proyecto Reasis
Script para corregir automáticamente la clasificación rural/urbano usando la fuente primaria del INEI
"""

import sqlite3
import pandas as pd
from pathlib import Path

def corregir_clasificacion_rural_automatico():
    """Corrige automáticamente la clasificación rural/urbano usando la fuente primaria"""
    print("CORRECTOR AUTOMATICO DE CLASIFICACION RURAL/URBANO")
    print("=" * 70)
    
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
        
        print(f"Registros validos para correccion: {len(df_fuente_rural)}")
        
        # 2. Conectar a base de datos y analizar
        print("\n2. ANALIZANDO ESTADO ACTUAL")
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
        
        print(f"Total instituciones: {len(df_actual)}")
        print(f"Inconsistencias encontradas: {inconsistencias_antes}")
        
        # 3. Aplicar correcciones automáticamente
        print("\n3. APLICANDO CORRECCIONES AUTOMATICAMENTE")
        print("-" * 40)
        
        cursor = conn.cursor()
        correcciones_aplicadas = 0
        
        # Hacer backup antes de modificar
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS instituciones_educativas_backup AS 
            SELECT * FROM instituciones_educativas_v2_mejorada LIMIT 0
        """)
        
        cursor.execute("""
            INSERT OR REPLACE INTO instituciones_educativas_backup 
            SELECT * FROM instituciones_educativas_v2_mejorada
        """)
        
        print("Backup creado exitosamente")
        
        # Aplicar correcciones basadas en fuente primaria
        for _, row_fuente in df_fuente_rural.iterrows():
            codigo = str(row_fuente['codigo_modular'])
            area_oficial = row_fuente['area_censo_oficial']
            es_rural_oficial = 1 if area_oficial == 'Rural' else 0
            
            # Actualizar registro
            cursor.execute("""
                UPDATE instituciones_educativas_v2_mejorada 
                SET es_rural = ?
                WHERE codigo_modular = ?
            """, (es_rural_oficial, codigo))
            
            if cursor.rowcount > 0:
                correcciones_aplicadas += 1
        
        conn.commit()
        print(f"Correcciones aplicadas: {correcciones_aplicadas}")
        
        # 4. Verificar resultado
        print("\n4. VERIFICANDO RESULTADO")
        print("-" * 40)
        
        df_verificacion = pd.read_sql_query("""
            SELECT area_censo, es_rural, COUNT(*) as total
            FROM instituciones_educativas_v2_mejorada
            GROUP BY area_censo, es_rural
            ORDER BY area_censo, es_rural
        """, conn)
        
        print("Distribucion final:")
        for _, row in df_verificacion.iterrows():
            tipo_flag = "Rural" if row['es_rural'] == 1 else "Urbano" 
            print(f"- Area censo '{row['area_censo']}' + Flag '{tipo_flag}': {row['total']} instituciones")
        
        # Verificar inconsistencias finales
        df_check = pd.read_sql_query("""
            SELECT codigo_modular, area_censo, es_rural
            FROM instituciones_educativas_v2_mejorada
        """, conn)
        
        inconsistencias_despues = len(df_check[
            ((df_check['area_censo'] == 'Rural') & (df_check['es_rural'] == 0)) |
            ((df_check['area_censo'] == 'Urbana') & (df_check['es_rural'] == 1))
        ])
        
        print(f"\nResultado de la correccion:")
        print(f"- Inconsistencias antes: {inconsistencias_antes}")
        print(f"- Inconsistencias despues: {inconsistencias_despues}")
        print(f"- Inconsistencias corregidas: {inconsistencias_antes - inconsistencias_despues}")
        
        if inconsistencias_despues == 0:
            print("✓ TODAS LAS INCONSISTENCIAS HAN SIDO CORREGIDAS")
        else:
            print(f"⚠ Quedan {inconsistencias_despues} inconsistencias por resolver")
        
        conn.close()
        
        print(f"\n✓ CORRECCION AUTOMATICA COMPLETADA")
        print("=" * 70)
        print("💾 Se creo un backup en 'instituciones_educativas_backup'")
        print("📊 La tabla 'instituciones_educativas_v2_mejorada' ha sido corregida")
        
    except Exception as e:
        print(f"Error durante la correccion: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    corregir_clasificacion_rural_automatico()