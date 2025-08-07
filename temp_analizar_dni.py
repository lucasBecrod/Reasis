#!/usr/bin/env python3

import pandas as pd
import sqlite3

# Read Excel data directly
df_2023 = pd.read_excel('assets/Consultoria/Información actualizada/2. PADD Consolidado.xlsx', sheet_name='2023')
df_2024 = pd.read_excel('assets/Consultoria/Información actualizada/2. PADD Consolidado.xlsx', sheet_name='2024')

# Process DNI the same way as our script
dni_2023 = pd.to_numeric(df_2023['Número de documento'], errors='coerce').fillna(0).astype(int).astype(str)
dni_2023 = dni_2023[dni_2023 != '0'].tolist()

dni_2024 = pd.to_numeric(df_2024['DNI'], errors='coerce').fillna(0).astype(int).astype(str)
dni_2024 = dni_2024[dni_2024 != '0'].tolist()

print('ANÁLISIS DETALLADO DNI PROCESADOS:')
print('=' * 50)
print(f'DNI válidos 2023: {len(dni_2023)}')
print(f'DNI válidos 2024: {len(dni_2024)}')

# Check for overlap
set_2023 = set(dni_2023)
set_2024 = set(dni_2024) 
overlap = set_2023.intersection(set_2024)

print(f'DNI en ambos años: {len(overlap)}')

if overlap:
    print('DNI duplicados encontrados:')
    for dni in list(overlap)[:10]:
        print(f'  {dni}')
        
# Check existing DB data
conn = sqlite3.connect('reasis_database.db')
existing_data = pd.read_sql_query('SELECT dni, año FROM docentes_data', conn)
print(f'\nDNI en BD existente: {len(existing_data)}')
if len(existing_data) > 0:
    print('Primeros 5 DNI en BD:')
    print(existing_data.head().to_string(index=False))
    
    # Check if any 2024 DNI conflicts with existing
    existing_dni = set(existing_data['dni'].tolist())
    conflicts = set(dni_2024).intersection(existing_dni)
    print(f'\nConflictos con BD existente: {len(conflicts)}')
    if conflicts:
        print('Primeros conflictos:')
        for dni in list(conflicts)[:10]:
            print(f'  DNI {dni} ya existe en BD')

conn.close()