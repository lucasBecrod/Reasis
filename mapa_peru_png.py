import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Polygon
import matplotlib.patches as patches

def crear_mapa_peru_png():
    # Leer el archivo CSV
    archivo_csv = r"archivado\clustering\01 Analisis Excel\reasis_database_v5_final.csv"
    
    # Leer el archivo con diferentes codificaciones
    try:
        df = pd.read_csv(archivo_csv, sep=';', encoding='utf-8')
    except UnicodeDecodeError:
        try:
            df = pd.read_csv(archivo_csv, sep=';', encoding='latin-1')
        except UnicodeDecodeError:
            df = pd.read_csv(archivo_csv, sep=';', encoding='cp1252')
    
    print(f"Total de registros: {len(df)}")
    
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
    
    # Crear la figura
    fig, ax = plt.subplots(figsize=(12, 14))
    
    # Límites geográficos de Perú
    ax.set_xlim(-82, -68)
    ax.set_ylim(-18.5, 0)
    
    # Agregar grilla
    ax.grid(True, alpha=0.3, linestyle='--')
    
    # Dibujar contorno básico del Perú (aproximado)
    # Coordenadas aproximadas del contorno peruano
    peru_coords = np.array([
        [-81.3, -0.2],    # Frontera norte-oeste
        [-75.2, -0.1],    # Frontera norte
        [-69.0, -0.1],    # Frontera noreste
        [-68.7, -9.0],    # Este medio
        [-69.2, -13.2],   # Sureste
        [-70.0, -15.0],   # Sureste 2
        [-71.0, -17.2],   # Sur
        [-75.0, -18.4],   # Suroeste
        [-81.3, -18.4],   # Costa suroeste
        [-81.3, -15.0],   # Costa oeste medio
        [-80.2, -10.0],   # Costa oeste norte
        [-81.3, -0.2]     # Regreso al inicio
    ])
    
    # Dibujar el contorno del Perú
    poly = Polygon(peru_coords, fill=False, edgecolor='black', linewidth=2, alpha=0.7)
    ax.add_patch(poly)
    
    # Rellenar el interior del Perú
    poly_fill = Polygon(peru_coords, fill=True, facecolor='lightgray', alpha=0.2)
    ax.add_patch(poly_fill)
    
    # Definir colores para cada red
    colores_redes = {
        44: '#ff4444',  # Rojo
        47: '#4444ff',  # Azul
        48: '#44ff44',  # Verde
        54: '#ff44ff',  # Magenta
        72: '#ffaa00',  # Naranja
        79: '#aa0044',  # Rojo oscuro
    }
    
    marcadores_redes = {
        44: 'o',  # Círculo
        47: 's',  # Cuadrado
        48: '^',  # Triángulo
        54: 'D',  # Diamante
        72: 'v',  # Triángulo invertido
        79: 'h',  # Hexágono
    }
    
    # Graficar los puntos por red
    if 'NUMERO_FYA' in df_validas.columns:
        redes = sorted(df_validas['NUMERO_FYA'].unique())
        
        for red in redes:
            mask_red = df_validas['NUMERO_FYA'] == red
            if mask_red.sum() > 0:
                lats = df_validas.loc[mask_red, 'LATITUD'].astype(float)
                lons = df_validas.loc[mask_red, 'LONGITUD'].astype(float)
                
                color = colores_redes.get(red, '#666666')
                marcador = marcadores_redes.get(red, 'o')
                
                ax.scatter(lons, lats, 
                          c=color, 
                          marker=marcador,
                          s=100, 
                          alpha=0.8, 
                          edgecolors='white',
                          linewidth=1,
                          label=f'Red {red} ({mask_red.sum()} IIEE)',
                          zorder=5)
    
    # Configurar etiquetas y título
    ax.set_xlabel('Longitud', fontsize=12)
    ax.set_ylabel('Latitud', fontsize=12)
    ax.set_title('Mapa del Perú - Instituciones Educativas Fe y Alegría\nDistribución Geográfica por Coordenadas', 
                fontsize=14, fontweight='bold', pad=20)
    
    # Agregar leyenda
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=10)
    
    # Agregar información estadística en el mapa
    stats_text = f"""Estadísticas:
    • Total instituciones: {len(df_validas)}
    • Rango latitud: {df_validas['LATITUD'].astype(float).min():.2f}° a {df_validas['LATITUD'].astype(float).max():.2f}°
    • Rango longitud: {df_validas['LONGITUD'].astype(float).min():.2f}° a {df_validas['LONGITUD'].astype(float).max():.2f}°
    • Altitud: {df_validas['ALTITUD_MSNM'].astype(float).min():.0f} - {df_validas['ALTITUD_MSNM'].astype(float).max():.0f} msnm"""
    
    ax.text(0.02, 0.02, stats_text, transform=ax.transAxes, 
            fontsize=9, verticalalignment='bottom',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    # Ajustar diseño
    plt.tight_layout()
    
    # Guardar como PNG de alta resolución
    nombre_archivo = 'mapa_peru_fe_y_alegria.png'
    plt.savefig(nombre_archivo, dpi=300, bbox_inches='tight', 
                facecolor='white', edgecolor='none')
    
    print(f"\nMapa PNG guardado como: {nombre_archivo}")
    
    # Mostrar estadísticas detalladas
    print("\n=== ESTADÍSTICAS GEOGRÁFICAS ===")
    lats = df_validas['LATITUD'].astype(float)
    lons = df_validas['LONGITUD'].astype(float)
    alts = df_validas['ALTITUD_MSNM'].astype(float)
    
    print(f"Latitud - Min: {lats.min():.4f}°, Max: {lats.max():.4f}°")
    print(f"Longitud - Min: {lons.min():.4f}°, Max: {lons.max():.4f}°")
    print(f"Altitud - Min: {alts.min():.0f} msnm, Max: {alts.max():.0f} msnm")
    
    if 'NUMERO_FYA' in df_validas.columns:
        print("\n=== DISTRIBUCIÓN POR RED ===")
        distribucion = df_validas['NUMERO_FYA'].value_counts().sort_index()
        for red, cantidad in distribucion.items():
            color = colores_redes.get(red, '#666666')
            print(f"Red {red}: {cantidad} instituciones (Color: {color})")
    
    # Mostrar el mapa
    plt.show()
    
    return df_validas

if __name__ == "__main__":
    try:
        datos_mapeados = crear_mapa_peru_png()
        print("\n¡Mapa PNG generado exitosamente!")
        print("El archivo se encuentra en la carpeta actual del proyecto.")
    except Exception as e:
        print(f"Error al generar el mapa: {str(e)}")
        import traceback
        traceback.print_exc()