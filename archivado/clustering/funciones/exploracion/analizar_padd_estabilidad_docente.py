#!/usr/bin/env python3
"""
Análisis específico de datos PADD para estabilidad docente
Proyecto Reasis - Análisis detallado de "Cargo / Carrera" para variable X5_ED

Objetivo: Extraer información sobre estabilidad laboral docente de archivos PADD
Archivo fuente: "Información actualizada/2. PADD Consolidado.xlsx"
Variable objetivo: X5_ED (Nombrados vs Contratados)
"""

import pandas as pd
import sqlite3

def analizar_cargos_docentes(df, año):
    """Analiza columna Cargo/Carrera para identificar tipos de estabilidad"""
    
    print(f"\n   ANÁLISIS DETALLADO DE CARGOS {año}:")
    
    if 'Cargo / Carrera' not in df.columns:
        print("     [ERROR] No se encuentra columna 'Cargo / Carrera'")
        return {}
    
    # Obtener todos los valores únicos de cargo
    cargos_unicos = df['Cargo / Carrera'].value_counts()
    print(f"     Total registros: {len(df)}")
    print(f"     Tipos de cargo diferentes: {len(cargos_unicos)}")
    
    print("\n     DISTRIBUCIÓN COMPLETA DE CARGOS:")
    for cargo, cantidad in cargos_unicos.items():
        print(f"       {cargo}: {cantidad}")
    
    # Intentar clasificar por estabilidad laboral
    nombrados_patterns = ['nombrado', 'titular', 'permanente', 'estable']
    contratados_patterns = ['contratado', 'temporal', 'suplente', 'interino']
    
    clasificacion = {
        'posible_nombrado': [],
        'posible_contratado': [],
        'indeterminado': []
    }
    
    for cargo in cargos_unicos.index:
        cargo_lower = str(cargo).lower()
        
        es_nombrado = any(pattern in cargo_lower for pattern in nombrados_patterns)
        es_contratado = any(pattern in cargo_lower for pattern in contratados_patterns)
        
        if es_nombrado and not es_contratado:
            clasificacion['posible_nombrado'].append(cargo)
        elif es_contratado and not es_nombrado:
            clasificacion['posible_contratado'].append(cargo)
        else:
            clasificacion['indeterminado'].append(cargo)
    
    print(f"\n     CLASIFICACIÓN POR PATRONES:")
    print(f"       Posibles nombrados: {clasificacion['posible_nombrado']}")
    print(f"       Posibles contratados: {clasificacion['posible_contratado']}")
    print(f"       Indeterminados: {clasificacion['indeterminado']}")
    
    return clasificacion

def buscar_otras_columnas_estabilidad(df, año):
    """Busca otras columnas que puedan contener información de estabilidad"""
    
    print(f"\n   BÚSQUEDA DE OTRAS COLUMNAS RELACIONADAS {año}:")
    
    terminos_busqueda = [
        'nombr', 'contrat', 'estabil', 'permanente', 'temporal',
        'situacion', 'condicion', 'regimen', 'modalidad', 'tipo'
    ]
    
    columnas_encontradas = []
    
    for col in df.columns:
        col_lower = str(col).lower()
        for termino in terminos_busqueda:
            if termino in col_lower:
                columnas_encontradas.append(col)
                break
    
    if columnas_encontradas:
        print(f"     Columnas potencialmente relevantes: {columnas_encontradas}")
        
        for col in columnas_encontradas[:5]:  # Limitar a 5 primeras
            valores_unicos = df[col].value_counts().head(10)
            print(f"       {col}:")
            for valor, cantidad in valores_unicos.items():
                print(f"         {valor}: {cantidad}")
    else:
        print("     [NO ENCONTRADO] Sin columnas adicionales relevantes")
    
    return columnas_encontradas

