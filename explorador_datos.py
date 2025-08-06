#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Explorador de Datos - Proyecto Reasis
Script para explorar y analizar los archivos Excel en la carpeta Consultoria
"""

import os
import pandas as pd
import sqlite3
from pathlib import Path
import json
from datetime import datetime

class ExploradorDatos:
    def __init__(self):
        self.base_path = Path("assets/Consultoria")
        self.report_data = {}
        
    def explorar_archivos_excel(self):
        """Explora todos los archivos Excel en la carpeta Consultoria"""
        print("🔍 EXPLORANDO ARCHIVOS EXCEL...")
        print("=" * 50)
        
        excel_files = []
        
        # Buscar archivos Excel en todas las subcarpetas
        for root, dirs, files in os.walk(self.base_path):
            for file in files:
                if file.endswith(('.xlsx', '.xls')):
                    full_path = Path(root) / file
                    excel_files.append(full_path)
        
        print(f"📁 Encontrados {len(excel_files)} archivos Excel:")
        for file in excel_files:
            print(f"   - {file}")
        
        return excel_files
    
    def analizar_archivo_excel(self, file_path):
        """Analiza un archivo Excel y extrae información sobre sus hojas y columnas"""
        try:
            print(f"\n📊 Analizando: {file_path.name}")
            
            # Leer todas las hojas del Excel
            excel_file = pd.ExcelFile(file_path)
            hojas = excel_file.sheet_names
            
            info_archivo = {
                'ruta': str(file_path),
                'hojas': {},
                'total_hojas': len(hojas)
            }
            
            for hoja in hojas:
                try:
                    # Leer la hoja
                    df = pd.read_excel(file_path, sheet_name=hoja, nrows=5)  # Solo primeras 5 filas para análisis
                    
                    info_hoja = {
                        'columnas': list(df.columns),
                        'total_columnas': len(df.columns),
                        'tipos_datos': df.dtypes.to_dict(),
                        'filas_muestra': len(df)
                    }
                    
                    info_archivo['hojas'][hoja] = info_hoja
                    
                    print(f"   📋 Hoja '{hoja}': {len(df.columns)} columnas")
                    
                except Exception as e:
                    print(f"   ❌ Error en hoja '{hoja}': {e}")
                    info_archivo['hojas'][hoja] = {'error': str(e)}
            
            return info_archivo
            
        except Exception as e:
            print(f"❌ Error analizando {file_path.name}: {e}")
            return {'error': str(e)}
    
    def generar_reporte(self, archivos_analizados):
        """Genera un reporte completo de los datos encontrados"""
        print("\n📋 GENERANDO REPORTE...")
        print("=" * 50)
        
        reporte = {
            'fecha_analisis': datetime.now().isoformat(),
            'total_archivos': len(archivos_analizados),
            'archivos': archivos_analizados,
            'resumen': {}
        }
        
        # Contar total de hojas y columnas
        total_hojas = 0
        total_columnas = 0
        todas_las_columnas = set()
        
        for archivo, info in archivos_analizados.items():
            if 'error' not in info:
                total_hojas += info.get('total_hojas', 0)
                
                for hoja, info_hoja in info.get('hojas', {}).items():
                    if 'error' not in info_hoja:
                        total_columnas += info_hoja.get('total_columnas', 0)
                        todas_las_columnas.update(info_hoja.get('columnas', []))
        
        reporte['resumen'] = {
            'total_hojas': total_hojas,
            'total_columnas_unicas': len(todas_las_columnas),
            'columnas_unicas': sorted(list(todas_las_columnas))
        }
        
        # Guardar reporte en JSON
        with open('reporte_exploracion_datos.json', 'w', encoding='utf-8') as f:
            json.dump(reporte, f, indent=2, ensure_ascii=False)
        
        print(f"📊 RESUMEN:")
        print(f"   - Archivos Excel: {len(archivos_analizados)}")
        print(f"   - Total de hojas: {total_hojas}")
        print(f"   - Columnas únicas encontradas: {len(todas_las_columnas)}")
        print(f"\n📄 Reporte guardado en: reporte_exploracion_datos.json")
        
        return reporte
    
    def mostrar_columnas_importantes(self, reporte):
        """Muestra las columnas que podrían ser importantes para el análisis"""
        print("\n🎯 COLUMNAS POTENCIALMENTE IMPORTANTES:")
        print("=" * 50)
        
        columnas_importantes = []
        palabras_clave = [
            'institucion', 'escuela', 'colegio', 'codigo', 'nombre',
            'docente', 'estudiante', 'alumno', 'profesor',
            'rural', 'urbano', 'eib', 'intercultural',
            'conectividad', 'internet', 'equipamiento', 'computadora',
            'rendimiento', 'academico', 'nota', 'calificacion',
            'red', 'region', 'provincia', 'distrito',
            'padd', 'competencia', 'digital'
        ]
        
        todas_las_columnas = reporte['resumen']['columnas_unicas']
        
        for columna in todas_las_columnas:
            columna_lower = columna.lower()
            for palabra in palabras_clave:
                if palabra in columna_lower:
                    columnas_importantes.append(columna)
                    break
        
        print("Columnas que podrían ser relevantes para el análisis:")
        for col in sorted(set(columnas_importantes)):
            print(f"   - {col}")
        
        return columnas_importantes

def main():
    """Función principal del explorador"""
    print("🚀 EXPLORADOR DE DATOS - PROYECTO REASIS")
    print("=" * 60)
    
    explorador = ExploradorDatos()
    
    # Paso 1: Encontrar archivos Excel
    archivos_excel = explorador.explorar_archivos_excel()
    
    if not archivos_excel:
        print("❌ No se encontraron archivos Excel")
        return
    
    # Paso 2: Analizar cada archivo
    archivos_analizados = {}
    for archivo in archivos_excel:
        info = explorador.analizar_archivo_excel(archivo)
        archivos_analizados[archivo.name] = info
    
    # Paso 3: Generar reporte
    reporte = explorador.generar_reporte(archivos_analizados)
    
    # Paso 4: Mostrar columnas importantes
    explorador.mostrar_columnas_importantes(reporte)
    
    print("\n✅ EXPLORACIÓN COMPLETADA")
    print("=" * 60)
    print("📝 Próximos pasos:")
    print("   1. Revisar el reporte JSON generado")
    print("   2. Identificar qué datos queremos consolidar")
    print("   3. Crear script de mapeo de datos")
    print("   4. Crear base de datos SQLite")

if __name__ == "__main__":
    main() 