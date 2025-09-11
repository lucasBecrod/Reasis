#!/usr/bin/env python3
"""
Procesador Anual SIAGIE - Garantiza el procesamiento completo y optimizado
de todas las filas de un año específico, con bajo consumo de memoria.

Uso:
  python procesador_anual_siagie.py <año>

Ejemplo:
  python procesador_anual_siagie.py 2024
"""

import sqlite3
from dbfread import DBF
import pandas as pd
import os
from datetime import datetime
import sys
import gc

class ProcesadorAnualSIAGIE:
    def __init__(self, año):
        self.año = año
        self.output_dir = "data/siagie_procesado"
        self.block_size = 100000  # Procesar en bloques de 100,000 registros
        
        print("1. Cargando instituciones de Fe y Alegría desde la base de datos...")
        self.instituciones_fya = self._cargar_instituciones_fya()
        self.dict_cod_mod = {inst['codigo_modular']: inst for inst in self.instituciones_fya}
        self.dict_cod_local = {inst['codigo_local']: inst for inst in self.instituciones_fya if inst['codigo_local']}
        
        print("2. Creando diccionarios de búsqueda normalizados (numéricos)...")
        self.dict_cod_mod_numeric = {}
        self.dict_cod_local_numeric = {}

        for inst in self.instituciones_fya:
            try:
                # Para códigos modulares
                cod_mod_int = int(inst['codigo_modular'])
                self.dict_cod_mod_numeric[cod_mod_int] = inst
            except (ValueError, TypeError):
                pass  # Ignorar si el código no es puramente numérico

            try:
                # Para códigos locales
                if inst['codigo_local']:
                    cod_local_int = int(inst['codigo_local'])
                    self.dict_cod_local_numeric[cod_local_int] = inst
            except (ValueError, TypeError):
                pass # Ignorar si el código no es puramente numérico
        
        os.makedirs(self.output_dir, exist_ok=True)
        
        print(f"\n=== PROCESADOR ANUAL SIAGIE PARA EL AÑO {self.año} ===")
        print(f"Instituciones Fe y Alegría cargadas: {len(self.instituciones_fya)}")
        print(f"Códigos modulares para búsqueda: {len(self.dict_cod_mod)}")
        print(f"Códigos locales para búsqueda: {len(self.dict_cod_local)}")
        print(f"Tamaño de bloque: {self.block_size:,} registros")
        print(f"Códigos modulares numéricos para búsqueda flexible: {len(self.dict_cod_mod_numeric)}")
        print(f"Códigos locales numéricos para búsqueda flexible: {len(self.dict_cod_local_numeric)}")

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

    def _get_value_from_record(self, record, keys, default=''):
        """Obtiene un valor de un registro probando una lista de posibles llaves."""
        for key in keys:
            if key in record and record[key] is not None:
                return str(record[key]).strip()
        return default

    def procesar_bloque_y_escribir(self, records_block, archivo_csv, es_primer_bloque):
        """Procesa un bloque, normaliza los datos y los escribe directamente al CSV."""
        encontrados = []
        
        for record in records_block:
            # Búsqueda robusta de códigos usando una lista de posibles nombres de columna
            # --- CORRECCIÓN CRÍTICA: Preservar ceros a la izquierda ---
            # Se elimina la conversión a float/int que eliminaba los ceros.
            # Ahora se trata como texto y solo se limpia el ".0" si existe.
            cod_mod_raw = self._get_value_from_record(record, ['cod_mod', 'codmod', 'codigomodu'])
            cod_local_raw = self._get_value_from_record(record, ['cod_local', 'codlocal', 'codigoloca', 'codlocalu'])
            cod_mod = cod_mod_raw.split('.')[0]
            cod_local = cod_local_raw.split('.')[0]
            
            institucion_encontrada = None
            metodo = None

            # --- ESTRATEGIA DE VINCULACIÓN MULTI-NIVEL ---

            # Nivel 1: Coincidencia Exacta (Máxima Confianza)
            if cod_mod and cod_mod in self.dict_cod_mod:
                institucion_encontrada = self.dict_cod_mod[cod_mod]
                metodo = "CODIGO_MODULAR_EXACTO"
            elif cod_local and cod_local in self.dict_cod_local:
                institucion_encontrada = self.dict_cod_local[cod_local]
                metodo = "CODIGO_LOCAL_EXACTO"

            # Nivel 2: Coincidencia Numérica Normalizada (para casos como '0600692' vs '600692')
            if not institucion_encontrada:
                try:
                    cod_mod_int = int(cod_mod)
                    if cod_mod_int in self.dict_cod_mod_numeric:
                        institucion_encontrada = self.dict_cod_mod_numeric[cod_mod_int]
                        metodo = "CODIGO_MODULAR_NORMALIZADO"
                except (ValueError, TypeError):
                    pass # El código del SIAGIE no es numérico

                if not institucion_encontrada:
                    try:
                        cod_local_int = int(cod_local)
                        if cod_local_int in self.dict_cod_local_numeric:
                            institucion_encontrada = self.dict_cod_local_numeric[cod_local_int]
                            metodo = "CODIGO_LOCAL_NORMALIZADO"
                    except (ValueError, TypeError):
                        pass # El código del SIAGIE no es numérico

            if institucion_encontrada:
                registro_completo = dict(record)
                
                # NORMALIZACIÓN DE CAMPOS CLAVE
                # --- AJUSTE CLAVE: Usar los códigos de NUESTRA BD como la fuente de verdad ---
                registro_completo['codigo_modular_norm'] = institucion_encontrada['codigo_modular']
                registro_completo['codigo_local_norm'] = institucion_encontrada['codigo_local']
                
                total_alumnos_val = self._get_value_from_record(record, ['total', 'talumnos', 'talum'])
                try:
                    registro_completo['total_alumnos_norm'] = int(float(total_alumnos_val)) if total_alumnos_val else 0
                except (ValueError, TypeError):
                    registro_completo['total_alumnos_norm'] = 0

                # METADATOS DE VINCULACIÓN
                registro_completo['metodo_vinculacion'] = metodo
                registro_completo['nombre_fya_bd'] = institucion_encontrada['nombre']
                registro_completo['red_fya'] = institucion_encontrada['red']
                registro_completo['fecha_procesamiento'] = datetime.now().isoformat()
                
                encontrados.append(registro_completo)
        
        if encontrados:
            df_bloque = pd.DataFrame(encontrados)
            # Forzar el tipo de dato a string para las columnas de código ANTES de guardar.
            # Esto previene que pandas los interprete como números y pierda ceros a la izquierda.
            for col in ['codigo_modular_norm', 'codigo_local_norm', 'cod_mod', 'cod_local', 'codigomodu', 'codigoloca']:
                if col in df_bloque.columns:
                    df_bloque[col] = df_bloque[col].astype(str).replace({r'\.0$': ''}, regex=True)
            if es_primer_bloque:
                df_bloque.to_csv(archivo_csv, index=False, encoding='utf-8', mode='w')
            else:
                df_bloque.to_csv(archivo_csv, index=False, encoding='utf-8', mode='a', header=False)
        
        return len(encontrados)

    def procesar(self):
        """Garantiza el procesamiento de TODAS las filas del archivo DBF para el año especificado."""
        archivo_siagie = f'data/bases_de_datos/siagie/SIAGIE Reporte Matricula {self.año}.dbf'
        
        if not os.path.exists(archivo_siagie):
            print(f"\n[ERROR] El archivo para el año {self.año} no fue encontrado en la ruta:")
            print(f"  > {archivo_siagie}")
            return
        
        print(f"\n2. Iniciando procesamiento del archivo: {archivo_siagie}")
        archivo_salida = os.path.join(self.output_dir, f'siagie_fya_{self.año}_completo.csv')
        
        total_procesados = 0
        total_encontrados = 0
        bloque_actual = 1
        es_primer_bloque = True
        
        if os.path.exists(archivo_salida):
            os.remove(archivo_salida)
            print(f"   - Se eliminó el archivo de resultados anterior para empezar de cero.")

        try:
            with DBF(archivo_siagie, encoding='latin1', lowernames=True) as table:
                print(f"   - Columnas detectadas en el archivo: {', '.join(table.field_names)}")
                print("\n3. Procesando registros en bloques (esto puede tardar)...")
                
                records_block = []
                for record in table:
                    records_block.append(record)
                    total_procesados += 1
                    
                    if len(records_block) >= self.block_size:
                        encontrados_bloque = self.procesar_bloque_y_escribir(records_block, archivo_salida, es_primer_bloque)
                        total_encontrados += encontrados_bloque
                        if encontrados_bloque > 0: es_primer_bloque = False
                        
                        print(f"   - Bloque {bloque_actual} ({total_procesados:,} registros revisados): {encontrados_bloque} coincidencias encontradas.")
                        
                        records_block.clear()
                        bloque_actual += 1
                        gc.collect()

                if records_block:
                    encontrados_bloque = self.procesar_bloque_y_escribir(records_block, archivo_salida, es_primer_bloque)
                    total_encontrados += encontrados_bloque
                    print(f"   - Bloque final {bloque_actual} ({total_procesados:,} registros revisados): {encontrados_bloque} coincidencias encontradas.")

        except Exception as e:
            print(f"\n[ERROR FATAL] Ocurrió un error durante el procesamiento: {e}")
            import traceback
            traceback.print_exc()
            return

        # Resumen final después de procesar todo el archivo
        if total_encontrados > 0:
            print("\n4. Calculando estadísticas finales...")
            try:
                df_stats = pd.read_csv(archivo_salida, usecols=['codigo_modular_norm', 'total_alumnos_norm'], encoding='utf-8', dtype={'codigo_modular_norm': str})
                instituciones_unicas = df_stats['codigo_modular_norm'].nunique()
                total_alumnos = df_stats['total_alumnos_norm'].sum()

                print(f"\n{'='*60}")
                print(f"RESUMEN FINAL - AÑO {self.año}")
                print(f"{'='*60}")
                print(f"   - Total de registros SIAGIE revisados: {total_procesados:,}")
                print(f"   - Total de registros Fe y Alegría encontrados: {total_encontrados:,}")
                print(f"   - Instituciones únicas encontradas: {instituciones_unicas}")
                print(f"   - Total de alumnos en IIEE encontradas: {int(total_alumnos):,}")
                print(f"   - Resultados guardados en: {archivo_salida}")
                print(f"{'='*60}")
            except Exception as e:
                print(f"[ERROR] No se pudieron calcular las estadísticas finales: {e}")
        elif total_procesados > 0:
            print("\n[INFO] No se encontraron registros de Fe y Alegría en el archivo.")

def main():
    """Función principal para ejecutar el procesador desde la línea de comandos."""
    if len(sys.argv) != 2:
        print("Uso incorrecto. Debes especificar el año a procesar.")
        print("Ejemplo: python procesador_anual_siagie.py 2024")
        sys.exit(1)
    
    try:
        año = int(sys.argv[1])
        procesador = ProcesadorAnualSIAGIE(año)
        procesador.procesar()
    except ValueError:
        print(f"[ERROR] El argumento '{sys.argv[1]}' no es un año válido.")
        sys.exit(1)

if __name__ == "__main__":
    main()