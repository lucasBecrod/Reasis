# TEMPLATE DE REPLICACIÓN - PROYECTOS SIMILARES

## 🎯 INTRODUCCIÓN

Este template proporciona una guía paso a paso para replicar el proceso de identificación de códigos modulares faltantes en proyectos similares. Está basado en la metodología exitosa desarrollada para el proyecto Reasis (100% de éxito en vinculación).

---

## 📋 CHECKLIST PRE-PROYECTO

### ✅ Requisitos Técnicos
- [ ] Python 3.8+ instalado
- [ ] Dependencias instaladas: `dbfread`, `pandas`, `fuzzywuzzy`
- [ ] SQLite o base de datos compatible
- [ ] Acceso a padrón nacional actualizado (MINEDU)
- [ ] Espacio en disco: 500MB+ para padrón y procesamiento
- [ ] RAM disponible: 4GB+ recomendados

### ✅ Datos del Proyecto
- [ ] Tabla con registros académicos/educativos identificada
- [ ] Campo equivalente a `codigo_modular` identificado
- [ ] Campo con nombres de instituciones disponible
- [ ] Campo con códigos locales/identificadores alternativos
- [ ] Backup de base de datos creado

### ✅ Objetivos Definidos
- [ ] Porcentaje mínimo de vinculación deseado (recomendado: 95%+)
- [ ] Criterios de calidad establecidos
- [ ] Tiempo disponible para el proyecto definido

---

## 🔍 FASE 1: DIAGNÓSTICO INICIAL

### Paso 1.1: Análisis de Datos Faltantes
```sql
-- Adaptar esta consulta a tu estructura de datos
SELECT 
    COUNT(*) as total_registros,
    COUNT(CASE WHEN campo_codigo_modular IS NOT NULL THEN 1 END) as con_codigo,
    COUNT(CASE WHEN campo_codigo_modular IS NULL THEN 1 END) as sin_codigo,
    ROUND(
        COUNT(CASE WHEN campo_codigo_modular IS NOT NULL THEN 1 END) * 100.0 / COUNT(*), 
        2
    ) as porcentaje_vinculado
FROM tu_tabla_principal;
```

### Paso 1.2: Extracción de Instituciones Problemáticas
```sql
-- Identificar instituciones únicas sin código
SELECT DISTINCT 
    campo_codigo_local,
    campo_nombre_institucion, 
    campo_identificador_completo,
    COUNT(*) as registros_afectados
FROM tu_tabla_principal 
WHERE campo_codigo_modular IS NULL 
    AND campo_codigo_local IS NOT NULL 
GROUP BY campo_codigo_local, campo_nombre_institucion, campo_identificador_completo
ORDER BY registros_afectados DESC;
```

### Paso 1.3: Generación de JSON de Trabajo
```python
# Script: extraer_datos_faltantes.py
import sqlite3
import json
from datetime import datetime

def generar_json_trabajo(archivo_db, tabla, campos):
    """
    Genera JSON con instituciones sin código para investigación
    
    Args:
        archivo_db (str): Ruta a base de datos
        tabla (str): Nombre de la tabla principal
        campos (dict): Mapeo de campos locales a estándar
    """
    
    conn = sqlite3.connect(archivo_db)
    cursor = conn.cursor()
    
    query = f"""
    SELECT DISTINCT 
        {campos['codigo_local']}, 
        {campos['nombre_institucion']}, 
        {campos['identificador_completo']},
        COUNT(*) as total_registros,
        GROUP_CONCAT(DISTINCT {campos['region']}) as regiones,
        GROUP_CONCAT(DISTINCT {campos['nivel']}) as niveles,
        GROUP_CONCAT(DISTINCT {campos['año']}) as años
    FROM {tabla}
    WHERE {campos['codigo_modular']} IS NULL 
    GROUP BY {campos['codigo_local']}, {campos['nombre_institucion']}, {campos['identificador_completo']}
    ORDER BY total_registros DESC
    """
    
    cursor.execute(query)
    resultados = cursor.fetchall()
    
    # Crear estructura JSON
    data = {
        'metadata': {
            'fecha_extraccion': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'proyecto': 'NOMBRE_TU_PROYECTO',
            'tabla_origen': tabla,
            'total_instituciones_faltantes': len(resultados),
            'total_registros_afectados': sum([r[3] for r in resultados])
        },
        'instituciones_faltantes': []
    }
    
    for i, row in enumerate(resultados, 1):
        institucion = {
            'id_secuencial': i,
            'codigo_local': row[0],
            'nombre_institucion': row[1],
            'identificador_completo': row[2],
            'registros_afectados': row[3],
            'regiones': row[4].split(',') if row[4] else [],
            'niveles': row[5].split(',') if row[5] else [],
            'años': row[6].split(',') if row[6] else [],
            'estado_investigacion': 'PENDIENTE',
            'codigo_modular_propuesto': None,
            'notas': ''
        }
        data['instituciones_faltantes'].append(institucion)
    
    # Guardar JSON
    with open('instituciones_faltantes.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"JSON generado: {len(resultados)} instituciones a investigar")
    conn.close()
    return data

# Configuración específica del proyecto
campos_mapping = {
    'codigo_modular': 'tu_campo_codigo_modular',
    'codigo_local': 'tu_campo_codigo_local',
    'nombre_institucion': 'tu_campo_nombre',
    'identificador_completo': 'tu_campo_id_completo',
    'region': 'tu_campo_region',
    'nivel': 'tu_campo_nivel',
    'año': 'tu_campo_año'
}

# Ejecutar
data = generar_json_trabajo('tu_base_datos.db', 'tu_tabla', campos_mapping)
```

