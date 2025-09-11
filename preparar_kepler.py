import pandas as pd

def crear_archivo_para_kepler():
    """
    Prepara el archivo CSV optimizado para usar en Kepler.gl
    """
    
    # Cargar datos de instituciones
    try:
        df = pd.read_csv('instituciones_con_region.csv', encoding='utf-8')
        print(f"Datos cargados: {len(df)} instituciones")
    except FileNotFoundError:
        print("Error: Archivo 'instituciones_con_region.csv' no encontrado")
        print("Ejecuta primero: python identificar_regiones.py")
        return
    
    # Crear archivo optimizado para Kepler.gl
    df_kepler = df.copy()
    
    # Limpiar y optimizar columnas para Kepler
    df_kepler['RED_NOMBRE'] = 'Red Fe y Alegria ' + df_kepler['NUMERO_FYA'].astype(str)
    df_kepler['INSTITUCION_TOOLTIP'] = (
        df_kepler['NOMBRE_INSTITUCION'].fillna('Sin nombre') + 
        ' - Red ' + df_kepler['NUMERO_FYA'].astype(str) + 
        ' (' + df_kepler['REGION'] + ')'
    )
    
    # Asegurar que las coordenadas son numéricas
    df_kepler['LATITUD'] = pd.to_numeric(df_kepler['LATITUD'], errors='coerce')
    df_kepler['LONGITUD'] = pd.to_numeric(df_kepler['LONGITUD'], errors='coerce')
    df_kepler['ALTITUD_MSNM'] = pd.to_numeric(df_kepler['ALTITUD_MSNM'], errors='coerce')
    
    # Eliminar filas con coordenadas inválidas
    df_kepler = df_kepler.dropna(subset=['LATITUD', 'LONGITUD'])
    
    # Seleccionar columnas importantes para Kepler
    columnas_kepler = [
        'CODIGO_MODULAR', 'NOMBRE_INSTITUCION', 'NUMERO_FYA', 'RED_NOMBRE',
        'LATITUD', 'LONGITUD', 'ALTITUD_MSNM', 'REGION', 'INSTITUCION_TOOLTIP'
    ]
    
    df_final = df_kepler[columnas_kepler].copy()
    
    # Guardar archivo para Kepler.gl
    archivo_kepler = 'iiee_fe_y_alegria_kepler.csv'
    df_final.to_csv(archivo_kepler, index=False, encoding='utf-8')
    
    # Contar instituciones por región
    conteo_regiones = df_final['REGION'].value_counts()
    conteo_redes = df_final['NUMERO_FYA'].value_counts().sort_index()
    
    print(f"\n" + "="*60)
    print("ARCHIVO PREPARADO PARA KEPLER.GL")
    print("="*60)
    print(f"Archivo creado: {archivo_kepler}")
    print(f"Total instituciones: {len(df_final)}")
    print(f"Coordenadas validas: {len(df_final)}")
    
    print(f"\nINSTRUCCIONES PASO A PASO:")
    print("1. Ve a: https://kepler.gl/")
    print(f"2. Arrastra el archivo: {archivo_kepler}")
    print("3. Kepler detectara automaticamente las coordenadas")
    print("4. Configuraciones recomendadas:")
    print("   - Tipo de capa: Point (puntos)")
    print("   - Color por: NUMERO_FYA o RED_NOMBRE")
    print("   - Tamaño por: ALTITUD_MSNM (opcional)")
    print("   - Tooltip: INSTITUCION_TOOLTIP")
    print("5. Mapa base: Selecciona 'Satellite' o 'Streets'")
    print("6. Agrega filtros por REGION si quieres")
    print("7. Exporta: Camera icon -> Export Image -> PNG")
    
    print(f"\nESTADISTICAS POR REGION:")
    for i, (region, cantidad) in enumerate(conteo_regiones.items(), 1):
        porcentaje = (cantidad / len(df_final)) * 100
        print(f"{i:2d}. {region:15s}: {cantidad:2d} IIEE ({porcentaje:4.1f}%)")
    
    print(f"\nESTADISTICAS POR RED:")
    for red, cantidad in conteo_redes.items():
        porcentaje = (cantidad / len(df_final)) * 100
        print(f"Red {red}: {cantidad:2d} IIEE ({porcentaje:4.1f}%)")
    
    # Crear archivo de estadísticas adicional
    stats_file = 'estadisticas_regiones.txt'
    with open(stats_file, 'w', encoding='utf-8') as f:
        f.write("ESTADISTICAS INSTITUCIONES EDUCATIVAS FE Y ALEGRIA\n")
        f.write("="*50 + "\n\n")
        f.write(f"Total instituciones: {len(df_final)}\n")
        f.write(f"Regiones cubiertas: {len(conteo_regiones)}\n\n")
        
        f.write("DISTRIBUCION POR REGION:\n")
        for region, cantidad in conteo_regiones.items():
            porcentaje = (cantidad / len(df_final)) * 100
            f.write(f"{region}: {cantidad} IIEE ({porcentaje:.1f}%)\n")
        
        f.write("\nDISTRIBUCION POR RED:\n")
        for red, cantidad in conteo_redes.items():
            porcentaje = (cantidad / len(df_final)) * 100
            f.write(f"Red {red}: {cantidad} IIEE ({porcentaje:.1f}%)\n")
    
    print(f"\nArchivo de estadisticas creado: {stats_file}")
    print(f"\nListo para usar en Kepler.gl!")
    
    return df_final

if __name__ == "__main__":
    crear_archivo_para_kepler()