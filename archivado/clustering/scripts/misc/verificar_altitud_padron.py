#!/usr/bin/env python3
"""
Script para verificar qué datos de altitud están disponibles en el padrón MINEDU
"""

from dbfread import DBF
import pandas as pd

def verificar_altitud_padron():
    """Verifica disponibilidad de datos de altitud en el padrón MINEDU"""
    
    print("=== VERIFICANDO ALTITUD EN PADRON MINEDU ===")
    
    # Lista de códigos a verificar
    codigos = ['0600692', '1768829', '0481093', '0488403', '0304642', '0428714', '3025715', '2533906', '1781897']
    
    try:
        # Leer archivo DBF
        table = DBF('data/bases_de_datos/Padron_web_20250731/Padron_web.dbf', encoding='latin-1')
        records = []
        for record in table:
            records.append(dict(record))
        
        df = pd.DataFrame(records)
        df['COD_MOD'] = df['COD_MOD'].astype(str)
        
        print(f"Padrón cargado: {len(df)} registros, {len(df.columns)} columnas")
        
        # Buscar columnas relacionadas con altitud y geografía
        columnas_geograficas = []
        for col in df.columns:
            col_upper = col.upper()
            if any(keyword in col_upper for keyword in ['ALT', 'ELEV', 'HEIGHT', 'LAT', 'LON', 'COORD', 'X_', 'Y_', 'GEO', 'UTM']):
                columnas_geograficas.append(col)
        
        print(f"\nColumnas geográficas encontradas: {len(columnas_geograficas)}")
        for col in columnas_geograficas:
            print(f"  {col}")
        
        # Buscar nuestros códigos
        df_encontrado = df[df['COD_MOD'].isin(codigos)]
        
        if len(df_encontrado) == 0:
            print("\nNo se encontraron códigos coincidentes")
            return
        
        print(f"\nEncontrados {len(df_encontrado)} registros")
        
        # Analizar cada institución
        for _, row in df_encontrado.iterrows():
            codigo = row['COD_MOD']
            nombre = str(row.get('CEN_EDU', 'Sin nombre')).strip()
            
            print(f"\n--- {codigo} - {nombre} ---")
            
            # Mostrar datos geográficos disponibles
            datos_geo = {}
            for col in columnas_geograficas:
                valor = row.get(col)
                if valor is not None and str(valor).strip() != '' and valor != 0:
                    datos_geo[col] = valor
            
            if datos_geo:
                print("  Datos geográficos disponibles:")
                for col, valor in datos_geo.items():
                    print(f"    {col:15}: {valor} ({type(valor).__name__})")
            else:
                print("  Sin datos geográficos específicos")
                
                # Buscar campos numéricos que podrían ser coordenadas o altitud
                print("  Campos numéricos relevantes:")
                for col, valor in row.items():
                    if isinstance(valor, (int, float)) and valor != 0:
                        # Posibles rangos para coordenadas o altitud
                        if (-90 <= valor <= 90) or (-180 <= valor <= 180) or (valor > 500):
                            print(f"    {col:15}: {valor} (posible geo)")
        
        # Verificar si hay datos de altitud en general en el padrón
        print(f"\n=== ANÁLISIS GENERAL DE ALTITUD ===")
        for col in columnas_geograficas:
            if 'ALT' in col.upper():
                no_nulos = df[col].notna().sum()
                no_ceros = (df[col] != 0).sum()
                print(f"{col}: {no_nulos} no nulos, {no_ceros} no ceros de {len(df)} total")
                
                if no_ceros > 0:
                    valores_ejemplo = df[df[col] != 0][col].head(5).tolist()
                    print(f"  Ejemplos: {valores_ejemplo}")
        
        return df_encontrado
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return None

def verificar_otras_fuentes_altitud():
    """Verifica si hay otras fuentes de datos de altitud"""
    
    print(f"\n=== VERIFICANDO OTRAS FUENTES DE ALTITUD ===")
    
    # Buscar en archivo de datos locales adicionales si existe
    try:
        table_local = DBF('data/bases_de_datos/Padron_web_20250731/Padlocaladi_web.dbf', encoding='latin-1')
        records_local = []
        for record in table_local:
            records_local.append(dict(record))
        
        df_local = pd.DataFrame(records_local)
        print(f"Archivo datos locales: {len(df_local)} registros, {len(df_local.columns)} columnas")
        
        # Buscar columnas de altitud
        columnas_alt_local = [col for col in df_local.columns if 'ALT' in col.upper()]
        if columnas_alt_local:
            print(f"Columnas de altitud en datos locales: {columnas_alt_local}")
            for col in columnas_alt_local:
                no_nulos = df_local[col].notna().sum()
                print(f"  {col}: {no_nulos} valores no nulos")
        else:
            print("No se encontraron columnas de altitud en datos locales")
            
    except Exception as e:
        print(f"No se pudo cargar datos locales adicionales: {e}")

if __name__ == "__main__":
    df_encontrado = verificar_altitud_padron()
    verificar_otras_fuentes_altitud()