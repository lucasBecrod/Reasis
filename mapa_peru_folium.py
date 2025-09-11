import pandas as pd
import folium
from folium.plugins import MarkerCluster
import webbrowser
import os

def crear_mapa_peru_folium():
    # Leer el archivo CSV
    archivo_csv = r"archivado\clustering\01 Analisis Excel\reasis_database_v5_final.csv"
    
    # Leer el archivo con separador de punto y coma (probando diferentes codificaciones)
    try:
        df = pd.read_csv(archivo_csv, sep=';', encoding='utf-8')
    except UnicodeDecodeError:
        try:
            df = pd.read_csv(archivo_csv, sep=';', encoding='latin-1')
        except UnicodeDecodeError:
            df = pd.read_csv(archivo_csv, sep=';', encoding='cp1252')
    
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
    
    # Centro geográfico aproximado del Perú
    centro_lat = df_validas['LATITUD'].astype(float).mean()
    centro_lon = df_validas['LONGITUD'].astype(float).mean()
    
    # Crear el mapa base
    mapa = folium.Map(
        location=[centro_lat, centro_lon],
        zoom_start=6,
        tiles='OpenStreetMap'
    )
    
    # Definir colores para cada red
    colores_redes = {
        44: 'red',
        47: 'blue', 
        48: 'green',
        54: 'purple',
        72: 'orange',
        79: 'darkred',
        # Agregar más colores si hay más redes
    }
    
    # Crear cluster para mejor visualización
    marker_cluster = MarkerCluster().add_to(mapa)
    
    # Agregar marcadores para cada institución
    for idx, row in df_validas.iterrows():
        lat = float(row['LATITUD'])
        lon = float(row['LONGITUD'])
        nombre = row['NOMBRE_INSTITUCION'] if pd.notna(row['NOMBRE_INSTITUCION']) else 'Sin nombre'
        red = row['NUMERO_FYA'] if pd.notna(row['NUMERO_FYA']) else 'Sin red'
        codigo = row['CODIGO_MODULAR'] if pd.notna(row['CODIGO_MODULAR']) else 'Sin código'
        altitud = row['ALTITUD_MSNM'] if pd.notna(row['ALTITUD_MSNM']) else 'N/A'
        
        # Definir color según la red
        color = colores_redes.get(red, 'gray')
        
        # Crear popup con información de la institución
        popup_html = f"""
        <div style="font-size: 12px; width: 200px;">
            <b>{nombre}</b><br>
            <b>Código:</b> {codigo}<br>
            <b>Red:</b> {red}<br>
            <b>Altitud:</b> {altitud} msnm<br>
            <b>Coordenadas:</b> {lat:.4f}, {lon:.4f}
        </div>
        """
        
        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=f"{nombre} (Red {red})",
            icon=folium.Icon(color=color, icon='graduation-cap', prefix='fa')
        ).add_to(marker_cluster)
    
    # Agregar leyenda
    leyenda_html = """
    <div style="position: fixed; 
                top: 10px; right: 10px; width: 150px; height: auto; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:12px; padding: 10px">
    <h4>Redes Fe y Alegría</h4>
    """
    
    # Obtener estadísticas por red
    if 'NUMERO_FYA' in df_validas.columns:
        distribucion = df_validas['NUMERO_FYA'].value_counts().sort_index()
        for red in distribucion.index:
            cantidad = distribucion[red]
            color = colores_redes.get(red, 'gray')
            leyenda_html += f'<p><i class="fa fa-circle" style="color:{color}"></i> Red {red}: {cantidad} IIEE</p>'
    
    leyenda_html += "</div>"
    mapa.get_root().html.add_child(folium.Element(leyenda_html))
    
    # Guardar el mapa
    nombre_archivo = 'mapa_peru_fe_y_alegria.html'
    mapa.save(nombre_archivo)
    
    # Mostrar estadísticas
    print("\n=== ESTADÍSTICAS GEOGRÁFICAS ===")
    lats = df_validas['LATITUD'].astype(float)
    lons = df_validas['LONGITUD'].astype(float)
    
    print(f"Latitud mínima: {lats.min():.4f}")
    print(f"Latitud máxima: {lats.max():.4f}")
    print(f"Longitud mínima: {lons.min():.4f}")
    print(f"Longitud máxima: {lons.max():.4f}")
    print(f"Centro del mapa: {centro_lat:.4f}, {centro_lon:.4f}")
    
    if 'NUMERO_FYA' in df_validas.columns:
        print("\n=== DISTRIBUCIÓN POR RED ===")
        distribucion = df_validas['NUMERO_FYA'].value_counts().sort_index()
        for red, cantidad in distribucion.items():
            print(f"Red {red}: {cantidad} instituciones")
    
    print(f"\nMapa interactivo guardado como: {nombre_archivo}")
    print("Abriendo mapa en el navegador...")
    
    # Abrir el mapa en el navegador
    ruta_completa = os.path.abspath(nombre_archivo)
    webbrowser.open(f'file://{ruta_completa}')
    
    return df_validas

if __name__ == "__main__":
    try:
        datos_mapeados = crear_mapa_peru_folium()
        print("\n¡Mapa generado exitosamente!")
    except Exception as e:
        print(f"Error al generar el mapa: {str(e)}")
        print("\nPosibles soluciones:")
        print("1. Instalar librerías: pip install folium pandas")
        print("2. Verificar que el archivo CSV exista en la ruta especificada")