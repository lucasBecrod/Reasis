#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Exportador de Instituciones Educativas - Proyecto Reasis
Script para exportar la tabla de instituciones a CSV para análisis manual
"""

import sqlite3
import pandas as pd
from pathlib import Path

def exportar_instituciones_csv():
    """Exporta la tabla de instituciones educativas a CSV"""
    print("EXPORTADOR DE INSTITUCIONES EDUCATIVAS A CSV")
    print("=" * 60)
    
    # 1. Conectar a base de datos
    print("\n1. CONECTANDO A BASE DE DATOS")
    print("-" * 40)
    
    db_path = "reasis_database.db"
    
    if not Path(db_path).exists():
        print(f"Error: Base de datos no encontrada: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        
        # 2. Exportar tabla principal
        print("\n2. EXPORTANDO TABLA INSTITUCIONES_EDUCATIVAS_V2_MEJORADA")
        print("-" * 40)
        
        # Consulta para obtener todos los datos ordenados
        query = """
            SELECT 
                id,
                codigo_modular,
                codigo_local,
                nombre_institucion,
                tipo_institucion,
                region,
                provincia,
                distrito,
                nivel_educativo,
                modalidad_especifica,
                gestion,
                area_censo,
                es_rural,
                es_fya,
                latitud,
                longitud,
                altitud,
                total_alumnos,
                alumnos_hombres,
                alumnos_mujeres,
                total_docentes,
                docentes_hombres,
                docentes_mujeres,
                total_secciones,
                numero_fya,
                unidad_ejecutora,
                multiplicidad1,
                multiplicidad2,
                estado_validacion,
                director,
                telefono,
                email,
                fecha_actualizacion
            FROM instituciones_educativas_v2_mejorada
            ORDER BY region, provincia, distrito, codigo_modular
        """
        
        df = pd.read_sql_query(query, conn)
        
        print(f"Total registros exportados: {len(df)}")
        print(f"Total columnas: {len(df.columns)}")
        
        # 3. Crear carpeta si no existe
        output_dir = Path("data consolidada")
        output_dir.mkdir(exist_ok=True)
        
        # 4. Exportar CSV principal
        csv_path = output_dir / "instituciones_educativas_v2_completa.csv"
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        
        print(f"Archivo exportado: {csv_path}")
        
        # 5. Crear también una versión resumida para exploración rápida
        print("\n3. EXPORTANDO VERSION RESUMIDA")
        print("-" * 40)
        
        df_resumido = df[[
            'codigo_modular', 'nombre_institucion', 'region', 'provincia', 'distrito',
            'nivel_educativo', 'modalidad_especifica', 'area_censo', 'es_rural', 'es_fya',
            'total_alumnos', 'total_docentes', 'numero_fya'
        ]].copy()
        
        csv_resumido_path = output_dir / "instituciones_educativas_resumido.csv"
        df_resumido.to_csv(csv_resumido_path, index=False, encoding='utf-8-sig')
        
        print(f"Archivo resumido exportado: {csv_resumido_path}")
        
        # 6. Exportar listado único de instituciones (consolidando servicios múltiples)
        print("\n4. EXPORTANDO LISTADO UNICO DE INSTITUCIONES")
        print("-" * 40)
        
        # Agrupar por codigo_local para consolidar instituciones con múltiples servicios
        df_unico = df.groupby(['codigo_local', 'nombre_institucion', 'region', 'provincia', 'distrito']).agg({
            'codigo_modular': lambda x: ', '.join(x.astype(str)),
            'nivel_educativo': lambda x: ', '.join(x.unique()),
            'modalidad_especifica': lambda x: ', '.join(x.unique()) if x.nunique() == 1 else ', '.join(x.unique()),
            'area_censo': 'first',
            'es_rural': 'first',
            'es_fya': 'first',
            'total_alumnos': 'sum',
            'total_docentes': 'sum',
            'latitud': 'first',
            'longitud': 'first',
            'numero_fya': 'first',
            'unidad_ejecutora': 'first'
        }).reset_index()
        
        # Renombrar columnas para claridad
        df_unico.rename(columns={
            'codigo_modular': 'codigos_modulares',
            'nivel_educativo': 'niveles_educativos',
            'modalidad_especifica': 'modalidades'
        }, inplace=True)
        
        csv_unico_path = output_dir / "instituciones_unicas_consolidadas.csv"
        df_unico.to_csv(csv_unico_path, index=False, encoding='utf-8-sig')
        
        print(f"Instituciones únicas consolidadas: {len(df_unico)}")
        print(f"Archivo consolidado exportado: {csv_unico_path}")
        
        # 7. Resumen estadístico
        print("\n5. RESUMEN ESTADISTICO")
        print("-" * 40)
        
        print(f"Total servicios educativos: {len(df)}")
        print(f"Total instituciones físicas únicas: {len(df_unico)}")
        print(f"Promedio servicios por institución: {len(df)/len(df_unico):.2f}")
        
        print(f"\nDistribución por modalidad:")
        for modalidad, count in df['modalidad_especifica'].value_counts().head(10).items():
            print(f"- {modalidad}: {count} servicios")
        
        print(f"\nDistribución rural/urbano:")
        rural_urbano = df.groupby(['area_censo', 'es_rural']).size()
        for (area, rural), count in rural_urbano.items():
            tipo = "Rural" if rural == 1 else "Urbano"
            print(f"- Área {area} + Flag {tipo}: {count} servicios")
        
        conn.close()
        
        print(f"\n✓ EXPORTACION COMPLETADA")
        print("=" * 60)
        print("📁 Archivos generados en carpeta 'data consolidada':")
        print("   1. instituciones_educativas_v2_completa.csv - Tabla completa con todos los campos")
        print("   2. instituciones_educativas_resumido.csv - Versión resumida para exploración")
        print("   3. instituciones_unicas_consolidadas.csv - Instituciones físicas únicas")
        
    except Exception as e:
        print(f"Error durante la exportación: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    exportar_instituciones_csv()