import sqlite3

def imputar_x12_toe():
    conn = sqlite3.connect('reasis_database.db')
    cur = conn.cursor()
    
    # Caso específico RER FA 48
    cur.execute("""
        UPDATE indices_metodologicos 
        SET X12_TOE = 1 
        WHERE CODIGO_MODULAR = '3916573'
    """)
    
    # Resto de casos
    cur.execute("""
        UPDATE indices_metodologicos 
        SET X12_TOE = 
        CASE 
            WHEN (SELECT total_docentes FROM instituciones_educativas 
                  WHERE codigo_modular = indices_metodologicos.CODIGO_MODULAR) = 1 THEN 1  -- UNIDOCENTE
            WHEN (SELECT total_docentes FROM instituciones_educativas 
                  WHERE codigo_modular = indices_metodologicos.CODIGO_MODULAR) = 2 THEN 2  -- BIDOCENTE
            WHEN (SELECT es_rural FROM instituciones_educativas 
                  WHERE codigo_modular = indices_metodologicos.CODIGO_MODULAR) = 1 THEN 3  -- MULTIGRADO
            ELSE 4  -- POLIDOCENTE
        END
        WHERE X12_TOE IS NULL
        AND CODIGO_MODULAR IN (SELECT codigo_modular FROM instituciones_educativas)
    """)
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    imputar_x12_toe()
    print("Imputación X12_TOE completada")