---

## 🗄️ FASE 2: CONFIGURACIÓN DEL PADRÓN NACIONAL

### Paso 2.1: Descarga del Padrón Actualizado
```bash
# 1. Acceder a portal MINEDU
# URL: http://escale.minedu.gob.pe/
# 2. Navegar a Padrones > Padrón de Instituciones Educativas
# 3. Descargar versión más reciente (formato DBF)
# 4. Extraer en carpeta del proyecto
```

### Paso 2.2: Configuración de Rutas
```python
# config.py
import os

# Configuración de rutas del proyecto
RUTAS = {
    'padron_nacional': r'C:\tu_proyecto\data\padron\Padron_web.dbf',
    'base_datos_principal': r'C:\tu_proyecto\tu_base_datos.db',
    'directorio_resultados': r'C:\tu_proyecto\resultados_codigos',
    'json_trabajo': r'C:\tu_proyecto\instituciones_faltantes.json'
}

# Verificar que los archivos existen
def verificar_configuracion():
    for nombre, ruta in RUTAS.items():
        if nombre.endswith('directorio'):
            os.makedirs(ruta, exist_ok=True)
        elif not os.path.exists(ruta):
            print(f"⚠️  ARCHIVO NO ENCONTRADO: {nombre} - {ruta}")
            return False
    
    print("✅ Configuración verificada correctamente")
    return True

if __name__ == "__main__":
    verificar_configuracion()
```

### Paso 2.3: Carga y Verificación del Padrón
```python
# cargar_padron.py
from dbfread import DBF
import config

def cargar_y_verificar_padron():
    """Carga el padrón nacional y verifica su integridad"""
    
    print("Cargando padrón nacional...")
    tabla = DBF(config.RUTAS['padron_nacional'], encoding='latin-1')
    
    # Verificaciones básicas
    print(f"✅ Registros totales: {len(tabla):,}")
    
    # Verificar campos clave
    campos_requeridos = ['COD_MOD', 'CEN_EDU', 'CODLOCAL', 'D_DPTO', 'D_ESTADO']
    for campo in campos_requeridos:
        if campo not in tabla.field_names:
            print(f"❌ Campo faltante: {campo}")
            return None
    
    print("✅ Estructura del padrón verificada")
    
    # Estadísticas rápidas
    activas = sum(1 for r in tabla if r.get('ESTADO') == '1')
    print(f"📊 Instituciones activas: {activas:,}")
    
    return tabla

if __name__ == "__main__":
    padron = cargar_y_verificar_padron()
```

---

## 🔍 FASE 3: IMPLEMENTACIÓN DE BÚSQUEDAS

