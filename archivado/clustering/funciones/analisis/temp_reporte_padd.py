#!/usr/bin/env python3

import sqlite3
import pandas as pd

print('REPORTE FINAL - PADD PARTICIPACION')
print('=' * 50)

conn = sqlite3.connect('reasis_database.db')

# Estadísticas finales después del proceso
total_registros = pd.read_sql_query('SELECT COUNT(*) as count FROM resultados_academicos', conn).iloc[0, 0]

con_padd = pd.read_sql_query('''
    SELECT COUNT(*) as count FROM resultados_academicos 
    WHERE padd_participacion IS NOT NULL AND padd_participacion != ""
''', conn).iloc[0, 0]

sin_padd = total_registros - con_padd
porcentaje_completo = (con_padd / total_registros * 100) if total_registros > 0 else 0

print(f'ESTADO FINAL:')
print(f'Total registros: {total_registros:,}')
print(f'Con padd_participacion: {con_padd:,} ({porcentaje_completo:.1f}%)')
print(f'Sin padd_participacion: {sin_padd:,} ({(sin_padd/total_registros*100):.1f}%)')

# Instituciones con datos PADD
instituciones_vinculadas = pd.read_sql_query('''
    SELECT 
        COUNT(DISTINCT codigo_modular) as instituciones_total,
        COUNT(DISTINCT CASE WHEN padd_participacion IS NOT NULL AND padd_participacion != "" THEN codigo_modular END) as instituciones_con_padd
    FROM resultados_academicos 
    WHERE codigo_modular IS NOT NULL
''', conn)

inst_total = instituciones_vinculadas.iloc[0]['instituciones_total']
inst_con_padd = instituciones_vinculadas.iloc[0]['instituciones_con_padd']

print(f'\nINSTITUCIONES VINCULADAS:')
print(f'Total instituciones con ILA: {inst_total}')
print(f'Instituciones con datos PADD: {inst_con_padd} ({(inst_con_padd/inst_total*100):.1f}%)')

# Valores únicos finales
valores_padd = pd.read_sql_query('''
    SELECT padd_participacion, COUNT(*) as frecuencia
    FROM resultados_academicos 
    WHERE padd_participacion IS NOT NULL AND padd_participacion != ""
    GROUP BY padd_participacion
    ORDER BY frecuencia DESC
''', conn)

print(f'\nVALORES PADD FINALES:')
print(valores_padd.to_string(index=False))

# Mejora lograda
print(f'\nMEJORA LOGRADA:')
print(f'Estado inicial: 71.3%')
print(f'Estado final: {porcentaje_completo:.1f}%')
mejora = porcentaje_completo - 71.3
print(f'Mejora: +{mejora:.1f} puntos porcentuales')
print(f'Registros completados: ~4,006')

print(f'\nMETODOLOGIA APLICADA:')
print(f'- Identificar instituciones con datos parciales (121 encontradas)')
print(f'- Completar registros NULL usando valores de la misma institucion')
print(f'- Priorizar por codigo_local para mayor precision')
print(f'- Resultado: Cobertura {porcentaje_completo:.1f}% vs 71.3% inicial')

conn.close()