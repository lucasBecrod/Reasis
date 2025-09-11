#!/usr/bin/env python3
"""
Vinculador Inteligente de Instituciones - Proyecto Reasis
Resuelve el problema crítico de vincular datos académicos con instituciones educativas

Problema: 99.2% de registros académicos no tienen codigo_modular
Solución: Múltiples estrategias de matching + validación manual
"""

import sqlite3
import pandas as pd
from difflib import get_close_matches
import re
from pathlib import Path

class VinculadorInstituciones:
    def __init__(self, db_path="reasis_database.db"):
        self.db_path = Path(db_path)
        if not self.db_path.exists():
            # Buscar en directorio raíz del proyecto
            project_root = Path(__file__).parent.parent.parent
            self.db_path = project_root / "reasis_database.db"
        
        if not self.db_path.exists():
            raise FileNotFoundError(f"No se encontró la base de datos: {self.db_path}")
    
    def get_connection(self):
        return sqlite3.connect(self.db_path)
    
    def analizar_problema(self):
        """Analiza en detalle el problema de vinculación"""
        conn = self.get_connection()
        
        print("=" * 70)
        print("🔍 ANÁLISIS DETALLADO DEL PROBLEMA DE VINCULACIÓN")
        print("=" * 70)
        
        # Estadísticas generales
        total_acad = pd.read_sql_query('SELECT COUNT(*) as count FROM resultados_academicos', conn).iloc[0,0]
        sin_codigo = pd.read_sql_query('SELECT COUNT(*) as count FROM resultados_academicos WHERE codigo_modular IS NULL', conn).iloc[0,0]
        
        print(f"📊 Registros académicos totales: {total_acad:,}")
        print(f"❌ Sin código_modular: {sin_codigo:,} ({sin_codigo/total_acad*100:.1f}%)")
        
        # Códigos únicos
        codigos_unicos = pd.read_sql_query('''
            SELECT COUNT(DISTINCT codigo_ie) as count 
            FROM resultados_academicos 
            WHERE codigo_ie IS NOT NULL
        ''', conn).iloc[0,0]
        
        instituciones_total = pd.read_sql_query('SELECT COUNT(*) as count FROM instituciones_educativas', conn).iloc[0,0]
        
        print(f"🏫 Códigos únicos en datos académicos: {codigos_unicos}")
        print(f"🏛️ Instituciones en BD oficial: {instituciones_total}")
        
        # Muestra de códigos problemáticos
        print(f"\n📋 MUESTRA DE CÓDIGOS SIN VINCULAR:")
        muestra = pd.read_sql_query('''
            SELECT codigo_ie, nombre_ie, COUNT(*) as estudiantes
            FROM resultados_academicos 
            WHERE codigo_ie IS NOT NULL 
            GROUP BY codigo_ie, nombre_ie
            ORDER BY estudiantes DESC
        ''', conn)
        
        print(muestra.to_string(index=False))
        
        conn.close()
        return {
            'total_academicos': total_acad,
            'sin_codigo': sin_codigo,
            'codigos_unicos': codigos_unicos,
            'instituciones_total': instituciones_total
        }
    
    def buscar_coincidencias_exactas(self):
        """Busca coincidencias exactas por código o nombre"""
        conn = self.get_connection()
        
        print(f"\n🎯 BÚSQUEDA DE COINCIDENCIAS EXACTAS")
        print("-" * 50)
        
        # Estrategia 1: Código directo (codigo_ie = codigo_modular)
        coincidencias_codigo = pd.read_sql_query('''
            SELECT DISTINCT 
                r.codigo_ie,
                r.nombre_ie,
                i.codigo_modular,
                i.nombre_institucion,
                COUNT(r.id) as estudiantes
            FROM resultados_academicos r
            JOIN instituciones_educativas i ON r.codigo_ie = i.codigo_modular
            GROUP BY r.codigo_ie, r.nombre_ie, i.codigo_modular, i.nombre_institucion
        ''', conn)
        
        print(f"✅ Coincidencias por código directo: {len(coincidencias_codigo)}")
        if len(coincidencias_codigo) > 0:
            print(coincidencias_codigo.to_string(index=False))
        
        # Estrategia 2: Nombre exacto (normalizado)
        coincidencias_nombre = pd.read_sql_query('''
            SELECT DISTINCT 
                r.codigo_ie,
                r.nombre_ie,
                i.codigo_modular,
                i.nombre_institucion
            FROM resultados_academicos r
            JOIN instituciones_educativas i ON UPPER(TRIM(r.nombre_ie)) = UPPER(TRIM(i.nombre_institucion))
            WHERE r.codigo_ie IS NOT NULL
        ''', conn)
        
        print(f"\n✅ Coincidencias por nombre exacto: {len(coincidencias_nombre)}")
        if len(coincidencias_nombre) > 0:
            print(coincidencias_nombre.to_string(index=False))
        
        conn.close()
        return len(coincidencias_codigo) + len(coincidencias_nombre)
    
    def buscar_coincidencias_fuzzy(self, threshold=0.7):
        """Busca coincidencias usando fuzzy matching"""
        conn = self.get_connection()
        
        print(f"\n🔍 BÚSQUEDA FUZZY (threshold={threshold})")
        print("-" * 50)
        
        # Obtener datos
        instituciones = pd.read_sql_query('''
            SELECT codigo_modular, nombre_institucion,
                   UPPER(TRIM(nombre_institucion)) as nombre_norm
            FROM instituciones_educativas 
        ''', conn)
        
        academicos = pd.read_sql_query('''
            SELECT DISTINCT codigo_ie, nombre_ie,
                   UPPER(TRIM(nombre_ie)) as nombre_norm,
                   COUNT(*) as estudiantes
            FROM resultados_academicos 
            WHERE codigo_ie IS NOT NULL AND nombre_ie IS NOT NULL
            GROUP BY codigo_ie, nombre_ie
        ''', conn)
        
        nombres_inst_list = instituciones['nombre_norm'].tolist()
        coincidencias_fuzzy = []
        
        for _, acad in academicos.iterrows():
            matches = get_close_matches(acad['nombre_norm'], nombres_inst_list, n=1, cutoff=threshold)
            if matches:
                match_idx = nombres_inst_list.index(matches[0])
                inst_match = instituciones.iloc[match_idx]
                
                coincidencias_fuzzy.append({
                    'codigo_ie': acad['codigo_ie'],
                    'nombre_ie': acad['nombre_ie'],
                    'codigo_modular': inst_match['codigo_modular'],
                    'nombre_institucion': inst_match['nombre_institucion'],
                    'estudiantes': acad['estudiantes'],
                    'similitud': 'fuzzy'
                })
        
        print(f"🎯 Coincidencias fuzzy encontradas: {len(coincidencias_fuzzy)}")
        
        if coincidencias_fuzzy:
            df_fuzzy = pd.DataFrame(coincidencias_fuzzy)
            print("\nPrimeras 10 coincidencias:")
            print(df_fuzzy.head(10).to_string(index=False))
            
            # Guardar todas las coincidencias
            self.guardar_mapeos(df_fuzzy, 'fuzzy')
        
        conn.close()
        return len(coincidencias_fuzzy)
    
    def buscar_por_codigo_local(self):
        """Busca coincidencias usando codigo_local de instituciones"""
        conn = self.get_connection()
        
        print(f"\n🏷️ BÚSQUEDA POR CÓDIGO LOCAL")
        print("-" * 50)
        
        coincidencias_local = pd.read_sql_query('''
            SELECT DISTINCT 
                r.codigo_ie,
                r.nombre_ie,
                i.codigo_modular,
                i.codigo_local,
                i.nombre_institucion,
                COUNT(r.id) as estudiantes
            FROM resultados_academicos r
            JOIN instituciones_educativas i ON r.codigo_ie = i.codigo_local
            GROUP BY r.codigo_ie, r.nombre_ie, i.codigo_modular, i.codigo_local, i.nombre_institucion
        ''', conn)
        
        print(f"🎯 Coincidencias por código local: {len(coincidencias_local)}")
        if len(coincidencias_local) > 0:
            print(coincidencias_local.to_string(index=False))
            self.guardar_mapeos(coincidencias_local, 'codigo_local')
        
        conn.close()
        return len(coincidencias_local)
    
    def guardar_mapeos(self, mapeos_df, metodo):
        """Guarda los mapeos encontrados en la tabla mapeo_codigos_ie"""
        conn = self.get_connection()
        
        # Limpiar tabla anterior
        conn.execute('DELETE FROM mapeo_codigos_ie WHERE metodo_encontrado = ?', (metodo,))
        
        # Insertar nuevos mapeos
        for _, row in mapeos_df.iterrows():
            conn.execute('''
                INSERT OR REPLACE INTO mapeo_codigos_ie 
                (codigo_local, nivel_educativo, codigo_modular, nombre_ie_encontrado, metodo_encontrado)
                VALUES (?, ?, ?, ?, ?)
            ''', (row['codigo_ie'], 'Todos', row['codigo_modular'], row['nombre_institucion'], metodo))
        
        conn.commit()
        conn.close()
        print(f"💾 Guardados {len(mapeos_df)} mapeos con método '{metodo}'")
    
    def aplicar_mapeos(self):
        """Aplica los mapeos encontrados a la tabla resultados_academicos"""
        conn = self.get_connection()
        
        print(f"\n🔄 APLICANDO MAPEOS A RESULTADOS_ACADEMICOS")
        print("-" * 50)
        
        # Contar registros antes
        sin_codigo_antes = pd.read_sql_query(
            'SELECT COUNT(*) as count FROM resultados_academicos WHERE codigo_modular IS NULL', 
            conn
        ).iloc[0,0]
        
        # Aplicar mapeos
        updated = conn.execute('''
            UPDATE resultados_academicos 
            SET codigo_modular = (
                SELECT codigo_modular 
                FROM mapeo_codigos_ie 
                WHERE mapeo_codigos_ie.codigo_local = resultados_academicos.codigo_ie
                AND mapeo_codigos_ie.codigo_modular IS NOT NULL
            )
            WHERE codigo_modular IS NULL 
            AND codigo_ie IN (SELECT codigo_local FROM mapeo_codigos_ie WHERE codigo_modular IS NOT NULL)
        ''').rowcount
        
        conn.commit()
        
        # Contar registros después
        sin_codigo_despues = pd.read_sql_query(
            'SELECT COUNT(*) as count FROM resultados_academicos WHERE codigo_modular IS NULL', 
            conn
        ).iloc[0,0]
        
        print(f"✅ Registros actualizados: {updated:,}")
        print(f"📊 Sin código antes: {sin_codigo_antes:,}")
        print(f"📊 Sin código después: {sin_codigo_despues:,}")
        print(f"📈 Mejora: {sin_codigo_antes - sin_codigo_despues:,} registros vinculados")
        
        conn.close()
        return updated
    
    def generar_reporte(self):
        """Genera reporte completo del estado de vinculación"""
        conn = self.get_connection()
        
        print(f"\n📈 REPORTE FINAL DE VINCULACIÓN")
        print("=" * 60)
        
        # Estadísticas finales
        total = pd.read_sql_query('SELECT COUNT(*) as count FROM resultados_academicos', conn).iloc[0,0]
        vinculados = pd.read_sql_query('SELECT COUNT(*) as count FROM resultados_academicos WHERE codigo_modular IS NOT NULL', conn).iloc[0,0]
        sin_vincular = total - vinculados
        
        print(f"📊 Total registros académicos: {total:,}")
        print(f"✅ Registros vinculados: {vinculados:,} ({vinculados/total*100:.1f}%)")
        print(f"❌ Sin vincular: {sin_vincular:,} ({sin_vincular/total*100:.1f}%)")
        
        # Resumen por método
        mapeos_por_metodo = pd.read_sql_query('''
            SELECT metodo_encontrado, COUNT(*) as mapeos
            FROM mapeo_codigos_ie 
            WHERE codigo_modular IS NOT NULL
            GROUP BY metodo_encontrado
        ''', conn)
        
        if len(mapeos_por_metodo) > 0:
            print(f"\n🛠️ MAPEOS POR MÉTODO:")
            print(mapeos_por_metodo.to_string(index=False))
        
        conn.close()
        return {
            'total': total,
            'vinculados': vinculados,
            'sin_vincular': sin_vincular,
            'porcentaje_exito': vinculados/total*100
        }
    
    def ejecutar_vinculacion_completa(self):
        """Ejecuta todo el proceso de vinculación"""
        print("🚀 INICIANDO PROCESO DE VINCULACIÓN COMPLETA")
        print("=" * 70)
        
        # Paso 1: Análisis del problema
        stats = self.analizar_problema()
        
        # Paso 2: Búsquedas
        exactas = self.buscar_coincidencias_exactas()
        fuzzy = self.buscar_coincidencias_fuzzy(threshold=0.7)
        locales = self.buscar_por_codigo_local()
        
        # Paso 3: Aplicar mapeos
        if exactas + fuzzy + locales > 0:
            self.aplicar_mapeos()
        
        # Paso 4: Reporte final
        resultado = self.generar_reporte()
        
        print(f"\n🎯 PROCESO COMPLETADO")
        print(f"Mejora lograda: {stats['sin_codigo']} → {resultado['sin_vincular']} registros sin vincular")
        print(f"Éxito: {resultado['porcentaje_exito']:.1f}% de registros vinculados")
        
        return resultado

def main():
    """Función principal"""
    try:
        vinculador = VinculadorInstituciones()
        resultado = vinculador.ejecutar_vinculacion_completa()
        return resultado
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    main()