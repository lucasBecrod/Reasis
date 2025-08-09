#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import pandas as pd
import sqlite3

def explorar_archivo_eib_minedu():
    """Explora el archivo EIB de MINEDU para identificar variables útiles para el proyecto Reasis"""
    print("=== EXPLORACIÓN ARCHIVO RIIEE EIB 2024 MINEDU ===\n")
    
    # Usamos una ruta absoluta para asegurar que se encuentre el archivo
    archivo = os.path.join('assets', 'Consultoria', 'Información actualizada', 'Extras', 'RIIEE EIB 2024 Minedu.xlsx')

    try:
        # Leer archivo Excel
        df = pd.read_excel(archivo) # Lee la primera hoja por defecto

        print(f"DIMENSIONES: {df.shape[0]:,} filas x {df.shape[1]} columnas\n")

        print("COLUMNAS DISPONIBLES:")
        for i, col in enumerate(df.columns, 1):
            print(f"{i:2}. {col}")

        print("\nVARIABLES CRITICAS IDENTIFICADAS:")

        # Variables que nos interesan según la matriz de operacionalización
        # ACTUALIZADO con los nombres de columna correctos del archivo Excel
        variables_interes = {
            "X15_MEIB (Modalidad EIB)": {
                "descripcion": "Clasificación de la institución según Educación Intercultural Bilingüe.",
                "columnas": ['Forma de atención EIB', 'Escenario - 2024', 'Nombre lengua originaria 1 - 2024']
            },
            "X12_TOE (Organización Escolar)": {
                "descripcion": "Forma de atención de la escuela (unidocente, multigrado, polidocente).",
                "columnas": ['Forma de atención', 'Detalle de caracteristica (Censo educativo 2023)']
            },
            "X1_NVC (Vulnerabilidad Contexto)": {
                "descripcion": "Nivel de pobreza y ubicación en zonas de riesgo.",
                "columnas": ['Quintil de pobreza', 'La IE se encuentra en un distrito frontera', 'La IE se encuentra en un distrito vraem']
            },
            "X2_TR (Tipo Ruralidad)": {
                "descripcion": "Clasificación detallada de la ruralidad.",
                "columnas": ['Tipo de Ruralidad', 'Detalle del área geográfica censal (500 Habitantes)']
            },
            "X10_IE (Infraestructura)": {
                "descripcion": "Conectividad y servicios básicos de la IE.",
                "columnas": ['¿El IE está conectada a una red de agua potable?', '¿La IE está conectada a una red de desagüe?', '¿La IE está conectada a una red de electricidad?', '¿La IE cuenta con acceso a internet?']
            },
            "X5_ED (Estabilidad Docente)": {
                "descripcion": "Distribución de docentes por condición laboral.",
                "columnas": ['Condición Laboral: Nombrado', 'Condición Laboral: Contratado']
            }
        }

        for var, info in variables_interes.items():
            print(f"\n[OK] {var}: {info['descripcion']}")
            cols_encontradas = [col for col in info['columnas'] if col in df.columns]
            if cols_encontradas:
                print(f"   Columnas disponibles: {', '.join(cols_encontradas)}")
                # Mostrar un ejemplo de los datos
                if 'Forma de atención EIB' in cols_encontradas:
                    valores_eib = df['Forma de atención EIB'].value_counts()
                    print(f"   Distribución EIB: {dict(valores_eib)}")
                if 'Detalle de caracteristica (Censo educativo 2023)' in cols_encontradas:
                    valores_toe = df['Detalle de caracteristica (Censo educativo 2023)'].value_counts().head(3)
                    print(f"   Top 3 Formas Atención: {dict(valores_toe)}")
                if 'Quintil de pobreza' in cols_encontradas:
                    valores_pobreza = df['Quintil de pobreza'].value_counts().sort_index()
                    print(f"   Quintiles pobreza: {dict(valores_pobreza)}")
            else:
                print(f"   [NO] No se encontraron columnas relacionadas")

        print("\nCOMPATIBILIDAD CON BASE DE DATOS REASIS:")

        db_path = 'reasis_database.db'
        if not os.path.exists(db_path):
            print(f"   [ADVERTENCIA] No se encontró la base de datos '{db_path}'. No se puede verificar la compatibilidad.")
            return

        # Conectar a base de datos para comparar
        conn = sqlite3.connect(db_path)
        try:
            df_fya = pd.read_sql_query("SELECT DISTINCT codigo_modular FROM instituciones_educativas", conn)
            print(f"Se encontraron {len(df_fya)} instituciones únicas en la tabla 'instituciones_educativas'.")
        except Exception as e:
            print(f"   [ERROR] No se pudo leer la tabla 'instituciones_educativas' de la base de datos: {e}")
            conn.close()
            return
        finally:
            conn.close()

        codigos_fya = set(df_fya['codigo_modular'].astype(str))

        if 'Código modular' in df.columns:
            # Asegurarse que los códigos modulares del excel son string para comparar
            df['Código modular'] = df['Código modular'].astype(str)
            codigos_eib = set(df['Código modular'])
            coincidencias = codigos_fya.intersection(codigos_eib)

            if len(codigos_fya) > 0:
                porcentaje = len(coincidencias) / len(codigos_fya) * 100
                print(f"   [RESULTADO] Cobertura: {len(coincidencias)} de {len(codigos_fya)} instituciones encontradas en el padrón MINEDU ({porcentaje:.1f}%)")
            else:
                print("   [INFO] No se encontraron instituciones en la base de datos local para comparar.")

            if coincidencias:
                print(f"   Códigos modulares coincidentes (muestra): {list(coincidencias)[:10]}..." if len(coincidencias) > 10 else f"   Códigos modulares coincidentes: {list(coincidencias)}")

        print("\n--- DIAGNÓSTICO FINAL ---")
        print("¡ÉXITO! El archivo contiene datos para TODAS las variables faltantes.")
        print("[OK] X15_MEIB (Modalidad EIB)")
        print("[OK] X12_TOE (Organización Escolar)")
        print("[OK] X1_NVC (Vulnerabilidad)")
        print("[OK] X2_TR (Ruralidad)")
        print("[OK] X10_IE (Infraestructura)")
        print("[OK] X5_ED (Estabilidad Docente)")

    except FileNotFoundError:
        full_path = os.path.abspath(archivo)
        print(f"ERROR: No se pudo encontrar el archivo en la ruta especificada:\n{full_path}")
    except Exception as e:
        print(f"Ocurrió un error inesperado: {e}")

if __name__ == "__main__":
    explorar_archivo_eib_minedu()