import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Polygon
import matplotlib.colors as colors

def crear_mapa_peru_con_forma():
    """
    Crea un mapa del Perú con forma reconocible y regiones delimitadas
    """
    
    # Cargar datos de instituciones
    try:
        df = pd.read_csv('instituciones_con_region.csv', encoding='utf-8')
    except:
        print("Error: Primero ejecuta identificar_regiones.py")
        return
    
    # Contar instituciones por región
    conteo_regiones = df['REGION'].value_counts()
    
    print(f"Generando mapa del Perú con {len(df)} instituciones en {len(conteo_regiones)} regiones")
    
    # Crear figura
    fig, ax = plt.subplots(figsize=(10, 14))
    ax.set_xlim(-82, -68)
    ax.set_ylim(-18.5, 0)
    
    # Contorno detallado del Perú (forma reconocible)
    peru_contorno = np.array([
        # Frontera norte con Ecuador
        [-81.33, -3.24], [-80.89, -3.76], [-80.30, -3.39], [-79.86, -4.26],
        [-79.22, -4.45], [-78.64, -4.64], [-78.16, -4.95], [-77.54, -4.61],
        [-77.13, -4.45], [-76.64, -4.38], [-75.91, -4.60], [-75.35, -4.45],
        [-74.74, -4.34], [-74.17, -4.19], [-73.66, -3.84], [-72.86, -3.67],
        [-72.18, -3.42], [-71.66, -2.61], [-70.99, -2.30], [-70.35, -2.27],
        [-69.94, -1.71], [-69.44, -1.46], [-68.67, -1.07], [-68.66, -0.54],
        
        # Frontera este con Brasil
        [-68.67, -0.96], [-68.88, -1.29], [-69.20, -1.71], [-69.61, -2.22],
        [-69.98, -2.84], [-70.30, -3.57], [-70.58, -4.41], [-70.82, -5.36],
        [-71.02, -6.42], [-71.18, -7.59], [-71.30, -8.87], [-71.38, -10.26],
        [-71.42, -11.76], [-71.42, -13.37], [-71.38, -15.09], [-71.30, -16.92],
        [-70.94, -17.29], [-70.48, -17.54], [-69.92, -17.67], [-69.26, -17.69],
        [-68.67, -17.58],
        
        # Frontera sur
        [-68.66, -18.35], [-69.96, -17.58], [-70.84, -17.11], [-71.40, -16.46],
        [-71.64, -15.63], [-71.56, -14.62], [-71.16, -13.44], [-70.44, -12.08],
        [-75.23, -18.35], [-76.00, -18.35], [-81.33, -18.35], [-81.33, -17.50],
        
        # Costa oeste
        [-81.33, -16.50], [-81.20, -15.40], [-81.05, -14.25], [-80.88, -13.05],
        [-80.69, -11.80], [-80.48, -10.50], [-80.25, -9.15], [-80.00, -7.75],
        [-79.73, -6.30], [-79.44, -4.80], [-79.13, -3.25], [-81.33, -3.24]
    ])
    
    # Dibujar contorno del Perú
    poly_peru = Polygon(peru_contorno, closed=True, 
                       facecolor='#f0f0f0', alpha=0.5,
                       edgecolor='black', linewidth=2.5, zorder=1)
    ax.add_patch(poly_peru)
    
    # Configurar colores para regiones
    cmap = plt.cm.YlOrRd
    norm = colors.Normalize(vmin=conteo_regiones.min(), vmax=conteo_regiones.max())
    
    # Coordenadas aproximadas de regiones principales (polígonos simples)
    regiones_formas = {
        'Piura': [[-81.3, -4.0], [-79.8, -4.0], [-79.0, -6.0], [-80.8, -6.2], [-81.3, -5.0]],
        'Lambayeque': [[-80.8, -5.8], [-79.0, -5.8], [-78.8, -7.2], [-80.6, -7.2]],
        'La Libertad': [[-79.8, -6.8], [-78.0, -6.8], [-77.8, -8.8], [-79.6, -8.8]],
        'Áncash': [[-78.7, -8.0], [-76.8, -8.0], [-76.8, -10.8], [-78.7, -10.8]],
        'Lima': [[-77.8, -10.8], [-75.8, -10.8], [-75.8, -13.0], [-77.8, -13.0]],
        'Ica': [[-76.5, -13.0], [-74.8, -13.0], [-74.8, -15.8], [-76.5, -15.8]],
        'Arequipa': [[-74.5, -14.3], [-70.8, -14.3], [-70.8, -16.7], [-74.5, -16.7]],
        'Cusco': [[-73.8, -11.0], [-70.8, -11.0], [-70.8, -14.8], [-73.8, -14.8]],
        'Ayacucho': [[-75.2, -12.0], [-72.8, -12.0], [-72.8, -15.8], [-75.2, -15.8]],
        'Ucayali': [[-75.8, -7.8], [-72.8, -7.8], [-72.8, -11.8], [-75.8, -11.8]],
        'Selva': [[-76.0, -1.8], [-68.8, -1.8], [-68.8, -8.0], [-76.0, -8.0]]
    }
    
    # Dibujar regiones con colores
    for region, coords in regiones_formas.items():
        if region in conteo_regiones.index:
            cantidad = conteo_regiones[region]
            color = cmap(norm(cantidad))
            
            poly_coords = np.array(coords)
            poly = Polygon(poly_coords, closed=True,
                          facecolor=color, alpha=0.7,
                          edgecolor='darkblue', linewidth=1, zorder=2)
            ax.add_patch(poly)
            
            # Etiqueta de región
            center_x = poly_coords[:, 0].mean()
            center_y = poly_coords[:, 1].mean()
            ax.text(center_x, center_y, f'{region}\n{cantidad} IIEE', 
                   ha='center', va='center', fontsize=8, fontweight='bold',
                   bbox=dict(boxstyle='round,pad=0.2', facecolor='white', 
                            alpha=0.9, edgecolor='navy'), zorder=5)
    
    # Agregar puntos de instituciones educativas
    colores_redes = {
        44: '#ff4444', 47: '#4444ff', 48: '#44ff44',
        54: '#ff44ff', 72: '#ffaa44', 79: '#aa4444'
    }
    
    marcadores = {44: 'o', 47: 's', 48: '^', 54: 'D', 72: 'v', 79: 'h'}
    
    legend_elements = []
    for red in sorted(df['NUMERO_FYA'].unique()):
        mask_red = df['NUMERO_FYA'] == red
        if mask_red.sum() > 0:
            lats = df.loc[mask_red, 'LATITUD'].astype(float)
            lons = df.loc[mask_red, 'LONGITUD'].astype(float)
            
            color_red = colores_redes.get(red, '#666666')
            marcador = marcadores.get(red, 'o')
            
            scatter = ax.scatter(lons, lats, 
                               c=color_red, marker=marcador, s=50, 
                               alpha=0.9, edgecolors='white', linewidth=0.8,
                               zorder=10)
            
            # Elemento de leyenda
            legend_elements.append(plt.Line2D([0], [0], marker=marcador, color='w',
                                            markerfacecolor=color_red, markersize=8,
                                            label=f'Red {red} ({mask_red.sum()})',
                                            markeredgecolor='white', markeredgewidth=0.8))
    
    # Configurar el mapa
    ax.set_xlabel('Longitud', fontsize=11, fontweight='bold')
    ax.set_ylabel('Latitud', fontsize=11, fontweight='bold')
    ax.set_title('MAPA DEL PERÚ\nInstituciones Educativas Fe y Alegría por Región', 
                fontsize=14, fontweight='bold', pad=20)
    
    # Grilla
    ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
    
    # Leyenda de redes
    legend1 = ax.legend(handles=legend_elements, title='Redes Fe y Alegría', 
                       loc='upper left', fontsize=8, title_fontsize=9,
                       framealpha=0.9, edgecolor='navy')
    legend1.get_title().set_fontweight('bold')
    
    # Barra de colores para regiones
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax, shrink=0.8, aspect=25, pad=0.02)
    cbar.set_label('Cantidad de IIEE por Región', rotation=270, labelpad=20, fontweight='bold')
    
    # Estadísticas en el mapa
    total_iiee = len(df)
    region_mayor = conteo_regiones.index[0]
    cantidad_mayor = conteo_regiones.iloc[0]
    
    stats_text = f"""ESTADÍSTICAS NACIONALES
Total IIEE: {total_iiee}
Regiones: {len(conteo_regiones)}
Mayor concentración:
{region_mayor} ({cantidad_mayor} IIEE)
Rango altitudinal:
{df['ALTITUD_MSNM'].min():.0f} - {df['ALTITUD_MSNM'].max():.0f} msnm"""
    
    ax.text(0.02, 0.25, stats_text, transform=ax.transAxes, fontsize=8,
            bbox=dict(boxstyle='round,pad=0.4', facecolor='lightcyan', 
                     alpha=0.9, edgecolor='navy'), verticalalignment='top')
    
    # Ajustar diseño
    plt.tight_layout()
    
    # Guardar
    nombre_archivo = 'mapa_peru_forma_real.png'
    plt.savefig(nombre_archivo, dpi=300, bbox_inches='tight', 
                facecolor='white', edgecolor='none')
    
    print(f"\nMapa guardado como: {nombre_archivo}")
    print(f"Resolución: 300 DPI")
    
    # Mostrar estadísticas por región
    print(f"\n{'='*50}")
    print("DISTRIBUCIÓN REGIONAL DE INSTITUCIONES EDUCATIVAS")
    print(f"{'='*50}")
    
    for i, (region, cantidad) in enumerate(conteo_regiones.items(), 1):
        porcentaje = (cantidad / total_iiee) * 100
        print(f"{i:2d}. {region:15s}: {cantidad:2d} IIEE ({porcentaje:5.1f}%)")
    
    plt.show()
    return df, conteo_regiones

if __name__ == "__main__":
    try:
        datos, conteos = crear_mapa_peru_con_forma()
        print(f"\n¡Mapa del Perú con forma real generado exitosamente!")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()