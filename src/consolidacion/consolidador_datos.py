#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Consolidador de Datos - Proyecto Reasis
Script para consolidar todos los datos Excel en una base de datos SQLite
"""

import os
import pandas as pd
import sqlite3
from pathlib import Path
import numpy as np
from datetime import datetime

class ConsolidadorDatos:
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
                    region TEXT,
                    provincia TEXT,
                    distrito TEXT,
                    rural BOOLEAN,
                    eib BOOLEAN,
                    toe BOOLEAN,
                    red_educativa TEXT,
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
            
            'indicadores_infraestructura_base': '''
                CREATE TABLE IF NOT EXISTS indicadores_infraestructura_base (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    institucion_id INTEGER,
                    año INTEGER,
                    tiene_internet BOOLEAN,
                    velocidad_internet REAL,
                    computadoras_funcionando INTEGER,
                    computadoras_por_estudiante REAL,
                    tiene_laboratorio_computo BOOLEAN,
                    tiene_proyector BOOLEAN,
                    tiene_pizarra_digital BOOLEAN,
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
    
    def procesar_instituciones(self):
        """Procesa los datos de instituciones educativas"""
        print("\n🏫 PROCESANDO DATOS DE INSTITUCIONES...")
        print("=" * 50)
        
        # Archivos con datos de instituciones
        archivos_instituciones = [
            "DatosLucas/Matematica y Comunicación/BD1- Matemática 2024.xlsx",
            "DatosLucas/Matematica y Comunicación/BD2- Comunicación 2024.xlsx",
            "DatosLucas/Matematica y Comunicación/BD3 - Producción de textos 2024.xlsx",
            "Información actualizada/1. Ruralidad, EIB y TOE.xlsx"
        ]
        
        instituciones_procesadas = set()
        
        for archivo_relativo in archivos_instituciones:
            archivo_path = self.base_path / archivo_relativo
            if not archivo_path.exists():
                continue
                
            print(f"\n📊 Procesando: {archivo_path.name}")
            
            try:
                # Leer todas las hojas del archivo
                excel_file = pd.ExcelFile(archivo_path)
                
                for hoja in excel_file.sheet_names:
                    if 'colegio' in hoja.lower() or 'institucion' in hoja.lower():
                        print(f"   📋 Procesando hoja: {hoja}")
                        
                        # Leer TODAS las filas de la hoja
                        df = pd.read_excel(archivo_path, sheet_name=hoja)
                        print(f"      Filas encontradas: {len(df)}")
                        
                        # Procesar cada fila
                        for index, row in df.iterrows():
                            try:
                                # Extraer datos de institución
                                nombre_inst = str(row.get('Institución Educativa', row.get('Nombre a reemplazar', '')))
                                region = str(row.get('Región', ''))
                                año = row.get('Año', 2024)
                                
                                if nombre_inst and nombre_inst != 'nan':
                                    # Crear código único
                                    codigo_inst = f"{nombre_inst}_{region}_{año}".replace(' ', '_')
                                    
                                    if codigo_inst not in instituciones_procesadas:
                                        # Insertar en base de datos
                                        cursor = self.conn.cursor()
                                        cursor.execute('''
                                            INSERT OR IGNORE INTO instituciones_educativas 
                                            (codigo_institucion, nombre_institucion, region, año)
                                            VALUES (?, ?, ?, ?)
                                        ''', (codigo_inst, nombre_inst, region, año))
                                        
                                        instituciones_procesadas.add(codigo_inst)
                                        print(f"      ✅ Institución agregada: {nombre_inst}")
                                        
                            except Exception as e:
                                print(f"      ❌ Error procesando fila {index}: {e}")
                                
            except Exception as e:
                print(f"❌ Error procesando {archivo_path.name}: {e}")
        
        print(f"\n✅ Total de instituciones procesadas: {len(instituciones_procesadas)}")
    
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
                        
                        # Buscar ID de institución
                        cursor = self.conn.cursor()
                        cursor.execute('''
                            SELECT id FROM instituciones_educativas 
                            WHERE nombre_institucion = ? AND año = ?
                        ''', (nombre_inst, año))
                        
                        result = cursor.fetchone()
                        if result:
                            institucion_id = result[0]
                            
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
    
    def procesar_competencia_digital(self):
        """Procesa los datos de competencia digital"""
        print("\n💻 PROCESANDO DATOS DE COMPETENCIA DIGITAL...")
        print("=" * 50)
        
        archivos_digitales = [
            ("DatosLucas/Competencias Digitales Estudiantes/BD1 - 2024 Competencias Digitales - Estudiantes.xlsx", "estudiantes"),
            ("DatosLucas/Competencias Digitales Docentes/02 Base de datos Informe Docentes Digital  2025 - RER Rural.xlsx", "docentes")
        ]
        
        for archivo_relativo, tipo in archivos_digitales:
            archivo_path = self.base_path / archivo_relativo
            if not archivo_path.exists():
                continue
                
            print(f"\n📊 Procesando competencia digital ({tipo}): {archivo_path.name}")
            
            try:
                # Leer hoja DATA
                df = pd.read_excel(archivo_path, sheet_name='DATA')
                print(f"   📋 Filas en DATA: {len(df)}")
                
                # Procesar cada fila
                for index, row in df.iterrows():
                    try:
                        # Extraer datos de competencia digital
                        nombre_inst = str(row.get('Institución Educativa', ''))
                        año = 2024
                        
                        # Buscar ID de institución
                        cursor = self.conn.cursor()
                        cursor.execute('''
                            SELECT id FROM instituciones_educativas 
                            WHERE nombre_institucion = ? AND año = ?
                        ''', (nombre_inst, año))
                        
                        result = cursor.fetchone()
                        if result:
                            institucion_id = result[0]
                            
                            # Procesar columnas de preguntas (excluir columnas de identificación)
                            for columna in df.columns:
                                if 'pregunta' in columna.lower() or 'competencia' in columna.lower():
                                    respuesta = str(row.get(columna, ''))
                                    if respuesta and respuesta != 'nan':
                                        cursor.execute('''
                                            INSERT INTO datos_competencia_digital 
                                            (institucion_id, año, tipo_encuesta, pregunta, respuesta)
                                            VALUES (?, ?, ?, ?, ?)
                                        ''', (institucion_id, año, tipo, columna, respuesta))
                            
                            print(f"      ✅ Datos de competencia digital agregados para: {nombre_inst}")
                            
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
            'indicadores_infraestructura_base',
            'datos_competencia_digital'
        ]
        
        for tabla in tablas:
            cursor.execute(f"SELECT COUNT(*) FROM {tabla}")
            count = cursor.fetchone()[0]
            print(f"   📋 {tabla}: {count} registros")
        
        # Mostrar algunas instituciones como ejemplo
        cursor.execute("SELECT nombre_institucion, region FROM instituciones_educativas LIMIT 5")
        instituciones = cursor.fetchall()
        
        print(f"\n🏫 Ejemplos de instituciones procesadas:")
        for inst in instituciones:
            print(f"   - {inst[0]} ({inst[1]})")
        
        print(f"\n✅ CONSOLIDACIÓN COMPLETADA")
        print("=" * 50)
        print(f"📄 Base de datos: {self.db_path}")
        print("📝 Próximos pasos:")
        print("   1. Revisar la calidad de los datos consolidados")
        print("   2. Crear análisis estadístico")
        print("   3. Generar visualizaciones")
        print("   4. Crear informe automatizado")

def main():
    """Función principal del consolidador"""
    print("🚀 CONSOLIDADOR DE DATOS - PROYECTO REASIS")
    print("=" * 60)
    
    consolidador = ConsolidadorDatos()
    
    # Paso 1: Crear base de datos
    consolidador.crear_base_datos()
    
    # Paso 2: Procesar instituciones
    consolidador.procesar_instituciones()
    
    # Paso 3: Procesar datos académicos
    consolidador.procesar_datos_academicos()
    
    # Paso 4: Procesar competencia digital
    consolidador.procesar_competencia_digital()
    
    # Paso 5: Generar reporte
    consolidador.generar_reporte_consolidacion()
    
    # Cerrar conexión
    if consolidador.conn:
        consolidador.conn.close()

if __name__ == "__main__":
    main()
