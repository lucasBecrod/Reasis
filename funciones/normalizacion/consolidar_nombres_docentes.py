#!/usr/bin/env python3
"""
Consolidar Nombres Docentes - Proyecto Reasis
Unifica campos nombres y apellidos en nombre_completo y elimina campos separados
"""

import pandas as pd
import sqlite3

def analizar_estructura_actual():
    """Analizar estructura actual de nombres en tabla docentes"""
    print("ANÁLISIS ESTRUCTURA ACTUAL - NOMBRES DOCENTES")
    print("=" * 60)
    
    conn = sqlite3.connect('reasis_database.db')
    
    # Verificar campos existentes
    campos = pd.read_sql_query("PRAGMA table_info(docentes_data)", conn)
    print("Campos actuales relacionados con nombres:")
    campos_nombres = campos[campos['name'].str.contains('nombre|apellido', case=False)]
    print(campos_nombres[['name', 'type', 'notnull']].to_string(index=False))
    
    # Analizar completitud por año
    completitud = pd.read_sql_query('''
        SELECT 
            año,
            COUNT(*) as total_registros,
            COUNT(nombres) as con_nombres,
            COUNT(apellidos) as con_apellidos,
            COUNT(nombre_completo) as con_nombre_completo,
            ROUND(COUNT(nombres) * 100.0 / COUNT(*), 1) as pct_nombres,
            ROUND(COUNT(apellidos) * 100.0 / COUNT(*), 1) as pct_apellidos,
            ROUND(COUNT(nombre_completo) * 100.0 / COUNT(*), 1) as pct_completo
        FROM docentes_data
        GROUP BY año
        ORDER BY año
    ''', conn)
    
    print(f"\nCompletitud de campos de nombres por año:")
    print(completitud.to_string(index=False))
    
    # Mostrar ejemplos de datos actuales
    ejemplos = pd.read_sql_query('''
        SELECT año, dni, nombres, apellidos, nombre_completo
        FROM docentes_data
        WHERE nombres IS NOT NULL OR apellidos IS NOT NULL OR nombre_completo IS NOT NULL
        ORDER BY año, dni
        LIMIT 10
    ''', conn)
    
    print(f"\nEjemplos de datos actuales (primeros 10):")
    print(ejemplos.to_string(index=False))
    
    conn.close()
    return completitud

def consolidar_nombres():
    """Consolidar nombres y apellidos en campo nombre_completo"""
    print(f"\nCONSOLIDACIÓN DE NOMBRES")
    print("-" * 40)
    
    conn = sqlite3.connect('reasis_database.db')
    cursor = conn.cursor()
    
    # Paso 1: Actualizar nombre_completo donde esté NULL pero tengamos nombres y apellidos
    print("Paso 1: Consolidando nombres + apellidos -> nombre_completo")
    
    update_sql = '''
        UPDATE docentes_data 
        SET nombre_completo = TRIM(
            COALESCE(nombres, '') || ' ' || COALESCE(apellidos, '')
        )
        WHERE (nombre_completo IS NULL OR nombre_completo = '')
        AND (nombres IS NOT NULL OR apellidos IS NOT NULL)
    '''
    
    cursor.execute(update_sql)
    registros_actualizados = cursor.rowcount
    print(f"Registros actualizados: {registros_actualizados}")
    
    # Paso 2: Verificar resultado
    verificacion = pd.read_sql_query('''
        SELECT 
            año,
            COUNT(*) as total,
            COUNT(nombre_completo) as con_nombre_completo,
            COUNT(CASE WHEN nombre_completo IS NULL OR nombre_completo = '' THEN 1 END) as sin_nombre_completo
        FROM docentes_data
        GROUP BY año
        ORDER BY año
    ''', conn)
    
    print(f"\nVerificación post-consolidación:")
    print(verificacion.to_string(index=False))
    
    # Paso 3: Mostrar ejemplos después de la consolidación
    ejemplos_post = pd.read_sql_query('''
        SELECT año, dni, nombres, apellidos, nombre_completo
        FROM docentes_data
        ORDER BY año, dni
        LIMIT 15
    ''', conn)
    
    print(f"\nEjemplos después de consolidación (primeros 15):")
    print(ejemplos_post.to_string(index=False))
    
    conn.commit()
    conn.close()
    
    return registros_actualizados

