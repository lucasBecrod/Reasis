#!/usr/bin/env python3
"""
Verificador final del estado de la base de datos después de la limpieza
"""

import sqlite3

def verificar_tablas():
    conn = sqlite3.connect('reasis_database.db')
    cursor = conn.cursor()

    print("=== TABLAS RESTANTES DESPUÉS DE LIMPIEZA ===\n")
    
    # Obtener todas las tablas
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tablas = cursor.fetchall()
    
    total_registros = 0
    tablas_activas = []
    
    for tabla in tablas:
        nombre_tabla = tabla[0]
        if nombre_tabla != 'sqlite_sequence':
            cursor.execute(f'SELECT COUNT(*) FROM [{nombre_tabla}]')
            registros = cursor.fetchone()[0]
            total_registros += registros
            tablas_activas.append((nombre_tabla, registros))
            print(f"- {nombre_tabla}: {registros:,} registros")
    
    print(f"\nRESUMEN FINAL:")
    print(f"- Tablas activas: {len(tablas_activas)}")
    print(f"- Total registros: {total_registros:,}")
    
    # Verificar tablas esenciales
    tablas_esperadas = [
        'instituciones_educativas',
        'resultados_academicos', 
        'docentes_data',
        'competencia_digital_docentes',
        'datos_eib_minedu',
        'ruralidad_cesar',
        'x5_ed_estabilidad_docente',
        'variables_eib_mejoradas_final',
        'datos_toe_servicios_2024',
        'conectividad_equipamiento',
        'mapeo_codigos_ie',
        'redes_fe_y_alegria'
    ]
    
    print(f"\n=== VERIFICACIÓN TABLAS ESENCIALES ===")
    tablas_existentes = [t[0] for t in tablas_activas]
    
    for tabla_esperada in tablas_esperadas:
        if tabla_esperada in tablas_existentes:
            registros = next(t[1] for t in tablas_activas if t[0] == tabla_esperada)
            print(f"✅ {tabla_esperada}: {registros:,} registros")
        else:
            print(f"❌ {tabla_esperada}: NO ENCONTRADA")
    
    # Identificar tablas adicionales
    tablas_extra = [t for t in tablas_existentes if t not in tablas_esperadas]
    if tablas_extra:
        print(f"\n=== TABLAS ADICIONALES ===")
        for tabla in tablas_extra:
            registros = next(t[1] for t in tablas_activas if t[0] == tabla)
            print(f"📋 {tabla}: {registros:,} registros")
    
    conn.close()
    return len(tablas_activas), total_registros

if __name__ == "__main__":
    verificar_tablas()