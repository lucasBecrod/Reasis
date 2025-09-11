#!/usr/bin/env python3
"""
Extractor de Datos Docentes V2 - Proyecto Reasis  
Versión corregida con concatenación correcta de nombres y notas renombradas
"""

import pandas as pd
import sqlite3
from pathlib import Path
from datetime import datetime

class ExtractorDocentesV2:
    def __init__(self):
        self.excel_path = Path("assets/Consultoria/Información actualizada/2. PADD Consolidado.xlsx")
        self.db_path = Path("reasis_database.db")
    
    def recrear_tabla_docentes(self):
        """Recrear tabla docentes con estructura corregida"""
        print("RECREANDO ESTRUCTURA TABLA DOCENTES")
        print("=" * 50)
        
        conn = sqlite3.connect(self.db_path)
        
        # Eliminar tabla anterior si existe
        conn.execute('DROP TABLE IF EXISTS docentes_data')
        
        # Crear nueva tabla con estructura corregida
        create_sql = """
        CREATE TABLE docentes_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            
            -- Identificación del docente
            dni TEXT NOT NULL,
            nombre_completo TEXT,
            genero_personal TEXT,  -- Género como sexo de la persona
            
            -- Información institucional
            rer TEXT,
            institucion_actual TEXT,
            codigo_modular_actual TEXT,
            nivel_educativo TEXT,
            
            -- Continuidad/Estabilidad
            continua_rer TEXT,
            institucion_continua TEXT,
            codigo_modular_continua TEXT,
            
            -- Notas de evaluaciones académicas (solo 2023)
            nota_matematica REAL,
            nota_comunicacion REAL,
            nota_digital REAL,
            nota_genero REAL,  -- Competencia transversal género
            
            -- Estado y año
            estado_evaluacion TEXT,
            año INTEGER NOT NULL,
            
            -- Vinculación con tabla instituciones
            codigo_modular_vinculado TEXT,
            metodo_vinculacion TEXT,
            
            -- Campos de control
            archivo_origen TEXT,
            fecha_procesamiento TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        conn.execute(create_sql)
        
        # Crear índices
        indices = [
            'CREATE INDEX idx_docentes_dni ON docentes_data(dni)',
            'CREATE INDEX idx_docentes_codigo_modular ON docentes_data(codigo_modular_actual)',
            'CREATE INDEX idx_docentes_año ON docentes_data(año)',
            'CREATE INDEX idx_docentes_rer ON docentes_data(rer)',
            'CREATE INDEX idx_docentes_vinculado ON docentes_data(codigo_modular_vinculado)'
        ]
        
        for idx_sql in indices:
            conn.execute(idx_sql)
        
        conn.commit()
        conn.close()
        
        print("- Tabla docentes_data recreada con estructura correcta")
        print("- Campos de notas renombrados para evitar confusion")
        print("- Sin restriccion UNIQUE - mantiene todos los datos puros")
    
    def verificar_archivo(self):
        """Verificar que el archivo Excel existe y tiene las hojas necesarias"""
        print("\nVERIFICACIÓN DE ARCHIVO EXCEL")
        print("=" * 50)
        
        if not self.excel_path.exists():
            print(f"ERROR: Archivo no encontrado: {self.excel_path}")
            return False
        
        print(f"Archivo encontrado: {self.excel_path.name}")
        
        try:
            excel_file = pd.ExcelFile(self.excel_path)
            hojas = excel_file.sheet_names
            print(f"Hojas disponibles: {hojas}")
            
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
        """Extraer datos de la hoja 2023 con concatenación correcta"""
        print("\nEXTRACCIÓN DATOS 2023")
        print("-" * 30)
        
        try:
            df_2023 = pd.read_excel(self.excel_path, sheet_name='2023')
            print(f"Registros encontrados: {len(df_2023)}")
            print(f"Columnas: {len(df_2023.columns)}")
            
            # Mostrar columnas clave para verificar
            print("Columnas clave encontradas:")
            columnas_clave = ['Apellidos', 'Nombres', 'Número de documento', 'GENERO', 'MATEMATICA', 'COMUNICACIÓN', 'DIGITAL']
            for col in columnas_clave:
                if col in df_2023.columns:
                    print(f"  OK {col}")
                else:
                    print(f"  FALTA {col}")
            
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
            
            # Mostrar columnas clave
            columnas_clave = ['DNI', 'DOCENTES PARTICIPANTES', 'ESTADO']
            for col in columnas_clave:
                if col in df_2024.columns:
                    print(f"  OK {col}")
                else:
                    print(f"  FALTA {col}")
            
            return df_2024
            
        except Exception as e:
            print(f"ERROR extrayendo datos 2024: {e}")
            return None
    
    def normalizar_datos_2023(self, df_2023):
        """Normalizar datos de 2023 con concatenación correcta Apellidos + Nombres"""
        print("\nNORMALIZANDO DATOS 2023")
        print("-" * 30)
        
        if df_2023 is None:
            return None
        
        # Limpiar datos - remover filas completamente vacías
        df_2023 = df_2023.dropna(how='all')
        
        try:
            df_norm = pd.DataFrame()
            columnas = df_2023.columns.tolist()
            print(f"Procesando {len(df_2023)} registros de 2023")
            
            # DNI - limpiar correctamente (remover .0 de Excel)
            if 'Número de documento' in columnas:
                df_norm['dni'] = pd.to_numeric(df_2023['Número de documento'], errors='coerce').fillna(0).astype(int).astype(str)
                df_norm = df_norm[df_norm['dni'] != '0']  # Remover valores 0 (NaN convertidos)
                print(f"DNI procesados: {len(df_norm)}")
            
            # NOMBRE COMPLETO - Concatenación correcta: Apellidos + Nombres (con espacios)
            nombres_col = None
            apellidos_col = None
            
            # Buscar columnas con nombres exactos (pueden tener espacios)
            for col in columnas:
                if 'Nombres' in col:
                    nombres_col = col
                if 'Apellidos' in col:
                    apellidos_col = col
            
            if apellidos_col and nombres_col:
                apellidos = df_2023[apellidos_col].fillna('').astype(str).str.strip()
                nombres = df_2023[nombres_col].fillna('').astype(str).str.strip()
                # Concatenar: Apellidos + ", " + Nombres (formato estándar)
                df_norm['nombre_completo'] = apellidos + ', ' + nombres
                # Limpiar casos donde solo hay un campo
                df_norm['nombre_completo'] = df_norm['nombre_completo'].str.replace(r'^, |, $', '', regex=True)
                print(f"Nombres completos creados: {len(df_norm[df_norm['nombre_completo'] != ''])}")
            else:
                print(f"ADVERTENCIA: No se encontraron columnas de nombres")
                df_norm['nombre_completo'] = None
            
            # Género personal (sexo de la persona, no competencia)
            genero_personal_col = None
            for col in columnas:
                if 'Género' in col:  # Con tilde
                    genero_personal_col = col
                    break
            
            if genero_personal_col:
                df_norm['genero_personal'] = df_2023[genero_personal_col]
                print(f"Género personal procesado desde: {genero_personal_col}")
            else:
                # Si no hay columna con tilde, verificar si GENERO es texto o número
                if 'GENERO' in columnas:
                    valores_genero = df_2023['GENERO'].dropna().unique()[:5]
                    print(f"Verificando valores en GENERO: {valores_genero}")
                    # Si son números, es competencia; si son texto, es sexo
                    try:
                        pd.to_numeric(valores_genero, errors='raise')
                        # Son números = competencia, no asignar a genero_personal
                        df_norm['genero_personal'] = None
                        print("GENERO contiene números - es competencia, no género personal")
                    except:
                        # Son texto = sexo de la persona
                        df_norm['genero_personal'] = df_2023['GENERO']
                        print("GENERO contiene texto - es género personal")
                else:
                    df_norm['genero_personal'] = None
            
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
            
            # NOTAS DE EVALUACIÓN (renombradas correctamente)
            # Buscar columnas exactas que pueden tener espacios
            matematica_col = None
            comunicacion_col = None
            digital_col = None
            genero_nota_col = None
            
            for col in columnas:
                if 'MATEMATICA' in col:
                    matematica_col = col
                if 'COMUNICACIÓN' in col:
                    comunicacion_col = col
                if 'DIGITAL' in col:
                    digital_col = col
                if col == 'GENERO':  # Exacto para evitar confusión con Género personal
                    genero_nota_col = col
            
            if matematica_col:
                df_norm['nota_matematica'] = pd.to_numeric(df_2023[matematica_col], errors='coerce')
                print(f"Notas matemática procesadas desde: {matematica_col}")
                
            if comunicacion_col:
                df_norm['nota_comunicacion'] = pd.to_numeric(df_2023[comunicacion_col], errors='coerce')
                print(f"Notas comunicación procesadas desde: {comunicacion_col}")
                
            if digital_col:
                df_norm['nota_digital'] = pd.to_numeric(df_2023[digital_col], errors='coerce')
                print(f"Notas digital procesadas desde: {digital_col}")
                
            if genero_nota_col:
                # Solo si son valores numéricos (competencia)
                try:
                    df_norm['nota_genero'] = pd.to_numeric(df_2023[genero_nota_col], errors='coerce')
                    print(f"Notas género (competencia) procesadas desde: {genero_nota_col}")
                except:
                    df_norm['nota_genero'] = None
            
            # Estado
            if 'ESTADO' in columnas:
                df_norm['estado_evaluacion'] = df_2023['ESTADO']
            
            # Año y origen
            df_norm['año'] = 2023
            df_norm['archivo_origen'] = '2023'
            
            print(f"Registros normalizados 2023: {len(df_norm)}")
            
            # Mostrar muestra
            if len(df_norm) > 0:
                print("Muestra de datos 2023:")
                muestra = df_norm[['dni', 'nombre_completo', 'nota_matematica', 'nota_comunicacion']].head(3)
                print(muestra.to_string(index=False))
            
            return df_norm
            
        except Exception as e:
            print(f"ERROR normalizando datos 2023: {e}")
            import traceback
            print(traceback.format_exc())
            return None
    
    def normalizar_datos_2024(self, df_2024):
        """Normalizar datos de 2024"""
        print("\nNORMALIZANDO DATOS 2024")
        print("-" * 30)
        
        if df_2024 is None:
            return None
        
        # Limpiar datos - remover filas completamente vacías
        df_2024 = df_2024.dropna(how='all')
        
        try:
            df_norm = pd.DataFrame()
            columnas = df_2024.columns.tolist()
            print(f"Procesando {len(df_2024)} registros de 2024")
            
            # DNI - limpiar correctamente
            if 'DNI' in columnas:
                df_norm['dni'] = pd.to_numeric(df_2024['DNI'], errors='coerce').fillna(0).astype(int).astype(str)
                df_norm = df_norm[df_norm['dni'] != '0']
                print(f"DNI procesados: {len(df_norm)}")
            
            # NOMBRE COMPLETO - Usar directamente columna DOCENTES PARTICIPANTES
            if 'DOCENTES PARTICIPANTES' in columnas:
                df_norm['nombre_completo'] = df_2024['DOCENTES PARTICIPANTES'].astype(str).str.strip()
                print(f"Nombres completos asignados desde DOCENTES PARTICIPANTES")
            
            # Género personal - no disponible en 2024
            df_norm['genero_personal'] = None
            
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
            
            # Notas de evaluación - no disponibles en 2024
            df_norm['nota_matematica'] = None
            df_norm['nota_comunicacion'] = None
            df_norm['nota_digital'] = None
            df_norm['nota_genero'] = None
            
            # Estado
            if 'ESTADO' in columnas:
                df_norm['estado_evaluacion'] = df_2024['ESTADO']
            
            # Año y origen
            df_norm['año'] = 2024
            df_norm['archivo_origen'] = '2024'
            
            print(f"Registros normalizados 2024: {len(df_norm)}")
            
            # Mostrar muestra
            if len(df_norm) > 0:
                print("Muestra de datos 2024:")
                muestra = df_norm[['dni', 'nombre_completo', 'rer', 'estado_evaluacion']].head(3)
                print(muestra.to_string(index=False))
            
            return df_norm
            
        except Exception as e:
            print(f"ERROR normalizando datos 2024: {e}")
            import traceback
            print(traceback.format_exc())
            return None
    
    def insertar_datos_consolidados(self, df_2023_norm, df_2024_norm):
        """Insertar todos los datos sin filtrar duplicados"""
        print("\nINSERTANDO DATOS EN docentes_data (SIN FILTRAR DUPLICADOS)")
        print("-" * 60)
        
        conn = sqlite3.connect(self.db_path)
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
        
        # Insertar datos 2024 - SIN restricción de duplicados
        if df_2024_norm is not None:
            try:
                df_2024_norm.to_sql('docentes_data', conn, if_exists='append', index=False)
                registros_2024 = len(df_2024_norm)
                registros_insertados += registros_2024
                print(f"Registros 2024 insertados: {registros_2024}")
            except Exception as e:
                print(f"ERROR insertando 2024: {e}")
        
        conn.commit()
        conn.close()
        
        print(f"Total registros insertados: {registros_insertados}")
        return registros_insertados
    
    def generar_reporte_final(self):
        """Generar reporte final de consolidación"""
        print("\nREPORTE FINAL - CONSOLIDACIÓN DOCENTES V2")
        print("=" * 60)
        
        conn = sqlite3.connect(self.db_path)
        
        # Estadísticas generales
        total = pd.read_sql_query('SELECT COUNT(*) as count FROM docentes_data', conn).iloc[0, 0]
        
        por_año = pd.read_sql_query('''
            SELECT año, COUNT(*) as registros
            FROM docentes_data
            GROUP BY año
            ORDER BY año
        ''', conn)
        
        print(f"Total registros consolidados: {total:,}")
        print("Registros por año:")
        print(por_año.to_string(index=False))
        
        # Verificar nombres
        nombres_completos = pd.read_sql_query('''
            SELECT COUNT(*) as total, COUNT(nombre_completo) as con_nombre
            FROM docentes_data
            WHERE nombre_completo IS NOT NULL AND nombre_completo != ''
        ''', conn).iloc[0]
        
        print(f"\nNombres completos: {nombres_completos['con_nombre']}/{nombres_completos['total']} ({nombres_completos['con_nombre']/nombres_completos['total']*100:.1f}%)")
        
        # Verificar notas (solo 2023)
        notas_2023 = pd.read_sql_query('''
            SELECT 
                COUNT(*) as total_2023,
                COUNT(nota_matematica) as con_matematica,
                COUNT(nota_comunicacion) as con_comunicacion,
                COUNT(nota_digital) as con_digital,
                COUNT(nota_genero) as con_genero
            FROM docentes_data
            WHERE año = 2023
        ''', conn).iloc[0]
        
        if notas_2023['total_2023'] > 0:
            print(f"\nNotas disponibles 2023:")
            print(f"  Matemática: {notas_2023['con_matematica']}/{notas_2023['total_2023']}")
            print(f"  Comunicación: {notas_2023['con_comunicacion']}/{notas_2023['total_2023']}")
            print(f"  Digital: {notas_2023['con_digital']}/{notas_2023['total_2023']}")  
            print(f"  Género (competencia): {notas_2023['con_genero']}/{notas_2023['total_2023']}")
        
        conn.close()
        
        return {'total': total, 'por_año': por_año.to_dict('records')}
    
    def ejecutar_consolidacion_completa(self):
        """Ejecutar proceso completo de consolidación V2"""
        print("EXTRACTOR Y CONSOLIDADOR DE DATOS DOCENTES V2")
        print("=" * 70)
        
        # Paso 1: Recrear tabla con estructura correcta
        self.recrear_tabla_docentes()
        
        # Paso 2: Verificar archivo
        if not self.verificar_archivo():
            return False
        
        # Paso 3: Extraer datos
        df_2023 = self.extraer_datos_2023()
        df_2024 = self.extraer_datos_2024()
        
        if df_2023 is None and df_2024 is None:
            print("ERROR: No se pudieron extraer datos de ninguna hoja")
            return False
        
        # Paso 4: Normalizar datos con correcciones
        df_2023_norm = self.normalizar_datos_2023(df_2023)
        df_2024_norm = self.normalizar_datos_2024(df_2024)
        
        # Paso 5: Insertar todos los datos
        registros = self.insertar_datos_consolidados(df_2023_norm, df_2024_norm)
        
        # Paso 6: Generar reporte
        self.generar_reporte_final()
        
        print(f"\nCONSOLIDACIÓN V2 COMPLETADA")
        print("=" * 40)
        print(f"- Datos puros mantenidos (sin filtrar duplicados)")
        print(f"- Nombres 2023: Apellidos + Nombres")
        print(f"- Nombres 2024: DOCENTES PARTICIPANTES")
        print(f"- Notas renombradas: nota_matematica, nota_comunicacion, etc.")
        print(f"- Total registros procesados: {registros}")
        
        return registros > 0

def main():
    """Función principal"""
    extractor = ExtractorDocentesV2()
    exito = extractor.ejecutar_consolidacion_completa()
    
    if exito:
        print("\nExtracción y consolidación V2 exitosa")
    else:
        print("\nERROR en extracción y consolidación V2")
    
    return exito

if __name__ == "__main__":
    main()