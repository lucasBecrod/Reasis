#!/usr/bin/env python3
"""
Script para analizar si existen datos históricos en las bases de datos disponibles
"""

from dbfread import DBF
import pandas as pd
import re

def analizar_archivo_dbf(nombre_archivo, descripcion):
    """Analiza un archivo DBF para identificar datos históricos"""
    
    print(f"\n=== ANALIZANDO {descripcion.upper()} ===")
    ruta_archivo = f'data/bases_de_datos/Padron_web_20250731/{nombre_archivo}'
    
    try:
        # Leer archivo DBF
        table = DBF(ruta_archivo, encoding='latin-1')
        records = []
        for i, record in enumerate(table):
            records.append(dict(record))
            if i >= 100:  # Muestra de 100 registros para análisis
                break
        
        if not records:
            print(f"  Archivo vacío: {nombre_archivo}")
            return
        
        df = pd.DataFrame(records)
        
        print(f"  Registros: {len(df)}")
        print(f"  Columnas: {len(df.columns)}")
        
        # Buscar columnas que indiquen datos históricos o temporales
        columnas_temporales = []
        columnas_numericas_anos = []
        
        for col in df.columns:
            col_upper = col.upper()
            
            # Buscar patrones de años (2004-2024)
            if re.search(r'20[0-2][0-9]', col):
                columnas_numericas_anos.append(col)
            
            # Buscar palabras clave temporales
            elif any(keyword in col_upper for keyword in ['HIST', 'ANIO', 'AÑO', 'YEAR', 'PERIODO', 'FECHA']):
                columnas_temporales.append(col)
        
        if columnas_numericas_anos:
            print(f"  ✓ Columnas con años encontradas ({len(columnas_numericas_anos)}):")
            for col in columnas_numericas_anos[:10]:  # Mostrar primeras 10
                print(f"    {col}")
            if len(columnas_numericas_anos) > 10:
                print(f"    ... y {len(columnas_numericas_anos)-10} más")
        
        if columnas_temporales:
            print(f"  ✓ Columnas temporales encontradas ({len(columnas_temporales)}):")
            for col in columnas_temporales:
                print(f"    {col}")
        
        # Buscar columnas relacionadas con estudiantes, docentes, secciones
        columnas_academicas = []
        for col in df.columns:
            col_upper = col.upper()
            if any(keyword in col_upper for keyword in ['ALUM', 'ESTUD', 'MATRIC', 'DOC', 'PROF', 'SECC', 'AULA']):
                columnas_academicas.append(col)
        
        if columnas_academicas:
            print(f"  ✓ Columnas académicas encontradas ({len(columnas_academicas)}):")
            for col in columnas_academicas[:10]:
                print(f"    {col}")
            if len(columnas_academicas) > 10:
                print(f"    ... y {len(columnas_academicas)-10} más")
        
        # Mostrar muestra de datos si hay columnas relevantes
        if columnas_numericas_anos or columnas_temporales or columnas_academicas:
            print(f"  \n  MUESTRA DE DATOS:")
            columnas_interes = (columnas_numericas_anos[:3] + 
                              columnas_temporales[:3] + 
                              columnas_academicas[:3])
            
            if 'COD_MOD' in df.columns:
                columnas_interes = ['COD_MOD'] + columnas_interes
            elif 'CODMOD' in df.columns:
                columnas_interes = ['CODMOD'] + columnas_interes
            
            if columnas_interes:
                muestra = df[columnas_interes].head(3)
                for _, row in muestra.iterrows():
                    print(f"    {dict(row)}")
        
        if not (columnas_numericas_anos or columnas_temporales or columnas_academicas):
            print(f"  ✗ No se encontraron datos históricos evidentes")
            print(f"  Columnas disponibles (primeras 10):")
            for col in df.columns[:10]:
                print(f"    {col}")
        
        return {
            'archivo': nombre_archivo,
            'registros': len(df),
            'columnas_anos': columnas_numericas_anos,
            'columnas_temporales': columnas_temporales,
            'columnas_academicas': columnas_academicas,
            'tiene_datos_historicos': bool(columnas_numericas_anos or columnas_temporales)
        }
        
    except Exception as e:
        print(f"  ✗ Error procesando {nombre_archivo}: {e}")
        return None

