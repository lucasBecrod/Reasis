#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GEMINI OPTIMIZER - Integración de IA para optimización de base de datos Reasis
Funciones para llamar a Gemini API y obtener respuestas estructuradas para análisis de datos
"""
import requests
import json
import pandas as pd
import sqlite3
import base64
import os
from typing import Optional, Dict, List, Union
from PIL import Image
import io

# Configuración API Gemini - PRODUCCIÓN
GEMINI_API_KEY_PRODUCTION = "AIzaSyCV4K7OWFXcgU-ROLcO-yxIR3XeULakIqc"
GEMINI_API_KEY_PRIMARY = "AIzaSyDi8ggbQO_dbDoWUj2rGbkHLjyPfGZ16nU" 
GEMINI_API_KEY_BACKUP = "AIzaSyDqSlwH1rDtRGatRquZX6WVK0cM28Y38z0"
GEMINI_ENDPOINT_PRODUCTION = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key={GEMINI_API_KEY_PRODUCTION}"
GEMINI_ENDPOINT_PRIMARY = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key={GEMINI_API_KEY_PRIMARY}"
GEMINI_ENDPOINT_BACKUP = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key={GEMINI_API_KEY_BACKUP}"

class GeminiOptimizer:
    """Clase principal para optimización de datos usando Gemini AI"""
    
    def __init__(self, use_production=False):
        if use_production:
            # Usar API de producción como principal
            self.api_key_primary = GEMINI_API_KEY_PRODUCTION
            self.api_key_backup = GEMINI_API_KEY_PRIMARY  
            self.endpoint_primary = GEMINI_ENDPOINT_PRODUCTION
            self.endpoint_backup = GEMINI_ENDPOINT_PRIMARY
        else:
            # Usar configuración normal
            self.api_key_primary = GEMINI_API_KEY_PRIMARY
            self.api_key_backup = GEMINI_API_KEY_BACKUP
            self.endpoint_primary = GEMINI_ENDPOINT_PRIMARY
            self.endpoint_backup = GEMINI_ENDPOINT_BACKUP
            
        self.current_endpoint = self.endpoint_primary
        self.current_key = self.api_key_primary
        
    def call_gemini(self, prompt: str, temperature: float = 0.0) -> Optional[str]:
        """
        Función principal para llamar a Gemini API
        
        Args:
            prompt (str): El prompt a enviar a Gemini
            temperature (float): Nivel de creatividad (0.0-1.0)
            
        Returns:
            str: Respuesta de Gemini o None si hay error
        """
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": temperature
            }
        }
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.post(
                self.current_endpoint, 
                json=payload, 
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 429:  # Rate limit exceeded
                print(f"[WARNING] Rate limit en API primaria, intentando con backup...")
                if self.current_endpoint == self.endpoint_primary:
                    self.current_endpoint = self.endpoint_backup
                    self.current_key = self.api_key_backup
                    # Reintentar con backup
                    response = requests.post(
                        self.current_endpoint, 
                        json=payload, 
                        headers=headers,
                        timeout=30
                    )
            
            if response.status_code != 200:
                print(f"[ERROR] API Error: {response.status_code}")
                print(f"Response: {response.text}")
                return None
                
            data = response.json()
            content = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            
            return content if content else "No se recibió una respuesta válida."
            
        except Exception as e:
            print(f"[ERROR] Error en call_gemini: {str(e)}")
            return None
    
    def ask_yes_no(self, prompt: str) -> Optional[bool]:
        """
        Pregunta que espera respuesta Sí/No de Gemini
        
        Args:
            prompt (str): Pregunta para Gemini
            
        Returns:
            bool: True para Sí, False para No, None si no se puede determinar
        """
        full_prompt = f"""
        {prompt}
        
        INSTRUCCIONES:
        - Responde ÚNICAMENTE con "SÍ" o "NO"
        - No agregues explicaciones adicionales
        - Analiza cuidadosamente antes de responder
        """
        
        response = self.call_gemini(full_prompt, temperature=0.0)
        
        if not response:
            return None
            
        response_clean = response.strip().upper()
        
        if "SÍ" in response_clean or "SI" in response_clean or "YES" in response_clean:
            return True
        elif "NO" in response_clean:
            return False
        else:
            print(f"[WARNING] Respuesta ambigua de Gemini: {response}")
            return None
    
    def ask_structured_json(self, prompt: str, expected_schema: Dict) -> Optional[Dict]:
        """
        Solicita respuesta estructurada en formato JSON
        
        Args:
            prompt (str): Pregunta para Gemini
            expected_schema (dict): Esquema JSON esperado
            
        Returns:
            dict: Respuesta estructurada o None si hay error
        """
        schema_str = json.dumps(expected_schema, indent=2, ensure_ascii=False)
        
        full_prompt = f"""
        {prompt}
        
        INSTRUCCIONES CRÍTICAS:
        - Responde ÚNICAMENTE con un objeto JSON válido
        - Sigue exactamente este esquema:
        {schema_str}
        
        - No agregues texto adicional fuera del JSON
        - Usa valores null si no tienes información suficiente
        - Asegúrate de que el JSON sea válido
        """
        
        response = self.call_gemini(full_prompt, temperature=0.1)
        
        if not response:
            return None
            
        try:
            # Limpiar respuesta para extraer JSON
            response_clean = response.strip()
            
            # Buscar inicio y fin del JSON
            start = response_clean.find('{')
            end = response_clean.rfind('}') + 1
            
            if start == -1 or end == 0:
                print(f"[ERROR] No se encontró JSON en respuesta: {response_clean}")
                return None
                
            json_str = response_clean[start:end]
            result = json.loads(json_str)
            
            return result
            
        except json.JSONDecodeError as e:
            print(f"[ERROR] Error parsing JSON: {str(e)}")
            print(f"Response: {response}")
            return None
    
    def analyze_data_quality(self, table_name: str, sample_data: pd.DataFrame) -> Optional[Dict]:
        """
        Analiza calidad de datos usando Gemini
        
        Args:
            table_name (str): Nombre de la tabla
            sample_data (DataFrame): Muestra de datos a analizar
            
        Returns:
            dict: Análisis de calidad estructurado
        """
        data_summary = f"""
        Tabla: {table_name}
        Filas: {len(sample_data)}
        Columnas: {list(sample_data.columns)}
        
        Muestra de datos:
        {sample_data.head(10).to_string()}
        
        Tipos de datos:
        {sample_data.dtypes.to_string()}
        
        Valores nulos por columna:
        {sample_data.isnull().sum().to_string()}
        """
        
        schema = {
            "calidad_general": "Alta/Media/Baja",
            "problemas_detectados": ["lista", "de", "problemas"],
            "columnas_problematicas": {
                "nombre_columna": "descripcion_problema"
            },
            "recomendaciones": ["lista", "de", "recomendaciones"],
            "completitud_estimada": 0.95,
            "consistencia_estimada": 0.90,
            "prioridad_limpieza": "Alta/Media/Baja"
        }
        
        prompt = f"""
        Analiza la calidad de los siguientes datos de una base de datos educativa:
        
        {data_summary}
        
        Evalúa:
        1. Completitud de datos (valores faltantes)
        2. Consistencia en formatos
        3. Posibles errores o inconsistencias
        4. Calidad general para análisis estadístico
        """
        
        return self.ask_structured_json(prompt, schema)
    
    def suggest_data_normalization(self, column_data: pd.Series, column_name: str) -> Optional[Dict]:
        """
        Sugiere normalización para una columna específica
        
        Args:
            column_data (Series): Datos de la columna
            column_name (str): Nombre de la columna
            
        Returns:
            dict: Sugerencias de normalización
        """
        unique_values = column_data.value_counts().head(20).to_string()
        
        schema = {
            "requiere_normalizacion": True,
            "tipo_normalizacion": "categoricas/numericas/texto/fechas",
            "valores_problematicos": ["valor1", "valor2"],
            "mapeo_sugerido": {
                "valor_actual": "valor_normalizado"
            },
            "patron_detectado": "descripcion_del_patron",
            "confianza": 0.85
        }
        
        prompt = f"""
        Analiza esta columna de datos educativos para sugerir normalización:
        
        Columna: {column_name}
        Total valores: {len(column_data)}
        Valores únicos: {column_data.nunique()}
        
        Distribución de valores:
        {unique_values}
        
        ¿Necesita normalización? ¿Qué tipo de limpieza requiere?
        """
        
        return self.ask_structured_json(prompt, schema)
    
    def validate_institutional_data(self, row_data: Dict) -> Optional[bool]:
        """
        Valida si los datos de una institución educativa son consistentes
        
        Args:
            row_data (dict): Datos de una fila/institución
            
        Returns:
            bool: True si los datos parecen consistentes
        """
        prompt = f"""
        Valida si estos datos de una institución educativa son lógicamente consistentes:
        
        {json.dumps(row_data, indent=2, ensure_ascii=False)}
        
        Considera:
        - ¿Los niveles educativos coinciden con los códigos?
        - ¿La ubicación geográfica es coherente?
        - ¿Los números de estudiantes/docentes son razonables?
        - ¿La modalidad educativa es consistente con otros campos?
        
        ¿Son estos datos CONSISTENTES Y VÁLIDOS?
        """
        
        return self.ask_yes_no(prompt)
    
    def encode_image_to_base64(self, image_path: str) -> Optional[str]:
        """
        Convierte una imagen a Base64
        
        Args:
            image_path (str): Ruta a la imagen
            
        Returns:
            str: Imagen codificada en Base64
        """
        try:
            with open(image_path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                return encoded_string
        except Exception as e:
            print(f"[ERROR] Error codificando imagen: {str(e)}")
            return None
    
    def call_gemini_vision(self, prompt: str, image_paths: List[str], temperature: float = 0.0) -> Optional[str]:
        """
        Llama a Gemini Vision API con imágenes
        
        Args:
            prompt (str): Prompt para el análisis
            image_paths (list): Lista de rutas a imágenes
            temperature (float): Nivel de creatividad
            
        Returns:
            str: Respuesta de Gemini Vision
        """
        # Codificar todas las imágenes
        image_parts = []
        
        for image_path in image_paths:
            if not os.path.exists(image_path):
                print(f"[WARNING] Imagen no encontrada: {image_path}")
                continue
                
            base64_image = self.encode_image_to_base64(image_path)
            if base64_image:
                # Detectar tipo MIME basado en extensión
                ext = os.path.splitext(image_path)[1].lower()
                mime_type = {
                    '.png': 'image/png',
                    '.jpg': 'image/jpeg', 
                    '.jpeg': 'image/jpeg',
                    '.gif': 'image/gif',
                    '.webp': 'image/webp'
                }.get(ext, 'image/png')
                
                image_parts.append({
                    "inlineData": {
                        "mimeType": mime_type,
                        "data": base64_image
                    }
                })
        
        if not image_parts:
            print("[ERROR] No se pudo codificar ninguna imagen")
            return None
            
        # Construir payload
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt},
                        *image_parts
                    ]
                }
            ],
            "generationConfig": {
                "temperature": temperature
            }
        }
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.post(
                self.current_endpoint, 
                json=payload, 
                headers=headers,
                timeout=60  # Mayor timeout para imágenes
            )
            
            if response.status_code != 200:
                print(f"[ERROR] Vision API Error: {response.status_code}")
                print(f"Response: {response.text}")
                return None
                
            data = response.json()
            content = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            
            return content if content else "No se recibió una respuesta válida."
            
        except Exception as e:
            print(f"[ERROR] Error en call_gemini_vision: {str(e)}")
            return None
    
    def analyze_document_images(self, image_paths: List[str], document_type: str = "educativo") -> Optional[Dict]:
        """
        Analiza imágenes de documentos educativos y extrae datos estructurados
        
        Args:
            image_paths (list): Lista de rutas a imágenes
            document_type (str): Tipo de documento a analizar
            
        Returns:
            dict: Datos extraídos estructurados
        """
        schema = {
            "tipo_documento": "cedula_identidad/acta_nacimiento/certificado_estudios/otro",
            "datos_extraidos": {
                "nombres": "texto_extraido",
                "apellidos": "texto_extraido", 
                "dni": "numero_documento",
                "fecha_nacimiento": "YYYY-MM-DD",
                "lugar_nacimiento": "lugar",
                "otros_datos": {}
            },
            "confianza_extraccion": 0.95,
            "requiere_validacion_manual": False,
            "observaciones": "comentarios_adicionales"
        }
        
        prompt = f"""
        Analiza estas imágenes de documentos {document_type} y extrae toda la información personal visible.
        
        INSTRUCCIONES:
        - Extrae nombres, apellidos, números de documento, fechas, lugares
        - Identifica qué tipo de documento es
        - Indica tu nivel de confianza en la extracción
        - Señala si requiere validación manual
        - Solo extrae información claramente legible
        
        IMPORTANTE: Mantén la privacidad y solo extrae datos necesarios para análisis educativo.
        """
        
        return self.ask_structured_json_with_images(prompt, image_paths, schema)
    
    def ask_structured_json_with_images(self, prompt: str, image_paths: List[str], expected_schema: Dict) -> Optional[Dict]:
        """
        Solicita respuesta estructurada JSON analizando imágenes
        
        Args:
            prompt (str): Prompt para análisis
            image_paths (list): Lista de rutas a imágenes  
            expected_schema (dict): Esquema JSON esperado
            
        Returns:
            dict: Respuesta estructurada
        """
        schema_str = json.dumps(expected_schema, indent=2, ensure_ascii=False)
        
        full_prompt = f"""
        {prompt}
        
        INSTRUCCIONES CRÍTICAS:
        - Analiza cuidadosamente todas las imágenes proporcionadas
        - Responde ÚNICAMENTE con un objeto JSON válido
        - Sigue exactamente este esquema:
        {schema_str}
        
        - No agregues texto adicional fuera del JSON
        - Usa valores null si no encuentras información en las imágenes
        - Asegúrate de que el JSON sea válido
        """
        
        response = self.call_gemini_vision(full_prompt, image_paths, temperature=0.1)
        
        if not response:
            return None
            
        try:
            # Limpiar respuesta para extraer JSON
            response_clean = response.strip()
            
            # Buscar inicio y fin del JSON
            start = response_clean.find('{')
            end = response_clean.rfind('}') + 1
            
            if start == -1 or end == 0:
                print(f"[ERROR] No se encontró JSON en respuesta: {response_clean}")
                return None
                
            json_str = response_clean[start:end]
            result = json.loads(json_str)
            
            return result
            
        except json.JSONDecodeError as e:
            print(f"[ERROR] Error parsing JSON: {str(e)}")
            print(f"Response: {response}")
            return None

def demo_gemini_optimizer():
    """Función de demostración del optimizador Gemini"""
    print("=== DEMO GEMINI OPTIMIZER ===\n")
    
    optimizer = GeminiOptimizer()
    
    # Test 1: Pregunta básica
    print("1. TEST PREGUNTA BÁSICA:")
    response = optimizer.call_gemini("¿Cuál es la capital de Perú?")
    print(f"Respuesta: {response}\n")
    
    # Test 2: Pregunta Sí/No
    print("2. TEST PREGUNTA SÍ/NO:")
    answer = optimizer.ask_yes_no("¿Es Lima la capital de Perú?")
    print(f"Respuesta: {answer}\n")
    
    # Test 3: JSON estructurado
    print("3. TEST JSON ESTRUCTURADO:")
    schema = {
        "pais": "nombre_del_pais",
        "capital": "nombre_capital",
        "poblacion": 0,
        "es_sudamericano": True
    }
    
    structured = optimizer.ask_structured_json(
        "Proporciona información sobre Perú", 
        schema
    )
    print(f"Respuesta JSON: {json.dumps(structured, indent=2, ensure_ascii=False)}\n")
    
    print("Demo completada. Gemini Optimizer listo para usar.")

if __name__ == "__main__":
    demo_gemini_optimizer()