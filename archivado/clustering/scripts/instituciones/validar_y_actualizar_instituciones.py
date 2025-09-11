#!/usr/bin/env python3
"""
Script para validar tipos de datos y actualizar las 9 instituciones con información completa
"""

import sqlite3
import pandas as pd
from typing import Dict, Any, Optional

def verificar_estructura_tabla():
    """Verifica la estructura actual de la tabla instituciones_educativas"""
    
    conn = sqlite3.connect('reasis_database.db')
    cursor = conn.cursor()
    
    # Obtener estructura de la tabla
    cursor.execute('PRAGMA table_info(instituciones_educativas)')
    columnas = cursor.fetchall()
    
    print("=== ESTRUCTURA TABLA instituciones_educativas ===")
    estructura = {}
    for col in columnas:
        col_id, nombre, tipo, no_null, default, pk = col
        estructura[nombre] = {
            'tipo': tipo,
            'no_null': bool(no_null),
            'default': default,
            'pk': bool(pk)
        }
        print(f"{col_id:2}: {nombre:25} {tipo:10} {'NOT NULL' if no_null else '':8} {'PK' if pk else ''}")
    
    conn.close()
    return estructura

def validar_valor_columna(valor: Any, columna: str, tipo_esperado: str) -> tuple[bool, Any]:
    """
    Valida y convierte un valor para que sea compatible con el tipo de columna
    
    Returns:
        (is_valid, converted_value)
    """
    
    if valor is None:
        return True, None
    
    try:
        tipo_esperado = tipo_esperado.upper()
        
        if tipo_esperado == 'TEXT':
            return True, str(valor)
        
        elif tipo_esperado == 'INT':
            if isinstance(valor, (int, float)):
                return True, int(valor)
            elif isinstance(valor, str) and valor.strip():
                return True, int(float(valor))
            else:
                return True, None
        
        elif tipo_esperado == 'REAL':
            if isinstance(valor, (int, float)):
                return True, float(valor)
            elif isinstance(valor, str) and valor.strip():
                return True, float(valor)
            else:
                return True, None
        
        elif tipo_esperado == 'NUM':
            # Tipo numérico genérico - puede ser int o float
            if isinstance(valor, (int, float)):
                return True, valor
            elif isinstance(valor, str) and valor.strip():
                # Intentar como int primero, luego float
                try:
                    return True, int(valor)
                except:
                    return True, float(valor)
            else:
                return True, None
        
        else:
            # Tipo desconocido, mantener como está
            return True, valor
    
    except Exception as e:
        print(f"Error validando {columna} = {valor}: {e}")
        return False, None

