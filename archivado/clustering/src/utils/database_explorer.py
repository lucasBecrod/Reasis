#!/usr/bin/env python3
"""
Explorador Interactivo de Base de Datos Reasis
Permite visualizar tablas, estructuras y datos de forma fácil
"""

import sqlite3
import pandas as pd
from pathlib import Path

class ReasisDatabaseExplorer:
    def __init__(self, db_path="reasis_database.db"):
        self.db_path = Path(db_path)
        if not self.db_path.exists():
            # Buscar en directorio raíz del proyecto
            project_root = Path(__file__).parent.parent.parent
            self.db_path = project_root / "reasis_database.db"
        
        if not self.db_path.exists():
            raise FileNotFoundError(f"No se encontró la base de datos: {self.db_path}")
    
    def get_connection(self):
        return sqlite3.connect(self.db_path)
    
    def list_tables(self):
        """Lista todas las tablas con conteo de registros"""
        conn = self.get_connection()
        
        print("=" * 60)
        print("🗄️  BASE DE DATOS REASIS - RESUMEN DE TABLAS")
        print("=" * 60)
        
        tables = pd.read_sql_query(
            'SELECT name FROM sqlite_master WHERE type="table" ORDER BY name', 
            conn
        )
        
        for table_name in tables['name']:
            try:
                count = pd.read_sql_query(
                    f'SELECT COUNT(*) as count FROM "{table_name}"', 
                    conn
                ).iloc[0,0]
                print(f"📊 {table_name:40} - {count:,} registros")
            except Exception as e:
                print(f"❌ {table_name:40} - Error: {e}")
        
        conn.close()
    
    def describe_table(self, table_name):
        """Describe la estructura de una tabla"""
        conn = self.get_connection()
        
        print(f"\n📋 ESTRUCTURA DE TABLA: {table_name}")
        print("=" * 60)
        
        try:
            # Estructura de columnas
            columns = pd.read_sql_query(f'PRAGMA table_info("{table_name}")', conn)
            print("Columnas:")
            for _, col in columns.iterrows():
                null_text = "NOT NULL" if col['notnull'] else "NULL"
                pk_text = "(PK)" if col['pk'] else ""
                print(f"  {col['cid']:2}. {col['name']:25} {col['type']:15} {null_text} {pk_text}")
            
            # Conteo de registros
            count = pd.read_sql_query(f'SELECT COUNT(*) as count FROM "{table_name}"', conn).iloc[0,0]
            print(f"\nTotal registros: {count:,}")
            
        except Exception as e:
            print(f"❌ Error describiendo tabla: {e}")
        
        conn.close()
    
    def sample_data(self, table_name, limit=5):
        """Muestra datos de muestra de una tabla"""
        conn = self.get_connection()
        
        print(f"\n📄 MUESTRA DE DATOS: {table_name} (primeros {limit} registros)")
        print("=" * 80)
        
        try:
            sample = pd.read_sql_query(f'SELECT * FROM "{table_name}" LIMIT {limit}', conn)
            if len(sample) > 0:
                print(sample.to_string(index=False, max_cols=10))
            else:
                print("⚠️  La tabla está vacía")
                
        except Exception as e:
            print(f"❌ Error obteniendo muestra: {e}")
        
        conn.close()
    
    def search_data(self, table_name, column, value):
        """Busca datos específicos en una tabla"""
        conn = self.get_connection()
        
        print(f"\n🔍 BÚSQUEDA: {table_name}.{column} = '{value}'")
        print("=" * 60)
        
        try:
            query = f'SELECT * FROM "{table_name}" WHERE "{column}" LIKE "%{value}%" LIMIT 10'
            results = pd.read_sql_query(query, conn)
            
            if len(results) > 0:
                print(f"Encontrados {len(results)} resultados:")
                print(results.to_string(index=False))
            else:
                print("❌ No se encontraron resultados")
                
        except Exception as e:
            print(f"❌ Error en búsqueda: {e}")
        
        conn.close()
    
    def interactive_menu(self):
        """Menú interactivo para explorar la base de datos"""
        while True:
            print("\n" + "="*60)
            print("🗄️  EXPLORADOR INTERACTIVO - BASE DE DATOS REASIS")
            print("="*60)
            print("1. 📋 Listar todas las tablas")
            print("2. 🔍 Describir estructura de tabla")
            print("3. 📄 Ver muestra de datos")
            print("4. 🔎 Buscar en tabla")
            print("5. 🚪 Salir")
            
            choice = input("\nSelecciona una opción (1-5): ").strip()
            
            if choice == '1':
                self.list_tables()
                
            elif choice == '2':
                table = input("Nombre de tabla: ").strip()
                if table:
                    self.describe_table(table)
                    
            elif choice == '3':
                table = input("Nombre de tabla: ").strip()
                if table:
                    try:
                        limit = int(input("Número de registros (default 5): ") or "5")
                        self.sample_data(table, limit)
                    except ValueError:
                        self.sample_data(table)
                        
            elif choice == '4':
                table = input("Nombre de tabla: ").strip()
                column = input("Nombre de columna: ").strip()
                value = input("Valor a buscar: ").strip()
                if table and column and value:
                    self.search_data(table, column, value)
                    
            elif choice == '5':
                print("👋 ¡Hasta luego!")
                break
                
            else:
                print("❌ Opción inválida")
            
            input("\nPresiona Enter para continuar...")

def main():
    """Función principal"""
    try:
        explorer = ReasisDatabaseExplorer()
        
        # Si se ejecuta con argumentos, usar modo comando
        import sys
        if len(sys.argv) > 1:
            if sys.argv[1] == "list":
                explorer.list_tables()
            elif sys.argv[1] == "describe" and len(sys.argv) > 2:
                explorer.describe_table(sys.argv[2])
            elif sys.argv[1] == "sample" and len(sys.argv) > 2:
                limit = int(sys.argv[3]) if len(sys.argv) > 3 else 5
                explorer.sample_data(sys.argv[2], limit)
        else:
            # Modo interactivo
            explorer.interactive_menu()
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()