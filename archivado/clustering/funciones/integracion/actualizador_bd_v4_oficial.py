#!/usr/bin/env python3
"""
Actualizador Base de Datos v4 - IIEE RER Oficiales
Actualiza reasis_database_v4.db con información oficial de Fe y Alegría
Solo mantiene las 163 IIEE RER confirmadas oficialmente
"""

import sqlite3
import pandas as pd
from pathlib import Path
import logging

# Configuración
EXCEL_PATH = Path("data/bases_de_datos/IIEE CONFIRMADAS POR RER FE Y ALEGRIA.xlsx")
DATABASE_V4_PATH = "reasis_database_v4.db"

def setup_logging():
    """Configurar logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('data/reports/actualizacion_bd_v4.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def leer_datos_oficiales(excel_path):
    """Leer datos oficiales del archivo Excel"""
    logger = logging.getLogger(__name__)
    
    logger.info("Leyendo archivo Excel oficial...")
    
    # Leer tabla RER
    df_rer = pd.read_excel(excel_path, sheet_name='RER')
    logger.info(f"RER leídas: {len(df_rer)} registros")
    
    # Leer tabla Instituciones Educativas
    df_iiee = pd.read_excel(excel_path, sheet_name='Instituciones Educativas')
    logger.info(f"IIEE leídas: {len(df_iiee)} registros")
    
    # Limpiar y estandarizar nombres de columnas
    df_rer.columns = df_rer.columns.str.strip()
    df_iiee.columns = df_iiee.columns.str.strip()
    
    return df_rer, df_iiee

def actualizar_tabla_rer(conn, df_rer):
    """Actualizar tabla RER con datos oficiales"""
    logger = logging.getLogger(__name__)
    
    logger.info("Actualizando tabla RER...")
    
    # Crear tabla RER actualizada
    cursor = conn.cursor()
    
    # Eliminar tabla RER existente y recrear
    cursor.execute("DROP TABLE IF EXISTS redes_rer_oficial")
    
    create_query = """
    CREATE TABLE redes_rer_oficial (
        rer_numero TEXT PRIMARY KEY,
        region TEXT,
        ugel TEXT,
        provincia TEXT,
        direccion TEXT,
        cantidad_iiee_confirmadas INTEGER,
        grupo_rer TEXT,
        unidad_ejecutora TEXT,
        fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
    cursor.execute(create_query)
    
    # Insertar datos oficiales
    for _, row in df_rer.iterrows():
        cursor.execute("""
            INSERT OR REPLACE INTO redes_rer_oficial 
            (rer_numero, region, ugel, provincia, direccion, cantidad_iiee_confirmadas, grupo_rer, unidad_ejecutora)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(row.get('RER', '')).strip(),
            str(row.get('Región', '')).strip(),
            str(row.get('UGEL', '')).strip(),
            str(row.get('Provincia', '')).strip(),
            str(row.get('Dirección', '')).strip(),
            int(row.get('IIEE', 0)),
            str(row.get('GRUPO', '')).strip(),
            str(row.get('Unidad Ejecutora', '')).strip()
        ))
    
    conn.commit()
    logger.info(f"Tabla RER actualizada con {len(df_rer)} RER oficiales")
    
    return True

def sincronizar_instituciones_educativas(conn, df_iiee):
    """Sincronizar tabla instituciones_educativas con IIEE oficiales"""
    logger = logging.getLogger(__name__)
    
    logger.info("Sincronizando tabla instituciones_educativas...")
    
    cursor = conn.cursor()
    
    # Obtener IIEE actuales en BD
    cursor.execute("SELECT codigo_modular FROM instituciones_educativas")
    codigos_bd = {str(row[0]) for row in cursor.fetchall()}
    
    # Obtener códigos oficiales
    codigos_oficiales = {str(codigo) for codigo in df_iiee['Código Modular'].dropna()}
    
    logger.info(f"IIEE en BD actual: {len(codigos_bd)}")
    logger.info(f"IIEE oficiales: {len(codigos_oficiales)}")
    
    # Encontrar diferencias
    solo_en_bd = codigos_bd - codigos_oficiales
    solo_en_oficial = codigos_oficiales - codigos_bd
    comunes = codigos_bd & codigos_oficiales
    
    logger.info(f"Solo en BD (a eliminar): {len(solo_en_bd)}")
    logger.info(f"Solo en oficial (a agregar): {len(solo_en_oficial)}")
    logger.info(f"Comunes (mantener): {len(comunes)}")
    
    # Eliminar IIEE que no están en la lista oficial
    if solo_en_bd:
        placeholders = ','.join(['?' for _ in solo_en_bd])
        cursor.execute(f"DELETE FROM instituciones_educativas WHERE codigo_modular IN ({placeholders})", 
                      list(solo_en_bd))
        logger.info(f"Eliminadas {len(solo_en_bd)} IIEE no oficiales")
    
    # Agregar IIEE nuevas si las hay
    if solo_en_oficial:
        for codigo in solo_en_oficial:
            fila_oficial = df_iiee[df_iiee['Código Modular'].astype(str) == str(codigo)].iloc[0]
            
            # Insertar nueva institución con datos básicos
            cursor.execute("""
                INSERT OR REPLACE INTO instituciones_educativas 
                (codigo_modular, nombre_institucion, codigo_local, nivel_educativo, region, provincia, distrito, numero_fya)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(fila_oficial['Código Modular']),
                str(fila_oficial.get('Nombre de la I.E.', '')),
                str(fila_oficial.get('Código Local', '')),
                str(fila_oficial.get('Nivel Educativo / Modalidad', '')),
                str(fila_oficial.get('Región', '')),
                str(fila_oficial.get('Provincia', '')),
                str(fila_oficial.get('Distrito', '')),
                str(fila_oficial.get('Nombre RER', ''))
            ))
        
        logger.info(f"Agregadas {len(solo_en_oficial)} IIEE oficiales nuevas")
    
    # Actualizar información de IIEE comunes con datos oficiales
    for codigo in comunes:
        fila_oficial = df_iiee[df_iiee['Código Modular'].astype(str) == str(codigo)].iloc[0]
        
        cursor.execute("""
            UPDATE instituciones_educativas 
            SET nombre_institucion = ?, codigo_local = ?, nivel_educativo = ?, 
                region = ?, provincia = ?, distrito = ?, numero_fya = ?
            WHERE codigo_modular = ?
        """, (
            str(fila_oficial.get('Nombre de la I.E.', '')),
            str(fila_oficial.get('Código Local', '')),
            str(fila_oficial.get('Nivel Educativo / Modalidad', '')),
            str(fila_oficial.get('Región', '')),
            str(fila_oficial.get('Provincia', '')),
            str(fila_oficial.get('Distrito', '')),
            str(fila_oficial.get('Nombre RER', '')),
            str(codigo)
        ))
    
    conn.commit()
    
    # Verificar resultado final
    cursor.execute("SELECT COUNT(*) FROM instituciones_educativas")
    total_final = cursor.fetchone()[0]
    
    logger.info(f"Sincronización completada. Total IIEE en BD: {total_final}")
    
    return total_final

