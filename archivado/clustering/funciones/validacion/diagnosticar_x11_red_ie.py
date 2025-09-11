# funciones/validacion/diagnosticar_x11_red_ie.py
import sqlite3, pandas as pd, glob, sys

def diagnosticar(cod):
    cod = str(cod)
    conn = sqlite3.connect('reasis_database.db')
    print(f'--- Diagnóstico X11_RED para codigo_modular={cod} ---')

    q1 = f"""
    SELECT codigo_modular, nombre_institucion, total_alumnos, total_docentes, X11_RED
    FROM instituciones_educativas
    WHERE codigo_modular = ?
    """
    df_ie = pd.read_sql_query(q1, conn, params=[cod])
    print('\n[instituciones_educativas]')
    print(df_ie if not df_ie.empty else 'No existe en la tabla.')

    q2 = f"""
    SELECT CODIGO_MODULAR, NOMBRE_INSTITUCION, X11_RED
    FROM indices_metodologicos
    WHERE CODIGO_MODULAR = ?
    """
    df_idx = pd.read_sql_query(q2, conn, params=[cod])
    print('\n[indices_metodologicos]')
    print(df_idx if not df_idx.empty else 'No existe en la tabla.')

    files = sorted(glob.glob('temp_data/x11_red_preliminar_*.csv'))
    if files:
        csv = files[-1]
        df_csv = pd.read_csv(csv, dtype={'codigo_modular': str})
        df_row = df_csv[df_csv['codigo_modular'] == cod]
        print(f'\n[CSV preliminar] {csv}')
        print(df_row if not df_row.empty else 'No aparece en el CSV.')
    else:
        print('\n[CSV preliminar] No encontrado.')

    if not df_ie.empty:
        ta = df_ie.at[0, 'total_alumnos']
        td = df_ie.at[0, 'total_docentes']
        if pd.isna(ta) or pd.isna(td) or ta <= 0 or td <= 0:
            print('\nCAUSA: total_alumnos/total_docentes nulos o <= 0 (excluida del cálculo).')
        else:
            print(f'\nVALOR ESPERADO: X11_RED = {ta} / {td} = {float(ta)/float(td):.6f}')

    conn.close()

if __name__ == '__main__':
    cod = sys.argv[1] if len(sys.argv) > 1 else '2533906'
    diagnosticar(cod)
