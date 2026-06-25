# src/models/model_verifier.py
# ===================================================================
# TASK-5.2: Verificacion de Integridad de Modelos AI (Anti-Tamper)
#
# Calcula el SHA-256 del modelo distribuido (yolov8n.pt) en tiempo de
# ejecucion y lo compara contra el hash pre-aprobado embebido en el
# codigo. En produccion, PyArmor (TASK-4.4) ofusca este modulo,
# convirtiendo EXPECTED_MODEL_SHA256 en bytecode C irreversible.
#
# Si el modelo fue reemplazado por un modelo falso o con backdoor, el
# hash no coincide y el CameraWorker aborta la inferencia (SPEC 5.2 DoD).
#
# ANTI-VIBE HACKING: No relajar la verificacion devolviendo True por
# defecto ni capturar la excepcion de mismatch silenciosamente en el
# llamador.
# ===================================================================

import hashlib
import hmac
import logging
import os
from typing import Optional

_logger = logging.getLogger(__name__)

# Hash SHA-256 pre-aprobado del modelo oficial yolov8n.pt distribuido con el VMS.
# Generado con: hashlib.sha256(open('yolov8n.pt','rb').read()).hexdigest()
# (En produccion ofuscado por PyArmor — SPEC 1.6.3 / TASK-5.2.1)
EXPECTED_MODEL_SHA256 = "f59b3d833e2ff32e194b5bb8e08d211dc7c5bdf144b90d2c8412c47ccfc83b36"

_CHUNK_SIZE = 1 << 20  # 1 MiB — lectura por bloques para no cargar el .pt completo en RAM


class ModelIntegrityError(RuntimeError):
    """Se lanza cuando el modelo AI en disco no coincide con el hash pre-aprobado."""


def compute_model_hash(model_path: str) -> str:
    """
    Calcula el SHA-256 del archivo de modelo leyendo en bloques.

    Lee de forma binaria estricta (SPEC 5.2.2). Compatible con rutas
    resueltas por get_resource_path() (sys._MEIPASS en binarios B2B).
    """
    if not os.path.isfile(model_path):
        raise FileNotFoundError(f"Modelo AI no encontrado para verificacion: {model_path}")

    sha = hashlib.sha256()
    with open(model_path, "rb") as fh:
        for chunk in iter(lambda: fh.read(_CHUNK_SIZE), b""):
            sha.update(chunk)
    return sha.hexdigest()


def verify_model(model_path: str, expected_hash: Optional[str] = None) -> bool:
    """
    Verifica que el modelo en disco coincida con el hash pre-aprobado.

    Args:
        model_path: Ruta al archivo .pt (resuelta via get_resource_path).
        expected_hash: Hash esperado; por defecto EXPECTED_MODEL_SHA256.

    Returns:
        True si el hash coincide exactamente.
    """
    expected = (expected_hash or EXPECTED_MODEL_SHA256).lower().strip()
    actual = compute_model_hash(model_path).lower()
    match = hmac.compare_digest(actual, expected)
    if not match:
        _logger.error(
            "[ModelVerifier] Integridad del modelo COMPROMETIDA. "
            "esperado=%s... actual=%s...", expected[:12], actual[:12]
        )
    else:
        _logger.info("[ModelVerifier] Integridad del modelo AI verificada (SHA-256 OK).")
    return match


def assert_model_integrity(model_path: str, expected_hash: Optional[str] = None) -> None:
    """
    Igual que verify_model pero lanza ModelIntegrityError si no coincide.
    Usado por CameraWorker para abortar la inferencia ante manipulacion (SPEC 5.2 DoD).
    """
    if not verify_model(model_path, expected_hash):
        raise ModelIntegrityError(
            "El modelo AI ha sido manipulado o reemplazado. "
            "Inferencia abortada por seguridad (TASK-5.2)."
        )
