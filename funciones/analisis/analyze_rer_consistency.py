import sqlite3
import pandas as pd
import re

conn = sqlite3.connect('reasis_database.db')

query = """
SELECT
    ce.codigo_modular,
    ce.si_pertence_a_una_red_rural_indique_el_nombre_de_su_ie AS ce_nombre_rer,
    ce.modalidad AS ce_modalidad,
    ie.es_rural,
    ie.codigo_red,
    ie.codigo_rer,
    ie.modalidad_especifica
FROM
    conectividad_equipamiento ce
LEFT JOIN
    instituciones_educativas ie ON ce.codigo_modular = ie.codigo_modular
"""

df_joined = pd.read_sql_query(query, conn)

output_lines = []
output_lines.append(f"\n--- Análisis de Vinculación RER ---")
output_lines.append(f"Total de registros en conectividad_equipamiento: {len(df_joined)}")

# Registros con codigo_modular que no tienen match en instituciones_educativas
no_match_ie = df_joined[df_joined['es_rural'].isna()]
output_lines.append(f"Registros en conectividad_equipamiento sin match en instituciones_educativas: {len(no_match_ie)}")

# Filtrar solo los que sí tienen match para el análisis de consistencia
df_matched = df_joined.dropna(subset=['es_rural']).copy() # Usar .copy() para evitar SettingWithCopyWarning
output_lines.append(f"Registros con match en instituciones_educativas: {len(df_matched)}")

# Convertir ie.es_rural a string 'Sí'/'No' para consistencia
df_matched.loc[:, 'es_rural_str'] = df_matched['es_rural'].apply(lambda x: 'Sí' if x == 1.0 else 'No')

# Análisis de consistencia de modalidad/ruralidad
rer_in_ce = df_matched[df_matched['ce_modalidad'] == 'RER']
output_lines.append(f"\nRegistros donde ce.modalidad es 'RER': {len(rer_in_ce)}")

rer_consistent = rer_in_ce[rer_in_ce['es_rural_str'] == 'Sí']
output_lines.append(f"  - Consistentes (ie.es_rural es 'Sí'): {len(rer_consistent)}")

rer_inconsistent_rural = rer_in_ce[rer_in_ce['es_rural_str'] != 'Sí']
output_lines.append(f"  - Inconsistentes (ie.es_rural no es 'Sí'): {len(rer_inconsistent_rural)}")

# Función para extraer solo dígitos de una cadena
def extract_digits(text):
    if pd.isna(text): return ''
    return ''.join(filter(str.isdigit, str(text)))

# Normalizar las columnas extrayendo solo dígitos para una mejor comparación
df_matched.loc[:, 'ce_nombre_rer_digits'] = df_matched['ce_nombre_rer'].apply(extract_digits)
df_matched.loc[:, 'codigo_red_digits'] = df_matched['codigo_red'].apply(extract_digits)
df_matched.loc[:, 'codigo_rer_digits'] = df_matched['codigo_rer'].apply(extract_digits)

# Análisis de consistencia de nombre RER / código RER (comparando dígitos)
rer_name_consistent = df_matched[
    (df_matched['ce_nombre_rer_digits'] != '') & (
        df_matched.apply(lambda row: row['ce_nombre_rer_digits'] in row['codigo_red_digits'] if row['codigo_red_digits'] else False, axis=1) |
        df_matched.apply(lambda row: row['ce_nombre_rer_digits'] in row['codigo_rer_digits'] if row['codigo_rer_digits'] else False, axis=1)
    )
]
output_lines.append(f"\nRegistros donde ce_nombre_rer (dígitos) coincide con ie.codigo_red o ie.codigo_rer (dígitos): {len(rer_name_consistent)}")

rer_name_inconsistent = df_matched[
    (df_matched['ce_nombre_rer_digits'] != '') & 
    ~((df_matched.apply(lambda row: row['ce_nombre_rer_digits'] in row['codigo_red_digits'] if row['codigo_red_digits'] else False, axis=1) |
       df_matched.apply(lambda row: row['ce_nombre_rer_digits'] in row['codigo_rer_digits'] if row['codigo_rer_digits'] else False, axis=1)))
]
output_lines.append(f"Registros donde ce_nombre_rer (dígitos) NO coincide con ie.codigo_red o ie.codigo_rer (dígitos): {len(rer_name_inconsistent)}")

# Mostrar ejemplos de inconsistencias si existen
if not rer_inconsistent_rural.empty:
    output_lines.append("\nEjemplos de inconsistencias (ce.modalidad='RER' pero ie.es_rural != 'Sí'):")
    output_lines.append(rer_inconsistent_rural[['codigo_modular', 'ce_modalidad', 'es_rural_str']].head().to_string())

if not rer_name_inconsistent.empty:
    output_lines.append("\nEjemplos de inconsistencias (ce_nombre_rer NO coincide con ie.codigo_red/rer):")
    output_lines.append(rer_name_inconsistent[['codigo_modular', 'ce_nombre_rer', 'codigo_red', 'codigo_rer', 'ce_nombre_rer_digits', 'codigo_red_digits', 'codigo_rer_digits']].head().to_string())

conn.close()

with open('analysis_output.txt', 'w', encoding='utf-8') as f:
    for line in output_lines:
        f.write(line + '\n')