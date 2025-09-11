#!/usr/bin/env python3
"""
Procesador SIAGIE optimizado para memoria - No acumula registros en memoria
Procesa cada año por bloques pequeños y escribe directamente a CSV
"""

import sqlite3
from dbfread import DBF
import pandas as pd
import os
from datetime import datetime
import sys

class ProcesadorSIAGIEOptimizado:
    def __init__(self):
        self.output_dir = "data/siagie_procesado"
        self.block_size = 100000  # Bloques más pequeños para memoria
        self.instituciones_fya = self._cargar_instituciones_fya()
        self.dict_cod_mod = {inst['codigo_modular']: inst for inst in self.instituciones_fya}
        self.dict_cod_local = {inst['codigo_local']: inst for inst in self.instituciones_fya if inst['codigo_local']}
        
        # Asegurar que existe directorio de salida
        os.makedirs(self.output_dir, exist_ok=True)
        
        print(f"=== PROCESADOR SIAGIE OPTIMIZADO ===")
        print(f"Instituciones Fe y Alegría: {len(self.instituciones_fya)}")
        print(f"Códigos modulares: {len(self.dict_cod_mod)}")
        print(f"Tamaño de bloque: {self.block_size:,} registros")
    
    def _cargar_instituciones_fya(self):
        """Carga instituciones Fe y Alegría de la BD"""
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
    
    def procesar_bloque_directo(self, records_block, archivo_csv, es_primer_bloque):
        """Procesa un bloque y lo escribe directamente al CSV sin acumular"""
        encontrados = []
        
        for record in records_block:
            cod_mod = str(record.get('CODIGOMODU', '')).strip()
            cod_local = str(record.get('CODLOCALU', '')).strip()
            
            institucion_encontrada = None
            metodo = None
            
            # ESTRATEGIA 1: Código modular
            if cod_mod in self.dict_cod_mod:
                institucion_encontrada = self.dict_cod_mod[cod_mod]
                metodo = "CODIGO_MODULAR"
            
            # ESTRATEGIA 2: Código local
            elif cod_local in self.dict_cod_local:
                institucion_encontrada = self.dict_cod_local[cod_local]
                metodo = "CODIGO_LOCAL"
            
            if institucion_encontrada:
                # Crear registro completo
                registro_completo = dict(record)
                registro_completo['METODO_VINCULACION'] = metodo
                registro_completo['NOMBRE_FYA_BD'] = institucion_encontrada['nombre']
                registro_completo['RED_FYA'] = institucion_encontrada['red']
                registro_completo['DEPARTAMENTO_BD'] = institucion_encontrada['departamento_bd']
                registro_completo['PROVINCIA_BD'] = institucion_encontrada['provincia_bd']
                registro_completo['DISTRITO_BD'] = institucion_encontrada['distrito_bd']
                registro_completo['FECHA_PROCESAMIENTO'] = datetime.now().isoformat()
                
                encontrados.append(registro_completo)
        
        # Escribir al CSV inmediatamente si hay resultados
        if encontrados:
            df_bloque = pd.DataFrame(encontrados)
            
            # Primera vez: crear archivo con headers
            if es_primer_bloque:
                df_bloque.to_csv(archivo_csv, index=False, encoding='utf-8', mode='w')
            else:
                # Siguientes veces: append sin headers
                df_bloque.to_csv(archivo_csv, index=False, encoding='utf-8', mode='a', header=False)
        
        return len(encontrados)
    
    def procesar_año_optimizado(self, año):
        """Procesa un año completo de forma optimizada para memoria"""
        archivo_siagie = f'data/bases_de_datos/siagie/SIAGIE Reporte Matricula {año}.dbf'
        
        if not os.path.exists(archivo_siagie):
            print(f"[ERROR] Archivo no encontrado: {archivo_siagie}")
            return None
        
        print(f"\n[PROCESANDO] AÑO {año} - MODO OPTIMIZADO")
        print(f"Archivo: {archivo_siagie}")
        
        archivo_salida = os.path.join(self.output_dir, f'siagie_fya_{año}_optimizado.csv')
        
        total_procesados = 0
        total_encontrados = 0
        bloque_actual = 1
        es_primer_bloque = True
        
        try:
            with DBF(archivo_siagie, encoding='latin1') as table:
                print(f"Procesamiento directo a CSV...")
                
                records_block = []
                
                for record in table:
                    records_block.append(record)
                    total_procesados += 1
                    
                    # Procesar cuando se llena el bloque
                    if len(records_block) >= self.block_size:
                        encontrados_bloque = self.procesar_bloque_directo(
                            records_block, archivo_salida, es_primer_bloque
                        )
                        
                        total_encontrados += encontrados_bloque
                        
                        if encontrados_bloque > 0:
                            print(f"  Bloque {bloque_actual}: {encontrados_bloque} IIEE FyA encontradas (total: {total_encontrados})")
                        
                        # Limpiar memoria
                        records_block.clear()
                        bloque_actual += 1
                        es_primer_bloque = False
                        
                        # Progress cada 5 bloques
                        if bloque_actual % 5 == 0:
                            print(f"    Progreso: {total_procesados:,} registros procesados")
                
                # Último bloque
                if records_block:
                    encontrados_bloque = self.procesar_bloque_directo(
                        records_block, archivo_salida, es_primer_bloque
                    )
                    total_encontrados += encontrados_bloque
                    
                    if encontrados_bloque > 0:
                        print(f"  Bloque final: {encontrados_bloque} IIEE FyA encontradas")
        
        except Exception as e:
            print(f"[ERROR] Error procesando {año}: {e}")
            return None
        
        # Calcular estadísticas finales sin cargar todo en memoria
        if total_encontrados > 0 and os.path.exists(archivo_salida):
            # Leer solo las columnas necesarias para estadísticas
            df_stats = pd.read_csv(archivo_salida, usecols=['CODIGOMODU', 'TOTAL'], encoding='utf-8')
            instituciones_unicas = df_stats['CODIGOMODU'].nunique()
            total_alumnos = df_stats['TOTAL'].sum()
            
            print(f"\n[COMPLETADO] AÑO {año}:")
            print(f"   Registros procesados: {total_procesados:,}")
            print(f"   Registros FyA encontrados: {total_encontrados:,}")
            print(f"   Instituciones únicas: {instituciones_unicas}")
            print(f"   Total alumnos: {int(total_alumnos):,}")
            print(f"   Archivo: {archivo_salida}")
            
            return {
                'año': año,
                'registros_encontrados': total_encontrados,
                'instituciones_unicas': instituciones_unicas,
                'total_alumnos': int(total_alumnos),
                'archivo': archivo_salida
            }
        
        else:
            print(f"[ERROR] No se encontraron datos Fe y Alegría para el año {año}")
            return None

    def procesar_todos_los_años(self, años=None):
        """Procesa todos los años disponibles"""
        if años is None:
            años = [2019, 2020, 2021, 2022, 2023, 2024]
        resultados = []
        
        print(f"\n{'='*60}")
        print(f"INICIANDO PROCESAMIENTO COMPLETO - TODOS LOS AÑOS")
        print(f"Años a procesar: {años}")
        print(f"{'='*60}")
        
        for año in años:
            resultado = self.procesar_año_optimizado(año)
            if resultado:
                resultados.append(resultado)

        if not resultados:
            print("[ERROR] No se pudieron procesar datos de ningún año.")
            return
        
        # Resumen final si se procesó al menos un año
        self._resumen_final(resultados)

    def _resumen_final(self, resultados):
        """Imprime un resumen de los resultados del procesamiento."""
        print(f"\n{'='*60}")
        print(f"RESUMEN FINAL - PROCESAMIENTO OPTIMIZADO COMPLETADO")
        print(f"{'='*60}")
        
        total_registros = sum(r['registros_encontrados'] for r in resultados)
        total_alumnos = sum(r['total_alumnos'] for r in resultados)
        
        print(f"Años procesados exitosamente: {len(resultados)}")
        print(f"Total registros Fe y Alegría: {total_registros:,}")
        print(f"Total alumnos: {total_alumnos:,}")
        print(f"\nResultados por año:")
        
        for resultado in resultados:
            print(f"   {resultado['año']}: {resultado['registros_encontrados']:,} registros, {resultado['total_alumnos']:,} alumnos")

def main():
    """
    Función principal.
    Permite procesar años específicos pasados como argumentos de línea de comandos.
    Si no se pasan argumentos, procesa todos los años por defecto.
    Ejemplo para un año: python procesador_siagie_optimizado.py 2022
    Ejemplo para varios años: python procesador_siagie_optimizado.py 2022 2023
    """
    procesador = ProcesadorSIAGIEOptimizado()
    
    if len(sys.argv) > 1:
        try:
            años_a_procesar = [int(arg) for arg in sys.argv[1:]]
            print(f"Se procesarán los años especificados: {años_a_procesar}")
            procesador.procesar_todos_los_años(años=años_a_procesar)
        except ValueError:
            print("[ERROR] Por favor, proporciona años válidos como argumentos (ej: 2022 2023).")
    else:
        print("No se especificaron años. Se procesarán todos los años por defecto.")
        procesador.procesar_todos_los_años()

if __name__ == "__main__":
    main()