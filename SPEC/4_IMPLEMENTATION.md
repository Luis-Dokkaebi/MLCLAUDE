# 4. IMPLEMENTATION: Manual de Referencia de Código, Patrones B2B y SecOps

Este manual contiene los bloques de construcción (Snippets) y las estructuras de clases exactas que deben utilizarse para implementar el escalamiento B2B de "Oficina Eficiencia". Las soluciones aquí expuestas han sido diseñadas para prevenir bloqueos de I/O, fugas de memoria (OOM), y ataques de ingeniería inversa.

**🚨 DIRECTIVA ESTRICTA DE IMPLEMENTACIÓN (ANTI-VIBE HACKING PROTOCOL) 🚨**
> *Cualquier IA que genere código basándose en este documento DEBE respetar la firma de estos métodos y las librerías indicadas.* **PROHIBICIONES ABSOLUTAS:**
> 1. No uses `time.sleep()` en el hilo principal de la UI (`CustomTkinter`).
> 2. No almacenes contraseñas, claves privadas RSA o hashes esperados en texto plano (`expected_hash = "12345"`).
> 3. No uses f-strings sin sanitizar en sentencias SQL (`f"SELECT * FROM users WHERE name = '{name}'"`). Usa siempre parametrización (`?` o `:nombre`).
> 4. No captures excepciones genéricas (`except Exception: pass`) ocultando errores críticos de WMI o SQLite.

---

## 4.1 Patrón Productor-Consumidor (Gestión de Colas de Memoria Limitada)

El hilo productor (`CameraWorker`) procesa los frames de OpenCV con YOLOv8 y los deposita en una cola thread-safe. Si el hilo consumidor (`UI`) es lento renderizando (ej. una PC sin GPU dedicada), la cola se llenaría y causaría un *Out of Memory (OOM)*. Se aplica un **Drop Frame Protocol**.

```python
# src/tracking/camera_worker.py
import cv2
import queue
import threading
import time
from typing import Tuple, Any
import numpy as np

class CameraWorker(threading.Thread):
    def __init__(self, camera_id: int | str, frame_queue: queue.Queue, model: Any, fps_limit: int = 15):
        super().__init__(daemon=True) # El hilo muere al cerrar la app
        self.camera_id = camera_id
        self.frame_queue = frame_queue
        self.model = model
        self.fps_limit = fps_limit
        self.running = False
        self._delay = 1.0 / self.fps_limit

    def run(self):
        self.running = True
        cap = cv2.VideoCapture(self.camera_id)
        
        # Optimizacin OpenCV B2B: Forzar resolucion (opcional)
        # cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        # cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

        while self.running:
            start_time = time.time()
            ret, frame = cap.read()
            
            if not ret:
                # Log de reconexion en entorno Enterprise (ej. RTSP perdido)
                time.sleep(2.0)
                cap = cv2.VideoCapture(self.camera_id)
                continue

            # Inferencia YOLOv8
            results = self.model(frame, verbose=False)
            annotated_frame = results[0].plot() # numpy array (BGR)
            
            # --- DROP FRAME PROTOCOL (Anti-Memory Leak) ---
            try:
                # Intenta encolar sin bloquear. Si est llena (UI lagueada), entra al except
                self.frame_queue.put_nowait((self.camera_id, annotated_frame))
            except queue.Full:
                # Se descarta este frame para que la memoria no colapse
                pass 
                
            # Limitar FPS para ahorrar CPU (Artificial Throttle)
            elapsed_time = time.time() - start_time
            time_to_wait = self._delay - elapsed_time
            if time_to_wait > 0:
                time.sleep(time_to_wait)
                
        cap.release()

    def stop(self):
        self.running = False
```

## 4.2 Consumidor Asíncrono en CustomTkinter (El "Grid View")

El hilo principal de `CustomTkinter` consumirá las colas sin bloquearse, usando el método nativo `.after()`.

