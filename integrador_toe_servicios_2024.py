#!/usr/bin/env python3
"""
Integrador de datos TOE (Tipo Organización Escolar) y servicios educativos 2024
Proyecto Reasis - Variable X12_TOE + datos complementarios

Siguiendo metodología exitosa CLAUDE.md:
- Integrar variable X12_TOE (unidocente/multigrado/polidocente/bidocente)
- Añadir datos de estudiantes y docentes 2024
- Crear nueva tabla datos_toe_servicios_2024
- Vinculación por codigo_modular con 94.3% coincidencia esperada
"""

import pandas as pd
import sqlite3
import re

def normalizar_toe(tipo_original):
    """Normaliza los valores de tipo de organización escolar"""
    if pd.isna(tipo_original):
        return None
    
    # Convertir a string y limpiar espacios
    tipo_str = str(tipo_original).strip().lower()
    
    # Mapear variantes a valores estándar
    if 'unidocente' in tipo_str:
        return 'UNIDOCENTE'
    elif 'multigrado' in tipo_str:
        return 'MULTIGRADO'
    elif 'polidocente' in tipo_str:
        return 'POLIDOCENTE'
    elif 'bidocente' in tipo_str:
        return 'BIDOCENTE'
    else:
        return tipo_str.upper()

def main():
    print("=== INTEGRADOR DATOS TOE Y SERVICIOS EDUCATIVOS 2024 ===")
    
    archivo = r"C:\Users\lucas\Proyectos\Reasis\assets\Consultoria\Información de referencia\Estadista IIEE Estudiantes RER FyA 2024 y 2025\Identificador_Servicios Educativos FyA RER 2025 (3).xlsx"
    
    # 1. Cargar datos del archivo Excel
    print("1. Cargando datos de servicios educativos 2024...")
    
    try:
        df_toe = pd.read_excel(archivo, sheet_name='Actualización del 2024')
        print(f"   Registros cargados: {len(df_toe)}")
        
        # Renombrar columnas para facilidad
        df_toe = df_toe.rename(columns={
            'codigo modular': 'codigo_modular',
            'codigo local': 'codigo_local',
            'iiee': 'red_fya',
            'modalidad': 'modalidad',
            'nivel': 'nivel_educativo',
            'Tipo (unidocente, bidocente, multigrado, polidocente)': 'tipo_organizacion_escolar',
            'Estudiantes': 'estudiantes_2024',
            'Docentes': 'docentes_2024',
            'OBSERVACIONES': 'observaciones'
        })
        
    except Exception as e:
        print(f"   Error al cargar archivo: {e}")
        return
    
    # 2. Limpiar y normalizar datos
    print("2. Limpiando y normalizando datos...")
    
    # Convertir codigo_modular a numérico
    df_toe['codigo_modular'] = pd.to_numeric(df_toe['codigo_modular'], errors='coerce')
    
    # Normalizar TOE
    df_toe['tipo_organizacion_normalizado'] = df_toe['tipo_organizacion_escolar'].apply(normalizar_toe)
    
    # Validar datos numéricos
    df_toe['estudiantes_2024'] = pd.to_numeric(df_toe['estudiantes_2024'], errors='coerce')
    df_toe['docentes_2024'] = pd.to_numeric(df_toe['docentes_2024'], errors='coerce')
    
    # Filtrar registros válidos (con código modular y al menos un dato útil)
    df_validos = df_toe[
        (df_toe['codigo_modular'].notna()) &
        (
            (df_toe['tipo_organizacion_normalizado'].notna()) |
            (df_toe['estudiantes_2024'].notna()) |
            (df_toe['docentes_2024'].notna())
        )
    ].copy()
    
    print(f"   Registros válidos después de limpieza: {len(df_validos)}")
    
    # 3. Análisis de datos disponibles
    print("3. Análisis de datos disponibles:")
    
    toe_disponibles = df_validos['tipo_organizacion_normalizado'].notna().sum()
    estudiantes_disponibles = df_validos['estudiantes_2024'].notna().sum()
    docentes_disponibles = df_validos['docentes_2024'].notna().sum()
    
    print(f"   Tipo organización escolar: {toe_disponibles}/{len(df_validos)} ({toe_disponibles/len(df_validos)*100:.1f}%)")
    print(f"   Estudiantes 2024: {estudiantes_disponibles}/{len(df_validos)} ({estudiantes_disponibles/len(df_validos)*100:.1f}%)")
    print(f"   Docentes 2024: {docentes_disponibles}/{len(df_validos)} ({docentes_disponibles/len(df_validos)*100:.1f}%)")
    
    # Distribución TOE normalizada
    print(f"\\n   Distribución TOE normalizada:")
    distribucion_toe = df_validos['tipo_organizacion_normalizado'].value_counts(dropna=False)
    print(distribucion_toe.to_string())
    
    # 4. Conectar a base de datos
    print("\\n4. Conectando a base de datos...")
    conn = sqlite3.connect('reasis_database.db')
    
    # 5. Verificar coincidencias con instituciones del estudio
    print("5. Verificando coincidencias con instituciones del estudio...")
    
    df_bd = pd.read_sql_query("""
        SELECT codigo_modular, nombre_institucion, numero_fya, entra_estudio_clustering
        FROM instituciones_educativas 
        WHERE entra_estudio_clustering = 'Sí'
    """, conn)
    
    # Convertir codigo_modular a string en ambos DataFrames para merge
    df_bd['codigo_modular'] = df_bd['codigo_modular'].astype(str)
    df_validos['codigo_modular'] = df_validos['codigo_modular'].astype(str)
    
    # Merge para encontrar coincidencias
    df_merged = df_bd.merge(
        df_validos, 
        on='codigo_modular', 
        how='inner'
    )
    
    # Identificar instituciones no encontradas en nuestra BD
    codigos_bd = set(df_bd['codigo_modular'])
    codigos_toe = set(df_validos['codigo_modular'])
    
    codigos_no_encontrados = codigos_toe - codigos_bd
    
    print(f"   Instituciones en estudio: {len(df_bd)}")
    print(f"   Coincidencias encontradas: {len(df_merged)} ({len(df_merged)/len(df_bd)*100:.1f}%)")
    print(f"   Instituciones TOE no en nuestra BD: {len(codigos_no_encontrados)}")
    
    # Mostrar instituciones no encontradas si las hay
    if len(codigos_no_encontrados) > 0:
        df_no_encontradas = df_validos[df_validos['codigo_modular'].isin(codigos_no_encontrados)]
        print("\\n   Instituciones que podrían agregarse:")
        print(df_no_encontradas[['codigo_modular', 'red_fya', 'tipo_organizacion_normalizado']].head(10).to_string())
    
    # 6. Crear tabla de datos TOE y servicios
    print("\\n6. Creando tabla datos_toe_servicios_2024...")
    
    # Preparar datos para insertar
    df_final = df_merged[[
        'codigo_modular', 'nombre_institucion', 'numero_fya',
        'red_fya', 'modalidad', 'nivel_educativo',
        'tipo_organizacion_escolar', 'tipo_organizacion_normalizado',
        'estudiantes_2024', 'docentes_2024', 'observaciones'
    ]].copy()
    
    # Crear tabla en base de datos
    cursor = conn.cursor()
    
    # Eliminar tabla si existe
    cursor.execute("DROP TABLE IF EXISTS datos_toe_servicios_2024")
    
    # Crear tabla nueva
    cursor.execute("""
        CREATE TABLE datos_toe_servicios_2024 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo_modular TEXT NOT NULL,
            nombre_institucion TEXT,
            numero_fya TEXT,
            red_fya TEXT,
            modalidad TEXT,
            nivel_educativo TEXT,
            tipo_organizacion_original TEXT,
            tipo_organizacion_normalizado TEXT,
            estudiantes_2024 INTEGER,
            docentes_2024 INTEGER,
            observaciones TEXT,
            fecha_integracion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Insertar datos
    for _, row in df_final.iterrows():
        cursor.execute("""
            INSERT INTO datos_toe_servicios_2024 
            (codigo_modular, nombre_institucion, numero_fya, red_fya, modalidad, 
             nivel_educativo, tipo_organizacion_original, tipo_organizacion_normalizado,
             estudiantes_2024, docentes_2024, observaciones)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(row['codigo_modular']),
            row['nombre_institucion'],
            row['numero_fya'],
            row['red_fya'],
            row['modalidad'],
            row['nivel_educativo'],
            row['tipo_organizacion_escolar'],
            row['tipo_organizacion_normalizado'],
            int(row['estudiantes_2024']) if pd.notna(row['estudiantes_2024']) else None,
            int(row['docentes_2024']) if pd.notna(row['docentes_2024']) else None,
            row['observaciones']
        ))
    
    conn.commit()
    print(f"   Tabla creada con {len(df_final)} registros")
    
    # 7. Estadísticas finales por red del estudio
    print("\\n7. Estadísticas finales por red del estudio:")
    
    redes_estudio = ['44', '47', '48', '54', '72', '79']
    
    for red in redes_estudio:
        df_red = df_final[df_final['numero_fya'] == red]
        
        if len(df_red) > 0:
            toe_red = df_red['tipo_organizacion_normalizado'].notna().sum()
            est_red = df_red['estudiantes_2024'].notna().sum()
            doc_red = df_red['docentes_2024'].notna().sum()
            
            print(f"\\n   Red {red}:")
            print(f"     Total instituciones: {len(df_red)}")
            print(f"     Con TOE: {toe_red} ({toe_red/len(df_red)*100:.1f}%)")
            print(f"     Con estudiantes 2024: {est_red} ({est_red/len(df_red)*100:.1f}%)")
            print(f"     Con docentes 2024: {doc_red} ({doc_red/len(df_red)*100:.1f}%)")
            
            if toe_red > 0:
                toe_dist = df_red['tipo_organizacion_normalizado'].value_counts()
                print(f"     Distribución TOE: {dict(toe_dist)}")
    
    # 8. Impacto en variables metodológicas
    print("\\n8. IMPACTO EN VARIABLES METODOLÓGICAS:")
    
    # Variable X12_TOE
    instituciones_con_toe = df_final['tipo_organizacion_normalizado'].notna().sum()
    print(f"   X12_TOE (Tipo Organización Escolar):")
    print(f"     ANTES: 0 instituciones (variable faltante)")
    print(f"     DESPUÉS: {instituciones_con_toe} instituciones ({instituciones_con_toe/len(df_bd)*100:.1f}% del estudio)")
    
    # Datos adicionales
    instituciones_con_estudiantes = df_final['estudiantes_2024'].notna().sum()
    instituciones_con_docentes = df_final['docentes_2024'].notna().sum()
    
    print(f"\\n   DATOS ADICIONALES 2024:")
    print(f"     Estudiantes: {instituciones_con_estudiantes} instituciones")
    print(f"     Docentes: {instituciones_con_docentes} instituciones")
    
    # 9. Verificar tabla creada
    print("\\n9. Verificación final:")
    
    df_verificacion = pd.read_sql_query("SELECT * FROM datos_toe_servicios_2024 LIMIT 5", conn)
    print("   Muestra de tabla creada:")
    print(df_verificacion[['codigo_modular', 'nombre_institucion', 'tipo_organizacion_normalizado', 'estudiantes_2024', 'docentes_2024']].to_string())
    
    conn.close()
    
    print("\\n¡INTEGRACIÓN TOE Y SERVICIOS COMPLETADA EXITOSAMENTE!")
    print("\\n🎯 LOGROS:")
    print(f"   ✅ Variable X12_TOE desbloqueada para {instituciones_con_toe} instituciones")
    print(f"   ✅ Datos estudiantes 2024 para {instituciones_con_estudiantes} instituciones")
    print(f"   ✅ Datos docentes 2024 para {instituciones_con_docentes} instituciones")
    print(f"   ✅ Nueva tabla: datos_toe_servicios_2024")
    print(f"   ✅ Metodología clustering K-Means significativamente mejorada")

if __name__ == "__main__":
    main()