import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import requests
import json
from matplotlib.patches import Polygon
from matplotlib.collections import PatchCollection
import matplotlib.colors as colors

def descargar_geojson_peru():
    """
    Descarga los datos geográficos de las regiones del Perú
    """
    try:
        # URL de datos geográficos del Perú (regiones)
        url = "https://raw.githubusercontent.com/holtzy/D3-graph-gallery/master/DATA/world.geojson"
        
        # Intentar con una fuente específica del Perú
        url_peru = "https://raw.githubusercontent.com/juaneladio/peru-geojson/master/peru_departamental_simple.geojson"
        
        print("Intentando descargar datos geográficos del Perú...")
        response = requests.get(url_peru, timeout=10)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error al descargar desde {url_peru}: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"Error al descargar GeoJSON: {e}")
        return None

def crear_mapa_peru_real_alternativo():
    """
    Crea un mapa del Perú usando coordenadas aproximadas de las regiones
    con forma más realista
    """
    
    # Cargar datos de instituciones
    try:
        df = pd.read_csv('instituciones_con_region.csv', encoding='utf-8')
    except:
        print("Error: Primero ejecuta identificar_regiones.py")
        return
    
    # Contar instituciones por región
    conteo_regiones = df['REGION'].value_counts()
    
    print(f"Cargados {len(df)} registros")
    print(f"Regiones identificadas: {len(conteo_regiones)}")
    
    # Crear figura
    fig, ax = plt.subplots(figsize=(12, 16))
    
    # Límites del Perú
    ax.set_xlim(-82, -68)
    ax.set_ylim(-18.5, 0)
    
    # Coordenadas más detalladas del contorno del Perú
    peru_detailed = np.array([
        # Costa norte
        [-81.327, -3.239], [-80.896, -4.046], [-80.469, -4.636],
        [-80.131, -5.390], [-79.985, -6.153], [-79.368, -6.853],
        [-78.603, -7.453], [-78.180, -8.065], [-77.866, -8.643],
        [-77.629, -9.184], [-77.288, -9.679], [-76.947, -10.069],
        
        # Costa centro
        [-76.598, -10.487], [-76.283, -11.008], [-76.032, -11.580],
        [-75.821, -12.205], [-75.650, -12.883], [-75.519, -13.615],
        [-75.428, -14.400], [-75.377, -15.238], [-75.366, -16.129],
        
        # Costa sur
        [-75.395, -17.074], [-75.464, -18.069], [-70.930, -18.069],
        
        # Frontera con Bolivia y Brasil (este)
        [-68.665, -18.069], [-68.665, -16.290], [-69.116, -15.479],
        [-69.567, -14.668], [-69.945, -13.857], [-70.249, -13.046],
        [-70.479, -12.235], [-70.635, -11.424], [-70.717, -10.613],
        [-70.725, -9.802], [-70.659, -8.991], [-70.519, -8.180],
        [-70.305, -7.369], [-70.017, -6.558], [-69.655, -5.747],
        [-69.219, -4.936], [-68.709, -4.125], [-68.125, -3.314],
        
        # Frontera norte (con Ecuador y Colombia)
        [-68.467, -2.503], [-69.809, -1.692], [-70.651, -0.881],
        [-71.993, -0.070], [-73.335, -0.741], [-74.177, -1.552],
        [-75.019, -2.363], [-75.861, -3.174], [-77.203, -2.985],
        [-78.045, -3.796], [-79.387, -3.607], [-80.229, -3.418],
        [-81.071, -3.229], [-81.327, -3.239]
    ])
    
    # Dibujar el contorno del Perú
    poly_peru = Polygon(peru_detailed, closed=True, 
                       facecolor='lightgray', alpha=0.3,
                       edgecolor='black', linewidth=2)
    ax.add_patch(poly_peru)
    
    # Definir colores para cantidad de instituciones
    max_instituciones = conteo_regiones.max()
    min_instituciones = conteo_regiones.min()
    
    # Crear mapa de calor para regiones
    cmap = plt.cm.YlOrRd
    norm = colors.Normalize(vmin=min_instituciones, vmax=max_instituciones)
    
    # Dibujar regiones aproximadas con sus formas
    regiones_coords = {
        'Piura': np.array([
            [-81.3, -4.0], [-80.2, -4.0], [-79.8, -5.0], 
            [-79.5, -5.8], [-80.8, -6.2], [-81.3, -5.0], [-81.3, -4.0]
        ]),
        'Tumbes': np.array([
            [-81.3, -3.2], [-80.2, -3.2], [-80.0, -4.0], 
            [-81.3, -4.0], [-81.3, -3.2]
        ]),
        'Lambayeque': np.array([
            [-80.8, -6.0], [-79.5, -5.8], [-79.2, -7.0], 
            [-80.5, -7.2], [-80.8, -6.0]
        ]),
        'La Libertad': np.array([
            [-79.8, -7.0], [-78.5, -6.8], [-78.0, -8.5], 
            [-79.5, -8.8], [-79.8, -7.0]
        ]),
        'Áncash': np.array([
            [-78.5, -8.5], [-77.2, -8.0], [-76.8, -10.5], 
            [-78.0, -10.8], [-78.5, -8.5]
        ]),
        'Lima': np.array([
            [-77.5, -10.8], [-76.2, -10.8], [-75.8, -13.0], 
            [-77.0, -13.2], [-77.5, -10.8]
        ]),
        'Ica': np.array([
            [-76.5, -13.0], [-75.0, -13.0], [-74.8, -15.8], 
            [-76.2, -15.8], [-76.5, -13.0]
        ]),
        'Arequipa': np.array([
            [-74.5, -14.3], [-71.5, -14.3], [-70.8, -16.7], 
            [-73.8, -16.7], [-74.5, -14.3]
        ]),
        'Cusco': np.array([
            [-73.8, -11.0], [-70.8, -11.0], [-70.8, -14.8], 
            [-73.8, -14.8], [-73.8, -11.0]
        ]),
        'Ayacucho': np.array([
            [-75.2, -12.0], [-72.8, -12.0], [-72.8, -15.8], 
            [-75.2, -15.8], [-75.2, -12.0]
        ]),
        'Ucayali': np.array([
            [-75.8, -7.8], [-72.8, -7.8], [-72.8, -11.8], 
            [-75.8, -11.8], [-75.8, -7.8]
        ]),
        'Selva': np.array([  # Loreto principalmente
            [-76.8, -1.8], [-73.8, -1.8], [-68.8, -5.8], 
            [-73.8, -8.8], [-76.8, -5.8], [-76.8, -1.8]
        ])
    }
    
    # Dibujar cada región con color según cantidad de IIEE
    for region, coordenadas in regiones_coords.items():
        if region in conteo_regiones.index:
            cantidad = conteo_regiones[region]
            color = cmap(norm(cantidad))
            
            poly_region = Polygon(coordenadas, closed=True,
                                facecolor=color, alpha=0.7,
                                edgecolor='navy', linewidth=1)
            ax.add_patch(poly_region)
            
            # Agregar etiqueta
            center_x = coordenadas[:, 0].mean()
            center_y = coordenadas[:, 1].mean()
            ax.text(center_x, center_y, f'{region}\n({cantidad})', 
                   ha='center', va='center', fontsize=9, fontweight='bold',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))
    
    # Agregar puntos de instituciones
    colores_redes = {
        44: '#ff0000', 47: '#0000ff', 48: '#00ff00',
        54: '#ff00ff', 72: '#ffaa00', 79: '#800000'
    }
    
    for red in sorted(df['NUMERO_FYA'].unique()):
        mask_red = df['NUMERO_FYA'] == red
        if mask_red.sum() > 0:
            lats = df.loc[mask_red, 'LATITUD'].astype(float)
            lons = df.loc[mask_red, 'LONGITUD'].astype(float)
            
            ax.scatter(lons, lats, 
                      c=colores_redes.get(red, '#666666'),
                      s=40, alpha=0.9, edgecolors='white', linewidth=0.5,
                      label=f'Red {red} ({mask_red.sum()})',
                      zorder=10)
    
    # Configurar mapa
    ax.set_xlabel('Longitud', fontsize=12, fontweight='bold')
    ax.set_ylabel('Latitud', fontsize=12, fontweight='bold')
    ax.set_title('Mapa del Perú - Distribución Regional de Instituciones Educativas Fe y Alegría', 
                fontsize=13, fontweight='bold', pad=20)
    
    ax.grid(True, alpha=0.3)
    ax.legend(title='Redes Fe y Alegría', loc='upper right', fontsize=8)
    
    # Barra de colores
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax, shrink=0.6)
    cbar.set_label('Número de IIEE por Región', rotation=270, labelpad=15)
    
    # Estadísticas
    stats = f"""DISTRIBUCIÓN NACIONAL:
• Total: {len(df)} instituciones
• {len(conteo_regiones)} regiones
• Mayor: {conteo_regiones.index[0]} ({conteo_regiones.iloc[0]})
• Menor: {conteo_regiones.index[-1]} ({conteo_regiones.iloc[-1]})"""
    
    ax.text(0.02, 0.02, stats, transform=ax.transAxes, fontsize=9,
            bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))
    
    plt.tight_layout()
    
    # Guardar
    nombre_archivo = 'mapa_peru_real_regiones.png'
    plt.savefig(nombre_archivo, dpi=300, bbox_inches='tight')
    print(f"\nMapa guardado como: {nombre_archivo}")
    
    # Mostrar estadísticas
    print("\n=== DISTRIBUCIÓN POR REGIÓN ===")
    for region, cantidad in conteo_regiones.items():
        print(f"{region:15s}: {cantidad:2d} IIEE")
    
    plt.show()
    return df, conteo_regiones

if __name__ == "__main__":
    try:
        # Intentar descargar datos reales primero
        geojson_data = descargar_geojson_peru()
        
        if geojson_data is None:
            print("Usando coordenadas aproximadas...")
            crear_mapa_peru_real_alternativo()
        else:
            print("Datos GeoJSON descargados exitosamente")
            # Aquí implementarías el procesamiento del GeoJSON
            crear_mapa_peru_real_alternativo()
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()