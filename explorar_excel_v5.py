import pandas as pd
import numpy as np

def explorar_archivo_excel_v5():
    """
    Explora el archivo Excel v5 para identificar variables de clustering y riesgo-resiliencia
    """
    
    archivo_excel = r"archivado\clustering\02 Informe Entregado\Anexo A - Base de datos XLS v5.xlsx"
    
    try:
        # Obtener lista de hojas
        xl_file = pd.ExcelFile(archivo_excel)
        hojas = xl_file.sheet_names
        
        print("HOJAS ENCONTRADAS EN EXCEL v5:")
        print("="*50)
        for i, hoja in enumerate(hojas, 1):
            print(f"{i}. {hoja}")
        
        # Explorar cada hoja buscando variables de clustering
        variables_clustering = {}
        
        for hoja in hojas:
            print(f"\n--- HOJA: {hoja} ---")
            
            try:
                # Leer hoja
                df = pd.read_excel(archivo_excel, sheet_name=hoja)
                print(f"Filas: {len(df)}, Columnas: {len(df.columns)}")
                
                # Mostrar columnas
                print("Columnas:")
                for col in df.columns:
                    print(f"  - {col}")
                
                # Buscar columnas relacionadas con clustering o riesgo-resiliencia
                clustering_keywords = [
                    'cluster', 'grupo', 'tipologia', 'kmeans', 'k_means', 'k-means',
                    'riesgo', 'resiliencia', 'vulnerabilidad', 'capacidad',
                    'categoria', 'clasificacion', 'perfil', 'tipo',
                    'grupo_kmeans', 'cluster_', 'riesgo_', 'resiliencia_'
                ]
                
                cols_relevantes = []
                for col in df.columns:
                    col_lower = str(col).lower()
                    if any(keyword in col_lower for keyword in clustering_keywords):
                        cols_relevantes.append(col)
                
                if cols_relevantes:
                    print(f"COLUMNAS DE CLUSTERING/RIESGO ENCONTRADAS:")
                    for col in cols_relevantes:
                        print(f"  *** {col}")
                        
                        # Obtener valores únicos de estas columnas
                        if col in df.columns:
                            valores_unicos = df[col].dropna().unique()
                            if len(valores_unicos) <= 20:  # Solo mostrar si no son demasiados
                                print(f"      Valores únicos: {list(valores_unicos)}")
                            else:
                                print(f"      {len(valores_unicos)} valores únicos (muestra: {list(valores_unicos[:10])})")
                    
                    variables_clustering[hoja] = cols_relevantes
                
                # Mostrar muestra de datos (primeras 3 filas, primeras 10 columnas)
                print("Muestra de datos (primeras 3 filas):")
                muestra_cols = df.columns[:min(10, len(df.columns))]
                muestra = df[muestra_cols].head(3)
                for idx, row in muestra.iterrows():
                    print(f"  Fila {idx+1}: {dict(zip(muestra_cols, row.values))}")
                
                # Si hay muchas columnas, mostrar las últimas también
                if len(df.columns) > 10:
                    print("Últimas columnas:")
                    ultimas_cols = df.columns[-10:]
                    for col in ultimas_cols:
                        valores_sample = df[col].dropna().head(3).tolist()
                        print(f"  - {col}: {valores_sample}")
                
            except Exception as e:
                print(f"Error al leer hoja '{hoja}': {e}")
        
        # Resumen final
        print(f"\n" + "="*70)
        print("RESUMEN: VARIABLES DE CLUSTERING Y RIESGO-RESILIENCIA ENCONTRADAS")
        print("="*70)
        
        if variables_clustering:
            for hoja, variables in variables_clustering.items():
                print(f"\nHoja: {hoja}")
                for var in variables:
                    print(f"  - {var}")
        else:
            print("No se encontraron variables evidentes de clustering o riesgo-resiliencia")
            print("\nBuscar manualmente en las hojas:")
            for hoja in hojas:
                print(f"  - {hoja}")
        
        return variables_clustering
        
    except Exception as e:
        print(f"Error al leer archivo Excel: {e}")
        return None

if __name__ == "__main__":
    vars_encontradas = explorar_archivo_excel_v5()
    
    if vars_encontradas:
        print(f"\n" + "="*50)
        print("SIGUIENTE PASO:")
        print("="*50)
        print("Identificar exactamente cuáles variables agregar a 'indices_metodologicos':")
        for hoja, variables in vars_encontradas.items():
            print(f"\nDe la hoja '{hoja}':")
            for var in variables:
                print(f"  - {var} (revisar si contiene grupos K-means y/o riesgo-resiliencia)")
    else:
        print("\nNecesario revisar manualmente los archivos para encontrar:")
        print("- Columnas con grupos de clustering (ej: 'Grupo_1', 'Cluster_A', etc.)")
        print("- Columnas con etiquetas de riesgo-resiliencia")
        print("- Columnas con probabilidades de pertenencia a grupos")