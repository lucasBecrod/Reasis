import sqlite3
import pandas as pd

conn = sqlite3.connect('reasis_database.db')

print('=== ANÁLISIS DE VARIABLES CON MAYOR CERTEZA ===')

# 1. X1_NVC - Vulnerabilidad Contextual
print('\n1. X1_NVC - VULNERABILIDAD CONTEXTUAL')
print('   Fuente: datos_eib_minedu')

query_x1 = '''
SELECT 
    COUNT(DISTINCT im.codigo_modular) as total_instituciones,
    COUNT(DISTINCT CASE WHEN eib.quintil_pobreza IS NOT NULL THEN im.codigo_modular END) as con_datos_pobreza,
    ROUND((COUNT(DISTINCT CASE WHEN eib.quintil_pobreza IS NOT NULL THEN im.codigo_modular END) * 100.0 / COUNT(DISTINCT im.codigo_modular)), 1) as porcentaje_cobertura
FROM indices_metodologicos im
LEFT JOIN datos_eib_minedu eib ON im.codigo_modular = eib.codigo_modular
'''

df_x1 = pd.read_sql_query(query_x1, conn)
print(f'   Cobertura: {df_x1.iloc[0,1]}/{df_x1.iloc[0,0]} instituciones ({df_x1.iloc[0,2]}%)')

# 2. Y2_TD - Tendencia Desempeño
print('\n2. Y2_TD - TENDENCIA DESEMPEÑO')
print('   Fuente: matriculas_siagie')

query_y2 = '''
SELECT 
    COUNT(DISTINCT codigo_modular) as instituciones_con_datos,
    COUNT(DISTINCT anio) as años_disponibles,
    MIN(anio) as año_inicial,
    MAX(anio) as año_final
FROM matriculas_siagie
WHERE codigo_modular IS NOT NULL AND anio IS NOT NULL
'''

df_y2 = pd.read_sql_query(query_y2, conn)
print(f'   Datos: {df_y2.iloc[0,0]} instituciones con datos de {df_y2.iloc[0,2]} a {df_y2.iloc[0,3]} ({df_y2.iloc[0,1]} años)')

# 3. X4_IDD - Desempeño Docente
print('\n3. X4_IDD - DESEMPEÑO DOCENTE')
print('   Fuente: docentes_data')

query_x4 = '''
SELECT 
    COUNT(*) as total_registros,
    COUNT(DISTINCT codigo_modular) as instituciones_diferentes,
    COUNT(CASE WHEN promedio_final IS NOT NULL AND promedio_final != 'NULL' AND promedio_final != '' THEN 1 END) as con_promedio
FROM docentes_data
WHERE codigo_modular IS NOT NULL
'''

df_x4 = pd.read_sql_query(query_x4, conn)
print(f'   Datos: {df_x4.iloc[0,1]} instituciones con {df_x4.iloc[0,2]} registros con promedio')

print('\n=== RECOMENDACIÓN DE IMPLEMENTACIÓN ===')

# Calcular scores de viabilidad
cobertura_x1 = df_x1.iloc[0,2]
cobertura_y2 = (df_y2.iloc[0,0] / 184) * 100  # Asumiendo 184 total
cobertura_x4 = (df_x4.iloc[0,1] / 184) * 100

print(f'1. X1_NVC: {cobertura_x1}% cobertura - MEDIA certeza (datos parciales)')
print(f'2. Y2_TD: {cobertura_y2:.1f}% cobertura - ALTA certeza (datos completos multi-año)')
print(f'3. X4_IDD: {cobertura_x4:.1f}% cobertura - MEDIA certeza (datos de evaluación)')

# Determinar mejor opción
if cobertura_y2 > cobertura_x1 and cobertura_y2 > cobertura_x4:
    mejor = "Y2_TD (Tendencia Desempeño)"
elif cobertura_x1 > cobertura_x4:
    mejor = "X1_NVC (Vulnerabilidad Contextual)"
else:
    mejor = "X4_IDD (Desempeño Docente)"

print(f'\nRECOMENDACIÓN: Implementar primero {mejor}')

conn.close()