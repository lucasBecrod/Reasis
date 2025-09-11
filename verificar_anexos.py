import pandas as pd
import sqlite3

def verificar_anexo_b_sql():
    """
    Verifica si las nuevas columnas están en el Anexo B (SQL)
    """
    
    db_path = r"archivado\clustering\02 Informe Entregado\Anexo B - Base de datos SQL v5.db"
    
    try:
        conn = sqlite3.connect(db_path)
        
        # Verificar columnas actuales
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(indices_metodologicos)")
        columnas_actuales = cursor.fetchall()
        
        nombres_columnas = [col[1] for col in columnas_actuales]
        
        print("=== VERIFICACION ANEXO B (SQL) ===")
        print(f"Total columnas actuales: {len(nombres_columnas)}")
        
        # Columnas que deberían estar (K=4 y riesgo-resiliencia)
        columnas_esperadas = [
            'CLUSTER_KMEANS',
            'TIPOLOGIA_KMEANS', 
            'SILHOUETTE_SCORE',
            'DISTANCIA_CENTROIDE',
            'Y1_ILA_PREDICHO',
            'RESIDUOS',
            'PRO_SCORE',
            'CATEGORIA_RESILIENCIA',
            'CATEGORIA_RIESGO',
            'REGION_DASHBOARD',
            'CATEGORIA_ALTITUD'
        ]
        
        # Verificar cuáles faltan
        columnas_faltantes = []
        columnas_presentes = []
        
        for col in columnas_esperadas:
            if col in nombres_columnas:
                columnas_presentes.append(col)
            else:
                columnas_faltantes.append(col)
        
        print(f"Columnas K=4/riesgo presentes: {len(columnas_presentes)}")
        for col in columnas_presentes:
            print(f"  ✓ {col}")
        
        if columnas_faltantes:
            print(f"Columnas K=4/riesgo FALTANTES: {len(columnas_faltantes)}")
            for col in columnas_faltantes:
                print(f"  ✗ {col}")
        else:
            print("TODAS las columnas K=4/riesgo están presentes en Anexo B")
        
        # Verificar datos de muestra
        if 'CLUSTER_KMEANS' in nombres_columnas:
            cursor.execute("SELECT CLUSTER_KMEANS, TIPOLOGIA_KMEANS, COUNT(*) as cantidad FROM indices_metodologicos WHERE CLUSTER_KMEANS IS NOT NULL GROUP BY CLUSTER_KMEANS, TIPOLOGIA_KMEANS ORDER BY CLUSTER_KMEANS")
            distribucion = cursor.fetchall()
            
            print(f"\nDistribución K=4 en Anexo B:")
            for cluster, tipologia, cantidad in distribucion:
                print(f"  Cluster {cluster} - {tipologia}: {cantidad} IIEE")
        
        conn.close()
        return len(columnas_faltantes) == 0, columnas_faltantes
        
    except Exception as e:
        print(f"Error al verificar Anexo B: {e}")
        return False, []

def verificar_anexo_a_excel():
    """
    Verifica si las nuevas columnas están en el Anexo A (Excel)
    """
    
    excel_path = r"archivado\clustering\02 Informe Entregado\Anexo A - Base de datos XLS v5.xlsx"
    
    try:
        # Leer hoja indices_metodologicos
        df_excel = pd.read_excel(excel_path, sheet_name='indices_metodologicos')
        
        print("=== VERIFICACION ANEXO A (EXCEL) ===")
        print(f"Total columnas actuales: {len(df_excel.columns)}")
        
        # Columnas que deberían estar
        columnas_esperadas = [
            'CLUSTER_KMEANS',
            'TIPOLOGIA_KMEANS', 
            'SILHOUETTE_SCORE',
            'DISTANCIA_CENTROIDE',
            'Y1_ILA_PREDICHO',
            'RESIDUOS',
            'PRO_SCORE',
            'CATEGORIA_RESILIENCIA',
            'CATEGORIA_RIESGO',
            'REGION_DASHBOARD',
            'CATEGORIA_ALTITUD'
        ]
        
        # Verificar cuáles faltan
        columnas_faltantes = []
        columnas_presentes = []
        
        for col in columnas_esperadas:
            if col in df_excel.columns:
                columnas_presentes.append(col)
            else:
                columnas_faltantes.append(col)
        
        print(f"Columnas K=4/riesgo presentes: {len(columnas_presentes)}")
        for col in columnas_presentes:
            print(f"  ✓ {col}")
        
        if columnas_faltantes:
            print(f"Columnas K=4/riesgo FALTANTES: {len(columnas_faltantes)}")
            for col in columnas_faltantes:
                print(f"  ✗ {col}")
        else:
            print("TODAS las columnas K=4/riesgo están presentes en Anexo A")
        
        # Verificar distribución si está presente
        if 'CLUSTER_KMEANS' in df_excel.columns:
            distribucion = df_excel.groupby(['CLUSTER_KMEANS', 'TIPOLOGIA_KMEANS']).size()
            
            print(f"\nDistribución K=4 en Anexo A:")
            for (cluster, tipologia), cantidad in distribucion.items():
                print(f"  Cluster {cluster} - {tipologia}: {cantidad} IIEE")
        
        return len(columnas_faltantes) == 0, columnas_faltantes, df_excel
        
    except Exception as e:
        print(f"Error al verificar Anexo A: {e}")
        return False, [], None

def main_verificacion():
    """
    Función principal de verificación
    """
    
    print("VERIFICANDO ANEXOS A Y B")
    print("="*40)
    
    # Verificar Anexo B (SQL)
    sql_completo, sql_faltantes = verificar_anexo_b_sql()
    
    print("\n" + "="*40)
    
    # Verificar Anexo A (Excel)  
    excel_completo, excel_faltantes, df_excel = verificar_anexo_a_excel()
    
    print("\n" + "="*40)
    print("RESUMEN VERIFICACION:")
    print("="*40)
    
    if sql_completo:
        print("✓ Anexo B (SQL): COMPLETO con datos K=4")
    else:
        print(f"✗ Anexo B (SQL): FALTAN {len(sql_faltantes)} columnas")
    
    if excel_completo:
        print("✓ Anexo A (Excel): COMPLETO con datos K=4")
    else:
        print(f"✗ Anexo A (Excel): FALTAN {len(excel_faltantes)} columnas")
    
    # Determinar qué hacer
    if not sql_completo or not excel_completo:
        print(f"\nNECESARIO ACTUALIZAR:")
        if not sql_completo:
            print(f"  - Anexo B (SQL): {sql_faltantes}")
        if not excel_completo:
            print(f"  - Anexo A (Excel): {excel_faltantes}")
        return False
    else:
        print(f"\n🎯 AMBOS ANEXOS TIENEN DATOS K=4 COMPLETOS")
        return True

if __name__ == "__main__":
    resultado = main_verificacion()