def limpiar_indices_metodologicos(conn):
    """Limpiar tabla indices_metodologicos manteniendo solo IIEE oficiales"""
    logger = logging.getLogger(__name__)
    
    logger.info("Limpiando tabla indices_metodologicos...")
    
    cursor = conn.cursor()
    
    # Obtener códigos modulares oficiales de la tabla actualizada
    cursor.execute("SELECT codigo_modular FROM instituciones_educativas")
    codigos_oficiales = {str(row[0]) for row in cursor.fetchall()}
    
    # Verificar tabla indices_metodologicos
    try:
        cursor.execute("SELECT codigo_modular FROM indices_metodologicos")
        codigos_indices = {str(row[0]) for row in cursor.fetchall()}
        
        # Encontrar registros a eliminar
        a_eliminar = codigos_indices - codigos_oficiales
        
        if a_eliminar:
            placeholders = ','.join(['?' for _ in a_eliminar])
            cursor.execute(f"DELETE FROM indices_metodologicos WHERE codigo_modular IN ({placeholders})", 
                          list(a_eliminar))
            logger.info(f"Eliminados {len(a_eliminar)} registros de indices_metodologicos")
        
        # Verificar resultado
        cursor.execute("SELECT COUNT(*) FROM indices_metodologicos")
        total_indices = cursor.fetchone()[0]
        
        logger.info(f"Índices metodológicos finales: {total_indices}")
        
        conn.commit()
        return total_indices
        
    except sqlite3.OperationalError as e:
        logger.warning(f"No se pudo limpiar indices_metodologicos: {e}")
        return 0

