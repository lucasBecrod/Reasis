import pandas as pd
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import numpy as np

def crear_mapa_peru_coordenadas():
    # Leer el archivo CSV
    archivo_csv = r"archivado\clustering\01 Analisis Excel\reasis_database_v5_final.csv"
    
    # Leer el archivo con separador de punto y coma
    df = pd.read_csv(archivo_csv, sep=';', encoding='utf-8')
    
    print(f"Total de registros: {len(df)}")
    print(f"Columnas disponibles: {list(df.columns)}")
    
    # Verificar coordenadas
    latitudes = pd.to_numeric(df['LATITUD'], errors='coerce')
    longitudes = pd.to_numeric(df['LONGITUD'], errors='coerce')
    
    # Filtrar coordenadas válidas y dentro del rango de Perú
    mask_validas = (~latitudes.isna()) & (~longitudes.isna())
    mask_peru = (latitudes >= -18.5) & (latitudes <= 0) & (longitudes >= -82) & (longitudes <= -68)
    
    df_validas = df[mask_validas & mask_peru].copy()
    
    print(f"Registros con coordenadas válidas: {len(df_validas)}")
    
    if len(df_validas) == 0:
        print("No se encontraron coordenadas válidas")
        return
    
    # Crear el mapa
    fig = plt.figure(figsize=(12, 10))
    ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())
    
    # Límites geográficos de Perú (aproximados)
    ax.set_extent([-82, -68, -18.5, 0], crs=ccrs.PlateCarree())
    
    # Agregar características geográficas
    ax.add_feature(cfeature.COASTLINE, linewidth=0.8)
    ax.add_feature(cfeature.BORDERS, linewidth=0.8)
    ax.add_feature(cfeature.RIVERS, alpha=0.3)
    ax.add_feature(cfeature.LAKES, alpha=0.3)
    ax.add_feature(cfeature.LAND, color='lightgray', alpha=0.3)
    ax.add_feature(cfeature.OCEAN, color='lightblue', alpha=0.3)
    
    # Agregar líneas de grilla
    ax.gridlines(draw_labels=True, alpha=0.3)
    
    # Graficar los puntos de las instituciones educativas
    lats = pd.to_numeric(df_validas['LATITUD'])
    lons = pd.to_numeric(df_validas['LONGITUD'])
    
    # Colorear por red/región si disponible
    if 'NUMERO_FYA' in df_validas.columns:
        # Obtener números de red únicos
        redes = df_validas['NUMERO_FYA'].unique()
        colores = plt.cm.tab10(np.linspace(0, 1, len(redes)))
        
        for i, red in enumerate(redes):
            mask_red = df_validas['NUMERO_FYA'] == red
            if mask_red.sum() > 0:
                ax.scatter(lons[mask_red], lats[mask_red], 
                          c=[colores[i]], s=50, alpha=0.7, 
                          transform=ccrs.PlateCarree(),
                          label=f'Red {red}')
        
        # Agregar leyenda
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    else:
        # Si no hay información de red, usar color único
        ax.scatter(lons, lats, c='red', s=50, alpha=0.7, 
                  transform=ccrs.PlateCarree())
    
    plt.title('Mapa del Perú - Instituciones Educativas Fe y Alegría\nUbicación por Coordenadas Geográficas', 
              fontsize=14, pad=20)
    
    # Ajustar diseño
    plt.tight_layout()
    
    # Mostrar estadísticas
    print("\n=== ESTADÍSTICAS GEOGRÁFICAS ===")
    print(f"Latitud mínima: {lats.min():.4f}")
    print(f"Latitud máxima: {lats.max():.4f}")
    print(f"Longitud mínima: {lons.min():.4f}")
    print(f"Longitud máxima: {lons.max():.4f}")
    
    if 'NUMERO_FYA' in df_validas.columns:
        print("\n=== DISTRIBUCIÓN POR RED ===")
        distribucion = df_validas['NUMERO_FYA'].value_counts().sort_index()
        for red, cantidad in distribucion.items():
            print(f"Red {red}: {cantidad} instituciones")
    
    # Guardar el mapa
    plt.savefig('mapa_peru_fe_y_alegria.png', dpi=300, bbox_inches='tight')
    print(f"\nMapa guardado como: mapa_peru_fe_y_alegria.png")
    
    # Mostrar el mapa
    plt.show()
    
    return df_validas

if __name__ == "__main__":
    try:
        datos_mapeados = crear_mapa_peru_coordenadas()
        print("\n¡Mapa generado exitosamente!")
    except Exception as e:
        print(f"Error al generar el mapa: {str(e)}")
        print("\nPosibles soluciones:")
        print("1. Instalar librerías: pip install cartopy matplotlib pandas")
        print("2. Verificar que el archivo CSV exista en la ruta especificada")