def main():
    print("=== ANÁLISIS PADD PARA ESTABILIDAD DOCENTE ===")
    
    archivo = r"C:\Users\lucas\Proyectos\Reasis\assets\Consultoria\Información actualizada\2. PADD Consolidado.xlsx"
    
    try:
        xl_file = pd.ExcelFile(archivo)
        print(f"Hojas disponibles: {xl_file.sheet_names}")
        
        resultados_analisis = {}
        
        # Analizar cada hoja (2023 y 2024)
        for hoja in xl_file.sheet_names:
            print(f"\n=== ANALIZANDO HOJA: {hoja} ===")
            
            try:
                df = pd.read_excel(archivo, sheet_name=hoja)
                print(f"   Registros cargados: {len(df)}")
                print(f"   Columnas disponibles: {len(df.columns)}")
                
                # Mostrar muestra de columnas
                print(f"   Primeras columnas: {list(df.columns[:10])}")
                
                # Analizar cargos para estabilidad
                clasificacion_cargos = analizar_cargos_docentes(df, hoja)
                
                # Buscar otras columnas relevantes  
                otras_columnas = buscar_otras_columnas_estabilidad(df, hoja)
                
                # Verificar si hay códigos modulares para vinculación
                columnas_codigo = [col for col in df.columns if 'codigo' in str(col).lower() or 'modular' in str(col).lower()]
                if columnas_codigo:
                    print(f"\n   COLUMNAS PARA VINCULACIÓN: {columnas_codigo}")
                    
                    for col_codigo in columnas_codigo:
                        codigos_validos = df[col_codigo].notna().sum()
                        print(f"     {col_codigo}: {codigos_validos}/{len(df)} ({codigos_validos/len(df)*100:.1f}%)")
                        
                        if codigos_validos > 0:
                            muestra_codigos = df[col_codigo].dropna().head(5).tolist()
                            print(f"       Muestra: {muestra_codigos}")
                
                resultados_analisis[hoja] = {
                    'registros': len(df),
                    'clasificacion_cargos': clasificacion_cargos,
                    'otras_columnas': otras_columnas,
                    'columnas_codigo': columnas_codigo
                }
                
            except Exception as e:
                print(f"   Error procesando hoja {hoja}: {e}")
        
        # ANÁLISIS CONSOLIDADO
        print(f"\n=== ANÁLISIS CONSOLIDADO ===")
        
        total_registros = sum(r['registros'] for r in resultados_analisis.values())
        print(f"Total registros PADD: {total_registros}")
        
        # Verificar potencial para X5_ED
        potencial_x5_ed = False
        for hoja, resultado in resultados_analisis.items():
            clasificacion = resultado['clasificacion_cargos']
            if clasificacion.get('posible_nombrado') or clasificacion.get('posible_contratado'):
                potencial_x5_ed = True
                print(f"\n[POTENCIAL X5_ED] Hoja {hoja} contiene clasificaciones de estabilidad")
        
        if not potencial_x5_ed:
            print("\n[ANÁLISIS] No se encontraron patrones claros de nombrado vs contratado")
            print("RECOMENDACIÓN: Explorar otros archivos o considerar crear categorías basadas en:")
            print("- Tipo de cargo (Director, Docente de aula, etc.)")
            print("- Permanencia en la institución")
            print("- Modalidad de contratación indirecta")
        
        # PLAN DE INTEGRACIÓN
        print(f"\n=== PLAN DE INTEGRACIÓN PROPUESTO ===")
        
        if potencial_x5_ed:
            print("FASE 1: Clasificación manual de cargos")
            print("- Crear mapeo de cargos a categorías de estabilidad")
            print("- Validar clasificación con experto en recursos humanos")
            
            print("\nFASE 2: Integración con BD principal")
            print("- Vincular por código modular o nombre de docente")
            print("- Crear tabla auxiliar con datos de estabilidad")
            
            print("\nFASE 3: Completar variable X5_ED")
            print("- Generar indicador de estabilidad por institución")
            print("- Calcular ratio nombrados/contratados por IIEE")
        else:
            print("ALTERNATIVA: Explorar otros archivos del directorio")
            print("- Archivo de servicios educativos")
            print("- Registros EIB que pueden contener información laboral")
            print("- Datos ESCALE si están disponibles")
        
        print(f"\nRESULTADO: Variable X5_ED {'FACTIBLE' if potencial_x5_ed else 'REQUIERE EXPLORACIÓN ADICIONAL'}")
        
    except Exception as e:
        print(f"Error general: {e}")

if __name__ == "__main__":
    main()