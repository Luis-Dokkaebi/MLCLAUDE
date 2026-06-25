# 0. REVIEW FINDINGS: Auditoría de las Especificaciones (Spec Review)

Este documento es una **revisión crítica de las propias especificaciones** (`1_SPECIFICATIONS` … `6_KEYGEN_GUIDE`) contrastadas contra el código real en `src/`, `config/`, `tests/` y `requirements.txt`.

Su objetivo es registrar las inconsistencias, sobrepromesas y desalineaciones spec↔código detectadas, y servir como backlog de saneamiento de la documentación. Las correcciones documentales ya aplicadas se marcan con ✅; las que requieren trabajo de implementación se marcan con ⏳.

> **Fecha de revisión:** 2026-06-22
> **Alcance:** Documentos `SPEC/*.md`, `docs/security_audit_report.md`, `requirements.txt`, `src/`, `config/`.

---

## Veredicto general

Las specs son **sólidas y bien estructuradas**: flujo Specs-Driven completo (Spec → Plan → Tasks → Implementation → Review → Keygen), con Definition of Done verificable por tarea, matriz de riesgos, diagramas de secuencia, máquinas de estado y guía de estilo. Y no son humo: existe `tests/` con cobertura que mapea a las tareas, más un reporte de auditoría OWASP real.

Las observaciones siguientes **no invalidan** el diseño; corrigen inconsistencias internas, desalineaciones con el código y afirmaciones de seguridad sobredimensionadas.

---

## 🔴 P0 — Bloqueantes / bugs reales

### P0-1 ✅ Conflicto de merge sin resolver en `requirements.txt`
El archivo contenía marcadores `<<<<<<< HEAD … ======= … >>>>>>>`, lo que hace fallar `pip install -r requirements.txt`. Además las dos mitades se contradecían (stack B2B fijado vs. stack legacy con `face_recognition`, `reportlab`, `plotly`).
**Resuelto:** se unificó a la **unión real** de dependencias que el código importa (`face_recognition`, `matplotlib`, `seaborn`, `tkcalendar`, `pillow`, `numpy`) + el stack B2B fijado + `pycryptodome` (usado por `drm.py` y los scripts de keygen). Se eliminaron `reportlab`/`plotly` por no estar importados en `src/`.

### P0-2 ✅ SQLCipher exigido por la spec — resuelto vía el fallback autorizado (AES-256 at-rest)
SPEC 1.6.3 y TASK-4.3 exigen `pysqlcipher3` + `PRAGMA key`; la auditoría 5.3.2 exige que el `.db` aparezca cifrado. `pysqlcipher3` no compila de forma fiable en Windows sin Build Tools/OpenSSL, por lo que se adoptó **formalmente el fallback de TASK-0.1**: cifrado a nivel de aplicación con AES-256-GCM.
**Resuelto:** `src/security/db_crypto.py::EncryptedDBVault` cifra el `local_tracking.db` completo a `local_tracking.enc_db` en reposo (blob ilegible para DB Browser → cumple 5.3.2), con clave derivada del `Machine_Hash` (WMI). `main_ui` lo descifra al montar el Tenant y lo re-cifra al cerrar. Cobertura: `tests/test_db_encryption.py`. Ver `4_IMPLEMENTATION` §4.6.

