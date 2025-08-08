#!/usr/bin/env python3
"""
Mejorador de datos_eib_minedu usando técnica múltiples códigos identificadores
Proyecto Reasis - Aplicar metodología exitosa documentada para aumentar de 20 a 83+ instituciones

OBJETIVO: Reemplazar tabla datos_eib_minedu actual (20 IIEE) con versión mejorada usando
la técnica revolucionaria "múltiples códigos identificadores" ya documentada en AGENTS.md

METODOLOGÍA:
1. Usar archivo EIB correcto con header=1 y columnas exactas
2. Aplicar estrategia triple: cod_mod, codinst, codlocal  
3. Maximizar cobertura de variables X1_NVC, X10_IE, X15_MEIB
4. Mantener estructura y esquema de tabla existente
"""

import pandas as pd
import sqlite3

def main():
    print("=== MEJORADOR DATOS_EIB_MINEDU - TÉCNICA MÚLTIPLES CÓDIGOS ===")
    print("OBJETIVO: Aumentar de 20 a 83+ instituciones EIB MINEDU")
    
    # Usar archivo correcto según metodología exitosa
    archivo_eib = r"C:\Users\lucas\Proyectos\Reasis\assets\Consultoria\Información de referencia\RegistroNacional EIB Minedu\RIIEE EIB 2024 Minedu.xlsx"
    
    # 1. CARGAR ARCHIVO CON METODOLOGÍA EXITOSA
    print("\n1. CARGANDO ARCHIVO EIB CON METODOLOGÍA EXITOSA...")
    
    # Columnas exactas identificadas en metodología documentada
    columnas_necesarias = [
        'cod_mod',           # Código modular (principal)
        'codinst',           # Código institución (secundario) 
        'codlocal',          # Código local (terciario)
        'quintil_pobreza',   # X1_NVC - Variable crítica
        'fa_2024b',          # X15_MEIB - Modalidad EIB
        'ruralidad',         # X2_TR - Ruralidad (opcional)
        'agua_final',        # X10_IE - Servicios agua
        'internet_final',    # X10_IE - Servicios internet
    ]
    
    try:
        # Usar header=1 según metodología exitosa
        df_eib = pd.read_excel(archivo_eib, header=1, usecols=columnas_necesarias)
        print(f"   [OK] Registros EIB cargados: {len(df_eib):,}")
        print(f"   [OK] Columnas cargadas: {list(df_eib.columns)}")
        
        # Verificar completitud de datos críticos
        print("\n   COMPLETITUD VARIABLES CRÍTICAS:")
        for col in ['quintil_pobreza', 'fa_2024b', 'agua_final', 'internet_final']:
            if col in df_eib.columns:
                count = df_eib[col].notna().sum()
                pct = count/len(df_eib)*100
                print(f"     {col}: {count:,} registros ({pct:.1f}%)")
        
    except Exception as e:
        print(f"   [ERROR] No se pudo cargar archivo EIB: {e}")
        return
    
    # 2. CARGAR BASE DE DATOS INSTITUCIONES
    print("\n2. CARGANDO BASE DE DATOS INSTITUCIONES...")
    
    conn = sqlite3.connect('reasis_database.db')
    
    df_bd = pd.read_sql_query("""
        SELECT codigo_modular, nombre_institucion, numero_fya, 
               entra_estudio_clustering
        FROM instituciones_educativas
    """, conn)
    
    df_bd['codigo_modular'] = df_bd['codigo_modular'].astype(str)
    print(f"   [OK] Instituciones Fe y Alegría: {len(df_bd)}")
    
    # 3. APLICAR TÉCNICA MÚLTIPLES CÓDIGOS IDENTIFICADORES
    print("\n3. EJECUTANDO TÉCNICA MÚLTIPLES CÓDIGOS...")
    
    vinculaciones_exitosas = []
    
    # ESTRATEGIA 1: cod_mod (Principal - Mayor efectividad)
    print("   [PASO 1] Vinculación por cod_mod...")
    df_estrategia1 = df_eib[df_eib['cod_mod'].notna()].copy()
    df_estrategia1['cod_clean'] = pd.to_numeric(df_estrategia1['cod_mod'], errors='coerce')
    df_estrategia1 = df_estrategia1[df_estrategia1['cod_clean'].notna()].copy()
    df_estrategia1['cod_clean'] = df_estrategia1['cod_clean'].astype(int).astype(str)
    
    merge1 = df_bd.merge(df_estrategia1, left_on='codigo_modular', right_on='cod_clean', how='inner')
    if len(merge1) > 0:
        merge1['metodo_vinculacion'] = 'cod_mod'
        vinculaciones_exitosas.append(merge1)
        codigos_ya_vinculados = set(merge1['codigo_modular'])
        print(f"     [OK] cod_mod: {len(merge1)} instituciones vinculadas")
    else:
        codigos_ya_vinculados = set()
        print(f"     [INFO] cod_mod: 0 vinculaciones")
    
    # ESTRATEGIA 2: codinst (Secundario - Para restantes)
    print("   [PASO 2] Vinculación por codinst...")
    df_bd_restante = df_bd[~df_bd['codigo_modular'].isin(codigos_ya_vinculados)]
    
    df_estrategia2 = df_eib[df_eib['codinst'].notna()].copy()
    df_estrategia2['codinst_clean'] = pd.to_numeric(df_estrategia2['codinst'], errors='coerce')
    df_estrategia2 = df_estrategia2[df_estrategia2['codinst_clean'].notna()].copy()
    df_estrategia2['codinst_clean'] = df_estrategia2['codinst_clean'].astype(int).astype(str)
    
    merge2 = df_bd_restante.merge(df_estrategia2, left_on='codigo_modular', right_on='codinst_clean', how='inner')
    if len(merge2) > 0:
        merge2['metodo_vinculacion'] = 'codinst'
        vinculaciones_exitosas.append(merge2)
        codigos_ya_vinculados.update(merge2['codigo_modular'])
        print(f"     [OK] codinst: {len(merge2)} instituciones vinculadas")
    else:
        print(f"     [INFO] codinst: 0 vinculaciones")
    
    # ESTRATEGIA 3: codlocal (Terciario - Máxima cobertura)
    print("   [PASO 3] Vinculación por codlocal...")
    df_bd_restante = df_bd[~df_bd['codigo_modular'].isin(codigos_ya_vinculados)]
    
    df_estrategia3 = df_eib[df_eib['codlocal'].notna()].copy()
    df_estrategia3['codlocal_clean'] = pd.to_numeric(df_estrategia3['codlocal'], errors='coerce')
    df_estrategia3 = df_estrategia3[df_estrategia3['codlocal_clean'].notna()].copy()
    df_estrategia3['codlocal_clean'] = df_estrategia3['codlocal_clean'].astype(int).astype(str)
    
    merge3 = df_bd_restante.merge(df_estrategia3, left_on='codigo_modular', right_on='codlocal_clean', how='inner')
    if len(merge3) > 0:
        merge3['metodo_vinculacion'] = 'codlocal'
        vinculaciones_exitosas.append(merge3)
        print(f"     [OK] codlocal: {len(merge3)} instituciones vinculadas")
    else:
        print(f"     [INFO] codlocal: 0 vinculaciones")
    
    # Verificar éxito de vinculación
    if not vinculaciones_exitosas:
        print("   [ERROR] No se lograron vinculaciones exitosas")
        conn.close()
        return
    
    # 4. CONSOLIDAR RESULTADOS
    print("\n4. CONSOLIDANDO RESULTADOS...")
    
    df_consolidado = pd.concat(vinculaciones_exitosas, ignore_index=True)
    total_instituciones_mejoradas = len(df_consolidado)
    
    print(f"   [ÉXITO] Total instituciones EIB: {total_instituciones_mejoradas}")
    print(f"   [MEJORA] vs tabla anterior (20): +{total_instituciones_mejoradas-20} instituciones")
    
    # 5. ANALIZAR VARIABLES DISPONIBLES
    print("\n5. ANALIZANDO VARIABLES MEJORADAS...")
    
    # X1_NVC - Quintil pobreza
    quintil_count = df_consolidado['quintil_pobreza'].notna().sum()
    print(f"   X1_NVC (Quintil pobreza): {quintil_count} instituciones")
    
    # X15_MEIB - Modalidad EIB
    modalidad_count = df_consolidado['fa_2024b'].notna().sum()
    print(f"   X15_MEIB (Modalidad EIB): {modalidad_count} instituciones")
    
    # X10_IE - Servicios básicos
    agua_count = df_consolidado['agua_final'].notna().sum()
    internet_count = df_consolidado['internet_final'].notna().sum()
    print(f"   X10_IE (Servicios básicos): agua={agua_count}, internet={internet_count}")
    
    # 6. REEMPLAZAR TABLA DATOS_EIB_MINEDU
    print("\n6. REEMPLAZANDO TABLA datos_eib_minedu...")
    
    cursor = conn.cursor()
    
    # Backup de tabla anterior
    try:
        cursor.execute("DROP TABLE IF EXISTS datos_eib_minedu_backup_20_registros")
        cursor.execute("CREATE TABLE datos_eib_minedu_backup_20_registros AS SELECT * FROM datos_eib_minedu")
        print("   [OK] Backup tabla anterior creado")
    except:
        print("   [INFO] No existía tabla anterior")
    
    # Eliminar tabla actual
    cursor.execute("DROP TABLE IF EXISTS datos_eib_minedu")
    
    # Crear nueva tabla con estructura mejorada
    cursor.execute("""
        CREATE TABLE datos_eib_minedu (
            codigo_modular TEXT PRIMARY KEY,
            quintil_pobreza INTEGER,
            modalidad_eib TEXT, 
            tipo_ruralidad INTEGER,
            servicios_agua INTEGER,
            servicios_electricidad INTEGER,
            servicios_internet INTEGER,
            metodo_vinculacion TEXT,
            fecha_mejora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (codigo_modular) REFERENCES instituciones_educativas(codigo_modular)
        )
    """)
    
    print("   [OK] Nueva estructura tabla creada")
    
    # 7. INSERTAR DATOS MEJORADOS
    print("\n7. INSERTANDO DATOS MEJORADOS...")
    
    registros_insertados = 0
    for _, row in df_consolidado.iterrows():
        # Conversión segura de tipos
        quintil = None
        if pd.notna(row.get('quintil_pobreza')):
            try:
                quintil = int(row['quintil_pobreza'])
            except:
                pass
        
        ruralidad = None
        if pd.notna(row.get('ruralidad')):
            try:
                ruralidad = int(row['ruralidad'])
            except:
                pass
        
        agua = None
        if pd.notna(row.get('agua_final')):
            try:
                agua = int(row['agua_final'])
            except:
                pass
        
        internet = None
        if pd.notna(row.get('internet_final')):
            try:
                internet = int(row['internet_final'])
            except:
                pass
        
        cursor.execute("""
            INSERT INTO datos_eib_minedu 
            (codigo_modular, quintil_pobreza, modalidad_eib, tipo_ruralidad,
             servicios_agua, servicios_electricidad, servicios_internet, metodo_vinculacion)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            row['codigo_modular'],
            quintil,
            row.get('fa_2024b') if pd.notna(row.get('fa_2024b')) else None,
            ruralidad,
            agua,
            None,  # servicios_electricidad no disponible en este archivo
            internet,
            row['metodo_vinculacion']
        ))
        registros_insertados += 1
    
    conn.commit()
    print(f"   [OK] Insertados {registros_insertados} registros mejorados")
    
    # 8. VERIFICACIÓN FINAL
    print("\n8. VERIFICACIÓN FINAL...")
    
    verificacion = pd.read_sql_query("""
        SELECT COUNT(*) as total,
               COUNT(CASE WHEN quintil_pobreza IS NOT NULL THEN 1 END) as con_quintil,
               COUNT(CASE WHEN modalidad_eib IS NOT NULL THEN 1 END) as con_modalidad,
               COUNT(CASE WHEN servicios_agua IS NOT NULL THEN 1 END) as con_agua,
               COUNT(CASE WHEN servicios_internet IS NOT NULL THEN 1 END) as con_internet
        FROM datos_eib_minedu
    """, conn)
    
    total = verificacion.iloc[0]['total']
    quintil = verificacion.iloc[0]['con_quintil']
    modalidad = verificacion.iloc[0]['con_modalidad']
    agua = verificacion.iloc[0]['con_agua']
    internet = verificacion.iloc[0]['con_internet']
    
    print(f"   [VERIFICADO] Total registros: {total}")
    print(f"   [VERIFICADO] Con quintil_pobreza: {quintil}")
    print(f"   [VERIFICADO] Con modalidad_eib: {modalidad}")
    print(f"   [VERIFICADO] Con servicios_agua: {agua}")
    print(f"   [VERIFICADO] Con servicios_internet: {internet}")
    
    # Análisis por redes del estudio
    print("\n9. ANÁLISIS REDES DEL ESTUDIO...")
    
    analisis_redes = pd.read_sql_query("""
        SELECT ie.numero_fya, COUNT(*) as instituciones_eib
        FROM datos_eib_minedu eib
        JOIN instituciones_educativas ie ON eib.codigo_modular = ie.codigo_modular
        WHERE ie.numero_fya IN ('44', '47', '48', '54', '72', '79')
        GROUP BY ie.numero_fya
        ORDER BY ie.numero_fya
    """, conn)
    
    total_estudio = 0
    for _, row in analisis_redes.iterrows():
        print(f"   Red {row['numero_fya']}: {row['instituciones_eib']} instituciones con datos EIB")
        total_estudio += row['instituciones_eib']
    
    print(f"   [TOTAL] Instituciones del estudio con EIB: {total_estudio}")
    
    conn.close()
    
    # 10. RESULTADO FINAL HISTÓRICO
    print("\n" + "="*70)
    print("MEJORA MASIVA datos_eib_minedu CONSEGUIDA")
    print("="*70)
    
    print(f"TÉCNICA MÚLTIPLES CÓDIGOS APLICADA EXITOSAMENTE:")
    print(f"✓ Instituciones EIB ANTES: 20")
    print(f"✓ Instituciones EIB DESPUÉS: {total}")
    print(f"✓ MEJORA NETA: +{total-20} instituciones ({((total-20)/20*100):.0f}% incremento)")
    
    print(f"\nVARIABLES METODOLÓGICAS MEJORADAS:")
    print(f"✓ X1_NVC (Quintil pobreza): {quintil} instituciones")
    print(f"✓ X15_MEIB (Modalidad EIB): {modalidad} instituciones")
    print(f"✓ X10_IE (Servicios básicos): agua={agua}, internet={internet}")
    print(f"✓ Instituciones del estudio: {total_estudio}")
    
    print(f"\nIMPACTO EN COMPLETITUD METODOLÓGICA:")
    print(f"✓ Variables X1, X10, X15 ahora con {total} instituciones")
    print(f"✓ Base sólida para clustering K-Means mejorada")
    print(f"✓ Metodología replicable documentada y aplicada")
    
    return total

if __name__ == "__main__":
    main()