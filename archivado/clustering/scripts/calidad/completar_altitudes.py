#!/usr/bin/env python3
"""
Script para completar las altitudes faltantes de las 9 instituciones usando API
"""

import sqlite3
import requests
import time
import math

def obtener_altitud_open_elevation(lat, lon):
    """Obtiene altitud usando Open-Elevation API"""
    try:
        url = f'https://api.open-elevation.com/api/v1/lookup?locations={lat},{lon}'
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if data['results'] and len(data['results']) > 0:
                return data['results'][0]['elevation']
    except Exception as e:
        print(f'    Error API: {e}')
    return None

def completar_altitudes_faltantes():
    """Completa las altitudes faltantes para las 9 instituciones"""
    
    print("=== COMPLETANDO ALTITUDES FALTANTES ===")
    
    codigos = ['0600692', '1768829', '0481093', '0488403', '0304642', '0428714', '3025715', '2533906', '1781897']
    
    conn = sqlite3.connect('reasis_database.db')
    cursor = conn.cursor()
    
    # Verificar estado actual
    codigos_str = ','.join([f"'{c}'" for c in codigos])
    query = f'''
        SELECT codigo_modular, latitud, longitud, altitud
        FROM instituciones_educativas 
        WHERE codigo_modular IN ({codigos_str})
        ORDER BY codigo_modular
    '''
    
    cursor.execute(query)
    registros = cursor.fetchall()
    
    print("Estado actual de altitudes:")
    instituciones_sin_altitud = []
    
    for codigo, lat, lon, alt in registros:
        # Verificar si altitud es None o NaN
        necesita_altitud = False
        if alt is None:
            necesita_altitud = True
        elif isinstance(alt, float) and (math.isnan(alt) or alt == 0):
            necesita_altitud = True
        
        if necesita_altitud:
            print(f"  {codigo}: Lat={lat}, Lon={lon}, Altitud=NULL (FALTA)")
            instituciones_sin_altitud.append({'codigo': codigo, 'lat': lat, 'lon': lon})
        else:
            print(f"  {codigo}: Lat={lat}, Lon={lon}, Altitud={alt}m (OK)")
    
    print(f"\nInstituciones sin altitud: {len(instituciones_sin_altitud)}")
    
    # Obtener altitudes para las instituciones faltantes
    if len(instituciones_sin_altitud) > 0:
        print("\n=== OBTENIENDO ALTITUDES FALTANTES ===")
        
        altitudes_nuevas = {}
        
        for i, inst in enumerate(instituciones_sin_altitud):
            codigo = inst['codigo']
            lat = inst['lat']
            lon = inst['lon']
            
            print(f"  {i+1}/{len(instituciones_sin_altitud)} - {codigo}: Lat={lat:.4f}, Lon={lon:.4f}", end=" -> ")
            
            altitud = obtener_altitud_open_elevation(lat, lon)
            
            if altitud is not None:
                altitudes_nuevas[codigo] = altitud
                print(f"{altitud}m")
                
                # Actualizar en base de datos
                cursor.execute('''
                    UPDATE instituciones_educativas 
                    SET altitud = ?
                    WHERE codigo_modular = ?
                ''', (altitud, codigo))
            else:
                print("Sin altitud (API no responde)")
            
            # Pausa para no sobrecargar la API
            if i < len(instituciones_sin_altitud) - 1:
                time.sleep(2)
        
        conn.commit()
        
        print(f"\n=== RESUMEN DE NUEVAS ALTITUDES ===")
        print(f"Altitudes obtenidas en esta ejecución: {len(altitudes_nuevas)}")
        
        if altitudes_nuevas:
            print("Nuevas altitudes:")
            for codigo, alt in altitudes_nuevas.items():
                print(f"  {codigo}: {alt}m")
    else:
        print("\n✓ Todas las instituciones ya tienen altitud")
    
    # Verificación final
    print("\n=== VERIFICACION FINAL ===")
    cursor.execute(query)
    registros_final = cursor.fetchall()
    sin_altitud_final = 0
    
    print("Estado final:")
    for codigo, lat, lon, alt in registros_final:
        if alt is None or (isinstance(alt, float) and math.isnan(alt)):
            print(f"  {codigo}: SIN ALTITUD")
            sin_altitud_final += 1
        else:
            print(f"  {codigo}: {alt}m")
    
    print(f"\nResumen final: {sin_altitud_final}/9 instituciones sin altitud")
    
    if sin_altitud_final == 0:
        print("🎉 ¡Todas las instituciones ahora tienen altitud!")
    
    conn.close()
    return sin_altitud_final == 0

if __name__ == "__main__":
    completar_altitudes_faltantes()