#!/usr/bin/env python3
"""
Normalizar columna numero_fya y eliminar numero_fya_secundario
Proyecto Reasis - Consolidación de códigos de red

Objetivo: 
- Convertir numero_fya a formato simple (44, 47, 48, etc.)
- Usar nombre_red_fya_matched como fuente de verdad
- Eliminar columna numero_fya_secundario que es redundante
"""

import sqlite3
import pandas as pd
import re

def extraer_codigo_red(nombre_red):
    """Extrae el código numérico de la red desde nombre_red_fya_matched"""
    if not nombre_red or pd.isna(nombre_red):
        return None
    
    # Buscar patrón "Red Fe y Alegría XX"
    match = re.search(r'Red Fe y Alegría (\d+)', str(nombre_red))
    if match:
        return match.group(1)
    
    return None

def main():
    print("=== NORMALIZANDO COLUMNA numero_fya ===")
    
    conn = sqlite3.connect('reasis_database.db')
    
    # 1. Cargar todos los registros
    print("1. Cargando datos actuales...")
    df = pd.read_sql_query("""
        SELECT codigo_modular, numero_fya, numero_fya_secundario, nombre_red_fya_matched
        FROM instituciones_educativas
        WHERE nombre_red_fya_matched IS NOT NULL AND nombre_red_fya_matched != ''
    """, conn)
    
    print(f"   Total registros a procesar: {len(df)}")
    
    # 2. Extraer códigos normalizados
    print("2. Extrayendo códigos normalizados...")
    df['codigo_red_extraido'] = df['nombre_red_fya_matched'].apply(extraer_codigo_red)
    
    # Verificar extracción
    exitosos = df['codigo_red_extraido'].notna().sum()
    print(f"   Códigos extraídos exitosamente: {exitosos}/{len(df)} ({exitosos/len(df)*100:.1f}%)")
    
    # 3. Mostrar ejemplos de normalización
    print("\n3. Ejemplos de normalización:")
    print("   ANTES                    ->  DESPUÉS")
    for i, row in df.head(10).iterrows():
        antes = row['numero_fya']
        despues = row['codigo_red_extraido']
        red = row['nombre_red_fya_matched']
        print(f"   {antes:<24} ->  {despues:<3} ({red})")
    
    # 4. Estadísticas de cambios
    print("\n4. Estadísticas de cambios necesarios:")
    
    # Comparar valores actuales vs normalizados
    df['necesita_cambio'] = df['numero_fya'] != df['codigo_red_extraido']
    cambios_necesarios = df['necesita_cambio'].sum()
    
    print(f"   Registros que necesitan normalización: {cambios_necesarios}")
    print(f"   Registros que ya están correctos: {len(df) - cambios_necesarios}")
    
    # Mostrar distribución de cambios por formato actual
    cambios_por_formato = df[df['necesita_cambio']].groupby('numero_fya').size().sort_values(ascending=False)
    print("\n   Cambios por formato actual:")
    print(cambios_por_formato.head(10).to_string())
    
    # 5. Ejecutar normalización
    print(f"\n5. Ejecutando normalización de {cambios_necesarios} registros...")
    cursor = conn.cursor()
    
    actualizados = 0
    for _, row in df[df['necesita_cambio']].iterrows():
        codigo_modular = row['codigo_modular']
        nuevo_numero_fya = row['codigo_red_extraido']
        
        cursor.execute("""
            UPDATE instituciones_educativas 
            SET numero_fya = ?
            WHERE codigo_modular = ?
        """, (nuevo_numero_fya, codigo_modular))
        
        actualizados += 1
        if actualizados % 50 == 0:
            print(f"   Procesados: {actualizados}/{cambios_necesarios}")
    
    print(f"   Total registros actualizados: {actualizados}")
    
    # 6. Eliminar columna numero_fya_secundario
    print("\n6. Eliminando columna numero_fya_secundario...")
    
    # Verificar si la columna existe
    cursor.execute("PRAGMA table_info(instituciones_educativas)")
    columnas = [col[1] for col in cursor.fetchall()]
    
    if 'numero_fya_secundario' in columnas:
        # En SQLite no se puede eliminar columna directamente, crear tabla temporal
        print("   Creando tabla temporal sin numero_fya_secundario...")
        
        # Obtener esquema actual
        cursor.execute("SELECT sql FROM sqlite_master WHERE name='instituciones_educativas'")
        schema_original = cursor.fetchone()[0]
        
        # Crear tabla temporal
        cursor.execute("""
            CREATE TABLE instituciones_educativas_temp AS
            SELECT 
                id, codigo_modular, codigo_local, codigo_rie, numero_procedimiento,
                cuadro_datos, nombre_institucion, nombre_corto, tipo_institucion,
                region, provincia, distrito, departamento, direccion, localidad,
                centro_poblado, area_censo, latitud, longitud, altitud,
                nivel_educativo, modalidad, modalidad_especifica, gestion,
                gestion_departamental, tipo_sexo, turno, codigo_carrera,
                total_alumnos, alumnos_hombres, alumnos_mujeres, total_docentes,
                total_secciones, directivos_hombres, directivos_mujeres, directivos_total,
                docentes_hombres, docentes_mujeres, docentes_total, es_rural, es_eib,
                es_toe, estado_validacion, director, telefono, email, pagina_web,
                es_fya, numero_fya, unidad_ejecutora, multiplicidad1, multiplicidad2,
                identificador, fuente_datos, fecha_actualizacion, usuario_actualizacion,
                codigo_red, codigo_rer, id_red_fya, nombre_red_fya_matched, entra_estudio_clustering
            FROM instituciones_educativas
        """)
        
        # Eliminar tabla original y renombrar
        cursor.execute("DROP TABLE instituciones_educativas")
        cursor.execute("ALTER TABLE instituciones_educativas_temp RENAME TO instituciones_educativas")
        
        print("   Columna numero_fya_secundario eliminada exitosamente")
    else:
        print("   Columna numero_fya_secundario no existe")
    
    # 7. Confirmar cambios
    conn.commit()
    
    # 8. Verificar resultado final
    print("\n7. Verificación final:")
    df_final = pd.read_sql_query("""
        SELECT DISTINCT numero_fya, COUNT(*) as cantidad
        FROM instituciones_educativas
        WHERE numero_fya IS NOT NULL AND numero_fya != ''
        GROUP BY numero_fya
        ORDER BY CAST(numero_fya AS INTEGER)
    """, conn)
    
    print("   Distribución final de numero_fya:")
    print(df_final.to_string())
    
    # Verificar que solo hay números
    no_numericos = df_final[~df_final['numero_fya'].str.match(r'^\d+$')]
    if len(no_numericos) > 0:
        print(f"\n   ADVERTENCIA: {len(no_numericos)} valores no numéricos detectados:")
        print(no_numericos.to_string())
    else:
        print(f"\n   ✓ ÉXITO: Todos los valores de numero_fya son numéricos")
        print(f"   ✓ Total redes normalizadas: {len(df_final)}")
    
    conn.close()
    print("\n¡NORMALIZACIÓN COMPLETADA!")

if __name__ == "__main__":
    main()