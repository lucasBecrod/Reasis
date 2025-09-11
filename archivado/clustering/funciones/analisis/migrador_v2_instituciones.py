#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Migrador V2.0 - Instituciones Educativas - Proyecto Reasis
Script para crear la nueva estructura V2.0 de instituciones educativas
"""

import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

def crear_estructura_v2():
    """Crea la nueva estructura V2.0 de instituciones educativas"""
    print("🏗️ CREANDO ESTRUCTURA V2.0 - INSTITUCIONES EDUCATIVAS")
    print("=" * 70)
    
    db_path = "reasis_database.db"
    
    if not Path(db_path).exists():
        print(f"❌ Base de datos no encontrada: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        
        # Crear tabla V2.0
        print(f"\n📋 CREANDO TABLA V2.0")
        print("-" * 40)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS instituciones_educativas_v2 (
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
                usuario_actualizacion TEXT
            )
        """)
        
        # Crear índices para optimizar consultas
        print(f"📊 CREANDO ÍNDICES")
        print("-" * 40)
        
        conn.execute("CREATE INDEX IF NOT EXISTS idx_codigo_modular ON instituciones_educativas_v2(codigo_modular)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_codigo_local ON instituciones_educativas_v2(codigo_local)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_region ON instituciones_educativas_v2(region)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_es_fya ON instituciones_educativas_v2(es_fya)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_nivel_educativo ON instituciones_educativas_v2(nivel_educativo)")
        
        conn.commit()
        print("   ✅ Estructura V2.0 creada exitosamente")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creando estructura V2.0: {e}")
        return False
    finally:
        conn.close()

def procesar_fuente_primaria():
    """Procesa la fuente primaria de datos"""
    print(f"\n📊 PROCESANDO FUENTE PRIMARIA")
    print("=" * 50)
    
    archivo_path = Path("assets/Consultoria/Información actualizada/1. Ruralidad, EIB y TOE.xlsx")
    
    if not archivo_path.exists():
        print(f"❌ Archivo no encontrado: {archivo_path}")
        return None, None
    
    try:
        # Cargar datos
        df_datos_globales = pd.read_excel(archivo_path, sheet_name='DatosGlobales')
        df_escuelas_fya = pd.read_excel(archivo_path, sheet_name='Escuelas confirmadas FyA a Juli')
        
        print(f"   📋 DatosGlobales cargados: {len(df_datos_globales)} registros")
        print(f"   📋 Escuelas FyA cargadas: {len(df_escuelas_fya)} registros")
        
        return df_datos_globales, df_escuelas_fya
        
    except Exception as e:
        print(f"❌ Error procesando fuente primaria: {e}")
        return None, None

def limpiar_y_transformar_datos(df_datos_globales, df_escuelas_fya):
    """Limpia y transforma los datos para la nueva estructura"""
    print(f"\n🧹 LIMPIANDO Y TRANSFORMANDO DATOS")
    print("=" * 50)
    
    try:
        # 1. LIMPIAR DATOSGLOBALES
        print(f"   📊 Limpiando DatosGlobales...")
        
        # Crear copia para no modificar el original
        df_clean = df_datos_globales.copy()
        
        # Limpiar códigos modulares
        df_clean['cod_mod'] = df_clean['cod_mod'].astype(str).str.strip()
        df_clean['codlocal'] = df_clean['codlocal'].astype(str).str.strip()
        
        # Limpiar nombres
        df_clean['cen_edu'] = df_clean['cen_edu'].astype(str).str.strip()
        
        # Limpiar coordenadas
        df_clean['nlat_ie'] = pd.to_numeric(df_clean['nlat_ie'], errors='coerce')
        df_clean['nlong_ie'] = pd.to_numeric(df_clean['nlong_ie'], errors='coerce')
        df_clean['altitud'] = pd.to_numeric(df_clean['altitud'], errors='coerce')
        
        # Limpiar estadísticas
        columnas_numericas = ['talumno', 'talum_hom', 'talum_muj', 'tdocente', 'tseccion',
                             'NDirectivosH', 'NDirectivosM', 'NDocentesH', 'NDocentesM']
        
        for col in columnas_numericas:
            if col in df_clean.columns:
                df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
        
        # 2. LIMPIAR ESCUELAS FyA
        print(f"   📊 Limpiando Escuelas FyA...")
        
        df_fya_clean = df_escuelas_fya.copy()
        
        # Limpiar códigos
        df_fya_clean['cod_mod'] = df_fya_clean['cod_mod'].astype(str).str.strip()
        df_fya_clean['Código Local'] = df_fya_clean['Código Local'].astype(str).str.strip()
        
        # Limpiar nombres
        df_fya_clean['Institución Educativa'] = df_fya_clean['Institución Educativa'].astype(str).str.strip()
        
        print(f"   ✅ Datos limpiados exitosamente")
        
        return df_clean, df_fya_clean
        
    except Exception as e:
        print(f"❌ Error limpiando datos: {e}")
        return None, None

