import pandas as pd

# Ruta del archivo Excel
excel_path = r'C:\Users\lucas\Proyectos\Reasis\data\bases_de_datos\pobreza_monetaria\Pobreza monetaria por distrito.xlsx'

# Leer los nombres de las hojas
xls = pd.ExcelFile(excel_path)
print(f"Hojas disponibles: {xls.sheet_names}")

# Extraer encabezados y primeras 10 filas de Anexo1 y Anexo2
for hoja in ['Anexo1', 'Anexo2']:
    print(f"\n--- {hoja} ---")
    df = pd.read_excel(excel_path, sheet_name=hoja)
    print("Encabezados:", list(df.columns))
    print(df.head(10))
