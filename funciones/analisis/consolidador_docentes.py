#!/usr/bin/env python3
"""
Consolidador de Datos Docentes - Proyecto Reasis
Consolida datos de docentes de tablas 2023 y 2024 del archivo PADD Consolidado.xlsx
"""

import pandas as pd
import sqlite3
from pathlib import Path

def analizar_estructura_docentes():
    """Analizar estructura de los datos docentes en ambas hojas"""
    print("ANÁLISIS DE ESTRUCTURA - DATOS DOCENTES")
    print("=" * 60)
    
    # Ruta al archivo (ajustar según ubicación real)
    excel_path = Path("assets/Consultoria") # Necesitaremos la ruta exacta
    
    print("ESTRUCTURA IDENTIFICADA DESDE MUESTRA:")
    print("-" * 40)
    
    print("HOJA 2023:")
    print("- RER: Red Educativa Rural")
    print("- Nombres: Nombre del docente")
    print("- Apellidos: Apellidos del docente")
    print("- Número de documento: DNI")
    print("- Institución Educativa en la que brinda su servicio")
    print("- CÓDIGO MODULAR DE IIE")
    print("- SI CONTINÚA EN LA RER (SI/NO)")
    print("- EN QUÉ IIEE CONTINÚA")
    print("- CÓDIGO MODULAR DE LA IIEE EN LA QUE CONTINÚA")
    print("- Nivel: Nivel educativo")
    print("- MATEMATICA: Puntaje evaluación")
    print("- COMUNICACIÓN: Puntaje evaluación") 
    print("- DIGITAL: Puntaje evaluación")
    print("- GENERO: Género del docente")
    print("- ESTADO: Estado de evaluación")
    
    print("\nHOJA 2024:")
    print("- RER: Red Educativa Rural")
    print("- N°: Número correlativo")
    print("- DNI: Documento de identidad")
    print("- DOCENTES PARTICIPANTES: Nombre completo")
    print("- Institución Educativa en la que brinda su servicio")
    print("- CÓDIGO MODULAR DE IIE")
    print("- CONTINÚA EN LA RER (SI/NO)")
    print("- EN QUÉ IIEE CONTINÚA")
    print("- CÓDIGO MODULAR DE LA IIEE EN LA QUE CONTINÚA")
    print("- ESTADO: Estado de evaluación")
    
    return True

def diseñar_tabla_consolidada():
    """Diseñar estructura de tabla consolidada docentes_data"""
    print("\nDISEÑO DE TABLA CONSOLIDADA: docentes_data")
    print("=" * 60)
    
    estructura_sql = """
    CREATE TABLE docentes_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        
        -- Identificación del docente
        dni TEXT NOT NULL,
        nombres TEXT,
        apellidos TEXT,
        nombre_completo TEXT,
        genero TEXT,
        
        -- Información institucional
        rer TEXT,
        institucion_actual TEXT,
        codigo_modular_actual TEXT,
        nivel_educativo TEXT,
        
        -- Continuidad/Estabilidad
        continua_rer TEXT, -- SI/NO
        institucion_continua TEXT,
        codigo_modular_continua TEXT,
        
        -- Evaluaciones académicas (solo 2023)
        puntaje_matematica INTEGER,
        puntaje_comunicacion INTEGER,
        puntaje_digital INTEGER,
        
        -- Estado y año
        estado_evaluacion TEXT,
        año INTEGER NOT NULL,
        
        -- Vinculación con tabla instituciones
        codigo_modular_vinculado TEXT, -- Para vincular con instituciones_educativas
        metodo_vinculacion TEXT,
        
        -- Campos de control
        archivo_origen TEXT,
        fecha_procesamiento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        
        -- Índices únicos
        UNIQUE(dni, año)
    )
    """
    
    print("ESTRUCTURA SQL PROPUESTA:")
    print(estructura_sql)
    
    print("\nCRITERIOS DE DISEÑO:")
    print("- dni + año como clave única (un docente por año)")
    print("- Campos flexibles para nombres (2023 separado, 2024 completo)")
    print("- Evaluaciones académicas solo disponibles en 2023")
    print("- Campo codigo_modular_vinculado para linking con instituciones_educativas")
    print("- Campos de control para trazabilidad")
    
    return estructura_sql

