#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROCESADOR CONECTIVIDAD PERSISTENTE - Con guardado automático en BD
Guarda cada resultado inmediatamente en la base de datos para no perder progreso
"""
import pandas as pd
import sqlite3
import time
from normalizador_ie_conectividad import NormalizadorIEConectividad

class ProcesadorConectividadPersistente:
    """Procesador que guarda cada resultado inmediatamente en BD"""
    
    def __init__(self, db_path: str = 'reasis_database.db'):
        self.db_path = db_path
        self.normalizador = NormalizadorIEConectividad(db_path)
        self.inicializar_tabla_progreso()
    
    def inicializar_tabla_progreso(self):
        """Crea la tabla de progreso de conectividad si no existe"""
        conn = sqlite3.connect(self.db_path)
        
        query_crear_tabla = """
        CREATE TABLE IF NOT EXISTS conectividad_progreso (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            indice_original INTEGER,
            nombre_manual TEXT,
            red_fya TEXT,
            codigo_modular_identificado TEXT,
            matching_status TEXT,
            fecha_procesamiento TEXT DEFAULT CURRENT_TIMESTAMP,
            numero_batch INTEGER,
            observaciones TEXT
        )
        """
        
        conn.execute(query_crear_tabla)
        conn.commit()
        conn.close()
        
        print("[OK] Tabla conectividad_progreso inicializada")
    
    def verificar_progreso_existente(self):
        """Verifica qué registros ya han sido procesados"""
        conn = sqlite3.connect(self.db_path)
        
        query = "SELECT indice_original, matching_status, codigo_modular_identificado FROM conectividad_progreso"
        df_progreso = pd.read_sql_query(query, conn)
        conn.close()
        
        if len(df_progreso) > 0:
            print(f"[OK] Progreso existente encontrado: {len(df_progreso)} registros procesados")
            return df_progreso
        else:
            print("[INFO] No se encontró progreso previo")
            return pd.DataFrame()
    
    def guardar_resultado_inmediato(self, indice_original: int, nombre_manual: str, red_fya: str, 
                                   codigo_identificado: str, status: str, batch_num: int, observaciones: str = ""):
        """Guarda inmediatamente un resultado en la base de datos"""
        conn = sqlite3.connect(self.db_path)
        
        query_insertar = """
        INSERT OR REPLACE INTO conectividad_progreso 
        (indice_original, nombre_manual, red_fya, codigo_modular_identificado, 
         matching_status, numero_batch, observaciones)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        
        cursor = conn.cursor()
        cursor.execute(query_insertar, (
            indice_original, nombre_manual, red_fya, codigo_identificado, 
            status, batch_num, observaciones
        ))
        
        conn.commit()
        conn.close()
        
        print(f"  → [{status}] Guardado en BD: {codigo_identificado}")
    
    def procesar_archivo_completo(self, batch_size: int = 50):
        """Procesa el archivo completo con persistencia en BD"""
        print("=== PROCESADOR CONECTIVIDAD PERSISTENTE ===\n")
        
        # Cargar archivo
        archivo_path = r"C:\Users\lucas\Proyectos\Reasis\assets\Consultoria\Información actualizada\4. Conectividad y equipamiento.xlsx"
        df = pd.read_excel(archivo_path, sheet_name='hoja1', engine='openpyxl')
        
        # Cargar datos de referencia
        self.normalizador.cargar_referencia_ie()
        
        # Columnas
        col_ie_nombre = 'Si pertence a una Red Rural, indique el nombre de su IE'
        col_fya = 'Fe y Alegría Nro. ....'
        
        # Filtrar registros con nombres
        registros_procesar = df[df[col_ie_nombre].notna()].copy()
        registros_procesar = registros_procesar.reset_index()  # Mantener índices originales
        
        # Verificar progreso existente
        progreso_existente = self.verificar_progreso_existente()
        indices_procesados = set(progreso_existente['indice_original'].tolist()) if len(progreso_existente) > 0 else set()
        
        print(f"=== CONFIGURACIÓN PROCESAMIENTO ===")
        print(f"Total registros en archivo: {len(df)}")
        print(f"Registros con nombres IE: {len(registros_procesar)}")
        print(f"Ya procesados: {len(indices_procesados)}")
        print(f"Pendientes por procesar: {len(registros_procesar) - len(indices_procesados)}")
        print(f"Tamaño de bloque: {batch_size}")
        
        # Procesar registros pendientes
        registros_pendientes = [
            (idx, row) for idx, row in registros_procesar.iterrows() 
            if row['index'] not in indices_procesados
        ]
        
        if len(registros_pendientes) == 0:
            print("\n[OK] TODOS LOS REGISTROS YA ESTÁN PROCESADOS")
            self.generar_reporte_final()
            return
        
        print(f"\nIniciando procesamiento de {len(registros_pendientes)} registros pendientes...\n")
        
        # Procesar en bloques
        total_procesados = 0
        total_matches = 0
        total_errores = 0
        
        for batch_start in range(0, len(registros_pendientes), batch_size):
            batch_end = min(batch_start + batch_size, len(registros_pendientes))
            batch_actual = registros_pendientes[batch_start:batch_end]
            batch_num = (batch_start // batch_size) + 1
            
            print(f"=== BLOQUE {batch_num} ===")
            print(f"Procesando {len(batch_actual)} registros ({batch_start + 1}-{batch_end})...")
            
            batch_matches = 0
            batch_errores = 0
            
            for idx_batch, (df_idx, row) in enumerate(batch_actual):
                indice_original = row['index']
                nombre_manual = str(row[col_ie_nombre]).strip()
                red_fya = str(row[col_fya]) if pd.notna(row[col_fya]) else ""
                
                print(f"  [{idx_batch + 1}/{len(batch_actual)}] '{nombre_manual[:40]}...'", end="")
                
                try:
                    # Llamada a Gemini
                    codigo_identificado = self.normalizador.identificar_ie_con_gemini(nombre_manual, red_fya)
                    
                    if codigo_identificado == "NO_MATCH":
                        self.guardar_resultado_inmediato(
                            indice_original, nombre_manual, red_fya, 
                            "NO_MATCH", "NO_MATCH", batch_num, "No se encontró coincidencia"
                        )
                        
                    elif codigo_identificado and len(codigo_identificado) == 7 and codigo_identificado.isdigit():
                        self.guardar_resultado_inmediato(
                            indice_original, nombre_manual, red_fya, 
                            codigo_identificado, "MATCHED", batch_num, "Match exitoso"
                        )
                        batch_matches += 1
                        
                    else:
                        observacion = f"Respuesta inesperada: {codigo_identificado}"
                        self.guardar_resultado_inmediato(
                            indice_original, nombre_manual, red_fya, 
                            str(codigo_identificado) if codigo_identificado else "ERROR", 
                            "ERROR", batch_num, observacion
                        )
                        batch_errores += 1
                
                except Exception as e:
                    print(f"  → [ERROR] Excepción: {str(e)}")
                    self.guardar_resultado_inmediato(
                        indice_original, nombre_manual, red_fya, 
                        "ERROR", "ERROR", batch_num, f"Excepción: {str(e)}"
                    )
                    batch_errores += 1
                
                # Pausa entre requests
                time.sleep(0.5)
            
            # Estadísticas del bloque
            total_procesados += len(batch_actual)
            total_matches += batch_matches
            total_errores += batch_errores
            
            print(f"\n  BLOQUE {batch_num} COMPLETADO:")
            print(f"  - Procesados: {len(batch_actual)}")
            print(f"  - Matches: {batch_matches}")
            print(f"  - Errores: {batch_errores}")
            print(f"  - Tasa éxito: {(batch_matches/len(batch_actual)*100):.1f}%")
            print(f"  - [OK] Progreso guardado en BD automáticamente")
            
            # Pausa entre bloques
            if batch_end < len(registros_pendientes):
                print(f"  Pausa de 2 segundos antes del siguiente bloque...")
                time.sleep(2)
        
        # Estadísticas finales
        print(f"\n=== PROCESAMIENTO COMPLETADO ===")
        print(f"Total procesados en esta sesión: {total_procesados}")
        print(f"Total matches: {total_matches}")
        print(f"Total errores: {total_errores}")
        print(f"Tasa éxito global: {(total_matches/total_procesados*100):.1f}%")
        
        # Generar reporte final
        self.generar_reporte_final()
    
    def generar_reporte_final(self):
        """Genera reporte final del procesamiento completo"""
        print(f"\n=== GENERANDO REPORTE FINAL ===")
        
        conn = sqlite3.connect(self.db_path)
        
        # Estadísticas generales
        query_stats = """
        SELECT 
            matching_status,
            COUNT(*) as count,
            COUNT(*) * 100.0 / (SELECT COUNT(*) FROM conectividad_progreso) as porcentaje
        FROM conectividad_progreso 
        GROUP BY matching_status
        ORDER BY count DESC
        """
        
        df_stats = pd.read_sql_query(query_stats, conn)
        
        print("Estadísticas finales:")
        for _, row in df_stats.iterrows():
            print(f"  {row['matching_status']}: {row['count']} ({row['porcentaje']:.1f}%)")
        
        # Matches exitosos
        query_matches = """
        SELECT nombre_manual, codigo_modular_identificado, red_fya
        FROM conectividad_progreso 
        WHERE matching_status = 'MATCHED'
        ORDER BY fecha_procesamiento
        """
        
        df_matches = pd.read_sql_query(query_matches, conn)
        
        print(f"\nMatches exitosos ({len(df_matches)}):")
        for idx, row in df_matches.head(10).iterrows():
            nombre = row['nombre_manual'][:30] + "..." if len(row['nombre_manual']) > 30 else row['nombre_manual']
            print(f"  '{nombre}' → {row['codigo_modular_identificado']}")
        
        if len(df_matches) > 10:
            print(f"  ... y {len(df_matches) - 10} más")
        
        # Exportar a Excel
        output_path = "conectividad_normalizado_COMPLETO.xlsx"
        df_matches.to_excel(output_path, index=False, engine='openpyxl')
        print(f"\n[OK] Matches exportados a: {output_path}")
        
        conn.close()
        
        print(f"\n[OK] PROCESAMIENTO COMPLETO - Todo guardado en BD")
    
    def resumir_estado(self):
        """Muestra un resumen del estado actual"""
        progreso = self.verificar_progreso_existente()
        
        if len(progreso) > 0:
            status_counts = progreso['matching_status'].value_counts()
            print("\nEstado actual en BD:")
            for status, count in status_counts.items():
                print(f"  {status}: {count}")
            
            return len(progreso)
        return 0

def main():
    print("PROCESADOR PERSISTENTE CONECTIVIDAD\n")
    
    procesador = ProcesadorConectividadPersistente()
    
    # Mostrar estado actual
    registros_existentes = procesador.resumir_estado()
    
    if registros_existentes > 0:
        print(f"\nSe encontraron {registros_existentes} registros ya procesados en BD")
        respuesta = input("¿Continuar procesando registros pendientes? (s/n): ").lower()
    else:
        respuesta = input("¿Iniciar procesamiento completo con guardado persistente? (s/n): ").lower()
    
    if respuesta in ['s', 'si', 'yes', 'y']:
        print("\nIniciando procesamiento persistente...")
        procesador.procesar_archivo_completo(batch_size=50)
        print(f"\n[OK] PROCESAMIENTO COMPLETADO CON PERSISTENCIA")
    else:
        print("Procesamiento cancelado")

if __name__ == "__main__":
    main()