def buscar_datos_historicos_codigo(codigo_modular):
    """Busca datos históricos específicos para un código modular"""
    
    print(f"\n=== BUSCANDO DATOS HISTÓRICOS PARA {codigo_modular} ===")
    
    archivos = [
        ('Padron_web.dbf', 'Padrón Principal'),
        ('Padlocaladi_web.dbf', 'Datos Locales Adicionales'),
        ('Instituciones_apoyo.dbf', 'Instituciones de Apoyo')
    ]
    
    for nombre_archivo, descripcion in archivos:
        ruta_archivo = f'data/bases_de_datos/Padron_web_20250731/{nombre_archivo}'
        
        try:
            table = DBF(ruta_archivo, encoding='latin-1')
            
            for record in table:
                record_dict = dict(record)
                
                # Buscar por diferentes campos de código
                codigo_encontrado = False
                if 'COD_MOD' in record_dict and str(record_dict['COD_MOD']) == codigo_modular:
                    codigo_encontrado = True
                elif 'CODMOD' in record_dict and str(record_dict['CODMOD']) == codigo_modular:
                    codigo_encontrado = True
                
                if codigo_encontrado:
                    print(f"  ✓ Encontrado en {descripcion}")
                    
                    # Mostrar campos que podrían ser históricos
                    campos_historicos = {}
                    for campo, valor in record_dict.items():
                        if (re.search(r'20[0-2][0-9]', campo) or 
                            any(kw in campo.upper() for kw in ['HIST', 'ANIO', 'AÑO']) or
                            any(kw in campo.upper() for kw in ['ALUM', 'DOC', 'SECC'])):
                            campos_historicos[campo] = valor
                    
                    if campos_historicos:
                        print(f"    Campos históricos/académicos:")
                        for campo, valor in list(campos_historicos.items())[:10]:
                            print(f"      {campo}: {valor}")
                    else:
                        print(f"    No se encontraron campos históricos específicos")
                    
                    break
            else:
                print(f"  ✗ No encontrado en {descripcion}")
                
        except Exception as e:
            print(f"  ✗ Error en {nombre_archivo}: {e}")

def main():
    """Función principal para analizar datos históricos"""
    
    print("=== ANÁLISIS DE DATOS HISTÓRICOS EN BASES MINEDU ===")
    
    # Analizar cada archivo DBF
    archivos_analisis = [
        ('Padron_web.dbf', 'Padrón Principal'),
        ('Padlocaladi_web.dbf', 'Datos Locales Adicionales'), 
        ('Instituciones_apoyo.dbf', 'Instituciones de Apoyo')
    ]
    
    resultados = []
    
    for nombre_archivo, descripcion in archivos_analisis:
        resultado = analizar_archivo_dbf(nombre_archivo, descripcion)
        if resultado:
            resultados.append(resultado)
    
    # Resumen de hallazgos
    print(f"\n{'='*80}")
    print(f"RESUMEN DE HALLAZGOS")
    print(f"{'='*80}")
    
    archivos_con_historicos = [r for r in resultados if r['tiene_datos_historicos']]
    
    if archivos_con_historicos:
        print(f"✓ {len(archivos_con_historicos)} archivo(s) con datos históricos potenciales:")
        for r in archivos_con_historicos:
            print(f"  - {r['archivo']}: {len(r['columnas_anos'])} cols. años, {len(r['columnas_academicas'])} cols. académicas")
    else:
        print(f"✗ No se encontraron datos históricos evidentes en los archivos DBF")
        print(f"  Esto sugiere que los datos históricos de ESCALE requieren:")
        print(f"  1. Web scraping de las fichas individuales")
        print(f"  2. Acceso a APIs no públicas del MINEDU")
        print(f"  3. Otros archivos/bases de datos no incluidos")
    
    # Buscar datos específicos para una institución de ejemplo
    print(f"\n" + "="*80)
    print(f"BÚSQUEDA ESPECÍFICA DE EJEMPLO")
    print(f"="*80)
    
    codigo_ejemplo = "0600692"  # Una de nuestras instituciones
    buscar_datos_historicos_codigo(codigo_ejemplo)
    
    return archivos_con_historicos

if __name__ == "__main__":
    main()