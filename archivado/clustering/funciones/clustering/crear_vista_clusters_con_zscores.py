#!/usr/bin/env python3
"""
Crea una vista que une resultados del clustering avanzado con z-scores
para facilitar reportes y exportaciones.

Vista: vw_clusters_zscores_avanzado
"""

import sqlite3


def main() -> None:
    conn = sqlite3.connect("reasis_database.db")
    try:
        cur = conn.cursor()
        # Eliminar vista si existe (SQLite no soporta IF EXISTS en todas las versiones para VIEW)
        try:
            cur.execute("DROP VIEW IF EXISTS vw_clusters_zscores_avanzado")
        except Exception:
            pass

        # Construir lista de columnas ZS dinámicamente
        cols = [
            r[1] for r in cur.execute("PRAGMA table_info(indices_zscores_avanzado)").fetchall()
            if r[1] != "CODIGO_MODULAR"
        ]
        select_cols = ",\n       ".join([f"iz.'{c}' AS '{c}'" for c in cols])

        sql = f"""
        CREATE VIEW vw_clusters_zscores_avanzado AS
        SELECT 
            rc.codigo_modular,
            ie.nombre_institucion,
            rc.numero_fya,
            rc.cluster_asignado,
            rc.k_clusters,
            rc.silhouette_score,
            rc.tipologia_label,
            {select_cols}
        FROM resultados_clustering_avanzado rc
        LEFT JOIN indices_zscores_avanzado iz
            ON iz.CODIGO_MODULAR = rc.codigo_modular
        LEFT JOIN indices_metodologicos ie
            ON ie.CODIGO_MODULAR = rc.codigo_modular
        """

        cur.execute(sql)
        conn.commit()
        print("[OK] Vista vw_clusters_zscores_avanzado creada")
    finally:
        conn.close()


if __name__ == "__main__":
    main()


