#!/usr/bin/env python3
"""
Limpiar columnas innecesarias de tabla instituciones_educativas
Proyecto Reasis - Reducción de columnas redundantes y vacías

Basado en análisis previo: eliminar 16 columnas innecesarias
"""

import sqlite3
import pandas as pd

def main():
    print("=== LIMPIEZA DE COLUMNAS instituciones_educativas ===")
    
    conn = sqlite3.connect('reasis_database.db')
    cursor = conn.cursor()
    
    # 1. Lista de columnas a eliminar basada en análisis
    columnas_eliminar = [
        # Columnas completamente vacías (3)
        'nombre_corto',
        'codigo_rie', 
        'usuario_actualizacion',
        
        # Columnas constantes/con un solo valor (8)
        'cuadro_datos',         # Solo "C303"
        'tipo_institucion',     # Solo "IE"
        'fuente_datos',         # Solo "MINEDU"
        'es_toe',              # Solo 0
        'estado_validacion',    # Solo "VALIDO"
        'fecha_actualizacion',  # Solo un timestamp
        'es_fya',              # Solo 1 (todas son Fe y Alegría)
        'identificador',        # Solo 1
        
        # Columnas redundantes (2)
        'codigo_red',          # 30% completitud, redundante con numero_fya
        'codigo_rer',          # 30% completitud, redundante con numero_fya
        
        # Columnas de poco valor (2)
        'pagina_web',          # Solo 3 valores, 99% vacío
        'departamento'         # Redundante con region (analizar primero)
    ]
    
    print(f"1. Planificando eliminación de {len(columnas_eliminar)} columnas...")
    
    # 2. Verificar si departamento y region son realmente redundantes
    print("2. Verificando redundancia region vs departamento...")
    
    cursor.execute("""
        SELECT COUNT(*) FROM instituciones_educativas 
        WHERE region != departamento OR 
              (region IS NULL AND departamento IS NOT NULL) OR
              (region IS NOT NULL AND departamento IS NULL)
    """)
    diferencias_geo = cursor.fetchone()[0]
    
    if diferencias_geo > 0:
        print(f"   Encontradas {diferencias_geo} diferencias -> MANTENER departamento")
        columnas_eliminar.remove('departamento')
    else:
        print("   region y departamento son equivalentes -> ELIMINAR departamento")
    
    # 3. Obtener esquema actual
    print("3. Obteniendo esquema actual...")
    cursor.execute("PRAGMA table_info(instituciones_educativas)")
    schema_actual = cursor.fetchall()
    
    columnas_actuales = [col[1] for col in schema_actual]
    print(f"   Columnas actuales: {len(columnas_actuales)}")
    
    # Verificar que las columnas a eliminar existen
    columnas_eliminar_validas = [col for col in columnas_eliminar if col in columnas_actuales]
    columnas_no_encontradas = [col for col in columnas_eliminar if col not in columnas_actuales]
    
    if columnas_no_encontradas:
        print(f"   Columnas no encontradas: {columnas_no_encontradas}")
    
    columnas_eliminar = columnas_eliminar_validas
    print(f"   Columnas a eliminar válidas: {len(columnas_eliminar)}")
    
    # 4. Crear lista de columnas a mantener
    columnas_mantener = [col for col in columnas_actuales if col not in columnas_eliminar]
    
    print(f"4. Columnas finales: {len(columnas_mantener)} (reducción de {len(columnas_eliminar)} columnas)")
    
    # 5. Mostrar columnas que se mantendrán
    print("\\n5. Columnas que se mantendrán:")
    for i, col in enumerate(sorted(columnas_mantener), 1):
        print(f"   {i:2d}. {col}")
    
    # 6. Crear respaldo antes de la limpieza
    print("\\n6. Creando respaldo...")
    cursor.execute("CREATE TABLE instituciones_educativas_backup AS SELECT * FROM instituciones_educativas")
    print("   Respaldo creado: instituciones_educativas_backup")
    
    # 7. Crear tabla temporal con solo las columnas necesarias
    print("\\n7. Creando tabla optimizada...")
    
    # Construir SELECT con columnas a mantener
    select_columnas = ", ".join(columnas_mantener)
    
    cursor.execute(f"""
        CREATE TABLE instituciones_educativas_limpia AS
        SELECT {select_columnas}
        FROM instituciones_educativas
    """)
    
    # 8. Reemplazar tabla original
    print("8. Reemplazando tabla original...")
    cursor.execute("DROP TABLE instituciones_educativas")
    cursor.execute("ALTER TABLE instituciones_educativas_limpia RENAME TO instituciones_educativas")
    
    # 9. Confirmar cambios
    conn.commit()
    
    # 10. Verificar resultado final
    print("\\n9. Verificación final:")
    cursor.execute("PRAGMA table_info(instituciones_educativas)")
    schema_final = cursor.fetchall()
    
    print(f"   Columnas finales: {len(schema_final)}")
    print(f"   Columnas eliminadas: {len(columnas_actuales) - len(schema_final)}")
    print(f"   Reducción: {(len(columnas_actuales) - len(schema_final))/len(columnas_actuales)*100:.1f}%")
    
    # Verificar que no se perdieron registros
    cursor.execute("SELECT COUNT(*) FROM instituciones_educativas")
    registros_final = cursor.fetchone()[0]
    print(f"   Registros mantenidos: {registros_final}")
    
    # 11. Mostrar columnas eliminadas
    print("\\n10. Columnas eliminadas exitosamente:")
    for col in sorted(columnas_eliminar):
        print(f"    - {col}")
    
    print("\\n11. Columnas críticas mantenidas:")
    columnas_criticas = ['codigo_modular', 'nombre_institucion', 'numero_fya', 
                        'nombre_red_fya_matched', 'region', 'distrito', 
                        'total_alumnos', 'docentes_total', 'entra_estudio_clustering']
    for col in columnas_criticas:
        if col in [c[1] for c in schema_final]:
            print(f"    [OK] {col}")
        else:
            print(f"    [ERROR] {col} - NO ENCONTRADA")
    
    conn.close()
    print("\\n¡LIMPIEZA COMPLETADA EXITOSAMENTE!")

if __name__ == "__main__":
    main()