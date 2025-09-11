#!/usr/bin/env python3
"""
Constructor de Índices Metodológicos - Proyecto Reasis
Implementa estandarización z-score y construcción de índices compuestos
según las fórmulas de la matriz de operacionalización.

ÍNDICES A CONSTRUIR:
- X1_NVC: Nivel de Vulnerabilidad Contextual
- X4_IDD: Índice de Desempeño Docente  
- X10_IE: Infraestructura Educativa
- Estandarización z-score para todas las variables continuas
"""

import pandas as pd
import sqlite3
import numpy as np

def estandarizar_zscore(serie):
    """Aplicar estandarización z-score a una serie"""
    media = serie.mean()
    desviacion = serie.std()
    return (serie - media) / desviacion

def construir_base_metodologica():
    """Construir base de datos consolidada para análisis metodológico"""
    print("=== CONSTRUCTOR ÍNDICES METODOLÓGICOS ===")
    print("1. CONSOLIDANDO BASE DE DATOS METODOLÓGICA...")
    
    conn = sqlite3.connect('reasis_database.db')
    
    # Base principal: instituciones educativas
    query_base = """
        SELECT codigo_modular, nombre_institucion, numero_fya, nombre_red_fya_matched,
               area_censo, modalidad, nivel_educativo
        FROM instituciones_educativas
    """
    df_base = pd.read_sql_query(query_base, conn)
    print(f"   Base: {len(df_base)} instituciones")
    
    # Y1: ILA - Índice de Logro Académico
    print("\n2. CALCULANDO Y1_ILA (Índice de Logro Académico)...")
    query_ila = """
        SELECT codigo_modular,
               AVG(CASE WHEN materia LIKE '%Matem%tica%' THEN nivel_logro_numerico END) as prom_matematica,
               AVG(CASE WHEN materia LIKE '%Comunicaci%n%' THEN nivel_logro_numerico END) as prom_comunicacion,
               COUNT(*) as total_estudiantes
        FROM resultados_academicos
        WHERE codigo_modular IS NOT NULL 
        GROUP BY codigo_modular
        HAVING COUNT(*) >= 10
    """
    df_ila = pd.read_sql_query(query_ila, conn)
    df_ila['Y1_ILA'] = (df_ila['prom_matematica'] + df_ila['prom_comunicacion']) / 2
    df_ila['Y1_ILA_zscore'] = estandarizar_zscore(df_ila['Y1_ILA'])
    
    df_base = df_base.merge(df_ila[['codigo_modular', 'Y1_ILA', 'Y1_ILA_zscore', 'total_estudiantes']], 
                           on='codigo_modular', how='left')
    print(f"   ILA calculado: {df_ila['Y1_ILA'].notna().sum()} instituciones")
    
    # Y2: TD - Tendencia de Desempeño
    print("\n3. CALCULANDO Y2_TD (Tendencia de Desempeño)...")
    query_td = """
        SELECT codigo_modular, año,
               AVG(CASE WHEN materia LIKE '%Matem%tica%' THEN nivel_logro_numerico END) as prom_mat,
               AVG(CASE WHEN materia LIKE '%Comunicaci%n%' THEN nivel_logro_numerico END) as prom_com
        FROM resultados_academicos
        WHERE codigo_modular IS NOT NULL AND año IN (2022, 2024)
        GROUP BY codigo_modular, año
    """
    df_td = pd.read_sql_query(query_td, conn)
    df_td['ila_año'] = (df_td['prom_mat'] + df_td['prom_com']) / 2
    
    # Calcular TD: (ILA_2024 - ILA_2022) / ILA_2022
    df_pivot = df_td.pivot(index='codigo_modular', columns='año', values='ila_año')
    if 2022 in df_pivot.columns and 2024 in df_pivot.columns:
        df_td_calc = df_pivot.dropna().copy()
        df_td_calc['Y2_TD'] = (df_td_calc[2024] - df_td_calc[2022]) / df_td_calc[2022]
        df_td_calc['Y2_TD_zscore'] = estandarizar_zscore(df_td_calc['Y2_TD'])
        
        # Categorizar TD según metodología
        df_td_calc['Y2_TD_categoria'] = 'estancamiento'
        df_td_calc.loc[df_td_calc['Y2_TD'] > 0.05, 'Y2_TD_categoria'] = 'mejora'
        df_td_calc.loc[df_td_calc['Y2_TD'] < -0.05, 'Y2_TD_categoria'] = 'deterioro'
        
        df_base = df_base.merge(df_td_calc[['Y2_TD', 'Y2_TD_zscore', 'Y2_TD_categoria']], 
                               left_on='codigo_modular', right_index=True, how='left')
        print(f"   TD calculado: {df_td_calc['Y2_TD'].notna().sum()} instituciones")
    
    # X1: NVC - Nivel de Vulnerabilidad Contextual
    print("\n4. CONSTRUYENDO X1_NVC (Nivel Vulnerabilidad Contextual)...")
    query_nvc = """
        SELECT eib.codigo_modular, eib.quintil_pobreza,
               ie.area_censo,
               eib.servicios_agua, eib.servicios_internet
        FROM datos_eib_minedu eib
        JOIN instituciones_educativas ie ON eib.codigo_modular = ie.codigo_modular
    """
    df_nvc = pd.read_sql_query(query_nvc, conn)
    
    if len(df_nvc) > 0:
        # Normalizar quintil pobreza (1-5) a (0-1): quintil más alto = más vulnerable
        df_nvc['nbi_normalizado'] = (df_nvc['quintil_pobreza'] - 1) / 4
        
        # Ruralidad: Rural = 1, Urbano = 0
        df_nvc['ruralidad_bin'] = df_nvc['area_censo'].map({'Rural': 1, 'Urbana': 0}).fillna(0.5)
        
        # Servicios básicos: 1 - promedio de servicios (invertido para vulnerabilidad)
        df_nvc['servicios_promedio'] = df_nvc[['servicios_agua', 'servicios_internet']].mean(axis=1, skipna=True)
        df_nvc['servicios_inv'] = 1 - df_nvc['servicios_promedio'].fillna(0.5)
        
        # Fórmula NVC: (NBI × 0.4) + (Ruralidad × 0.3) + (1-Servicios × 0.3)
        df_nvc['X1_NVC'] = (df_nvc['nbi_normalizado'] * 0.4 + 
                           df_nvc['ruralidad_bin'] * 0.3 + 
                           df_nvc['servicios_inv'] * 0.3)
        df_nvc['X1_NVC_zscore'] = estandarizar_zscore(df_nvc['X1_NVC'])
        
        df_base = df_base.merge(df_nvc[['codigo_modular', 'X1_NVC', 'X1_NVC_zscore']], 
                               on='codigo_modular', how='left')
        print(f"   NVC calculado: {df_nvc['X1_NVC'].notna().sum()} instituciones")
    
    # X2: TR - Tipo de Ruralidad (ya categorizado)
    print("\n5. PROCESANDO X2_TR (Tipo de Ruralidad)...")
    # Mapear área censo a valores ordinales
    df_base['X2_TR'] = df_base['area_censo'].map({'Urbana': 1, 'Rural': 2}).fillna(2)
    
    # Mejorar con datos específicos de César si existen
    query_ruralidad = """
        SELECT codigo_modular, tipo_ruralidad_cesar
        FROM ruralidad_cesar
        WHERE tipo_ruralidad_cesar IS NOT NULL
    """
    df_rural = pd.read_sql_query(query_ruralidad, conn)
    if len(df_rural) > 0:
        # Mapear Rural 1, Rural 2, Rural 3 a valores ordinales
        mapeo_rural = {'Rural 1': 2, 'Rural 2': 3, 'Rural 3': 4}
        df_rural['X2_TR_mejorado'] = df_rural['tipo_ruralidad_cesar'].map(mapeo_rural)
        
        # Actualizar con datos más específicos donde estén disponibles
        df_base = df_base.merge(df_rural[['codigo_modular', 'X2_TR_mejorado']], 
                               on='codigo_modular', how='left')
        df_base['X2_TR'] = df_base['X2_TR_mejorado'].fillna(df_base['X2_TR'])
        print(f"   TR mejorado: {df_rural['X2_TR_mejorado'].notna().sum()} instituciones específicas")
    
    # X4: IDD - Índice de Desempeño Docente
    print("\n6. CONSTRUYENDO X4_IDD (Índice Desempeño Docente)...")
    query_idd = """
        SELECT codigo_modular_vinculado as codigo_modular,
               AVG((nota_matematica + nota_comunicacion + nota_digital + nota_genero)/4) as idd_promedio,
               COUNT(*) as total_docentes
        FROM docentes_data
        WHERE codigo_modular_vinculado IS NOT NULL 
          AND nota_matematica IS NOT NULL
        GROUP BY codigo_modular_vinculado
    """
    df_idd = pd.read_sql_query(query_idd, conn)
    df_idd['X4_IDD'] = df_idd['idd_promedio']
    df_idd['X4_IDD_zscore'] = estandarizar_zscore(df_idd['X4_IDD'])
    
    df_base = df_base.merge(df_idd[['codigo_modular', 'X4_IDD', 'X4_IDD_zscore', 'total_docentes']], 
                           on='codigo_modular', how='left')
    print(f"   IDD calculado: {df_idd['X4_IDD'].notna().sum()} instituciones")
    
    # X5: ED - Estabilidad Docente
    print("\n7. PROCESANDO X5_ED (Estabilidad Docente)...")
    try:
        query_ed = """
            SELECT codigo_modular, estabilidad_calculada
            FROM x5_ed_estabilidad_docente
        """
        df_ed = pd.read_sql_query(query_ed, conn)
        df_ed['X5_ED'] = df_ed['estabilidad_calculada']
        df_ed['X5_ED_zscore'] = estandarizar_zscore(df_ed['X5_ED'])
        
        df_base = df_base.merge(df_ed[['codigo_modular', 'X5_ED', 'X5_ED_zscore']], 
                               on='codigo_modular', how='left')
        print(f"   ED procesado: {df_ed['X5_ED'].notna().sum()} instituciones")
    except:
        print("   ED no disponible - tabla faltante")
    
    # X10: IE - Infraestructura Educativa
    print("\n8. CONSTRUYENDO X10_IE (Infraestructura Educativa)...")
    # Combinar datos de servicios básicos y conectividad
    query_servicios = """
        SELECT codigo_modular,
               servicios_agua, servicios_electricidad, servicios_internet
        FROM datos_eib_minedu
    """
    df_servicios = pd.read_sql_query(query_servicios, conn)
    
    # Calcular índice de servicios básicos (0-1)
    if len(df_servicios) > 0:
        servicios_cols = ['servicios_agua', 'servicios_electricidad', 'servicios_internet']
        df_servicios['servicios_basicos'] = df_servicios[servicios_cols].mean(axis=1, skipna=True)
        
        # Por simplicidad, usar servicios básicos como proxy de IE
        # Fórmula completa requeriría datos de mobiliario y biblioteca
        df_servicios['X10_IE'] = df_servicios['servicios_basicos'] * 0.4 + 0.3  # Asumir valores medios para otros componentes
        df_servicios['X10_IE_zscore'] = estandarizar_zscore(df_servicios['X10_IE'])
        
        df_base = df_base.merge(df_servicios[['codigo_modular', 'X10_IE', 'X10_IE_zscore']], 
                               on='codigo_modular', how='left')
        print(f"   IE calculado: {df_servicios['X10_IE'].notna().sum()} instituciones")
    
    # X11: RED - Ratio Estudiante-Docente
    print("\n9. CALCULANDO X11_RED (Ratio Estudiante-Docente)...")
    query_red = """
        SELECT codigo_modular,
               estudiantes_2024, docentes_2024
        FROM datos_toe_servicios_2024
        WHERE estudiantes_2024 IS NOT NULL AND docentes_2024 IS NOT NULL AND docentes_2024 > 0
    """
    df_red = pd.read_sql_query(query_red, conn)
    df_red['X11_RED'] = df_red['estudiantes_2024'] / df_red['docentes_2024']
    df_red['X11_RED_zscore'] = estandarizar_zscore(df_red['X11_RED'])
    
    df_base = df_base.merge(df_red[['codigo_modular', 'X11_RED', 'X11_RED_zscore']], 
                           on='codigo_modular', how='left')
    print(f"   RED calculado: {df_red['X11_RED'].notna().sum()} instituciones")
    
    # X12: TOE - Tipo de Organización Escolar
    print("\n10. PROCESANDO X12_TOE (Tipo Organización Escolar)...")
    query_toe = """
        SELECT codigo_modular, tipo_organizacion_normalizado
        FROM datos_toe_servicios_2024
        WHERE tipo_organizacion_normalizado IS NOT NULL
    """
    df_toe = pd.read_sql_query(query_toe, conn)
    
    # Mapear a valores ordinales según metodología
    mapeo_toe = {
        'Polidocente': 1,
        'Multigrado': 2, 
        'Unidocente': 3
    }
    df_toe['X12_TOE'] = df_toe['tipo_organizacion_normalizado'].map(mapeo_toe)
    
    df_base = df_base.merge(df_toe[['codigo_modular', 'X12_TOE']], 
                           on='codigo_modular', how='left')
    print(f"   TOE procesado: {df_toe['X12_TOE'].notna().sum()} instituciones")
    
    # X15: MEIB - Modalidad EIB
    print("\n11. PROCESANDO X15_MEIB (Modalidad EIB)...")
    query_meib = """
        SELECT codigo_modular, modalidad_eib
        FROM datos_eib_minedu
        WHERE modalidad_eib IS NOT NULL
    """
    df_meib = pd.read_sql_query(query_meib, conn)
    
    # Codificar modalidad EIB
    mapeo_meib = {
        'fortalecimiento': 1,
        'revitalización': 2
    }
    df_meib['X15_MEIB'] = df_meib['modalidad_eib'].map(mapeo_meib)
    
    df_base = df_base.merge(df_meib[['codigo_modular', 'X15_MEIB']], 
                           on='codigo_modular', how='left')
    print(f"   MEIB procesado: {df_meib['X15_MEIB'].notna().sum()} instituciones")
    
    conn.close()
    
    return df_base

