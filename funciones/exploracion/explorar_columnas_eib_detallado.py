#!/usr/bin/env python3
"""
Explorador detallado de columnas EIB para aplicar técnica múltiples códigos
Proyecto Reasis - Identificar columnas exactas disponibles
"""

import pandas as pd

def main():
    print("=== EXPLORADOR DETALLADO COLUMNAS EIB ===")
    
    archivo_eib = r"C:\Users\lucas\Proyectos\Reasis\assets\Consultoria\Información de referencia\RegistroNacional EIB Minedu\RIIEE EIB 2024 Minedu.xlsx"
    
    try:
        # Cargar con header=1 para códigos cortos
        df_eib = pd.read_excel(archivo_eib, header=1, nrows=3)
        
        print(f"Total columnas: {len(df_eib.columns)}")
        
        # Buscar patrones específicos para variables
        patrones = {
            'quintil': ['quintil', 'pobreza'],
            'ruralidad': ['rural', 'tipo'],
            'agua': ['agua', 'water'],
            'electricidad': ['electric', 'energia'],
            'internet': ['internet', 'conectiv'],
            'eib': ['eib', 'forma', 'atencion']
        }
        
        print("\nCOLUMNAS POR CATEGORIA:")
        
        for categoria, terminos in patrones.items():
            print(f"\n{categoria.upper()}:")
            encontradas = []
            for col in df_eib.columns:
                col_str = str(col).lower()
                if any(termino in col_str for termino in terminos):
                    encontradas.append(col)
            
            if encontradas:
                for col in encontradas[:5]:  # Mostrar máximo 5
                    print(f"  - {col}")
            else:
                print("  - No encontradas")
        
        print("\nCOLUMNAS CONFIRMADAS DISPONIBLES:")
        columnas_confirmadas = []
        
        for col in df_eib.columns:
            col_str = str(col).lower()
            if any(term in col_str for term in ['cod_mod', 'codinst', 'codlocal', 'quintil_pobreza', 'fa_2024b']):
                columnas_confirmadas.append(col)
                print(f"  [OK] {col}")
        
        print(f"\nTotal columnas confirmadas: {len(columnas_confirmadas)}")
        
        # Mostrar muestra de datos de columnas confirmadas
        print("\nMUESTRA DE DATOS:")
        if len(columnas_confirmadas) > 0:
            df_muestra = df_eib[columnas_confirmadas]
            print(df_muestra.to_string())
        
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    main()