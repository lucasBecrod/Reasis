#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Consolidador Mejorado - Proyecto Reasis
Script para consolidar datos usando los nombres de columnas correctos
"""

import os
import pandas as pd
import sqlite3
from pathlib import Path
import numpy as np
from datetime import datetime

class ConsolidadorMejorado:
    def __init__(self):
        self.base_path = Path("assets/Consultoria")
        self.db_path = "reasis_database.db"
        self.conn = None
        
    def crear_base_datos(self):
        """Crea la base de datos SQLite con las tablas necesarias"""
        print("🗄️ CREANDO BASE DE DATOS...")
        print("=" * 50)
        
        self.conn = sqlite3.connect(self.db_path)
        
        # Crear tablas principales
        tablas = {
            'instituciones_educativas': '''
                CREATE TABLE IF NOT EXISTS instituciones_educativas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    codigo_institucion TEXT,
                    nombre_institucion TEXT,
                    nombre_rer TEXT,
                    region TEXT,
                    provincia TEXT,
                    distrito TEXT,
                    rural BOOLEAN,
                    eib BOOLEAN,
                    toe BOOLEAN,
                    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''',
            
            'indicadores_academicos_base': '''
                CREATE TABLE IF NOT EXISTS indicadores_academicos_base (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    institucion_id INTEGER,
                    año INTEGER,
                    materia TEXT,
                    nivel_educativo TEXT,
                    grado TEXT,
                    total_estudiantes INTEGER,
                    estudiantes_aprobados INTEGER,
                    estudiantes_desaprobados INTEGER,
                    promedio_notas REAL,
                    porcentaje_aprobacion REAL,
                    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (institucion_id) REFERENCES instituciones_educativas(id)
                )
            ''',
            
            'indicadores_docentes_base': '''
                CREATE TABLE IF NOT EXISTS indicadores_docentes_base (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    institucion_id INTEGER,
                    año INTEGER,
                    total_docentes INTEGER,
                    docentes_contratados INTEGER,
                    docentes_nombrados INTEGER,
                    docentes_con_formacion_eib INTEGER,
                    docentes_con_competencia_digital REAL,
                    promedio_edad_docentes REAL,
                    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (institucion_id) REFERENCES instituciones_educativas(id)
                )
            ''',
            
            'datos_competencia_digital': '''
                CREATE TABLE IF NOT EXISTS datos_competencia_digital (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    institucion_id INTEGER,
                    año INTEGER,
                    tipo_encuesta TEXT, -- 'docentes' o 'estudiantes'
                    pregunta TEXT,
                    respuesta TEXT,
                    puntuacion REAL,
                    ambito TEXT,
                    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (institucion_id) REFERENCES instituciones_educativas(id)
                )
            '''
        }
        
        cursor = self.conn.cursor()
        for nombre_tabla, sql in tablas.items():
            cursor.execute(sql)
            print(f"   ✅ Tabla '{nombre_tabla}' creada")
        
        self.conn.commit()
        print(f"✅ Base de datos '{self.db_path}' creada exitosamente")
    
    def procesar_competencia_digital_docentes(self):
        """Procesa los datos de competencia digital de docentes"""
        print("\n💻 PROCESANDO COMPETENCIA DIGITAL DOCENTES...")
        print("=" * 50)
        
        archivo_path = self.base_path / "DatosLucas/Competencias Digitales Docentes/02 Base de datos Informe Docentes Digital  2025 - RER Rural.xlsx"
        
        if not archivo_path.exists():
            print(f"❌ Archivo no encontrado: {archivo_path}")
            return
        
        try:
            # Leer hoja DATA que contiene los datos principales
            df = pd.read_excel(archivo_path, sheet_name='DATA')
            print(f"   📋 Filas en DATA: {len(df)}")
            
            # Procesar cada fila
            for index, row in df.iterrows():
                try:
                    # Extraer datos básicos
                    nombre_rer = str(row.get('Nombre de la RER', ''))
                    año = row.get('Año', 2023)
                    ambito = str(row.get('Ambito', ''))
                    puntuacion = row.get('Puntuación', 0)
                    
                    if nombre_rer and nombre_rer != 'nan':
                        # Buscar o crear institución
                        cursor = self.conn.cursor()
                        cursor.execute('''
                            SELECT id FROM instituciones_educativas 
                            WHERE nombre_rer = ? AND año = ?
                        ''', (nombre_rer, año))
                        
                        result = cursor.fetchone()
                        if result:
                            institucion_id = result[0]
                        else:
                            # Crear nueva institución
                            cursor.execute('''
                                INSERT INTO instituciones_educativas 
                                (nombre_rer, año, ambito)
                                VALUES (?, ?, ?)
                            ''', (nombre_rer, año, ambito))
                            institucion_id = cursor.lastrowid
                        
                        # Procesar columnas de preguntas (excluir columnas de identificación)
                        columnas_excluir = ['Marca temporal', 'Año', 'Ambito', 'Puntuación', 'Nombre de la RER', 
                                          'Edad', 'Rango edad', 'Sexo', 'Nota Global %', 'Nota Global Relativa']
                        
                        for columna in df.columns:
                            if columna not in columnas_excluir and not columna.startswith('Unnamed'):
                                respuesta = str(row.get(columna, ''))
                                if respuesta and respuesta != 'nan' and respuesta != '':
                                    cursor.execute('''
                                        INSERT INTO datos_competencia_digital 
                                        (institucion_id, año, tipo_encuesta, pregunta, respuesta, ambito)
                                        VALUES (?, ?, ?, ?, ?, ?)
                                    ''', (institucion_id, año, 'docentes', columna, respuesta, ambito))
                        
                        print(f"      ✅ Datos de competencia digital agregados para: {nombre_rer}")
                        
                except Exception as e:
                    print(f"      ❌ Error procesando fila {index}: {e}")
                    
        except Exception as e:
            print(f"❌ Error procesando {archivo_path.name}: {e}")
    
    def procesar_competencia_digital_estudiantes(self):
        """Procesa los datos de competencia digital de estudiantes"""
        print("\n💻 PROCESANDO COMPETENCIA DIGITAL ESTUDIANTES...")
        print("=" * 50)
        
        archivo_path = self.base_path / "DatosLucas/Competencias Digitales Estudiantes/BD1 - 2024 Competencias Digitales - Estudiantes.xlsx"
        
        if not archivo_path.exists():
            print(f"❌ Archivo no encontrado: {archivo_path}")
            return
        
        try:
            # Leer hoja DATA que contiene los datos principales
            df = pd.read_excel(archivo_path, sheet_name='DATA')
            print(f"   📋 Filas en DATA: {len(df)}")
            
            # Procesar cada fila
            for index, row in df.iterrows():
                try:
                    # Extraer datos básicos
                    nombre_inst = str(row.get('Nombre de la IIEE', ''))
                    año = 2024  # Asumimos 2024 para estudiantes
                    
                    if nombre_inst and nombre_inst != 'nan':
                        # Buscar o crear institución
                        cursor = self.conn.cursor()
                        cursor.execute('''
                            SELECT id FROM instituciones_educativas 
                            WHERE nombre_institucion = ? AND año = ?
                        ''', (nombre_inst, año))
                        
                        result = cursor.fetchone()
                        if result:
                            institucion_id = result[0]
                        else:
                            # Crear nueva institución
                            cursor.execute('''
                                INSERT INTO instituciones_educativas 
                                (nombre_institucion, año)
                                VALUES (?, ?)
                            ''', (nombre_inst, año))
                            institucion_id = cursor.lastrowid
                        
                        # Procesar columnas de preguntas (excluir columnas de identificación)
                        columnas_excluir = ['Marca temporal', 'Nombre de la IIEE', 'Edad', 'Sexo']
                        
                        for columna in df.columns:
                            if columna not in columnas_excluir and not columna.startswith('Unnamed'):
                                respuesta = str(row.get(columna, ''))
                                if respuesta and respuesta != 'nan' and respuesta != '':
                                    cursor.execute('''
                                        INSERT INTO datos_competencia_digital 
                                        (institucion_id, año, tipo_encuesta, pregunta, respuesta)
                                        VALUES (?, ?, ?, ?, ?)
                                    ''', (institucion_id, año, 'estudiantes', columna, respuesta))
                        
                        print(f"      ✅ Datos de competencia digital agregados para: {nombre_inst}")
                        
                except Exception as e:
                    print(f"      ❌ Error procesando fila {index}: {e}")
                    
        except Exception as e:
            print(f"❌ Error procesando {archivo_path.name}: {e}")
    
    def procesar_datos_academicos(self):
        """Procesa los datos académicos (matemática, comunicación)"""
        print("\n📚 PROCESANDO DATOS ACADÉMICOS...")
        print("=" * 50)
        
        archivos_academicos = [
            ("DatosLucas/Matematica y Comunicación/BD1- Matemática 2024.xlsx", "Matemática"),
            ("DatosLucas/Matematica y Comunicación/BD2- Comunicación 2024.xlsx", "Comunicación"),
            ("DatosLucas/Matematica y Comunicación/BD3 - Producción de textos 2024.xlsx", "Producción de textos")
        ]
        
        for archivo_relativo, materia in archivos_academicos:
            archivo_path = self.base_path / archivo_relativo
            if not archivo_path.exists():
                continue
                
            print(f"\n📊 Procesando {materia}: {archivo_path.name}")
            
            try:
                # Leer hoja DATA que contiene los datos principales
                df = pd.read_excel(archivo_path, sheet_name='DATA')
                print(f"   📋 Filas en DATA: {len(df)}")
                
                # Procesar cada fila
                for index, row in df.iterrows():
                    try:
                        # Extraer datos académicos
                        nombre_inst = str(row.get('Institución Educativa', ''))
                        año = row.get('Año', 2024)
                        nivel = str(row.get('Nivel', ''))
                        grado = str(row.get('Grado', ''))
                        
                        if nombre_inst and nombre_inst != 'nan':
                            # Buscar o crear institución
                            cursor = self.conn.cursor()
                            cursor.execute('''
                                SELECT id FROM instituciones_educativas 
                                WHERE nombre_institucion = ? AND año = ?
                            ''', (nombre_inst, año))
                            
                            result = cursor.fetchone()
                            if result:
                                institucion_id = result[0]
                            else:
                                # Crear nueva institución
                                cursor.execute('''
                                    INSERT INTO instituciones_educativas 
                                    (nombre_institucion, año)
                                    VALUES (?, ?)
                                ''', (nombre_inst, año))
                                institucion_id = cursor.lastrowid
                            
                            # Insertar datos académicos
                            cursor.execute('''
                                INSERT INTO indicadores_academicos_base 
                                (institucion_id, año, materia, nivel_educativo, grado)
                                VALUES (?, ?, ?, ?, ?)
                            ''', (institucion_id, año, materia, nivel, grado))
                            
                            print(f"      ✅ Datos académicos agregados para: {nombre_inst}")
                            
                    except Exception as e:
                        print(f"      ❌ Error procesando fila {index}: {e}")
                        
            except Exception as e:
                print(f"❌ Error procesando {archivo_path.name}: {e}")
    
    def generar_reporte_consolidacion(self):
        """Genera un reporte de la consolidación realizada"""
        print("\n📊 REPORTE DE CONSOLIDACIÓN")
        print("=" * 50)
        
        cursor = self.conn.cursor()
        
        # Contar registros en cada tabla
        tablas = [
            'instituciones_educativas',
            'indicadores_academicos_base', 
            'indicadores_docentes_base',
            'datos_competencia_digital'
        ]
        
        for tabla in tablas:
            cursor.execute(f"SELECT COUNT(*) FROM {tabla}")
            count = cursor.fetchone()[0]
            print(f"   📋 {tabla}: {count} registros")
        
        # Mostrar algunas instituciones como ejemplo
        cursor.execute("SELECT nombre_institucion, nombre_rer, año FROM instituciones_educativas LIMIT 5")
        instituciones = cursor.fetchall()
        
        print(f"\n🏫 Ejemplos de instituciones procesadas:")
        for inst in instituciones:
            nombre = inst[0] if inst[0] else inst[1]
            print(f"   - {nombre} ({inst[2]})")
        
        print(f"\n✅ CONSOLIDACIÓN COMPLETADA")
        print("=" * 50)
        print(f"📄 Base de datos: {self.db_path}")
        print("📝 Próximos pasos:")
        print("   1. Revisar la calidad de los datos consolidados")
        print("   2. Crear análisis estadístico")
        print("   3. Generar visualizaciones")
        print("   4. Crear informe automatizado")

def main():
    """Función principal del consolidador mejorado"""
    print("🚀 CONSOLIDADOR MEJORADO - PROYECTO REASIS")
    print("=" * 60)
    
    consolidador = ConsolidadorMejorado()
    
    # Paso 1: Crear base de datos
    consolidador.crear_base_datos()
    
    # Paso 2: Procesar competencia digital docentes
    consolidador.procesar_competencia_digital_docentes()
    
    # Paso 3: Procesar competencia digital estudiantes
    consolidador.procesar_competencia_digital_estudiantes()
    
    # Paso 4: Procesar datos académicos
    consolidador.procesar_datos_academicos()
    
    # Paso 5: Generar reporte
    consolidador.generar_reporte_consolidacion()
    
    # Cerrar conexión
    if consolidador.conn:
        consolidador.conn.close()

if __name__ == "__main__":
    main()
