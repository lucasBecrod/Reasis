import sqlite3
import pandas as pd

def explorar_base_datos_sql_v5():
    """
    Explora la base de datos SQL v5 para identificar variables de clustering y riesgo-resiliencia
    """
    
    db_path = r"archivado\clustering\02 Informe Entregado\Anexo B - Base de datos SQL v5.db"
    
    try:
        # Conectar a la base de datos
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Obtener lista de tablas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tablas = cursor.fetchall()
        
        print("TABLAS ENCONTRADAS EN SQL v5:")
        print("="*50)
        for i, (tabla,) in enumerate(tablas, 1):
            print(f"{i}. {tabla}")
        
        # Explorar cada tabla para buscar variables de clustering
        tablas_relevantes = []
        
        for (tabla,) in tablas:
            print(f"\n--- TABLA: {tabla} ---")
            
            # Obtener información de columnas
            cursor.execute(f"PRAGMA table_info({tabla})")
            columnas = cursor.fetchall()
            
            print("Columnas:")
            for col_info in columnas:
                col_name = col_info[1]
                col_type = col_info[2]
                print(f"  - {col_name} ({col_type})")
            
            # Obtener muestra de datos
            try:
                cursor.execute(f"SELECT * FROM {tabla} LIMIT 3")
                muestra = cursor.fetchall()
                
                if muestra:
                    print("Muestra de datos:")
                    col_names = [desc[0] for desc in cursor.description]
                    for fila in muestra:
                        print(f"  {dict(zip(col_names, fila))}")
                
                # Buscar columnas que podrían ser de clustering o riesgo-resiliencia
                col_names = [desc[0] for desc in cursor.description]
                clustering_cols = [col for col in col_names if any(keyword in col.lower() 
                                  for keyword in ['cluster', 'grupo', 'tipologia', 'kmeans', 'riesgo', 'resiliencia', 'k_means'])]
                
                if clustering_cols:
                    print(f"COLUMNAS DE INTERES ENCONTRADAS: {clustering_cols}")
                    tablas_relevantes.append((tabla, clustering_cols))
                    
                    # Obtener estadísticas de estas columnas
                    for col in clustering_cols:
                        try:
                            cursor.execute(f"SELECT DISTINCT {col} FROM {tabla} WHERE {col} IS NOT NULL LIMIT 10")
                            valores_unicos = cursor.fetchall()
                            print(f"  {col} - Valores únicos: {[v[0] for v in valores_unicos]}")
                        except:
                            pass
                            
            except Exception as e:
                print(f"  Error al leer muestra: {e}")
        
        # Resumen de tablas relevantes
        print(f"\n" + "="*60)
        print("RESUMEN: TABLAS CON VARIABLES DE CLUSTERING/RIESGO")
        print("="*60)
        
        if tablas_relevantes:
            for tabla, columnas in tablas_relevantes:
                print(f"\nTabla: {tabla}")
                print(f"Variables: {', '.join(columnas)}")
        else:
            print("No se encontraron variables evidentes de clustering o riesgo-resiliencia")
            print("Revisar manualmente las tablas:")
            for (tabla,) in tablas:
                print(f"  - {tabla}")
        
        conn.close()
        return tablas_relevantes
        
    except Exception as e:
        print(f"Error al conectar con la base de datos: {e}")
        return None

if __name__ == "__main__":
    explorar_base_datos_sql_v5()