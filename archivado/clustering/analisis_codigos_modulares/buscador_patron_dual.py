#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Buscador con Patrón Dual - Separación Código + Nombre
Explota el patrón "número + espacio + nombre" en nombre_ie_original
"""

import json
import re
from dbfread import DBF
from fuzzywuzzy import fuzz

def separar_codigo_nombre(texto):
    """Separa código numérico y nombre del texto combinado"""
    if not texto:
        return None, texto
    
    texto = str(texto).strip()
    
    # Patrón: número al inicio + espacio + resto
    match = re.match(r'^(\d+)\s+(.+)$', texto)
    if match:
        return match.group(1), match.group(2)
    
    # Si no hay patrón, devolver None para código y texto completo como nombre
    return None, texto

def normalizar_texto(texto):
    """Normaliza texto para comparación"""
    if not texto:
        return ""
    
    texto = str(texto).upper().strip()
    # Remover caracteres especiales y normalizar espacios
    texto = re.sub(r'[^\w\s]', ' ', texto)
    texto = re.sub(r'\s+', ' ', texto).strip()
    return texto

def buscar_con_patron_dual():
    """Búsqueda mejorada usando patrón dual código + nombre"""
    
    print("=== BUSCADOR CON PATRON DUAL ===")
    print()
    
    # 1. Cargar instituciones pendientes
    with open('instituciones_pendientes_codigo_modular.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    instituciones = data['instituciones_sin_codigo_modular']
    print(f"Instituciones a procesar: {len(instituciones)}")
    
    # 2. Cargar padrón nacional
    print("Cargando padrón nacional...")
    padron_file = r'C:\Users\lucas\Proyectos\Reasis\data\bases_de_datos\Padron_web_20250731\Padron_web.dbf'
    table = DBF(padron_file, encoding='latin-1')
    
    # 3. Crear índices especializados
    print("Creando índices especializados...")
    
    indice_codlocal = {}  # código local -> info
    indice_nombres = {}   # nombre normalizado -> info
    indice_codmod = {}    # código modular -> info
    
    contador = 0
    for record in table:
        contador += 1
        if contador % 50000 == 0:
            print(f"  Procesando registro {contador}...")
        
        nombre_ie = record['CEN_EDU']
        cod_modular = record['COD_MOD']
        codlocal = record['CODLOCAL']
        
        if not (nombre_ie and cod_modular):
            continue
            
        info = {
            'cod_modular': cod_modular.strip(),
            'codlocal': codlocal.strip() if codlocal else '',
            'nombre_original': nombre_ie.strip(),
            'departamento': record['D_DPTO'].strip() if record['D_DPTO'] else '',
            'distrito': record['D_DIST'].strip() if record['D_DIST'] else '',
            'estado': record['D_ESTADO'].strip() if record['D_ESTADO'] else ''
        }
        
        # Indexar por código local
        if codlocal:
            indice_codlocal[codlocal.strip()] = info
        
        # Indexar por código modular
        indice_codmod[cod_modular.strip()] = info
        
        # Indexar por nombre normalizado
        nombre_norm = normalizar_texto(nombre_ie)
        if nombre_norm:
            indice_nombres[nombre_norm] = info
            
        # También indexar variaciones del nombre (sin números)
        _, solo_nombre = separar_codigo_nombre(nombre_ie)
        if solo_nombre:
            nombre_solo_norm = normalizar_texto(solo_nombre)
            if nombre_solo_norm and nombre_solo_norm != nombre_norm:
                indice_nombres[nombre_solo_norm] = info
    
    print(f"Índices creados:")
    print(f"  - Códigos locales: {len(indice_codlocal)}")
    print(f"  - Nombres: {len(indice_nombres)}")
    print(f"  - Códigos modulares: {len(indice_codmod)}")
    print()
    
    # 4. Ejecutar búsqueda con patrón dual
    print("EJECUTANDO BUSQUEDA CON PATRON DUAL:")
    print()
    
    resultados = []
    
    for i, inst in enumerate(instituciones, 1):
        nombre_original = inst['nombre_ie_original']
        codigo_local = inst['codigo_local']
        
        print(f"{i:2d}. {nombre_original}")
        
        # Separar código y nombre del nombre_ie_original
        codigo_extraido, nombre_extraido = separar_codigo_nombre(nombre_original)
        
        if codigo_extraido:
            print(f"    Patrón detectado -> Código: '{codigo_extraido}', Nombre: '{nombre_extraido}'")
        else:
            print(f"    Sin patrón -> Nombre completo: '{nombre_extraido}'")
        
        encontrado = False
        match_info = None
        tipo_match = None
        
        # ESTRATEGIA 1: Buscar por código extraído como código modular
        if codigo_extraido and codigo_extraido in indice_codmod:
            match_info = indice_codmod[codigo_extraido]
            tipo_match = 'CODIGO_MODULAR_DIRECTO'
            encontrado = True
            print(f"    [COD_MOD_DIRECTO] {match_info['cod_modular']} - {match_info['departamento']}")
        
        # ESTRATEGIA 2: Buscar por código extraído como código local  
        if not encontrado and codigo_extraido and codigo_extraido in indice_codlocal:
            match_info = indice_codlocal[codigo_extraido]
            tipo_match = 'CODIGO_LOCAL_EXTRAIDO'
            encontrado = True
            print(f"    [COD_LOCAL_EXT] {match_info['cod_modular']} - {match_info['departamento']}")
        
        # ESTRATEGIA 3: Buscar por nombre extraído (exacto)
        if not encontrado and nombre_extraido:
            nombre_norm = normalizar_texto(nombre_extraido)
            if nombre_norm in indice_nombres:
                match_info = indice_nombres[nombre_norm]
                tipo_match = 'NOMBRE_EXTRAIDO_EXACTO'
                encontrado = True
                print(f"    [NOMBRE_EXT_EXACTO] {match_info['cod_modular']} - {match_info['departamento']}")
        
        # ESTRATEGIA 4: Buscar por código local original
        if not encontrado and codigo_local and str(codigo_local).strip() in indice_codlocal:
            match_info = indice_codlocal[str(codigo_local).strip()]
            tipo_match = 'CODIGO_LOCAL_ORIGINAL'
            encontrado = True
            print(f"    [COD_LOCAL_ORIG] {match_info['cod_modular']} - {match_info['departamento']}")
        
        # ESTRATEGIA 5: Búsqueda fuzzy en nombres (solo si no se encontró nada)
        if not encontrado and nombre_extraido:
            nombre_buscar = normalizar_texto(nombre_extraido)
            mejor_score = 0
            mejor_match = None
            
            # Buscar entre una muestra de nombres (optimización)
            for nombre_idx, info in list(indice_nombres.items())[:2000]:
                score = fuzz.ratio(nombre_buscar, nombre_idx)
                if score > mejor_score and score >= 90:
                    mejor_score = score
                    mejor_match = info
            
            if mejor_match:
                match_info = mejor_match
                tipo_match = f'FUZZY_NOMBRE_{mejor_score}'
                encontrado = True
                print(f"    [FUZZY_NOMBRE_{mejor_score}%] {match_info['cod_modular']} - {match_info['departamento']}")
        
        if not encontrado:
            print("    [NO ENCONTRADO]")
        
        # Guardar resultado
        resultado = {
            'id_original': inst['id_secuencial'],
            'nombre_original': nombre_original,
            'codigo_extraido': codigo_extraido,
            'nombre_extraido': nombre_extraido,
            'codigo_local_original': codigo_local,
            'encontrado': encontrado,
            'tipo_match': tipo_match,
            'info_encontrada': match_info
        }
        resultados.append(resultado)
        print()
    
    # 5. Procesar resultados
    encontrados = len([r for r in resultados if r['encontrado']])
    
    print("=== RESULTADOS BUSQUEDA PATRON DUAL ===")
    print(f"Total procesadas: {len(instituciones)}")
    print(f"Encontradas: {encontrados}")
    print(f"Porcentaje de éxito: {(encontrados/len(instituciones)*100):.1f}%")
    
    if encontrados > 0:
        print()
        print("TIPOS DE MATCHES ENCONTRADOS:")
        tipos = {}
        for r in resultados:
            if r['encontrado']:
                tipo = r['tipo_match']
                tipos[tipo] = tipos.get(tipo, 0) + 1
        
        for tipo, cantidad in tipos.items():
            print(f"  {tipo}: {cantidad}")
        
        print()
        print("CODIGOS MODULARES ENCONTRADOS:")
        for r in resultados:
            if r['encontrado']:
                info = r['info_encontrada']
                print(f"  {r['nombre_original'][:40]}... -> {info['cod_modular']} ({r['tipo_match']})")
    
    return resultados

if __name__ == "__main__":
    try:
        resultados = buscar_con_patron_dual()
        print("\\nBusqueda completada exitosamente")
    except Exception as e:
        print(f"\\nError: {e}")
        import traceback
        traceback.print_exc()