def mapeo_campos():
    """Definir mapeo entre hojas 2023/2024 y tabla consolidada"""
    print("\nMAPEO DE CAMPOS:")
    print("=" * 60)
    
    mapeo_2023 = {
        'dni': 'Número de documento',
        'nombres': 'Nombres',
        'apellidos': 'Apellidos', 
        'nombre_completo': 'CONCAT(Nombres, " ", Apellidos)',
        'genero': 'GENERO',
        'rer': 'RER',
        'institucion_actual': 'Institución Educativa en la que brinda su servicio',
        'codigo_modular_actual': 'CÓDIGO MODULAR DE IIE',
        'nivel_educativo': 'Nivel',
        'continua_rer': 'SI CONTINÚA EN LA RER (SI/NO)',
        'institucion_continua': 'EN QUÉ IIEE CONTINÚA',
        'codigo_modular_continua': 'CÓDIGO MODULAR DE LA IIEE EN LA QUE CONTINÚA',
        'puntaje_matematica': 'MATEMATICA',
        'puntaje_comunicacion': 'COMUNICACIÓN',
        'puntaje_digital': 'DIGITAL',
        'estado_evaluacion': 'ESTADO',
        'año': '2023'
    }
    
    mapeo_2024 = {
        'dni': 'DNI',
        'nombres': 'SPLIT(DOCENTES PARTICIPANTES, " ")[0]',
        'apellidos': 'SPLIT(DOCENTES PARTICIPANTES, " ")[1:]',
        'nombre_completo': 'DOCENTES PARTICIPANTES',
        'genero': 'NULL',
        'rer': 'RER',
        'institucion_actual': 'Institución Educativa en la que brinda su servicio',
        'codigo_modular_actual': 'CÓDIGO MODULAR DE IIE',
        'nivel_educativo': 'NULL',
        'continua_rer': 'CONTINÚA EN LA RER (SI/NO)',
        'institucion_continua': 'EN QUÉ IIEE CONTINÚA',
        'codigo_modular_continua': 'CÓDIGO MODULAR DE LA IIEE EN LA QUE CONTINÚA',
        'puntaje_matematica': 'NULL',
        'puntaje_comunicacion': 'NULL', 
        'puntaje_digital': 'NULL',
        'estado_evaluacion': 'ESTADO',
        'año': '2024'
    }
    
    print("MAPEO 2023:")
    for campo_destino, campo_origen in mapeo_2023.items():
        print(f"  {campo_destino:25} <- {campo_origen}")
        
    print("\nMAPEO 2024:")
    for campo_destino, campo_origen in mapeo_2024.items():
        print(f"  {campo_destino:25} <- {campo_origen}")
    
    return mapeo_2023, mapeo_2024

