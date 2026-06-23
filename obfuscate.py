#!/usr/bin/env python
# obfuscate.py
# ===================================================================
# TASK-4.4: Inyeccion de Ofuscacion PyArmor en el Build Pipeline
#
# Script pre-build (SECOPS) que se ejecuta ANTES de PyInstaller:
#   1. Limpia los directorios de build previos (build/, dist/obfuscated/).
#   2. Ofusca src/ y config/ con PyArmor 8.x en modo restrictivo.
#
# Salida: dist/obfuscated/{src,config}/...  + pyarmor_runtime_000000/
# Esa ruta es exactamente la que consume gui_app.spec (Analysis entry =
# dist/obfuscated/src/main_ui.py).
#
# ANTI-VIBE HACKING: No se permite saltar este paso "para simplificar".
# El binario B2B debe distribuirse SIEMPRE ofuscado (SPEC 1.6.3).
# ===================================================================

import os
import shutil
import subprocess
import sys

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join("dist", "obfuscated")

# Paquetes del proyecto a ofuscar (src y config son importados por main_ui).
SOURCE_PACKAGES = ["src", "config"]

# Directorios a limpiar antes de regenerar.
CLEAN_DIRS = ["build", OUTPUT_DIR]


def build_pyarmor_command():
    """
    Construye el comando PyArmor 8.x. Separado para poder testearlo sin
    necesidad de tener PyArmor instalado.

    pyarmor gen -O dist/obfuscated --enable-jit --restrict 1 src config
    """
    return [
        "pyarmor", "gen",
        "-O", OUTPUT_DIR,
        "--enable-jit",       # bytecode JIT C irreversible (SPEC 1.6.3)
        "--restrict", "1",    # modo restrictivo: los .py ofuscados no se pueden importar fuera
        *SOURCE_PACKAGES,
    ]


def clean_previous_builds():
    """Elimina build/ y dist/obfuscated/ para evitar artefactos obsoletos."""
    for d in CLEAN_DIRS:
        full = os.path.join(PROJECT_ROOT, d)
        if os.path.isdir(full):
            print(f"[obfuscate] Limpiando {d}/ ...")
            shutil.rmtree(full, ignore_errors=True)


def run_obfuscation():
    """Ejecuta la ofuscacion PyArmor. Aborta el build si PyArmor falla."""
    if shutil.which("pyarmor") is None:
        print("[obfuscate] ERROR: 'pyarmor' no esta instalado o no esta en el PATH.")
        print("            Instale con: pip install pyarmor==8.4.6")
        return 1

    clean_previous_builds()
    cmd = build_pyarmor_command()
    print(f"[obfuscate] Ofuscando {SOURCE_PACKAGES} -> {OUTPUT_DIR}/")
    print(f"[obfuscate] $ {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=PROJECT_ROOT)
    if result.returncode != 0:
        print("[obfuscate] ERROR: La ofuscacion PyArmor fallo. Build abortado.")
        return result.returncode

    print(f"[obfuscate] OK. Codigo ofuscado disponible en {OUTPUT_DIR}/")
    return 0


if __name__ == "__main__":
    sys.exit(run_obfuscation())