def obtener_datos_actualizados():
    """Obtiene los datos validados para las 9 instituciones desde el padrón"""
    
    # Los datos que extrajimos del padrón MINEDU
    instituciones_data = {
        '0600692': {
            'nombre_institucion': 'NUESTRA SEÑORA DE LA CANDELARIA',
            'departamento': 'HUANCAVELICA',
            'provincia': 'ACOBAMBA', 
            'distrito': 'ACOBAMBA',
            'nivel_educativo': 'Secundaria',
            'modalidad': 'Escolarizada',
            'gestion': 'Pública de gestión directa',
            'tipo_sexo': 'Mixto',
            'turno': 'Mañana-Tarde',
            'latitud': -12.0,
            'longitud': -74.0,
            'es_eib': 0
        },
        '1768829': {
            'nombre_institucion': '1574',
            'departamento': 'CAJAMARCA',
            'provincia': 'JAEN',
            'distrito': 'CHONTALI',
            'nivel_educativo': 'Inicial - Jardín',
            'modalidad': 'Escolarizada',
            'gestion': 'Pública de gestión directa',
            'tipo_sexo': 'Mixto',
            'turno': 'Mañana',
            'latitud': -5.0,
            'longitud': -79.0,
            'es_eib': 0
        },
        '0481093': {
            'nombre_institucion': 'JOSE CARLOS MARIATEGUI',
            'departamento': 'MOQUEGUA',
            'provincia': 'MARISCAL NIETO',
            'distrito': 'SAMEGUA',
            'nivel_educativo': 'Instituto Superior Tecnológico',
            'modalidad': 'Escolarizada',
            'gestion': 'Pública de gestión directa',
            'tipo_sexo': 'Mixto',
            'turno': 'Mañana-Noche',
            'latitud': -17.0,
            'longitud': -70.0,
            'es_eib': 0
        },
        '0488403': {
            'nombre_institucion': '88225',
            'departamento': 'ANCASH',
            'provincia': 'SANTA',
            'distrito': 'MORO',
            'nivel_educativo': 'Primaria',
            'modalidad': 'Escolarizada',
            'gestion': 'Pública de gestión directa',
            'tipo_sexo': 'Mixto',
            'turno': 'Mañana',
            'latitud': -9.0,
            'longitud': -78.0,
            'es_eib': 0
        },
        '0304642': {
            'nombre_institucion': '64155',
            'departamento': 'UCAYALI',
            'provincia': 'CORONEL PORTILLO',
            'distrito': 'IPARIA',
            'nivel_educativo': 'Primaria',
            'modalidad': 'Escolarizada',
            'gestion': 'Pública de gestión directa',
            'tipo_sexo': 'Mixto',
            'turno': 'Mañana',
            'latitud': -9.0,
            'longitud': -74.0,
            'es_eib': 0
        },
        '0428714': {
            'nombre_institucion': '36153 SAYRI TUPAC',
            'departamento': 'HUANCAVELICA',
            'provincia': 'ACOBAMBA',
            'distrito': 'ACOBAMBA',
            'nivel_educativo': 'Primaria',
            'modalidad': 'Escolarizada',
            'gestion': 'Pública de gestión directa',
            'tipo_sexo': 'Mixto',
            'turno': 'Mañana',
            'latitud': -12.0,
            'longitud': -74.0,
            'es_eib': 0
        },
        '3025715': {
            'nombre_institucion': '5154 SANTIAGO ANTUNEZ DE MAYOLO',
            'departamento': 'CALLAO',
            'provincia': 'CALLAO',
            'distrito': 'VENTANILLA',
            'nivel_educativo': 'Secundaria',
            'modalidad': 'Escolarizada',
            'gestion': 'Pública de gestión directa',
            'tipo_sexo': 'Mixto',
            'turno': 'Mañana',
            'latitud': -11.0,
            'longitud': -77.0,
            'es_eib': 0
        },
        '2533906': {
            'nombre_institucion': 'YANACANCHA',
            'departamento': 'CAJAMARCA',
            'provincia': 'CELENDIN',
            'distrito': 'CHUMUCH',
            'nivel_educativo': 'Inicial - Programa no escolarizado',
            'modalidad': 'Escolarizada',
            'gestion': 'Pública de gestión directa',
            'tipo_sexo': 'Mixto',
            'turno': 'Mañana',
            'latitud': -6.0,
            'longitud': -78.0,
            'es_eib': 0
        },
        '1781897': {
            'nombre_institucion': '64346',
            'departamento': 'UCAYALI',
            'provincia': 'CORONEL PORTILLO',
            'distrito': 'CALLERIA',
            'nivel_educativo': 'Secundaria',
            'modalidad': 'Escolarizada',
            'gestion': 'Pública de gestión directa',
            'tipo_sexo': 'Mixto',
            'turno': 'Mañana',
            'latitud': -8.0,
            'longitud': -74.0,
            'es_eib': 0
        }
    }
    
    return instituciones_data

def determinar_es_rural(departamento: str, provincia: str, distrito: str) -> int:
    """Determina si una institución es rural basado en su ubicación"""
    
    # Criterios básicos de ruralidad para Peru
    departamentos_rurales = ['HUANCAVELICA', 'APURIMAC', 'AYACUCHO', 'AMAZONAS']
    
    if departamento in departamentos_rurales:
        return 1
    
    # Distritos conocidos como rurales
    distritos_rurales = ['IPARIA', 'CHONTALI', 'CHUMUCH', 'ACOBAMBA']
    
    if distrito in distritos_rurales:
        return 1
    
    # El resto (urbanos)
    return 0

