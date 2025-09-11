import sqlite3
import pandas as pd
import re

def normalize_col_name(col_name):
    # Remove special characters and spaces
    col_name = re.sub(r'[^a-zA-Z0-9_]', ' ', str(col_name))
    # Replace multiple spaces with a single underscore
    col_name = re.sub(r'\s+', '_', col_name).lower()
    return col_name

# Path to the source file
EXCEL_PATH = r'C:\Users\lucas\Proyectos\Reasis\assets\Consultoria\Información actualizada\3. BD Comp Digitales Docentes 2025.xlsx'
DB_PATH = 'reasis_database.db'

# Read the Excel file
df = pd.read_excel(EXCEL_PATH)

# Normalize column names
original_columns = df.columns.tolist()
df.columns = [normalize_col_name(col) for col in df.columns]
normalized_columns = df.columns.tolist()

# Print the mapping of original to normalized column names
print("Mapeo de nombres de columnas:")
for orig, norm in zip(original_columns, normalized_columns):
    print(f"'{orig}' -> '{norm}'")

# Create a connection to the database
conn = sqlite3.connect(DB_PATH)

# Define the new table name
new_table_name = 'docentes_competencias_contexto'

# Create the new table
df.to_sql(new_table_name, conn, if_exists='replace', index=False)

print(f"\nLa tabla '{new_table_name}' ha sido creada y poblada con {len(df)} registros.")

conn.close()