### Paso 3.1: Búsqueda Automática Básica
```python
# buscador_automatico.py
import json
from dbfread import DBF
from fuzzywuzzy import fuzz
import config

def ejecutar_busqueda_automatica():
    """Implementa las estrategias básicas de búsqueda"""
    
    # Cargar datos
    with open(config.RUTAS['json_trabajo'], 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    tabla_padron = DBF(config.RUTAS['padron_nacional'], encoding='latin-1')
    
    # Crear índices de búsqueda
    print("Creando índices de búsqueda...")
    indices = {
        'por_nombre': {},
        'por_codigo_local': {},
        'por_codigo_modular': {}
    }
    
    contador = 0
    for record in tabla_padron:
        contador += 1
        if contador % 50000 == 0:
            print(f"  Indexados {contador:,} registros...")
        
        # Solo instituciones activas
        if record.get('ESTADO') != '1':
            continue
            
        cod_mod = record.get('COD_MOD', '').strip()
        nombre = record.get('CEN_EDU', '').upper().strip()
        cod_local = record.get('CODLOCAL', '').strip()
        
        info = {
            'codigo_modular': cod_mod,
            'codigo_local': cod_local,
            'nombre_original': record.get('CEN_EDU', ''),
            'departamento': record.get('D_DPTO', ''),
            'distrito': record.get('D_DIST', ''),
            'estado': record.get('D_ESTADO', '')
        }
        
        if nombre:
            indices['por_nombre'][nombre] = info
        if cod_local:
            indices['por_codigo_local'][cod_local] = info
        if cod_mod:
            indices['por_codigo_modular'][cod_mod] = info
    
    print(f"Índices creados: {len(indices['por_nombre']):,} nombres, {len(indices['por_codigo_local']):,} códigos")
    
    # Ejecutar búsquedas
    resultados = []
    for inst in data['instituciones_faltantes']:
        resultado = buscar_institucion_multiple(inst, indices)
        resultados.append(resultado)
        
        if resultado['encontrado']:
            print(f"✅ {inst['nombre_institucion'][:40]}... -> {resultado['codigo_encontrado']}")
        else:
            print(f"❌ {inst['nombre_institucion'][:40]}... -> No encontrado")
    
    return resultados

def buscar_institucion_multiple(institucion, indices):
    """Aplica múltiples estrategias de búsqueda para una institución"""
    
    nombre = institucion['nombre_institucion']
    codigo_local = institucion['codigo_local']
    
    # ESTRATEGIA 1: Nombre exacto
    nombre_norm = nombre.upper().strip()
    if nombre_norm in indices['por_nombre']:
        return {
            'encontrado': True,
            'metodo': 'NOMBRE_EXACTO',
            'codigo_encontrado': indices['por_nombre'][nombre_norm]['codigo_modular'],
            'info': indices['por_nombre'][nombre_norm]
        }
    
    # ESTRATEGIA 2: Código local
    if codigo_local and str(codigo_local) in indices['por_codigo_local']:
        return {
            'encontrado': True,
            'metodo': 'CODIGO_LOCAL',
            'codigo_encontrado': indices['por_codigo_local'][str(codigo_local)]['codigo_modular'],
            'info': indices['por_codigo_local'][str(codigo_local)]
        }
    
    # ESTRATEGIA 3: Fuzzy matching
    mejor_score = 0
    mejor_match = None
    
    for nombre_indice, info in list(indices['por_nombre'].items())[:2000]:  # Muestra para performance
        score = fuzz.ratio(nombre_norm, nombre_indice)
        if score > mejor_score and score >= 85:
            mejor_score = score
            mejor_match = info
    
    if mejor_match:
        return {
            'encontrado': True,
            'metodo': f'FUZZY_{mejor_score}',
            'codigo_encontrado': mejor_match['codigo_modular'],
            'info': mejor_match
        }
    
    return {
        'encontrado': False,
        'metodo': 'NO_ENCONTRADO',
        'codigo_encontrado': None,
        'info': None
    }

if __name__ == "__main__":
    resultados = ejecutar_busqueda_automatica()
    print(f"Búsqueda completada: {len([r for r in resultados if r['encontrado']])} instituciones encontradas")
```

