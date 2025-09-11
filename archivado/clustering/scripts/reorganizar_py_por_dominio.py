#!/usr/bin/env python3
# Reorganiza .py del raíz por dominios dentro de scripts/

from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path('.').resolve()
SCRIPTS = ROOT / 'scripts'

MAPEO = [
    (['siagie', 'procesar_siagie', 'procesador_siagie', 'cargador_siagie', 'consolidador_siagie', 'analizar_datos_siagie', 'analizar_historico_siagie', 'debug_siagie'], 'scripts/siagie'),
    (['docente', 'docentes', 'integrar_docentes', 'imputador_docentes', 'explorar_source_docentes', 'finalizar_integracion_docentes', 'analizar_internet_docentes', 'crear_tabla_docentes'], 'scripts/docentes'),
    (['pobreza', 'vincular_pobreza', 'enriquecedor_matricula_siagie', 'enriquecer_instituciones_con_pobreza'], 'scripts/pobreza'),
    (['institucion', 'instituciones', 'buscar_info_instituciones', 'explorar_instituciones'], 'scripts/instituciones'),
    (['indices', 'gestor_indices_metodologicos', 'migrador_indices_metodologicos', 'imputar_y3_pr', 'identificar_y3_pr', 'aplicar_y3_pr', 'calculador_x11_red', 'calculador_tendencia_matricula'], 'scripts/indices'),
    (['analisis', 'analizar_', 'investigar_', 'explorar_', 'generador_reportes'], 'scripts/analisis'),
    (['limpiar', 'limpiador_', 'limpiar_', 'ajustador_', 'corrector_', 'corregir_', 'completar_', 'integrar_variables_contextuales'], 'scripts/calidad'),
]

EXCLUDE = {'scripts/reorganizar_py_por_dominio.py', 'scripts/reorganizar_raiz.py'}


def destino_para(nombre: str) -> Path:
    low = nombre.lower()
    for patrones, carpeta in MAPEO:
        if any(p in low for p in patrones):
            return ROOT / carpeta
    return ROOT / 'scripts' / 'misc'


def move_files() -> None:
    moved = []
    SCRIPTS.mkdir(parents=True, exist_ok=True)
    for p in ROOT.iterdir():
        if not p.is_file() or p.suffix.lower() != '.py':
            continue
        rel = p.relative_to(ROOT).as_posix()
        if rel in EXCLUDE or rel.startswith('scripts/'):
            continue
        target_dir = destino_para(p.name)
        target_dir.mkdir(parents=True, exist_ok=True)
        dest = target_dir / p.name
        if dest.exists():
            # evitar colisión
            dest = target_dir / f"{p.stem}_migrado{p.suffix}"
        shutil.move(str(p), str(dest))
        moved.append((str(p), str(dest)))
    print(f"Archivos .py movidos: {len(moved)}")
    for a, b in moved:
        print(f"- {a} -> {b}")


if __name__ == '__main__':
    move_files()



