# tests/test_db_encryption.py
# TASK-4.3 / Auditoria 5.3.2 DoD: el artefacto en reposo (.enc_db) NO es una
# BD SQLite legible (DB Browser lo veria corrupto), pero la app la descifra
# y lee perfectamente. Clave derivada del hardware: no portable a otra PC.

import os
import sys
import sqlite3
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.security.db_crypto import (
    EncryptedDBVault, derive_db_key, enc_path_for, is_sqlite_file,
)


def _make_plain_db(path):
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE empleados (id INTEGER, nombre TEXT)")
    conn.execute("INSERT INTO empleados VALUES (1, 'Juan Perez')")
    conn.commit()
    conn.close()


def test_locked_db_is_not_readable_as_sqlite(tmp_path):
    db = str(tmp_path / "local_tracking.db")
    _make_plain_db(db)
    assert is_sqlite_file(db) is True  # en claro es legible

    vault = EncryptedDBVault(db, key=derive_db_key("a" * 64))
    enc = vault.lock()

    # Auditoria 5.3.2: el .enc_db NO se abre como SQLite (aparece corrupto).
    assert os.path.exists(enc)
    assert enc.endswith(".enc_db")
    assert is_sqlite_file(enc) is False
    # El .db en claro fue eliminado del reposo.
    assert not os.path.exists(db)
    # No hay nombres de empleados legibles en el blob.
    assert b"Juan Perez" not in open(enc, "rb").read()


def test_unlock_restores_identical_data(tmp_path):
    db = str(tmp_path / "local_tracking.db")
    _make_plain_db(db)
    key = derive_db_key("a" * 64)

    EncryptedDBVault(db, key=key).lock()
    assert not os.path.exists(db)

    EncryptedDBVault(db, key=key).unlock()
    assert is_sqlite_file(db) is True
    conn = sqlite3.connect(db)
    row = conn.execute("SELECT nombre FROM empleados WHERE id=1").fetchone()
    conn.close()
    assert row[0] == "Juan Perez"


def test_wrong_hardware_key_cannot_decrypt(tmp_path):
    db = str(tmp_path / "local_tracking.db")
    _make_plain_db(db)
    EncryptedDBVault(db, key=derive_db_key("rightmachine")).lock()

    wrong = EncryptedDBVault(db, key=derive_db_key("othermachine"))
    with pytest.raises(ValueError):
        wrong.unlock()


def test_unlock_noop_when_no_vault(tmp_path):
    db = str(tmp_path / "local_tracking.db")
    # Primera ejecucion: no hay .enc_db -> unlock no falla y no crea nada.
    EncryptedDBVault(db).unlock()
    assert not os.path.exists(db)


def test_key_is_deterministic_per_machine():
    assert derive_db_key("machineA") == derive_db_key("machineA")
    assert derive_db_key("machineA") != derive_db_key("machineB")
    assert len(derive_db_key("machineA")) == 32  # AES-256