```python
# src/gui_app.py o src/main_ui.py
import customtkinter as ctk
import queue
from PIL import Image, ImageTk
import cv2

class DashboardFrame(ctk.CTkFrame):
    def __init__(self, master, camera_queues: dict):
        super().__init__(master)
        self.camera_queues = camera_queues # dict: {cam_id: queue.Queue}
        self.video_labels = {}
        
        # Configurar Grid de NxN dinmico (Ejemplo para 4 cmaras, 2x2)
        self.grid_rowconfigure((0, 1), weight=1)
        self.grid_columnconfigure((0, 1), weight=1)
        
        # Inicializar Labels Negros
        for i, cam_id in enumerate(self.camera_queues.keys()):
            lbl = ctk.CTkLabel(self, text="")
            row = i // 2
            col = i % 2
            lbl.grid(row=row, column=col, sticky="nsew", padx=2, pady=2)
            self.video_labels[cam_id] = lbl
            
            # Binding para Single View (Doble Clic)
            lbl.bind("<Double-1>", lambda event, cid=cam_id: self.toggle_single_view(cid))

        # Iniciar loop asncrono de actualizacin de frames (ej. a 30 FPS = ~33ms)
        self.update_frames()

    def update_frames(self):
        for cam_id, q in self.camera_queues.items():
            try:
                # Vacia la cola hasta el frame mas reciente (Descarte de atraso)
                # En entornos B2B preferimos ver el "Ahora" saltando frames intermedios
                frame_data = None
                while not q.empty():
                    frame_data = q.get_nowait()
                
                if frame_data is not None:
                    _, bgr_frame = frame_data
                    # Convertir OpenCV (BGR) a Pillow (RGB)
                    rgb_frame = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
                    
                    # Redimensionar al tamao actual del Label
                    lbl = self.video_labels[cam_id]
                    target_w = lbl.winfo_width()
                    target_h = lbl.winfo_height()
                    if target_w > 10 and target_h > 10:
                        rgb_frame = cv2.resize(rgb_frame, (target_w, target_h))
                    
                    pil_image = Image.fromarray(rgb_frame)
                    ctk_image = ctk.CTkImage(pil_image, size=(target_w, target_h))
                    
                    # Actualizar Label en UI
                    lbl.configure(image=ctk_image)
                    lbl.image = ctk_image # Prevenir Garbage Collection del CPython
                    
            except Exception as e:
                # Loggear silenciosamente sin crashear la UI
                pass

        # Reprogramar la funcin en el Hilo Principal en 33ms
        self.after(33, self.update_frames)

    def toggle_single_view(self, cam_id):
        # Lgica para ocultar (.grid_forget()) los demas labels y expandir cam_id al 100%
        pass
```

## 4.3 Módulo DRM: Fingerprint WMI y Cifrado de SQLite (SQLCipher)

Este bloque extrae la identidad del hardware y la usa para validar licencias offline y cifrar la base de datos `local_tracking.db` mediante `pysqlcipher3`.

```python
# src/security/drm.py
import wmi
import hashlib
import uuid
from typing import Optional

class DRMValidator:
    @staticmethod
    def get_hardware_fingerprint() -> str:
        """Extrae un hash inmutable del hardware usando WMI en Windows."""
        try:
            c = wmi.WMI()
            
            # CPU
            processors = c.Win32_Processor()
            cpu_id = processors[0].ProcessorId.strip() if processors else "UNKNOWN_CPU"
            
            # Motherboard
            boards = c.Win32_BaseBoard()
            board_sn = boards[0].SerialNumber.strip() if boards else "UNKNOWN_BOARD"
            
            # Dispositivo Principal de Arranque (Disco)
            disks = c.Win32_DiskDrive()
            disk_sn = disks[0].SerialNumber.strip() if disks else "UNKNOWN_DISK"
            
            raw = f"B2B_{cpu_id}_{board_sn}_{disk_sn}"
            
        except Exception:
            # Fallback seguro (Anti-Vibe Hacking: No fallar con str vacio, usar MAC)
            mac = uuid.getnode()
            raw = f"B2B_FALLBACK_{mac}"
            
        # Hasheo con Salt Ofuscado
        salt = b"0f1c1n4_3f1c13nc14_V1"
        hw_hash = hashlib.sha256(raw.encode('utf-8') + salt).hexdigest()
        return hw_hash

# src/storage/database_manager.py
# Modificacion B2B para usar pysqlcipher3 y encriptar en reposo
# IMPORTANTE: pysqlcipher3 debe estar compilado para Windows
#
# ⚠️ ESTADO REAL (ver SPEC/0_REVIEW_FINDINGS.md P0-2): el codigo actual en
#    src/storage/database_manager.py todavia usa sqlite3 PLANO (sin cifrado).
#    Este snippet es el OBJETIVO; aun no esta implementado. Hasta entonces,
#    la BD biometrica NO esta cifrada en reposo.
import sqlite3 # Reemplazar por: from pysqlcipher3 import dbapi2 as sqlite3 en produccion
import re

class DatabaseManager:
    def __init__(self, db_path: str, encryption_key_hex: str):
        self.db_path = db_path
        # La clave SQLCipher se entrega como hex de 64 chars (256 bits),
        # derivada del Machine_Hash. Se valida ANTES de interpolar.
        if not re.fullmatch(r'[0-9a-fA-F]{64}', encryption_key_hex):
            raise ValueError("Encryption key must be a 64-char hex string.")
        self.encryption_key_hex = encryption_key_hex.lower()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        # ANTI-SQLi (directiva §4.0 #3): PRAGMA no admite placeholders '?', por lo que
        # NO se usa f-string con input crudo. Se usa la forma de blob hexadecimal
        # (PRAGMA key = "x'<hex>'") con la clave ya validada como [0-9a-f]{64},
        # lo que la hace segura frente a inyeccion.
        conn.execute('PRAGMA key = "x\'%s\'";' % self.encryption_key_hex)
        conn.row_factory = sqlite3.Row
        return conn

    def test_connection(self) -> bool:
        try:
            with self._get_connection() as conn:
                # Sentencia parametrizada (Anti-SQL Injection)
                conn.execute("SELECT count(*) FROM sqlite_master;")
                return True
        except sqlite3.DatabaseError:
            # Clave incorrecta o base de datos corrupta
            return False
```

