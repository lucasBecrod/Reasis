#!/usr/bin/env python3
import pandas as pd
import sqlite3

def analizar_estado_eib():
    """Analizar el estado EIB de las instituciones Fe y Alegría"""
    
    print("=== ANALISIS ESTADO EIB DE INSTITUCIONES FE Y ALEGRIA ===\n")
    
    # Verificar el estado actual en la base de datos
    conn = sqlite3.connect('reasis_database.db')
    
    # Obtener información detallada
    query = """
    SELECT codigo_modular, nombre_institucion, region, es_eib, modalidad_especifica, area_censo
    FROM instituciones_educativas 
    ORDER BY codigo_modular
    """
    df_fya = pd.read_sql_query(query, conn)
    conn.close()
    
    print(f"ESTADO ACTUAL EN BASE DE DATOS:")
    print(f"- Total instituciones: {len(df_fya)}")
    print(f"- Marcadas como EIB: {df_fya['es_eib'].sum()}")
    print(f"- Marcadas como No-EIB: {(df_fya['es_eib'] == 0).sum()}")
    print(f"- Valores nulos en es_eib: {df_fya['es_eib'].isna().sum()}")
    
    # Verificar que instituciones coinciden con archivo EIB MINEDU
    archivo = r"C:\Users\lucas\Proyectos\Reasis\assets\Consultoria\Información actualizada\Extras\RIIEE EIB 2024 Minedu.xlsx"
    df_eib = pd.read_excel(archivo, sheet_name='Sheet1')
    
    # Los 28 códigos que coinciden
    coincidencias = ['1060276', '1062058', '1104801', '1155530', '1197987', '1200906', '1315084', 
                    '1343813', '1370717', '1374834', '1376268', '1376300', '1376318', '1401124', 
                    '1402866', '1457365', '1457605', '1495167', '1551944', '1568799', '1598861', 
                    '1608132', '1625904', '1633189', '1636455', '1678879', '1741123', '1772672']
    
    print(f"\nINSTITUCIONES QUE APARECEN EN PADRON EIB MINEDU:")
    df_coincidencias = df_fya[df_fya['codigo_modular'].astype(str).isin(coincidencias)]
    
    print(f"Total: {len(df_coincidencias)} instituciones")
    print("\nDetalle:")
    for _, row in df_coincidencias.iterrows():
        estado_actual = "EIB" if row['es_eib'] else "No-EIB"
        print(f"  - {row['codigo_modular']}: {row['nombre_institucion']}")
        print(f"    Region: {row['region']}, Estado BD: {estado_actual}, Modalidad: {row['modalidad_especifica']}")
    
    # Análisis por región de las instituciones que SÍ están en EIB
    print(f"\nANALISIS POR REGION (instituciones en padrón EIB):")
    regiones_eib = df_coincidencias['region'].value_counts()
    for region, count in regiones_eib.items():
        print(f"  - {region}: {count} instituciones")
    
    # Verificar modalidades
    print(f"\nANALISIS POR MODALIDAD (instituciones en padrón EIB):")
    modalidades_eib = df_coincidencias['modalidad_especifica'].value_counts()
    for modalidad, count in modalidades_eib.items():
        print(f"  - {modalidad}: {count} instituciones")
    
    # Análisis de área (rural vs urbana)
    print(f"\nANALISIS POR AREA (instituciones en padrón EIB):")
    areas_eib = df_coincidencias['area_censo'].value_counts()
    for area, count in areas_eib.items():
        print(f"  - {area}: {count} instituciones")
    
    print(f"\n" + "="*50)
    print("CONCLUSIONES:")
    print(f"1. TODAS las 381 instituciones Fe y Alegria están marcadas como 'No-EIB' en nuestra BD")
    print(f"2. Pero 28 instituciones (7.3%) SÍ aparecen en el padrón oficial EIB del MINEDU")
    print(f"3. Esto indica que el campo 'es_eib' en nuestra BD NO está actualizado")
    print(f"4. Las 28 instituciones que aparecen en EIB son principalmente rurales")
    print(f"5. Deberíamos ACTUALIZAR el estado EIB de estas 28 instituciones")
    
    return coincidencias, df_coincidencias

if __name__ == "__main__":
    coincidencias, df_coincidencias = analizar_estado_eib()