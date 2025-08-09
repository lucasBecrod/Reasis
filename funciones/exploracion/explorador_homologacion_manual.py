#!/usr/bin/env python3
"""
Explorador Homologación Manual Lucas - Proyecto Reasis
Explora archivo homologacionManualLucas.xlsx tabla colegios para vincular RER
"""

import pandas as pd
import sqlite3
from pathlib import Path

def explorar_archivo_homologacion():
    """Explorar estructura del archivo homologacionManualLucas.xlsx"""
    print("EXPLORADOR HOMOLOGACIÓN MANUAL LUCAS")
    print("=" * 60)
    
    archivo_path = Path("assets/Consultoria/DatosLucas/homologacionManualLucas.xlsx")
    
    if not archivo_path.exists():
        print(f"ERROR: Archivo no encontrado: {archivo_path}")
        return None
    
    print(f"Archivo encontrado: {archivo_path.name}")
    
    try:
        # Verificar hojas disponibles
        excel_file = pd.ExcelFile(archivo_path)
        hojas = excel_file.sheet_names
        print(f"Hojas disponibles: {hojas}")
        
        # Explorar hoja 'colegios'
        if 'colegios' in hojas:
            print(f"\n=== EXPLORACIÓN HOJA 'colegios' ===")
            df_colegios = pd.read_excel(archivo_path, sheet_name='colegios')
            
            print(f"Dimensiones: {df_colegios.shape[0]} filas × {df_colegios.shape[1]} columnas")
            
            # Mostrar columnas
            print(f"\nColumnas disponibles:")
            for i, col in enumerate(df_colegios.columns):
                print(f"  {i:2}: {col}")
            
            # Verificar campos clave
            campos_clave = ['codigo_local', 'rer']
            print(f"\nCampos clave encontrados:")
            for campo in campos_clave:
                if campo in df_colegios.columns:
                    print(f"  ✓ {campo}")
                else:
                    # Buscar variaciones del nombre
                    campos_similares = [col for col in df_colegios.columns if campo.lower() in col.lower()]
                    if campos_similares:
                        print(f"  ~ {campo} (posibles: {campos_similares})")
                    else:
                        print(f"  ✗ {campo}")
            
            # Mostrar primeras filas
            print(f"\nPrimeras 5 filas (campos relevantes):")
            print("-" * 60)
            
            # Identificar columnas que contienen 'codigo' o 'rer'
            cols_relevantes = []
            for col in df_colegios.columns:
                if any(keyword in col.lower() for keyword in ['codigo', 'rer', 'local']):
                    cols_relevantes.append(col)
            
            if cols_relevantes:
                print(f"Columnas relevantes detectadas: {cols_relevantes}")
                muestra = df_colegios[cols_relevantes].head()
                print(muestra.to_string(index=True))
            else:
                # Mostrar todas las columnas si no se detectan relevantes
                print("Mostrando todas las columnas:")
                print(df_colegios.head().to_string(index=True))
            
            # Análisis de valores únicos en campos RER
            for col in df_colegios.columns:
                if 'rer' in col.lower():
                    valores_unicos = df_colegios[col].dropna().unique()[:10]  # Primeros 10
                    print(f"\nValores únicos en '{col}' (muestra):")
                    print(f"  Total únicos: {len(df_colegios[col].dropna().unique())}")
                    print(f"  Muestra: {valores_unicos}")
            
            return df_colegios
            
        else:
            print(f"ERROR: Hoja 'colegios' no encontrada")
            print(f"Hojas disponibles: {hojas}")
            return None
            
    except Exception as e:
        print(f"ERROR leyendo archivo: {e}")
        return None

