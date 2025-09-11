import pandas as pd
import sqlite3

def actualizar_anexo_a_excel():
    """
    Actualiza el Anexo A (Excel) con datos del archivo indices_metodologicos_k4_correcto.csv
    """
    
    print("ACTUALIZANDO ANEXO A (EXCEL) CON DATOS K=4")
    print("="*50)
    
    # Rutas
    csv_actualizado = 'indices_metodologicos_k4_correcto.csv'
    excel_path = r"archivado\clustering\02 Informe Entregado\Anexo A - Base de datos XLS v5.xlsx"
    
    try:
        # Cargar datos actualizados con K=4
        df_k4 = pd.read_csv(csv_actualizado, encoding='utf-8')
        print(f"Datos K=4 cargados: {len(df_k4)} registros, {len(df_k4.columns)} columnas")
        
        # Verificar columnas K=4 presentes
        columnas_k4 = [col for col in df_k4.columns if any(keyword in col for keyword in 
                      ['CLUSTER', 'TIPOLOGIA', 'RESILIENCIA', 'RIESGO', 'PRO_', 'SILHOUETTE'])]
        
        print(f"Columnas K=4 encontradas: {len(columnas_k4)}")
        for col in columnas_k4:
            print(f"  - {col}")
        
        # Verificar distribución K=4
        if 'CLUSTER_KMEANS' in df_k4.columns:
            dist_k4 = df_k4.groupby(['CLUSTER_KMEANS', 'TIPOLOGIA_KMEANS']).size()
            print(f"\nDistribución K=4 a agregar:")
            for (cluster, tipologia), cantidad in dist_k4.items():
                print(f"  Cluster {cluster} - {tipologia}: {cantidad} IIEE")
        
        # Leer Excel actual
        try:
            df_excel = pd.read_excel(excel_path, sheet_name='indices_metodologicos')
            print(f"Excel actual: {len(df_excel)} registros, {len(df_excel.columns)} columnas")
        except:
            print("Error leyendo Excel actual")
            return False
        
        # Verificar si ya tiene columnas K=4
        tiene_k4 = 'CLUSTER_KMEANS' in df_excel.columns
        if tiene_k4:
            print("AVISO: Excel ya tiene columnas K=4, las reemplazaremos")
        else:
            print("Excel NO tiene columnas K=4, las agregaremos")
        
        # Usar directamente los datos K=4 actualizados
        print(f"\nReemplazando hoja 'indices_metodologicos' con datos K=4...")
        
        # Crear ExcelWriter para actualizar solo una hoja
        with pd.ExcelWriter(excel_path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
            df_k4.to_excel(writer, sheet_name='indices_metodologicos', index=False)
        
        print("Hoja 'indices_metodologicos' actualizada exitosamente")
        
        # Verificar actualización
        df_verificacion = pd.read_excel(excel_path, sheet_name='indices_metodologicos')
        print(f"Verificación: {len(df_verificacion)} registros, {len(df_verificacion.columns)} columnas")
        
        # Verificar columnas K=4
        columnas_k4_final = [col for col in df_verificacion.columns if any(keyword in col for keyword in 
                            ['CLUSTER', 'TIPOLOGIA', 'RESILIENCIA', 'RIESGO', 'PRO_'])]
        
        print(f"Columnas K=4 en Excel final: {len(columnas_k4_final)}")
        for col in columnas_k4_final:
            print(f"  - {col}")
        
        # Verificar distribución K=4 final
        if 'CLUSTER_KMEANS' in df_verificacion.columns:
            print(f"\nDistribución K=4 final en Excel:")
            dist_final = df_verificacion.groupby(['CLUSTER_KMEANS', 'TIPOLOGIA_KMEANS']).size()
            for (cluster, tipologia), cantidad in dist_final.items():
                print(f"  Cluster {cluster} - {tipologia}: {cantidad} IIEE")
        
        # Verificar resiliencia
        if 'CATEGORIA_RESILIENCIA' in df_verificacion.columns:
            print(f"\nDistribución resiliencia final:")
            dist_resiliencia = df_verificacion['CATEGORIA_RESILIENCIA'].value_counts()
            for categoria, cantidad in dist_resiliencia.items():
                print(f"  {categoria}: {cantidad} IIEE")
        
        return True
        
    except Exception as e:
        print(f"Error al actualizar Anexo A: {e}")
        import traceback
        traceback.print_exc()
        return False

def verificar_ambos_anexos():
    """
    Verificación final de que ambos anexos tienen los datos K=4
    """
    
    print(f"\n{'='*50}")
    print("VERIFICACION FINAL AMBOS ANEXOS")
    print("="*50)
    
    # Verificar Anexo B (SQL)
    try:
        conn = sqlite3.connect(r"archivado\clustering\02 Informe Entregado\Anexo B - Base de datos SQL v5.db")
        
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM indices_metodologicos WHERE CLUSTER_KMEANS IS NOT NULL")
        sql_k4 = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM indices_metodologicos WHERE CATEGORIA_RESILIENCIA IS NOT NULL")
        sql_resiliencia = cursor.fetchone()[0]
        
        conn.close()
        
        print(f"Anexo B (SQL):")
        print(f"  - K=4 clustering: {sql_k4} instituciones")
        print(f"  - Riesgo-resiliencia: {sql_resiliencia} instituciones")
        
    except Exception as e:
        print(f"Error verificando SQL: {e}")
    
    # Verificar Anexo A (Excel)
    try:
        df_excel = pd.read_excel(r"archivado\clustering\02 Informe Entregado\Anexo A - Base de datos XLS v5.xlsx", 
                                sheet_name='indices_metodologicos')
        
        excel_k4 = df_excel['CLUSTER_KMEANS'].notna().sum() if 'CLUSTER_KMEANS' in df_excel.columns else 0
        excel_resiliencia = df_excel['CATEGORIA_RESILIENCIA'].notna().sum() if 'CATEGORIA_RESILIENCIA' in df_excel.columns else 0
        
        print(f"Anexo A (Excel):")
        print(f"  - K=4 clustering: {excel_k4} instituciones")
        print(f"  - Riesgo-resiliencia: {excel_resiliencia} instituciones")
        
        if excel_k4 > 0 and excel_resiliencia > 0:
            print(f"\nEXITO: Ambos anexos tienen datos K=4 y riesgo-resiliencia")
            return True
        else:
            print(f"\nERROR: Anexo A aún no tiene todos los datos")
            return False
        
    except Exception as e:
        print(f"Error verificando Excel: {e}")
        return False

if __name__ == "__main__":
    # Actualizar Anexo A
    exito = actualizar_anexo_a_excel()
    
    if exito:
        # Verificación final
        verificar_ambos_anexos()
        
        print(f"\n{'='*60}")
        print("PROCESO COMPLETADO")
        print("="*60)
        print("ANEXO A y ANEXO B actualizados con:")
        print("  - K=4 clustering con tipologias exactas")
        print("  - Riesgo-resiliencia con categorias")
        print("  - Variables adicionales para dashboard")
        print("  - Listo para crear dashboard interactivo")
    else:
        print("Error en la actualización")