## 4.4 Ofuscación PyArmor y Configuración de PyInstaller (`gui_app.spec`)

Para evitar la ingeniería inversa de Python (`uncompyle6`), ofuscamos `src/` antes del empaquetado.

**Paso 1: Modificar `compilar_exe.bat`**
```bat
@echo off
echo [1] Limpiando builds anteriores...
rmdir /s /q build dist ofuscado
echo [2] Ofuscando codigo fuente con PyArmor (Modo Restrictivo JIT)...
pyarmor gen -O ofuscado --enable-jit --restrict 1 src/
echo [3] Empaquetando ejecutable ofuscado...
pyinstaller gui_app.spec --clean -y
echo [4] Compilacion B2B Exitosa.
pause
```

**Paso 2: Modificar `gui_app.spec`**
El `.spec` debe apuntar al directorio `ofuscado/src/` y agregar las dependencias de PyArmor.

```python
# gui_app.spec
# -*- mode: python ; coding: utf-8 -*-

import os
# Configuracion estricta para evitar bloqueos OpenMP
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

block_cipher = None

# IMPORTANTE: Apuntar al main file ofuscado
a = Analysis(
    ['ofuscado/src/gui_app.py'], # <--- Cambio Crucial
    pathex=['ofuscado/src', '.'],
    binaries=[],
    datas=[
        ('yolov8n.pt', '.'),
        ('VERSION', '.'),
        # Las extensiones nativas de PyArmor (.pyd) se incluyen auto
    ],
    hiddenimports=[
        'torch', 'torchvision', 'ultralytics', 'supervision', 'shapely',
        'face_recognition_models', 'wmi', 'sqlite3', # pysqlcipher3
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='OficinaEficiencia_B2B', # Renombrado B2B
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True, # Compresion (Opcional, puede causar falsos positivos en AV)
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False, # True para debugear, False para produccion B2B
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico' # Opcional
)

## 4.5 Módulo de Reportes Asincrónicos (I/O Sin Bloqueos B2B)

Este código evita los cuellos de botella del disco duro. Un reporte de "Pandas" puede tomar 5 segundos en un SQLite gigante, durante los cuales el sistema de cámaras debe seguir corriendo fluido y el usuario no debe percibir congelamientos en la UI (CustomTkinter).

```python
# src/analysis/report_generator.py
import threading
import pandas as pd
from typing import Callable
import time
import os

class DatabaseWorker:
    def __init__(self, db_manager):
        self.db = db_manager

    def generate_excel_async(self, query: str, output_path: str, on_success: Callable, on_error: Callable):
        """Ejecuta un volcado a Excel asincronamente usando hilos."""
        
        def _worker():
            try:
                # 1. Simular carga inicial conectando al db
                conn = self.db._get_connection()
                
                # 2. Cargar en Pandas (puede demorar)
                df = pd.read_sql_query(query, conn)
                
                # 3. Validar si el archivo esta en uso por Excel.exe (PermissionError local)
                if os.path.exists(output_path):
                    try:
                        os.rename(output_path, output_path)
                    except OSError:
                        raise PermissionError(f"Cierre el archivo {output_path} en Microsoft Excel antes de sobrescribir.")

                # 4. Exportar a XLSX (Operacion bloqueante de I/O)
                df.to_excel(output_path, index=False, engine='openpyxl')
                
                # 5. Invocar Callback Exitoso en el Hilo Principal
                if on_success:
                    on_success(output_path, len(df))
            
            except Exception as e:
                # 6. Invocar Callback de Error
                if on_error:
                    on_error(str(e))
            finally:
                if 'conn' in locals():
                    conn.close()

        # Iniciar y desatar el hilo
        t = threading.Thread(target=_worker, daemon=True, name="DB_Excel_Export")
        t.start()
