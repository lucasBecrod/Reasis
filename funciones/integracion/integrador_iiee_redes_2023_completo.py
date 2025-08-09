#!/usr/bin/env python3
"""
Integrador completo IIEE Redes Rurales 2023
Proyecto Reasis - Metodología CLAUDE.md con enfoque robusto

ESTRATEGIAS DE INTEGRACIÓN:
1. Vinculación directa por código modular
2. Vinculación por coincidencia fuzzy de nombres
3. Agregación de instituciones faltantes
4. Robustecimiento de asignaciones de red
5. Integración de datos académicos 2023
"""

import pandas as pd
import sqlite3
from fuzzywuzzy import fuzz, process
import re

def limpiar_estudiantes_2023(valor):
    """Limpia y convierte datos de estudiantes a numérico"""
    if pd.isna(valor):
        return None
    
    valor_str = str(valor).strip()
    
    if valor_str in ['H', 'M', 'Total', 'h', 'm', 'total']:
        return None
    
    try:
        return int(float(valor_str))
    except:
        return None

def normalizar_nombre_ie(nombre):
    """Normaliza nombres de instituciones para matching"""
    if pd.isna(nombre):
        return ""
    
    # Convertir a string y limpiar
    nombre_limpio = str(nombre).upper().strip()
    
    # Remover números comunes que pueden variar
    nombre_limpio = re.sub(r'^\d+\s*', '', nombre_limpio)  # Números al inicio
    nombre_limpio = re.sub(r'\s+\d+\s*$', '', nombre_limpio)  # Números al final
    
    # Remover caracteres especiales comunes
    nombre_limpio = re.sub(r'[^\w\s]', ' ', nombre_limpio)
    
    # Normalizar espacios
    nombre_limpio = ' '.join(nombre_limpio.split())
    
    return nombre_limpio

