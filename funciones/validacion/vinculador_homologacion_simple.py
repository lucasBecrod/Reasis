#!/usr/bin/env python3
"""
Vinculador Homologación Simple - Proyecto Reasis
Procesa homologacionManualLucas.xlsx para mejorar vinculación RER
"""

import pandas as pd
import sqlite3

def procesar_homologacion():
    """Procesar archivo homologacionManualLucas.xlsx"""
    print("PROCESANDO HOMOLOGACIÓN MANUAL LUCAS")
    print("=" * 60)
    
    try:
        # Leer archivo
        df_colegios = pd.read_excel('assets/Consultoria/DatosLucas/homologacionManualLucas.xlsx', sheet_name='colegios')
        print(f"Archivo leído exitosamente: {len(df_colegios)} registros")
        print(f"Columnas: {list(df_colegios.columns)}")
        
        # Mostrar muestra
        print(f"\nMuestra de datos:")
        print(df_colegios.head(10).to_string(index=False))
        
        # Análisis de RER
        rer_dist = df_colegios['rer'].value_counts()
        print(f"\nDistribución por RER:")
        print(rer_dist.to_string())
        
        return df_colegios
        
    except Exception as e:
        print(f"ERROR: {e}")
        return None

def ejecutar_vinculacion_mejorada(df_colegios):
    """Ejecutar vinculación mejorada usando datos de homologación"""
    if df_colegios is None:
        return 0
        
    print(f"\nEJECUTANDO VINCULACIÓN MEJORADA")
    print("=" * 50)
    
    conn = sqlite3.connect('reasis_database.db')
    
    # Verificar coincidencias actuales
    codigos_ie = pd.read_sql_query('''
        SELECT DISTINCT codigo_local, codigo_red
        FROM instituciones_educativas
        WHERE codigo_local IS NOT NULL AND codigo_local != ''
    ''', conn)
    
    print(f"Códigos locales en IE: {len(codigos_ie)}")
    
    # Analizar coincidencias
    set_ie = set(codigos_ie['codigo_local'].astype(str))
    set_colegios = set(df_colegios['codigo_local'].astype(str))
    
    coincidencias = set_ie.intersection(set_colegios)
    print(f"Coincidencias encontradas: {len(coincidencias)}")
    print(f"Porcentaje de coincidencia: {len(coincidencias)/len(set_ie)*100:.1f}%")
    
    if len(coincidencias) == 0:
        print("No hay coincidencias para procesar")
        conn.close()
        return 0
    
    # Mostrar algunas coincidencias
    print(f"Muestra de códigos coincidentes: {list(coincidencias)[:10]}")
    
    # Crear tabla temporal
    df_temp = df_colegios[['codigo_local', 'rer']].copy()
    df_temp = df_temp.dropna()
    df_temp.to_sql('temp_homologacion', conn, if_exists='replace', index=False)
    
    print(f"Tabla temporal creada con {len(df_temp)} registros")
    
    # Contar instituciones sin RER actualmente
    sin_rer_antes = pd.read_sql_query('SELECT COUNT(*) as count FROM instituciones_educativas WHERE codigo_red IS NULL', conn).iloc[0, 0]
    print(f"Instituciones sin RER antes: {sin_rer_antes}")
    
    # Actualizar instituciones_educativas
    cursor = conn.cursor()
    
    update_sql = '''
        UPDATE instituciones_educativas 
        SET codigo_red = 
            CASE 
                WHEN t.rer = '44' THEN 'RER FA 44'
                WHEN t.rer = '47' THEN 'RER FA 47'
                WHEN t.rer = '48' THEN 'RER FA 48'
                WHEN t.rer = '54' THEN 'RER FA 54'
                WHEN t.rer = '72' THEN 'RER FA 72'
                WHEN t.rer = '79' THEN 'RER FA 79'
            END
        FROM temp_homologacion t
        WHERE instituciones_educativas.codigo_local = t.codigo_local
        AND (instituciones_educativas.codigo_red IS NULL OR instituciones_educativas.codigo_red = '')
        AND t.rer IN ('44', '47', '48', '54', '72', '79')
    '''
    
    cursor.execute(update_sql)
    actualizadas = cursor.rowcount
    
    print(f"Instituciones actualizadas: {actualizadas}")
    
    # Contar instituciones sin RER después
    sin_rer_despues = pd.read_sql_query('SELECT COUNT(*) as count FROM instituciones_educativas WHERE codigo_red IS NULL', conn).iloc[0, 0]
    print(f"Instituciones sin RER después: {sin_rer_despues}")
    
    # Estadísticas finales
    resultado_final = pd.read_sql_query('''
        SELECT 
            ie.codigo_red,
            r.nombre_completo,
            COUNT(*) as instituciones_vinculadas
        FROM instituciones_educativas ie
        INNER JOIN redes_fe_y_alegria r ON ie.codigo_red = r.codigo_red
        GROUP BY ie.codigo_red, r.nombre_completo
        ORDER BY instituciones_vinculadas DESC
    ''', conn)
    
    print(f"\nRESULTADO FINAL:")
    print(resultado_final.to_string(index=False))
    
    # Totales
    total_vinculadas = resultado_final['instituciones_vinculadas'].sum()
    total_instituciones = pd.read_sql_query('SELECT COUNT(*) as count FROM instituciones_educativas', conn).iloc[0, 0]
    
    print(f"\nTOTALES FINALES:")
    print(f"Total instituciones: {total_instituciones}")
    print(f"Vinculadas con RER: {total_vinculadas}")
    print(f"Porcentaje vinculado: {total_vinculadas/total_instituciones*100:.1f}%")
    print(f"Mejora lograda: +{actualizadas} instituciones")
    
    # Limpiar
    conn.execute('DROP TABLE IF EXISTS temp_homologacion')
    conn.commit()
    conn.close()
    
    return actualizadas

def main():
    """Función principal"""
    print("VINCULADOR HOMOLOGACIÓN SIMPLE")
    print("=" * 50)
    
    # Procesar archivo
    df_colegios = procesar_homologacion()
    
    # Ejecutar vinculación
    if df_colegios is not None:
        mejoras = ejecutar_vinculacion_mejorada(df_colegios)
        
        print(f"\nPROCESO COMPLETADO")
        print(f"Instituciones adicionales vinculadas: {mejoras}")
    else:
        print("No se pudo procesar el archivo")

if __name__ == "__main__":
    main()