def eliminar_campos_separados():
    """Eliminar campos nombres y apellidos separados"""
    print(f"\nELIMINACIÓN DE CAMPOS SEPARADOS")
    print("-" * 40)
    
    conn = sqlite3.connect('reasis_database.db')
    cursor = conn.cursor()
    
    try:
        # SQLite no soporta DROP COLUMN directamente, necesitamos recrear la tabla
        print("Creando nueva estructura sin campos nombres/apellidos separados...")
        
        # Paso 1: Crear tabla temporal con nueva estructura
        create_temp_sql = '''
        CREATE TABLE docentes_data_temp (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            
            -- Identificación del docente
            dni TEXT NOT NULL,
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
        '''
        
        cursor.execute(create_temp_sql)
        
        # Paso 2: Copiar datos (excluyendo nombres y apellidos separados)
        copy_sql = '''
        INSERT INTO docentes_data_temp (
            dni, nombre_completo, genero, rer, institucion_actual, 
            codigo_modular_actual, nivel_educativo, continua_rer,
            institucion_continua, codigo_modular_continua, 
            puntaje_matematica, puntaje_comunicacion, puntaje_digital,
            estado_evaluacion, año, codigo_modular_vinculado, 
            metodo_vinculacion, archivo_origen
        )
        SELECT 
            dni, nombre_completo, genero, rer, institucion_actual,
            codigo_modular_actual, nivel_educativo, continua_rer,
            institucion_continua, codigo_modular_continua,
            puntaje_matematica, puntaje_comunicacion, puntaje_digital,
            estado_evaluacion, año, codigo_modular_vinculado,
            metodo_vinculacion, archivo_origen
        FROM docentes_data
        '''
        
        cursor.execute(copy_sql)
        registros_copiados = cursor.rowcount
        print(f"Registros copiados a nueva estructura: {registros_copiados}")
        
        # Paso 3: Eliminar tabla original
        cursor.execute('DROP TABLE docentes_data')
        
        # Paso 4: Renombrar tabla temporal
        cursor.execute('ALTER TABLE docentes_data_temp RENAME TO docentes_data')
        
        # Paso 5: Recrear índices
        indices_sql = [
            'CREATE INDEX idx_docentes_dni ON docentes_data(dni)',
            'CREATE INDEX idx_docentes_codigo_modular ON docentes_data(codigo_modular_actual)', 
            'CREATE INDEX idx_docentes_año ON docentes_data(año)',
            'CREATE INDEX idx_docentes_rer ON docentes_data(rer)',
            'CREATE INDEX idx_docentes_vinculado ON docentes_data(codigo_modular_vinculado)'
        ]
        
        for idx_sql in indices_sql:
            cursor.execute(idx_sql)
        
        print("Estructura actualizada exitosamente")
        print("Campos eliminados: nombres, apellidos")
        print("Campo consolidado: nombre_completo")
        
        conn.commit()
        conn.close()
        
        return registros_copiados
        
    except Exception as e:
        print(f"ERROR en eliminación de campos: {e}")
        conn.rollback()
        conn.close()
        return 0

def verificar_estructura_final():
    """Verificar estructura final de la tabla"""
    print(f"\nVERIFICACIÓN ESTRUCTURA FINAL")
    print("-" * 40)
    
    conn = sqlite3.connect('reasis_database.db')
    
    # Verificar nueva estructura
    campos_finales = pd.read_sql_query("PRAGMA table_info(docentes_data)", conn)
    print("Campos en estructura final:")
    print(campos_finales[['name', 'type', 'notnull']].to_string(index=False))
    
    # Verificar datos
    verificacion_final = pd.read_sql_query('''
        SELECT 
            COUNT(*) as total_registros,
            COUNT(nombre_completo) as con_nombre_completo,
            COUNT(DISTINCT dni) as docentes_unicos,
            COUNT(codigo_modular_vinculado) as vinculados_instituciones
        FROM docentes_data
    ''', conn)
    
    print(f"\nEstadísticas finales:")
    print(verificacion_final.to_string(index=False))
    
    # Mostrar muestra final
    muestra_final = pd.read_sql_query('''
        SELECT año, dni, nombre_completo, rer, estado_evaluacion
        FROM docentes_data
        ORDER BY año, dni
        LIMIT 10
    ''', conn)
    
    print(f"\nMuestra de datos finales:")
    print(muestra_final.to_string(index=False))
    
    conn.close()
    
    return verificacion_final.iloc[0].to_dict()

def main():
    """Función principal"""
    print("CONSOLIDADOR DE NOMBRES DOCENTES - PROYECTO REASIS")
    print("=" * 70)
    
    # Paso 1: Analizar estructura actual
    completitud_inicial = analizar_estructura_actual()
    
    # Paso 2: Consolidar nombres
    actualizados = consolidar_nombres()
    
    # Paso 3: Eliminar campos separados
    copiados = eliminar_campos_separados()
    
    # Paso 4: Verificación final
    stats_finales = verificar_estructura_final()
    
    print(f"\nCONSOLIDACIÓN COMPLETADA")
    print("=" * 40)
    print(f"- Nombres consolidados en campo unico 'nombre_completo'")
    print(f"- Campos 'nombres' y 'apellidos' eliminados")
    print(f"- Estructura optimizada y limpia")
    print(f"- {stats_finales['total_registros']} registros preservados")
    print(f"- {stats_finales['vinculados_instituciones']} docentes vinculados con instituciones")
    
    return stats_finales

if __name__ == "__main__":
    results = main()