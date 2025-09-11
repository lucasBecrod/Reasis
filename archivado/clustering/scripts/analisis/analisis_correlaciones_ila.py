import sqlite3
import pandas as pd
import numpy as np

conn = sqlite3.connect('reasis_database.db')

# Analizar correlaciones con ILA usando datos reales
query_full = '''
SELECT 
    im.Y1_ILA,
    im.numero_fya,
    ie.total_alumnos,
    ie.total_docentes,
    ie.total_secciones,
    ie.es_rural,
    ie.es_eib,
    ie.altitud,
    ie.region,
    ie.nivel_educativo,
    CASE 
        WHEN ie.total_docentes > 0 AND ie.total_alumnos > 0 
        THEN ROUND(CAST(ie.total_alumnos AS FLOAT) / ie.total_docentes, 2)
        ELSE NULL 
    END as ratio_alumno_docente
FROM indices_metodologicos im
JOIN instituciones_educativas ie ON im.codigo_modular = ie.codigo_modular
WHERE im.Y1_ILA IS NOT NULL
'''

df = pd.read_sql_query(query_full, conn)

print('=== ANÁLISIS DE CORRELACIONES CON ILA ===')
# Calcular correlaciones
correlaciones = df[['Y1_ILA', 'total_alumnos', 'total_docentes', 'total_secciones', 
                   'es_rural', 'es_eib', 'altitud', 'ratio_alumno_docente']].corr()['Y1_ILA'].sort_values(ascending=False)

print('Correlaciones con Y1_ILA:')
for var, corr in correlaciones.items():
    if var != 'Y1_ILA':
        print(f'{var:20s}: {corr:7.4f}')

print('\n=== ANÁLISIS POR CATEGORÍAS ===')
# Por red
print('ILA promedio por RED:')
ila_por_red = df.groupby('numero_fya')['Y1_ILA'].agg(['mean', 'count', 'std']).round(4)
print(ila_por_red)

print('\nILA promedio por REGIÓN:')
ila_por_region = df.groupby('region')['Y1_ILA'].agg(['mean', 'count', 'std']).round(4)
print(ila_por_region)

print('\nILA promedio por RURALIDAD:')
ila_por_rural = df.groupby('es_rural')['Y1_ILA'].agg(['mean', 'count', 'std']).round(4)
print(ila_por_rural)

# Análisis de tamaño de institución
print('\n=== ANÁLISIS POR TAMAÑO DE INSTITUCIÓN ===')
df['tamaño_categoria'] = pd.cut(df['total_alumnos'], 
                               bins=[0, 20, 50, 100, 500], 
                               labels=['Muy pequeña (1-20)', 'Pequeña (21-50)', 'Mediana (51-100)', 'Grande (101+)'])

ila_por_tamaño = df.groupby('tamaño_categoria')['Y1_ILA'].agg(['mean', 'count', 'std']).round(4)
print(ila_por_tamaño)

conn.close()