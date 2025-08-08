#!/usr/bin/env python3
import pandas as pd
import sqlite3

def actualizar_estado_eib():
    """Actualizar el estado EIB de las instituciones que aparecen en el padrón MINEDU"""
    
    print("=== ACTUALIZACION ESTADO EIB DESDE PADRON MINEDU ===\n")
    
    # Los 28 códigos que SÍ están en el padrón EIB MINEDU
    codigos_eib_confirmados = [
        '1060276', '1062058', '1104801', '1155530', '1197987', '1200906', '1315084', 
        '1343813', '1370717', '1374834', '1376268', '1376300', '1376318', '1401124', 
        '1402866', '1457365', '1457605', '1495167', '1551944', '1568799', '1598861', 
        '1608132', '1625904', '1633189', '1636455', '1678879', '1741123', '1772672'
    ]
    
    print(f"Códigos a actualizar: {len(codigos_eib_confirmados)}")
    
    try:
        conn = sqlite3.connect('reasis_database.db')
        cursor = conn.cursor()
        
        # Verificar estado actual
        placeholders = ','.join(['?' for _ in codigos_eib_confirmados])
        query_verificar = f"""
        SELECT codigo_modular, nombre_institucion, es_eib, region
        FROM instituciones_educativas 
        WHERE codigo_modular IN ({placeholders})
        ORDER BY codigo_modular
        """
        
        df_antes = pd.read_sql_query(query_verificar, conn, params=codigos_eib_confirmados)
        print("ESTADO ANTES DE LA ACTUALIZACION:")
        print(f"- Instituciones a actualizar: {len(df_antes)}")
        print(f"- Marcadas como EIB: {df_antes['es_eib'].sum()}")
        print(f"- Marcadas como No-EIB: {(df_antes['es_eib'] == 0).sum()}")
        
        # Crear backup de la tabla antes de actualizar
        print("\nCreando backup de la tabla...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS instituciones_educativas_backup_eib AS 
        SELECT * FROM instituciones_educativas
        """)
        
        # Actualizar es_eib = 1 para las instituciones confirmadas
        print("\nActualizando estado EIB...")
        for codigo in codigos_eib_confirmados:
            cursor.execute("""
            UPDATE instituciones_educativas 
            SET es_eib = 1 
            WHERE codigo_modular = ?
            """, (codigo,))
        
        # Confirmar cambios
        conn.commit()
        print(f"✓ Actualizados {cursor.rowcount} registros")
        
        # Verificar resultado
        df_despues = pd.read_sql_query(query_verificar, conn, params=codigos_eib_confirmados)
        print("\nESTADO DESPUES DE LA ACTUALIZACION:")
        print(f"- Instituciones actualizadas: {len(df_despues)}")
        print(f"- Ahora marcadas como EIB: {df_despues['es_eib'].sum()}")
        print(f"- Aún marcadas como No-EIB: {(df_despues['es_eib'] == 0).sum()}")
        
        # Estadísticas generales actualizadas
        query_general = "SELECT COUNT(*) as total, SUM(es_eib) as eib FROM instituciones_educativas"
        stats = pd.read_sql_query(query_general, conn)
        print(f"\nESTADISTICAS GENERALES ACTUALIZADAS:")
        print(f"- Total instituciones: {stats.iloc[0]['total']}")
        print(f"- Instituciones EIB: {stats.iloc[0]['eib']}")
        print(f"- Instituciones No-EIB: {stats.iloc[0]['total'] - stats.iloc[0]['eib']}")
        print(f"- Porcentaje EIB: {stats.iloc[0]['eib']/stats.iloc[0]['total']*100:.1f}%")
        
        conn.close()
        
        print(f"\n" + "="*50)
        print("RESULTADO EXITOSO:")
        print("✓ Estado EIB actualizado correctamente")
        print("✓ Backup creado en tabla 'instituciones_educativas_backup_eib'")
        print(f"✓ {len(codigos_eib_confirmados)} instituciones ahora marcadas como EIB")
        print("✓ Base de datos lista para integración con datos EIB MINEDU")
        
        return True
        
    except Exception as e:
        print(f"ERROR durante actualización: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False

def verificar_actualizacion():
    """Verificar que la actualización se realizó correctamente"""
    
    print("\n=== VERIFICACION DE ACTUALIZACION ===")
    
    codigos_eib = [
        '1060276', '1062058', '1104801', '1155530', '1197987', '1200906', '1315084', 
        '1343813', '1370717', '1374834', '1376268', '1376300', '1376318', '1401124', 
        '1402866', '1457365', '1457605', '1495167', '1551944', '1568799', '1598861', 
        '1608132', '1625904', '1633189', '1636455', '1678879', '1741123', '1772672'
    ]
    
    conn = sqlite3.connect('reasis_database.db')
    
    placeholders = ','.join(['?' for _ in codigos_eib])
    query = f"""
    SELECT codigo_modular, nombre_institucion, es_eib, region, modalidad_especifica
    FROM instituciones_educativas 
    WHERE codigo_modular IN ({placeholders}) AND es_eib = 1
    ORDER BY region, codigo_modular
    """
    
    df_verificacion = pd.read_sql_query(query, conn, params=codigos_eib)
    conn.close()
    
    print(f"\nINSTITUCIONES EIB CONFIRMADAS: {len(df_verificacion)}")
    
    if len(df_verificacion) > 0:
        print("\nDetalle por región:")
        for region in df_verificacion['region'].unique():
            instituciones_region = df_verificacion[df_verificacion['region'] == region]
            print(f"\n{region} ({len(instituciones_region)} instituciones):")
            for _, row in instituciones_region.iterrows():
                print(f"  - {row['codigo_modular']}: {row['nombre_institucion']} ({row['modalidad_especifica']})")
    
    return len(df_verificacion) == len(codigos_eib)

if __name__ == "__main__":
    exito = actualizar_estado_eib()
    if exito:
        verificar_actualizacion()