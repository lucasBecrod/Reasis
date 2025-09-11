#!/usr/bin/env python3
"""
Explorar archivo de servicios educativos FyA RER 2025
Proyecto Reasis - Identificación de datos tipo de organización escolar (TOE)

Siguiendo metodología exitosa de CLAUDE.md:
1. Explorar archivos Excel
2. Comprender contenido
3. Analizar relevancia para X12_TOE
4. Identificar método de vinculación
"""

import pandas as pd
import sys

def main():
    print("=== EXPLORANDO ARCHIVO SERVICIOS EDUCATIVOS ===")
    
    # Archivo a analizar
    archivo = r"C:\Users\lucas\Proyectos\Reasis\assets\Consultoria\Información de referencia\Estadista IIEE Estudiantes RER FyA 2024 y 2025\Identificador_Servicios Educativos FyA RER 2025 (3).xlsx"
    
    print(f"Archivo: {archivo}")
    
    # 1. Explorar hojas disponibles
    print("\n1. Explorando hojas disponibles...")
    try:
        xl_file = pd.ExcelFile(archivo)
        print(f"   Hojas encontradas: {len(xl_file.sheet_names)}")
        for i, hoja in enumerate(xl_file.sheet_names, 1):
            print(f"   {i}. {hoja}")
    except Exception as e:
        print(f"   Error al abrir archivo: {e}")
        return
    
    # 2. Explorar cada hoja
    print("\n2. Analizando contenido de cada hoja...")
    
    for hoja in xl_file.sheet_names:
        print(f"\n--- HOJA: {hoja} ---")
        
        try:
            # Leer primeras filas para entender estructura
            df = pd.read_excel(archivo, sheet_name=hoja, nrows=10)
            
            print(f"   Dimensiones: {df.shape[0]} filas x {df.shape[1]} columnas")
            print(f"   Columnas: {list(df.columns)}")
            
            # Mostrar muestra de datos
            print("   Muestra de datos (primeras 5 filas):")
            if len(df) > 0:
                print(df.head().to_string(max_cols=8))
            else:
                print("   [Hoja vacía]")
                
        except Exception as e:
            print(f"   Error al leer hoja: {e}")
    
    # 3. Análisis más profundo de la hoja principal (asumir primera)
    print(f"\n3. Análisis detallado de hoja principal...")
    
    try:
        hoja_principal = xl_file.sheet_names[0]
        print(f"   Analizando: {hoja_principal}")
        
        # Cargar datos completos
        df_completo = pd.read_excel(archivo, sheet_name=hoja_principal)
        
        print(f"   Total registros: {len(df_completo)}")
        print(f"   Total columnas: {len(df_completo.columns)}")
        
        # Analizar columnas potencialmente útiles
        print("\n   Análisis de columnas relevantes:")
        
        columnas_interes = []
        for col in df_completo.columns:
            col_lower = str(col).lower()
            
            # Buscar columnas relacionadas con tipo de servicio/organización
            if any(keyword in col_lower for keyword in ['codigo', 'modular', 'ie', 'institucion']):
                print(f"     [ID] {col}: Potencial identificador")
                columnas_interes.append(col)
                
            elif any(keyword in col_lower for keyword in ['servicio', 'tipo', 'organiza', 'docente', 'multi', 'uni', 'poli']):
                print(f"     [TOE] {col}: Potencial tipo organización escolar")
                columnas_interes.append(col)
                
            elif any(keyword in col_lower for keyword in ['red', 'rer', 'fya']):
                print(f"     [RED] {col}: Información de red")
                columnas_interes.append(col)
        
        # 4. Mostrar valores únicos en columnas de interés
        print("\n4. Valores únicos en columnas de interés:")
        
        for col in columnas_interes[:8]:  # Limitar a primeras 8
            valores_unicos = df_completo[col].value_counts().head(10)
            print(f"\n   Columna: {col}")
            print(f"   Valores únicos: {df_completo[col].nunique()}")
            print("   Distribución (top 10):")
            print(valores_unicos.to_string())
        
        # 5. Buscar específicamente tipos de servicio educativo
        print("\n5. Búsqueda específica de tipos de servicio educativo:")
        
        for col in df_completo.columns:
            # Buscar en valores de la columna términos relacionados con TOE
            valores_col = df_completo[col].astype(str).str.lower()
            
            tiene_unidocente = valores_col.str.contains('unidocente', na=False).any()
            tiene_multigrado = valores_col.str.contains('multigrado', na=False).any()  
            tiene_polidocente = valores_col.str.contains('polidocente', na=False).any()
            
            if tiene_unidocente or tiene_multigrado or tiene_polidocente:
                print(f"   ¡ENCONTRADO! Columna: {col}")
                print(f"     Unidocente: {'Sí' if tiene_unidocente else 'No'}")
                print(f"     Multigrado: {'Sí' if tiene_multigrado else 'No'}")
                print(f"     Polidocente: {'Sí' if tiene_polidocente else 'No'}")
                
                # Mostrar distribución
                print("     Distribución:")
                print(df_completo[col].value_counts().to_string())
        
        # 6. Analizar potencial para vinculación
        print("\n6. Análisis para vinculación con BD:")
        
        for col in df_completo.columns:
            col_lower = str(col).lower()
            
            if 'codigo' in col_lower and 'modular' in col_lower:
                print(f"   CLAVE PRINCIPAL: {col}")
                # Verificar formato de códigos
                muestra_codigos = df_completo[col].dropna().head(10)
                print(f"   Muestra de códigos: {list(muestra_codigos)}")
                
                # Verificar si son numéricos
                try:
                    codigos_numericos = pd.to_numeric(df_completo[col], errors='coerce').dropna()
                    print(f"   Códigos numéricos válidos: {len(codigos_numericos)}/{len(df_completo)}")
                except:
                    print("   No se pudieron convertir a numéricos")
        
    except Exception as e:
        print(f"   Error en análisis detallado: {e}")
    
    print("\n=== EXPLORACIÓN COMPLETADA ===")
    print("\nSIGUIENTES PASOS RECOMENDADOS:")
    print("1. Identificar columna de tipo de servicio educativo")
    print("2. Verificar calidad de códigos modulares para vinculación")
    print("3. Analizar relevancia para variable X12_TOE del clustering")
    print("4. Implementar integración siguiendo metodología exitosa")

if __name__ == "__main__":
    main()