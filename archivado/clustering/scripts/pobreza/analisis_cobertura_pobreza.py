import pandas as pd

# Leer el reporte de vinculación
reporte = pd.read_csv('temp_data/reporte_vinculacion_pobreza_20250810.csv')

# Resumen de métodos aplicados
metodos = reporte['metodo_vinculacion'].value_counts(dropna=False)
print('Resumen de métodos de vinculación aplicados:')
print(metodos)

# Cobertura de pobreza monetaria asignada
asignados = reporte['pobreza_monetaria_distrito'].notnull().sum()
total = len(reporte)
print(f'Instituciones con pobreza monetaria asignada: {asignados} de {total} ({asignados/total:.1%})')

# Ejemplo de instituciones sin vinculación
sin_vinculo = reporte[reporte['metodo_vinculacion'] == 'sin_vinculo']
print('\nEjemplo de instituciones sin vinculación:')
print(sin_vinculo[['codigo_modular', 'region', 'provincia', 'distrito']].head())
