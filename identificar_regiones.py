import pandas as pd
import numpy as np

def identificar_regiones_por_coordenadas():
    """
    Identifica las regiones del Perú basándose en las coordenadas geográficas
    """
    
    # Leer el archivo CSV
    archivo_csv = r"archivado\clustering\01 Analisis Excel\reasis_database_v5_final.csv"
    
    try:
        df = pd.read_csv(archivo_csv, sep=';', encoding='utf-8')
    except UnicodeDecodeError:
        try:
            df = pd.read_csv(archivo_csv, sep=';', encoding='latin-1')
        except UnicodeDecodeError:
            df = pd.read_csv(archivo_csv, sep=';', encoding='cp1252')
    
    # Filtrar coordenadas válidas
    latitudes = pd.to_numeric(df['LATITUD'], errors='coerce')
    longitudes = pd.to_numeric(df['LONGITUD'], errors='coerce')
    
    mask_validas = (~latitudes.isna()) & (~longitudes.isna())
    df_validas = df[mask_validas].copy()
    
    # Definir límites aproximados de regiones peruanas basados en coordenadas
    def asignar_region(lat, lon):
        lat, lon = float(lat), float(lon)
        
        # Región Amazonas
        if -6.5 < lat < -2.8 and -78.8 < lon < -75.8:
            return "Amazonas"
        
        # Región Áncash
        elif -10.8 < lat < -7.8 and -78.7 < lon < -76.8:
            return "Áncash"
        
        # Región Apurímac
        elif -14.8 < lat < -12.8 and -73.8 < lon < -71.8:
            return "Apurímac"
        
        # Región Arequipa
        elif -16.7 < lat < -14.3 and -74.5 < lon < -70.8:
            return "Arequipa"
        
        # Región Ayacucho
        elif -15.8 < lat < -12.0 and -75.2 < lon < -72.8:
            return "Ayacucho"
        
        # Región Cajamarca
        elif -7.6 < lat < -4.8 and -79.8 < lon < -77.8:
            return "Cajamarca"
        
        # Región Callao
        elif -12.2 < lat < -11.8 and -77.2 < lon < -76.9:
            return "Callao"
        
        # Región Cusco
        elif -14.8 < lat < -11.0 and -73.8 < lon < -70.8:
            return "Cusco"
        
        # Región Huancavelica
        elif -13.8 < lat < -11.8 and -75.8 < lon < -73.8:
            return "Huancavelica"
        
        # Región Huánuco
        elif -10.8 < lat < -8.8 and -77.8 < lon < -75.8:
            return "Huánuco"
        
        # Región Ica
        elif -15.8 < lat < -13.0 and -76.5 < lon < -74.8:
            return "Ica"
        
        # Región Junín
        elif -12.8 < lat < -10.0 and -76.8 < lon < -73.8:
            return "Junín"
        
        # Región La Libertad
        elif -8.8 < lat < -6.8 and -79.8 < lon < -77.8:
            return "La Libertad"
        
        # Región Lambayeque
        elif -7.0 < lat < -5.8 and -80.8 < lon < -78.8:
            return "Lambayeque"
        
        # Región Lima
        elif -13.0 < lat < -10.8 and -77.8 < lon < -75.8:
            return "Lima"
        
        # Región Loreto
        elif -5.8 < lat < -1.8 and -76.8 < lon < -73.8:
            return "Loreto"
        
        # Región Madre de Dios
        elif -13.8 < lat < -9.8 and -72.8 < lon < -68.8:
            return "Madre de Dios"
        
        # Región Moquegua
        elif -17.8 < lat < -15.8 and -71.8 < lon < -69.8:
            return "Moquegua"
        
        # Región Pasco
        elif -11.8 < lat < -9.8 and -76.8 < lon < -74.8:
            return "Pasco"
        
        # Región Piura
        elif -6.0 < lat < -4.0 and -81.8 < lon < -79.8:
            return "Piura"
        
        # Región Puno
        elif -17.8 < lat < -13.8 and -71.8 < lon < -68.8:
            return "Puno"
        
        # Región San Martín
        elif -8.8 < lat < -5.8 and -77.8 < lon < -75.8:
            return "San Martín"
        
        # Región Tacna
        elif -18.8 < lat < -16.8 and -71.8 < lon < -69.8:
            return "Tacna"
        
        # Región Tumbes
        elif -4.0 < lat < -3.0 and -81.8 < lon < -79.8:
            return "Tumbes"
        
        # Región Ucayali
        elif -11.8 < lat < -7.8 and -75.8 < lon < -72.8:
            return "Ucayali"
        
        # Si no coincide con ninguna región específica, intentar clasificación más amplia
        else:
            # Costa Norte
            if lat > -8 and lon < -79:
                return "Costa Norte"
            # Costa Centro
            elif -13 < lat <= -8 and lon < -76:
                return "Costa Centro"
            # Costa Sur
            elif lat <= -13 and lon < -74:
                return "Costa Sur"
            # Sierra Norte
            elif lat > -8 and -78 < lon <= -76:
                return "Sierra Norte"
            # Sierra Centro
            elif -13 < lat <= -8 and -77 < lon <= -74:
                return "Sierra Centro"
            # Sierra Sur
            elif lat <= -13 and -75 < lon <= -70:
                return "Sierra Sur"
            # Selva
            elif lon > -76:
                return "Selva"
            else:
                return "No identificado"
    
    # Asignar región a cada institución
    df_validas['REGION'] = df_validas.apply(
        lambda row: asignar_region(row['LATITUD'], row['LONGITUD']), axis=1
    )
    
    # Contar instituciones por región
    conteo_regiones = df_validas['REGION'].value_counts()
    
    print("=== IDENTIFICACIÓN DE REGIONES ===")
    print(f"Total de instituciones procesadas: {len(df_validas)}")
    print("\n=== DISTRIBUCIÓN POR REGIÓN ===")
    for region, cantidad in conteo_regiones.items():
        print(f"{region}: {cantidad} instituciones")
    
    # Mostrar algunas instituciones por región para verificación
    print("\n=== MUESTRA POR REGIÓN (para verificación) ===")
    for region in conteo_regiones.head(10).index:
        muestra = df_validas[df_validas['REGION'] == region].head(2)
        print(f"\n{region}:")
        for idx, row in muestra.iterrows():
            print(f"  - {row['NOMBRE_INSTITUCION']} (Lat: {row['LATITUD']}, Lon: {row['LONGITUD']})")
    
    # Guardar datos con región identificada
    archivo_salida = 'instituciones_con_region.csv'
    df_validas.to_csv(archivo_salida, index=False, encoding='utf-8')
    print(f"\nDatos guardados en: {archivo_salida}")
    
    return df_validas, conteo_regiones

if __name__ == "__main__":
    datos_con_region, conteos = identificar_regiones_por_coordenadas()