def analizar_cruces_posibles(df_colegios):
    """Analizar posibles cruces con tabla instituciones_educativas"""
    if df_colegios is None:
        return None
    
    print(f"\n=== ANÁLISIS DE CRUCES POSIBLES ===")
    print("=" * 50)
    
    conn = sqlite3.connect('reasis_database.db')
    
    # Obtener códigos locales de instituciones_educativas
    codigos_ie = pd.read_sql_query('''
        SELECT DISTINCT codigo_local
        FROM instituciones_educativas
        WHERE codigo_local IS NOT NULL AND codigo_local != ''
        ORDER BY codigo_local
    ''', conn)
    
    print(f"Códigos locales en instituciones_educativas: {len(codigos_ie)}")
    print(f"Muestra códigos IE: {codigos_ie['codigo_local'].head(10).tolist()}")
    
    # Buscar columna de código local en df_colegios
    col_codigo_colegio = None
    for col in df_colegios.columns:
        if 'codigo' in col.lower() and 'local' in col.lower():
            col_codigo_colegio = col
            break
    
    if not col_codigo_colegio:
        # Buscar solo 'codigo'
        for col in df_colegios.columns:
            if 'codigo' in col.lower():
                col_codigo_colegio = col
                break
    
    print(f"Columna código detectada en colegios: {col_codigo_colegio}")
    
    if col_codigo_colegio:
        codigos_colegios = df_colegios[col_codigo_colegio].dropna().unique()
        print(f"Códigos en tabla colegios: {len(codigos_colegios)}")
        print(f"Muestra códigos colegios: {list(codigos_colegios[:10])}")
        
        # Analizar coincidencias
        set_ie = set(codigos_ie['codigo_local'].astype(str))
        set_colegios = set(df_colegios[col_codigo_colegio].astype(str))
        
        coincidencias = set_ie.intersection(set_colegios)
        solo_ie = set_ie - set_colegios
        solo_colegios = set_colegios - set_ie
        
        print(f"\nANÁLISIS DE COINCIDENCIAS:")
        print(f"Códigos que coinciden: {len(coincidencias)}")
        print(f"Solo en IE: {len(solo_ie)}")
        print(f"Solo en colegios: {len(solo_colegios)}")
        print(f"Porcentaje de coincidencia: {len(coincidencias)/len(set_ie)*100:.1f}%")
        
        if len(coincidencias) > 0:
            print(f"\nPrimeras 10 coincidencias: {list(coincidencias)[:10]}")
            
            # Análisis de RER para códigos coincidentes
            col_rer = None
            for col in df_colegios.columns:
                if 'rer' in col.lower():
                    col_rer = col
                    break
            
            if col_rer:
                print(f"\nColumna RER detectada: {col_rer}")
                
                # Mostrar muestra de datos coincidentes
                df_muestra = df_colegios[df_colegios[col_codigo_colegio].astype(str).isin(list(coincidencias)[:20])]
                print(f"\nMuestra de datos coincidentes:")
                cols_mostrar = [col_codigo_colegio, col_rer]
                if 'nombre' in str(df_colegios.columns).lower():
                    col_nombre = None
                    for col in df_colegios.columns:
                        if 'nombre' in col.lower():
                            col_nombre = col
                            break
                    if col_nombre:
                        cols_mostrar.append(col_nombre)
                
                print(df_muestra[cols_mostrar].head(10).to_string(index=False))
                
                # Distribución de RER
                rer_dist = df_muestra[col_rer].value_counts()
                print(f"\nDistribución RER en códigos coincidentes:")
                print(rer_dist.head(10).to_string())
    
    conn.close()
    
    return {
        'col_codigo': col_codigo_colegio,
        'col_rer': col_rer if 'col_rer' in locals() else None,
        'coincidencias': len(coincidencias) if 'coincidencias' in locals() else 0
    }

