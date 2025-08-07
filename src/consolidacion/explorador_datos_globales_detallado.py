#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Explorador Detallado - DatosGlobales - Proyecto Reasis
Script para mostrar las 10 primeras filas de DatosGlobales con todos los campos
"""

import pandas as pd
import numpy as np
from pathlib import Path

def mostrar_datos_globales_detallado():
    """Muestra las 10 primeras filas de DatosGlobales con todos los campos"""
    print("🔍 EXPLORADOR DETALLADO - DATOSGLOBALES")
    print("=" * 70)
    
    archivo_path = Path("assets/Consultoria/Información actualizada/1. Ruralidad, EIB y TOE.xlsx")
    
    if not archivo_path.exists():
        print(f"❌ Archivo no encontrado: {archivo_path}")
        return
    
    try:
        # Cargar datos
        df_datos_globales = pd.read_excel(archivo_path, sheet_name='DatosGlobales')
        
        print(f"📊 INFORMACIÓN GENERAL")
        print("=" * 50)
        print(f"   📋 Total filas: {len(df_datos_globales)}")
        print(f"   📋 Total columnas: {len(df_datos_globales.columns)}")
        
        # Mostrar todas las columnas con su posición
        print(f"\n📋 TODAS LAS COLUMNAS DISPONIBLES:")
        print("=" * 50)
        for i, col in enumerate(df_datos_globales.columns):
            print(f"   {i+1:2d}. {col}")
        
        # Mostrar las 10 primeras filas con todos los campos
        print(f"\n📋 PRIMERAS 10 FILAS CON TODOS LOS CAMPOS:")
        print("=" * 100)
        
        for i in range(min(10, len(df_datos_globales))):
            print(f"\n--- FILA {i+1} ---")
            row = df_datos_globales.iloc[i]
            
            for col in df_datos_globales.columns:
                valor = str(row[col]) if pd.notna(row[col]) else "N/A"
                # Limitar el valor si es muy largo
                if len(valor) > 50:
                    valor = valor[:47] + "..."
                print(f"   {col}: {valor}")
        
        # Análisis de campos importantes que no estamos usando
        print(f"\n🔍 ANÁLISIS DE CAMPOS ADICIONALES")
        print("=" * 50)
        
        # Campos que podríamos estar perdiendo
        campos_adicionales = [
            'nroced', 'cuadro', 'd_cod_car', 'd_ges_dep', 'dre_ugel', 
            'dareacenso', 'nfya', 'modal', 'valido', 'ident', 
            'multiplicidad1', 'multiplicidad2'
        ]
        
        print(f"   📋 Campos adicionales que no estamos usando:")
        for campo in campos_adicionales:
            if campo in df_datos_globales.columns:
                valores_unicos = df_datos_globales[campo].dropna().nunique()
                print(f"      - {campo}: {valores_unicos} valores únicos")
                
                # Mostrar algunos ejemplos
                ejemplos = df_datos_globales[campo].dropna().head(3).tolist()
                print(f"        Ejemplos: {ejemplos}")
        
        # Análisis de campos específicos importantes
        print(f"\n📊 ANÁLISIS DE CAMPOS ESPECÍFICOS")
        print("=" * 50)
        
        # Análisis de nfya (número FyA)
        if 'nfya' in df_datos_globales.columns:
            nfya_no_nulos = df_datos_globales['nfya'].notna().sum()
            print(f"   📋 Campo 'nfya' (Número FyA):")
            print(f"      - Registros con valor: {nfya_no_nulos}")
            print(f"      - Porcentaje: {nfya_no_nulos/len(df_datos_globales)*100:.1f}%")
            
            if nfya_no_nulos > 0:
                ejemplos_nfya = df_datos_globales[df_datos_globales['nfya'].notna()]['nfya'].head(5).tolist()
                print(f"      - Ejemplos: {ejemplos_nfya}")
        
        # Análisis de modal
        if 'modal' in df_datos_globales.columns:
            modal_valores = df_datos_globales['modal'].value_counts()
            print(f"\n   📋 Campo 'modal':")
            for valor, count in modal_valores.items():
                print(f"      - {valor}: {count} registros")
        
        # Análisis de valido
        if 'valido' in df_datos_globales.columns:
            valido_valores = df_datos_globales['valido'].value_counts()
            print(f"\n   📋 Campo 'valido':")
            for valor, count in valido_valores.items():
                print(f"      - {valor}: {count} registros")
        
        # Análisis de multiplicidad
        if 'multiplicidad1' in df_datos_globales.columns:
            mult1_no_nulos = df_datos_globales['multiplicidad1'].notna().sum()
            print(f"\n   📋 Campo 'multiplicidad1':")
            print(f"      - Registros con valor: {mult1_no_nulos}")
            if mult1_no_nulos > 0:
                ejemplos_mult1 = df_datos_globales[df_datos_globales['multiplicidad1'].notna()]['multiplicidad1'].head(3).tolist()
                print(f"      - Ejemplos: {ejemplos_mult1}")
        
        if 'multiplicidad2' in df_datos_globales.columns:
            mult2_no_nulos = df_datos_globales['multiplicidad2'].notna().sum()
            print(f"   📋 Campo 'multiplicidad2':")
            print(f"      - Registros con valor: {mult2_no_nulos}")
            if mult2_no_nulos > 0:
                ejemplos_mult2 = df_datos_globales[df_datos_globales['multiplicidad2'].notna()]['multiplicidad2'].head(3).tolist()
                print(f"      - Ejemplos: {ejemplos_mult2}")
        
        # Propuesta de mejora para la estructura V2.0
        print(f"\n💡 PROPUESTA DE MEJORA PARA V2.0")
        print("=" * 50)
        
        print(f"   📋 Campos adicionales que podríamos incluir:")
        print(f"      - nroced: Número de procedimiento")
        print(f"      - cuadro: Cuadro de datos")
        print(f"      - d_cod_car: Código de carrera")
        print(f"      - d_ges_dep: Gestión departamental")
        print(f"      - dre_ugel: DRE/UGEL")
        print(f"      - dareacenso: Área de censo")
        print(f"      - nfya: Número FyA (ya tenemos pero podría ser más preciso)")
        print(f"      - modal: Modalidad específica")
        print(f"      - valido: Estado de validación")
        print(f"      - ident: Identificador único")
        print(f"      - multiplicidad1 y multiplicidad2: Información de multiplicidad")
        
        print(f"\n   🎯 SUGERENCIAS:")
        print(f"      1. Incluir campo 'estado_validacion' basado en 'valido'")
        print(f"      2. Incluir campo 'modalidad_especifica' basado en 'modal'")
        print(f"      3. Incluir campo 'numero_procedimiento' basado en 'nroced'")
        print(f"      4. Incluir campo 'area_censo' basado en 'dareacenso'")
        print(f"      5. Incluir campos de multiplicidad para análisis estadístico")
        print(f"      6. Mejorar el campo 'numero_fya' usando 'nfya' de la fuente primaria")
        
        # Mostrar algunos ejemplos de datos que podríamos estar perdiendo
        print(f"\n📋 EJEMPLOS DE DATOS ADICIONALES:")
        print("=" * 50)
        
        for i in range(min(3, len(df_datos_globales))):
            row = df_datos_globales.iloc[i]
            print(f"\n   Ejemplo {i+1}:")
            
            campos_importantes = ['nfya', 'modal', 'valido', 'multiplicidad1', 'multiplicidad2', 'dareacenso']
            for campo in campos_importantes:
                if campo in df_datos_globales.columns:
                    valor = str(row[campo]) if pd.notna(row[campo]) else "N/A"
                    print(f"      {campo}: {valor}")
        
        print(f"\n✅ EXPLORACIÓN DETALLADA COMPLETADA")
        print("=" * 70)
        
    except Exception as e:
        print(f"❌ Error explorando datos detallados: {e}")

if __name__ == "__main__":
    mostrar_datos_globales_detallado()
