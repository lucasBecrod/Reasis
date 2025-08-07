#!/usr/bin/env python3
"""
Consolidador de Resultados Académicos V3 - Proyecto Reasis
Reconstruye la tabla resultados_academicos con estructura correcta desde Excel originales
Vincula correctamente con instituciones_educativas usando codigo_local
"""

import pandas as pd
import sqlite3
import os
from pathlib import Path
from datetime import datetime

class ConsolidadorResultadosV3:
    def __init__(self, db_path="reasis_database.db"):
        self.db_path = Path(db_path)
        if not self.db_path.exists():
            project_root = Path(__file__).parent.parent.parent
            self.db_path = project_root / "reasis_database.db"
        
        self.excel_path = Path(__file__).parent.parent.parent / "assets" / "Consultoria" / "DatosLucas" / "Matematica y Comunicación"
        
        # Configuración de archivos
        self.archivos_config = {
            'matematica': {
                'archivo': 'BD1- Matemática 2024.xlsx',
                'columna_resultado': 'R Matemática',
                'columna_codigo': 'ID. IE',
                'materia': 'Matemática'
            },
            'comunicacion': {
                'archivo': 'BD2- Comunicación 2024.xlsx', 
                'columna_resultado': 'R Comunicación',
                'columna_codigo': 'IE. ID',
                'materia': 'Comunicación'
            },
            'produccion': {
                'archivo': 'BD3 - Producción de textos 2024.xlsx',
                'columna_resultado': 'R Producción de textos',
                'columna_codigo': 'ID IE',
                'materia': 'Producción de textos'
            }
        }
        
        # Mapeo de niveles de logro
        self.mapeo_logros = {
            'Inicio': 1,
            'Proceso': 2, 
            'Satisfactorio': 3,
            'Destacado': 4
        }
    
    def leer_archivo_excel(self, config_materia):
        """Lee un archivo Excel y extrae los datos necesarios"""
        archivo_path = self.excel_path / config_materia['archivo']
        
        if not archivo_path.exists():
            raise FileNotFoundError(f"No se encontró: {archivo_path}")
        
        print(f"📖 Leyendo: {config_materia['archivo']}")
        
        try:
            # Leer solo las columnas necesarias
            df = pd.read_excel(archivo_path, sheet_name='DATA')
            
            # Verificar que existan las columnas necesarias
            columnas_requeridas = [
                'Estudiante', 'Región', 'Nivel', 'Grado', 
                'Institución Educativa', 'Ambito', 'Sexo', 
                config_materia['columna_resultado'], 'Año', 
                'ANALISIS', 'PADD-R', config_materia['columna_codigo'], 'ID2'
            ]
            
            columnas_faltantes = [col for col in columnas_requeridas if col not in df.columns]
            if columnas_faltantes:
                print(f"⚠️  Columnas faltantes en {config_materia['archivo']}: {columnas_faltantes}")
            
            # Seleccionar solo las primeras 13 columnas útiles (evitar columnas extras)
            if len(df.columns) > 13:
                df = df.iloc[:, :13]
            
            # Limpiar datos
            df = df.dropna(subset=[config_materia['columna_codigo']])  # Eliminar sin código IE
            df = df.dropna(subset=[config_materia['columna_resultado']])  # Eliminar sin resultado
            
            print(f"✅ Registros válidos: {len(df):,}")
            return df
            
        except Exception as e:
            print(f"❌ Error leyendo {config_materia['archivo']}: {e}")
            return None
    
    def normalizar_datos(self, df, config_materia):
        """Normaliza los datos a estructura estándar"""
        if df is None:
            return None
        
        print(f"🔄 Normalizando datos de {config_materia['materia']}...")
        
        # Crear DataFrame normalizado
        df_norm = pd.DataFrame()
        
        # Campos básicos (mapeo directo)
        df_norm['estudiante_id'] = df['Estudiante']
        df_norm['region'] = df['Región']
        df_norm['nivel_educativo'] = df['Nivel'] 
        df_norm['grado'] = df['Grado']
        df_norm['nombre_ie_original'] = df['Institución Educativa']
        df_norm['ambito'] = df['Ambito']
        df_norm['sexo'] = df['Sexo']
        df_norm['año'] = df['Año']
        df_norm['analisis_cobertura'] = df['ANALISIS']
        df_norm['padd_participacion'] = df['PADD-R']
        
        # Campo clave: código local
        df_norm['codigo_local'] = df[config_materia['columna_codigo']].astype(str).str.strip()
        
        # Extraer código local limpio del ID2 si es necesario
        if 'ID2' in df.columns:
            df_norm['id2_completo'] = df['ID2']
            # Extraer solo el número del inicio de ID2
            df_norm['codigo_local_id2'] = df['ID2'].astype(str).str.extract(r'^(\d+)')[0]
        
        # Campo de materia
        df_norm['materia'] = config_materia['materia']
        
        # Resultado (texto y numérico)
        resultado_col = config_materia['columna_resultado']
        df_norm['nivel_logro_texto'] = df[resultado_col]
        df_norm['nivel_logro_numerico'] = df[resultado_col].map(self.mapeo_logros)
        
        # Campos de control
        df_norm['fecha_procesamiento'] = datetime.now()
        df_norm['archivo_origen'] = config_materia['archivo']
        
        # Limpiar valores
        df_norm = df_norm.dropna(subset=['nivel_logro_numerico'])  # Solo registros con resultado válido
        
        print(f"✅ Registros normalizados: {len(df_norm):,}")
        return df_norm
    
    def vincular_con_instituciones(self, df_consolidado):
        """Vincula los datos académicos con instituciones_educativas usando codigo_local"""
        conn = sqlite3.connect(self.db_path)
        
        print("🔗 Vinculando con tabla instituciones_educativas...")
        
        # Obtener códigos locales de instituciones
        instituciones = pd.read_sql_query('''
            SELECT DISTINCT codigo_local, codigo_modular, nombre_institucion
            FROM instituciones_educativas 
            WHERE codigo_local IS NOT NULL
        ''', conn)
        
        print(f"📊 Códigos locales en instituciones: {len(instituciones)}")
        
        # Intentar múltiples estrategias de vinculación
        df_consolidado['codigo_modular'] = None
        df_consolidado['metodo_vinculacion'] = None
        
        vinculados = 0
        
        # Estrategia 1: Match directo con codigo_local
        for idx, row in df_consolidado.iterrows():
            codigo_local = str(row['codigo_local']).strip()
            
            # Buscar match exacto
            match = instituciones[instituciones['codigo_local'].astype(str).str.strip() == codigo_local]
            
            if len(match) > 0:
                df_consolidado.at[idx, 'codigo_modular'] = match.iloc[0]['codigo_modular']
                df_consolidado.at[idx, 'metodo_vinculacion'] = 'codigo_local_exacto'
                vinculados += 1
            else:
                # Estrategia 2: Buscar en codigo_local_id2 si existe
                if 'codigo_local_id2' in df_consolidado.columns and pd.notna(row['codigo_local_id2']):
                    codigo_id2 = str(row['codigo_local_id2']).strip()
                    match_id2 = instituciones[instituciones['codigo_local'].astype(str).str.strip() == codigo_id2]
                    
                    if len(match_id2) > 0:
                        df_consolidado.at[idx, 'codigo_modular'] = match_id2.iloc[0]['codigo_modular']
                        df_consolidado.at[idx, 'metodo_vinculacion'] = 'codigo_local_id2'
                        vinculados += 1
        
        print(f"✅ Registros vinculados: {vinculados:,} de {len(df_consolidado):,} ({vinculados/len(df_consolidado)*100:.1f}%)")
        
        conn.close()
        return df_consolidado
    
    def guardar_en_bd(self, df_final):
        """Guarda el DataFrame final en la base de datos"""
        conn = sqlite3.connect(self.db_path)
        
        print("💾 Guardando en base de datos...")
        
        # Eliminar tabla anterior
        conn.execute('DROP TABLE IF EXISTS resultados_academicos')
        
        # Crear nueva tabla con estructura correcta
        create_table_sql = '''
        CREATE TABLE resultados_academicos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            estudiante_id TEXT,
            region TEXT,
            nivel_educativo TEXT,
            grado TEXT,
            codigo_local TEXT,
            codigo_modular TEXT,
            nombre_ie_original TEXT,
            id2_completo TEXT,
            ambito TEXT,
            sexo TEXT,
            materia TEXT,
            nivel_logro_texto TEXT,
            nivel_logro_numerico INTEGER,
            año INTEGER,
            analisis_cobertura TEXT,
            padd_participacion TEXT,
            metodo_vinculacion TEXT,
            archivo_origen TEXT,
            fecha_procesamiento TIMESTAMP
        )
        '''
        
        conn.execute(create_table_sql)
        
        # Insertar datos
        df_final.to_sql('resultados_academicos', conn, if_exists='append', index=False)
        
        # Crear índices para mejorar rendimiento
        indices_sql = [
            'CREATE INDEX idx_codigo_local ON resultados_academicos(codigo_local)',
            'CREATE INDEX idx_codigo_modular ON resultados_academicos(codigo_modular)',
            'CREATE INDEX idx_materia_año ON resultados_academicos(materia, año)',
            'CREATE INDEX idx_nivel_grado ON resultados_academicos(nivel_educativo, grado)'
        ]
        
        for sql in indices_sql:
            conn.execute(sql)
        
        conn.commit()
        conn.close()
        
        print(f"✅ {len(df_final):,} registros guardados exitosamente")
    
    def generar_reporte_vinculacion(self):
        """Genera reporte de éxito de vinculación"""
        conn = sqlite3.connect(self.db_path)
        
        print("\n" + "="*60)
        print("📈 REPORTE DE VINCULACIÓN FINAL")
        print("="*60)
        
        # Estadísticas generales
        stats = pd.read_sql_query('''
            SELECT 
                COUNT(*) as total_registros,
                COUNT(codigo_modular) as vinculados,
                COUNT(*) - COUNT(codigo_modular) as sin_vincular,
                ROUND(COUNT(codigo_modular) * 100.0 / COUNT(*), 2) as porcentaje_vinculado
            FROM resultados_academicos
        ''', conn)
        
        print(f"📊 Total registros: {stats.iloc[0]['total_registros']:,}")
        print(f"✅ Vinculados: {stats.iloc[0]['vinculados']:,}")
        print(f"❌ Sin vincular: {stats.iloc[0]['sin_vincular']:,}")
        print(f"📈 Porcentaje éxito: {stats.iloc[0]['porcentaje_vinculado']}%")
        
        # Por materia
        por_materia = pd.read_sql_query('''
            SELECT 
                materia,
                COUNT(*) as total,
                COUNT(codigo_modular) as vinculados,
                ROUND(COUNT(codigo_modular) * 100.0 / COUNT(*), 2) as porcentaje
            FROM resultados_academicos
            GROUP BY materia
            ORDER BY total DESC
        ''', conn)
        
        print(f"\n📋 VINCULACIÓN POR MATERIA:")
        print(por_materia.to_string(index=False))
        
        # Métodos de vinculación
        metodos = pd.read_sql_query('''
            SELECT 
                metodo_vinculacion,
                COUNT(*) as registros
            FROM resultados_academicos
            WHERE metodo_vinculacion IS NOT NULL
            GROUP BY metodo_vinculacion
        ''', conn)
        
        if len(metodos) > 0:
            print(f"\n🔗 MÉTODOS DE VINCULACIÓN:")
            print(metodos.to_string(index=False))
        
        conn.close()
        return stats.iloc[0]['porcentaje_vinculado']
    
    def ejecutar_consolidacion_completa(self):
        """Ejecuta todo el proceso de consolidación"""
        print("🚀 INICIANDO CONSOLIDACIÓN COMPLETA DE RESULTADOS ACADÉMICOS V3")
        print("="*70)
        
        dataframes = []
        
        # Procesar cada archivo
        for nombre, config in self.archivos_config.items():
            print(f"\n📚 PROCESANDO: {config['materia'].upper()}")
            print("-" * 50)
            
            # Leer Excel
            df_raw = self.leer_archivo_excel(config)
            
            if df_raw is not None:
                # Normalizar
                df_norm = self.normalizar_datos(df_raw, config)
                
                if df_norm is not None:
                    dataframes.append(df_norm)
        
        if not dataframes:
            print("❌ No se pudo procesar ningún archivo")
            return False
        
        # Consolidar todos los DataFrames
        print(f"\n🔄 CONSOLIDANDO {len(dataframes)} ARCHIVOS...")
        df_consolidado = pd.concat(dataframes, ignore_index=True)
        print(f"✅ Total registros consolidados: {len(df_consolidado):,}")
        
        # Vincular con instituciones
        df_final = self.vincular_con_instituciones(df_consolidado)
        
        # Guardar en BD
        self.guardar_en_bd(df_final)
        
        # Generar reporte
        porcentaje_exito = self.generar_reporte_vinculacion()
        
        print(f"\n🎯 CONSOLIDACIÓN COMPLETADA")
        print(f"Éxito de vinculación: {porcentaje_exito}%")
        
        return porcentaje_exito > 50  # Considerar exitoso si >50% vinculado

def main():
    """Función principal"""
    try:
        consolidador = ConsolidadorResultadosV3()
        exito = consolidador.ejecutar_consolidacion_completa()
        
        if exito:
            print("✅ Proceso completado exitosamente")
        else:
            print("⚠️ Proceso completado con baja tasa de vinculación")
            
    except Exception as e:
        print(f"❌ Error en consolidación: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()