def main():
    print("=== INTEGRADOR COMPLETO IIEE REDES RURALES 2023 ===")
    
    archivo = r"C:\Users\lucas\Proyectos\Reasis\assets\Consultoria\Información de referencia\Estadista IIEE Estudiantes RER FyA 2024 y 2025\Redes Rurales FyA - Lista de instituciones educativas (v25012024) v22022024 (2) (1).xlsx"
    
    # 1. Cargar y limpiar datos del Excel
    print("1. Cargando datos de instituciones educativas 2023...")
    
    try:
        df_excel = pd.read_excel(archivo, sheet_name='Redes Educativas Rurales 2023')
        
        # Limpiar primera fila si contiene headers
        if pd.isna(df_excel.iloc[0]['Código Modular']):
            df_excel = df_excel.iloc[1:].reset_index(drop=True)
            
        # Renombrar columnas
        df_clean = df_excel.rename(columns={
            'Código Modular': 'codigo_modular',
            'Código de local': 'codigo_local',
            'RED RURAL FYA': 'red_rural_fya',
            'Institución Educativa': 'nombre_institucion',
            'Nivel de Modalidad': 'nivel_modalidad',
            'Centro Poblado': 'centro_poblado',
            'Distrito': 'distrito',
            'Provincia': 'provincia',
            'Departamento': 'departamento',
            'Número de Estudiantes 2023 *': 'estudiantes_2023',
            'Número de Docentes': 'docentes_2023',
            'Número de secciones': 'secciones_2023'
        }).copy()
        
        # Limpiar datos
        df_clean['codigo_modular'] = pd.to_numeric(df_clean['codigo_modular'], errors='coerce')
        df_clean = df_clean[df_clean['codigo_modular'].notna()].copy()
        df_clean['codigo_modular'] = df_clean['codigo_modular'].astype(int).astype(str)
        
        # Limpiar datos académicos
        df_clean['estudiantes_2023'] = df_clean['estudiantes_2023'].apply(limpiar_estudiantes_2023)
        df_clean['docentes_2023'] = pd.to_numeric(df_clean['docentes_2023'], errors='coerce')
        df_clean['secciones_2023'] = pd.to_numeric(df_clean['secciones_2023'], errors='coerce')
        
        # Extraer número de red
        df_clean['numero_red'] = df_clean['red_rural_fya'].str.extract(r'RER FA (\\d+)')[0]
        
        # Normalizar nombres para matching
        df_clean['nombre_normalizado'] = df_clean['nombre_institucion'].apply(normalizar_nombre_ie)
        
        print(f"   Registros válidos procesados: {len(df_clean)}")
        
    except Exception as e:
        print(f"   Error al cargar archivo: {e}")
        return
    
    # 2. Cargar datos de la base de datos
    print("\\n2. Cargando datos de base de datos actual...")
    
    conn = sqlite3.connect('reasis_database.db')
    
    df_bd = pd.read_sql_query("""
        SELECT codigo_modular, nombre_institucion, numero_fya, nombre_red_fya_matched,
               region, distrito, total_alumnos, docentes_total, total_secciones,
               entra_estudio_clustering
        FROM instituciones_educativas
    """, conn)
    
    df_bd['codigo_modular'] = df_bd['codigo_modular'].astype(str)
    df_bd['nombre_normalizado'] = df_bd['nombre_institucion'].apply(normalizar_nombre_ie)
    
    print(f"   Registros en BD: {len(df_bd)}")
    print(f"   Del estudio: {len(df_bd[df_bd['entra_estudio_clustering'] == 'Sí'])}")
    
    # 3. ESTRATEGIA 1: Vinculación directa por código modular
    print("\\n3. VINCULACIÓN DIRECTA POR CÓDIGO MODULAR...")
    
    df_vinculacion_directa = df_bd.merge(
        df_clean,
        on='codigo_modular',
        how='inner',
        suffixes=('_bd', '_excel')
    )
    
    print(f"   Vinculaciones directas: {len(df_vinculacion_directa)}")
    
    # 4. ESTRATEGIA 2: Vinculación fuzzy por nombres
    print("\\n4. VINCULACIÓN FUZZY PARA INSTITUCIONES SIN CÓDIGO COINCIDENTE...")
    
    # Identificar instituciones no vinculadas por código
    codigos_vinculados = set(df_vinculacion_directa['codigo_modular'])
    
    df_excel_no_vinculado = df_clean[~df_clean['codigo_modular'].isin(codigos_vinculados)].copy()
    df_bd_no_vinculado = df_bd[~df_bd['codigo_modular'].isin(codigos_vinculados)].copy()
    
    print(f"   Excel sin vincular: {len(df_excel_no_vinculado)}")
    print(f"   BD sin vincular: {len(df_bd_no_vinculado)}")
    
    vinculaciones_fuzzy = []
    
    if len(df_excel_no_vinculado) > 0 and len(df_bd_no_vinculado) > 0:
        print("   Ejecutando matching fuzzy...")
        
        # Crear lista de nombres para matching
        nombres_bd = df_bd_no_vinculado['nombre_normalizado'].tolist()
        codigos_bd = df_bd_no_vinculado['codigo_modular'].tolist()
        
        for _, row_excel in df_excel_no_vinculado.iterrows():
            nombre_excel = row_excel['nombre_normalizado']
            
            if len(nombre_excel.strip()) > 3:  # Solo nombres con contenido significativo
                # Buscar mejor match
                mejor_match, score = process.extractOne(nombre_excel, nombres_bd, scorer=fuzz.ratio)
                
                if score >= 80:  # Umbral de similitud
                    # Encontrar índice del mejor match
                    idx_match = nombres_bd.index(mejor_match)
                    codigo_bd_match = codigos_bd[idx_match]
                    
                    vinculaciones_fuzzy.append({
                        'codigo_modular_excel': row_excel['codigo_modular'],
                        'codigo_modular_bd': codigo_bd_match,
                        'nombre_excel': row_excel['nombre_institucion'],
                        'nombre_bd': df_bd_no_vinculado[df_bd_no_vinculado['codigo_modular'] == codigo_bd_match]['nombre_institucion'].iloc[0],
                        'score': score,
                        'red_excel': row_excel['red_rural_fya'],
                        'estudiantes_2023': row_excel['estudiantes_2023'],
                        'docentes_2023': row_excel['docentes_2023'],
                        'secciones_2023': row_excel['secciones_2023']
                    })
    
    print(f"   Vinculaciones fuzzy encontradas: {len(vinculaciones_fuzzy)}")
    
    # Mostrar muestra de vinculaciones fuzzy
    if len(vinculaciones_fuzzy) > 0:
        print("\\n   MUESTRA DE VINCULACIONES FUZZY:")
        for i, vinc in enumerate(vinculaciones_fuzzy[:5], 1):
            print(f"   {i}. Score {vinc['score']}%")
            print(f"      Excel: {vinc['nombre_excel'][:50]}...")
            print(f"      BD:    {vinc['nombre_bd'][:50]}...")
    
    # 5. ESTRATEGIA 3: Identificar instituciones completamente nuevas
    print("\\n5. IDENTIFICANDO INSTITUCIONES COMPLETAMENTE NUEVAS...")
    
    codigos_fuzzy_excel = {v['codigo_modular_excel'] for v in vinculaciones_fuzzy}
    
    df_completamente_nuevas = df_excel_no_vinculado[
        ~df_excel_no_vinculado['codigo_modular'].isin(codigos_fuzzy_excel)
    ].copy()
    
    print(f"   Instituciones completamente nuevas: {len(df_completamente_nuevas)}")
    
    if len(df_completamente_nuevas) > 0:
        print("\\n   MUESTRA DE INSTITUCIONES NUEVAS:")
        nuevas_muestra = df_completamente_nuevas[['codigo_modular', 'red_rural_fya', 'nombre_institucion', 'estudiantes_2023']].head(10)
        print(nuevas_muestra.to_string())
    
    # 6. Crear tabla integrada con datos 2023
    print("\\n6. CREANDO TABLA INTEGRADA datos_iiee_2023...")
    
    cursor = conn.cursor()
    
    # Eliminar tabla si existe
    cursor.execute("DROP TABLE IF EXISTS datos_iiee_2023")
    
    # Crear tabla nueva
    cursor.execute("""
        CREATE TABLE datos_iiee_2023 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo_modular_excel TEXT NOT NULL,
            codigo_modular_bd TEXT,
            tipo_vinculacion TEXT,
            score_matching INTEGER,
            nombre_institucion_excel TEXT,
            nombre_institucion_bd TEXT,
            red_rural_fya TEXT,
            numero_red TEXT,
            nivel_modalidad TEXT,
            distrito TEXT,
            provincia TEXT,
            departamento TEXT,
            estudiantes_2023 INTEGER,
            docentes_2023 INTEGER,
            secciones_2023 INTEGER,
            en_estudio_clustering TEXT DEFAULT 'No',
            fecha_integracion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    registros_insertados = 0
    
    # Insertar vinculaciones directas
    for _, row in df_vinculacion_directa.iterrows():
        cursor.execute("""
            INSERT INTO datos_iiee_2023 
            (codigo_modular_excel, codigo_modular_bd, tipo_vinculacion, score_matching,
             nombre_institucion_excel, nombre_institucion_bd, red_rural_fya, numero_red,
             nivel_modalidad, distrito, provincia, departamento,
             estudiantes_2023, docentes_2023, secciones_2023, en_estudio_clustering)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            row['codigo_modular'],
            row['codigo_modular'],
            'DIRECTA',
            100,
            row['nombre_institucion_excel'],
            row['nombre_institucion_bd'],
            row['red_rural_fya'],
            row['numero_red'],
            row['nivel_modalidad'],
            row['distrito_excel'],
            row['provincia'],
            row['departamento'],
            int(row['estudiantes_2023']) if pd.notna(row['estudiantes_2023']) else None,
            int(row['docentes_2023']) if pd.notna(row['docentes_2023']) else None,
            int(row['secciones_2023']) if pd.notna(row['secciones_2023']) else None,
            row['entra_estudio_clustering']
        ))
        registros_insertados += 1
    
    # Insertar vinculaciones fuzzy
    for vinc in vinculaciones_fuzzy:
        cursor.execute("""
            INSERT INTO datos_iiee_2023 
            (codigo_modular_excel, codigo_modular_bd, tipo_vinculacion, score_matching,
             nombre_institucion_excel, nombre_institucion_bd, red_rural_fya, numero_red,
             estudiantes_2023, docentes_2023, secciones_2023)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            vinc['codigo_modular_excel'],
            vinc['codigo_modular_bd'],
            'FUZZY',
            vinc['score'],
            vinc['nombre_excel'],
            vinc['nombre_bd'],
            vinc['red_excel'],
            vinc['red_excel'].replace('RER FA ', ''),
            int(vinc['estudiantes_2023']) if pd.notna(vinc['estudiantes_2023']) else None,
            int(vinc['docentes_2023']) if pd.notna(vinc['docentes_2023']) else None,
            int(vinc['secciones_2023']) if pd.notna(vinc['secciones_2023']) else None
        ))
        registros_insertados += 1
    
    # Insertar instituciones completamente nuevas
    for _, row in df_completamente_nuevas.iterrows():
        cursor.execute("""
            INSERT INTO datos_iiee_2023 
            (codigo_modular_excel, tipo_vinculacion, score_matching,
             nombre_institucion_excel, red_rural_fya, numero_red,
             nivel_modalidad, distrito, provincia, departamento,
             estudiantes_2023, docentes_2023, secciones_2023)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            row['codigo_modular'],
            'NUEVA',
            0,
            row['nombre_institucion'],
            row['red_rural_fya'],
            row['numero_red'],
            row['nivel_modalidad'],
            row['distrito'],
            row['provincia'],
            row['departamento'],
            int(row['estudiantes_2023']) if pd.notna(row['estudiantes_2023']) else None,
            int(row['docentes_2023']) if pd.notna(row['docentes_2023']) else None,
            int(row['secciones_2023']) if pd.notna(row['secciones_2023']) else None
        ))
        registros_insertados += 1
    
    conn.commit()
    print(f"   Tabla creada con {registros_insertados} registros")
    
    # 7. Estadísticas finales
    print("\\n7. ESTADÍSTICAS FINALES DE INTEGRACIÓN...")
    
    df_estadisticas = pd.read_sql_query("""
        SELECT 
            tipo_vinculacion,
            COUNT(*) as cantidad,
            COUNT(CASE WHEN estudiantes_2023 IS NOT NULL THEN 1 END) as con_estudiantes,
            COUNT(CASE WHEN docentes_2023 IS NOT NULL THEN 1 END) as con_docentes,
            COUNT(CASE WHEN secciones_2023 IS NOT NULL THEN 1 END) as con_secciones
        FROM datos_iiee_2023 
        GROUP BY tipo_vinculacion
    """, conn)
    
    print("   Distribución por tipo de vinculación:")
    print(df_estadisticas.to_string())
    
    # Por redes del estudio
    redes_estudio = ['44', '47', '48', '54', '72', '79']
    print("\\n   Por redes del estudio:")
    
    for red in redes_estudio:
        df_red_stats = pd.read_sql_query("""
            SELECT COUNT(*) as total,
                   COUNT(CASE WHEN estudiantes_2023 IS NOT NULL THEN 1 END) as con_est_2023
            FROM datos_iiee_2023 
            WHERE numero_red = ?
        """, conn, params=[red])
        
        if df_red_stats.iloc[0]['total'] > 0:
            total = df_red_stats.iloc[0]['total']
            con_est = df_red_stats.iloc[0]['con_est_2023']
            print(f"   Red {red}: {total} IIEE, {con_est} con datos estudiantes 2023")
    
    # 8. Verificación final
    print("\\n8. VERIFICACIÓN FINAL:")
    
    df_verificacion = pd.read_sql_query("""
        SELECT tipo_vinculacion, codigo_modular_excel, nombre_institucion_excel, 
               red_rural_fya, estudiantes_2023, docentes_2023, secciones_2023
        FROM datos_iiee_2023 
        WHERE numero_red IN ('44', '47', '48', '54', '72', '79')
        LIMIT 10
    """, conn)
    
    print("   Muestra de registros integrados:")
    print(df_verificacion[['tipo_vinculacion', 'red_rural_fya', 'estudiantes_2023', 'docentes_2023']].to_string())
    
    conn.close()
    
    print("\\n¡INTEGRACIÓN COMPLETA FINALIZADA!")
    print(f"\\nRESULTADOS:")
    print(f"   - Vinculaciones directas: {len(df_vinculacion_directa)}")
    print(f"   - Vinculaciones fuzzy: {len(vinculaciones_fuzzy)}")
    print(f"   - Instituciones nuevas: {len(df_completamente_nuevas)}")
    print(f"   - Total registros integrados: {registros_insertados}")
    print(f"   - Nueva tabla: datos_iiee_2023")

if __name__ == "__main__":
    main()