def guardar_indices_metodologicos(df_indices):
    """Guardar índices en nueva tabla metodológica"""
    print("\n12. GUARDANDO ÍNDICES METODOLÓGICOS...")
    
    conn = sqlite3.connect('reasis_database.db')
    cursor = conn.cursor()
    
    # Crear tabla de índices metodológicos
    cursor.execute("DROP TABLE IF EXISTS indices_metodologicos")
    cursor.execute("""
        CREATE TABLE indices_metodologicos (
            codigo_modular TEXT PRIMARY KEY,
            nombre_institucion TEXT,
            numero_fya TEXT,
            nombre_red_fya_matched TEXT,
            
            -- Variables dependientes
            Y1_ILA REAL,
            Y1_ILA_zscore REAL,
            Y2_TD REAL,
            Y2_TD_zscore REAL,
            Y2_TD_categoria TEXT,
            
            -- Variables independientes
            X1_NVC REAL,
            X1_NVC_zscore REAL,
            X2_TR INTEGER,
            X4_IDD REAL,
            X4_IDD_zscore REAL,
            X5_ED REAL,
            X5_ED_zscore REAL,
            X10_IE REAL,
            X10_IE_zscore REAL,
            X11_RED REAL,
            X11_RED_zscore REAL,
            X12_TOE INTEGER,
            X15_MEIB INTEGER,
            
            -- Metadatos
            total_estudiantes INTEGER,
            total_docentes INTEGER,
            fecha_calculo TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (codigo_modular) REFERENCES instituciones_educativas(codigo_modular)
        )
    """)
    
    # Seleccionar solo las columnas que existen en la tabla
    columnas_tabla = [
        'codigo_modular', 'nombre_institucion', 'numero_fya', 'nombre_red_fya_matched',
        'Y1_ILA', 'Y1_ILA_zscore', 'Y2_TD', 'Y2_TD_zscore', 'Y2_TD_categoria',
        'X1_NVC', 'X1_NVC_zscore', 'X2_TR', 'X4_IDD', 'X4_IDD_zscore', 
        'X5_ED', 'X5_ED_zscore', 'X10_IE', 'X10_IE_zscore',
        'X11_RED', 'X11_RED_zscore', 'X12_TOE', 'X15_MEIB',
        'total_estudiantes', 'total_docentes'
    ]
    
    # Filtrar solo columnas disponibles
    columnas_disponibles = [col for col in columnas_tabla if col in df_indices.columns]
    df_para_insertar = df_indices[columnas_disponibles].copy()
    
    # Insertar datos
    df_para_insertar.to_sql('indices_metodologicos', conn, if_exists='replace', index=False, method='multi')
    
    conn.commit()
    conn.close()
    
    print(f"   [OK] {len(df_indices)} registros guardados en tabla indices_metodologicos")

