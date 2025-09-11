import pandas as pd
import matplotlib.pyplot as plt
import requests
import zipfile
import os
import json

def descargar_shapefile_peru():
    """
    Descarga los shapefiles oficiales del Perú desde fuentes gubernamentales
    """
    urls_shapefile = [
        # INEI - Límites políticos del Perú
        "https://raw.githubusercontent.com/juaneladio/peru-geojson/master/peru_departamental_simple.geojson",
        # Alternativa: Datos del gobierno peruano
        "https://raw.githubusercontent.com/DataScienceResearchPeru/covid-19_latinoamerica/master/latam_shapefile/PER_adm1.json"
    ]
    
    for i, url in enumerate(urls_shapefile):
        try:
            print(f"Intentando descargar desde fuente {i+1}...")
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                # Guardar el archivo GeoJSON
                filename = f"peru_regiones_{i+1}.geojson"
                with open(filename, 'w', encoding='utf-8') as f:
                    if url.endswith('.json'):
                        f.write(response.text)
                    else:
                        f.write(response.text)
                
                print(f"✓ Descargado exitosamente: {filename}")
                return filename, json.loads(response.text)
                
        except Exception as e:
            print(f"✗ Error con fuente {i+1}: {e}")
            continue
    
    return None, None

def crear_mapa_peru_profesional():
    """
    Crea un mapa profesional del Perú usando datos geográficos reales
    """
    
    # Cargar datos de instituciones
    try:
        df = pd.read_csv('instituciones_con_region.csv', encoding='utf-8')
    except:
        print("Error: Archivo 'instituciones_con_region.csv' no encontrado")
        print("Ejecuta primero: python identificar_regiones.py")
        return
    
    # Intentar descargar datos geográficos reales
    filename, geojson_data = descargar_shapefile_peru()
    
    if geojson_data is None:
        print("No se pudieron descargar los shapefiles.")
        print("Te recomiendo usar Kepler.gl online:")
        print("1. Ve a: https://kepler.gl/")
        print("2. Sube tu archivo: instituciones_con_region.csv")
        print("3. Configura las coordenadas LATITUD/LONGITUD")
        print("4. Agrega capa de mapa base de Perú")
        print("5. Exporta como PNG")
        return crear_csv_para_kepler(df)
    
    print("¡Datos geográficos descargados exitosamente!")
    
    # Procesar GeoJSON y crear mapa
    try:
        import geopandas as gpd
        print("Usando GeoPandas para procesamiento profesional...")
        return crear_mapa_con_geopandas(df, filename)
    except ImportError:
        print("GeoPandas no disponible. Instalando...")
        print("Ejecuta: pip install geopandas")
        return crear_csv_para_kepler(df)

def crear_csv_para_kepler(df):
    """
    Prepara archivo CSV optimizado para Kepler.gl
    """
    
    # Contar instituciones por región
    conteo_regiones = df['REGION'].value_counts()
    
    # Crear archivo optimizado para Kepler.gl
    df_kepler = df[['CODIGO_MODULAR', 'NOMBRE_INSTITUCION', 'NUMERO_FYA', 
                    'LATITUD', 'LONGITUD', 'ALTITUD_MSNM', 'REGION']].copy()
    
    # Agregar información adicional para visualización
    df_kepler['RED_NOMBRE'] = 'Red Fe y Alegría ' + df_kepler['NUMERO_FYA'].astype(str)
    df_kepler['TOOLTIP'] = (df_kepler['NOMBRE_INSTITUCION'] + 
                           ' (Red ' + df_kepler['NUMERO_FYA'].astype(str) + ')')
    
    # Guardar archivo para Kepler.gl
    archivo_kepler = 'iiee_para_kepler.csv'
    df_kepler.to_csv(archivo_kepler, index=False, encoding='utf-8')
    
    print(f"\n{'='*60}")
    print("📊 ARCHIVO PREPARADO PARA KEPLER.GL")
    print(f"{'='*60}")
    print(f"Archivo creado: {archivo_kepler}")
    print(f"Total instituciones: {len(df_kepler)}")
    
    print(f"\n📋 INSTRUCCIONES PARA KEPLER.GL:")
    print("1. Ve a: https://kepler.gl/")
    print(f"2. Sube el archivo: {archivo_kepler}")
    print("3. Configura coordenadas:")
    print("   - Latitud: LATITUD")
    print("   - Longitud: LONGITUD")
    print("4. Agrega capas adicionales:")
    print("   - Color por: NUMERO_FYA (redes)")
    print("   - Tamaño por: ALTITUD_MSNM")
    print("   - Filtro por: REGION")
    print("5. Configura mapa base: 'Peru' o 'Satellite'")
    print("6. Exporta como PNG de alta resolución")
    
    # Mostrar estadísticas
    print(f"\n📈 ESTADÍSTICAS POR REGIÓN:")
    for region, cantidad in conteo_regiones.items():
        porcentaje = (cantidad / len(df_kepler)) * 100
        print(f"   {region:15s}: {cantidad:2d} IIEE ({porcentaje:4.1f}%)")
    
    print(f"\n📈 ESTADÍSTICAS POR RED:")
    conteo_redes = df_kepler['NUMERO_FYA'].value_counts().sort_index()
    for red, cantidad in conteo_redes.items():
        porcentaje = (cantidad / len(df_kepler)) * 100
        print(f"   Red {red}: {cantidad:2d} IIEE ({porcentaje:4.1f}%)")
    
    return df_kepler

def crear_mapa_con_geopandas(df, shapefile):
    """
    Crea mapa usando GeoPandas (requiere instalación)
    """
    try:
        import geopandas as gpd
        from shapely.geometry import Point
        
        # Leer shapefile del Perú
        peru_regiones = gpd.read_file(shapefile)
        
        # Convertir instituciones a GeoDataFrame
        geometry = [Point(xy) for xy in zip(df['LONGITUD'], df['LATITUD'])]
        iiee_gdf = gpd.GeoDataFrame(df, geometry=geometry)
        
        # Crear el mapa
        fig, ax = plt.subplots(figsize=(12, 16))
        
        # Dibujar regiones del Perú
        peru_regiones.plot(ax=ax, color='lightgray', edgecolor='black', alpha=0.7)
        
        # Dibujar puntos de instituciones
        colores_redes = {44: 'red', 47: 'blue', 48: 'green', 54: 'purple', 72: 'orange', 79: 'brown'}
        
        for red in sorted(df['NUMERO_FYA'].unique()):
            mask = df['NUMERO_FYA'] == red
            iiee_red = iiee_gdf[mask]
            iiee_red.plot(ax=ax, color=colores_redes.get(red, 'gray'), 
                         markersize=50, alpha=0.8, label=f'Red {red}')
        
        ax.set_title('Mapa del Perú - Instituciones Educativas Fe y Alegría', 
                    fontsize=14, fontweight='bold')
        ax.legend()
        
        plt.savefig('mapa_peru_geopandas.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        print("¡Mapa creado con GeoPandas!")
        return iiee_gdf
        
    except ImportError:
        print("GeoPandas no disponible. Usa la opción de Kepler.gl")
        return crear_csv_para_kepler(df)

if __name__ == "__main__":
    crear_mapa_peru_profesional()