import pandas as pd
import json

def debug_excel_match():
    '''Debugs why cod_mod values are not matching in Excel.'''
    excel_path = r"C:\Users\lucas\Proyectos\Reasis\assets\Consultoria\Información actualizada\1. Ruralidad, EIB y TOE.xlsx"
    sheet_name = 'DatosGlobales'
    json_path = 'lib/iiee_faltantes.json'

    print(f"Leyendo datos desde: {excel_path} | Hoja: {sheet_name}")
    df_excel = pd.read_excel(excel_path, sheet_name=sheet_name)

    # Convert and pad cod_mod from Excel
    df_excel['cod_mod'] = df_excel['cod_mod'].astype(str).str.zfill(7)

    print("\n--- Muestra de 'cod_mod' en Excel (DatosGlobales) después de padding ---")
    print(df_excel['cod_mod'].head())
    print("Tipo de dato de 'cod_mod' en Excel después de padding:", df_excel['cod_mod'].dtype)

    with open(json_path, 'r', encoding='utf-8') as f:
        iiee_faltantes = json.load(f)
    codigos_a_actualizar = [ie['COD_MOD'] for ie in iiee_faltantes]

    print("\n--- Códigos Modulares de IIEE faltantes (desde JSON) ---")
    print(codigos_a_actualizar)

if __name__ == "__main__":
    debug_excel_match()