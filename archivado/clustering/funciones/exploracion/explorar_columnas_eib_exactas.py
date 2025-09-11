#!/usr/bin/env python3
"""
Explorador exacto de columnas del archivo EIB MINEDU
Proyecto Reasis - Identificar nombres exactos para integración

Objetivo: Encontrar los nombres exactos de todas las columnas relevantes
"""

import pandas as pd

def main():
    print("=== EXPLORADOR EXACTO COLUMNAS EIB MINEDU ===")
    
    archivo_eib = r"C:\Users\lucas\Proyectos\Reasis\assets\Consultoria\Información de referencia\RegistroNacional EIB Minedu\RIIEE EIB 2024 Minedu.xlsx"
    
    try:
        # Cargar solo las primeras filas para obtener nombres exactos
        df_sample = pd.read_excel(archivo_eib, nrows=3)
        
        print(f"Total columnas: {len(df_sample.columns)}")
        print("\nTODAS LAS COLUMNAS DISPONIBLES:")
        
        for i, col in enumerate(df_sample.columns):
            print(f"{i+1:3d}. '{col}'")
        
        print("\n" + "="*80)
        print("COLUMNAS RELEVANTES IDENTIFICADAS:")
        
        # Buscar columnas específicas
        columnas_relevantes = {}
        
        for col in df_sample.columns:
            col_lower = str(col).lower()
            
            # Códigos identificadores
            if 'código' in col_lower and 'modular' in col_lower:
                columnas_relevantes['codigo_modular'] = col
                print(f"✓ Código Modular: '{col}'")
            elif 'código' in col_lower and ('local' in col_lower or 'educativo' in col_lower):
                columnas_relevantes['codigo_local'] = col
                print(f"✓ Código Local: '{col}'")
            elif 'código' in col_lower and 'institución' in col_lower:
                columnas_relevantes['codigo_institucion'] = col
                print(f"✓ Código Institución: '{col}'")
            elif 'anexo' in col_lower:
                columnas_relevantes['anexo'] = col
                print(f"✓ Anexo: '{col}'")
            
            # Condición laboral
            elif 'condición' in col_lower and 'nombrado' in col_lower:
                columnas_relevantes['nombrado'] = col
                print(f"✓ Nombrado: '{col}'")
            elif 'condición' in col_lower and 'contratado' in col_lower:
                columnas_relevantes['contratado'] = col
                print(f"✓ Contratado: '{col}'")
            
            # Información institucional
            elif 'institución' in col_lower and 'educativa' in col_lower and 'condición' not in col_lower:
                columnas_relevantes['nombre_ie'] = col
                print(f"✓ Nombre IE: '{col}'")
            elif col_lower == 'región':
                columnas_relevantes['region'] = col
                print(f"✓ Región: '{col}'")
            elif col_lower == 'distrito':
                columnas_relevantes['distrito'] = col
                print(f"✓ Distrito: '{col}'")
        
        print("\n" + "="*80)
        print("RESUMEN DE DATOS PARA X5_ED:")
        
        # Verificar si tenemos lo mínimo necesario
        tiene_codigo = any(key in columnas_relevantes for key in ['codigo_modular', 'codigo_local', 'codigo_institucion'])
        tiene_estabilidad = 'nombrado' in columnas_relevantes and 'contratado' in columnas_relevantes
        
        print(f"✓ Códigos identificadores: {'SÍ' if tiene_codigo else 'NO'}")
        print(f"✓ Datos estabilidad docente: {'SÍ' if tiene_estabilidad else 'NO'}")
        
        if tiene_codigo and tiene_estabilidad:
            print("\n🎯 INTEGRACIÓN X5_ED ES FACTIBLE")
            print("Columnas necesarias están disponibles")
            
            # Mostrar muestra de datos
            if 'nombrado' in columnas_relevantes and 'contratado' in columnas_relevantes:
                col_nombrado = columnas_relevantes['nombrado']
                col_contratado = columnas_relevantes['contratado']
                
                print(f"\nMUESTRA DE DATOS DE ESTABILIDAD:")
                print(f"Nombrados:")
                print(df_sample[col_nombrado].describe())
                print(f"\nContratados:")
                print(df_sample[col_contratado].describe())
        else:
            print("\n❌ INTEGRACIÓN X5_ED NO FACTIBLE")
            print("Faltan columnas críticas")
        
        print("\n" + "="*80)
        print("SIGUIENTES PASOS:")
        
        if tiene_codigo and tiene_estabilidad:
            print("1. Usar columnas identificadas para integración")
            print("2. Implementar estrategia de vinculación múltiple")
            print("3. Completar variable X5_ED")
        else:
            print("1. Buscar archivos alternativos")
            print("2. Explorar otras fuentes de datos de estabilidad")
            print("3. Considerar proxies alternativos")
        
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    main()