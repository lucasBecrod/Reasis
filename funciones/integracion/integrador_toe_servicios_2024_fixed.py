#!/usr/bin/env python3
"""
Integrador de datos TOE (Tipo Organización Escolar) y servicios educativos 2024 - CORREGIDO
Proyecto Reasis - Variable X12_TOE + datos complementarios
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
    print("=== INTEGRADOR DATOS TOE Y SERVICIOS EDUCATIVOS 2024 (CORREGIDO) ===")
    
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
    
    # Convertir codigo_modular a entero y luego a string
    df_toe['codigo_modular'] = pd.to_numeric(df_toe['codigo_modular'], errors='coerce')
    df_toe = df_toe[df_toe['codigo_modular'].notna()].copy()  # Eliminar códigos inválidos
    df_toe['codigo_modular'] = df_toe['codigo_modular'].astype(int).astype(str)
    
    # Normalizar TOE
    df_toe['tipo_organizacion_normalizado'] = df_toe['tipo_organizacion_escolar'].apply(normalizar_toe)
    
    # Validar datos numéricos
    df_toe['estudiantes_2024'] = pd.to_numeric(df_toe['estudiantes_2024'], errors='coerce')
    df_toe['docentes_2024'] = pd.to_numeric(df_toe['docentes_2024'], errors='coerce')
    
    # Filtrar registros válidos (con código modular y al menos un dato útil)
    df_validos = df_toe[
        (df_toe['tipo_organizacion_normalizado'].notna()) |
        (df_toe['estudiantes_2024'].notna()) |
        (df_toe['docentes_2024'].notna())
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
    
    # Asegurar formato string en BD
    df_bd['codigo_modular'] = df_bd['codigo_modular'].astype(str)
    
    # Merge para encontrar coincidencias
    df_merged = df_bd.merge(
        df_validos, 
        on='codigo_modular', 
        how='inner'
    )
    
    # Identificar instituciones no encontradas
    codigos_bd = set(df_bd['codigo_modular'])
    codigos_toe = set(df_validos['codigo_modular'])
    
    codigos_no_encontrados = codigos_toe - codigos_bd
    
    print(f"   Instituciones en estudio: {len(df_bd)}")
    print(f"   Coincidencias encontradas: {len(df_merged)} ({len(df_merged)/len(df_bd)*100:.1f}%)")
    print(f"   Instituciones TOE no en nuestra BD: {len(codigos_no_encontrados)}")
    
    # Mostrar coincidencias encontradas
    if len(df_merged) > 0:
        print("\\n   MUESTRA DE COINCIDENCIAS:")
        muestra = df_merged[['codigo_modular', 'nombre_institucion', 'tipo_organizacion_normalizado', 'estudiantes_2024', 'docentes_2024']].head(10)
        print(muestra.to_string())
    
    # Mostrar instituciones no encontradas
    if len(codigos_no_encontrados) > 0:
        df_no_encontradas = df_validos[df_validos['codigo_modular'].isin(codigos_no_encontrados)]
        print("\\n   INSTITUCIONES QUE PODRIAN AGREGARSE:")
        print(df_no_encontradas[['codigo_modular', 'red_fya', 'tipo_organizacion_normalizado', 'estudiantes_2024']].head(10).to_string())
    
    # 6. Crear tabla de datos TOE y servicios
    print("\\n6. Creando tabla datos_toe_servicios_2024...")
    
    # Usar datos merged + datos no encontrados si el usuario quiere agregarlos
    df_final = df_merged.copy()
    
    # Si no hay coincidencias pero hay datos válidos, preguntar si agregar todo
    if len(df_merged) == 0 and len(df_validos) > 0:
        print("   No se encontraron coincidencias directas.")
        print("   Creando tabla con todos los datos TOE para referencia futura...")
        
        # Crear df_final con estructura consistente
        df_final = df_validos.copy()
        df_final['nombre_institucion'] = 'PENDIENTE_VALIDACION'
        df_final['numero_fya'] = df_final['red_fya'].str.extract(r'(\d+)')[0]
    
    if len(df_final) == 0:
        print("   No hay datos para crear la tabla")
        return
    
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
            fecha_integracion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            estado_vinculacion TEXT DEFAULT 'VALIDADO'
        )
    """)
    
    # Insertar datos
    registros_insertados = 0
    for _, row in df_final.iterrows():
        try:
            cursor.execute("""
                INSERT INTO datos_toe_servicios_2024 
                (codigo_modular, nombre_institucion, numero_fya, red_fya, modalidad, 
                 nivel_educativo, tipo_organizacion_original, tipo_organizacion_normalizado,
                 estudiantes_2024, docentes_2024, observaciones, estado_vinculacion)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(row['codigo_modular']),
                row.get('nombre_institucion', 'PENDIENTE_VALIDACION'),
                str(row.get('numero_fya', '')),
                str(row.get('red_fya', '')),
                str(row.get('modalidad', '')),
                str(row.get('nivel_educativo', '')),
                str(row.get('tipo_organizacion_escolar', '')),
                str(row.get('tipo_organizacion_normalizado', '')),
                int(row['estudiantes_2024']) if pd.notna(row['estudiantes_2024']) else None,
                int(row['docentes_2024']) if pd.notna(row['docentes_2024']) else None,
                str(row.get('observaciones', '')),
                'VALIDADO' if 'nombre_institucion' in row and row['nombre_institucion'] != 'PENDIENTE_VALIDACION' else 'PENDIENTE_VALIDACION'
            ))
            registros_insertados += 1
        except Exception as e:
            print(f"   Error insertando registro {row['codigo_modular']}: {e}")
    
    conn.commit()
    print(f"   Tabla creada con {registros_insertados} registros")
    
    # 7. Estadísticas finales
    print("\\n7. ESTADISTICAS FINALES:")
    
    toe_final = df_final['tipo_organizacion_normalizado'].notna().sum()
    estudiantes_final = df_final['estudiantes_2024'].notna().sum()
    docentes_final = df_final['docentes_2024'].notna().sum()
    
    print(f"   Variable X12_TOE disponible: {toe_final} instituciones")
    print(f"   Datos estudiantes 2024: {estudiantes_final} instituciones")
    print(f"   Datos docentes 2024: {docentes_final} instituciones")
    
    if toe_final > 0:
        distribucion_final = df_final['tipo_organizacion_normalizado'].value_counts()
        print(f"\\n   Distribución TOE:")
        for tipo, cantidad in distribucion_final.items():
            print(f"     {tipo}: {cantidad}")
    
    # 8. Verificar tabla creada
    print("\\n8. Verificación final:")
    
    df_verificacion = pd.read_sql_query("SELECT * FROM datos_toe_servicios_2024 LIMIT 5", conn)
    print("   Muestra de tabla creada:")
    if len(df_verificacion) > 0:
        print(df_verificacion[['codigo_modular', 'tipo_organizacion_normalizado', 'estudiantes_2024', 'docentes_2024', 'estado_vinculacion']].to_string())
    else:
        print("   [Tabla vacía]")
    
    conn.close()
    
    print("\\n¡INTEGRACION TOE Y SERVICIOS COMPLETADA!")
    print(f"RESULTADO: Nueva tabla con {registros_insertados} registros de TOE y servicios 2024")

if __name__ == "__main__":
    main()