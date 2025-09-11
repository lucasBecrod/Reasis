#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEST BATCH PEQUEÑO - Prueba con 5 registros antes del procesamiento completo
"""
import pandas as pd
from normalizador_ie_conectividad import NormalizadorIEConectividad

def test_batch_pequeno():
    """Prueba con los primeros 5 registros"""
    
    print("=== TEST BATCH PEQUEÑO (5 REGISTROS) ===\n")
    
    # Inicializar
    normalizador = NormalizadorIEConectividad()
    archivo_path = r"C:\Users\lucas\Proyectos\Reasis\assets\Consultoria\Información actualizada\4. Conectividad y equipamiento.xlsx"
    
    # Cargar datos
    df = pd.read_excel(archivo_path, sheet_name='hoja1', engine='openpyxl')
    normalizador.cargar_referencia_ie()
    
    # Columnas
    col_ie_nombre = 'Si pertence a una Red Rural, indique el nombre de su IE'
    col_fya = 'Fe y Alegría Nro. ....'
    
    # Primeros 5 con nombres
    registros_test = df[df[col_ie_nombre].notna()].head(5)
    
    print(f"Probando con {len(registros_test)} registros:")
    print()
    
    resultados = []
    
    for idx, (_, row) in enumerate(registros_test.iterrows(), 1):
        nombre_manual = str(row[col_ie_nombre]).strip()
        red_fya = str(row[col_fya]) if pd.notna(row[col_fya]) else ""
        
        print(f"[{idx}/5] Test: '{nombre_manual}' en {red_fya}")
        
        codigo = normalizador.identificar_ie_con_gemini(nombre_manual, red_fya)
        
        resultado = {
            'nombre_manual': nombre_manual,
            'red': red_fya,
            'codigo_identificado': codigo,
            'status': 'MATCH' if codigo and codigo != 'NO_MATCH' else 'NO_MATCH'
        }
        
        resultados.append(resultado)
        print(f"  -> Resultado: {codigo}")
        print()
    
    # Resumen
    matches = sum(1 for r in resultados if r['status'] == 'MATCH')
    print(f"=== RESUMEN TEST ===")
    print(f"Total probados: {len(resultados)}")
    print(f"Matches exitosos: {matches}")
    print(f"Tasa éxito: {(matches/len(resultados)*100):.1f}%")
    
    if matches >= 3:  # Al menos 60% de éxito
        print(f"\n[OK] TEST EXITOSO - Sistema listo para procesamiento completo")
        return True
    else:
        print(f"\n[WARNING] TEST CON PROBLEMAS - Revisar configuración")
        return False

if __name__ == "__main__":
    test_batch_pequeno()