```

### Integración en CustomTkinter (AppMain UI)

El callback devuelto por `DatabaseWorker` cruzará desde el Hilo Secundario al Hilo Principal (UI) a través del manejador seguro `.after()`.

```python
    def handle_report_click(self):
        """Metodo llamado por el Boton de Exportar en la Interfaz."""
        self.btn_export.configure(state="disabled", text="Exportando...") # Feedback visual B2B
        
        # Consultamos el ultimo mes de eventos
        query = "SELECT * FROM eventos_asistencia WHERE timestamp >= datetime('now', '-30 days')"
        
        # Rutas seguras via config/path_utils (Aislamiento de Tenant).
        # Ruta canonica: Tenants/<ID>/reportes/ (ver SPEC/0_REVIEW_FINDINGS.md P1-1)
        out_path = ConfigManager.get_tenant_path('reportes', f'reporte_{time.strftime("%Y%m")}.xlsx')

        # Lanzar tarea en background (Zero-Blocking)
        self.db_worker.generate_excel_async(
            query=query,
            output_path=out_path,
            on_success=self._on_export_success,
            on_error=self._on_export_error
        )

    def _on_export_success(self, final_path: str, records_count: int):
        # Programar la actualizacion de interfaz en el Main Loop (Thread Safe)
        self.after(0, lambda: self._show_toast_and_reset(f"Exportacion Exitosa: {records_count} registros.", "success"))
        
    def _on_export_error(self, err_msg: str):
        self.after(0, lambda: self._show_toast_and_reset(f"Error B2B: {err_msg}", "danger"))

    def _show_toast_and_reset(self, msg: str, mode: str):
        """Muestra un toast/snackbar notification y reactiva el boton"""
        self.btn_export.configure(state="normal", text="Exportar a Excel")
        # Logica del Toast de CustomTkinter (ej. CTkMessagebox)
        print(f"[{mode.upper()}] {msg}")
```
```

---

## 4.6 Registro de Implementación — Ejecución Secuencial de Sprints (2026-06-23)

Esta sección documenta la ejecución secuencial completa de las Tareas 1–6 sobre
la base de código existente. La mayor parte de los Sprints 1–5 ya estaban
implementados y cubiertos por `tests/`; este registro detalla el trabajo de
*cierre de brechas* realizado para satisfacer las DoD pendientes (⏳) que
quedaban registradas en `SPEC/0_REVIEW_FINDINGS.md`.

### Estado de verificación (entorno Linux/CI headless)
- **115 pruebas de lógica** pasan (Sprints 1, 3, 4, 5 + 16 nuevas).
- **5 pruebas de Grid View (Sprint 2)** pasan bajo Tkinter real (`Xvfb` + `python3.12`):
  `tests/test_dashboard_grid.py` (grid NxN dinámico, single-view toggle, consumo
  asíncrono de colas, transición 0→N cámaras).
- Fallos **solo ambientales** (no defectos de código): `test_drm_fallback.py`
  requiere el módulo `wmi` (exclusivo de Windows) y `test_ui_navigation` /
  `test_sprint5_audit::test_cprofile` instancian `AppMain`, que carga
  YOLO/torch (no instalable de forma ligera en este contenedor).

### Sprint 1 — Concurrencia (Zero Blocking)  ✅ ya implementado
`src/tracking/camera_worker.py` (Productor + Drop Frame Protocol con
`put_nowait`/`queue.Full`, throttle de FPS), colas `queue.Queue(maxsize=10)`,
y `DatabaseWorker.generate_excel_async` (hilo daemon, callbacks vía `.after`).
Cobertura: `test_camera_worker_leaks.py`, `test_async_excel.py`.

### Sprint 2 — Fluid UI (CustomTkinter)  ✅ ya implementado
`src/main_ui.py` (AppMain + `ViewManager`), `src/gui/dashboard.py`
(grid multiplexor + `<Double-1>` single view), `src/gui/views.py`.
Cobertura: `test_dashboard_grid.py`, `test_ui_navigation.py`.

### Sprint 3 — Multi-Tenant  ✅ ya implementado
`config/path_utils.py::ConfigManager` (ruta canónica `Tenants/<ID>/<subdir>`,
validación anti path-traversal) y `Bootloader` en `main_ui.py`.
Cobertura: `test_tenant_routing.py`, `test_security_fixes.py`.

