#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pandas as pd
import sqlite3
import numpy as np

def integrar_datos_eib():
    """Integra los datos EIB del padrón MINEDU con las instituciones Fe y Alegría"""
    print("=== INTEGRADOR DE DATOS EIB MINEDU ===\n")
    
    # Conectar a la base de datos
    conn = sqlite3.connect('reasis_database.db')
    
    # Cargar archivo EIB MINEDU
    archivo_eib = r"C:\Users\lucas\Proyectos\Reasis\assets\Consultoria\Información actualizada\Extras\RIIEE EIB 2024 Minedu.xlsx"
    
    try:
        print("Cargando archivo EIB MINEDU...")
        df_eib = pd.read_excel(archivo_eib, engine='openpyxl')
        print(f"[OK] Archivo cargado: {len(df_eib):,} instituciones")
        
        # Los 28 códigos Fe y Alegría confirmados en EIB
        codigos_eib_fya = [
            '0238253', '0238501', '0238782', '0238816', '0238824', '0238840',
            '0238857', '0239319', '0239327', '0239335', '0239343', '0242073',
            '0242081', '0242099', '0242107', '0242149', '0242156', '0451203',
            '0451211', '0451229', '0451237', '0451245', '0451252', '0451260',
            '0451278', '0451286', '0451294', '0451302'
        ]
        
        # Filtrar datos EIB solo para Fe y Alegría
        df_eib_fya = df_eib[df_eib['Código modular'].astype(str).str.zfill(7).isin(codigos_eib_fya)].copy()
        print(f"[OK] Instituciones Fe y Alegria en EIB: {len(df_eib_fya)}")
        
        if len(df_eib_fya) == 0:
            print("[ERROR] No se encontraron instituciones Fe y Alegria en el archivo EIB")
            return
            
        # Mostrar columnas disponibles para verificar nombres exactos
        print(f"\nColumnas disponibles en archivo EIB: {len(df_eib.columns)}")
        columnas_interes = [col for col in df_eib.columns if any(keyword in col.lower() 
                           for keyword in ['quintil', 'pobreza', 'rural', 'eib', 'agua', 'elect', 'internet', 'vraem', 'frontera'])]
        
        print(f"Columnas de interés identificadas: {len(columnas_interes)}")
        for col in columnas_interes[:10]:  # Mostrar primeras 10
            print(f"  - {col}")
        
        # Preparar datos para integración
        df_integracion = df_eib_fya.copy()
        df_integracion['codigo_modular'] = df_integracion['Código modular'].astype(str).str.zfill(7)
        
        # Variables clave a extraer
        variables_mapeo = {}
        
        # X1_NVC - Quintil de pobreza (buscar columna exacta)
        col_quintil = None
        for col in df_eib.columns:
            if 'quintil' in col.lower() and 'pobreza' in col.lower():
                col_quintil = col
                break
        
        if col_quintil:
            variables_mapeo['quintil_pobreza'] = col_quintil
            print(f"[OK] Quintil de pobreza: {col_quintil}")
        
        # X15_MEIB - Forma de atención EIB
        col_eib = None
        for col in df_eib.columns:
            if 'forma' in col.lower() and 'eib' in col.lower():
                col_eib = col
                break
                
        if col_eib:
            variables_mapeo['modalidad_eib'] = col_eib
            print(f"[OK] Modalidad EIB: {col_eib}")
        
        # X2_TR - Tipo ruralidad
        col_rural = None
        for col in df_eib.columns:
            if 'rural' in col.lower() and ('tipo' in col.lower() or 'área' in col.lower()):
                col_rural = col
                break
                
        if col_rural:
            variables_mapeo['tipo_ruralidad'] = col_rural
            print(f"[OK] Tipo ruralidad: {col_rural}")
            
        # Mostrar muestra de datos para verificar
        print(f"\nMuestra de datos para las primeras 3 instituciones:")
        for i, (idx, row) in enumerate(df_integracion.head(3).iterrows()):
            print(f"\nInstitucion {i+1}: {row['codigo_modular']}")
            for var_name, col_name in variables_mapeo.items():
                if col_name in row:
                    print(f"  {var_name}: {row[col_name]}")
        
        # Crear tabla EIB si no existe
        query_crear_tabla = """
        CREATE TABLE IF NOT EXISTS datos_eib_minedu (
            codigo_modular TEXT PRIMARY KEY,
            quintil_pobreza TEXT,
            modalidad_eib TEXT,
            tipo_ruralidad TEXT,
            servicios_agua TEXT,
            servicios_electricidad TEXT,
            servicios_internet TEXT,
            contexto_vraem TEXT,
            contexto_frontera TEXT,
            contexto_mineria TEXT,
            fecha_integracion TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (codigo_modular) REFERENCES instituciones_educativas_v2_mejorada(codigo_modular)
        )
        """
        
        conn.execute(query_crear_tabla)
        print(f"[OK] Tabla datos_eib_minedu creada/verificada")
        
        # Buscar columnas de servicios básicos
        col_agua = None
        col_electricidad = None  
        col_internet = None
        
        for col in df_eib.columns:
            if 'agua' in col.lower():
                col_agua = col
            elif 'electric' in col.lower():
                col_electricidad = col
            elif 'internet' in col.lower():
                col_internet = col
                
        # Buscar contextos especiales
        col_vraem = None
        col_frontera = None
        col_mineria = None
        
        for col in df_eib.columns:
            if 'vraem' in col.lower():
                col_vraem = col
            elif 'frontera' in col.lower():
                col_frontera = col
            elif 'miner' in col.lower():
                col_mineria = col
        
        # Preparar datos para inserción
        datos_insertar = []
        
        for idx, row in df_integracion.iterrows():
            datos = {
                'codigo_modular': row['codigo_modular'],
                'quintil_pobreza': str(row[col_quintil]) if col_quintil and col_quintil in row else None,
                'modalidad_eib': str(row[col_eib]) if col_eib and col_eib in row else None,
                'tipo_ruralidad': str(row[col_rural]) if col_rural and col_rural in row else None,
                'servicios_agua': str(row[col_agua]) if col_agua and col_agua in row else None,
                'servicios_electricidad': str(row[col_electricidad]) if col_electricidad and col_electricidad in row else None,
                'servicios_internet': str(row[col_internet]) if col_internet and col_internet in row else None,
                'contexto_vraem': str(row[col_vraem]) if col_vraem and col_vraem in row else None,
                'contexto_frontera': str(row[col_frontera]) if col_frontera and col_frontera in row else None,
                'contexto_mineria': str(row[col_mineria]) if col_mineria and col_mineria in row else None
            }
            datos_insertar.append(datos)
        
        # Insertar datos
        query_insertar = """
        INSERT OR REPLACE INTO datos_eib_minedu 
        (codigo_modular, quintil_pobreza, modalidad_eib, tipo_ruralidad, 
         servicios_agua, servicios_electricidad, servicios_internet,
         contexto_vraem, contexto_frontera, contexto_mineria)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        cursor = conn.cursor()
        for datos in datos_insertar:
            cursor.execute(query_insertar, (
                datos['codigo_modular'],
                datos['quintil_pobreza'],
                datos['modalidad_eib'], 
                datos['tipo_ruralidad'],
                datos['servicios_agua'],
                datos['servicios_electricidad'],
                datos['servicios_internet'],
                datos['contexto_vraem'],
                datos['contexto_frontera'],
                datos['contexto_mineria']
            ))
        
        conn.commit()
        print(f"[OK] Insertados {len(datos_insertar)} registros en tabla datos_eib_minedu")
        
        # Verificar inserción
        query_verificar = "SELECT COUNT(*) as total FROM datos_eib_minedu"
        resultado = pd.read_sql_query(query_verificar, conn)
        print(f"[OK] Total registros en tabla EIB: {resultado.iloc[0]['total']}")
        
        # Actualizar estado EIB en tabla principal
        query_actualizar = """
        UPDATE instituciones_educativas_v2_mejorada 
        SET es_eib = 'Sí'
        WHERE codigo_modular IN ({})
        """.format(','.join(['?' for _ in codigos_eib_fya]))
        
        cursor.execute(query_actualizar, codigos_eib_fya)
        conn.commit()
        print(f"[OK] Actualizados {cursor.rowcount} registros como EIB en tabla principal")
        
        # Mostrar resumen final
        print(f"\n=== RESUMEN DE INTEGRACION ===")
        print(f"Instituciones EIB integradas: {len(datos_insertar)}")
        print(f"Variables disponibles: {len([v for v in variables_mapeo.values() if v])}")
        print(f"Servicios básicos mapeados: {sum([1 for col in [col_agua, col_electricidad, col_internet] if col])}")
        print(f"Contextos especiales: {sum([1 for col in [col_vraem, col_frontera, col_mineria] if col])}")
        
        # Mostrar algunas estadísticas
        if col_quintil:
            quintiles = df_integracion[col_quintil].value_counts()
            print(f"\nDistribución por quintil de pobreza:")
            for quintil, count in quintiles.items():
                print(f"  {quintil}: {count} instituciones")
                
        if col_eib:
            modalidades = df_integracion[col_eib].value_counts()
            print(f"\nDistribución por modalidad EIB:")
            for modalidad, count in modalidades.items():
                print(f"  {modalidad}: {count} instituciones")
        
    except Exception as e:
        print(f"[ERROR] Error durante la integración: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    integrar_datos_eib()