def generar_reporte_indices():
    """Generar reporte de completitud de índices"""
    print("\n13. GENERANDO REPORTE DE ÍNDICES...")
    
    conn = sqlite3.connect('reasis_database.db')
    
    df_reporte = pd.read_sql_query("SELECT * FROM indices_metodologicos", conn)
    
    variables_metodologicas = [
        'Y1_ILA', 'Y2_TD', 'X1_NVC', 'X2_TR', 'X4_IDD', 
        'X5_ED', 'X10_IE', 'X11_RED', 'X12_TOE', 'X15_MEIB'
    ]
    
    print("\nREPORTE COMPLETITUD ÍNDICES METODOLÓGICOS:")
    print("-" * 60)
    
    total_vars = len(variables_metodologicas)
    vars_disponibles = 0
    
    for var in variables_metodologicas:
        if var in df_reporte.columns:
            count = df_reporte[var].notna().sum()
            porcentaje = (count / len(df_reporte)) * 100
            
            if count >= 50:
                status = "[OK] SUFICIENTE"
                vars_disponibles += 1
            elif count > 0:
                status = "[PARCIAL]"
                vars_disponibles += 0.5
            else:
                status = "[NO] FALTANTE"
        else:
            count = 0
            porcentaje = 0.0
            status = "[NO] FALTANTE"
            
        print(f"{var:10}: {count:3d} instituciones ({porcentaje:5.1f}%) {status}")
    
    completitud_final = (vars_disponibles / total_vars) * 100
    
    print(f"\nCOMPLETITUD ÍNDICES: {completitud_final:.1f}%")
    print(f"Variables disponibles: {vars_disponibles:.1f}/{total_vars}")
    
    if completitud_final >= 75:
        print("ESTADO: [OK] LISTO PARA CLUSTERING K-MEANS")
    
    # Estadísticas descriptivas para variables estandarizadas
    print(f"\nESTADISTICAS Z-SCORE (media=0, std=1):")
    zscore_vars = [col for col in df_reporte.columns if '_zscore' in col]
    for var in zscore_vars:
        if df_reporte[var].notna().sum() > 0:
            media = df_reporte[var].mean()
            std = df_reporte[var].std()
            print(f"{var:15}: media={media:6.3f}, std={std:6.3f}")
    
    conn.close()
    
    return completitud_final

def main():
    print("CONSTRUCTOR ÍNDICES METODOLÓGICOS - PROYECTO REASIS")
    print("=" * 60)
    
    # Construir base metodológica con índices
    df_indices = construir_base_metodologica()
    
    # Guardar en base de datos
    guardar_indices_metodologicos(df_indices)
    
    # Generar reporte final
    completitud = generar_reporte_indices()
    
    print(f"\n[COMPLETADO] Índices metodológicos creados con {completitud:.1f}% completitud")
    
    return df_indices, completitud

if __name__ == "__main__":
    df_indices, completitud = main()