### Paso 3.2: Implementar Algoritmo de Patrón Dual
```python
# buscador_patron_dual.py
import re
import json
from dbfread import DBF
import config

def separar_codigo_nombre(texto):
    """Separa código numérico y nombre del texto combinado"""
    if not texto:
        return None, texto
    
    texto = str(texto).strip()
    
    # Patrón: número al inicio + espacio + resto
    match = re.match(r'^(\d+)\s+(.+)$', texto)
    if match:
        return match.group(1), match.group(2)
    
    return None, texto

def buscar_con_patron_dual():
    """Implementa búsqueda con separación código + nombre"""
    
    # Cargar datos pendientes (después de búsqueda automática)
    with open('instituciones_restantes.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    tabla_padron = DBF(config.RUTAS['padron_nacional'], encoding='latin-1')
    
    # Crear índices especializados
    indices = {
        'por_codigo_modular': {},
        'por_nombre': {},
        'por_codigo_local': {}
    }
    
    for record in tabla_padron:
        if record.get('ESTADO') != '1':
            continue
            
        info = {
            'codigo_modular': record.get('COD_MOD', '').strip(),
            'nombre': record.get('CEN_EDU', ''),
            'departamento': record.get('D_DPTO', ''),
            'distrito': record.get('D_DIST', '')
        }
        
        # Indexar por diferentes campos
        if info['codigo_modular']:
            indices['por_codigo_modular'][info['codigo_modular']] = info
        
        if info['nombre']:
            nombre_norm = info['nombre'].upper().strip()
            indices['por_nombre'][nombre_norm] = info
            
            # También indexar sin números al inicio
            _, solo_nombre = separar_codigo_nombre(info['nombre'])
            if solo_nombre:
                nombre_solo_norm = solo_nombre.upper().strip()
                indices['por_nombre'][nombre_solo_norm] = info
        
        cod_local = record.get('CODLOCAL', '').strip()
        if cod_local:
            indices['por_codigo_local'][cod_local] = info
    
    # Procesar cada institución restante
    resultados = []
    for inst in data['instituciones_faltantes']:
        nombre_original = inst['nombre_institucion']
        
        # Aplicar separación de patrón dual
        codigo_extraido, nombre_extraido = separar_codigo_nombre(nombre_original)
        
        resultado = {
            'institucion_original': inst,
            'codigo_extraido': codigo_extraido,
            'nombre_extraido': nombre_extraido,
            'encontrado': False
        }
        
        # BÚSQUEDA 1: Código extraído como código modular directo
        if codigo_extraido and codigo_extraido in indices['por_codigo_modular']:
            resultado.update({
                'encontrado': True,
                'metodo': 'CODIGO_MODULAR_DIRECTO',
                'info_encontrada': indices['por_codigo_modular'][codigo_extraido]
            })
        
        # BÚSQUEDA 2: Código extraído como código local
        elif codigo_extraido and codigo_extraido in indices['por_codigo_local']:
            resultado.update({
                'encontrado': True,
                'metodo': 'CODIGO_LOCAL_EXTRAIDO', 
                'info_encontrada': indices['por_codigo_local'][codigo_extraido]
            })
        
        # BÚSQUEDA 3: Nombre extraído exacto
        elif nombre_extraido:
            nombre_norm = nombre_extraido.upper().strip()
            if nombre_norm in indices['por_nombre']:
                resultado.update({
                    'encontrado': True,
                    'metodo': 'NOMBRE_EXTRAIDO_EXACTO',
                    'info_encontrada': indices['por_nombre'][nombre_norm]
                })
        
        resultados.append(resultado)
        
        if resultado['encontrado']:
            info = resultado['info_encontrada']
            print(f"✅ {nombre_original} -> {info['codigo_modular']} ({resultado['metodo']})")
        else:
            print(f"❌ {nombre_original} -> No encontrado")
    
    return resultados

if __name__ == "__main__":
    resultados = buscar_con_patron_dual()
    encontrados = len([r for r in resultados if r['encontrado']])
    print(f"Patrón dual completado: {encontrados} instituciones adicionales encontradas")
```

---

## 💾 FASE 4: ACTUALIZACIÓN DE BASE DE DATOS

