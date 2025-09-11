#!/usr/bin/env python3
"""
Procesador SIAGIE Base - Plantilla para procesar años específicos
Versión corregida con nombres de columnas correctos
"""

import sqlite3
from dbfread import DBF
import pandas as pd
import os
from datetime import datetime

class ProcesadorSIAGIEBase:
    def __init__(self, año):
        self.output_dir = "data/siagie_procesado"
        self.block_size = 25000  # Bloques ultrapequeños para memoria limitada
        self.año = año
        self.instituciones_fya = self._cargar_instituciones_fya()
        self.dict_cod_mod = {inst['codigo_modular']: inst for inst in self.instituciones_fya}
        self.dict_cod_local = {inst['codigo_local']: inst for inst in self.instituciones_fya if inst['codigo_local']}
        
        # Asegurar que existe directorio de salida
        os.makedirs(self.output_dir, exist_ok=True)
        
        print(f"=== PROCESADOR SIAGIE {self.año} ===")
        print(f"Instituciones Fe y Alegría cargadas: {len(self.instituciones_fya)}")
        print(f"Códigos modulares: {len(self.dict_cod_mod)}")
        print(f"Códigos locales: {len(self.dict_cod_local)}")
        print(f"Tamaño de bloque: {self.block_size:,} registros")
    
    def _cargar_instituciones_fya(self):
        """Carga todas las instituciones Fe y Alegría de la BD"""
        conn = sqlite3.connect('reasis_database.db')
        cursor = conn.execute('''
            SELECT codigo_modular, codigo_local, nombre_institucion, numero_fya, 
                   departamento, provincia, distrito
            FROM instituciones_educativas 
            WHERE codigo_modular IS NOT NULL AND codigo_modular != ''
            ORDER BY numero_fya
        ''')
        
        instituciones = []
        for row in cursor.fetchall():
            instituciones.append({
                'codigo_modular': str(row[0]).strip(),
                'codigo_local': str(row[1]).strip() if row[1] else '',
                'nombre': row[2],
                'red': row[3],
                'departamento_bd': row[4],
                'provincia_bd': row[5],
                'distrito_bd': row[6]
            })
        
        conn.close()
        return instituciones
    
    def procesar_bloque(self, records_block):
        """Procesa un bloque de registros y extrae los de Fe y Alegría"""
        encontrados = []
        
        for record in records_block:
            # Obtener códigos del registro (NOMBRES CORRECTOS)
            cod_mod = str(record.get('COD_MOD', '')).strip()
            cod_local = str(record.get('COD_LOCAL', '')).strip()
            
            institucion_encontrada = None
            metodo = ""
            
            # ESTRATEGIA 1: Buscar por código modular
            if cod_mod in self.dict_cod_mod:
                institucion_encontrada = self.dict_cod_mod[cod_mod]
                metodo = "CODIGO_MODULAR"
            
            # ESTRATEGIA 2: Buscar por código local
            elif cod_local in self.dict_cod_local:
                institucion_encontrada = self.dict_cod_local[cod_local]
                metodo = "CODIGO_LOCAL"
            
            if institucion_encontrada:
                # Extraer TODAS las columnas del registro original
                registro_completo = dict(record)
                
                # Agregar metadatos de vinculación
                registro_completo['METODO_VINCULACION'] = metodo
                registro_completo['NOMBRE_FYA_BD'] = institucion_encontrada['nombre']
                registro_completo['RED_FYA'] = institucion_encontrada['red']
                registro_completo['DEPARTAMENTO_BD'] = institucion_encontrada['departamento_bd']
                registro_completo['PROVINCIA_BD'] = institucion_encontrada['provincia_bd']
                registro_completo['DISTRITO_BD'] = institucion_encontrada['distrito_bd']
                registro_completo['FECHA_PROCESAMIENTO'] = datetime.now().isoformat()
                
                encontrados.append(registro_completo)
        
        return encontrados
    
    def procesar_año(self):
        """Procesa el año especificado por bloques"""
        archivo_siagie = f'data/bases_de_datos/siagie/SIAGIE Reporte Matricula {self.año}.dbf'
        
        if not os.path.exists(archivo_siagie):
            print(f"[ERROR] Archivo no encontrado: {archivo_siagie}")
            return None
        
        print(f"\n[PROCESANDO] AÑO {self.año}")
        print(f"Archivo: {archivo_siagie}")
        
        # Archivo de salida
        archivo_salida = os.path.join(self.output_dir, f'siagie_fya_{self.año}_completo.csv')
        
        total_procesados = 0
        total_encontrados = 0
        bloque_actual = 1
        todos_encontrados = []
        
        try:
            with DBF(archivo_siagie, encoding='latin1') as table:
                print(f"Iniciando procesamiento por bloques...")
                
                records_block = []
                
                for record in table:
                    records_block.append(record)
                    total_procesados += 1
                    
                    # Cuando se completa un bloque
                    if len(records_block) >= self.block_size:
                        print(f"  Procesando bloque {bloque_actual}: registros {total_procesados-len(records_block)+1:,} - {total_procesados:,}")
                        
                        # Procesar bloque
                        encontrados_bloque = self.procesar_bloque(records_block)
                        todos_encontrados.extend(encontrados_bloque)
                        total_encontrados += len(encontrados_bloque)
                        
                        if len(encontrados_bloque) > 0:
                            print(f"    [OK] Encontradas {len(encontrados_bloque)} instituciones FyA en este bloque")
                        
                        # Limpiar bloque para liberar memoria
                        records_block = []
                        bloque_actual += 1
                
                # Procesar último bloque si queda algo
                if records_block:
                    print(f"  Procesando bloque final {bloque_actual}: registros {total_procesados-len(records_block)+1:,} - {total_procesados:,}")
                    encontrados_bloque = self.procesar_bloque(records_block)
                    todos_encontrados.extend(encontrados_bloque)
                    total_encontrados += len(encontrados_bloque)
                    
                    if len(encontrados_bloque) > 0:
                        print(f"    [OK] Encontradas {len(encontrados_bloque)} instituciones FyA en bloque final")
        
        except Exception as e:
            print(f"[ERROR] Error procesando {self.año}: {e}")
            return None
        
        # Guardar resultados
        if todos_encontrados:
            df_año = pd.DataFrame(todos_encontrados)
            df_año.to_csv(archivo_salida, index=False, encoding='utf-8')
            
            # Estadísticas
            instituciones_unicas = df_año['COD_MOD'].nunique()
            total_alumnos = df_año['TALUMNOS'].sum() if 'TALUMNOS' in df_año.columns else 0
            
            print(f"\n[COMPLETADO] AÑO {self.año}:")
            print(f"   Registros procesados: {total_procesados:,}")
            print(f"   Registros FyA encontrados: {total_encontrados:,}")
            print(f"   Instituciones únicas: {instituciones_unicas}")
            print(f"   Total alumnos: {int(total_alumnos):,}")
            print(f"   Guardado en: {archivo_salida}")
            
            # Distribución por red
            red_stats = df_año.groupby('RED_FYA').agg({
                'COD_MOD': 'nunique',
                'TALUMNOS': 'sum'
            }).reset_index()
            
            print(f"   Distribución por red:")
            for _, row in red_stats.iterrows():
                alumnos = int(row['TALUMNOS']) if pd.notna(row['TALUMNOS']) else 0
                print(f"     Red {row['RED_FYA']}: {row['COD_MOD']} instituciones, {alumnos} alumnos")
            
            return {
                'año': self.año,
                'registros_procesados': total_procesados,
                'registros_encontrados': total_encontrados,
                'instituciones_unicas': instituciones_unicas,
                'total_alumnos': int(total_alumnos),
                'archivo_salida': archivo_salida
            }
        
        else:
            print(f"[INFO] No se encontraron instituciones Fe y Alegría en {self.año}")
            return None

def crear_procesador_año(año):
    """Función auxiliar para crear procesador de año específico"""
    print(f"PROCESADOR SIAGIE {año} - INICIANDO")
    print(f"Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    procesador = ProcesadorSIAGIEBase(año)
    resultado = procesador.procesar_año()
    
    print(f"\n{'='*50}")
    print(f"PROCESAMIENTO {año} - RESULTADO FINAL")
    print(f"{'='*50}")
    
    if resultado:
        print(f"[OK] Año {año} procesado exitosamente")
        print(f"Registros FyA encontrados: {resultado['registros_encontrados']:,}")
        print(f"Instituciones únicas: {resultado['instituciones_unicas']}")
        print(f"Total alumnos: {resultado['total_alumnos']:,}")
        print(f"Archivo: {resultado['archivo_salida']}")
    else:
        print(f"[ERROR] No se pudo procesar el año {año}")
    
    print(f"Fin: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    return resultado