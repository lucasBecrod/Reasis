#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Migrador V2.0 Mejorado - Instituciones Educativas - Proyecto Reasis
Script para crear la estructura V2.0 mejorada con todos los campos disponibles
"""

import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

def crear_estructura_v2_mejorada():
    """Crea la estructura V2.0 mejorada con todos los campos disponibles"""
    print("🏗️ CREANDO ESTRUCTURA V2.0 MEJORADA - INSTITUCIONES EDUCATIVAS")
    print("=" * 70)
    
    db_path = "reasis_database.db"
    
    if not Path(db_path).exists():
        print(f"❌ Base de datos no encontrada: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        
        # Crear tabla V2.0 mejorada
        print(f"\n📋 CREANDO TABLA V2.0 MEJORADA")
        print("-" * 40)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS instituciones_educativas_v2_mejorada (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                
                -- CÓDIGOS OFICIALES
                codigo_modular TEXT UNIQUE NOT NULL,           -- cod_mod del MINEDU
                codigo_local TEXT,                             -- codlocal del MINEDU
                codigo_rie TEXT,                               -- Código RIE si existe
                numero_procedimiento TEXT,                     -- nroced
                cuadro_datos TEXT,                             -- cuadro
                
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
                area_censo TEXT,                               -- dareacenso (Rural/Urbana)
                
                -- COORDENADAS GPS
                latitud REAL,                                  -- nlat_ie
                longitud REAL,                                 -- nlong_ie
                altitud REAL,                                  -- altitud
                
                -- INFORMACIÓN EDUCATIVA
                nivel_educativo TEXT NOT NULL,                 -- d_niv_mod
                modalidad TEXT,                                -- d_forma
                modalidad_especifica TEXT,                     -- modal (EBR, RER, EBA, etc.)
                gestion TEXT NOT NULL,                         -- d_gestion
                gestion_departamental TEXT,                    -- d_ges_dep
                tipo_sexo TEXT,                                -- d_tipssexo
                turno TEXT,                                    -- d_cod_tur
                codigo_carrera TEXT,                           -- d_cod_car
                
                -- ESTADÍSTICAS
                total_alumnos INTEGER,                         -- talumno
                alumnos_hombres INTEGER,                       -- talum_hom
                alumnos_mujeres INTEGER,                       -- talum_muj
                total_docentes INTEGER,                        -- tdocente
                total_secciones INTEGER,                       -- tseccion
                directivos_hombres INTEGER,                    -- NDirectivosH
                directivos_mujeres INTEGER,                    -- NDirectivosM
                directivos_total INTEGER,                      -- NDirectivosT
                docentes_hombres INTEGER,                      -- NDocentesH
                docentes_mujeres INTEGER,                      -- NDocentesM
                docentes_total INTEGER,                        -- NDocentesT
                
                -- INFORMACIÓN ESPECIALIZADA
                es_rural BOOLEAN DEFAULT FALSE,                -- Basado en ruralidad
                es_eib BOOLEAN DEFAULT FALSE,                  -- Educación Intercultural Bilingüe
                es_toe BOOLEAN DEFAULT FALSE,                  -- Tiempo Oficial Extendido
                estado_validacion TEXT,                        -- valido
                
                -- INFORMACIÓN DE CONTACTO
                director TEXT,                                 -- director
                telefono TEXT,                                 -- telefono
                email TEXT,                                    -- email
                pagina_web TEXT,                               -- pagweb
                
                -- INFORMACIÓN FyA
                es_fya BOOLEAN DEFAULT FALSE,                  -- Es escuela Fe y Alegría
                numero_fya TEXT,                               -- nfya (más preciso que N° FYA)
                numero_fya_secundario TEXT,                    -- N° FYA de la hoja secundaria
                unidad_ejecutora TEXT,                         -- dre_ugel
                
                -- INFORMACIÓN DE MULTIPLICIDAD
                multiplicidad1 INTEGER,                        -- multiplicidad1
                multiplicidad2 INTEGER,                        -- multiplicidad2
                identificador TEXT,                            -- ident
                
                -- METADATOS
                fuente_datos TEXT DEFAULT 'MINEDU',
                fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                usuario_actualizacion TEXT
            )
        """)
        
        # Crear índices para optimizar consultas
        print(f"📊 CREANDO ÍNDICES")
        print("-" * 40)
        
        conn.execute("CREATE INDEX IF NOT EXISTS idx_codigo_modular_mejorado ON instituciones_educativas_v2_mejorada(codigo_modular)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_codigo_local_mejorado ON instituciones_educativas_v2_mejorada(codigo_local)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_region_mejorado ON instituciones_educativas_v2_mejorada(region)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_es_fya_mejorado ON instituciones_educativas_v2_mejorada(es_fya)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_nivel_educativo_mejorado ON instituciones_educativas_v2_mejorada(nivel_educativo)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_modalidad_especifica ON instituciones_educativas_v2_mejorada(modalidad_especifica)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_area_censo ON instituciones_educativas_v2_mejorada(area_censo)")
        
        conn.commit()
        print("   ✅ Estructura V2.0 mejorada creada exitosamente")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creando estructura V2.0 mejorada: {e}")
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