### Paso 4.1: Script de Actualización Masiva
```python
# actualizar_base_datos.py
import sqlite3
import json
import config

def actualizar_codigos_encontrados(resultados_busqueda, tabla_destino, campos_mapping):
    """
    Actualiza la base de datos con los códigos modulares encontrados
    
    Args:
        resultados_busqueda (list): Lista de resultados de búsqueda
        tabla_destino (str): Nombre de la tabla a actualizar
        campos_mapping (dict): Mapeo de campos locales a estándar
    """
    
    conn = sqlite3.connect(config.RUTAS['base_datos_principal'])
    cursor = conn.cursor()
    
    # Contar estado inicial
    cursor.execute(f"SELECT COUNT(*) FROM {tabla_destino} WHERE {campos_mapping['codigo_modular']} IS NULL")
    inicial_sin_codigo = cursor.fetchone()[0]
    
    cursor.execute(f"SELECT COUNT(*) FROM {tabla_destino} WHERE {campos_mapping['codigo_modular']} IS NOT NULL")
    inicial_con_codigo = cursor.fetchone()[0]
    
    print(f"Estado inicial:")
    print(f"  Con código: {inicial_con_codigo}")
    print(f"  Sin código: {inicial_sin_codigo}")
    
    # Procesar actualizaciones
    actualizaciones_totales = 0
    
    for resultado in resultados_busqueda:
        if not resultado['encontrado']:
            continue
            
        # Extraer datos para actualización
        inst_original = resultado['institucion_original']
        codigo_encontrado = resultado['info_encontrada']['codigo_modular']
        
        # Construir consulta de actualización
        query_update = f"""
        UPDATE {tabla_destino}
        SET {campos_mapping['codigo_modular']} = ?
        WHERE {campos_mapping['codigo_modular']} IS NULL
        AND {campos_mapping['nombre_institucion']} = ?
        AND {campos_mapping['codigo_local']} = ?
        """
        
        # Ejecutar actualización
        cursor.execute(query_update, (
            codigo_encontrado,
            inst_original['nombre_institucion'],
            inst_original['codigo_local']
        ))
        
        registros_actualizados = cursor.rowcount
        actualizaciones_totales += registros_actualizados
        
        if registros_actualizados > 0:
            print(f"✅ {inst_original['nombre_institucion'][:40]}... -> {codigo_encontrado} ({registros_actualizados} registros)")
    
    # Commit cambios
    conn.commit()
    
    # Verificar estado final
    cursor.execute(f"SELECT COUNT(*) FROM {tabla_destino} WHERE {campos_mapping['codigo_modular']} IS NULL")
    final_sin_codigo = cursor.fetchone()[0]
    
    cursor.execute(f"SELECT COUNT(*) FROM {tabla_destino} WHERE {campos_mapping['codigo_modular']} IS NOT NULL")
    final_con_codigo = cursor.fetchone()[0]
    
    cursor.execute(f"SELECT COUNT(*) FROM {tabla_destino}")
    total = cursor.fetchone()[0]
    
    print(f"\\nEstado final:")
    print(f"  Total registros: {total}")
    print(f"  Con código: {final_con_codigo}")
    print(f"  Sin código: {final_sin_codigo}")
    print(f"  Cobertura: {(final_con_codigo/total*100):.2f}%")
    print(f"  Registros actualizados: {actualizaciones_totales}")
    
    conn.close()
    
    return {
        'actualizaciones': actualizaciones_totales,
        'cobertura_final': final_con_codigo/total*100,
        'registros_restantes': final_sin_codigo
    }

# Configuración específica del proyecto
campos_mapping = {
    'codigo_modular': 'tu_campo_codigo_modular',
    'nombre_institucion': 'tu_campo_nombre',
    'codigo_local': 'tu_campo_codigo_local'
}

if __name__ == "__main__":
    # Cargar resultados de búsquedas previas
    with open('resultados_busqueda_final.json', 'r') as f:
        resultados = json.load(f)
    
    # Ejecutar actualización
    estadisticas = actualizar_codigos_encontrados(
        resultados, 
        'tu_tabla_principal', 
        campos_mapping
    )
    
    print(f"\\n🎉 Proceso completado:")
    print(f"  Cobertura final: {estadisticas['cobertura_final']:.2f}%")
    print(f"  Registros pendientes: {estadisticas['registros_restantes']}")
```

---

## 📊 FASE 5: VALIDACIÓN Y REPORTE

