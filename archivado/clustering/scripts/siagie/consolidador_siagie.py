#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Consolidador de Archivos SIAGIE 2019-2024
Unifica archivos CSV con diferentes esquemas de columnas en un solo archivo consolidado.
"""

import pandas as pd
import os
from datetime import datetime

class ConsolidadorSiagie:
    def __init__(self, directorio_datos):
        self.directorio_datos = directorio_datos
        
        # Mapeo de columnas para cada período
        self.mapeo_columnas = {
            # Mapeo para años 2019-2022
            'formato_2019_2022': {
                'id_anio': 'anio',
                'cod_dre': 'cod_dre',
                'nom_dre': 'nom_dre',
                'cod_ugel': 'cod_ugel',
                'nom_ugel': 'nom_ugel',
                'ubigeo': 'ubigeo',
                'dpto': 'departamento',
                'prov': 'provincia',
                'dist': 'distrito',
                'c_poblado': 'centro_poblado',
                'cod_local': 'codigo_local',
                'cod_mod': 'codigo_modular',
                'anexo': 'anexo',
                'nombre_iie': 'nombre_ie',
                'gestion': 'gestion',
                'nivel': 'nivel',
                'grado': 'grado',
                'seccion': 'seccion',
                'turno': 'turno',
                'talumnos': 'total_alumnos',
                'codigo_modular_norm': 'codigo_modular_norm',
                'codigo_local_norm': 'codigo_local_norm',
                'total_alumnos_norm': 'total_alumnos_norm',
                'metodo_vinculacion': 'metodo_vinculacion',
                'nombre_fya_bd': 'nombre_fya_bd',
                'red_fya': 'red_fya',
                'fecha_procesamiento': 'fecha_procesamiento'
            },
            
            # Mapeo para años 2023-2024
            'formato_2023_2024': {
                'anio': 'anio',  # 2023 usa 'anio', 2024 usa 'id_anio'
                'id_anio': 'anio',  # Para 2024
                'cod_dre': 'cod_dre',
                'nom_dre': 'nom_dre',
                'cod_ugel': 'cod_ugel',
                'nom_ugel': 'nom_ugel',
                'ubigeo': 'ubigeo',
                'departamen': 'departamento',
                'provincia': 'provincia',
                'distrito': 'distrito',
                'centropobl': 'centro_poblado',
                'codigoloca': 'codigo_local',
                'periodopro': 'periodo_promocion',
                'codigomodu': 'codigo_modular',
                'anexo': 'anexo',
                'nombre_ie': 'nombre_ie',
                'gestion': 'gestion',
                'dsc_nivel': 'nivel',
                'dsc_grado': 'grado',
                'dsc_seccio': 'seccion',
                'turno': 'turno',
                'total': 'total_alumnos',
                'codigo_modular_norm': 'codigo_modular_norm',
                'codigo_local_norm': 'codigo_local_norm',
                'total_alumnos_norm': 'total_alumnos_norm',
                'metodo_vinculacion': 'metodo_vinculacion',
                'nombre_fya_bd': 'nombre_fya_bd',
                'red_fya': 'red_fya',
                'fecha_procesamiento': 'fecha_procesamiento'
            }
        }
        
        # Columnas finales esperadas en el archivo consolidado
        self.columnas_finales = [
            'anio', 'cod_dre', 'nom_dre', 'cod_ugel', 'nom_ugel', 'ubigeo',
            'departamento', 'provincia', 'distrito', 'centro_poblado',
            'codigo_local', 'periodo_promocion', 'codigo_modular', 'anexo',
            'nombre_ie', 'gestion', 'nivel', 'grado', 'seccion', 'turno',
            'total_alumnos', 'codigo_modular_norm', 'codigo_local_norm',
            'total_alumnos_norm', 'metodo_vinculacion', 'nombre_fya_bd',
            'red_fya', 'fecha_procesamiento'
        ]
    
    def detectar_formato(self, df):
        """Detecta el formato del archivo basado en los nombres de columnas"""
        columnas = set(df.columns)
        
        # Verificar si es formato 2019-2022
        indicadores_2019_2022 = {'dpto', 'prov', 'dist', 'c_poblado', 'talumnos', 'cod_mod'}
        if indicadores_2019_2022.issubset(columnas):
            return 'formato_2019_2022'
        
        # Verificar si es formato 2023-2024
        indicadores_2023_2024 = {'departamen', 'provincia', 'distrito', 'centropobl', 'total', 'codigomodu'}
        if indicadores_2023_2024.issubset(columnas):
            return 'formato_2023_2024'
        
        # Si no puede detectar, asumir formato más reciente
        return 'formato_2023_2024'
    
    def normalizar_dataframe(self, df, formato):
        """Normaliza un DataFrame al esquema unificado"""
        mapeo = self.mapeo_columnas[formato]
        
        # Crear DataFrame normalizado
        df_normalizado = pd.DataFrame()
        
        for col_original, col_unificada in mapeo.items():
            if col_original in df.columns:
                df_normalizado[col_unificada] = df[col_original]
            else:
                # Agregar columna vacía si no existe
                df_normalizado[col_unificada] = None
        
        # Asegurar que todas las columnas finales estén presentes
        for col in self.columnas_finales:
            if col not in df_normalizado.columns:
                df_normalizado[col] = None
        
        # Reordenar columnas según el esquema final
        df_normalizado = df_normalizado[self.columnas_finales]
        
        return df_normalizado
    
    def cargar_archivo_anio(self, anio):
        """Carga y normaliza un archivo específico por año"""
        archivo_path = os.path.join(self.directorio_datos, f'siagie_fya_{anio}_completo.csv')
        
        if not os.path.exists(archivo_path):
            print(f"ADVERTENCIA: No se encontró el archivo para el año {anio}: {archivo_path}")
            return None
        
        try:
            # Leer el archivo forzando todos los tipos a string para máxima seguridad.
            # Esto previene que pandas interprete códigos como números y elimine ceros.
            df = pd.read_csv(archivo_path, encoding='utf-8', dtype=str)
            
            # Detectar formato
            formato = self.detectar_formato(df)
            print(f"Año {anio}: Formato detectado = {formato}, Registros = {len(df)}")
            
            # Normalizar DataFrame
            df_normalizado = self.normalizar_dataframe(df, formato)
            
            return df_normalizado
            
        except Exception as e:
            print(f"ERROR cargando archivo {anio}: {e}")
            return None
    
    def consolidar_todos_los_anios(self, anios_a_procesar=None):
        """Consolida todos los años en un solo DataFrame"""
        if anios_a_procesar is None:
            anios_a_procesar = [2019, 2020, 2021, 2022, 2023, 2024]
        
        dataframes_consolidados = []
        estadisticas = {}
        
        print("=== INICIANDO CONSOLIDACIÓN SIAGIE ===")
        print(f"Años a procesar: {anios_a_procesar}")
        
        for anio in anios_a_procesar:
            print(f"\n--- Procesando año {anio} ---")
            df_anio = self.cargar_archivo_anio(anio)
            
            if df_anio is not None:
                dataframes_consolidados.append(df_anio)
                estadisticas[anio] = len(df_anio)
                print(f"[OK] Año {anio} procesado exitosamente: {len(df_anio)} registros")
            else:
                estadisticas[anio] = 0
                print(f"[ERROR] Año {anio} falló al procesar")
        
        if not dataframes_consolidados:
            print("ERROR: No se pudo cargar ningún archivo")
            return None
        
        # Concatenar todos los DataFrames
        print("\n--- Consolidando todos los años ---")
        df_consolidado = pd.concat(dataframes_consolidados, ignore_index=True)
        
        # Mostrar estadísticas
        print(f"\n=== ESTADÍSTICAS DE CONSOLIDACIÓN ===")
        total_registros = 0
        for anio, count in estadisticas.items():
            print(f"Año {anio}: {count:,} registros")
            total_registros += count
        
        print(f"\nTOTAL CONSOLIDADO: {len(df_consolidado):,} registros")
        print(f"Columnas en archivo final: {len(df_consolidado.columns)}")
        
        return df_consolidado
    
    def guardar_consolidado(self, df_consolidado, nombre_archivo=None):
        """Guarda el DataFrame consolidado"""
        if nombre_archivo is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            nombre_archivo = f'siagie_fya_consolidado_2019-2024_{timestamp}.csv'
        
        archivo_salida = os.path.join(self.directorio_datos, nombre_archivo)
        
        try:
            df_consolidado.to_csv(archivo_salida, index=False, encoding='utf-8')
            print(f"\n[EXITO] Archivo consolidado guardado exitosamente:")
            print(f"   Archivo: {archivo_salida}")
            print(f"   Registros: {len(df_consolidado):,} registros totales")
            
            return archivo_salida
            
        except Exception as e:
            print(f"ERROR guardando archivo consolidado: {e}")
            return None

def main():
    """Función principal"""
    # Configuración
    directorio_datos = r'C:\Users\lucas\Proyectos\Reasis\data\siagie_procesado'
    
    # Crear consolidador
    consolidador = ConsolidadorSiagie(directorio_datos)
    
    # Consolidar todos los años
    df_consolidado = consolidador.consolidar_todos_los_anios()
    
    if df_consolidado is not None:
        # Guardar resultado
        archivo_salida = consolidador.guardar_consolidado(df_consolidado)
        
        # Mostrar muestra de datos
        print(f"\n=== MUESTRA DE DATOS CONSOLIDADOS ===")
        print(df_consolidado.head())
        
        print(f"\n=== RESUMEN POR AÑO ===")
        resumen_anios = df_consolidado.groupby('anio').size().reset_index(name='registros')
        for _, row in resumen_anios.iterrows():
            print(f"Año {row['anio']}: {row['registros']:,} registros")
        
    else:
        print("FALLO: No se pudo consolidar los archivos")

if __name__ == "__main__":
    main()