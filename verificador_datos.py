#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verificador de Datos - Proyecto Reasis
Script para verificar directamente los datos en la base de datos
"""

import sqlite3
import pandas as pd
from pathlib import Path

def verificar_datos():
    """Verifica los datos en la base de datos"""
    print("🔍 VERIFICADOR DE DATOS - PROYECTO REASIS")
    print("=" * 60)
    
    db_path = "reasis_database.db"
    
    if not Path(db_path).exists():
        print(f"❌ Base de datos no encontrada: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        
        # Verificar tablas
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tablas = cursor.fetchall()
        
        print(f"📋 TABLAS ENCONTRADAS:")
        for tabla in tablas:
            print(f"   - {tabla[0]}")
        
        print(f"\n📊 CONTEO DE REGISTROS:")
        
        # Contar registros en cada tabla
        for tabla in tablas:
            nombre_tabla = tabla[0]
            cursor.execute(f"SELECT COUNT(*) FROM {nombre_tabla}")
            count = cursor.fetchone()[0]
            print(f"   {nombre_tabla}: {count} registros")
        
        # Verificar datos específicos
        print(f"\n🔍 VERIFICACIÓN ESPECÍFICA:")
        
        # Verificar instituciones
        cursor.execute("SELECT COUNT(*) FROM instituciones_educativas")
        inst_count = cursor.fetchone()[0]
        print(f"   Instituciones educativas: {inst_count}")
        
        if inst_count > 0:
            cursor.execute("SELECT nombre_institucion, nombre_rer, año FROM instituciones_educativas LIMIT 3")
            instituciones = cursor.fetchall()
            print(f"   Ejemplos:")
            for inst in instituciones:
                nombre = inst[0] if inst[0] else inst[1]
                print(f"     - {nombre} ({inst[2]})")
        
        # Verificar datos académicos
        cursor.execute("SELECT COUNT(*) FROM indicadores_academicos_base")
        acad_count = cursor.fetchone()[0]
        print(f"   Datos académicos: {acad_count}")
        
        if acad_count > 0:
            cursor.execute("SELECT materia, COUNT(*) FROM indicadores_academicos_base GROUP BY materia")
            materias = cursor.fetchall()
            print(f"   Por materia:")
            for materia in materias:
                print(f"     - {materia[0]}: {materia[1]} registros")
        
        # Verificar competencia digital
        cursor.execute("SELECT COUNT(*) FROM datos_competencia_digital")
        comp_count = cursor.fetchone()[0]
        print(f"   Datos competencia digital: {comp_count}")
        
        if comp_count > 0:
            cursor.execute("SELECT tipo_encuesta, COUNT(*) FROM datos_competencia_digital GROUP BY tipo_encuesta")
            tipos = cursor.fetchall()
            print(f"   Por tipo:")
            for tipo in tipos:
                print(f"     - {tipo[0]}: {tipo[1]} registros")
        
        conn.close()
        
        print(f"\n✅ VERIFICACIÓN COMPLETADA")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Error verificando datos: {e}")

if __name__ == "__main__":
    verificar_datos()
