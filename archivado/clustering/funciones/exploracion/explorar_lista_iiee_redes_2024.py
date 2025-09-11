#!/usr/bin/env python3
"""
Explorar Lista de instituciones educativas Redes Rurales FyA 2024
Proyecto Reasis - Aplicando metodología exitosa CLAUDE.md

Objetivos:
1. Explorar estructura y datos disponibles (secciones, docentes, estudiantes 2023)
2. Validar consistencia asignaciones de redes vs nuestra BD
3. Identificar IIEE faltantes para enriquecer base principal
4. Planificar integración completa
"""

import pandas as pd
import sys

def main():
    print("=== EXPLORANDO LISTA IIEE REDES RURALES FyA 2024 ===")
    
    archivo = r"C:\Users\lucas\Proyectos\Reasis\assets\Consultoria\Información de referencia\Estadista IIEE Estudiantes RER FyA 2024 y 2025\Redes Rurales FyA - Lista de instituciones educativas (v25012024) v22022024 (2) (1).xlsx"
    
    print(f"Archivo: {archivo}")
    
    # 1. PASO 1 METODOLOGÍA: Explorar archivos Excel - Ver hojas
    print("\n1. EXPLORANDO HOJAS DISPONIBLES...")
    try:
        xl_file = pd.ExcelFile(archivo)
        print(f"   Hojas encontradas: {len(xl_file.sheet_names)}")
        for i, hoja in enumerate(xl_file.sheet_names, 1):
            print(f"   {i}. {hoja}")
    except Exception as e:
        print(f"   Error al abrir archivo: {e}")
        return
    
    # 2. PASO 2 METODOLOGÍA: Comprender contenido - Analizar cada hoja
    print("\n2. ANALIZANDO CONTENIDO DE CADA HOJA...")
    
    for hoja in xl_file.sheet_names:
        print(f"\n--- HOJA: {hoja} ---")
        
        try:
            # Leer muestra para entender estructura
            df_muestra = pd.read_excel(archivo, sheet_name=hoja, nrows=5)
            
            print(f"   Dimensiones muestra: {df_muestra.shape[0]} filas x {df_muestra.shape[1]} columnas")
            print(f"   Columnas: {list(df_muestra.columns)}")
            
            # Mostrar muestra de datos
            if len(df_muestra) > 0:
                print("   Muestra de datos:")
                print(df_muestra.to_string(max_cols=10))
            
            # Cargar datos completos para análisis
            df_completo = pd.read_excel(archivo, sheet_name=hoja)
            print(f"   Total registros: {len(df_completo)}")
            
        except Exception as e:
            print(f"   Error al leer hoja: {e}")
            continue
    
    # 3. ANÁLISIS DETALLADO DE DATOS RELEVANTES
    print("\n3. ANÁLISIS DETALLADO DE DATOS RELEVANTES...")
    
    # Analizar hoja principal (primera o más completa)
    try:
        hoja_principal = xl_file.sheet_names[0]  # Asumir primera hoja como principal
        print(f"\n   Analizando hoja principal: {hoja_principal}")
        
        df_principal = pd.read_excel(archivo, sheet_name=hoja_principal)
        print(f"   Total instituciones: {len(df_principal)}")
        
        # 4. IDENTIFICAR COLUMNAS DE INTERÉS
        print("\n4. IDENTIFICANDO COLUMNAS DE INTERÉS...")
        
        columnas_interes = {
            'identificadores': [],
            'datos_academicos_2023': [],
            'datos_personal': [],
            'datos_redes': [],
            'otros_relevantes': []
        }
        
        for col in df_principal.columns:
            col_lower = str(col).lower()
            
            # Identificadores
            if any(word in col_lower for word in ['codigo', 'modular', 'local', 'ie']):
                columnas_interes['identificadores'].append(col)
                print(f"     [ID] {col}")
                
            # Datos académicos 2023
            elif any(word in col_lower for word in ['estudiante', 'alumno', 'matricula', 'seccion', '2023']):
                columnas_interes['datos_academicos_2023'].append(col)
                print(f"     [ACAD2023] {col}")
                
            # Personal docente
            elif any(word in col_lower for word in ['docente', 'profesor', 'personal']):
                columnas_interes['datos_personal'].append(col)
                print(f"     [PERSONAL] {col}")
                
            # Información de redes
            elif any(word in col_lower for word in ['red', 'rer', 'fya']):
                columnas_interes['datos_redes'].append(col)
                print(f"     [RED] {col}")
                
            # Otros relevantes
            elif any(word in col_lower for word in ['nombre', 'region', 'distrito', 'nivel', 'modalidad']):
                columnas_interes['otros_relevantes'].append(col)
                print(f"     [INFO] {col}")
        
        # 5. ANÁLISIS DE DATOS ACADÉMICOS 2023
        print("\n5. ANÁLISIS DE DATOS ACADÉMICOS 2023...")
        
        datos_2023_disponibles = []
        for col in columnas_interes['datos_academicos_2023']:
            valores_no_vacios = df_principal[col].notna().sum()
            porcentaje = (valores_no_vacios / len(df_principal)) * 100
            
            print(f"   {col}: {valores_no_vacios}/{len(df_principal)} ({porcentaje:.1f}%)")
            
            if porcentaje > 50:  # Columnas con buena completitud
                datos_2023_disponibles.append(col)
                
                # Mostrar estadísticas básicas si es numérico
                try:
                    if df_principal[col].dtype in ['int64', 'float64']:
                        stats = df_principal[col].describe()
                        print(f"     Min: {stats['min']:.0f}, Max: {stats['max']:.0f}, Promedio: {stats['mean']:.1f}")
                except:
                    pass
        
        # 6. ANÁLISIS DE CÓDIGOS PARA VINCULACIÓN
        print("\n6. ANÁLISIS DE CÓDIGOS PARA VINCULACIÓN...")
        
        columna_codigo_principal = None
        for col in columnas_interes['identificadores']:
            if 'modular' in col.lower():
                columna_codigo_principal = col
                break
        
        if columna_codigo_principal:
            print(f"   Columna código principal: {columna_codigo_principal}")
            
            # Verificar calidad de códigos
            codigos_validos = df_principal[columna_codigo_principal].notna().sum()
            print(f"   Códigos válidos: {codigos_validos}/{len(df_principal)} ({codigos_validos/len(df_principal)*100:.1f}%)")
            
            # Muestra de códigos
            muestra_codigos = df_principal[columna_codigo_principal].dropna().head(10).tolist()
            print(f"   Muestra códigos: {muestra_codigos}")
            
            # Verificar formato numérico
            try:
                codigos_numericos = pd.to_numeric(df_principal[columna_codigo_principal], errors='coerce').notna().sum()
                print(f"   Códigos convertibles a numérico: {codigos_numericos}/{codigos_validos}")
            except:
                print("   Error al verificar formato numérico")
        
        # 7. ANÁLISIS DE REDES
        print("\n7. ANÁLISIS DE ASIGNACIONES DE REDES...")
        
        for col in columnas_interes['datos_redes']:
            print(f"\n   Columna: {col}")
            distribucion_redes = df_principal[col].value_counts().head(10)
            print("   Distribución (top 10):")
            print(distribucion_redes.to_string())
        
        # 8. IDENTIFICAR REDES DEL ESTUDIO
        print("\n8. IDENTIFICANDO REDES DEL ESTUDIO (44, 47, 48, 54, 72, 79)...")
        
        redes_estudio = ['44', '47', '48', '54', '72', '79']
        instituciones_estudio = 0
        
        for col in columnas_interes['datos_redes']:
            for red in redes_estudio:
                # Buscar instituciones que contengan el número de red
                mask = df_principal[col].astype(str).str.contains(red, na=False)
                count_red = mask.sum()
                
                if count_red > 0:
                    print(f"   Red {red} en columna {col}: {count_red} instituciones")
                    instituciones_estudio += count_red
        
        print(f"   Total instituciones potenciales del estudio: {instituciones_estudio}")
        
    except Exception as e:
        print(f"   Error en análisis detallado: {e}")
    
    # 9. PLAN DE INTEGRACIÓN
    print("\n9. PLAN DE INTEGRACIÓN PROPUESTO...")
    
    print("\n   FASE 1: VALIDACIÓN DE CONSISTENCIA")
    print("   - Comparar asignaciones de redes entre archivo y BD actual")
    print("   - Identificar discrepancias en clasificación de IIEE por red")
    print("   - Validar códigos modulares para vinculación")
    
    print("\n   FASE 2: ENRIQUECIMIENTO DE DATOS")
    print("   - Integrar datos académicos 2023 (estudiantes, secciones)")
    print("   - Actualizar información de personal docente")
    print("   - Agregar metadatos de instituciones")
    
    print("\n   FASE 3: EXPANSIÓN DE BASE")
    print("   - Identificar IIEE faltantes en nuestra BD principal")
    print("   - Agregar instituciones Fe y Alegría no catalogadas")
    print("   - Robustecer cobertura de redes del estudio")
    
    print("\n   FASE 4: CONSOLIDACIÓN FINAL")
    print("   - Crear tabla integrada con datos 2023")
    print("   - Validar integridad y consistencia")
    print("   - Generar reporte de mejoras en variables metodológicas")
    
    print("\n=== EXPLORACIÓN COMPLETADA ===")
    print("\nSIGUIENTES PASOS:")
    print("1. Ejecutar análisis detallado de datos 2023")
    print("2. Implementar validación cruzada con BD actual")
    print("3. Crear integrador siguiendo metodología CLAUDE.md")
    print("4. Robustecer base de datos principal")

if __name__ == "__main__":
    main()