#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analizador de Fuente Primaria - Proyecto Reasis
Script para analizar en detalle la fuente primaria de datos
"""

import pandas as pd
import numpy as np
from pathlib import Path

def analizar_fuente_primaria():
    """Analiza en detalle la fuente primaria de datos"""
    print("🔍 ANALIZADOR DE FUENTE PRIMARIA DE DATOS")
    print("=" * 70)
    
    archivo_path = Path("assets/Consultoria/Información actualizada/1. Ruralidad, EIB y TOE.xlsx")
    
    if not archivo_path.exists():
        print(f"❌ Archivo no encontrado: {archivo_path}")
        return
    
    try:
        # Cargar datos
        df_datos_globales = pd.read_excel(archivo_path, sheet_name='DatosGlobales')
        df_escuelas_fya = pd.read_excel(archivo_path, sheet_name='Escuelas confirmadas FyA a Juli')
        
        print(f"📊 ANÁLISIS DE DATOSGLOBALES")
        print("=" * 50)
        
        # 1. ANÁLISIS DE CÓDIGOS
        print(f"\n🔢 ANÁLISIS DE CÓDIGOS:")
        print("-" * 30)
        
        if 'cod_mod' in df_datos_globales.columns:
            codigos_modulares = df_datos_globales['cod_mod'].dropna()
            print(f"   📋 Códigos modulares únicos: {codigos_modulares.nunique()}")
            print(f"   📊 Rango: {codigos_modulares.min()} - {codigos_modulares.max()}")
            print(f"   📋 Ejemplos: {codigos_modulares.head().tolist()}")
        
        if 'codlocal' in df_datos_globales.columns:
            codigos_locales = df_datos_globales['codlocal'].dropna()
            print(f"\n   📋 Códigos locales únicos: {codigos_locales.nunique()}")
            print(f"   📊 Rango: {codigos_locales.min()} - {codigos_locales.max()}")
            print(f"   📋 Ejemplos: {codigos_locales.head().tolist()}")
        
        # 2. ANÁLISIS GEOGRÁFICO
        print(f"\n🌍 ANÁLISIS GEOGRÁFICO:")
        print("-" * 30)
        
        columnas_geo = ['dpto', 'prov', 'dist', 'region_edu', 'region_nat']
        for col in columnas_geo:
            if col in df_datos_globales.columns:
                valores_unicos = df_datos_globales[col].dropna().unique()
                print(f"   📋 {col}: {len(valores_unicos)} valores únicos")
                print(f"   📊 Ejemplos: {valores_unicos[:5].tolist()}")
        
        # 3. ANÁLISIS DE COORDENADAS
        print(f"\n📍 ANÁLISIS DE COORDENADAS:")
        print("-" * 30)
        
        if 'nlat_ie' in df_datos_globales.columns and 'nlong_ie' in df_datos_globales.columns:
            latitudes = df_datos_globales['nlat_ie'].dropna()
            longitudes = df_datos_globales['nlong_ie'].dropna()
            
            print(f"   📋 Instituciones con coordenadas: {len(latitudes)}")
            print(f"   📊 Latitud: {latitudes.min():.6f} - {latitudes.max():.6f}")
            print(f"   📊 Longitud: {longitudes.min():.6f} - {longitudes.max():.6f}")
        
        # 4. ANÁLISIS DE NIVELES EDUCATIVOS
        print(f"\n📚 ANÁLISIS DE NIVELES EDUCATIVOS:")
        print("-" * 30)
        
        if 'd_niv_mod' in df_datos_globales.columns:
            niveles = df_datos_globales['d_niv_mod'].value_counts()
            print(f"   📋 Niveles educativos únicos: {len(niveles)}")
            for nivel, count in niveles.items():
                print(f"   📊 {nivel}: {count} instituciones")
        
        # 5. ANÁLISIS DE GESTIÓN
        print(f"\n🏛️ ANÁLISIS DE GESTIÓN:")
        print("-" * 30)
        
        if 'd_gestion' in df_datos_globales.columns:
            gestiones = df_datos_globales['d_gestion'].value_counts()
            print(f"   📋 Tipos de gestión únicos: {len(gestiones)}")
            for gestion, count in gestiones.items():
                print(f"   📊 {gestion}: {count} instituciones")
        
        # 6. ANÁLISIS DE ESCUELAS FyA
        print(f"\n🏫 ANÁLISIS DE ESCUELAS FyA:")
        print("-" * 30)
        
        print(f"   📋 Total escuelas FyA: {len(df_escuelas_fya)}")
        
        if 'Región' in df_escuelas_fya.columns:
            regiones_fya = df_escuelas_fya['Región'].value_counts()
            print(f"   📊 Distribución por región:")
            for region, count in regiones_fya.items():
                print(f"      - {region}: {count} escuelas")
        
        if 'N° FYA' in df_escuelas_fya.columns:
            rer_fya = df_escuelas_fya['N° FYA'].value_counts()
            print(f"   📊 Distribución por RER:")
            for rer, count in rer_fya.items():
                print(f"      - {rer}: {count} escuelas")
        
        # 7. CRUCE DE INFORMACIÓN
        print(f"\n🔗 CRUCE DE INFORMACIÓN:")
        print("-" * 30)
        
        # Verificar si hay códigos modulares en ambas tablas
        if 'cod_mod' in df_datos_globales.columns and 'cod_mod' in df_escuelas_fya.columns:
            codigos_dg = set(df_datos_globales['cod_mod'].dropna())
            codigos_fya = set(df_escuelas_fya['cod_mod'].dropna())
            
            interseccion = codigos_dg.intersection(codigos_fya)
            print(f"   📋 Códigos modulares en ambas tablas: {len(interseccion)}")
            print(f"   📊 Solo en DatosGlobales: {len(codigos_dg - codigos_fya)}")
            print(f"   📊 Solo en Escuelas FyA: {len(codigos_fya - codigos_dg)}")
        
        # 8. PROPUESTA DE NUEVA ESTRUCTURA
        print(f"\n💡 PROPUESTA DE NUEVA ESTRUCTURA V2.0")
        print("=" * 50)
        
        print(f"""
