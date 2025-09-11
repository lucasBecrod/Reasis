"""
Script para calcular X2_TR - Tipo de Ruralidad
Convierte es_rural (0/1) a categorías TR según matriz de operacionalización

Autor: Proyecto Reasis
Fecha: 2025-08-10
"""

import sqlite3
import pandas as pd
import json
from datetime import datetime

def calcular_x2_tr():
    """
    Calcula X2_TR basado en es_rural de instituciones_educativas
    
    Lógica de conversión:
    - es_rural = 1 (Rural) → X2_TR = 2 (Rural)  
    - es_rural = 0 (Urbano) → X2_TR = 1 (Urbano)
    """
    
    print("=== CALCULANDO X2_TR - TIPO RURALIDAD ===\n")
    
    conn = sqlite3.connect('reasis_database.db')
    
    # 1. Verificar datos disponibles en instituciones_educativas
    print("1. VERIFICANDO DATOS FUENTE:")
    df_fuente = pd.read_sql_query("""
        SELECT codigo_modular, nombre_institucion, es_rural 
        FROM instituciones_educativas 
        ORDER BY es_rural, codigo_modular
    """, conn)
    
    print(f"   Total instituciones: {len(df_fuente)}")
    
    # Distribución es_rural
    distribucion = df_fuente['es_rural'].value_counts().sort_index()
    for valor, count in distribucion.items():
        tipo = "Rural" if valor == 1 else "Urbano" if valor == 0 else "NULL/Indefinido"
        print(f"   es_rural={valor} ({tipo}): {count} instituciones")
    
    # 2. Conversión a X2_TR
    print("\n2. APLICANDO CONVERSION X2_TR:")
    print("   Logica: es_rural=1 -> X2_TR=2 (Rural)")
    print("           es_rural=0 -> X2_TR=1 (Urbano)")
    
    df_fuente['X2_TR'] = df_fuente['es_rural'].map({
        0: 1,  # Urbano
        1: 2   # Rural
    })
    
    # Verificar conversión
    conversion_ok = df_fuente['X2_TR'].notna().sum()
    print(f"   Conversion exitosa: {conversion_ok}/{len(df_fuente)} instituciones")
    
    # 3. Preparar datos para actualización
    df_resultado = df_fuente[['codigo_modular', 'X2_TR']].copy()
    
    # 4. Guardar archivo temporal  
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = f"temp_data/x2_tr_preliminar_{timestamp}.csv"
    df_resultado.to_csv(csv_path, index=False)
    print(f"\n3. ARCHIVO PRELIMINAR GUARDADO: {csv_path}")
    
    # 5. Estadísticas finales
    estadisticas = {
        "fecha_calculo": datetime.now().isoformat(),
        "total_instituciones": int(len(df_resultado)),
        "instituciones_con_x2_tr": int(df_resultado['X2_TR'].notna().sum()),
        "distribucion_x2_tr": {
            "Urbano_TR1": int((df_resultado['X2_TR'] == 1).sum()),
            "Rural_TR2": int((df_resultado['X2_TR'] == 2).sum())
        },
        "porcentaje_cobertura": float((df_resultado['X2_TR'].notna().sum() / len(df_resultado)) * 100),
        "metodo_aplicado": "Conversion directa es_rural -> X2_TR",
        "fuente_datos": "instituciones_educativas.es_rural"
    }
    
    # Guardar estadísticas
    json_path = f"data/intermedios/x2_tr_resumen_{timestamp}.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(estadisticas, f, indent=2, ensure_ascii=False)
    
    print(f"4. ESTADISTICAS GUARDADAS: {json_path}")
    
    # 6. Mostrar resumen
    print("\n=== RESUMEN X2_TR ===")
    print(f"Cobertura: {estadisticas['instituciones_con_x2_tr']}/{estadisticas['total_instituciones']} ({estadisticas['porcentaje_cobertura']:.1f}%)")
    print(f"TR=1 (Urbano): {estadisticas['distribucion_x2_tr']['Urbano_TR1']} instituciones")
    print(f"TR=2 (Rural): {estadisticas['distribucion_x2_tr']['Rural_TR2']} instituciones")
    print(f"Metodo: {estadisticas['metodo_aplicado']}")
    
    conn.close()
    
    return csv_path, json_path, estadisticas

if __name__ == "__main__":
    csv_file, json_file, stats = calcular_x2_tr()
    print(f"\nX2_TR calculado exitosamente")
    print(f"CSV: {csv_file}")
    print(f"JSON: {json_file}")