### P0-3 ✅ El snippet de referencia enseña el anti-patrón que la spec prohíbe
En `4_IMPLEMENTATION` §4.3 el ejemplo hacía `conn.execute(f"PRAGMA key = '{self.encryption_key}';")` — interpolación por f-string en SQL, justo lo prohibido por la directiva anti-vibe-hacking §4.0(#3) y por la auditoría A03.
**Resuelto:** el snippet ahora usa `PRAGMA key` parametrizado (placeholder) y documenta el formato hex blob.

---

## 🟠 P1 — Inconsistencias internas entre documentos

### P1-1 ✅ Rutas de Tenant contradictorias (cuatro variantes)
Existían a la vez:
- `Tenants/<ID>/db/` (árbol §1.3.1) — **sin** `data/`
- `Tenants/[ID]/data/db` (PLANNING §3.2)
- `Tenants/[ID]/data/reportes/` (REVIEW §5.1.1)
- `Tenants/Norte/data/export/` (REVIEW §5.4)

**Ruta canónica (la que implementa `config/path_utils.py::get_tenant_path`):**
```
%APPDATA%/OficinaEficiencia/Tenants/<TenantID>/
├── db/
├── faces/
├── snapshots/
├── zonas/
└── reportes/        # exportaciones XLSX/PDF
```
No hay segmento `data/`. Todos los documentos se alinearon a esta forma.

### P1-2 ✅ Algoritmo de hash inconsistente
§1.6.1 decía **SHA-3_256**, TASK-4.1.3 decía "SHA-3/SHA-256", y el código (`drm.py`) usa **SHA-256**. Se unificó a **SHA-256** en toda la documentación para coincidir con la implementación.

### P1-3 ✅ Descripción criptográfica RSA incorrecta ("cifrar" en vez de "firmar")
§1.6.2 describía "*Cifrarás* el Machine_Hash con la **llave privada**" y el cliente "*descifra* con la pública". Eso es firma/verificación digital, no cifrado — y contradecía a `6_KEYGEN_GUIDE`, que correctamente usa `pkcs1_15.sign()`. Se reescribió §1.6.2 en términos de **firmar/verificar**.

### P1-4 ✅ `pycryptodome` ausente del freeze de dependencias
TASK-0.1 fijaba `cryptography` pero `6_KEYGEN_GUIDE`, `drm.py` y los scripts dependen de `pycryptodome`. Se añadió `pycryptodome==3.20.0` al freeze de TASK-0.1 y a `requirements.txt`.

### P1-5 ✅ Numeraciones duplicadas
`5_REVIEW` tenía dos secciones "5.6"; `3_TASKS` tenía dos "Sub-tarea 0.1.2". Renumeradas (`5.6`/`5.7`, `0.1.2`/`0.1.3`).

---

## 🟡 P2 — Sobrepromesa de seguridad (riesgo de credibilidad B2B)

### P2-1 ⏳ "Grado militar" / "matemáticamente inquebrantable"
PyArmor + clave pública embebida **no** es inquebrantable. El vector real no es decompilar `drm.py`, sino **parchear al llamador** (`if drm.is_valid()` → NOP) o hookear en runtime. Se recomienda atenuar el lenguaje a "disuasión razonable contra copia casual". *(Pendiente de decisión del propietario sobre el tono comercial.)*

### P2-2 ⏳ Clave de integridad biométrica débil (`platform.node()`)
La auditoría F-03 deriva el HMAC del **hostname**, trivialmente modificable, lo que contradice el discurso de "huella de hardware inmutable". Debería derivarse del mismo `machine_id` (WMI) que usa el DRM.

### P2-3 ⏳ Hardware binding sin ruta de recuperación
Si la BD se cifra con `Machine_Hash` y el cliente cambia disco/placa, la licencia **y** la BD quedan irrecuperables. Falta una spec de *recovery / re-key* (re-emisión de licencia + re-cifrado/migración de la base de datos). Generador garantizado de tickets de soporte en B2B.

---

## ⚪ P3 — Realismo técnico

### P3-1 ⏳ 16 cámaras con YOLO + face_recognition en CPU
El GIL impide paralelismo real de inferencia CPU-bound entre *threads*. El skip-frame ayuda, pero un modelo por hilo no escala. Recomendación: definir un **pool de inferencia compartido** (o `multiprocessing`) y publicar números realistas de cámaras por perfil de hardware.

### P3-2 ✅ Concurrencia SQLite — WAL llevado al código (RESUELTO COMPLETO)
`database_manager.py` aplica `PRAGMA journal_mode=WAL` + `synchronous=NORMAL` en `_create_table()` (persiste como propiedad de la BD) y expone `_get_connection()` con `WAL` + `busy_timeout=30000`.
**✅ Resuelto completo (2026-06-25):** se aplicó **CR-03** — **todos** los métodos de lectura/escritura (`insert_record`, `insert_snapshot`, `insert_state`, `update_attendance`, `get_all_records`, `employee_exists`, `save_employee_profile`, `get_all_employee_names`, `get_unique_employees`, `get_attendance_report`, `get_efficiency_report`, `get_employee_snapshots`, `anonymize_employee`, `delete_employee_profile`) más `_create_table()` ahora usan `self._get_connection()` con WAL + `busy_timeout=30000`. Verificado con `grep -n "sqlite3.connect(self.db_path)"` (0 resultados) y prueba de estrés (2 escritores + 1 lector → 1000 filas, 0 `OperationalError`). Ver **CR-03** en `SPEC/8_PRODUCTION_CODE_REVIEW.md`.

---

## 🧩 Gaps (faltantes del todo en las specs)

1. **Cumplimiento legal de biometría** — lo más serio para B2B: consentimiento, DPIA, retención/borrado, base legal (GDPR Art. 9 / leyes locales de datos biométricos). Solo hay una mención de pasada. Requiere sección propia.
2. **Cifrado en reposo de `.pkl`/`.npz`** — hoy la biometría tiene integridad (HMAC) pero no confidencialidad.
3. **CI/CD real** — se menciona pipeline pero no existe (`.github/workflows`).
4. **Backup/restore + migración de esquema con BD cifrada** — PLANNING §2.5 lo menciona sin detalle de re-key.
5. **Auto-update del `.exe`** y rotación operativa de salt/llaves (REVIEW §5.5 lo insinúa, sin mecanismo).

---

## Resumen de estado

| ID | Severidad | Estado |
|---|---|---|
| P0-1 requirements.txt merge | 🔴 | ✅ Corregido |
| P0-2 SQLCipher no implementado | 🔴 | ✅ Resuelto (fallback AES-256 at-rest) |
| P0-3 f-string en PRAGMA key (snippet) | 🔴 | ✅ Corregido |
| P1-1 rutas de Tenant | 🟠 | ✅ Canonizado |
| P1-2 hash SHA-3 vs SHA-256 | 🟠 | ✅ Unificado |
| P1-3 RSA cifrar→firmar | 🟠 | ✅ Corregido |
| P1-4 pycryptodome en freeze | 🟠 | ✅ Añadido |
| P1-5 numeraciones duplicadas | 🟠 | ✅ Corregido |
| P2-1 lenguaje "grado militar" | 🟡 | ⏳ Decisión propietario |
| P2-2 HMAC desde hostname | 🟡 | ⏳ Pendiente (código) |
| P2-3 recovery hardware binding | 🟡 | ⏳ Pendiente (spec+código) |
| P3-1 16 cámaras CPU / GIL | ⚪ | ⏳ Pendiente (diseño) |
| P3-2 WAL no aplicado | ⚪ | ✅ Resuelto completo (CR-03) |

Las correcciones documentales (✅) se aplicaron directamente sobre los `SPEC/*.md` correspondientes en este mismo cambio. Los ítems ⏳ requieren trabajo de implementación o una decisión de negocio y quedan como backlog priorizado.
