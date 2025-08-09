#!/usr/bin/env python3
import pandas as pd

def analizar_errores():
    """Analiza los errores encontrados durante la exploración del archivo EIB"""
    
    print("=== ANÁLISIS DE ERRORES DURANTE EXPLORACIÓN EIB ===\n")
    
    archivo = r"C:\Users\lucas\Proyectos\Reasis\assets\Consultoria\Información actualizada\Extras\RIIEE EIB 2024 Minedu.xlsx"
    
    try:
        df = pd.read_excel(archivo, sheet_name='Sheet1')
        print("Archivo cargado exitosamente\n")
        
        # ERROR 1: Problemas de codificación Unicode
        print("ERROR 1: CODIFICACIÓN UNICODE")
        print("Problema: UnicodeEncodeError al usar emojis en print()")
        print("Causa: Terminal Windows (cmd) usa codificación cp1252 que no soporta emojis Unicode")
        print("Solución aplicada: Reemplazar emojis con texto [OK], [NO], [ERROR]")
        print("Lección: Evitar caracteres Unicode complejos en output de terminal\n")
        
        # ERROR 2: Nombres de columnas inconsistentes
        print("ERROR 2: NOMBRES DE COLUMNAS INCONSISTENTES")
        print("Problema: Código asumía nombres de columnas que no coincidían con el archivo real")
        cols_problema = ['cod_mod', 'fa_2024b', 'ruralidad', 'quintil_pobreza']
        cols_reales = ['Código modular', 'Forma de atención EIB', 'Tipo de Ruralidad', 'Quintil de pobreza']
        
        for i, (problema, real) in enumerate(zip(cols_problema, cols_reales)):
            print(f"  - Asumido: '{problema}' | Real: '{real}'")
        
        print("Causa: No revisar estructura real del archivo antes de programar")
        print("Solución aplicada: Inspección manual de columnas y actualización de nombres")
        print("Lección: SIEMPRE hacer df.columns first para ver nombres reales\n")
        
        # ERROR 3: Tipos de datos inconsistentes
        print("ERROR 3: TIPOS DE DATOS INCONSISTENTES")
        print("Problema: Error \"'<' not supported between instances of 'str' and 'int'\"")
        print("Identificando el problema...")
        
        # Verificar tipos en quintil de pobreza
        if 'Quintil de pobreza' in df.columns:
            valores_unicos = df['Quintil de pobreza'].unique()
            tipos = [type(x).__name__ for x in valores_unicos[:5]]
            print(f"  - Valores únicos en 'Quintil de pobreza': {valores_unicos[:10]}")
            print(f"  - Tipos de datos: {tipos}")
            
            # Verificar si hay valores no numéricos
            valores_no_numericos = df['Quintil de pobreza'][~pd.to_numeric(df['Quintil de pobreza'], errors='coerce').notna()]
            if len(valores_no_numericos) > 0:
                print(f"  - Valores no numéricos encontrados: {valores_no_numericos.unique()}")
        
        print("Causa: Mezcla de tipos de datos (int, str, NaN) en columnas numéricas")
        print("Solución: Usar pd.to_numeric() con errors='coerce' antes de sort_index()")
        print("Lección: Validar tipos de datos antes de operaciones de comparación/ordenamiento\n")
        
        # ERROR 4: Contextos especiales con tipos de datos incorrectos
        print("ERROR 4: CONTEXTOS ESPECIALES - TIPOS INCORRECTOS")
        contextos = ['La IE se encuentra en un distrito frontera', 
                    'La IE se encuentra en un distrito vraem',
                    'La IE se encuentra en un distrito minero ilegal']
        
        for contexto in contextos:
            if contexto in df.columns:
                valores = df[contexto].unique()
                print(f"  - '{contexto}': {valores}")
        
        print("Problema: Asumimos que serían valores binarios (0/1) pero podrían ser texto")
        print("Causa: No verificar el formato real de las variables booleanas")
        print("Solución: Convertir 'Sí'/'No' a 1/0 antes de sum()")
        print("Lección: Variables booleanas pueden tener múltiples formatos\n")
        
        # ERROR 5: KeyError por descripcion vs descripción
        print("ERROR 5: TYPO EN DICCIONARIOS")
        print("Problema: KeyError: 'descripcion'")
        print("Causa: Inconsistencia entre 'descripcion' y 'descripción' (con tilde)")
        print("Solución aplicada: Estandarizar sin tildes en claves de diccionarios")
        print("Lección: Mantener consistencia en naming conventions, preferir sin caracteres especiales\n")
        
    except Exception as e:
        print(f"Error en análisis: {e}")

if __name__ == "__main__":
    analizar_errores()