### Sprint 4 — DRM / SecOps
- **TASK-4.1 / 4.2 (DRM RSA-2048 + WMI fingerprint):** ✅ ya implementado en
  `src/security/drm.py`. Cobertura: `test_drm_rsa_b2b.py`.
- **TASK-4.3 (BD cifrada):** 🆕 **implementado este ciclo** vía el *fallback
  autorizado por TASK-0.1* (AES-256-GCM a nivel de aplicación, no SQLCipher
  nativo, que no compila de forma fiable en Windows sin Build Tools/OpenSSL).
  - `src/security/db_crypto.py::EncryptedDBVault`: cifra el `local_tracking.db`
    completo a `local_tracking.enc_db` en reposo y lo descifra al montar el
    Tenant. El blob `.enc_db` es ilegible para DB Browser (cumple Auditoría
    5.3.2). Clave AES derivada del `Machine_Hash` (WMI) → indescifrable si se
    copia a otra PC.
  - `DatabaseManager._get_connection()`: conexión central con
    `PRAGMA journal_mode=WAL` + `synchronous=NORMAL` + `busy_timeout` (mitiga
    Riesgo 4 / resuelve P3-2). Usado por el `DatabaseWorker` asíncrono.
  - Wiring en `main_ui.py`: `unlock()` al montar Tenant, `lock()` al cerrar.
  - Cobertura: `test_db_encryption.py` (5 pruebas).
  - Resuelve `0_REVIEW_FINDINGS` **P0-2** y **P3-2**.
- **TASK-4.4 (PyArmor en el pipeline):** 🆕 **implementado este ciclo.**
  - `obfuscate.py`: script pre-build que limpia `build/` + `dist/obfuscated/`
    y ofusca `src/` + `config/` con `pyarmor gen -O dist/obfuscated
    --enable-jit --restrict 1`.
  - `compilar_exe.bat`: reescrito para ejecutar `obfuscate.py` **antes** de
    `pyinstaller gui_app.spec` (antes saltaba la ofuscación por completo).
  - `gui_app.spec` ya apuntaba a `dist/obfuscated/src/main_ui.py` y declara los
    `hiddenimports` de `wmi`/`win32com`/`pywintypes`/`Crypto` (TASK-4.4.5).
  - Cobertura: `test_obfuscate_pipeline.py`.

### Sprint 5 — Refinamiento B2B / Auditoría
- **TASK-5.1 (excepthook global + crash log AES-256):** 🆕 **implementado.**
  `src/security/crash_logger.py`: `install_global_excepthook()` registra el
  traceback **cifrado** (AES-256-GCM, clave del hardware) en
  `Config/crash_logs.dat` y muestra solo "Contacte a Soporte B2B".
  `decrypt_crash_logs()` es la herramienta de soporte. Wiring en `main_ui`
  `__main__`. Cobertura: `test_crash_logger.py`.
- **TASK-5.2 (integridad del modelo AI):** 🆕 **implementado.**
  `src/models/model_verifier.py`: SHA-256 pre-aprobado embebido de `yolov8n.pt`;
  `CameraWorker` verifica el modelo en `__init__` y `run()` aborta el tracking si
  fue manipulado. Cobertura: `test_model_verifier.py`.
- **TASK-5.3 (sanitización de inputs):** ✅ ya implementado (regex anti
  path-traversal en `ConfigManager.set_active_tenant` y formularios).
- **TASK-5.4 (stress test de exportación I/O):** ✅ ya implementado
  (`test_sprint5_audit.py` — 50k registros, UI no bloqueada).

### Sprint 0 — Freeze de dependencias
- **TASK-0.1:** ✅ `requirements.txt` unificado (P0-1). Nota: este ciclo usa el
  *fallback* de TASK-0.1 para la BD cifrada (AES-256 vía `pycryptodome`/
  `cryptography`), por lo que `pysqlcipher3` no es un bloqueante.

### Brechas que permanecen como backlog consciente (no implementadas)
- **P2-2 (HMAC biométrico desde `platform.node()`):** el *contrato de pruebas*
  (`test_security_fixes.py::_get_integrity_key`) fija el HMAC al hostname.
  Migrarlo al `machine_id` del DRM rompería esa prueba; se deja como decisión de
  diseño explícita (requiere actualizar también la prueba).
- **P2-1 / P2-3 / P3-1 / Gaps legales:** decisiones de negocio o diseño
  documentadas en `0_REVIEW_FINDINGS`; fuera del alcance de código de este ciclo.
