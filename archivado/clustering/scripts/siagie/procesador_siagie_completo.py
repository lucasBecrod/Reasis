#!/usr/bin/env python3
"""
Procesador completo SIAGIE por bloques para extraer TODAS las IIEE Fe y Alegría
Procesa cada año completo en bloques de 400K registros y acumula resultados
"""

import sqlite3
from dbfread import DBF
import pandas as pd
import os
from datetime import datetime

class ProcesadorSIAGIECompleto:
    def __init__(self):
        self.output_dir = "data/siagie_procesado"
        self.block_size = 200000  # Registros por bloque (reducido para memoria)
        self.instituciones_fya = self._cargar_instituciones_fya()
        self.dict_cod_mod = {inst['codigo_modular']: inst for inst in self.instituciones_fya}
        self.dict_cod_local = {inst['codigo_local']: inst for inst in self.instituciones_fya if inst['codigo_local']}
        
        # Asegurar que existe directorio de salida
        os.makedirs(self.output_dir, exist_ok=True)
        
        print(f"=== PROCESADOR SIAGIE COMPLETO INICIALIZADO ===")
        print(f"Instituciones Fe y Alegría cargadas: {len(self.instituciones_fya)}")
        print(f"Códigos modulares: {len(self.dict_cod_mod)}")
        print(f"Códigos locales: {len(self.dict_cod_local)}")
        print(f"Tamaño de bloque: {self.block_size:,} registros")
        print(f"Directorio salida: {self.output_dir}")
    
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
    
    def procesar_bloque(self, records_block, año):
        """Procesa un bloque de registros y extrae los de Fe y Alegría"""
        encontrados = []
        
        for record in records_block:
            # Obtener códigos del registro
            cod_mod = str(record.get('CODIGOMODU', '')).strip()
            cod_local = str(record.get('CODIGOLOCA', '')).strip()
            
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
    
    def procesar_año_completo(self, año):
        """Procesa un año completo por bloques"""
        archivo_siagie = f'data/bases_de_datos/siagie/SIAGIE Reporte Matricula {año}.dbf'
        
        if not os.path.exists(archivo_siagie):
            print(f"[ERROR] Archivo no encontrado: {archivo_siagie}")
            return None
        
        print(f"\n[PROCESANDO] AÑO {año} - ARCHIVO COMPLETO")
        print(f"Archivo: {archivo_siagie}")
        
        # Archivo de salida para este año
        archivo_salida = os.path.join(self.output_dir, f'siagie_fya_{año}_completo.csv')
        
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
                        encontrados_bloque = self.procesar_bloque(records_block, año)
                        todos_encontrados.extend(encontrados_bloque)
                        total_encontrados += len(encontrados_bloque)
                        
                        if len(encontrados_bloque) > 0:
                            print(f"    [OK] Encontradas {len(encontrados_bloque)} instituciones FyA en este bloque")
                        
                        # Limpiar bloque
                        records_block = []
                        bloque_actual += 1
                
                # Procesar último bloque si queda algo
                if records_block:
                    print(f"  Procesando bloque final {bloque_actual}: registros {total_procesados-len(records_block)+1:,} - {total_procesados:,}")
                    encontrados_bloque = self.procesar_bloque(records_block, año)
                    todos_encontrados.extend(encontrados_bloque)
                    total_encontrados += len(encontrados_bloque)
                    
                    if len(encontrados_bloque) > 0:
                        print(f"    [OK] Encontradas {len(encontrados_bloque)} instituciones FyA en bloque final")
        
        except Exception as e:
            print(f"[ERROR] Error procesando {año}: {e}")
            return None
        
        # Guardar resultados del año
        if todos_encontrados:
            df_año = pd.DataFrame(todos_encontrados)
            df_año.to_csv(archivo_salida, index=False, encoding='utf-8')
            
            # Estadísticas del año
            instituciones_unicas = df_año['CODIGOMODU'].nunique()
            total_alumnos = df_año['TOTAL'].sum()
            
            print(f"\n[COMPLETADO] AÑO {año}:")
            print(f"   Registros procesados: {total_procesados:,}")
            print(f"   Registros FyA encontrados: {total_encontrados:,}")
            print(f"   Instituciones únicas: {instituciones_unicas}")
            print(f"   Total alumnos: {int(total_alumnos):,}")
            print(f"   Guardado en: {archivo_salida}")
            
            # Distribución por red
            red_stats = df_año.groupby('RED_FYA').agg({
                'CODIGOMODU': 'nunique',
                'TOTAL': 'sum'
            }).reset_index()
            
            print(f"   Distribución por red:")
            for _, row in red_stats.iterrows():
                print(f"     Red {row['RED_FYA']}: {row['CODIGOMODU']} instituciones, {int(row['TOTAL'])} alumnos")
            
            return {
                'año': año,
                'registros_procesados': total_procesados,
                'registros_encontrados': total_encontrados,
                'instituciones_unicas': instituciones_unicas,
                'total_alumnos': int(total_alumnos),
                'archivo_salida': archivo_salida
            }
        
        else:
            print(f"[INFO] No se encontraron instituciones Fe y Alegría en {año}")
            return None
    
    def procesar_todos_años(self, años=None):
        """Procesa todos los años disponibles"""
        if años is None:
            años = [2019, 2020, 2021, 2022, 2023, 2024]
        
        print(f"[INICIO] PROCESAMIENTO COMPLETO SIAGIE")
        print(f"Años a procesar: {años}")
        print(f"Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        resultados_años = []
        
        for año in años:
            resultado = self.procesar_año_completo(año)
            if resultado:
                resultados_años.append(resultado)
        
        # Consolidar resultados
        if resultados_años:
            self._consolidar_resultados(resultados_años)
        
        print(f"\n[TERMINADO] PROCESAMIENTO COMPLETO")
        print(f"Fin: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return resultados_años
    
    def _consolidar_resultados(self, resultados_años):
        """Consolida todos los resultados en un archivo maestro"""
        print(f"\n[CONSOLIDANDO] RESULTADOS DE TODOS LOS AÑOS...")
        
        todos_dataframes = []
        
        for resultado in resultados_años:
            if os.path.exists(resultado['archivo_salida']):
                df = pd.read_csv(resultado['archivo_salida'])
                todos_dataframes.append(df)
        
        if todos_dataframes:
            df_consolidado = pd.concat(todos_dataframes, ignore_index=True)
            
            # Archivo consolidado
            archivo_consolidado = os.path.join(self.output_dir, 'siagie_fya_historico_completo.csv')
            df_consolidado.to_csv(archivo_consolidado, index=False, encoding='utf-8')
            
            # Estadísticas consolidadas
            total_registros = len(df_consolidado)
            instituciones_totales = df_consolidado['CODIGOMODU'].nunique()
            alumnos_totales = df_consolidado['TOTAL'].sum()
            
            print(f"[CONSOLIDACION COMPLETADA]:")
            print(f"   Total registros históricos: {total_registros:,}")
            print(f"   Instituciones únicas encontradas: {instituciones_totales}")
            print(f"   Total alumnos históricos: {alumnos_totales:,}")
            print(f"   Archivo consolidado: {archivo_consolidado}")
            
            # Resumen por año
            print(f"\nRESUMEN POR AÑO:")
            resumen_años = df_consolidado.groupby('ID_ANIO').agg({
                'CODIGOMODU': 'nunique',
                'TOTAL': 'sum'
            }).reset_index()
            
            for _, row in resumen_años.iterrows():
                print(f"   {row['ID_ANIO']}: {row['CODIGOMODU']} instituciones, {int(row['TOTAL'])} alumnos")
            
            return archivo_consolidado
        
        return None

def main():
    """Función principal"""
    procesador = ProcesadorSIAGIECompleto()
    
    # Procesar todos los años
    resultados = procesador.procesar_todos_años()
    
    print(f"\n{'='*60}")
    print("PROCESAMIENTO SIAGIE COMPLETO - RESUMEN FINAL")
    print(f"{'='*60}")
    
    if resultados:
        total_registros = sum(r['registros_encontrados'] for r in resultados)
        total_alumnos = sum(r['total_alumnos'] for r in resultados)
        años_exitosos = len(resultados)
        
        print(f"[OK] Años procesados exitosamente: {años_exitosos}")
        print(f"Total registros FyA encontrados: {total_registros:,}")
        print(f"Total alumnos históricos: {total_alumnos:,}")
        print(f"Archivos generados en: data/siagie_procesado/")
        
        for resultado in resultados:
            print(f"   {resultado['año']}: {resultado['registros_encontrados']:,} registros, {resultado['total_alumnos']:,} alumnos")
    
    else:
        print("[ERROR] No se pudieron procesar datos de ningún año")

if __name__ == "__main__":
    main()