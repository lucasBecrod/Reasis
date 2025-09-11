#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Buscador Automático de Códigos Modulares Faltantes
Busca códigos modulares en el padrón nacional para completar registros académicos
"""

import json
import re
from dbfread import DBF
from fuzzywuzzy import fuzz

def normalizar_nombre(nombre):
    """Normaliza nombres para búsqueda"""
    if not nombre:
        return ""
    
    # Convertir a mayúsculas y limpiar
    nombre = str(nombre).upper().strip()
    
    # Remover caracteres especiales comunes
    nombre = re.sub(r'[^\w\s]', ' ', nombre)
    
    # Normalizar espacios
    nombre = re.sub(r'\s+', ' ', nombre).strip()
    
    return nombre

def crear_variaciones_nombre(nombre):
    """Crea variaciones del nombre para búsqueda"""
    variaciones = set()
    nombre_norm = normalizar_nombre(nombre)
    
    # Versión original normalizada
    variaciones.add(nombre_norm)
    
    # Sin números al inicio
    sin_numeros = re.sub(r'^\d+\s*', '', nombre_norm).strip()
    if sin_numeros and sin_numeros != nombre_norm:
        variaciones.add(sin_numeros)
    
    # Solo números al inicio (si existen)
    solo_numeros = re.match(r'^\d+', nombre_norm)
    if solo_numeros:
        variaciones.add(solo_numeros.group())
    
    return list(variaciones)

def buscar_en_padron():
    """Función principal de búsqueda"""
    print("=== BUSCADOR AUTOMATICO DE CODIGOS MODULARES ===\n")
    
    # 1. Cargar instituciones faltantes
    print("1. Cargando instituciones sin código modular...")
    with open('instituciones_sin_codigo_modular.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    instituciones_faltantes = data['instituciones_sin_codigo_modular']
    print(f"   Instituciones a buscar: {len(instituciones_faltantes)}")
    
    # 2. Cargar padrón nacional
    print("\n2. Cargando padrón nacional...")
    padron_file = r'C:\Users\lucas\Proyectos\Reasis\data\bases_de_datos\Padron_web_20250731\Padron_web.dbf'
    table = DBF(padron_file, encoding='latin-1')
    print(f"   Total instituciones en padrón: {len(table)}")
    
    # 3. Crear índice de búsqueda optimizado
    print("\n3. Creando índice de búsqueda...")
    indice_nombres = {}
    indice_codigos = {}
    
    contador = 0
    for record in table:
        contador += 1
        if contador % 50000 == 0:
            print(f"   Procesando registro {contador}...")
        
        nombre_ie = record['CEN_EDU']
        cod_modular = record['COD_MOD']
        codlocal = record['CODLOCAL']
        
        if nombre_ie and cod_modular:
            info_ie = {
                'cod_modular': cod_modular.strip(),
                'codlocal': codlocal.strip() if codlocal else '',
                'nombre_original': nombre_ie.strip(),
                'departamento': record['D_DPTO'].strip() if record['D_DPTO'] else '',
                'distrito': record['D_DIST'].strip() if record['D_DIST'] else '',
                'direccion': record['DIR_CEN'].strip() if record['DIR_CEN'] else '',
                'estado': record['D_ESTADO'].strip() if record['D_ESTADO'] else ''
            }
            
            # Indexar por variaciones de nombre
            for variacion in crear_variaciones_nombre(nombre_ie):
                if variacion:
                    indice_nombres[variacion] = info_ie
            
            # Indexar por código local
            if codlocal and codlocal.strip():
                indice_codigos[codlocal.strip()] = info_ie
    
    print(f"   Índice creado: {len(indice_nombres)} nombres, {len(indice_codigos)} códigos")
    
    # 4. Buscar cada institución
    print("\n4. Ejecutando búsquedas...\n")
    resultados = []
    
    for i, inst in enumerate(instituciones_faltantes, 1):
        print(f"{i:2d}. {inst['nombre_ie_original'][:50]}...")
        
        encontrado = False
        match_info = None
        tipo_match = None
        
        # ESTRATEGIA 1: Búsqueda por nombre exacto
        nombre_buscar = normalizar_nombre(inst['nombre_ie_original'])
        if nombre_buscar in indice_nombres:
            match_info = indice_nombres[nombre_buscar]
            tipo_match = 'NOMBRE_EXACTO'
            encontrado = True
            print(f"    [EXACTO] {match_info['cod_modular']} - {match_info['departamento']}")
        
        # ESTRATEGIA 2: Búsqueda por código local
        if not encontrado and inst['codigo_local']:
            codigo_local_norm = str(inst['codigo_local']).strip()
            if codigo_local_norm in indice_codigos:
                match_info = indice_codigos[codigo_local_norm]
                tipo_match = 'CODIGO_LOCAL'
                encontrado = True
                print(f"    [COD_LOCAL] {match_info['cod_modular']} - {match_info['departamento']}")
        
        # ESTRATEGIA 3: Búsqueda fuzzy (solo para casos críticos)
        if not encontrado:
            mejor_score = 0
            mejor_match = None
            
            # Buscar entre las primeras 1000 entradas del índice (optimización)
            for nombre_idx, info in list(indice_nombres.items())[:1000]:
                score = fuzz.ratio(nombre_buscar, nombre_idx)
                if score > mejor_score and score >= 85:
                    mejor_score = score
                    mejor_match = info
            
            if mejor_match:
                match_info = mejor_match
                tipo_match = f'FUZZY_{mejor_score}'
                encontrado = True
                print(f"    [FUZZY_{mejor_score}%] {match_info['cod_modular']} - {match_info['departamento']}")
        
        if not encontrado:
            print("    [NO ENCONTRADO]")
        
        # Guardar resultado
        resultado = {
            'id_original': inst['id_secuencial'],
            'nombre_original': inst['nombre_ie_original'],
            'codigo_local_original': inst['codigo_local'],
            'encontrado': encontrado,
            'tipo_match': tipo_match,
            'cod_modular_encontrado': match_info['cod_modular'] if match_info else None,
            'codlocal_encontrado': match_info['codlocal'] if match_info else None,
            'departamento_encontrado': match_info['departamento'] if match_info else None,
            'distrito_encontrado': match_info['distrito'] if match_info else None,
            'info_completa': match_info
        }
        resultados.append(resultado)
    
    # 5. Actualizar JSON original
    print(f"\n5. Actualizando archivo JSON...")
    encontrados = 0
    for i, resultado in enumerate(resultados):
        if resultado['encontrado']:
            data['instituciones_sin_codigo_modular'][i]['codigo_modular_propuesto'] = resultado['cod_modular_encontrado']
            data['instituciones_sin_codigo_modular'][i]['estado_investigacion'] = 'ENCONTRADO'
            data['instituciones_sin_codigo_modular'][i]['notas_investigacion'] = f"Match tipo: {resultado['tipo_match']}"
            encontrados += 1
        else:
            data['instituciones_sin_codigo_modular'][i]['estado_investigacion'] = 'NO_ENCONTRADO'
    
    # Guardar JSON actualizado
    with open('instituciones_sin_codigo_modular_actualizado.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    # 6. Generar reporte de resultados
    print(f"\n=== REPORTE FINAL ===")
    print(f"Total instituciones buscadas: {len(instituciones_faltantes)}")
    print(f"Códigos modulares encontrados: {encontrados}")
    print(f"Porcentaje de éxito: {(encontrados/len(instituciones_faltantes)*100):.1f}%")
    print(f"\nArchivo actualizado: instituciones_sin_codigo_modular_actualizado.json")
    
    # Mostrar resumen por tipo de match
    tipos_match = {}
    for r in resultados:
        if r['encontrado']:
            tipo = r['tipo_match']
            tipos_match[tipo] = tipos_match.get(tipo, 0) + 1
    
    if tipos_match:
        print(f"\nTipos de matches encontrados:")
        for tipo, cantidad in tipos_match.items():
            print(f"  {tipo}: {cantidad}")
    
    return resultados

if __name__ == "__main__":
    try:
        resultados = buscar_en_padron()
        print("\n✅ Búsqueda completada exitosamente")
    except Exception as e:
        print(f"\n❌ Error en la búsqueda: {e}")
        import traceback
        traceback.print_exc()