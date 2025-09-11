#!/usr/bin/env python3
import pandas as pd
import sqlite3

def analizar_datos_eib_simple():
    """Análisis simple del archivo EIB para identificar coincidencias con Fe y Alegría"""
    
    print("=== ANALISIS DATOS EIB MINEDU PARA FE Y ALEGRIA ===\n")
    
    archivo = r"C:\Users\lucas\Proyectos\Reasis\assets\Consultoria\Información actualizada\Extras\RIIEE EIB 2024 Minedu.xlsx"
    
    try:
        # Leer archivo Excel
        df = pd.read_excel(archivo, sheet_name='Sheet1')
        print(f"Archivo cargado: {df.shape[0]:,} instituciones EIB de MINEDU")
        
        # Conectar a base de datos para obtener códigos de Fe y Alegría
        conn = sqlite3.connect('reasis_database.db')
        df_fya = pd.read_sql_query("SELECT codigo_modular FROM instituciones_educativas", conn)
        codigos_fya = set(df_fya['codigo_modular'].astype(str))
        print(f"Instituciones Fe y Alegria en BD: {len(codigos_fya)}")
        
        # Verificar coincidencias
        if 'Código modular' in df.columns:
            codigos_eib = set(df['Código modular'].astype(str))
            coincidencias = codigos_fya.intersection(codigos_eib)
            
            print(f"\nCOINCIDENCIAS ENCONTRADAS: {len(coincidencias)}/{len(codigos_fya)} ({len(coincidencias)/len(codigos_fya)*100:.1f}%)")
            
            if len(coincidencias) > 0:
                print(f"Codigos Fe y Alegria en archivo EIB: {sorted(list(coincidencias))}")
                
                # Obtener datos de las instituciones Fe y Alegría que están en EIB
                df_fya_eib = df[df['Código modular'].astype(str).isin(coincidencias)]
                
                print(f"\nDATOS DISPONIBLES PARA INSTITUCIONES FE Y ALEGRIA:")
                
                # Modalidad EIB
                if 'Forma de atención EIB' in df.columns:
                    print("\n- MODALIDAD EIB (X15_MEIB):")
                    modalidad_eib = df_fya_eib['Forma de atención EIB'].value_counts()
                    for modalidad, count in modalidad_eib.items():
                        print(f"  * {modalidad}: {count} instituciones")
                
                # Quintil de pobreza
                if 'Quintil de pobreza' in df.columns:
                    print("\n- QUINTIL DE POBREZA (X1_NVC):")
                    quintiles = df_fya_eib['Quintil de pobreza'].value_counts()
                    for q, count in sorted(quintiles.items()):
                        print(f"  * Quintil {q}: {count} instituciones")
                
                # Tipo de ruralidad
                if 'Tipo de Ruralidad' in df.columns:
                    print("\n- TIPO DE RURALIDAD (X2_TR):")
                    ruralidad = df_fya_eib['Tipo de Ruralidad'].value_counts()
                    for tipo, count in ruralidad.items():
                        print(f"  * {tipo}: {count} instituciones")
                
                # Contextos especiales
                contextos = []
                if 'La IE se encuentra en un distrito frontera' in df.columns:
                    frontera = df_fya_eib['La IE se encuentra en un distrito frontera'].sum()
                    if frontera > 0:
                        contextos.append(f"Frontera: {frontera}")
                
                if 'La IE se encuentra en un distrito vraem' in df.columns:
                    vraem = df_fya_eib['La IE se encuentra en un distrito vraem'].sum()
                    if vraem > 0:
                        contextos.append(f"VRAEM: {vraem}")
                
                if 'La IE se encuentra en un distrito minero ilegal' in df.columns:
                    minero = df_fya_eib['La IE se encuentra en un distrito minero ilegal'].sum()
                    if minero > 0:
                        contextos.append(f"Minero ilegal: {minero}")
                
                if contextos:
                    print(f"\n- CONTEXTOS ESPECIALES: {', '.join(contextos)}")
                
                # Estabilidad docente (X5_ED)
                if 'Condición Laboral: Nombrado' in df.columns and 'Condición Laboral: Contratado' in df.columns:
                    print("\n- ESTABILIDAD DOCENTE (X5_ED):")
                    nombrados = df_fya_eib['Condición Laboral: Nombrado'].sum()
                    contratados = df_fya_eib['Condición Laboral: Contratado'].sum()
                    total = nombrados + contratados
                    if total > 0:
                        print(f"  * Nombrados: {nombrados} ({nombrados/total*100:.1f}%)")
                        print(f"  * Contratados: {contratados} ({contratados/total*100:.1f}%)")
                
                # Infraestructura (X10_IE)
                infraestructura = []
                if '¿El IE está conectada a una red de agua potable?' in df.columns:
                    agua = df_fya_eib['¿El IE está conectada a una red de agua potable?'].sum()
                    infraestructura.append(f"Agua: {agua}")
                
                if '¿El IE está conectada a una red de electricidad?' in df.columns:
                    electricidad = df_fya_eib['¿El IE está conectada a una red de electricidad?'].sum()
                    infraestructura.append(f"Electricidad: {electricidad}")
                
                if '¿La IE cuenta con acceso a internet?' in df.columns:
                    internet = df_fya_eib['¿La IE cuenta con acceso a internet?'].sum()
                    infraestructura.append(f"Internet: {internet}")
                
                if infraestructura:
                    print(f"\n- INFRAESTRUCTURA (X10_IE): {', '.join(infraestructura)} instituciones")
                
                # Mostrar muestra de datos
                print(f"\nMUESTRA DE DATOS (primeras 3 instituciones):")
                cols_muestra = ['Código modular', 'Nro y/o Nombre del servicios educativo', 'Nombre de región', 'Forma de atención EIB', 'Quintil de pobreza']
                cols_disponibles = [col for col in cols_muestra if col in df_fya_eib.columns]
                if not df_fya_eib.empty:
                    print(df_fya_eib[cols_disponibles].head(3).to_string(index=False))
                
                print(f"\n🎯 VARIABLES QUE PODEMOS MEJORAR:")
                print(f"✓ X15_MEIB: Modalidad EIB específica disponible")
                print(f"✓ X1_NVC: Quintil de pobreza disponible")
                print(f"✓ X2_TR: Tipo de ruralidad mejorado disponible")
                print(f"✓ X5_ED: Datos nombrados vs contratados disponibles")
                print(f"✓ X10_IE: Datos básicos de infraestructura disponibles")
                print(f"✓ CONTEXTO: Variables especiales (VRAEM, frontera, etc.)")
                
            else:
                print("No se encontraron instituciones Fe y Alegría en el archivo EIB")
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    analizar_datos_eib_simple()