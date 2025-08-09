#!/usr/bin/env python3
import pandas as pd
import sqlite3

def verificar_cobertura_completa():
    """Verificación exhaustiva de cobertura entre instituciones Fe y Alegría y archivo EIB"""
    
    print("=== VERIFICACION EXHAUSTIVA DE COBERTURA EIB ===\n")
    
    archivo = r"C:\Users\lucas\Proyectos\Reasis\assets\Consultoria\Información actualizada\Extras\RIIEE EIB 2024 Minedu.xlsx"
    
    try:
        # Cargar archivo EIB
        df_eib = pd.read_excel(archivo, sheet_name='Sheet1')
        print(f"Archivo EIB cargado: {df_eib.shape[0]:,} instituciones")
        
        # Cargar base de datos Fe y Alegría
        conn = sqlite3.connect('reasis_database.db')
        df_fya = pd.read_sql_query("""
            SELECT codigo_modular, nombre_institucion, region, es_eib, modalidad_especifica
            FROM instituciones_educativas 
            ORDER BY codigo_modular
        """, conn)
        conn.close()
        
        print(f"Instituciones Fe y Alegria: {len(df_fya)}")
        print(f"Instituciones Fe y Alegria marcadas como EIB: {df_fya['es_eib'].sum()}")
        
        # Convertir códigos a string para comparación
        codigos_fya = set(df_fya['codigo_modular'].astype(str))
        codigos_eib = set(df_eib['Código modular'].astype(str))
        
        print(f"\nCODIGOS UNICOS:")
        print(f"- Fe y Alegria: {len(codigos_fya)} códigos únicos")
        print(f"- Archivo EIB: {len(codigos_eib)} códigos únicos")
        
        # Verificar coincidencias directas
        coincidencias_directas = codigos_fya.intersection(codigos_eib)
        print(f"\nCOINCIDENCIAS DIRECTAS: {len(coincidencias_directas)}")
        
        if coincidencias_directas:
            print(f"Códigos que coinciden: {sorted(list(coincidencias_directas))}")
        
        # Verificar instituciones Fe y Alegría que NO están en EIB
        faltantes = codigos_fya - codigos_eib
        print(f"\nINSTITUCIONES FE Y ALEGRIA NO ENCONTRADAS EN EIB: {len(faltantes)}")
        
        if faltantes:
            print("Códigos faltantes (primeros 20):")
            df_faltantes = df_fya[df_fya['codigo_modular'].astype(str).isin(list(faltantes))]
            for _, row in df_faltantes.head(20).iterrows():
                eib_status = "EIB" if row['es_eib'] else "No-EIB"
                print(f"  - {row['codigo_modular']}: {row['nombre_institucion']} ({row['region']}) [{eib_status}]")
            
            if len(faltantes) > 20:
                print(f"  ... y {len(faltantes) - 20} más")
        
        # Análisis por estado EIB
        print(f"\nANALISIS POR ESTADO EIB:")
        fya_eib = df_fya[df_fya['es_eib'] == True]
        fya_no_eib = df_fya[df_fya['es_eib'] == False]
        
        print(f"- Fe y Alegria marcadas como EIB: {len(fya_eib)}")
        print(f"- Fe y Alegria marcadas como No-EIB: {len(fya_no_eib)}")
        
        # Verificar cuántas de las marcadas como EIB están en el archivo MINEDU
        codigos_fya_eib = set(fya_eib['codigo_modular'].astype(str))
        coincidencias_eib = codigos_fya_eib.intersection(codigos_eib)
        
        print(f"- Fe y Alegria EIB encontradas en archivo MINEDU: {len(coincidencias_eib)}/{len(fya_eib)} ({len(coincidencias_eib)/len(fya_eib)*100:.1f}%)")
        
        # Verificar si algunas marcadas como No-EIB aparecen en archivo MINEDU
        codigos_fya_no_eib = set(fya_no_eib['codigo_modular'].astype(str))
        coincidencias_no_eib = codigos_fya_no_eib.intersection(codigos_eib)
        
        if coincidencias_no_eib:
            print(f"- Fe y Alegria No-EIB que aparecen en archivo MINEDU: {len(coincidencias_no_eib)}")
            print("  Esto sugiere que algunas instituciones deberían estar marcadas como EIB")
            
            # Mostrar ejemplos
            df_sorpresa = df_fya[df_fya['codigo_modular'].astype(str).isin(list(coincidencias_no_eib))]
            print("  Ejemplos de instituciones 'No-EIB' que aparecen en padrón EIB MINEDU:")
            for _, row in df_sorpresa.head(10).iterrows():
                print(f"    * {row['codigo_modular']}: {row['nombre_institucion']} ({row['region']})")
        
        # Verificar posibles problemas de formato en códigos
        print(f"\nVERIFICACION DE FORMATO DE CODIGOS:")
        
        # Códigos Fe y Alegría con longitudes atípicas
        longitudes_fya = [len(str(cod)) for cod in codigos_fya]
        longitud_mas_comun = max(set(longitudes_fya), key=longitudes_fya.count)
        print(f"- Longitud más común en Fe y Alegria: {longitud_mas_comun} caracteres")
        
        codigos_atipicos = [cod for cod in codigos_fya if len(str(cod)) != longitud_mas_comun]
        if codigos_atipicos:
            print(f"- Códigos Fe y Alegria con longitud atípica: {len(codigos_atipicos)}")
            print(f"  Ejemplos: {codigos_atipicos[:10]}")
        
        # Códigos EIB con longitudes atípicas  
        longitudes_eib = [len(str(cod)) for cod in codigos_eib]
        longitud_mas_comun_eib = max(set(longitudes_eib), key=longitudes_eib.count)
        print(f"- Longitud más común en archivo EIB: {longitud_mas_comun_eib} caracteres")
        
        # Búsqueda por similitud parcial (últimos 6 dígitos)
        print(f"\nBUSQUEDA POR SIMILITUD PARCIAL:")
        print("Verificando si códigos faltantes tienen coincidencias parciales...")
        
        coincidencias_parciales = 0
        for cod_fya in list(faltantes)[:50]:  # Solo primeros 50 para no saturar
            cod_corto = str(cod_fya)[-6:]  # Últimos 6 dígitos
            matches = [cod_eib for cod_eib in codigos_eib if cod_corto in str(cod_eib)]
            if matches:
                coincidencias_parciales += 1
                print(f"  - {cod_fya} podría coincidir con: {matches[:3]}")
        
        if coincidencias_parciales > 0:
            print(f"Se encontraron {coincidencias_parciales} posibles coincidencias parciales")
        else:
            print("No se encontraron coincidencias parciales significativas")
        
        # Resumen final
        print(f"\n" + "="*50)
        print("RESUMEN FINAL:")
        print(f"- Coincidencias exactas: {len(coincidencias_directas)}/381 (7.3%)")
        print(f"- Instituciones EIB confirmadas: {len(coincidencias_eib)}/{len(fya_eib)}")
        print(f"- Posibles actualizaciones de estado EIB: {len(coincidencias_no_eib)}")
        print(f"- Instituciones sin datos EIB: {len(faltantes)}")
        
        return coincidencias_directas, faltantes, coincidencias_no_eib
        
    except Exception as e:
        print(f"Error: {e}")
        return None, None, None

if __name__ == "__main__":
    coincidencias_directas, faltantes, coincidencias_no_eib = verificar_cobertura_completa()