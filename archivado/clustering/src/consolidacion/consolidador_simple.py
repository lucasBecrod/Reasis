#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Consolidador Simple - Proyecto Reasis
Script simple para consolidar datos paso a paso
"""

import os
import pandas as pd
import sqlite3
from pathlib import Path
import numpy as np
from datetime import datetime

def crear_base_datos():
    """Crea la base de datos SQLite con las tablas necesarias"""
    print("🗄️ CREANDO BASE DE DATOS...")
    print("=" * 50)
    
    conn = sqlite3.connect("reasis_database.db")
    
    # Crear tabla de instituciones
    conn.execute('''
        CREATE TABLE IF NOT EXISTS instituciones_educativas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre_institucion TEXT,
            nombre_rer TEXT,
            año INTEGER,
            ambito TEXT,
            fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Crear tabla de datos de competencia digital
    conn.execute('''
        CREATE TABLE IF NOT EXISTS datos_competencia_digital (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            institucion_id INTEGER,
            año INTEGER,
            tipo_encuesta TEXT,
            pregunta TEXT,
            respuesta TEXT,
            ambito TEXT,
            fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (institucion_id) REFERENCES instituciones_educativas(id)
        )
    ''')
    
    # Crear tabla de datos académicos
    conn.execute('''
        CREATE TABLE IF NOT EXISTS indicadores_academicos_base (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            institucion_id INTEGER,
            año INTEGER,
            materia TEXT,
            nivel_educativo TEXT,
            grado TEXT,
            fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (institucion_id) REFERENCES instituciones_educativas(id)
        )
    ''')
    
    conn.commit()
    print("✅ Base de datos creada exitosamente")
    return conn

def procesar_competencia_digital_docentes(conn):
    """Procesa los datos de competencia digital de docentes"""
    print("\n💻 PROCESANDO COMPETENCIA DIGITAL DOCENTES...")
    print("=" * 50)
    
    archivo_path = Path("assets/Consultoria/DatosLucas/Competencias Digitales Docentes/02 Base de datos Informe Docentes Digital  2025 - RER Rural.xlsx")
    
    if not archivo_path.exists():
        print(f"❌ Archivo no encontrado: {archivo_path}")
        return
    
    try:
        # Leer hoja DATA
        df = pd.read_excel(archivo_path, sheet_name='DATA')
        print(f"   📋 Filas en DATA: {len(df)}")
        
        # Mostrar las primeras columnas para verificar
        print(f"   📊 Columnas disponibles: {list(df.columns[:10])}")
        
        # Procesar cada fila
        for index, row in df.iterrows():
            try:
                # Extraer datos básicos
                nombre_rer = str(row.get('Nombre de la RER', ''))
                año = row.get('Año', 2023)
                ambito = str(row.get('Ambito', ''))
                
                if nombre_rer and nombre_rer != 'nan':
                    # Buscar o crear institución
                    cursor = conn.cursor()
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
                    
                    if index % 100 == 0:  # Mostrar progreso cada 100 filas
                        print(f"      ✅ Procesadas {index} filas...")
                        
            except Exception as e:
                print(f"      ❌ Error procesando fila {index}: {e}")
                break  # Salir si hay muchos errores
                
    except Exception as e:
        print(f"❌ Error procesando {archivo_path.name}: {e}")

def generar_reporte_final(conn):
    """Genera un reporte final de la consolidación"""
    print("\n📊 REPORTE FINAL DE CONSOLIDACIÓN")
    print("=" * 50)
    
    cursor = conn.cursor()
    
    # Contar registros en cada tabla
    tablas = [
        'instituciones_educativas',
        'indicadores_academicos_base', 
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
    print("📄 Base de datos: reasis_database.db")
    print("📝 Próximos pasos:")
    print("   1. Revisar la calidad de los datos consolidados")
    print("   2. Crear análisis estadístico")
    print("   3. Generar visualizaciones")
    print("   4. Crear informe automatizado")

def main():
    """Función principal"""
    print("🚀 CONSOLIDADOR SIMPLE - PROYECTO REASIS")
    print("=" * 60)
    
    # Paso 1: Crear base de datos
    conn = crear_base_datos()
    
    # Paso 2: Procesar competencia digital docentes
    procesar_competencia_digital_docentes(conn)
    
    # Paso 3: Generar reporte
    generar_reporte_final(conn)
    
    # Cerrar conexión
    conn.close()

if __name__ == "__main__":
    main()
