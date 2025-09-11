#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EXTRACTOR DE MUESTRA DE INSTITUCIONES POR CLUSTER V3
Selecciona instituciones representativas de cada tipología
"""

import sqlite3
import pandas as pd
import numpy as np

def extraer_muestra_instituciones():
    """Extrae muestra representativa de instituciones por cluster"""
    
    conn = sqlite3.connect('reasis_database_v3.db')
    
    # Consulta completa con información institucional
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
        i.total_estudiantes_2024,
        i.total_docentes_2024,
        i.total_secciones_2024,
        -- Variables clave
        z.Y1_ILA_ZS,
        z.Y2_TD_ZS,
        z.Y3_PR_ZS,
        z.X2_TR_ZS,
        z.X4_IDD_ZS,
        z.X6_CDD_ZS,
        z.X11_RED_ZS
    FROM resultados_clustering_v3 c
    LEFT JOIN instituciones_educativas i ON c.codigo_modular = i.codigo_modular
    LEFT JOIN indices_zscores_avanzado z ON c.codigo_modular = z.CODIGO_MODULAR
    ORDER BY c.cluster_asignado, i.total_estudiantes_2024 DESC
    '''
    
    df = pd.read_sql_query(query, conn)
    
    print("=" * 80)
    print("MUESTRA REPRESENTATIVA DE INSTITUCIONES POR CLUSTER V3")
    print("=" * 80)
    print()
    
    # Para cada cluster, mostrar instituciones más representativas
    for cluster in sorted(df['cluster_asignado'].unique()):
        cluster_data = df[df['cluster_asignado'] == cluster].copy()
        
        print(f"CLUSTER {cluster} - {len(cluster_data)} instituciones")
        print("-" * 60)
        
        # Seleccionar muestra diversa:
        # 1. La más grande (por estudiantes)
        # 2. Una representativa de cada red principal
        # 3. Una con características típicas del cluster
        
        muestra = []
        
        # 1. Más grande del cluster
        if len(cluster_data) > 0:
            mas_grande = cluster_data.iloc[0]  # Ya ordenado por estudiantes DESC
            muestra.append(("MAS_GRANDE", mas_grande))
        
        # 2. Representativa de redes principales (hasta 2)
        redes_principales = cluster_data['numero_fya'].value_counts().head(2)
        for red in redes_principales.index:
            red_data = cluster_data[cluster_data['numero_fya'] == red]
            if len(red_data) > 0:
                # Seleccionar la del medio (mediana por estudiantes)
                idx_medio = len(red_data) // 2
                representativa = red_data.iloc[idx_medio]
                muestra.append((f"RED_{red}", representativa))
        
        # 3. Si hay pocas instituciones, agregar todas
        if len(cluster_data) <= 5:
            for idx, inst in cluster_data.iterrows():
                if not any(inst['codigo_modular'] == m[1]['codigo_modular'] for m in muestra):
                    muestra.append(("ADICIONAL", inst))
        
        # Mostrar muestra seleccionada
        print(f"Muestra seleccionada ({len(muestra)} instituciones):")
        print()
        
        for tipo, inst in muestra:
            # Información básica
            nombre = str(inst['nombre_institucion'])[:45] + "..." if len(str(inst['nombre_institucion'])) > 45 else str(inst['nombre_institucion'])
            
            print(f"[{tipo}] {inst['codigo_modular']} - Red {inst['numero_fya']}")
            print(f"  Nombre: {nombre}")
            print(f"  Ubicación: {inst['distrito']}, {inst['provincia']}, {inst['departamento']}")
            print(f"  Área: {inst['area_censo']} | Nivel: {inst['nivel_educativo']} | Modalidad: {inst['modalidad']}")
            print(f"  Estudiantes: {inst['total_estudiantes_2024'] or 'N/D'} | Docentes: {inst['total_docentes_2024'] or 'N/D'} | Secciones: {inst['total_secciones_2024'] or 'N/D'}")
            
            # Variables clave (z-scores más significativas)
            variables_clave = []
            for var, val in [('Y1_ILA', inst['Y1_ILA_ZS']), ('Y2_TD', inst['Y2_TD_ZS']), 
                            ('Y3_PR', inst['Y3_PR_ZS']), ('X2_TR', inst['X2_TR_ZS']),
                            ('X4_IDD', inst['X4_IDD_ZS']), ('X6_CDD', inst['X6_CDD_ZS']),
                            ('X11_RED', inst['X11_RED_ZS'])]:
                if pd.notna(val) and abs(val) > 0.3:  # Solo mostrar valores significativos
                    direccion = "alto" if val > 0 else "bajo"
                    variables_clave.append(f"{var}: {val:+.2f} ({direccion})")
            
            if variables_clave:
                print(f"  Variables distintivas: {' | '.join(variables_clave)}")
            
            print()
        
        # Resumen estadístico del cluster
        print("Resumen estadístico del cluster:")
        print(f"  - Estudiantes promedio: {cluster_data['total_estudiantes_2024'].mean():.0f}")
        print(f"  - Redes representadas: {list(cluster_data['numero_fya'].unique())}")
        print(f"  - Departamentos: {list(cluster_data['departamento'].unique())}")
        print(f"  - Modalidades: {list(cluster_data['modalidad'].unique())}")
        
        print()
        print("=" * 60)
        print()
    
    # Resumen general
    print("RESUMEN GENERAL")
    print("-" * 40)
    print(f"Total instituciones analizadas: {len(df)}")
    print(f"Clusters identificados: {len(df['cluster_asignado'].unique())}")
    print(f"Redes representadas: {sorted(df['numero_fya'].unique())}")
    print(f"Departamentos cubiertos: {len(df['departamento'].unique())}")
    
    # Exportar muestra completa a CSV para análisis adicional
    output_file = 'muestra_instituciones_clustering_v3.csv'
    df.to_csv(output_file, index=False, encoding='utf-8')
    print(f"\nDatos completos exportados a: {output_file}")
    
    conn.close()

if __name__ == "__main__":
    extraer_muestra_instituciones()