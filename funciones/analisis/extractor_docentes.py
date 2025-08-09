#!/usr/bin/env python3
"""
Extractor de Datos Docentes - Proyecto Reasis
Extrae y consolida datos de docentes desde PADD Consolidado.xlsx (hojas 2023 y 2024)
"""

import pandas as pd
import sqlite3
from pathlib import Path
from datetime import datetime

class ExtractorDocentes:
    def __init__(self):
        self.excel_path = Path("C:/Users/lucas/Proyectos/Reasis/assets/Consultoria/Información actualizada/2. PADD Consolidado.xlsx")
        self.db_path = Path("reasis_database.db")
    
    def verificar_archivo(self):
        """Verificar que el archivo Excel existe y tiene las hojas necesarias"""
        print("VERIFICACIÓN DE ARCHIVO EXCEL")
        print("=" * 50)
        
        if not self.excel_path.exists():
            print(f"ERROR: Archivo no encontrado: {self.excel_path}")
            return False
        
        print(f"Archivo encontrado: {self.excel_path.name}")
        
        # Verificar hojas disponibles
        try:
            excel_file = pd.ExcelFile(self.excel_path)
            hojas = excel_file.sheet_names
            print(f"Hojas disponibles: {hojas}")
            
            # Verificar hojas necesarias
            hojas_necesarias = ['2023', '2024']
            hojas_encontradas = []
            
            for hoja in hojas_necesarias:
                if hoja in hojas:
                    hojas_encontradas.append(hoja)
                    print(f"  - Hoja '{hoja}': ENCONTRADA")
                else:
                    print(f"  - Hoja '{hoja}': NO ENCONTRADA")
            
            return len(hojas_encontradas) == len(hojas_necesarias)
            
        except Exception as e:
            print(f"ERROR leyendo archivo: {e}")
            return False
    
    def extraer_datos_2023(self):
        """Extraer datos de la hoja 2023"""
        print("\nEXTRACCIÓN DATOS 2023")
        print("-" * 30)
        
        try:
            df_2023 = pd.read_excel(self.excel_path, sheet_name='2023')
            print(f"Registros encontrados: {len(df_2023)}")
            print(f"Columnas: {len(df_2023.columns)}")
            
            # Mostrar primeras columnas para verificar estructura
            print("Columnas encontradas:")
            for i, col in enumerate(df_2023.columns[:15]):  # Primeras 15 columnas
                print(f"  {i:2}: {col}")
            
            # Mostrar muestra de datos
            print("\nMuestra de datos (primeras 3 filas):")
            print(df_2023.head(3).to_string())
            
            return df_2023
            
        except Exception as e:
            print(f"ERROR extrayendo datos 2023: {e}")
            return None
    
    def extraer_datos_2024(self):
        """Extraer datos de la hoja 2024"""
        print("\nEXTRACCIÓN DATOS 2024")
        print("-" * 30)
        
        try:
            df_2024 = pd.read_excel(self.excel_path, sheet_name='2024')
            print(f"Registros encontrados: {len(df_2024)}")
            print(f"Columnas: {len(df_2024.columns)}")
            
            # Mostrar primeras columnas para verificar estructura
            print("Columnas encontradas:")
            for i, col in enumerate(df_2024.columns[:15]):  # Primeras 15 columnas
                print(f"  {i:2}: {col}")
            
            # Mostrar muestra de datos
            print("\nMuestra de datos (primeras 3 filas):")
            print(df_2024.head(3).to_string())
            
            return df_2024
            
        except Exception as e:
            print(f"ERROR extrayendo datos 2024: {e}")
            return None
    
    def normalizar_datos_2023(self, df_2023):
        """Normalizar datos de 2023 para estructura consolidada"""
        print("\nNORMALIZANDO DATOS 2023")
        print("-" * 30)
        
        if df_2023 is None:
            return None
        
        # Limpiar datos - remover filas completamente vacías
        df_2023 = df_2023.dropna(how='all')
        
        try:
            df_norm = pd.DataFrame()
            
            # Mapeo directo de campos (ajustar nombres según columnas reales)
            # Necesitamos ver las columnas exactas para hacer el mapeo correcto
            columnas = df_2023.columns.tolist()
            print(f"Columnas disponibles para mapeo: {len(columnas)}")
            
            # Intentar mapeo basado en estructura esperada
            # (Ajustaremos según las columnas reales que aparezcan)
            
            # Campos básicos - limpiar DNI correctamente (remover .0 de Excel)
            if 'Número de documento' in columnas:
                df_norm['dni'] = pd.to_numeric(df_2023['Número de documento'], errors='coerce').fillna(0).astype(int).astype(str)
                df_norm = df_norm[df_norm['dni'] != '0']  # Remover valores 0 (NaN convertidos)
            elif 'DNI' in columnas:
                df_norm['dni'] = pd.to_numeric(df_2023['DNI'], errors='coerce').fillna(0).astype(int).astype(str)
                df_norm = df_norm[df_norm['dni'] != '0']  # Remover valores 0 (NaN convertidos)
            
            if 'Nombres' in columnas:
                df_norm['nombres'] = df_2023['Nombres']
            if 'Apellidos' in columnas:
                df_norm['apellidos'] = df_2023['Apellidos']
                
            # Nombre completo combinado
            if 'Nombres' in columnas and 'Apellidos' in columnas:
                df_norm['nombre_completo'] = df_2023['Nombres'].astype(str) + ' ' + df_2023['Apellidos'].astype(str)
            
            # Género
            if 'GENERO' in columnas:
                df_norm['genero'] = df_2023['GENERO']
            
            # RER
            if 'RER' in columnas:
                df_norm['rer'] = df_2023['RER']
            
            # Institución actual
            col_institucion = None
            for col in columnas:
                if 'Institución Educativa' in col and 'brinda' in col:
                    col_institucion = col
                    break
            if col_institucion:
                df_norm['institucion_actual'] = df_2023[col_institucion]
            
            # Código modular actual
            col_codigo = None
            for col in columnas:
                if 'CÓDIGO MODULAR DE IIE' in col and 'CONTINÚA' not in col:
                    col_codigo = col
                    break
            if col_codigo:
                df_norm['codigo_modular_actual'] = df_2023[col_codigo].astype(str).str.strip()
            
            # Nivel educativo
            if 'Nivel' in columnas:
                df_norm['nivel_educativo'] = df_2023['Nivel']
            
            # Continuidad
            col_continua = None
            for col in columnas:
                if 'CONTINÚA' in col and 'SI/NO' in col:
                    col_continua = col
                    break
            if col_continua:
                df_norm['continua_rer'] = df_2023[col_continua]
            
            # Institución donde continúa
            col_inst_continua = None
            for col in columnas:
                if 'QUÉ IIEE CONTINÚA' in col:
                    col_inst_continua = col
                    break
            if col_inst_continua:
                df_norm['institucion_continua'] = df_2023[col_inst_continua]
            
            # Código modular donde continúa
            col_cod_continua = None
            for col in columnas:
                if 'CÓDIGO MODULAR' in col and 'CONTINÚA' in col:
                    col_cod_continua = col
                    break
            if col_cod_continua:
                df_norm['codigo_modular_continua'] = df_2023[col_cod_continua].astype(str).str.strip()
            
            # Puntajes académicos
            if 'MATEMATICA' in columnas:
                df_norm['puntaje_matematica'] = pd.to_numeric(df_2023['MATEMATICA'], errors='coerce')
            if 'COMUNICACIÓN' in columnas:
                df_norm['puntaje_comunicacion'] = pd.to_numeric(df_2023['COMUNICACIÓN'], errors='coerce')
            if 'DIGITAL' in columnas:
                df_norm['puntaje_digital'] = pd.to_numeric(df_2023['DIGITAL'], errors='coerce')
            
            # Estado
            if 'ESTADO' in columnas:
                df_norm['estado_evaluacion'] = df_2023['ESTADO']
            
            # Año y origen
            df_norm['año'] = 2023
            df_norm['archivo_origen'] = '2023'
            
            # Limpiar registros sin DNI
            df_norm = df_norm.dropna(subset=['dni'])
            df_norm = df_norm[df_norm['dni'] != 'nan']
            df_norm = df_norm[df_norm['dni'] != '']
            
            print(f"Registros normalizados 2023: {len(df_norm)}")
            if len(df_norm) > 0:
                print(f"Primeros 5 DNI 2023: {df_norm['dni'].head().tolist()}")
            
            return df_norm
            
        except Exception as e:
            print(f"ERROR normalizando datos 2023: {e}")
            return None
    
    def normalizar_datos_2024(self, df_2024):
        """Normalizar datos de 2024 para estructura consolidada"""
        print("\nNORMALIZANDO DATOS 2024")
        print("-" * 30)
        
        if df_2024 is None:
            return None
        
        # Limpiar datos - remover filas completamente vacías
        df_2024 = df_2024.dropna(how='all')
        
        try:
            df_norm = pd.DataFrame()
            
            columnas = df_2024.columns.tolist()
            print(f"Columnas disponibles para mapeo: {len(columnas)}")
            
            # DNI - limpiar correctamente (remover .0 de Excel)
            if 'DNI' in columnas:
                df_norm['dni'] = pd.to_numeric(df_2024['DNI'], errors='coerce').fillna(0).astype(int).astype(str)
                df_norm = df_norm[df_norm['dni'] != '0']  # Remover valores 0 (NaN convertidos)
            
            # Nombre completo y separar nombres/apellidos
            if 'DOCENTES PARTICIPANTES' in columnas:
                df_norm['nombre_completo'] = df_2024['DOCENTES PARTICIPANTES']
                
                # Intentar separar nombres y apellidos
                nombres_completos = df_2024['DOCENTES PARTICIPANTES'].fillna('').astype(str)
                partes = nombres_completos.str.split(' ', n=2)
                
                df_norm['nombres'] = partes.str[0]
                df_norm['apellidos'] = partes.str[1:].apply(lambda x: ' '.join(x) if isinstance(x, list) else '')
            
            # Género - no disponible en 2024
            df_norm['genero'] = None
            
            # RER
            if 'RER' in columnas:
                df_norm['rer'] = df_2024['RER']
            
            # Institución actual
            col_institucion = None
            for col in columnas:
                if 'Institución Educativa' in col and 'brinda' in col:
                    col_institucion = col
                    break
            if col_institucion:
                df_norm['institucion_actual'] = df_2024[col_institucion]
            
            # Código modular actual
            col_codigo = None
            for col in columnas:
                if 'CÓDIGO MODULAR DE IIE' in col and 'CONTINÚA' not in col:
                    col_codigo = col
                    break
            if col_codigo:
                df_norm['codigo_modular_actual'] = df_2024[col_codigo].astype(str).str.strip()
            
            # Nivel educativo - no disponible en 2024
            df_norm['nivel_educativo'] = None
            
            # Continuidad
            col_continua = None
            for col in columnas:
                if 'CONTINÚA' in col and 'SI/NO' in col:
                    col_continua = col
                    break
            if col_continua:
                df_norm['continua_rer'] = df_2024[col_continua]
            
            # Institución donde continúa
            col_inst_continua = None
            for col in columnas:
                if 'QUÉ IIEE CONTINÚA' in col:
                    col_inst_continua = col
                    break
            if col_inst_continua:
                df_norm['institucion_continua'] = df_2024[col_inst_continua]
            
            # Código modular donde continúa
            col_cod_continua = None
            for col in columnas:
                if 'CÓDIGO MODULAR' in col and 'CONTINÚA' in col:
                    col_cod_continua = col
                    break
            if col_cod_continua:
                df_norm['codigo_modular_continua'] = df_2024[col_cod_continua].astype(str).str.strip()
            
            # Puntajes académicos - no disponibles en 2024
            df_norm['puntaje_matematica'] = None
            df_norm['puntaje_comunicacion'] = None
            df_norm['puntaje_digital'] = None
            
            # Estado
            if 'ESTADO' in columnas:
                df_norm['estado_evaluacion'] = df_2024['ESTADO']
            
            # Año y origen  
            df_norm['año'] = 2024
            df_norm['archivo_origen'] = '2024'
            
            # Limpiar registros sin DNI
            df_norm = df_norm.dropna(subset=['dni'])
            df_norm = df_norm[df_norm['dni'] != 'nan']
            df_norm = df_norm[df_norm['dni'] != '']
            
            # Debugging - mostrar algunos DNI para verificar
            print(f"Registros normalizados 2024: {len(df_norm)}")
            if len(df_norm) > 0:
                print(f"Primeros 5 DNI 2024: {df_norm['dni'].head().tolist()}")
            
            return df_norm
            
        except Exception as e:
            print(f"ERROR normalizando datos 2024: {e}")
            return None
    
    def insertar_datos_consolidados(self, df_2023_norm, df_2024_norm):
        """Insertar datos normalizados en la tabla docentes_data"""
        print("\nINSERTANDO DATOS EN docentes_data")
        print("-" * 40)
        
        conn = sqlite3.connect(self.db_path)
        
        # Limpiar tabla anterior
        conn.execute('DELETE FROM docentes_data')
        print("Tabla limpiada")
        
        registros_insertados = 0
        
        # Insertar datos 2023
        if df_2023_norm is not None:
            try:
                df_2023_norm.to_sql('docentes_data', conn, if_exists='append', index=False)
                registros_2023 = len(df_2023_norm)
                registros_insertados += registros_2023
                print(f"Registros 2023 insertados: {registros_2023}")
            except Exception as e:
                print(f"ERROR insertando 2023: {e}")
        
        # Insertar datos 2024 - manejar duplicados por DNI que aparecen en ambos años
        if df_2024_norm is not None:
            try:
                # Usar INSERT OR REPLACE para manejar duplicados
                for _, row in df_2024_norm.iterrows():
                    placeholders = ', '.join(['?' for _ in row])
                    columns = ', '.join(row.index)
                    sql = f"INSERT OR REPLACE INTO docentes_data ({columns}) VALUES ({placeholders})"
                    conn.execute(sql, tuple(row))
                
                registros_2024 = len(df_2024_norm)
                registros_insertados += registros_2024
                print(f"Registros 2024 insertados/actualizados: {registros_2024}")
                print("  - Nota: Duplicados por DNI fueron actualizados con datos 2024")
            except Exception as e:
                print(f"ERROR insertando 2024: {e}")
                import traceback
                print(traceback.format_exc())
        
        conn.commit()
        conn.close()
        
        print(f"Total registros insertados: {registros_insertados}")
        return registros_insertados
    
    def generar_reporte_consolidacion(self):
        """Generar reporte de la consolidación"""
        print("\nREPORTE DE CONSOLIDACIÓN DOCENTES")
        print("=" * 50)
        
        conn = sqlite3.connect(self.db_path)
        
        # Estadísticas generales
        total = pd.read_sql_query('SELECT COUNT(*) as count FROM docentes_data', conn).iloc[0, 0]
        
        por_año = pd.read_sql_query('''
            SELECT año, COUNT(*) as registros
            FROM docentes_data
            GROUP BY año
            ORDER BY año
        ''', conn)
        
        print(f"Total registros consolidados: {total}")
        print("Registros por año:")
        print(por_año.to_string(index=False))
        
        # Docentes únicos
        docentes_unicos = pd.read_sql_query('SELECT COUNT(DISTINCT dni) as count FROM docentes_data', conn).iloc[0, 0]
        print(f"\nDocentes únicos (por DNI): {docentes_unicos}")
        
        # RER
        por_rer = pd.read_sql_query('''
            SELECT rer, COUNT(*) as registros
            FROM docentes_data
            GROUP BY rer
            ORDER BY registros DESC
            LIMIT 10
        ''', conn)
        
        print("\nTop 10 RER por registros:")
        print(por_rer.to_string(index=False))
        
        # Estados de evaluación
        por_estado = pd.read_sql_query('''
            SELECT estado_evaluacion, COUNT(*) as registros
            FROM docentes_data
            GROUP BY estado_evaluacion
            ORDER BY registros DESC
        ''', conn)
        
        print("\nEstados de evaluación:")
        print(por_estado.to_string(index=False))
        
        conn.close()
        
        return {
            'total': total,
            'docentes_unicos': docentes_unicos,
            'por_año': por_año
        }
    
    def ejecutar_consolidacion_completa(self):
        """Ejecutar proceso completo de consolidación"""
        print("EXTRACTOR Y CONSOLIDADOR DE DATOS DOCENTES")
        print("=" * 60)
        
        # Paso 1: Verificar archivo
        if not self.verificar_archivo():
            return False
        
        # Paso 2: Extraer datos
        df_2023 = self.extraer_datos_2023()
        df_2024 = self.extraer_datos_2024()
        
        if df_2023 is None and df_2024 is None:
            print("ERROR: No se pudieron extraer datos de ninguna hoja")
            return False
        
        # Paso 3: Normalizar datos
        df_2023_norm = self.normalizar_datos_2023(df_2023)
        df_2024_norm = self.normalizar_datos_2024(df_2024)
        
        # Paso 4: Insertar en base de datos
        registros = self.insertar_datos_consolidados(df_2023_norm, df_2024_norm)
        
        # Paso 5: Generar reporte
        self.generar_reporte_consolidacion()
        
        print(f"\nCONSOLIDACIÓN COMPLETADA")
        print(f"Total registros procesados: {registros}")
        
        return registros > 0

def main():
    """Función principal"""
    extractor = ExtractorDocentes()
    exito = extractor.ejecutar_consolidacion_completa()
    
    if exito:
        print("\nExtracción y consolidación exitosa")
    else:
        print("\nERROR en extracción y consolidación")
    
    return exito

if __name__ == "__main__":
    main()