#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ANÁLISIS DETALLADO CLUSTERING V3 - PROYECTO REASIS
Extracción completa de resultados de tipologías institucionales
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime

def analizar_clustering_v3():
    """Análisis completo del clustering v3"""
    
    # Conectar a la base de datos
    conn = sqlite3.connect('reasis_database_v3.db')
    
    print("=" * 80)
    print("ANÁLISIS DETALLADO CLUSTERING V3 - TIPOLOGÍAS INSTITUCIONALES")
    print("=" * 80)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 1. OBTENER DATOS COMPLETOS
    query = '''
    SELECT 
        c.codigo_modular,
        c.numero_fya,
        c.cluster_asignado,
        c.silhouette_score,
        i.nombre_institucion,
        z.*
    FROM resultados_clustering_v3 c
    LEFT JOIN indices_zscores_avanzado z ON c.codigo_modular = z.CODIGO_MODULAR
    LEFT JOIN instituciones_educativas i ON c.codigo_modular = i.codigo_modular
    '''
    
    df = pd.read_sql_query(query, conn)
    
    # Variables metodológicas principales
    variables_principales = [
        'Y1_ILA_ZS', 'Y2_TD_ZS', 'Y3_PR_ZS', 
        'X1_NVC_ZS', 'X2_TR_ZS', 'X4_IDD_ZS', 
        'X6_CDD_ZS', 'X10_IE_ZS', 'X11_RED_ZS', 
        'X12_TOE_ZS'
    ]
    
    # Variables adicionales de interés
    variables_adicionales = [
        'X13_TMATRC_ZS', 'X14_NIVEL_EDUCATIVO_ZS', 'X16_MODALIDAD_ZS',
        'X17_GESTION_ZS', 'X24_GPMD_ZS', 'X25_POBLACION_DISTRITO_ZS'
    ]
    
    todas_variables = variables_principales + variables_adicionales
    
    print("1. INFORMACIÓN GENERAL DEL CLUSTERING")
    print("-" * 50)
    print(f"Total instituciones analizadas: {len(df)}")
    print(f"Número de clusters: {len(df['cluster_asignado'].unique())}")
    print(f"Silhouette Score promedio: {df['silhouette_score'].mean():.4f}")
    print(f"Variables utilizadas: {len(todas_variables)}")
    print()
    
    # 2. DISTRIBUCIÓN POR CLUSTERS
    print("2. DISTRIBUCIÓN POR CLUSTERS")
    print("-" * 50)
    distribucion = df['cluster_asignado'].value_counts().sort_index()
    for cluster, count in distribucion.items():
        porcentaje = (count / len(df)) * 100
        print(f"Cluster {cluster}: {count:3d} instituciones ({porcentaje:5.1f}%)")
    print()
    
    # 3. CENTROIDES DE LOS CLUSTERS
    print("3. CENTROIDES DE LOS 6 CLUSTERS")
    print("-" * 50)
    print("Variables metodológicas principales:")
    print()
    
    centroides = df.groupby('cluster_asignado')[variables_principales].mean()
    
    # Mostrar centroides principales
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    pd.set_option('display.precision', 3)
    
    print(centroides)
    print()
    
    # 4. VARIABLES MÁS DISCRIMINANTES
    print("4. VARIABLES MÁS DISCRIMINANTES")
    print("-" * 50)
    
    # Calcular desviación estándar entre centroides para cada variable
    std_entre_clusters = centroides.std(axis=0).sort_values(ascending=False)
    
    print("Variables ordenadas por poder discriminante:")
    for i, (var, std_val) in enumerate(std_entre_clusters.items(), 1):
        var_limpio = var.replace('_ZS', '')
        print(f"{i:2d}. {var_limpio}: {std_val:.3f}")
    print()
    
    # 5. DISTRIBUCIÓN TERRITORIAL (POR REDES)
    print("5. DISTRIBUCIÓN TERRITORIAL POR CLUSTER")
    print("-" * 50)
    
    tabla_redes = pd.crosstab(df['cluster_asignado'], df['numero_fya'], margins=True)
    print("Distribución por Red Fe y Alegría:")
    print(tabla_redes)
    print()
    
    # Porcentajes por cluster
    print("Porcentajes por cluster:")
    tabla_porcentajes = pd.crosstab(df['cluster_asignado'], df['numero_fya'], normalize='index') * 100
    print(tabla_porcentajes.round(1))
    print()
    
    # 6. CARACTERIZACIÓN DE CLUSTERS
    print("6. CARACTERIZACIÓN DETALLADA DE CLUSTERS")
    print("-" * 50)
    
    for cluster in sorted(df['cluster_asignado'].unique()):
        cluster_data = df[df['cluster_asignado'] == cluster]
        n_inst = len(cluster_data)
        
        print(f"\n[CLUSTER {cluster}] ({n_inst} instituciones - {n_inst/len(df)*100:.1f}%)")
        print("-" * 30)
        
        # Redes principales
        redes_principales = cluster_data['numero_fya'].value_counts().head(3)
        print(f"Redes principales: {dict(redes_principales)}")
        
        # Variables más características (valores z-score más extremos)
        centroides_cluster = centroides.loc[cluster]
        valores_extremos = centroides_cluster[abs(centroides_cluster) > 0.5].sort_values(key=abs, ascending=False)
        
        if len(valores_extremos) > 0:
            print("Características distintivas (z-score > 0.5):")
            for var, valor in valores_extremos.head(5).items():
                var_limpio = var.replace('_ZS', '')
                direccion = "alto" if valor > 0 else "bajo"
                print(f"  - {var_limpio}: {valor:+.2f} ({direccion})")
        
        # Ejemplos de instituciones
        print("\nEjemplos de instituciones:")
        ejemplos = cluster_data[['codigo_modular', 'nombre_institucion', 'numero_fya']].head(3)
        for _, inst in ejemplos.iterrows():
            nombre = inst['nombre_institucion'][:50] + "..." if len(str(inst['nombre_institucion'])) > 50 else inst['nombre_institucion']
            print(f"  - {inst['codigo_modular']} | Red {inst['numero_fya']} | {nombre}")
    
    print()
    
    # 7. RESUMEN ESTADÍSTICO ADICIONAL
    print("7. ESTADÍSTICAS ADICIONALES")
    print("-" * 50)
    
    # Centroides de variables adicionales
    centroides_adicionales = df.groupby('cluster_asignado')[variables_adicionales].mean()
    print("Centroides variables adicionales:")
    print(centroides_adicionales)
    print()
    
    # Análisis de dispersión intra-cluster
    print("Dispersión promedio intra-cluster (por variable principal):")
    for var in variables_principales:
        dispersiones = []
        for cluster in sorted(df['cluster_asignado'].unique()):
            cluster_data = df[df['cluster_asignado'] == cluster][var].dropna()
            if len(cluster_data) > 1:
                dispersiones.append(cluster_data.std())
        
        dispersion_promedio = np.mean(dispersiones) if dispersiones else 0
        var_limpio = var.replace('_ZS', '')
        print(f"  {var_limpio}: {dispersion_promedio:.3f}")
    
    conn.close()
    
    print()
    print("=" * 80)
    print("ANÁLISIS COMPLETADO")
    print("=" * 80)

if __name__ == "__main__":
    analizar_clustering_v3()