def generar_reporte_actualizacion(conn):
    """Generar reporte de la actualización"""
    logger = logging.getLogger(__name__)
    
    cursor = conn.cursor()
    
    # Estadísticas finales
    cursor.execute("SELECT COUNT(*) FROM instituciones_educativas")
    total_iiee = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM redes_rer_oficial")
    total_rer = cursor.fetchone()[0]
    
    try:
        cursor.execute("SELECT COUNT(*) FROM indices_metodologicos")
        total_indices = cursor.fetchone()[0]
    except:
        total_indices = 0
    
    # Distribución por RER
    cursor.execute("""
        SELECT 
            SUBSTR(numero_fya, -2) as rer,
            COUNT(*) as cantidad
        FROM instituciones_educativas 
        WHERE numero_fya LIKE '%RER FA%'
        GROUP BY SUBSTR(numero_fya, -2)
        ORDER BY cantidad DESC
    """)
    distribucion = cursor.fetchall()
    
    logger.info("=== REPORTE DE ACTUALIZACIÓN BD v4 ===")
    logger.info(f"Total IIEE oficiales: {total_iiee}")
    logger.info(f"Total RER oficiales: {total_rer}")
    logger.info(f"Total índices metodológicos: {total_indices}")
    logger.info("Distribución por RER:")
    for rer, cantidad in distribucion:
        logger.info(f"  RER {rer}: {cantidad} IIEE")
    
    # Guardar reporte en archivo
    reporte_path = Path("data/reports/reporte_actualizacion_v4.txt")
    reporte_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(reporte_path, 'w', encoding='utf-8') as f:
        f.write("=== REPORTE ACTUALIZACIÓN BD v4 ===\n")
        f.write(f"Fecha: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total IIEE oficiales: {total_iiee}\n")
        f.write(f"Total RER oficiales: {total_rer}\n")
        f.write(f"Total índices metodológicos: {total_indices}\n")
        f.write("Distribución por RER:\n")
        for rer, cantidad in distribucion:
            f.write(f"  RER {rer}: {cantidad} IIEE\n")
    
    logger.info(f"Reporte guardado en: {reporte_path}")
    
    return {
        'total_iiee': total_iiee,
        'total_rer': total_rer,
        'total_indices': total_indices,
        'distribucion': distribucion
    }

def main():
    """Función principal"""
    logger = setup_logging()
    
    logger.info("=== INICIANDO ACTUALIZACIÓN BD v4 CON DATOS OFICIALES ===")
    
    try:
        # Verificar archivos
        if not EXCEL_PATH.exists():
            raise FileNotFoundError(f"No se encuentra el archivo Excel: {EXCEL_PATH}")
        
        if not Path(DATABASE_V4_PATH).exists():
            raise FileNotFoundError(f"No se encuentra la base de datos: {DATABASE_V4_PATH}")
        
        # Leer datos oficiales
        df_rer, df_iiee = leer_datos_oficiales(EXCEL_PATH)
        
        # Conectar a BD v4
        with sqlite3.connect(DATABASE_V4_PATH) as conn:
            # Actualizar tabla RER
            actualizar_tabla_rer(conn, df_rer)
            
            # Sincronizar instituciones educativas
            total_iiee = sincronizar_instituciones_educativas(conn, df_iiee)
            
            # Limpiar índices metodológicos
            total_indices = limpiar_indices_metodologicos(conn)
            
            # Generar reporte
            estadisticas = generar_reporte_actualizacion(conn)
        
        logger.info("=== ACTUALIZACIÓN BD v4 COMPLETADA EXITOSAMENTE ===")
        
        return estadisticas
        
    except Exception as e:
        logger.error(f"Error en actualización: {e}")
        return None

if __name__ == "__main__":
    resultado = main()