#!/usr/bin/env python3
"""
Script para explorar los datos de matrícula SIAGIE (2019-2024)
"""

from dbfread import DBF
import pandas as pd
import os

def analizar_archivo_siagie(año):
    """Analiza un archivo SIAGIE específico"""
    
    archivo = f'data/bases_de_datos/siagie/SIAGIE Reporte Matricula {año}.dbf'
    
    print(f"\n=== SIAGIE {año} ===")
    
    try:
        # Leer archivo DBF
        table = DBF(archivo, encoding='latin-1')
        
        # Convertir muestra a DataFrame para análisis
        records = []
        for i, record in enumerate(table):
            records.append(dict(record))
            if i >= 1000:  # Muestra de 1000 registros para análisis rápido
                break
        
        if not records:
            print(f"  ✗ Archivo vacío: {año}")
            return None
        
        df = pd.DataFrame(records)
        
        # Contar registros totales (reabrir para conteo completo si es necesario)
        table_count = DBF(archivo, encoding='latin-1')
        total_registros = sum(1 for _ in table_count)
        
        print(f"  Total registros: {total_registros:,}")
        print(f"  Columnas: {len(df.columns)}")
        
        # Mostrar estructura de columnas
        print(f"  \n  Columnas disponibles:")
        for i, col in enumerate(df.columns):
            if i % 6 == 0:
                print()
            print(f"    {col:15}", end=" ")
        print()
        
        # Buscar nuestras instituciones específicas
        codigos_buscar = ['0600692', '1768829', '0481093', '0488403', '0304642', '0428714', '3025715', '2533906', '1781897']
        
        # Determinar columna de código modular
        col_codigo = None
        for col in df.columns:
            if any(keyword in col.upper() for keyword in ['COD_MOD', 'CODMOD', 'MODULAR']):
                col_codigo = col
                break
        
        if col_codigo:
            df[col_codigo] = df[col_codigo].astype(str)
            encontradas = df[df[col_codigo].isin(codigos_buscar)]
            
            print(f"\n  Nuestras instituciones encontradas: {len(encontradas)}/{len(codigos_buscar)}")
            
            if len(encontradas) > 0:
                print(f"  Códigos encontrados:")
                for codigo in encontradas[col_codigo].unique():
                    registros_codigo = len(encontradas[encontradas[col_codigo] == codigo])
                    print(f"    {codigo}: {registros_codigo} registros")
        
        # Identificar campos importantes
        campos_importantes = {}
        
        for col in df.columns:
            col_upper = col.upper()
            if any(keyword in col_upper for keyword in ['MATRIC', 'ESTUD', 'ALUM']):
                campos_importantes['matricula'] = col
            elif any(keyword in col_upper for keyword in ['GRADO', 'GRAD']):
                campos_importantes['grado'] = col
            elif any(keyword in col_upper for keyword in ['NIVEL', 'NIV']):
                campos_importantes['nivel'] = col
            elif any(keyword in col_upper for keyword in ['SECC', 'SECTION']):
                campos_importantes['seccion'] = col
            elif any(keyword in col_upper for keyword in ['SEXO', 'GENERO']):
                campos_importantes['sexo'] = col
            elif any(keyword in col_upper for keyword in ['EDAD']):
                campos_importantes['edad'] = col
        
        if campos_importantes:
            print(f"\n  Campos importantes identificados:")
            for tipo, columna in campos_importantes.items():
                valores_unicos = df[columna].nunique()
                print(f"    {tipo.capitalize()}: {columna} ({valores_unicos} valores únicos)")
        
        # Muestra de datos
        print(f"\n  Muestra de datos (primeras 3 filas):")
        columnas_muestra = list(df.columns[:8])  # Primeras 8 columnas
        for i, (_, row) in enumerate(df.head(3).iterrows()):
            print(f"    Fila {i+1}:")
            for col in columnas_muestra:
                valor = row[col]
                if len(str(valor)) > 20:
                    valor = str(valor)[:17] + "..."
                print(f"      {col}: {valor}")
            print()
        
        return {
            'año': año,
            'total_registros': total_registros,
            'columnas': len(df.columns),
            'campos_importantes': campos_importantes,
            'nuestras_instituciones': len(encontradas) if col_codigo else 0,
            'columna_codigo': col_codigo
        }
        
    except Exception as e:
        print(f"  ✗ Error procesando {año}: {e}")
        return None