### Paso 5.1: Script de Validación
```python
# validar_resultados.py
import sqlite3
import config

def validar_actualizaciones(tabla, campos_mapping):
    """Valida la calidad de las actualizaciones realizadas"""
    
    conn = sqlite3.connect(config.RUTAS['base_datos_principal'])
    cursor = conn.cursor()
    
    validaciones = []
    
    # VALIDACIÓN 1: Integridad de códigos modulares
    cursor.execute(f"""
        SELECT {campos_mapping['codigo_modular']}, COUNT(*) 
        FROM {tabla} 
        WHERE {campos_mapping['codigo_modular']} IS NOT NULL
        AND LENGTH({campos_mapping['codigo_modular']}) != 7
        GROUP BY {campos_mapping['codigo_modular']}
    """)
    
    codigos_invalidos = cursor.fetchall()
    if codigos_invalidos:
        validaciones.append({
            'tipo': 'ERROR',
            'mensaje': f'Códigos modulares con longitud incorrecta: {len(codigos_invalidos)}'
        })
    else:
        validaciones.append({
            'tipo': 'OK',
            'mensaje': 'Todos los códigos modulares tienen formato válido (7 dígitos)'
        })
    
    # VALIDACIÓN 2: Códigos duplicados
    cursor.execute(f"""
        SELECT {campos_mapping['codigo_modular']}, COUNT(*) as veces
        FROM {tabla} 
        WHERE {campos_mapping['codigo_modular']} IS NOT NULL
        GROUP BY {campos_mapping['codigo_modular']}
        HAVING COUNT(*) > 100
    """)
    
    posibles_duplicados = cursor.fetchall()
    if posibles_duplicados:
        validaciones.append({
            'tipo': 'WARNING',
            'mensaje': f'Códigos con alta frecuencia (revisar): {len(posibles_duplicados)}'
        })
    else:
        validaciones.append({
            'tipo': 'OK',
            'mensaje': 'Distribución de códigos modulares sin anomalías'
        })
    
    # VALIDACIÓN 3: Cobertura por región/categoría
    cursor.execute(f"""
        SELECT 
            {campos_mapping.get('region', 'region')},
            COUNT(*) as total,
            COUNT({campos_mapping['codigo_modular']}) as vinculados,
            ROUND(COUNT({campos_mapping['codigo_modular']}) * 100.0 / COUNT(*), 2) as porcentaje
        FROM {tabla}
        GROUP BY {campos_mapping.get('region', 'region')}
        ORDER BY porcentaje DESC
    """)
    
    cobertura_regional = cursor.fetchall()
    cobertura_baja = [r for r in cobertura_regional if r[3] < 90]
    
    if cobertura_baja:
        validaciones.append({
            'tipo': 'WARNING',
            'mensaje': f'Regiones con cobertura <90%: {len(cobertura_baja)}'
        })
    else:
        validaciones.append({
            'tipo': 'OK',
            'mensaje': 'Cobertura uniforme en todas las regiones (>90%)'
        })
    
    # Mostrar resultados de validación
    print("\\n🔍 RESULTADOS DE VALIDACIÓN:")
    for val in validaciones:
        icono = "✅" if val['tipo'] == 'OK' else "⚠️" if val['tipo'] == 'WARNING' else "❌"
        print(f"  {icono} {val['mensaje']}")
    
    conn.close()
    return validaciones

def generar_reporte_final(tabla, campos_mapping):
    """Genera reporte final del proyecto"""
    
    conn = sqlite3.connect(config.RUTAS['base_datos_principal'])
    cursor = conn.cursor()
    
    # Estadísticas generales
    cursor.execute(f"SELECT COUNT(*) FROM {tabla}")
    total_registros = cursor.fetchone()[0]
    
    cursor.execute(f"SELECT COUNT(*) FROM {tabla} WHERE {campos_mapping['codigo_modular']} IS NOT NULL")
    registros_vinculados = cursor.fetchone()[0]
    
    cursor.execute(f"SELECT COUNT(*) FROM {tabla} WHERE {campos_mapping['codigo_modular']} IS NULL")
    registros_sin_vincular = cursor.fetchone()[0]
    
    cobertura = (registros_vinculados / total_registros) * 100
    
    reporte = {
        'fecha_reporte': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'proyecto': 'NOMBRE_TU_PROYECTO',
        'estadisticas_finales': {
            'total_registros': total_registros,
            'registros_vinculados': registros_vinculados,
            'registros_sin_vincular': registros_sin_vincular,
            'cobertura_porcentual': round(cobertura, 2)
        },
        'estado_proyecto': 'COMPLETADO' if cobertura >= 95 else 'PARCIAL',
        'metodologias_aplicadas': [
            'Búsqueda automática por nombre exacto',
            'Búsqueda por código local',
            'Búsqueda fuzzy (similitud)',
            'Algoritmo patrón dual (separación código + nombre)'
        ]
    }
    
    # Guardar reporte
    with open(f"{config.RUTAS['directorio_resultados']}/reporte_final.json", 'w', encoding='utf-8') as f:
        json.dump(reporte, f, indent=2, ensure_ascii=False)
    
    print(f"\\n📋 REPORTE FINAL DEL PROYECTO:")
    print(f"  Total de registros procesados: {total_registros:,}")
    print(f"  Registros vinculados: {registros_vinculados:,} ({cobertura:.2f}%)")
    print(f"  Registros sin vincular: {registros_sin_vincular:,}")
    print(f"  Estado: {reporte['estado_proyecto']}")
    
    return reporte

if __name__ == "__main__":
    # Configurar campos según tu proyecto
    campos_mapping = {
        'codigo_modular': 'tu_campo_codigo_modular',
        'region': 'tu_campo_region'  # opcional
    }
    
    validaciones = validar_actualizaciones('tu_tabla_principal', campos_mapping)
    reporte = generar_reporte_final('tu_tabla_principal', campos_mapping)
```

