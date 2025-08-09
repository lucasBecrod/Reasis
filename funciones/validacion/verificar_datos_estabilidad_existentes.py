#!/usr/bin/env python3
"""
Verificador de datos de estabilidad docente existentes
Proyecto Reasis - Búsqueda en tablas actuales de la BD

Objetivo: Revisar si ya tenemos información de estabilidad docente en las tablas existentes
"""

import pandas as pd
import sqlite3

def main():
    print("=== VERIFICACIÓN DE DATOS DE ESTABILIDAD EXISTENTES ===")
    
    conn = sqlite3.connect('reasis_database.db')
    
    # 1. Listar todas las tablas
    print("1. TABLAS DISPONIBLES EN LA BASE DE DATOS:")
    
    tablas = pd.read_sql_query("""
        SELECT name FROM sqlite_master WHERE type='table' ORDER BY name
    """, conn)
    
    for tabla in tablas['name']:
        print(f"   - {tabla}")
    
    # 2. Buscar en tabla EIB MINEDU si existe
    print("\n2. VERIFICANDO TABLA EIB MINEDU...")
    
    try:
        df_eib = pd.read_sql_query("SELECT * FROM datos_eib_minedu LIMIT 1", conn)
        columnas_eib = df_eib.columns.tolist()
        print(f"   Columnas en datos_eib_minedu: {len(columnas_eib)}")
        
        # Buscar columnas relacionadas con docentes/personal
        columnas_docentes = [col for col in columnas_eib if any(word in str(col).lower() for word in ['docente', 'profesor', 'personal', 'nombr', 'contrat'])]
        
        if columnas_docentes:
            print(f"   [ENCONTRADO] Columnas potenciales: {columnas_docentes}")
            
            # Obtener datos completos
            df_eib_completo = pd.read_sql_query("SELECT * FROM datos_eib_minedu", conn)
            
            for col in columnas_docentes:
                valores_unicos = df_eib_completo[col].value_counts()
                print(f"     {col}:")
                for valor, cantidad in valores_unicos.head(10).items():
                    print(f"       {valor}: {cantidad}")
                    
        else:
            print("   [NO ENCONTRADO] Sin columnas relacionadas con estabilidad docente")
            
    except Exception as e:
        print(f"   Tabla EIB no encontrada o error: {e}")
    
    # 3. Buscar en tabla docentes_data si existe
    print("\n3. VERIFICANDO TABLA DOCENTES_DATA...")
    
    try:
        df_docentes = pd.read_sql_query("SELECT * FROM docentes_data LIMIT 1", conn)
        columnas_docentes_data = df_docentes.columns.tolist()
        print(f"   Columnas en docentes_data: {columnas_docentes_data}")
        
        # Buscar columnas de estabilidad
        columnas_estabilidad = [col for col in columnas_docentes_data if any(word in str(col).lower() for word in ['nombr', 'contrat', 'cargo', 'estabil', 'situacion', 'condicion'])]
        
        if columnas_estabilidad:
            print(f"   [ENCONTRADO] Columnas potenciales: {columnas_estabilidad}")
            
            df_docentes_completo = pd.read_sql_query("SELECT * FROM docentes_data", conn)
            
            for col in columnas_estabilidad:
                valores_unicos = df_docentes_completo[col].value_counts()
                print(f"     {col}:")
                for valor, cantidad in valores_unicos.head(10).items():
                    print(f"       {valor}: {cantidad}")
                    
        else:
            print("   [NO ENCONTRADO] Sin columnas de estabilidad en docentes_data")
            
    except Exception as e:
        print(f"   Tabla docentes_data no encontrada o error: {e}")
    
    # 4. Verificar si el archivo EIB MINEDU grande tiene información adicional
    print("\n4. ANALIZANDO ARCHIVO EIB MINEDU COMPLETO...")
    
    try:
        archivo_eib = r"C:\Users\lucas\Proyectos\Reasis\assets\Consultoria\Información de referencia\RegistroNacional EIB Minedu\RIIEE EIB 2024 Minedu.xlsx"
        
        # Leer muestra para ver columnas
        df_eib_muestra = pd.read_excel(archivo_eib, nrows=3)
        columnas_eib_archivo = df_eib_muestra.columns.tolist()
        
        print(f"   Total columnas en archivo EIB: {len(columnas_eib_archivo)}")
        
        # Buscar columnas relacionadas con personal docente
        terminos_docentes = [
            'docente', 'profesor', 'personal', 'nombrad', 'contrat',
            'estabil', 'situacion', 'condicion', 'cargo', 'plaza',
            'laboral', 'empleo', 'puesto'
        ]
        
        columnas_personal = []
        for col in columnas_eib_archivo:
            col_lower = str(col).lower()
            for termino in terminos_docentes:
                if termino in col_lower:
                    columnas_personal.append(col)
                    break
        
        if columnas_personal:
            print(f"   [ENCONTRADO] Columnas relacionadas con personal docente:")
            for col in columnas_personal:
                print(f"     - {col}")
                
            print("\n   ANALIZANDO DATOS DE ESTAS COLUMNAS...")
            
            # Leer datos completos solo de estas columnas + código modular
            columnas_analizar = ['Código modular'] + columnas_personal
            df_personal = pd.read_excel(archivo_eib, usecols=columnas_analizar)
            
            print(f"   Total registros: {len(df_personal)}")
            
            # Ver valores únicos de cada columna personal
            for col in columnas_personal:
                if col in df_personal.columns:
                    valores_no_nulos = df_personal[col].notna().sum()
                    if valores_no_nulos > 0:
                        print(f"\n     {col}: {valores_no_nulos}/{len(df_personal)} registros ({valores_no_nulos/len(df_personal)*100:.1f}%)")
                        valores_unicos = df_personal[col].value_counts().head(15)
                        for valor, cantidad in valores_unicos.items():
                            print(f"       {valor}: {cantidad}")
                            
        else:
            print("   [NO ENCONTRADO] Sin columnas claras de personal docente")
            
    except Exception as e:
        print(f"   Error leyendo archivo EIB completo: {e}")
    
    # 5. RESUMEN Y RECOMENDACIONES
    print("\n5. RESUMEN Y RECOMENDACIONES...")
    
    print("\nSTATUS VARIABLE X5_ED:")
    print("- PADD 2023: Encontrado 1 registro 'Profesora nombrada' (indicador de que existe la clasificación)")
    print("- EIB MINEDU: Potencialmente disponible en archivo completo (28,390 instituciones)")
    print("- Docentes actuales: Verificar si contienen información de cargo/situación")
    
    print("\nSIGUIENTES PASOS RECOMENDADOS:")
    print("1. Explorar archivo Servicios Educativos (puede tener datos de personal)")
    print("2. Analizar columnas específicas del EIB MINEDU encontradas")
    print("3. Considerar integrar datos de ESCALE si están disponibles")
    print("4. Como alternativa: Crear proxy usando tipo de cargo (Director vs Docente)")
    
    conn.close()

if __name__ == "__main__":
    main()