#!/usr/bin/env python3
"""
Completador Automático de Datos Docentes - Proyecto Reasis
Completa valores NULL usando técnicas inteligentes basadas en análisis previo
"""

import pandas as pd
import sqlite3

def completar_nivel_educativo():
    """Completar campo nivel_educativo usando institución y RER"""
    print("COMPLETANDO NIVEL EDUCATIVO")
    print("=" * 40)
    
    conn = sqlite3.connect('reasis_database.db')
    
    # Paso 1: Completar usando datos de la misma institución
    print("Paso 1: Completando por institución...")
    
    completados_institucion = 0
    
    # Obtener instituciones con datos parciales
    instituciones_parciales = pd.read_sql_query('''
        SELECT 
            codigo_modular_actual,
            institucion_actual,
            COUNT(*) as total,
            COUNT(nivel_educativo) as con_nivel,
            COUNT(*) - COUNT(nivel_educativo) as sin_nivel
        FROM docentes_data
        WHERE codigo_modular_actual IS NOT NULL
        GROUP BY codigo_modular_actual, institucion_actual
        HAVING COUNT(*) > 1 AND sin_nivel > 0 AND con_nivel > 0
        ORDER BY sin_nivel DESC
    ''', conn)
    
    print(f"Instituciones con oportunidades: {len(instituciones_parciales)}")
    
    for _, inst in instituciones_parciales.iterrows():
        codigo = inst['codigo_modular_actual']
        
        # Obtener valor modal de nivel_educativo para esta institución
        valor_modal = pd.read_sql_query('''
            SELECT nivel_educativo, COUNT(*) as frecuencia
            FROM docentes_data
            WHERE codigo_modular_actual = ? AND nivel_educativo IS NOT NULL
            GROUP BY nivel_educativo
            ORDER BY frecuencia DESC, nivel_educativo
            LIMIT 1
        ''', conn, params=[codigo])
        
        if len(valor_modal) > 0:
            nivel_completar = valor_modal.iloc[0]['nivel_educativo']
            
            # Actualizar registros NULL de esta institución
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE docentes_data 
                SET nivel_educativo = ?
                WHERE codigo_modular_actual = ? 
                AND (nivel_educativo IS NULL OR nivel_educativo = '')
            ''', [nivel_completar, codigo])
            
            actualizados = cursor.rowcount
            completados_institucion += actualizados
            
            if actualizados > 0:
                print(f"  {codigo} ({inst['institucion_actual'][:30]}...): {actualizados} -> {nivel_completar}")
    
    print(f"Total completados por institución: {completados_institucion}")
    
    # Paso 2: Completar usando datos de la misma RER
    print("\nPaso 2: Completando por RER...")
    
    completados_rer = 0
    
    # Obtener RER con datos parciales
    rer_parciales = pd.read_sql_query('''
        SELECT 
            rer,
            COUNT(*) as total,
            COUNT(nivel_educativo) as con_nivel,
            COUNT(*) - COUNT(nivel_educativo) as sin_nivel
        FROM docentes_data
        WHERE rer IS NOT NULL AND (nivel_educativo IS NULL OR nivel_educativo = '')
        GROUP BY rer
        HAVING sin_nivel > 0
        ORDER BY sin_nivel DESC
    ''', conn)
    
    print(f"RER con registros NULL restantes: {len(rer_parciales)}")
    
    for _, rer_info in rer_parciales.iterrows():
        rer_codigo = rer_info['rer']
        
        # Obtener valor modal de nivel_educativo para esta RER
        valor_modal_rer = pd.read_sql_query('''
            SELECT nivel_educativo, COUNT(*) as frecuencia
            FROM docentes_data
            WHERE rer = ? AND nivel_educativo IS NOT NULL
            GROUP BY nivel_educativo
            ORDER BY frecuencia DESC, nivel_educativo
            LIMIT 1
        ''', conn, params=[rer_codigo])
        
        if len(valor_modal_rer) > 0:
            nivel_completar = valor_modal_rer.iloc[0]['nivel_educativo']
            
            # Actualizar registros NULL de esta RER
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE docentes_data 
                SET nivel_educativo = ?
                WHERE rer = ? 
                AND (nivel_educativo IS NULL OR nivel_educativo = '')
            ''', [nivel_completar, rer_codigo])
            
            actualizados = cursor.rowcount
            completados_rer += actualizados
            
            if actualizados > 0:
                print(f"  RER {rer_codigo}: {actualizados} -> {nivel_completar}")
    
    print(f"Total completados por RER: {completados_rer}")
    
    # Paso 3: Completar usando datos del mismo docente
    print("\nPaso 3: Completando por mismo docente...")
    
    completados_dni = 0
    
    # Docentes con datos en múltiples años
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE docentes_data 
        SET nivel_educativo = (
            SELECT nivel_educativo 
            FROM docentes_data d2 
            WHERE d2.dni = docentes_data.dni 
            AND d2.nivel_educativo IS NOT NULL 
            LIMIT 1
        )
        WHERE (nivel_educativo IS NULL OR nivel_educativo = '') 
        AND dni IN (
            SELECT dni 
            FROM docentes_data 
            WHERE nivel_educativo IS NOT NULL
        )
    ''')
    
    completados_dni = cursor.rowcount
    print(f"Total completados por mismo docente: {completados_dni}")
    
    conn.commit()
    
    total_completados = completados_institucion + completados_rer + completados_dni
    print(f"\nTOTAL NIVEL_EDUCATIVO COMPLETADO: {total_completados}")
    
    # Verificar resultado
    resultado = pd.read_sql_query('''
        SELECT 
            COUNT(*) as total,
            COUNT(nivel_educativo) as completos,
            COUNT(*) - COUNT(nivel_educativo) as restantes_null
        FROM docentes_data
    ''', conn).iloc[0]
    
    print(f"Estado final: {resultado['completos']}/{resultado['total']} completos ({resultado['completos']/resultado['total']*100:.1f}%)")
    print(f"NULL restantes: {resultado['restantes_null']}")
    
    conn.close()
    return total_completados

def completar_genero_personal():
    """Completar campo genero_personal usando RER y institución"""
    print("\nCOMPLETANDO GENERO PERSONAL")
    print("=" * 40)
    
    conn = sqlite3.connect('reasis_database.db')
    
    # Paso 1: Completar usando datos del mismo docente (máxima precisión)
    print("Paso 1: Completando por mismo docente...")
    
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE docentes_data 
        SET genero_personal = (
            SELECT genero_personal 
            FROM docentes_data d2 
            WHERE d2.dni = docentes_data.dni 
            AND d2.genero_personal IS NOT NULL 
            LIMIT 1
        )
        WHERE (genero_personal IS NULL OR genero_personal = '') 
        AND dni IN (
            SELECT dni 
            FROM docentes_data 
            WHERE genero_personal IS NOT NULL
        )
    ''')
    
    completados_dni = cursor.rowcount
    print(f"Total completados por mismo docente: {completados_dni}")
    
    # Paso 2: Completar usando datos de la misma institución
    print("\nPaso 2: Completando por institución...")
    
    completados_institucion = 0
    
    instituciones_parciales = pd.read_sql_query('''
        SELECT 
            codigo_modular_actual,
            institucion_actual,
            COUNT(*) as total,
            COUNT(genero_personal) as con_genero,
            COUNT(*) - COUNT(genero_personal) as sin_genero
        FROM docentes_data
        WHERE codigo_modular_actual IS NOT NULL
        AND (genero_personal IS NULL OR genero_personal = '')
        GROUP BY codigo_modular_actual, institucion_actual
        HAVING COUNT(*) > 1 AND sin_genero > 0
        ORDER BY sin_genero DESC
    ''', conn)
    
    print(f"Instituciones con oportunidades restantes: {len(instituciones_parciales)}")
    
    for _, inst in instituciones_parciales.iterrows():
        codigo = inst['codigo_modular_actual']
        
        # Obtener valor modal de genero_personal para esta institución
        valor_modal = pd.read_sql_query('''
            SELECT genero_personal, COUNT(*) as frecuencia
            FROM docentes_data
            WHERE codigo_modular_actual = ? AND genero_personal IS NOT NULL
            GROUP BY genero_personal
            ORDER BY frecuencia DESC, genero_personal
            LIMIT 1
        ''', conn, params=[codigo])
        
        if len(valor_modal) > 0:
            genero_completar = valor_modal.iloc[0]['genero_personal']
            
            # Actualizar registros NULL de esta institución
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE docentes_data 
                SET genero_personal = ?
                WHERE codigo_modular_actual = ? 
                AND (genero_personal IS NULL OR genero_personal = '')
            ''', [genero_completar, codigo])
            
            actualizados = cursor.rowcount
            completados_institucion += actualizados
            
            if actualizados > 0:
                print(f"  {codigo}: {actualizados} -> {genero_completar}")
    
    print(f"Total completados por institución: {completados_institucion}")
    
    # Paso 3: Completar usando datos de la misma RER (distribución modal)
    print("\nPaso 3: Completando por RER...")
    
    completados_rer = 0
    
    # Solo procesar si aún quedan NULL
    rer_pendientes = pd.read_sql_query('''
        SELECT 
            rer,
            COUNT(*) - COUNT(genero_personal) as sin_genero
        FROM docentes_data
        WHERE rer IS NOT NULL
        GROUP BY rer
        HAVING sin_genero > 0
        ORDER BY sin_genero DESC
    ''', conn)
    
    print(f"RER con registros NULL restantes: {len(rer_pendientes)}")
    
    for _, rer_info in rer_pendientes.iterrows():
        rer_codigo = rer_info['rer']
        
        # Para género, usar distribución estadística nacional (aproximadamente 50/50)
        # Pero primero verificar si hay datos en esta RER
        distribucion_rer = pd.read_sql_query('''
            SELECT genero_personal, COUNT(*) as frecuencia
            FROM docentes_data
            WHERE rer = ? AND genero_personal IS NOT NULL
            GROUP BY genero_personal
            ORDER BY frecuencia DESC
        ''', conn, params=[rer_codigo])
        
        if len(distribucion_rer) > 0:
            # Usar valor modal de la RER
            genero_completar = distribucion_rer.iloc[0]['genero_personal']
        else:
            # Si no hay datos en la RER, usar distribución general
            dist_general = pd.read_sql_query('''
                SELECT genero_personal, COUNT(*) as frecuencia
                FROM docentes_data
                WHERE genero_personal IS NOT NULL
                GROUP BY genero_personal
                ORDER BY frecuencia DESC
                LIMIT 1
            ''', conn)
            
            if len(dist_general) > 0:
                genero_completar = dist_general.iloc[0]['genero_personal']
            else:
                continue  # No hay datos suficientes
        
        # Actualizar solo algunos registros para mantener distribución natural
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE docentes_data 
            SET genero_personal = ?
            WHERE rer = ? 
            AND (genero_personal IS NULL OR genero_personal = '')
            AND ROWID IN (
                SELECT ROWID FROM docentes_data 
                WHERE rer = ? AND (genero_personal IS NULL OR genero_personal = '')
                LIMIT ?
            )
        ''', [genero_completar, rer_codigo, rer_codigo, min(rer_info['sin_genero'], 10)])  # Limitar para mantener naturalidad
        
        actualizados = cursor.rowcount
        completados_rer += actualizados
        
        if actualizados > 0:
            print(f"  RER {rer_codigo}: {actualizados} -> {genero_completar}")
    
    print(f"Total completados por RER: {completados_rer}")
    
    conn.commit()
    
    total_completados = completados_dni + completados_institucion + completados_rer
    print(f"\nTOTAL GENERO_PERSONAL COMPLETADO: {total_completados}")
    
    # Verificar resultado
    resultado = pd.read_sql_query('''
        SELECT 
            COUNT(*) as total,
            COUNT(genero_personal) as completos,
            COUNT(*) - COUNT(genero_personal) as restantes_null
        FROM docentes_data
    ''', conn).iloc[0]
    
    print(f"Estado final: {resultado['completos']}/{resultado['total']} completos ({resultado['completos']/resultado['total']*100:.1f}%)")
    print(f"NULL restantes: {resultado['restantes_null']}")
    
    conn.close()
    return total_completados

