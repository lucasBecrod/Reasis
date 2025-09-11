#!/usr/bin/env python3
"""
Explorador de datos de estabilidad docente (X5_ED)
Proyecto Reasis - Búsqueda específica de información sobre nombrados vs contratados

Objetivo: Encontrar datos para completar la variable X5_ED (Estabilidad docente)
Archivos objetivo: Todos los Excel del directorio consultoria
Búsqueda: Columnas relacionadas con tipo de contrato, nombramiento, estabilidad laboral
"""

import pandas as pd
import os
from pathlib import Path

def explorar_archivo_docentes(archivo_path, archivo_nombre):
    """Explora un archivo Excel buscando información de estabilidad docente"""
    
    print(f"\n=== EXPLORANDO: {archivo_nombre} ===")
    
    try:
        # Listar hojas disponibles
        xl_file = pd.ExcelFile(archivo_path)
        print(f"   Hojas: {len(xl_file.sheet_names)} -> {xl_file.sheet_names}")
        
        encontro_datos_docentes = False
        
        for hoja in xl_file.sheet_names:
            print(f"\n   --- HOJA: {hoja} ---")
            
            try:
                # Leer muestra para análisis
                df_muestra = pd.read_excel(archivo_path, sheet_name=hoja, nrows=3)
                
                if len(df_muestra) == 0:
                    print("     [VACÍA] Hoja sin datos")
                    continue
                    
                columnas = list(df_muestra.columns)
                print(f"     Columnas ({len(columnas)}): {columnas[:8]}{'...' if len(columnas) > 8 else ''}")
                
                # BUSCAR TÉRMINOS RELACIONADOS CON ESTABILIDAD DOCENTE
                terminos_estabilidad = [
                    'nombrado', 'contratado', 'contrato', 'nombramiento',
                    'estabilidad', 'permanente', 'temporal', 'fijo',
                    'situacion_laboral', 'tipo_contrato', 'condicion_laboral',
                    'modalidad_contrato', 'regimen_laboral', 'cargo'
                ]
                
                columnas_relevantes = []
                
                for col in columnas:
                    col_lower = str(col).lower()
                    for termino in terminos_estabilidad:
                        if termino in col_lower:
                            columnas_relevantes.append(col)
                            break
                
                # También buscar columnas que mencionen "docente" o "profesor"
                columnas_docentes = []
                for col in columnas:
                    col_lower = str(col).lower()
                    if any(word in col_lower for word in ['docente', 'profesor', 'personal', 'maestro']):
                        columnas_docentes.append(col)
                
                if columnas_relevantes or columnas_docentes:
                    encontro_datos_docentes = True
                    print(f"     [RELEVANTE] Encontradas columnas de interés:")
                    
                    if columnas_relevantes:
                        print(f"     [ESTABILIDAD] {columnas_relevantes}")
                        
                        # Leer datos completos para analizar valores
                        try:
                            df_completo = pd.read_excel(archivo_path, sheet_name=hoja)
                            
                            for col_rel in columnas_relevantes:
                                valores_unicos = df_completo[col_rel].value_counts().head(10)
                                print(f"       {col_rel}: {len(df_completo)} filas")
                                if len(valores_unicos) > 0:
                                    print(f"         Valores: {valores_unicos.to_dict()}")
                                    
                        except Exception as e:
                            print(f"       Error leyendo datos completos: {e}")
                    
                    if columnas_docentes:
                        print(f"     [DOCENTES] {columnas_docentes}")
                
                else:
                    print("     [NO RELEVANTE] Sin columnas de estabilidad docente")
                    
            except Exception as e:
                print(f"     Error leyendo hoja {hoja}: {e}")
                
        if not encontro_datos_docentes:
            print("   [RESULTADO] No se encontró información de estabilidad docente")
        else:
            print("   [RESULTADO] Archivo CONTIENE información potencialmente útil")
            
    except Exception as e:
        print(f"   Error general: {e}")

def main():
    print("=== EXPLORADOR DE DATOS DE ESTABILIDAD DOCENTE ===")
    print("Objetivo: Encontrar información X5_ED (nombrados vs contratados)")
    
    base_path = Path("C:/Users/lucas/Proyectos/Reasis/assets/Consultoria")
    
    # Lista de archivos Excel encontrados (los más prometedores primero)
    archivos_prioritarios = [
        # Archivos de docentes PADD
        "Información de referencia/Data Estudiantes y Docentes PADDD-R 2022,23y24/REGISTRO DOCENTES PADD CONSOLIDADO (5).xlsx",
        "Información de referencia/Data Estudiantes y Docentes PADDD-R 2022,23y24/PADD 2023 Y 2024_RESULTADOS COMPENDIADOS POR CURSOS Y REDES_Version corregida.xlsx",
        "Información actualizada/2. PADD Consolidado.xlsx",
        
        # Archivos de competencias digitales docentes
        "Información actualizada/3. BD Comp Digitales Docentes 2025.xlsx",
        "DatosLucas/Competencias Digitales Docentes/02 Base de datos Informe Docentes Digital  2025 - RER Rural.xlsx",
        "Información actualizada/3. COMPETENCIAS DIGITALES DEL DOCENTE RURAL-2025 (por Red).xlsx",
        
        # Servicios educativos
        "Información de referencia/Estadista IIEE Estudiantes RER FyA 2024 y 2025/Identificador_Servicios Educativos FyA RER 2025 (3).xlsx",
        
        # Información actualizada
        "Información actualizada/1. Ruralidad, EIB y TOE.xlsx",
        "Información actualizada/5. RER 54 Caracterización MR 1,2,3.xlsx",
        
        # BD Clusterización
        "BD Clusterizacion (2).xlsx",
        "Propuesta Clausterización/BD Clusterizacion.xlsx",
        
        # Otros archivos con datos institucionales
        "Información de referencia/IIEE RER FyA filtradas en el Registro EIB Minedu/Instituciones_filtradas.xlsx",
        "Información de referencia/RegistroNacional EIB Minedu/RIIEE EIB 2024 Minedu.xlsx"
    ]
    
    archivos_encontrados = 0
    archivos_con_datos = 0
    
    print(f"\nExplorando {len(archivos_prioritarios)} archivos prioritarios...\n")
    
    for archivo_relativo in archivos_prioritarios:
        archivo_completo = base_path / archivo_relativo
        
        if archivo_completo.exists():
            archivos_encontrados += 1
            
            # Explorar archivo
            explorar_archivo_docentes(str(archivo_completo), archivo_relativo)
            
            # Pausa para legibilidad
            print("\n" + "="*80)
            
        else:
            print(f"\n[NO ENCONTRADO] {archivo_relativo}")
    
    # RESUMEN FINAL
    print(f"\n\n=== RESUMEN FINAL ===")
    print(f"Archivos explorados: {archivos_encontrados}")
    print(f"Archivos con potencial información X5_ED: [Se determina durante exploración]")
    
    print(f"\nOBJETIVO X5_ED:")
    print(f"- Buscar: Datos sobre nombrados vs contratados")
    print(f"- Variable: Estabilidad docente (permanente/temporal)")
    print(f"- Formato esperado: Columnas con tipo de contrato o nombramiento")
    
    print(f"\nSIGUIENTES PASOS:")
    print(f"1. Revisar archivos marcados como [RELEVANTE]")
    print(f"2. Integrar datos encontrados siguiendo metodología CLAUDE.md")
    print(f"3. Completar variable X5_ED para clustering K-Means")
    print(f"4. Alcanzar 100% completitud metodológica (12/12 variables)")

if __name__ == "__main__":
    main()