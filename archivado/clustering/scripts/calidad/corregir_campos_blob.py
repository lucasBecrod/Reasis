#!/usr/bin/env python3
"""
Script para corregir campos BLOB y convertirlos a enteros
"""

import sqlite3
import struct

def bytes_to_int(blob_data):
    """Convierte bytes a entero usando little-endian"""
    if blob_data and len(blob_data) >= 4:
        # Tomar los primeros 4 bytes y convertir a int32 little-endian
        return struct.unpack('<i', blob_data[:4])[0]
    return 0

def corregir_campos_blob():
    """Corrige los campos BLOB en las 9 instituciones problemáticas"""
    
    print("=== CORRIGIENDO CAMPOS BLOB A ENTEROS ===")
    
    codigos = ['0600692', '1768829', '0481093', '0488403', '0304642', '0428714', '3025715', '2533906', '1781897']
    
    conn = sqlite3.connect('reasis_database.db')
    cursor = conn.cursor()
    
    # Campos numéricos que pueden tener problemas BLOB
    campos_numericos = [
        'total_alumnos', 'alumnos_hombres', 'alumnos_mujeres',
        'total_docentes', 'docentes_hombres', 'docentes_mujeres', 'docentes_total',
        'total_secciones', 'directivos_hombres', 'directivos_mujeres', 'directivos_total'
    ]
    
    for codigo in codigos:
        print(f"\n--- Corrigiendo {codigo} ---")
        
        # Obtener los valores actuales
        campos_str = ', '.join(campos_numericos)
        query = f'SELECT rowid, {campos_str} FROM instituciones_educativas WHERE codigo_modular = ?'
        cursor.execute(query, (codigo,))
        row = cursor.fetchone()
        
        if not row:
            print(f"  No encontrado: {codigo}")
            continue
        
        rowid = row[0]
        valores_corregidos = {}
        
        for i, campo in enumerate(campos_numericos):
            valor_actual = row[i+1]  # +1 porque row[0] es rowid
            
            if isinstance(valor_actual, bytes):
                valor_convertido = bytes_to_int(valor_actual)
                valores_corregidos[campo] = valor_convertido
                print(f"  {campo}: bytes -> {valor_convertido}")
            elif isinstance(valor_actual, int):
                print(f"  {campo}: {valor_actual} (ya correcto)")
            elif valor_actual is None:
                valores_corregidos[campo] = None
                print(f"  {campo}: NULL (mantener)")
            else:
                try:
                    valores_corregidos[campo] = int(valor_actual)
                    print(f"  {campo}: {valor_actual} -> {valores_corregidos[campo]}")
                except:
                    valores_corregidos[campo] = 0
                    print(f"  {campo}: {valor_actual} -> 0 (por defecto)")
        
        # Actualizar solo los campos que necesitan corrección
        if valores_corregidos:
            sets = []
            params = []
            
            for campo, valor in valores_corregidos.items():
                if valor is not None:
                    sets.append(f'{campo} = ?')
                    params.append(valor)
                else:
                    sets.append(f'{campo} = NULL')
            
            if sets:
                params.append(codigo)  # Para el WHERE
                update_sql = f'UPDATE instituciones_educativas SET {", ".join(sets)} WHERE codigo_modular = ?'
                
                try:
                    cursor.execute(update_sql, params)
                    print(f"  [OK] Corregidos {len(valores_corregidos)} campos")
                except Exception as e:
                    print(f"  [ERROR] {e}")
    
    conn.commit()
    
    # Verificar correcciones
    print("\n=== VERIFICANDO CORRECCIONES ===")
    
    for codigo in codigos:
        cursor.execute('''
            SELECT codigo_modular, total_alumnos, total_docentes, total_secciones
            FROM instituciones_educativas 
            WHERE codigo_modular = ?
        ''', (codigo,))
        
        row = cursor.fetchone()
        if row:
            codigo, alumnos, docentes, secciones = row
            print(f"{codigo}: Alumnos={alumnos} ({type(alumnos).__name__}), " +
                  f"Docentes={docentes} ({type(docentes).__name__}), " +
                  f"Secciones={secciones} ({type(secciones).__name__})")
        else:
            print(f"{codigo}: No encontrado")
    
    conn.close()
    
    return True

if __name__ == "__main__":
    corregir_campos_blob()