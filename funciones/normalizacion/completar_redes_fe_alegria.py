#!/usr/bin/env python3
"""
Completar datos faltantes en tabla redes_fe_y_alegria
Proyecto Reasis - Consolidación de datos de redes educativas rurales

Fuente: assets/Consultoria/Redes.xlsx
- Hoja "Redes": Información completa de las 6 redes del estudio
- Hoja "colegiosRedConfirmadas": Validación de 330 IIEE
- Hoja "colegiosXred": Códigos IE organizados por red

Objetivo: Completar columnas vacías para las 6 redes objeto de estudio
"""

import pandas as pd
import sqlite3
import sys

def main():
    print("=== COMPLETANDO DATOS REDES FE Y ALEGRÍA ===")
    
    # Archivos
    archivo_redes = r"C:\Users\lucas\Proyectos\Reasis\assets\Consultoria\Redes.xlsx"
    db_path = "reasis_database.db"
    
    # 1. Cargar datos del Excel
    print("1. Cargando datos del Excel...")
    df_redes_excel = pd.read_excel(archivo_redes, sheet_name='Redes')
    print(f"   Redes cargadas desde Excel: {len(df_redes_excel)}")
    
    # 2. Conectar a base de datos
    conn = sqlite3.connect(db_path)
    
    # 3. Ver estado actual
    print("\n2. Estado actual de la tabla redes_fe_y_alegria:")
    df_actual = pd.read_sql_query("""
        SELECT codigo_red, nombre_completo, numero_region, lugar, ambito, red_lugar, entra_estudio_clustering 
        FROM redes_fe_y_alegria 
        WHERE entra_estudio_clustering = 'Sí'
        ORDER BY CAST(codigo_red AS INTEGER)
    """, conn)
    print(df_actual.to_string())
    
    # 4. Preparar datos para actualizar
    print("\n3. Preparando actualizaciones...")
    actualizaciones = []
    
    for _, row in df_redes_excel.iterrows():
        codigo_red = str(row['codigo_red'])
        
        # Limpiar texto con codificación
        red_region = str(row['RED Region']).replace('Ã­', 'í').replace('Ã³', 'ó')
        region = str(row['Region'])
        lugar = str(row['Lugar']) 
        ambito = str(row['Ambito'])
        red_lugar = str(row['RED Lugar'])
        
        actualizacion = {
            'codigo_red': codigo_red,
            'nombre_completo': red_region,
            'numero_region': region,
            'lugar': lugar,
            'ambito': ambito,
            'red_lugar': red_lugar
        }
        actualizaciones.append(actualizacion)
        
        print(f"   Red {codigo_red}: {red_region} -> {lugar}, {region}")
    
    # 5. Ejecutar actualizaciones
    print(f"\n4. Ejecutando {len(actualizaciones)} actualizaciones...")
    cursor = conn.cursor()
    
    for update in actualizaciones:
        query = """
            UPDATE redes_fe_y_alegria 
            SET nombre_completo = ?,
                numero_region = ?,
                lugar = ?,
                ambito = ?,
                red_lugar = ?
            WHERE codigo_red = ?
        """
        
        cursor.execute(query, (
            update['nombre_completo'],
            update['numero_region'], 
            update['lugar'],
            update['ambito'],
            update['red_lugar'],
            update['codigo_red']
        ))
        
        print(f"   Actualizada red {update['codigo_red']}")
    
    # 6. Confirmar cambios
    conn.commit()
    
    # 7. Verificar resultados
    print("\n5. Resultado final:")
    df_final = pd.read_sql_query("""
        SELECT codigo_red, nombre_completo, numero_region, lugar, ambito, red_lugar, entra_estudio_clustering 
        FROM redes_fe_y_alegria 
        WHERE entra_estudio_clustering = 'Sí'
        ORDER BY CAST(codigo_red AS INTEGER)
    """, conn)
    print(df_final.to_string())
    
    # 8. Estadísticas
    print(f"\n6. Estadísticas finales:")
    print(f"   - Total redes actualizadas: {len(actualizaciones)}")
    print(f"   - Campos completados por red: 5 (nombre_completo, numero_region, lugar, ambito, red_lugar)")
    print(f"   - Total campos completados: {len(actualizaciones) * 5}")
    
    conn.close()
    print("\n¡COMPLETADO! Datos de redes consolidados exitosamente.")

if __name__ == "__main__":
    main()