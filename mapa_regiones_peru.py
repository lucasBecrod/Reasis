import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Polygon
import matplotlib.patches as mpatches
from matplotlib.colors import ListedColormap
import matplotlib.cm as cm

def crear_mapa_regiones_peru():
    """
    Crea un mapa del Perú con regiones delimitadas, coloreadas según cantidad de IIEE
    e incluye los puntos de cada institución educativa
    """
    
    # Cargar datos con regiones identificadas
    try:
        df = pd.read_csv('instituciones_con_region.csv', encoding='utf-8')
    except:
        print("Error: Primero ejecuta identificar_regiones.py")
        return
    
    print(f"Cargados {len(df)} registros con regiones identificadas")
    
    # Contar instituciones por región
    conteo_regiones = df['REGION'].value_counts()
    print("\nDistribución por región:")
    for region, cantidad in conteo_regiones.items():
        print(f"  {region}: {cantidad} instituciones")
    
    # Crear figura grande
    fig, ax = plt.subplots(figsize=(15, 18))
    
    # Límites geográficos del Perú
    ax.set_xlim(-82, -68)
    ax.set_ylim(-18.5, 0)
    
    # Definir límites aproximados de cada región para el mapa
    regiones_limites = {
        'Piura': [(-6.0, -4.0, -81.8, -79.8), 'Piura'],
        'Tumbes': [(-4.0, -3.0, -81.8, -79.8), 'Tumbes'],
        'Lambayeque': [(-7.0, -5.8, -80.8, -78.8), 'Lambayeque'],
        'La Libertad': [(-8.8, -6.8, -79.8, -77.8), 'La Libertad'],
        'Cajamarca': [(-7.6, -4.8, -79.8, -77.8), 'Cajamarca'],
        'Amazonas': [(-6.5, -2.8, -78.8, -75.8), 'Amazonas'],
        'Loreto': [(-5.8, -1.8, -76.8, -73.8), 'Loreto'],
        'San Martín': [(-8.8, -5.8, -77.8, -75.8), 'San Martín'],
        'Ucayali': [(-11.8, -7.8, -75.8, -72.8), 'Ucayali'],
        'Áncash': [(-10.8, -7.8, -78.7, -76.8), 'Áncash'],
        'Lima': [(-13.0, -10.8, -77.8, -75.8), 'Lima'],
        'Callao': [(-12.2, -11.8, -77.2, -76.9), 'Callao'],
        'Ica': [(-15.8, -13.0, -76.5, -74.8), 'Ica'],
        'Huánuco': [(-10.8, -8.8, -77.8, -75.8), 'Huánuco'],
        'Pasco': [(-11.8, -9.8, -76.8, -74.8), 'Pasco'],
        'Junín': [(-12.8, -10.0, -76.8, -73.8), 'Junín'],
        'Huancavelica': [(-13.8, -11.8, -75.8, -73.8), 'Huancavelica'],
        'Ayacucho': [(-15.8, -12.0, -75.2, -72.8), 'Ayacucho'],
        'Apurímac': [(-14.8, -12.8, -73.8, -71.8), 'Apurímac'],
        'Cusco': [(-14.8, -11.0, -73.8, -70.8), 'Cusco'],
        'Madre de Dios': [(-13.8, -9.8, -72.8, -68.8), 'Madre de Dios'],
        'Arequipa': [(-16.7, -14.3, -74.5, -70.8), 'Arequipa'],
        'Moquegua': [(-17.8, -15.8, -71.8, -69.8), 'Moquegua'],
        'Tacna': [(-18.8, -16.8, -71.8, -69.8), 'Tacna'],
        'Puno': [(-17.8, -13.8, -71.8, -68.8), 'Puno'],
        'Selva': [(-12.0, -1.8, -76.0, -68.0), 'Selva (General)']
    }
    
    # Crear mapa de colores según cantidad de instituciones
    max_instituciones = conteo_regiones.max()
    min_instituciones = conteo_regiones.min()
    
    # Normalizar valores para colormap
    norm = plt.Normalize(vmin=min_instituciones, vmax=max_instituciones)
    colormap = cm.get_cmap('YlOrRd')  # Amarillo a Rojo
    
    # Dibujar regiones como rectángulos coloreados
    rectangulos_dibujados = []
    for region, cantidad in conteo_regiones.items():
        if region in regiones_limites:
            lat_min, lat_max, lon_min, lon_max = regiones_limites[region][0]
            nombre_region = regiones_limites[region][1]
            
            # Color basado en cantidad de instituciones
            color = colormap(norm(cantidad))
            
            # Crear rectángulo para la región
            rectangle = plt.Rectangle((lon_min, lat_min), 
                                    lon_max - lon_min, 
                                    lat_max - lat_min,
                                    facecolor=color, 
                                    alpha=0.6, 
                                    edgecolor='black', 
                                    linewidth=0.8)
            ax.add_patch(rectangle)
            rectangulos_dibujados.append(region)
            
            # Agregar etiqueta con nombre de región y cantidad
            center_lat = (lat_min + lat_max) / 2
            center_lon = (lon_min + lon_max) / 2
            ax.text(center_lon, center_lat, f'{nombre_region}\n({cantidad} IIEE)', 
                   ha='center', va='center', fontsize=8, fontweight='bold',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))
    
    # Agregar puntos de instituciones educativas
    colores_puntos = {
        44: '#ff0000',  # Rojo
        47: '#0000ff',  # Azul
        48: '#00ff00',  # Verde
        54: '#ff00ff',  # Magenta
        72: '#ffaa00',  # Naranja
        79: '#800000',  # Marrón
    }
    
    marcadores_puntos = {
        44: 'o',  # Círculo
        47: 's',  # Cuadrado
        48: '^',  # Triángulo
        54: 'D',  # Diamante
        72: 'v',  # Triángulo invertido
        79: 'h',  # Hexágono
    }
    
    # Graficar puntos de instituciones por red
    if 'NUMERO_FYA' in df.columns:
        redes = sorted(df['NUMERO_FYA'].unique())
        
        for red in redes:
            mask_red = df['NUMERO_FYA'] == red
            if mask_red.sum() > 0:
                lats = df.loc[mask_red, 'LATITUD'].astype(float)
                lons = df.loc[mask_red, 'LONGITUD'].astype(float)
                
                color_punto = colores_puntos.get(red, '#666666')
                marcador = marcadores_puntos.get(red, 'o')
                
                ax.scatter(lons, lats, 
                          c=color_punto, 
                          marker=marcador,
                          s=60, 
                          alpha=0.9, 
                          edgecolors='white',
                          linewidth=1,
                          label=f'Red {red} ({mask_red.sum()} IIEE)',
                          zorder=10)
    
    # Dibujar contorno general del Perú
    peru_coords = np.array([
        [-81.3, -0.2], [-75.2, -0.1], [-69.0, -0.1], [-68.7, -9.0], 
        [-69.2, -13.2], [-70.0, -15.0], [-71.0, -17.2], [-75.0, -18.4], 
        [-81.3, -18.4], [-81.3, -15.0], [-80.2, -10.0], [-81.3, -0.2]
    ])
    
    poly_contorno = Polygon(peru_coords, fill=False, edgecolor='black', linewidth=3)
    ax.add_patch(poly_contorno)
    
    # Configurar ejes
    ax.set_xlabel('Longitud', fontsize=12, fontweight='bold')
    ax.set_ylabel('Latitud', fontsize=12, fontweight='bold')
    ax.set_title('Mapa del Perú - Regiones por Cantidad de Instituciones Educativas Fe y Alegría\ncon Ubicación de cada IIEE por Red', 
                fontsize=14, fontweight='bold', pad=20)
    
    # Agregar grilla
    ax.grid(True, alpha=0.3, linestyle='--')
    
    # Crear barra de colores para regiones
    sm = plt.cm.ScalarMappable(cmap=colormap, norm=norm)
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax, shrink=0.8, aspect=30)
    cbar.set_label('Número de Instituciones Educativas por Región', 
                   rotation=270, labelpad=20, fontweight='bold')
    
    # Crear leyenda para redes (puntos)
    legend_elements_redes = []
    for red in sorted(df['NUMERO_FYA'].unique()):
        cantidad = (df['NUMERO_FYA'] == red).sum()
        color_punto = colores_puntos.get(red, '#666666')
        marcador = marcadores_puntos.get(red, 'o')
        legend_elements_redes.append(
            plt.Line2D([0], [0], marker=marcador, color='w', 
                      markerfacecolor=color_punto, markersize=8,
                      label=f'Red {red} ({cantidad} IIEE)',
                      markeredgecolor='white', markeredgewidth=1)
        )
    
    # Posicionar leyenda de redes
    legend_redes = ax.legend(handles=legend_elements_redes, 
                            title='Redes Fe y Alegría (Puntos)', 
                            loc='upper left', 
                            bbox_to_anchor=(0.02, 0.98),
                            fontsize=9,
                            title_fontsize=10)
    legend_redes.get_title().set_fontweight('bold')
    
    # Estadísticas en el mapa
    stats_text = f"""ESTADÍSTICAS GENERALES:
• Total instituciones: {len(df)}
• Regiones con IIEE: {len(conteo_regiones)}
• Mayor concentración: {conteo_regiones.index[0]} ({conteo_regiones.iloc[0]} IIEE)
• Rango altitudinal: {df['ALTITUD_MSNM'].min():.0f} - {df['ALTITUD_MSNM'].max():.0f} msnm"""
    
    ax.text(0.02, 0.15, stats_text, transform=ax.transAxes, 
            fontsize=9, verticalalignment='top',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='lightblue', alpha=0.8))
    
    # Ajustar diseño
    plt.tight_layout()
    
    # Guardar mapa
    nombre_archivo = 'mapa_peru_regiones_iiee.png'
    plt.savefig(nombre_archivo, dpi=300, bbox_inches='tight', 
                facecolor='white', edgecolor='none')
    
    print(f"\nMapa de regiones guardado como: {nombre_archivo}")
    
    # Mostrar estadísticas detalladas
    print("\n=== ESTADÍSTICAS DETALLADAS POR REGIÓN ===")
    for region, cantidad in conteo_regiones.items():
        porcentaje = (cantidad / len(df)) * 100
        print(f"{region:15s}: {cantidad:2d} IIEE ({porcentaje:4.1f}%)")
    
    # Mostrar el mapa
    plt.show()
    
    return df, conteo_regiones

if __name__ == "__main__":
    try:
        datos, conteos = crear_mapa_regiones_peru()
        print("\n¡Mapa de regiones con IIEE generado exitosamente!")
    except Exception as e:
        print(f"Error al generar el mapa: {str(e)}")
        import traceback
        traceback.print_exc()