def resumen_siagie():
    """Genera un resumen de todos los años SIAGIE"""
    
    print("=" * 80)
    print("EXPLORACIÓN COMPLETA DATOS SIAGIE 2019-2024")
    print("=" * 80)
    
    años = [2019, 2020, 2021, 2022, 2023, 2024]
    resultados = []
    
    for año in años:
        resultado = analizar_archivo_siagie(año)
        if resultado:
            resultados.append(resultado)
    
    # Resumen final
    print("\n" + "=" * 80)
    print("RESUMEN COMPARATIVO")
    print("=" * 80)
    
    print(f"\nDatos disponibles por año:")
    print(f"{'Año':<6} {'Registros':<12} {'Columnas':<10} {'Nuestras IIEE':<15} {'Col. Código':<15}")
    print("-" * 70)
    
    for res in resultados:
        print(f"{res['año']:<6} {res['total_registros']:,<12} {res['columnas']:<10} "
              f"{res['nuestras_instituciones']:<15} {res['columna_codigo'] or 'No encontrada':<15}")
    
    # Estadísticas generales
    total_registros = sum(res['total_registros'] for res in resultados)
    print(f"\nTotal registros históricos: {total_registros:,}")
    print(f"Años disponibles: {len(resultados)}")
    
    # Identificar campos comunes
    if resultados:
        print(f"\nCampos importantes encontrados:")
        campos_todos = {}
        for res in resultados:
            for tipo, campo in res['campos_importantes'].items():
                if tipo not in campos_todos:
                    campos_todos[tipo] = []
                campos_todos[tipo].append(f"{res['año']}: {campo}")
        
        for tipo, campos in campos_todos.items():
            print(f"  {tipo.capitalize()}:")
            for campo in campos:
                print(f"    {campo}")
    
    return resultados

def analizar_nuestras_instituciones():
    """Analiza específicamente las 9 instituciones en todos los años"""
    
    print("\n" + "=" * 80)
    print("ANÁLISIS ESPECÍFICO - NUESTRAS 9 INSTITUCIONES")
    print("=" * 80)
    
    codigos = ['0600692', '1768829', '0481093', '0488403', '0304642', '0428714', '3025715', '2533906', '1781897']
    años = [2019, 2020, 2021, 2022, 2023, 2024]
    
    resumen_instituciones = {}
    
    for año in años:
        archivo = f'data/bases_de_datos/siagie/SIAGIE Reporte Matricula {año}.dbf'
        
        try:
            table = DBF(archivo, encoding='latin-1')
            records = []
            
            # Leer registros y buscar nuestros códigos
            for record in table:
                record_dict = dict(record)
                
                # Buscar columna de código
                codigo_encontrado = None
                for key, value in record_dict.items():
                    if any(keyword in key.upper() for keyword in ['COD_MOD', 'CODMOD', 'MODULAR']):
                        if str(value) in codigos:
                            codigo_encontrado = str(value)
                            break
                
                if codigo_encontrado:
                    records.append({
                        'año': año,
                        'codigo': codigo_encontrado,
                        'registro_completo': record_dict
                    })
            
            print(f"\n{año}: {len(records)} registros de nuestras instituciones")
            
            if records:
                # Agrupar por código
                por_codigo = {}
                for record in records:
                    codigo = record['codigo']
                    if codigo not in por_codigo:
                        por_codigo[codigo] = []
                    por_codigo[codigo].append(record)
                
                for codigo, regs in por_codigo.items():
                    if codigo not in resumen_instituciones:
                        resumen_instituciones[codigo] = {}
                    resumen_instituciones[codigo][año] = len(regs)
                    print(f"  {codigo}: {len(regs)} registros")
        
        except Exception as e:
            print(f"  Error en {año}: {e}")
    
    # Resumen histórico por institución
    if resumen_instituciones:
        print(f"\n=== RESUMEN HISTÓRICO POR INSTITUCIÓN ===")
        print(f"{'Código':<10} " + " ".join([f"{año}" for año in años]))
        print("-" * 50)
        
        for codigo in sorted(resumen_instituciones.keys()):
            fila = f"{codigo:<10} "
            for año in años:
                count = resumen_instituciones[codigo].get(año, 0)
                fila += f"{count:>6} "
            print(fila)
    
    return resumen_instituciones

def main():
    """Función principal"""
    resultados = resumen_siagie()
    instituciones = analizar_nuestras_instituciones()
    
    print("\n" + "=" * 80)
    print("CONCLUSIONES Y RECOMENDACIONES")
    print("=" * 80)
    
    if resultados:
        print("\n✅ DATOS SIAGIE DISPONIBLES:")
        print(f"  • {len(resultados)} años de datos (2019-2024)")
        total = sum(res['total_registros'] for res in resultados)
        print(f"  • {total:,} registros totales de matrícula")
        print(f"  • Datos a nivel de estudiante individual")
        
        print("\n📊 DATOS ÚTILES PARA REASIS:")
        print(f"  • Matrícula histórica por institución")
        print(f"  • Distribución por grado y nivel")
        print(f"  • Datos por sexo y edad")
        print(f"  • Series históricas 2019-2024")
        
        print("\n🎯 VENTAJAS vs WEB SCRAPING:")
        print(f"  • Datos oficiales estructurados")
        print(f"  • 6 años de historia disponible")
        print(f"  • Formato DBF fácil de procesar")
        print(f"  • Datos detallados (nivel estudiante)")
        
    else:
        print("\n❌ No se pudieron procesar los archivos SIAGIE")

if __name__ == "__main__":
    main()