def crear_tabla_docentes():
    """Crear tabla docentes_data en la base de datos"""
    print("\nCREANDO TABLA docentes_data")
    print("=" * 40)
    
    conn = sqlite3.connect('reasis_database.db')
    
    # Eliminar tabla anterior si existe
    conn.execute('DROP TABLE IF EXISTS docentes_data')
    
    # Crear nueva tabla
    create_sql = """
    CREATE TABLE docentes_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        
        -- Identificación del docente
        dni TEXT NOT NULL,
        nombres TEXT,
        apellidos TEXT,
        nombre_completo TEXT,
        genero TEXT,
        
        -- Información institucional
        rer TEXT,
        institucion_actual TEXT,
        codigo_modular_actual TEXT,
        nivel_educativo TEXT,
        
        -- Continuidad/Estabilidad
        continua_rer TEXT,
        institucion_continua TEXT,
        codigo_modular_continua TEXT,
        
        -- Evaluaciones académicas (solo 2023)
        puntaje_matematica INTEGER,
        puntaje_comunicacion INTEGER,
        puntaje_digital INTEGER,
        
        -- Estado y año
        estado_evaluacion TEXT,
        año INTEGER NOT NULL,
        
        -- Vinculación con tabla instituciones
        codigo_modular_vinculado TEXT,
        metodo_vinculacion TEXT,
        
        -- Campos de control
        archivo_origen TEXT,
        fecha_procesamiento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        
        -- Índices únicos
        UNIQUE(dni, año)
    )
    """
    
    conn.execute(create_sql)
    
    # Crear índices
    indices = [
        'CREATE INDEX idx_docentes_dni ON docentes_data(dni)',
        'CREATE INDEX idx_docentes_codigo_modular ON docentes_data(codigo_modular_actual)',
        'CREATE INDEX idx_docentes_año ON docentes_data(año)',
        'CREATE INDEX idx_docentes_rer ON docentes_data(rer)'
    ]
    
    for idx_sql in indices:
        conn.execute(idx_sql)
    
    conn.commit()
    conn.close()
    
    print("✅ Tabla docentes_data creada exitosamente")
    print("✅ Índices creados para optimización")

def planificar_consolidacion():
    """Planificar el proceso de consolidación"""
    print("\nPLAN DE CONSOLIDACIÓN:")
    print("=" * 60)
    
    print("FASE 1: Preparación")
    print("- ✅ Analizar estructura de datos")
    print("- ✅ Diseñar tabla consolidada") 
    print("- ✅ Definir mapeo de campos")
    print("- ✅ Crear tabla en base de datos")
    
    print("\nFASE 2: Extracción (Próxima)")
    print("- 🔄 Leer hoja '2023' del archivo PADD Consolidado.xlsx")
    print("- 🔄 Leer hoja '2024' del archivo PADD Consolidado.xlsx")
    print("- 🔄 Normalizar y limpiar datos")
    print("- 🔄 Aplicar mapeo de campos")
    
    print("\nFASE 3: Consolidación (Próxima)")
    print("- 🔄 Insertar datos 2023 en docentes_data")
    print("- 🔄 Insertar datos 2024 en docentes_data")
    print("- 🔄 Validar unicidad (dni, año)")
    print("- 🔄 Generar reporte de consolidación")
    
    print("\nFASE 4: Vinculación (Próxima)")
    print("- 🔄 Vincular con tabla instituciones_educativas")
    print("- 🔄 Usar codigo_modular_actual para matching")
    print("- 🔄 Aplicar estrategias alternativas si es necesario")
    print("- 🔄 Calcular métricas de vinculación")
    
    print("\nFASE 5: Variables Docentes (Próxima)")
    print("- 🔄 Calcular X4: Índice de Desempeño Docente (IDD)")
    print("- 🔄 Calcular X5: Estabilidad Docente (ED)")
    print("- 🔄 Preparar para X6: Competencia Digital Docente (CDD)")
    
    return True

def main():
    """Función principal - Fase de análisis y preparación"""
    print("CONSOLIDADOR DE DATOS DOCENTES - PROYECTO REASIS")
    print("FASE 1: ANÁLISIS Y PREPARACIÓN")
    print("=" * 70)
    
    # Análisis de estructura
    analizar_estructura_docentes()
    
    # Diseño de tabla
    estructura = diseñar_tabla_consolidada()
    
    # Mapeo de campos
    mapeo_2023, mapeo_2024 = mapeo_campos()
    
    # Creación de tabla
    crear_tabla_docentes()
    
    # Planificación
    planificar_consolidacion()
    
    print(f"\n🎯 FASE 1 COMPLETADA")
    print(f"Tabla docentes_data lista para consolidación")
    print(f"Próximo paso: Implementar extracción desde Excel")
    
    return True

if __name__ == "__main__":
    main()