CREATE TABLE instituciones_educativas_v2 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- CÓDIGOS OFICIALES
    codigo_modular TEXT UNIQUE NOT NULL,           -- cod_mod del MINEDU
    codigo_local TEXT,                             -- codlocal del MINEDU
    codigo_rie TEXT,                               -- Código RIE si existe
    
    -- INFORMACIÓN BÁSICA
    nombre_institucion TEXT NOT NULL,              -- cen_edu
    nombre_corto TEXT,                             -- Nombre abreviado
    tipo_institucion TEXT NOT NULL,                -- 'RER', 'IE', 'CEBA', etc.
    
    -- INFORMACIÓN GEOGRÁFICA
    region TEXT NOT NULL,                          -- region_edu
    provincia TEXT NOT NULL,                       -- prov
    distrito TEXT NOT NULL,                        -- dist
    departamento TEXT,                             -- dpto
    direccion TEXT,                                -- direccion
    localidad TEXT,                                -- localidad
    centro_poblado TEXT,                           -- cen_pob
    
    -- COORDENADAS GPS
    latitud REAL,                                  -- nlat_ie
    longitud REAL,                                 -- nlong_ie
    altitud REAL,                                  -- altitud
    
    -- INFORMACIÓN EDUCATIVA
    nivel_educativo TEXT NOT NULL,                 -- d_niv_mod
    modalidad TEXT,                                -- d_forma
    gestion TEXT NOT NULL,                         -- d_gestion
    tipo_sexo TEXT,                                -- d_tipssexo
    turno TEXT,                                    -- d_cod_tur
    
    -- ESTADÍSTICAS
    total_alumnos INTEGER,                         -- talumno
    alumnos_hombres INTEGER,                       -- talum_hom
    alumnos_mujeres INTEGER,                       -- talum_muj
    total_docentes INTEGER,                        -- tdocente
    total_secciones INTEGER,                       -- tseccion
    directivos_hombres INTEGER,                    -- NDirectivosH
    directivos_mujeres INTEGER,                    -- NDirectivosM
    docentes_hombres INTEGER,                      -- NDocentesH
    docentes_mujeres INTEGER,                      -- NDocentesM
    
    -- INFORMACIÓN ESPECIALIZADA
    es_rural BOOLEAN DEFAULT FALSE,                -- Basado en ruralidad
    es_eib BOOLEAN DEFAULT FALSE,                  -- Educación Intercultural Bilingüe
    es_toe BOOLEAN DEFAULT FALSE,                  -- Tiempo Oficial Extendido
    
    -- INFORMACIÓN DE CONTACTO
    director TEXT,                                 -- director
    telefono TEXT,                                 -- telefono
    email TEXT,                                    -- email
    pagina_web TEXT,                               -- pagweb
    
    -- INFORMACIÓN FyA
    es_fya BOOLEAN DEFAULT FALSE,                  -- Es escuela Fe y Alegría
    numero_fya TEXT,                               -- N° FYA
    unidad_ejecutora TEXT,                         -- UGEL
    
    -- METADATOS
    fuente_datos TEXT DEFAULT 'MINEDU',
    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    usuario_actualizacion TEXT,
    
    -- ÍNDICES
    INDEX idx_codigo_modular (codigo_modular),
    INDEX idx_codigo_local (codigo_local),
    INDEX idx_region (region),
    INDEX idx_es_fya (es_fya)
);
        """)
        
        # 9. RESUMEN DE DATOS DISPONIBLES
        print(f"\n📊 RESUMEN DE DATOS DISPONIBLES")
        print("=" * 50)
        
        print(f"   📋 DatosGlobales:")
        print(f"      - Total instituciones: {len(df_datos_globales)}")
        print(f"      - Con códigos modulares: {df_datos_globales['cod_mod'].notna().sum()}")
        print(f"      - Con códigos locales: {df_datos_globales['codlocal'].notna().sum()}")
        print(f"      - Con coordenadas: {df_datos_globales['nlat_ie'].notna().sum()}")
        
        print(f"\n   📋 Escuelas FyA:")
        print(f"      - Total escuelas: {len(df_escuelas_fya)}")
        print(f"      - Con códigos modulares: {df_escuelas_fya['cod_mod'].notna().sum()}")
        print(f"      - Con códigos locales: {df_escuelas_fya['Código Local'].notna().sum()}")
        
        print(f"\n💡 RECOMENDACIONES:")
        print(f"   1. Usar DatosGlobales como fuente principal")
        print(f"   2. Enriquecer con datos de Escuelas FyA")
        print(f"   3. Crear migración automática a nueva estructura")
        print(f"   4. Validar datos con fuente secundaria")
        
    except Exception as e:
        print(f"❌ Error analizando fuente primaria: {e}")

if __name__ == "__main__":
    analizar_fuente_primaria()