---

## 🚀 FASE 6: DOCUMENTACIÓN Y ENTREGA

### Paso 6.1: Template de Documentación
```markdown
# PROYECTO [NOMBRE] - IDENTIFICACIÓN CÓDIGOS MODULARES

## Resumen Ejecutivo
- **Fecha**: [FECHA]
- **Registros procesados**: [TOTAL]
- **Cobertura inicial**: [%]
- **Cobertura final**: [%]
- **Mejora conseguida**: [+X registros vinculados]

## Metodologías Aplicadas
1. **Búsqueda automática**: [X instituciones encontradas]
2. **Patrón dual**: [X instituciones encontradas]  
3. **Identificación manual**: [X instituciones encontradas]

## Archivos Generados
- Scripts de búsqueda: `buscador_*.py`
- Datos de trabajo: `*.json`
- Reportes: `reporte_final.json`

## Instituciones Identificadas
[Lista de códigos modulares encontrados]

## Recomendaciones Futuras
[Sugerencias para proyectos similares]
```

### Paso 6.2: Checklist de Entrega
- [ ] Scripts de búsqueda probados y documentados
- [ ] Base de datos actualizada y verificada
- [ ] Reportes de validación generados
- [ ] Documentación técnica completa
- [ ] Backup de datos originales preservado
- [ ] Template de replicación preparado para futuros proyectos

---

## 💡 CONSEJOS Y MEJORES PRÁCTICAS

### Performance
- Usar índices en memoria para búsquedas repetitivas
- Procesar en lotes para archivos muy grandes
- Considerar paralelización para proyectos masivos

### Calidad de Datos
- Siempre validar códigos modulares (formato 7 dígitos)
- Verificar coherencia geográfica (IE en ubicación correcta)
- Documentar todas las decisiones de matching manual

### Mantenimiento
- Actualizar padrón nacional periódicamente
- Versionado de scripts para futuras referencias
- Mantener logs detallados de todos los cambios

---

## 🆘 TROUBLESHOOTING COMÚN

### Problemas de Encoding
```python
# Si hay problemas con caracteres especiales
tabla = DBF(archivo, encoding='latin-1')  # Probar primero
# tabla = DBF(archivo, encoding='utf-8')   # Alternativa
# tabla = DBF(archivo, encoding='cp1252')  # Windows
```

### Memoria Insuficiente
```python
# Procesar en lotes en lugar de cargar todo
def procesar_en_lotes(tabla_dbf, tamaño_lote=10000):
    lote = []
    for i, record in enumerate(tabla_dbf):
        lote.append(record)
        if len(lote) >= tamaño_lote:
            procesar_lote(lote)
            lote = []
    
    # Procesar último lote
    if lote:
        procesar_lote(lote)
```

### Campos Faltantes
```python
# Verificar campos antes de usar
def verificar_campo_existe(record, campo, valor_default=''):
    return record.get(campo, valor_default)

# Uso seguro
nombre = verificar_campo_existe(record, 'CEN_EDU', 'SIN_NOMBRE')
```

---

## 📞 SOPORTE TÉCNICO

**Documentación base**: `PROCEDIMIENTO_COMPLETO_CODIGOS_MODULARES.md`  
**Guía padrón nacional**: `GUIA_BASE_DATOS_NACIONAL_MINEDU.md`  
**Proyecto de referencia**: Reasis 2025 (100% éxito)  

---

*Template actualizado: 2025-08-09*  
*Basado en metodología exitosa proyecto Reasis*