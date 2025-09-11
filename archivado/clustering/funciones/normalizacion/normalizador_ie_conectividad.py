#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NORMALIZADOR IE CONECTIVIDAD - Usando IA Gemini para matching de nombres
Estrategia: Normalizar nombres escritos manualmente usando base de datos de referencia
"""
import pandas as pd
import sqlite3
import json
from gemini_optimizer import GeminiOptimizer
from typing import Optional, Dict, List

class NormalizadorIEConectividad:
    """Clase para normalizar nombres de IE usando IA Gemini"""
    
    def __init__(self, db_path: str = 'reasis_database.db'):
        self.db_path = db_path
        self.optimizer = GeminiOptimizer()
        print(f"[OK] Inicializado con API key primary: {self.optimizer.api_key_primary[:20]}...")
        print(f"[OK] API key backup disponible: {self.optimizer.api_key_backup[:20]}...")
        self.ie_referencia = None
        
    def cargar_referencia_ie(self) -> Dict:
        """Carga todas las IE de referencia desde la base de datos"""
        print("Cargando IE de referencia desde base de datos...")
        
        conn = sqlite3.connect(self.db_path)
        
        # Obtener todas las IE con datos relevantes para matching
        query = """
        SELECT 
            codigo_modular,
            codigo_local,
            nombre_institucion,
            distrito,
            provincia,
            region,
            modalidad,
            nivel_educativo,
            es_fya,
            codigo_red
        FROM instituciones_educativas
        WHERE es_fya = 1
        ORDER BY codigo_modular
        """
        
        df_ie = pd.read_sql_query(query, conn)
        conn.close()
        
        print(f"[OK] Cargadas {len(df_ie)} instituciones Fe y Alegría de referencia")
        
        # Convertir a lista de diccionarios para JSON
        ie_list = []
        for _, row in df_ie.iterrows():
            ie_dict = {
                "codigo_modular": row['codigo_modular'],
                "codigo_local": str(row['codigo_local']) if pd.notna(row['codigo_local']) else None,
                "nombre": row['nombre_institucion'],
                "distrito": row['distrito'],
                "provincia": row['provincia'],
                "region": row['region'],
                "modalidad": row['modalidad'],
                "nivel": row['nivel_educativo'],
                "red": row['codigo_red']
            }
            ie_list.append(ie_dict)
        
        self.ie_referencia = {
            "total_instituciones": len(ie_list),
            "instituciones": ie_list
        }
        
        return self.ie_referencia
    
    def construir_prompt_matching(self, nombre_manual: str, red_fya: str) -> str:
        """Construye el prompt optimizado para matching con Gemini"""
        
        ie_json = json.dumps(self.ie_referencia, indent=2, ensure_ascii=False)
        
        prompt = f"""
ROL: Eres un especialista en normalización de bases de datos educativas Fe y Alegría.

OBJETIVO: Identificar a qué institución educativa corresponde un nombre escrito manualmente.

DATOS DE REFERENCIA:
{ie_json}

NOMBRE MANUAL A IDENTIFICAR: "{nombre_manual}"
RED FE Y ALEGRÍA: "{red_fya}"

INSTRUCCIONES CRÍTICAS:
1. Analiza el nombre manual y encuentra la institución educativa más probable
2. Considera códigos modulares, códigos locales, nombres parciales, números
3. El nombre manual puede estar incompleto, tener errores de tipeo, o usar abreviaciones
4. Prioriza coincidencias que estén en la misma red Fe y Alegría si es posible
5. Responde ÚNICAMENTE con el código modular de la institución identificada
6. Si no encuentras coincidencia clara, responde "NO_MATCH"
7. NO agregues explicaciones, solo el código modular

EJEMPLOS DE FORMATO DE RESPUESTA:
- Si identificas la institución: "1234567"
- Si no hay coincidencia clara: "NO_MATCH"