def insertar_datos_v2(df_datos_globales, df_escuelas_fya):
    """Inserta los datos en la nueva estructura V2.0"""
    print(f"\n💾 INSERTANDO DATOS EN V2.0")
    print("=" * 50)
    
    db_path = "reasis_database.db"
    
    try:
        conn = sqlite3.connect(db_path)
        
        # Iniciar transacción
        conn.execute("BEGIN TRANSACTION")
        
        # 1. PROCESAR DATOSGLOBALES
        print(f"   📊 Procesando DatosGlobales...")
        
        registros_insertados = 0
        
        for _, row in df_datos_globales.iterrows():
            try:
                # Determinar tipo de institución basado en el nombre
                nombre = str(row['cen_edu']).strip()
                tipo_institucion = 'IE'  # Por defecto
                
                if 'RER' in nombre.upper():
                    tipo_institucion = 'RER'
                elif 'CEBA' in nombre.upper():
                    tipo_institucion = 'CEBA'
                elif 'CETPRO' in nombre.upper():
                    tipo_institucion = 'CETPRO'
                
                # Determinar si es rural basado en la región natural
                es_rural = False
                if 'region_nat' in row and pd.notna(row['region_nat']):
                    region_nat = str(row['region_nat']).strip()
                    if region_nat in ['Sierra', 'Selva Alta', 'Selva Baja']:
                        es_rural = True
                
                # Insertar registro
                conn.execute("""
                    INSERT INTO instituciones_educativas_v2 (
                        codigo_modular, codigo_local, nombre_institucion, tipo_institucion,
                        region, provincia, distrito, departamento, direccion, localidad, centro_poblado,
                        latitud, longitud, altitud, nivel_educativo, modalidad, gestion, tipo_sexo, turno,
                        total_alumnos, alumnos_hombres, alumnos_mujeres, total_docentes, total_secciones,
                        directivos_hombres, directivos_mujeres, docentes_hombres, docentes_mujeres,
                        es_rural, director, telefono, email, pagina_web, es_fya, fuente_datos
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(row['cod_mod']), str(row['codlocal']), str(row['cen_edu']), tipo_institucion,
                    str(row.get('region_edu', '')), str(row.get('prov', '')), str(row.get('dist', '')), str(row.get('dpto', '')),
                    str(row.get('direccion', '')), str(row.get('localidad', '')), str(row.get('cen_pob', '')),
                    row.get('nlat_ie'), row.get('nlong_ie'), row.get('altitud'),
                    str(row.get('d_niv_mod', '')), str(row.get('d_forma', '')), str(row.get('d_gestion', '')),
                    str(row.get('d_tipssexo', '')), str(row.get('d_cod_tur', '')),
                    row.get('talumno'), row.get('talum_hom'), row.get('talum_muj'),
                    row.get('tdocente'), row.get('tseccion'),
                    row.get('NDirectivosH'), row.get('NDirectivosM'), row.get('NDocentesH'), row.get('NDocentesM'),
                    es_rural, str(row.get('director', '')), str(row.get('telefono', '')), str(row.get('email', '')),
                    str(row.get('pagweb', '')), False, 'MINEDU'
                ))
                
                registros_insertados += 1
                
            except Exception as e:
                print(f"   ⚠️ Error procesando registro {row.get('cod_mod', 'N/A')}: {e}")
                continue
        
        print(f"   ✅ DatosGlobales procesados: {registros_insertados} registros")
        
        # 2. ENRIQUECER CON DATOS FyA
        print(f"   📊 Enriqueciendo con datos FyA...")
        
        registros_fya = 0
        
        for _, row in df_escuelas_fya.iterrows():
            try:
                codigo_modular = str(row['cod_mod']).strip()
                
                # Buscar si ya existe en la tabla V2
                existing = conn.execute("""
                    SELECT id FROM instituciones_educativas_v2 
                    WHERE codigo_modular = ?
                """, (codigo_modular,)).fetchone()
                
                if existing:
                    # Actualizar con información FyA
                    conn.execute("""
                        UPDATE instituciones_educativas_v2 SET
                            es_fya = TRUE,
                            numero_fya = ?,
                            unidad_ejecutora = ?,
                            codigo_rie = ?
                        WHERE codigo_modular = ?
                    """, (
                        str(row.get('N° FYA', '')),
                        str(row.get('Unidad Ejecutora', '')),
                        str(row.get('Código RIE', '')),
                        codigo_modular
                    ))
                    registros_fya += 1
                else:
                    # Insertar nuevo registro FyA
                    nombre = str(row.get('Institución Educativa', '')).strip()
                    tipo_institucion = 'RER' if 'RER' in nombre.upper() else 'IE'
                    
                    conn.execute("""
                        INSERT INTO instituciones_educativas_v2 (
                            codigo_modular, codigo_local, nombre_institucion, tipo_institucion,
                            region, provincia, distrito, direccion, centro_poblado,
                            nivel_educativo, es_fya, numero_fya, unidad_ejecutora, codigo_rie,
                            fuente_datos
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        codigo_modular, str(row.get('Código Local', '')), nombre, tipo_institucion,
                        str(row.get('Región', '')), str(row.get('Provincia', '')), str(row.get('Distrito', '')),
                        str(row.get('direccion', '')), str(row.get('Centro Poblado', '')),
                        str(row.get('Nivel Educativo/Modalidad', '')), True,
                        str(row.get('N° FYA', '')), str(row.get('Unidad Ejecutora', '')),
                        str(row.get('Código RIE', '')), 'MINEDU_FyA'
                    ))
                    registros_fya += 1
                
            except Exception as e:
                print(f"   ⚠️ Error procesando FyA {row.get('cod_mod', 'N/A')}: {e}")
                continue
        
        print(f"   ✅ Datos FyA procesados: {registros_fya} registros")
        
        # Confirmar transacción
        conn.commit()
        
        # 3. VERIFICAR RESULTADOS
        print(f"\n📊 VERIFICANDO RESULTADOS")
        print("-" * 40)
        
        total_registros = conn.execute("SELECT COUNT(*) FROM instituciones_educativas_v2").fetchone()[0]
        total_fya = conn.execute("SELECT COUNT(*) FROM instituciones_educativas_v2 WHERE es_fya = 1").fetchone()[0]
        total_con_coordenadas = conn.execute("SELECT COUNT(*) FROM instituciones_educativas_v2 WHERE latitud IS NOT NULL").fetchone()[0]
        
        print(f"   📋 Total registros: {total_registros}")
        print(f"   🏫 Escuelas FyA: {total_fya}")
        print(f"   📍 Con coordenadas: {total_con_coordenadas}")
        
        # Mostrar distribución por región
        print(f"\n🌍 Distribución por región:")
        regiones = conn.execute("""
            SELECT region, COUNT(*) as total 
            FROM instituciones_educativas_v2 
            GROUP BY region 
            ORDER BY total DESC
        """).fetchall()
        
        for region, total in regiones:
            print(f"   - {region}: {total} instituciones")
        
        # Mostrar distribución por nivel educativo
        print(f"\n📚 Distribución por nivel educativo:")
        niveles = conn.execute("""
            SELECT nivel_educativo, COUNT(*) as total 
            FROM instituciones_educativas_v2 
            GROUP BY nivel_educativo 
            ORDER BY total DESC
        """).fetchall()
        
        for nivel, total in niveles:
            print(f"   - {nivel}: {total} instituciones")
        
        conn.close()
        
        print(f"\n✅ MIGRACIÓN V2.0 COMPLETADA EXITOSAMENTE")
        print("=" * 70)
        
        return True
        
    except Exception as e:
        print(f"❌ Error en migración V2.0: {e}")
        conn.rollback()
        conn.close()
        return False

def main():
    """Función principal"""
    print("🚀 MIGRADOR V2.0 - INSTITUCIONES EDUCATIVAS")
    print("=" * 70)
    
    # 1. Crear estructura V2.0
    if not crear_estructura_v2():
        return
    
    # 2. Procesar fuente primaria
    df_datos_globales, df_escuelas_fya = procesar_fuente_primaria()
    if df_datos_globales is None:
        return
    
    # 3. Limpiar y transformar datos
    df_clean, df_fya_clean = limpiar_y_transformar_datos(df_datos_globales, df_escuelas_fya)
    if df_clean is None:
        return
    
    # 4. Insertar datos en V2.0
    if insertar_datos_v2(df_clean, df_fya_clean):
        print(f"\n🎉 MIGRACIÓN V2.0 EXITOSA")
        print("=" * 70)
        print(f"💡 La nueva estructura está lista para análisis estadístico")
    else:
        print(f"\n❌ ERROR EN MIGRACIÓN V2.0")

if __name__ == "__main__":
    main()