def ejecutar_vinculacion_mejorada(df_colegios, info_cruces):
    """Ejecutar vinculación mejorada usando tabla colegios"""
    if df_colegios is None or info_cruces['coincidencias'] == 0:
        print("No hay suficientes datos para vinculación mejorada")
        return 0
    
    print(f"\n=== VINCULACIÓN MEJORADA CON TABLA COLEGIOS ===")
    print("=" * 60)
    
    col_codigo = info_cruces['col_codigo']
    col_rer = info_cruces['col_rer']
    
    if not col_codigo or not col_rer:
        print("ERROR: No se pudieron identificar columnas necesarias")
        return 0
    
    conn = sqlite3.connect('reasis_database.db')
    
    # Crear tabla temporal con datos de colegios
    df_temp = df_colegios[[col_codigo, col_rer]].copy()
    df_temp.columns = ['codigo_local_temp', 'rer_temp']
    df_temp = df_temp.dropna()
    
    # Insertar en tabla temporal
    df_temp.to_sql('temp_colegios_rer', conn, if_exists='replace', index=False)
    
    print(f"Tabla temporal creada con {len(df_temp)} registros")
    
    # Actualizar instituciones_educativas con RER desde tabla colegios
    cursor = conn.cursor()
    
    # Paso 1: Actualizar codigo_red para instituciones que no lo tienen
    update_sql = '''
        UPDATE instituciones_educativas 
        SET codigo_red = 
            CASE 
                WHEN t.rer_temp = '44' THEN 'RER FA 44'
                WHEN t.rer_temp = '47' THEN 'RER FA 47' 
                WHEN t.rer_temp = '48' THEN 'RER FA 48'
                WHEN t.rer_temp = '54' THEN 'RER FA 54'
                WHEN t.rer_temp = '72' THEN 'RER FA 72'
                WHEN t.rer_temp = '79' THEN 'RER FA 79'
                ELSE codigo_red
            END
        FROM temp_colegios_rer t
        WHERE instituciones_educativas.codigo_local = t.codigo_local_temp
        AND (instituciones_educativas.codigo_red IS NULL OR instituciones_educativas.codigo_red = '')
        AND t.rer_temp IN ('44', '47', '48', '54', '72', '79')
    '''
    
    cursor.execute(update_sql)
    actualizadas_nuevas = cursor.rowcount
    
    print(f"Instituciones nuevas vinculadas: {actualizadas_nuevas}")
    
    # Verificar resultado
    resultado_final = pd.read_sql_query('''
        SELECT 
            ie.codigo_red,
            r.nombre_completo,
            r.lugar,
            COUNT(*) as instituciones_vinculadas
        FROM instituciones_educativas ie
        INNER JOIN redes_fe_y_alegria r ON ie.codigo_red = r.codigo_red
        GROUP BY ie.codigo_red, r.nombre_completo, r.lugar
        ORDER BY instituciones_vinculadas DESC
    ''', conn)
    
    print(f"\nRESULTADO FINAL DESPUÉS DE VINCULACIÓN MEJORADA:")
    print("-" * 60)
    print(resultado_final.to_string(index=False))
    
    # Estadísticas finales
    total_vinculadas = pd.read_sql_query('SELECT COUNT(*) as count FROM instituciones_educativas WHERE codigo_red IS NOT NULL', conn).iloc[0, 0]
    total_instituciones = pd.read_sql_query('SELECT COUNT(*) as count FROM instituciones_educativas', conn).iloc[0, 0]
    
    print(f"\nESTADÍSTICAS FINALES:")
    print(f"Total instituciones: {total_instituciones}")
    print(f"Vinculadas con RER: {total_vinculadas}")
    print(f"Porcentaje vinculado: {total_vinculadas/total_instituciones*100:.1f}%")
    print(f"Mejora lograda: +{actualizadas_nuevas} instituciones")
    
    # Limpiar tabla temporal
    conn.execute('DROP TABLE IF EXISTS temp_colegios_rer')
    
    conn.commit()
    conn.close()
    
    return actualizadas_nuevas

def main():
    """Función principal"""
    print("EXPLORADOR Y VINCULADOR HOMOLOGACIÓN MANUAL LUCAS")
    print("=" * 70)
    
    # Paso 1: Explorar archivo
    df_colegios = explorar_archivo_homologacion()
    
    # Paso 2: Analizar cruces posibles
    if df_colegios is not None:
        info_cruces = analizar_cruces_posibles(df_colegios)
        
        # Paso 3: Ejecutar vinculación mejorada
        if info_cruces and info_cruces['coincidencias'] > 0:
            mejoras = ejecutar_vinculacion_mejorada(df_colegios, info_cruces)
            
            print(f"\n{'='*70}")
            print("VINCULACIÓN MEJORADA COMPLETADA")
            print(f"Instituciones adicionales vinculadas: {mejoras}")
            print("="*70)
        else:
            print(f"\nNo hay suficientes coincidencias para vinculación mejorada")
    else:
        print(f"\nNo se pudo procesar el archivo de homologación")

if __name__ == "__main__":
    main()