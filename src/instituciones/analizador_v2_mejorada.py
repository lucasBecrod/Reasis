#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analizador V2.0 Mejorada - Instituciones Educativas - Proyecto Reasis
Script para analizar y mostrar la estructura V2.0 mejorada con todos los campos adicionales
"""

import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path

def mostrar_estructura_v2_mejorada():
    """Muestra la estructura y datos de la nueva tabla V2.0 mejorada"""
    print("📊 ANALIZADOR V2.0 MEJORADA - INSTITUCIONES EDUCATIVAS")
    print("=" * 70)
    
    db_path = "reasis_database.db"
    
    if not Path(db_path).exists():
        print(f"❌ Base de datos no encontrada: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        
        # 1. INFORMACIÓN GENERAL
        print(f"\n📋 INFORMACIÓN GENERAL")
        print("=" * 50)
        
        total_registros = conn.execute("SELECT COUNT(*) FROM instituciones_educativas_v2_mejorada").fetchone()[0]
        print(f"   📊 Total instituciones: {total_registros}")
        
        # Verificar campos completos
        campos_completos = conn.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN codigo_modular IS NOT NULL AND codigo_modular != '' THEN 1 ELSE 0 END) as con_codigo_modular,
                SUM(CASE WHEN codigo_local IS NOT NULL AND codigo_local != '' THEN 1 ELSE 0 END) as con_codigo_local,
                SUM(CASE WHEN nombre_institucion IS NOT NULL AND nombre_institucion != '' THEN 1 ELSE 0 END) as con_nombre,
                SUM(CASE WHEN region IS NOT NULL AND region != '' THEN 1 ELSE 0 END) as con_region,
                SUM(CASE WHEN latitud IS NOT NULL THEN 1 ELSE 0 END) as con_coordenadas,
                SUM(CASE WHEN es_fya = 1 THEN 1 ELSE 0 END) as escuelas_fya,
                SUM(CASE WHEN es_rural = 1 THEN 1 ELSE 0 END) as rurales,
                SUM(CASE WHEN modalidad_especifica IS NOT NULL AND modalidad_especifica != '' THEN 1 ELSE 0 END) as con_modalidad_especifica,
                SUM(CASE WHEN area_censo IS NOT NULL AND area_censo != '' THEN 1 ELSE 0 END) as con_area_censo
            FROM instituciones_educativas_v2_mejorada
        """).fetchone()
        
        print(f"   📋 Completitud de datos:")
        print(f"      - Con código modular: {campos_completos[1]} ({campos_completos[1]/campos_completos[0]*100:.1f}%)")
        print(f"      - Con código local: {campos_completos[2]} ({campos_completos[2]/campos_completos[0]*100:.1f}%)")
        print(f"      - Con nombre: {campos_completos[3]} ({campos_completos[3]/campos_completos[0]*100:.1f}%)")
        print(f"      - Con región: {campos_completos[4]} ({campos_completos[4]/campos_completos[0]*100:.1f}%)")
        print(f"      - Con coordenadas: {campos_completos[5]} ({campos_completos[5]/campos_completos[0]*100:.1f}%)")
        print(f"      - Escuelas FyA: {campos_completos[6]} ({campos_completos[6]/campos_completos[0]*100:.1f}%)")
        print(f"      - Instituciones rurales: {campos_completos[7]} ({campos_completos[7]/campos_completos[0]*100:.1f}%)")
        print(f"      - Con modalidad específica: {campos_completos[8]} ({campos_completos[8]/campos_completos[0]*100:.1f}%)")
        print(f"      - Con área de censo: {campos_completos[9]} ({campos_completos[9]/campos_completos[0]*100:.1f}%)")
        
        # 2. NUEVOS CAMPOS ADICIONADOS
        print(f"\n🆕 NUEVOS CAMPOS ADICIONADOS")
        print("=" * 50)
        
        print(f"   📋 Campos adicionales incluidos:")
        print(f"      ✅ numero_procedimiento (nroced)")
        print(f"      ✅ cuadro_datos (cuadro)")
        print(f"      ✅ modalidad_especifica (modal)")
        print(f"      ✅ gestion_departamental (d_ges_dep)")
        print(f"      ✅ codigo_carrera (d_cod_car)")
        print(f"      ✅ area_censo (dareacenso)")
        print(f"      ✅ estado_validacion (valido)")
        print(f"      ✅ multiplicidad1 y multiplicidad2")
        print(f"      ✅ identificador (ident)")
        print(f"      ✅ numero_fya mejorado (nfya)")
        print(f"      ✅ numero_fya_secundario (N° FYA)")
        print(f"      ✅ unidad_ejecutora (dre_ugel)")
        
        # 3. DISTRIBUCIÓN POR MODALIDAD ESPECÍFICA
        print(f"\n📚 DISTRIBUCIÓN POR MODALIDAD ESPECÍFICA")
        print("=" * 50)
        
        modalidades = conn.execute("""
            SELECT modalidad_especifica, COUNT(*) as total 
            FROM instituciones_educativas_v2_mejorada 
            GROUP BY modalidad_especifica 
            ORDER BY total DESC
        """).fetchall()
        
        for modalidad, total in modalidades:
            porcentaje = (total / campos_completos[0]) * 100
            print(f"   - {modalidad}: {total} instituciones ({porcentaje:.1f}%)")
        
        # 4. DISTRIBUCIÓN POR ÁREA DE CENSO
        print(f"\n🌍 DISTRIBUCIÓN POR ÁREA DE CENSO")
        print("=" * 50)
        
        areas_censo = conn.execute("""
            SELECT area_censo, COUNT(*) as total 
            FROM instituciones_educativas_v2_mejorada 
            GROUP BY area_censo 
            ORDER BY total DESC
        """).fetchall()
        
        for area, total in areas_censo:
            porcentaje = (total / campos_completos[0]) * 100
            print(f"   - {area}: {total} instituciones ({porcentaje:.1f}%)")
        
        # 5. ANÁLISIS DE NÚMEROS FyA
        print(f"\n🏫 ANÁLISIS DE NÚMEROS FyA")
        print("=" * 50)
        
        # Números FyA únicos
        numeros_fya = conn.execute("""
            SELECT numero_fya, COUNT(*) as total 
            FROM instituciones_educativas_v2_mejorada 
            WHERE numero_fya IS NOT NULL AND numero_fya != ''
            GROUP BY numero_fya 
            ORDER BY total DESC
            LIMIT 10
        """).fetchall()
        
        print(f"   📋 Principales números FyA:")
        for numero, total in numeros_fya:
            print(f"      - {numero}: {total} instituciones")
        
        # 6. ANÁLISIS DE MULTIPLICIDAD
        print(f"\n🔢 ANÁLISIS DE MULTIPLICIDAD")
        print("=" * 50)
        
        mult1_stats = conn.execute("""
            SELECT 
                MIN(multiplicidad1) as min_mult1,
                MAX(multiplicidad1) as max_mult1,
                AVG(multiplicidad1) as avg_mult1,
                COUNT(*) as total_con_mult1
            FROM instituciones_educativas_v2_mejorada 
            WHERE multiplicidad1 IS NOT NULL
        """).fetchone()
        
        mult2_stats = conn.execute("""
            SELECT 
                MIN(multiplicidad2) as min_mult2,
                MAX(multiplicidad2) as max_mult2,
                AVG(multiplicidad2) as avg_mult2,
                COUNT(*) as total_con_mult2
            FROM instituciones_educativas_v2_mejorada 
            WHERE multiplicidad2 IS NOT NULL
        """).fetchone()
        
        print(f"   📊 Multiplicidad 1:")
        print(f"      - Rango: {mult1_stats[0]} - {mult1_stats[1]}")
        print(f"      - Promedio: {mult1_stats[2]:.2f}")
        print(f"      - Registros con valor: {mult1_stats[3]}")
        
        print(f"   📊 Multiplicidad 2:")
        print(f"      - Rango: {mult2_stats[0]} - {mult2_stats[1]}")
        print(f"      - Promedio: {mult2_stats[2]:.2f}")
        print(f"      - Registros con valor: {mult2_stats[3]}")
        
        # 7. ANÁLISIS DE ESTADO DE VALIDACIÓN
        print(f"\n✅ ANÁLISIS DE ESTADO DE VALIDACIÓN")
        print("=" * 50)
        
        estados_validacion = conn.execute("""
            SELECT estado_validacion, COUNT(*) as total 
            FROM instituciones_educativas_v2_mejorada 
            GROUP BY estado_validacion 
            ORDER BY total DESC
        """).fetchall()
        
        for estado, total in estados_validacion:
            porcentaje = (total / campos_completos[0]) * 100
            print(f"   - {estado}: {total} instituciones ({porcentaje:.1f}%)")
        
        # 8. MUESTRA DE DATOS MEJORADOS
        print(f"\n📋 MUESTRA DE DATOS V2.0 MEJORADOS")
        print("=" * 50)
        
        muestra = conn.execute("""
            SELECT 
                id, codigo_modular, nombre_institucion, tipo_institucion,
                region, modalidad_especifica, area_censo, numero_fya,
                es_fya, es_rural, estado_validacion, multiplicidad1, multiplicidad2
            FROM instituciones_educativas_v2_mejorada 
            ORDER BY RANDOM() 
            LIMIT 10
        """).fetchall()
        
        for i, row in enumerate(muestra, 1):
            nombre_corto = row[2][:30] + "..." if len(row[2]) > 30 else row[2]
            print(f"   {i:2d}. ID: {row[0]:3d} | Código: {row[1]:<10} | Nombre: {nombre_corto:<30} | Modalidad: {row[5]:<5} | Área: {row[6]:<6} | FyA: {'Sí' if row[8] else 'No'} | Rural: {'Sí' if row[9] else 'No'} | Mult: {row[11]}/{row[12]}")
        
        # 9. COMPARACIÓN CON VERSIÓN ANTERIOR
        print(f"\n🔄 COMPARACIÓN CON VERSIÓN ANTERIOR")
        print("=" * 50)
        
        try:
            total_v1 = conn.execute("SELECT COUNT(*) FROM instituciones_educativas_v2").fetchone()[0]
            print(f"   📊 V2.0 Básica: {total_v1} instituciones")
            print(f"   📊 V2.0 Mejorada: {total_registros} instituciones")
            print(f"   📈 Incremento: {total_registros - total_v1} instituciones")
            
            # Verificar campos adicionales
            campos_adicionales_v1 = conn.execute("""
                SELECT 
                    SUM(CASE WHEN modalidad_especifica IS NOT NULL AND modalidad_especifica != '' THEN 1 ELSE 0 END) as con_modalidad_especifica,
                    SUM(CASE WHEN area_censo IS NOT NULL AND area_censo != '' THEN 1 ELSE 0 END) as con_area_censo,
                    SUM(CASE WHEN numero_fya IS NOT NULL AND numero_fya != '' THEN 1 ELSE 0 END) as con_numero_fya,
                    COUNT(*) as total
                FROM instituciones_educativas_v2_mejorada
            """).fetchone()
            
            print(f"   📋 Campos adicionales en V2.0 Mejorada:")
            print(f"      - Con modalidad específica: {campos_adicionales_v1[0]} ({campos_adicionales_v1[0]/campos_adicionales_v1[3]*100:.1f}%)")
            print(f"      - Con área de censo: {campos_adicionales_v1[1]} ({campos_adicionales_v1[1]/campos_adicionales_v1[3]*100:.1f}%)")
            print(f"      - Con número FyA mejorado: {campos_adicionales_v1[2]} ({campos_adicionales_v1[2]/campos_adicionales_v1[3]*100:.1f}%)")
            
        except Exception as e:
            print(f"   ⚠️ No se pudo comparar con versión anterior: {e}")
        
        # 10. MEJORAS LOGRADAS
        print(f"\n💡 MEJORAS LOGRADAS")
        print("=" * 50)
        
        print(f"   ✅ CAMPOS ADICIONALES INCLUIDOS:")
        print(f"      - Modalidad específica (EBR, RER, EBA, CETPRO, EBE, IEST)")
        print(f"      - Área de censo (Rural/Urbana)")
        print(f"      - Número FyA mejorado (nfya de fuente primaria)")
        print(f"      - Estado de validación (VALIDO)")
        print(f"      - Información de multiplicidad (multiplicidad1, multiplicidad2)")
        print(f"      - Número de procedimiento (nroced)")
        print(f"      - Cuadro de datos (cuadro)")
        print(f"      - Gestión departamental (d_ges_dep)")
        print(f"      - Código de carrera (d_cod_car)")
        print(f"      - Unidad ejecutora (dre_ugel)")
        print(f"      - Identificador único (ident)")
        
        print(f"\n   🎯 BENEFICIOS:")
        print(f"      - Información más detallada para análisis")
        print(f"      - Mejor identificación de escuelas FyA")
        print(f"      - Clasificación más precisa de ruralidad")
        print(f"      - Datos de multiplicidad para análisis estadístico")
        print(f"      - Información de validación de datos")
        print(f"      - Modalidades educativas específicas")
        
        print(f"\n   🚀 PRÓXIMOS PASOS:")
        print(f"      - Crear vistas SQL para análisis específicos")
        print(f"      - Desarrollar reportes por modalidad")
        print(f"      - Análisis geoespacial con coordenadas")
        print(f"      - Dashboard con todas las dimensiones")
        
        conn.close()
        
        print(f"\n✅ ANÁLISIS V2.0 MEJORADA COMPLETADO")
        print("=" * 70)
        
    except Exception as e:
        print(f"❌ Error analizando V2.0 mejorada: {e}")

if __name__ == "__main__":
    mostrar_estructura_v2_mejorada()
