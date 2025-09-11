import pandas as pd

def explore_excel():
    '''Explora las hojas y columnas de un archivo Excel.'''
    excel_path = r"C:\Users\lucas\Proyectos\Reasis\assets\Consultoria\Información actualizada\1. Ruralidad, EIB y TOE.xlsx"
    print(f"Explorando el archivo: {excel_path}")

    try:
        xls = pd.ExcelFile(excel_path)
        print("\n--- Hojas en el archivo ---")
        sheets = xls.sheet_names
        print(sheets)

        for sheet_name in sheets:
            print(f"\n--- Columnas en la hoja: '{sheet_name}' ---")
            df = pd.read_excel(xls, sheet_name=sheet_name)
            print(df.columns.tolist())

    except Exception as e:
        print(f"Ocurrió un error: {e}")

if __name__ == "__main__":
    explore_excel()
