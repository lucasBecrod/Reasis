#!/usr/bin/env python3
"""
Script para revisar y corregir todos los campos BLOB en la tabla instituciones_educativas
"""

import sqlite3
import struct

def bytes_to_int(blob_data):
    """Convierte bytes a entero usando little-endian"""
    if blob_data and len(blob_data) >= 4:
        return struct.unpack('<i', blob_data[:4])[0]
    elif blob_data and len(blob_data) >= 2:
        return struct.unpack('<h', blob_data[:2])[0]
    elif blob_data and len(blob_data) >= 1:
        return blob_data[0]
    return 0

def revisar_todos_los_blobs():
    """Revisa toda la tabla en busca de campos BLOB problemáticos"""
    
    print("=== REVISIÓN COMPLETA DE CAMPOS BLOB ===")
    
    conn = sqlite3.connect('reasis_database.db')
    cursor = conn.cursor()
    
    # Campos numéricos que deben ser INT o REAL
    campos_numericos = [
        'total_alumnos', 'alumnos_hombres', 'alumnos_mujeres',
        'total_docentes', 'docentes_hombres', 'docentes_mujeres', 'docentes_total',
        'total_secciones', 'directivos_hombres', 'directivos_mujeres', 'directivos_total',
        'latitud', 'longitud', 'altitud', 'es_rural', 'es_eib',
        'multiplicidad1', 'multiplicidad2', 'id_red_fya'
    ]
    
    # Buscar todos los registros
    cursor.execute("SELECT COUNT(*) FROM instituciones_educativas")
    total_registros = cursor.fetchone()[0]
    print(f"Revisando {total_registros} registros...")
    
    # Revisar cada registro
    registros_con_blobs = []
    
    campos_str = ', '.join(campos_numericos)
    query = f"SELECT rowid, codigo_modular, {campos_str} FROM instituciones_educativas"
    cursor.execute(query)
    
    while True:
        batch = cursor.fetchmany(50)  # Procesar en lotes de 50
        if not batch:
            break
        
        for row in batch:
            rowid = row[0]
            codigo = row[1]
            tiene_blobs = False
            campos_blob = []
            
            for i, campo in enumerate(campos_numericos):
                valor = row[i + 2]  # +2 porque row[0]=rowid, row[1]=codigo
                
                if isinstance(valor, bytes):
                    tiene_blobs = True
                    campos_blob.append((campo, valor))
            
            if tiene_blobs:
                registros_con_blobs.append({
                    'rowid': rowid,
                    'codigo': codigo,
                    'campos_blob': campos_blob
                })
    
    print(f"\nEncontrados {len(registros_con_blobs)} registros con campos BLOB")
    
    if len(registros_con_blobs) == 0:
        print("✓ No hay más campos BLOB problemáticos")
        conn.close()
        return
    
    # Mostrar muestra de registros problemáticos
    print("\n=== MUESTRA DE REGISTROS CON BLOBS ===")
    for i, reg in enumerate(registros_con_blobs[:10]):  # Mostrar primeros 10
        print(f"Fila {reg['rowid']} ({reg['codigo']}): {len(reg['campos_blob'])} campos BLOB")
        for campo, valor_blob in reg['campos_blob'][:3]:  # Mostrar primeros 3 campos
            valor_convertido = bytes_to_int(valor_blob)
            print(f"  {campo}: bytes -> {valor_convertido}")
        if len(reg['campos_blob']) > 3:
            print(f"  ... y {len(reg['campos_blob'])-3} campos más")
    
    if len(registros_con_blobs) > 10:
        print(f"... y {len(registros_con_blobs)-10} registros más")
    
    # Preguntar si proceder con la corrección
    respuesta = input(f"\n¿Proceder a corregir {len(registros_con_blobs)} registros? (s/n): ")
    
    if respuesta.lower() not in ['s', 'si', 'y', 'yes']:
        print("Corrección cancelada")
        conn.close()
        return
    
    # Proceder con la corrección
    print("\n=== CORRIGIENDO TODOS LOS CAMPOS BLOB ===")
    
    registros_corregidos = 0
    campos_corregidos = 0
    
    for reg in registros_con_blobs:
        rowid = reg['rowid']
        codigo = reg['codigo']
        
        # Preparar actualizaciones
        sets = []
        params = []
        
        for campo, valor_blob in reg['campos_blob']:
            valor_convertido = bytes_to_int(valor_blob)
            
            # Validaciones específicas por campo
            if campo in ['es_rural', 'es_eib'] and valor_convertido not in [0, 1]:
                valor_convertido = 1 if valor_convertido > 0 else 0
            elif campo in ['latitud', 'longitud'] and abs(valor_convertido) > 180:
                # Parece ser coordenada en formato incorrecto, dividir por factor
                valor_convertido = valor_convertido / 1000000.0 if valor_convertido != 0 else None
            
            if valor_convertido is not None:
                sets.append(f"{campo} = ?")
                params.append(valor_convertido)
                campos_corregidos += 1
        
        if sets:
            params.append(codigo)
            update_sql = f"UPDATE instituciones_educativas SET {', '.join(sets)} WHERE codigo_modular = ?"
            
            try:
                cursor.execute(update_sql, params)
                registros_corregidos += 1
                
                if registros_corregidos % 20 == 0:
                    print(f"  Corregidos: {registros_corregidos}/{len(registros_con_blobs)}")
                    
            except Exception as e:
                print(f"  ERROR en {codigo}: {e}")
    
    conn.commit()
    
    print(f"\n=== RESUMEN FINAL ===")
    print(f"Registros procesados: {registros_corregidos}/{len(registros_con_blobs)}")
    print(f"Campos corregidos: {campos_corregidos}")
    
    # Verificación final
    print("\n=== VERIFICACIÓN FINAL ===")
    cursor.execute(query)
    blobs_restantes = 0
    
    while True:
        batch = cursor.fetchmany(50)
        if not batch:
            break
        
        for row in batch:
            for i, campo in enumerate(campos_numericos):
                valor = row[i + 2]
                if isinstance(valor, bytes):
                    blobs_restantes += 1
                    break  # Solo contar una vez por registro
    
    if blobs_restantes == 0:
        print("✓ Todos los campos BLOB han sido corregidos exitosamente")
    else:
        print(f"⚠ Aún quedan {blobs_restantes} campos BLOB sin corregir")
    
    conn.close()

if __name__ == "__main__":
    revisar_todos_los_blobs()