#!/usr/bin/env python3
"""
Paso 4: Consistencia Final - Poblar codigo_rer en Instituciones - Proyecto Reasis
Asegura que la columna numérica 'codigo_rer' en 'instituciones_educativas'
sea consistente con la columna de texto 'codigo_red'.
"""

import sqlite3
import re

DB_PATH = 'reasis_database.db'

def poblar_codigo_rer_instituciones():
    """Extrae el número de 'codigo_red' y lo inserta en 'codigo_rer'."""
    print("--- INICIANDO PASO 4: CONSISTENCIA FINAL DE CÓDIGOS DE RED ---")
    print("=" * 65)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Obtener todas las instituciones que tienen un codigo_red
    cursor.execute("SELECT id, codigo_red FROM instituciones_educativas WHERE codigo_red IS NOT NULL")
    instituciones_a_actualizar = cursor.fetchall()

    if not instituciones_a_actualizar:
        print("No hay instituciones con 'codigo_red' para procesar. Proceso omitido.")
        conn.close()
        return

    print(f"Se encontraron {len(instituciones_a_actualizar)} instituciones para sincronizar 'codigo_rer'.")
    
    actualizados = 0
    for inst_id, codigo_red_texto in instituciones_a_actualizar:
        # Usar una expresión regular para extraer el número de forma segura
        match = re.search(r'\d+', codigo_red_texto)
        if match:
            codigo_rer_numerico = int(match.group(0))
            cursor.execute("UPDATE instituciones_educativas SET codigo_rer = ? WHERE id = ?", (codigo_rer_numerico, inst_id))
            actualizados += cursor.rowcount

    conn.commit()
    conn.close()

    print(f"✅ Proceso finalizado. Se actualizaron {actualizados} registros.")
    print("Las columnas 'codigo_red' y 'codigo_rer' ahora están sincronizadas.")
    print("=" * 65)

if __name__ == "__main__":
    poblar_codigo_rer_instituciones()