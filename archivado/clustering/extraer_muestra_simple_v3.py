#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EXTRACTOR SIMPLE DE MUESTRA DE INSTITUCIONES POR CLUSTER V3
"""

import sqlite3
import pandas as pd

def extraer_muestra_simple():
    """Extrae muestra básica de instituciones por cluster"""
    
    conn = sqlite3.connect('reasis_database_v3.db')
    
    # Consulta simplificada con campos que existen
    query = '''
    SELECT 
        c.codigo_modular,
        c.numero_fya,
        c.cluster_asignado,
        i.nombre_institucion,
        i.departamento,
        i.provincia,
        i.distrito,
        i.area_censo,
        i.nivel_educativo,
        i.modalidad,
        i.total_alumnos,
        i.total_docentes,
        i.total_secciones
    FROM resultados_clustering_v3 c
    LEFT JOIN instituciones_educativas i ON c.codigo_modular = i.codigo_modular
    ORDER BY c.cluster_asignado, i.total_alumnos DESC NULLS LAST
    '''
    
    df = pd.read_sql_query(query, conn)
    
    print("=" * 80)
    print("INSTITUCIONES REPRESENTATIVAS POR CLUSTER - CLUSTERING V3")
    print("=" * 80)
    print()
    
    # Para cada cluster, mostrar hasta 5 instituciones más representativas
    for cluster in sorted(df['cluster_asignado'].unique()):
        cluster_data = df[df['cluster_asignado'] == cluster].copy()
        
        print(f"CLUSTER {cluster} - {len(cluster_data)} instituciones ({len(cluster_data)/len(df)*100:.1f}%)")
        print("-" * 70)
        
        # Mostrar hasta 5 instituciones del cluster
        muestra = cluster_data.head(5)
        
        for idx, (_, inst) in enumerate(muestra.iterrows(), 1):
            nombre = str(inst['nombre_institucion'])[:50] + "..." if len(str(inst['nombre_institucion'])) > 50 else str(inst['nombre_institucion'])
            
            print(f"{idx}. [{inst['codigo_modular']}] Red {inst['numero_fya']}")
            print(f"   {nombre}")
            print(f"   📍 {inst['distrito']}, {inst['provincia']}, {inst['departamento']}")
            print(f"   📊 Área: {inst['area_censo']} | {inst['nivel_educativo']} | {inst['modalidad']}")
            
            # Datos académicos
            alumnos = inst['total_alumnos'] if pd.notna(inst['total_alumnos']) else 'N/D'
            docentes = inst['total_docentes'] if pd.notna(inst['total_docentes']) else 'N/D'
            secciones = inst['total_secciones'] if pd.notna(inst['total_secciones']) else 'N/D'
            print(f"   👥 Estudiantes: {alumnos} | Docentes: {docentes} | Secciones: {secciones}")
            print()
        
        # Estadísticas del cluster
        print("📈 Estadísticas del cluster:")
        
        # Promedios
        alumnos_prom = cluster_data['total_alumnos'].mean()
        docentes_prom = cluster_data['total_docentes'].mean()
        
        print(f"   • Promedio estudiantes: {alumnos_prom:.0f}" if pd.notna(alumnos_prom) else "   • Promedio estudiantes: N/D")
        print(f"   • Promedio docentes: {docentes_prom:.0f}" if pd.notna(docentes_prom) else "   • Promedio docentes: N/D")
        
        # Distribución por red
        redes_dist = cluster_data['numero_fya'].value_counts()
        redes_str = ", ".join([f"Red {red}: {count}" for red, count in redes_dist.head(3).items()])
        print(f"   • Redes principales: {redes_str}")
        
        # Distribución por área
        areas_dist = cluster_data['area_censo'].value_counts()
        areas_str = ", ".join([f"{area}: {count}" for area, count in areas_dist.items()])
        print(f"   • Distribución área: {areas_str}")
        
        print()
        print("=" * 70)
        print()
    
    # Estadísticas generales
    print("📊 RESUMEN GENERAL")
    print("-" * 40)
    print(f"🏫 Total instituciones: {len(df)}")
    print(f"🎯 Clusters generados: {len(df['cluster_asignado'].unique())}")
    print(f"🌐 Redes representadas: {sorted(df['numero_fya'].unique())}")
    print(f"🗺️ Departamentos: {len(df['departamento'].unique())}")
    
    # Distribución de tamaños de clusters
    print("\n📊 Distribución de clusters:")
    dist_clusters = df['cluster_asignado'].value_counts().sort_index()
    for cluster, count in dist_clusters.items():
        porcentaje = (count / len(df)) * 100
        print(f"   Cluster {cluster}: {count:3d} instituciones ({porcentaje:5.1f}%)")
    
    conn.close()
    
    return df

if __name__ == "__main__":
    df_resultado = extraer_muestra_simple()