RESPUESTA:"""
        
        return prompt
    
    def identificar_ie_con_gemini(self, nombre_manual: str, red_fya: str) -> Optional[str]:
        """Usa Gemini para identificar la IE correspondiente al nombre manual"""
        
        if not self.ie_referencia:
            print("[ERROR] No hay datos de referencia cargados")
            return None
            
        # Construir prompt
        prompt = self.construir_prompt_matching(nombre_manual, red_fya)
        
        # Llamar a Gemini
        respuesta = self.optimizer.call_gemini(prompt, temperature=0.0)
        
        if not respuesta:
            return None
            
        # Limpiar respuesta
        respuesta_clean = respuesta.strip().strip('"').strip("'")
        
        # Validar formato de respuesta
        if respuesta_clean == "NO_MATCH":
            return "NO_MATCH"
        elif respuesta_clean.isdigit() and len(respuesta_clean) == 7:
            return respuesta_clean
        else:
            print(f"[WARNING] Respuesta inesperada de Gemini: '{respuesta_clean}'")
            return None
    
    def procesar_archivo_conectividad(self, archivo_path: str) -> pd.DataFrame:
        """Procesa el archivo completo de conectividad normalizando nombres IE"""
        
        print("=== PROCESADOR CONECTIVIDAD CON IA ===\n")
        
        # Cargar archivo
        print("Cargando archivo de conectividad...")
        df = pd.read_excel(archivo_path, sheet_name='hoja1', engine='openpyxl')
        print(f"[OK] Archivo cargado: {len(df)} registros")
        
        # Cargar datos de referencia
        self.cargar_referencia_ie()
        
        # Identificar columnas relevantes
        col_ie_nombre = 'Si pertence a una Red Rural, indique el nombre de su IE'
        col_fya = 'Fe y Alegr í a Nro. ....'
        
        # Crear nueva columna para código modular normalizado
        df['codigo_modular_normalizado'] = None
        df['matching_status'] = 'PENDING'
        
        # Filtrar solo registros con nombres IE
        registros_con_nombre = df[df[col_ie_nombre].notna()].copy()
        
        print(f"\n[OK] Procesando {len(registros_con_nombre)} registros con nombres IE...")
        
        # Procesar cada registro
        for idx, (index, row) in enumerate(registros_con_nombre.iterrows()):
            nombre_manual = str(row[col_ie_nombre]).strip()
            red_fya = str(row[col_fya]) if pd.notna(row[col_fya]) else ""
            
            print(f"\n--- Registro {idx + 1}/{len(registros_con_nombre)} ---")
            print(f"Nombre manual: '{nombre_manual}'")
            print(f"Red FyA: '{red_fya}'")
            
            # Identificar con Gemini
            codigo_identificado = self.identificar_ie_con_gemini(nombre_manual, red_fya)
            
            if codigo_identificado == "NO_MATCH":
                df.loc[index, 'matching_status'] = 'NO_MATCH'
                print(f"Resultado: NO_MATCH")
            elif codigo_identificado:
                df.loc[index, 'codigo_modular_normalizado'] = codigo_identificado
                df.loc[index, 'matching_status'] = 'MATCHED'
                print(f"Resultado: {codigo_identificado}")
            else:
                df.loc[index, 'matching_status'] = 'ERROR'
                print(f"Resultado: ERROR")
            
            # Pausa pequeña para no saturar API
            if (idx + 1) % 5 == 0:
                print(f"\n[PROGRESS] Procesados {idx + 1} registros...")
        
        # Mostrar estadísticas finales
        self.mostrar_estadisticas_matching(df)
        
        return df
    
    def mostrar_estadisticas_matching(self, df: pd.DataFrame):
        """Muestra estadísticas del proceso de matching"""
        
        print(f"\n=== ESTADÍSTICAS MATCHING ===")
        
        status_counts = df['matching_status'].value_counts()
        total = len(df[df['matching_status'] != 'PENDING'])
        
        for status, count in status_counts.items():
            if status != 'PENDING':
                porcentaje = (count / total * 100) if total > 0 else 0
                print(f"{status}: {count} ({porcentaje:.1f}%)")
        
        # Mostrar muestra de matches exitosos
        matches_exitosos = df[df['matching_status'] == 'MATCHED']
        if len(matches_exitosos) > 0:
            print(f"\n=== MUESTRA DE MATCHES EXITOSOS ===")
            col_ie_nombre = 'Si pertence a una Red Rural, indique el nombre de su IE'
            
            for idx, (_, row) in enumerate(matches_exitosos.head(5).iterrows()):
                nombre_orig = row[col_ie_nombre]
                codigo_norm = row['codigo_modular_normalizado']
                print(f"'{nombre_orig}' → {codigo_norm}")
    
    def guardar_resultados(self, df: pd.DataFrame, output_path: str):
        """Guarda los resultados del procesamiento"""
        
        print(f"\nGuardando resultados en: {output_path}")
        df.to_excel(output_path, index=False, engine='openpyxl')
        print(f"[OK] Archivo guardado exitosamente")

def demo_normalizador():
    """Función de demostración del normalizador"""
    print("=== DEMO NORMALIZADOR IE CONECTIVIDAD ===\n")
    
    normalizador = NormalizadorIEConectividad()
    
    # Cargar referencia
    normalizador.cargar_referencia_ie()
    
    # Test con algunos nombres manuales
    casos_test = [
        ("525-B", "Fe y Alegr í a 72 RED RURAL"),
        ("6010231", "Fe y Alegr í a 47 RED RURAL"), 
        ("IE 64508-B", "Fe y Alegr í a 72 RED RURAL"),
        ("555-B", "Fe y Alegr í a 72 RED RURAL")
    ]
    
    print("=== TESTS DE MATCHING ===")
    for nombre, red in casos_test:
        print(f"\nTest: '{nombre}' en {red}")
        resultado = normalizador.identificar_ie_con_gemini(nombre, red)
        print(f"Resultado: {resultado}")

if __name__ == "__main__":
    # Ejecutar demo
    demo_normalizador()