def actualizar_instituciones_validado():
    """Actualiza las instituciones con validación de tipos de datos"""
    
    print("=== ACTUALIZANDO INSTITUCIONES CON VALIDACIÓN ===")
    
    # Obtener estructura de la tabla
    estructura = verificar_estructura_tabla()
    
    # Obtener datos a actualizar
    datos = obtener_datos_actualizados()
    
    # Conectar a la base de datos
    conn = sqlite3.connect('reasis_database.db')
    cursor = conn.cursor()
    
    # Procesar cada institución
    actualizaciones_exitosas = 0
    
    for codigo_modular, info in datos.items():
        print(f"\n--- Actualizando {codigo_modular}: {info['nombre_institucion']} ---")
        
        # Agregar es_rural basado en ubicación
        info['es_rural'] = determinar_es_rural(info['departamento'], info['provincia'], info['distrito'])
        
        # Validar y construir UPDATE
        sets_validados = []
        
        for columna, valor in info.items():
            if columna in estructura:
                tipo_columna = estructura[columna]['tipo']
                es_valido, valor_convertido = validar_valor_columna(valor, columna, tipo_columna)
                
                if es_valido and valor_convertido is not None:
                    if tipo_columna == 'TEXT':
                        valor_escapado = str(valor_convertido).replace("'", "''")
                        sets_validados.append(f"{columna} = '{valor_escapado}'")
                    else:
                        sets_validados.append(f"{columna} = {valor_convertido}")
                    
                    print(f"  ✓ {columna}: {valor_convertido} ({tipo_columna})")
                elif not es_valido:
                    print(f"  ✗ {columna}: Valor inválido {valor}")
        
        # Ejecutar UPDATE si hay campos válidos
        if sets_validados:
            update_sql = f"UPDATE instituciones_educativas SET {', '.join(sets_validados)} WHERE codigo_modular = '{codigo_modular}'"
            
            try:
                cursor.execute(update_sql)
                filas_afectadas = cursor.rowcount
                if filas_afectadas > 0:
                    print(f"  ✓ Actualización exitosa: {len(sets_validados)} campos")
                    actualizaciones_exitosas += 1
                else:
                    print(f"  ⚠ No se encontró la institución con código {codigo_modular}")
            except Exception as e:
                print(f"  ✗ Error en actualización: {e}")
        else:
            print("  ⚠ No hay campos válidos para actualizar")
    
    # Confirmar cambios
    conn.commit()
    conn.close()
    
    print(f"\n=== RESUMEN ===")
    print(f"Instituciones actualizadas exitosamente: {actualizaciones_exitosas}/{len(datos)}")
    
    return actualizaciones_exitosas

def verificar_actualizaciones():
    """Verifica las actualizaciones realizadas"""
    
    print("\n=== VERIFICANDO ACTUALIZACIONES ===")
    
    codigos = ['0600692', '1768829', '0481093', '0488403', '0304642', '0428714', '3025715', '2533906', '1781897']
    
    conn = sqlite3.connect('reasis_database.db')
    
    query = f"""
    SELECT codigo_modular, nombre_institucion, departamento, provincia, distrito,
           nivel_educativo, tipo_sexo, turno, latitud, longitud, es_rural, es_eib
    FROM instituciones_educativas
    WHERE codigo_modular IN ({','.join([f"'{c}'" for c in codigos])})
    ORDER BY codigo_modular
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    print(f"\nDatos actualizados ({len(df)} registros):")
    for _, row in df.iterrows():
        print(f"\n{row['codigo_modular']} - {row['nombre_institucion']}")
        print(f"  Ubicación: {row['departamento']}, {row['provincia']}, {row['distrito']}")
        print(f"  Nivel: {row['nivel_educativo']}")
        print(f"  Características: Rural={row['es_rural']}, EIB={row['es_eib']}")
        print(f"  Coordenadas: {row['latitud']}, {row['longitud']}")

if __name__ == "__main__":
    actualizaciones_exitosas = actualizar_instituciones_validado()
    if actualizaciones_exitosas > 0:
        verificar_actualizaciones()