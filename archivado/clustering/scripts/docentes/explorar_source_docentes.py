import pandas as pd
import glob

EXCEL_PATH = r'C:\Users\lucas\Proyectos\Reasis\assets\Consultoria\Información actualizada\3. BD Comp Digitales Docentes 2025.xlsx'

try:
    df = pd.read_excel(EXCEL_PATH)
    print("Columns in the source file:")
    print(df.columns.tolist())
except FileNotFoundError:
    print(f"File not found at the expected path. Searching for the file...")
    files = glob.glob('C:/Users/lucas/Proyectos/Reasis/**/3. BD Comp Digitales Docentes 2025.xlsx', recursive=True)
    if files:
        file_path = files[0]
        print(f"File found at: {file_path}")
        df = pd.read_excel(file_path)
        print("Columns in the source file:")
        print(df.columns.tolist())
    else:
        print("Could not find the file in the project directory.")