def limpiar_y_transformar_datos_mejorado(df_datos_globales, df_escuelas_fya):
    """Limpia y transforma los datos para la nueva estructura mejorada"""
    print(f"\n🧹 LIMPIANDO Y TRANSFORMANDO DATOS MEJORADO")
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
                             'NDirectivosH', 'NDirectivosM', 'NDirectivosT', 'NDocentesH', 'NDocentesM', 'NDocentesT',
                             'multiplicidad1', 'multiplicidad2']
        
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

def insertar_datos_v2_mejorado(df_datos_globales, df_escuelas_fya):
    """Inserta los datos en la nueva estructura V2.0 mejorada"""
    print(f"\n💾 INSERTANDO DATOS EN V2.0 MEJORADA")
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
                
                # Determinar si es rural basado en la región natural y área de censo
                es_rural = False
                if 'region_nat' in row and pd.notna(row['region_nat']):
                    region_nat = str(row['region_nat']).strip()
                    if region_nat in ['Sierra', 'Selva Alta', 'Selva Baja']:
                        es_rural = True
                
                # Verificar área de censo
                if 'dareacenso' in row and pd.notna(row['dareacenso']):
                    area_censo = str(row['dareacenso']).strip()
                    if area_censo == 'Rural':
                        es_rural = True
                
                # Determinar si es FyA basado en nfya
                es_fya = False
                numero_fya = ''
                if 'nfya' in row and pd.notna(row['nfya']):
                    nfya_valor = str(row['nfya']).strip()
                    if 'FA' in nfya_valor or 'RER FA' in nfya_valor:
                        es_fya = True
                        numero_fya = nfya_valor
                
                # Insertar registro mejorado
                conn.execute("""
                    INSERT INTO instituciones_educativas_v2_mejorada (
                        codigo_modular, codigo_local, codigo_rie, numero_procedimiento, cuadro_datos,
                        nombre_institucion, tipo_institucion, region, provincia, distrito, departamento,
                        direccion, localidad, centro_poblado, area_censo, latitud, longitud, altitud,
                        nivel_educativo, modalidad, modalidad_especifica, gestion, gestion_departamental,
                        tipo_sexo, turno, codigo_carrera, total_alumnos, alumnos_hombres, alumnos_mujeres,
                        total_docentes, total_secciones, directivos_hombres, directivos_mujeres, directivos_total,
                        docentes_hombres, docentes_mujeres, docentes_total, es_rural, estado_validacion,
                        director, telefono, email, pagina_web, es_fya, numero_fya, unidad_ejecutora,
                        multiplicidad1, multiplicidad2, identificador, fuente_datos
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(row['cod_mod']), str(row['codlocal']), str(row.get('codigo_rie', '')), 
                    str(row.get('nroced', '')), str(row.get('cuadro', '')),
                    str(row['cen_edu']), tipo_institucion, str(row.get('region_edu', '')), 
                    str(row.get('prov', '')), str(row.get('dist', '')), str(row.get('dpto', '')),
                    str(row.get('direccion', '')), str(row.get('localidad', '')), str(row.get('cen_pob', '')),
                    str(row.get('dareacenso', '')), row.get('nlat_ie'), row.get('nlong_ie'), row.get('altitud'),
                    str(row.get('d_niv_mod', '')), str(row.get('d_forma', '')), str(row.get('modal', '')),
                    str(row.get('d_gestion', '')), str(row.get('d_ges_dep', '')), str(row.get('d_tipssexo', '')),
                    str(row.get('d_cod_tur', '')), str(row.get('d_cod_car', '')),
                    row.get('talumno'), row.get('talum_hom'), row.get('talum_muj'),
                    row.get('tdocente'), row.get('tseccion'), row.get('NDirectivosH'), row.get('NDirectivosM'), row.get('NDirectivosT'),
                    row.get('NDocentesH'), row.get('NDocentesM'), row.get('NDocentesT'),
                    es_rural, str(row.get('valido', '')), str(row.get('director', '')), str(row.get('telefono', '')), 
                    str(row.get('email', '')), str(row.get('pagweb', '')), es_fya, numero_fya, str(row.get('dre_ugel', '')),
                    row.get('multiplicidad1'), row.get('multiplicidad2'), str(row.get('ident', '')), 'MINEDU'
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
                
                # Buscar si ya existe en la tabla V2 mejorada
                existing = conn.execute("""
                    SELECT id FROM instituciones_educativas_v2_mejorada 
                    WHERE codigo_modular = ?
                """, (codigo_modular,)).fetchone()
                
                if existing:
                    # Actualizar con información FyA secundaria
                    conn.execute("""
                        UPDATE instituciones_educativas_v2_mejorada SET
                            numero_fya_secundario = ?
                        WHERE codigo_modular = ?
                    """, (
                        str(row.get('N° FYA', '')),
                        codigo_modular
                    ))
                    registros_fya += 1
                else:
                    # Insertar nuevo registro FyA
                    nombre = str(row.get('Institución Educativa', '')).strip()
                    tipo_institucion = 'RER' if 'RER' in nombre.upper() else 'IE'
                    
                    conn.execute("""
                        INSERT INTO instituciones_educativas_v2_mejorada (
                            codigo_modular, codigo_local, nombre_institucion, tipo_institucion,
                            region, provincia, distrito, direccion, centro_poblado,
                            nivel_educativo, es_fya, numero_fya_secundario, unidad_ejecutora, codigo_rie,
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
        print(f"\n📊 VERIFICANDO RESULTADOS MEJORADOS")
        print("-" * 40)
        
        total_registros = conn.execute("SELECT COUNT(*) FROM instituciones_educativas_v2_mejorada").fetchone()[0]
        total_fya = conn.execute("SELECT COUNT(*) FROM instituciones_educativas_v2_mejorada WHERE es_fya = 1").fetchone()[0]
        total_con_coordenadas = conn.execute("SELECT COUNT(*) FROM instituciones_educativas_v2_mejorada WHERE latitud IS NOT NULL").fetchone()[0]
        total_rurales = conn.execute("SELECT COUNT(*) FROM instituciones_educativas_v2_mejorada WHERE es_rural = 1").fetchone()[0]
        
        print(f"   📋 Total registros: {total_registros}")
        print(f"   🏫 Escuelas FyA: {total_fya}")
        print(f"   📍 Con coordenadas: {total_con_coordenadas}")
        print(f"   🌾 Instituciones rurales: {total_rurales}")
        
        # Mostrar distribución por modalidad específica
        print(f"\n📚 Distribución por modalidad específica:")
        modalidades = conn.execute("""
            SELECT modalidad_especifica, COUNT(*) as total 
            FROM instituciones_educativas_v2_mejorada 
            GROUP BY modalidad_especifica 
            ORDER BY total DESC
        """).fetchall()
        
        for modalidad, total in modalidades:
            print(f"   - {modalidad}: {total} instituciones")
        
        # Mostrar distribución por área de censo
        print(f"\n🌍 Distribución por área de censo:")
        areas_censo = conn.execute("""
            SELECT area_censo, COUNT(*) as total 
            FROM instituciones_educativas_v2_mejorada 
            GROUP BY area_censo 
            ORDER BY total DESC
        """).fetchall()
        
        for area, total in areas_censo:
            print(f"   - {area}: {total} instituciones")
        
        conn.close()
        
        print(f"\n✅ MIGRACIÓN V2.0 MEJORADA COMPLETADA EXITOSAMENTE")
        print("=" * 70)
        
        return True
        
    except Exception as e:
        print(f"❌ Error en migración V2.0 mejorada: {e}")
        conn.rollback()
        conn.close()
        return False

def main():
    """Función principal"""
    print("🚀 MIGRADOR V2.0 MEJORADO - INSTITUCIONES EDUCATIVAS")
    print("=" * 70)
    
    # 1. Crear estructura V2.0 mejorada
    if not crear_estructura_v2_mejorada():
        return
    
    # 2. Procesar fuente primaria
    df_datos_globales, df_escuelas_fya = procesar_fuente_primaria()
    if df_datos_globales is None:
        return
    
    # 3. Limpiar y transformar datos
    df_clean, df_fya_clean = limpiar_y_transformar_datos_mejorado(df_datos_globales, df_escuelas_fya)
    if df_clean is None:
        return
    
    # 4. Insertar datos en V2.0 mejorada
    if insertar_datos_v2_mejorado(df_clean, df_fya_clean):
        print(f"\n🎉 MIGRACIÓN V2.0 MEJORADA EXITOSA")
        print("=" * 70)
        print(f"💡 La nueva estructura mejorada está lista para análisis estadístico")
        print(f"📊 Incluye todos los campos adicionales importantes de la fuente primaria")
    else:
        print(f"\n❌ ERROR EN MIGRACIÓN V2.0 MEJORADA")

if __name__ == "__main__":
    main()