def completar_codigo_modular_vinculado():
    """Completar campo codigo_modular_vinculado usando RER"""
    print("\nCOMPLETANDO CODIGO_MODULAR_VINCULADO")
    print("=" * 50)
    
    conn = sqlite3.connect('reasis_database.db')
    
    # Paso 1: Completar usando datos del mismo docente
    print("Paso 1: Completando por mismo docente...")
    
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE docentes_data 
        SET codigo_modular_vinculado = (
            SELECT codigo_modular_vinculado 
            FROM docentes_data d2 
            WHERE d2.dni = docentes_data.dni 
            AND d2.codigo_modular_vinculado IS NOT NULL 
            LIMIT 1
        ),
        metodo_vinculacion = 'codigo_modular_exacto'
        WHERE (codigo_modular_vinculado IS NULL OR codigo_modular_vinculado = '') 
        AND dni IN (
            SELECT dni 
            FROM docentes_data 
            WHERE codigo_modular_vinculado IS NOT NULL
        )
    ''')
    
    completados_dni = cursor.rowcount
    print(f"Total completados por mismo docente: {completados_dni}")
    
    # Paso 2: Re-ejecutar vinculación para códigos que ahora podrían coincidir
    print("\nPaso 2: Re-ejecutando vinculación por código modular...")
    
    cursor.execute('''
        UPDATE docentes_data 
        SET 
            codigo_modular_vinculado = (
                SELECT ie.codigo_modular
                FROM instituciones_educativas ie
                WHERE ie.codigo_modular = docentes_data.codigo_modular_actual
                LIMIT 1
            ),
            metodo_vinculacion = 'codigo_modular_exacto'
        WHERE (codigo_modular_vinculado IS NULL OR codigo_modular_vinculado = '')
        AND codigo_modular_actual IN (
            SELECT DISTINCT codigo_modular
            FROM instituciones_educativas
            WHERE codigo_modular IS NOT NULL
        )
    ''')
    
    completados_codigo = cursor.rowcount
    print(f"Total completados por código modular: {completados_codigo}")
    
    conn.commit()
    
    total_completados = completados_dni + completados_codigo
    print(f"\nTOTAL CODIGO_MODULAR_VINCULADO COMPLETADO: {total_completados}")
    
    # Verificar resultado
    resultado = pd.read_sql_query('''
        SELECT 
            COUNT(*) as total,
            COUNT(codigo_modular_vinculado) as completos,
            COUNT(*) - COUNT(codigo_modular_vinculado) as restantes_null
        FROM docentes_data
    ''', conn).iloc[0]
    
    print(f"Estado final: {resultado['completos']}/{resultado['total']} completos ({resultado['completos']/resultado['total']*100:.1f}%)")
    print(f"NULL restantes: {resultado['restantes_null']}")
    
    conn.close()
    return total_completados

def generar_reporte_final():
    """Generar reporte final de completitud mejorada"""
    print("\nREPORTE FINAL - COMPLETITUD MEJORADA")
    print("=" * 60)
    
    conn = sqlite3.connect('reasis_database.db')
    
    # Comparar antes vs después
    campos_mejorados = ['nivel_educativo', 'genero_personal', 'codigo_modular_vinculado', 'metodo_vinculacion']
    
    for campo in campos_mejorados:
        stats = pd.read_sql_query(f'''
            SELECT 
                COUNT(*) as total,
                COUNT({campo}) as completos,
                ROUND((COUNT({campo}) * 100.0 / COUNT(*)), 1) as porcentaje_completo
            FROM docentes_data
        ''', conn).iloc[0]
        
        print(f"{campo:25} - {stats['completos']:3}/{stats['total']:3} ({stats['porcentaje_completo']:5.1f}%)")
    
    # Distribución por género (si se completó)
    if 'genero_personal' in campos_mejorados:
        dist_genero = pd.read_sql_query('''
            SELECT genero_personal, COUNT(*) as cantidad
            FROM docentes_data
            WHERE genero_personal IS NOT NULL
            GROUP BY genero_personal
            ORDER BY cantidad DESC
        ''', conn)
        
        if len(dist_genero) > 0:
            print(f"\nDistribución de género:")
            print(dist_genero.to_string(index=False))
    
    # Distribución por nivel educativo
    if 'nivel_educativo' in campos_mejorados:
        dist_nivel = pd.read_sql_query('''
            SELECT nivel_educativo, COUNT(*) as cantidad
            FROM docentes_data
            WHERE nivel_educativo IS NOT NULL
            GROUP BY nivel_educativo
            ORDER BY cantidad DESC
        ''', conn)
        
        if len(dist_nivel) > 0:
            print(f"\nDistribución por nivel educativo:")
            print(dist_nivel.to_string(index=False))
    
    conn.close()

def main():
    """Función principal de completado automático"""
    print("COMPLETADOR AUTOMÁTICO DE DATOS DOCENTES")
    print("=" * 70)
    
    # Ejecutar completado en orden de prioridad
    total_completados = 0
    
    # 1. Nivel educativo (mayor impacto)
    total_completados += completar_nivel_educativo()
    
    # 2. Género personal
    total_completados += completar_genero_personal()
    
    # 3. Código modular vinculado
    total_completados += completar_codigo_modular_vinculado()
    
    # 4. Reporte final
    generar_reporte_final()
    
    print(f"\n{'='*70}")
    print(f"COMPLETADO AUTOMÁTICO FINALIZADO")
    print(f"Total de campos completados: {total_completados}")
    print(f"Técnica aplicada: Completado inteligente por institución, RER y mismo docente")
    print("="*70)
    
    return total_completados

if __name__ == "__main__":
    main()