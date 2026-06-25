# 8. PRODUCTION CODE REVIEW: Auditoría de Código para Release Comercial (Venta B2B)

Este documento es una **auditoría del código fuente real** (`src/`, `config/`) orientada a
determinar si el producto está listo para **venta / producción**. A diferencia de
`0_REVIEW_FINDINGS.md` (que audita las *especificaciones* contra el código), este
documento audita el **comportamiento en ejecución** del código tal como está hoy.

Cada hallazgo incluye: ubicación exacta, el código actual, el escenario de fallo
concreto, la **corrección paso a paso** (con snippets listos para aplicar) y el
**criterio de verificación** para marcarlo como resuelto. El objetivo es que un
desarrollador (o un Agente de IA) pueda aplicar cada fix **sin ambigüedad**.

> **Fecha de revisión:** 2026-06-25
> **Alcance:** `src/main.py`, `src/main_ui.py`, `src/gui/`, `src/storage/`,
> `src/tracking/`, `src/recognition/`, `config/`.
> **Metodología:** revisión línea por línea + trazado de llamadas (callers/callees)
> + verificación cruzada con `config.py`.

---

## Veredicto general

**🟢 BLOQUEANTES RESUELTOS (2026-06-25).** Auditoría original: **🔴 NO LISTO PARA VENTA**.

> **Actualización (2026-06-25):** los **10 hallazgos (CR-01…CR-10)** fueron corregidos
> en este ciclo. Los 3 bloqueantes funcionales (incl. la GUI que nunca grababa datos),
> los 3 fallos de seguridad (inyección SQL, fuga de `torch.load`, bypass del DRM) y los
> ítems de concurrencia/calidad están aplicados y verificados con pruebas
> (`tests/test_tracking_pipeline.py`, `tests/test_report_sql_injection.py`, suite de
> datos + `test_security_fixes.py`). Ver el estado por CR en cada sección y el resumen
> al final.

La auditoría original detectó **3 bloqueantes funcionales** (uno hacía que la interfaz
gráfica **nunca grabe datos**, dejando todos los reportes vacíos), más **3 fallos de
seguridad** (incluyendo una inyección SQL y un posible bypass del DRM) y problemas de
concurrencia y calidad — todos ahora corregidos.

| Severidad | Cantidad | IDs |
|---|---|---|
| 🔴 Bloqueante (no funciona / crash) | 3 | CR-01, CR-04, CR-07 |
| 🟠 Seguridad | 3 | CR-02, CR-05, CR-06 |
| 🟡 Concurrencia / Datos | 2 | CR-03, CR-09 |
| ⚪ Calidad / Mantenibilidad | 2 | CR-08, CR-10 |

**Mínimo viable para vender:** corregir CR-01, CR-04, CR-07 (bloqueantes) y CR-02
(inyección SQL). El resto es altamente recomendable antes del "Golden Master".

---

## 🔴 CR-01 — `config.LOCAL_DB_PATH` no existe → crash inmediato del modo headless

- **Archivo:** `src/main.py:86`
- **Severidad:** 🔴 Bloqueante
- **Estado:** ✅ Resuelto (2026-06-25) — `config.get_db_path()` + `set_active_tenant(OE_TENANT_ID|'Default')` al inicio de `start_video_stream()`

### Problema
```python
# src/main.py:86
db_manager = DatabaseManager(db_path=config.LOCAL_DB_PATH)
```
`config/config.py` **no define** ningún atributo `LOCAL_DB_PATH`. La ruta de la BD se
expone como **función** `get_db_path()` (config.py:23). Acceder a `config.LOCAL_DB_PATH`
lanza `AttributeError: module 'config.config' has no attribute 'LOCAL_DB_PATH'`.

### Escenario de fallo
Ejecutar `python src/main.py` (el pipeline headless de detección/tracking) aborta con
`AttributeError` antes de procesar un solo frame. El modo consola es **inutilizable**.

### Corrección
1. En `src/main.py`, reemplazar el acceso al atributo inexistente por la llamada a la
   función getter, que además es tenant-aware:
   ```python
   # ANTES
   db_manager = DatabaseManager(db_path=config.LOCAL_DB_PATH)

   # DESPUÉS
   db_manager = DatabaseManager(db_path=config.get_db_path())
   ```
2. **Importante:** `get_db_path()` invoca `ConfigManager.get_active_tenant()`, que
   lanza `ValueError` si no se ha seleccionado un Tenant. El modo headless de
   `main.py` no pasa por el `Bootloader`, así que **debe seleccionar un Tenant antes**.
   Añadir al inicio de `start_video_stream()` (después de cargar `config`):
   ```python
   from config.path_utils import ConfigManager
   import os
   # Modo headless: usar tenant por variable de entorno o "Default"
   ConfigManager.set_active_tenant(os.environ.get('OE_TENANT_ID', 'Default'))
   ```

### Verificación
- `python src/main.py` arranca sin `AttributeError` (con una cámara o video de prueba).
- La BD se crea en `%APPDATA%/OficinaEficiencia/Tenants/<TenantID>/db/local_tracking.db`.

---

## 🔴 CR-04 — La GUI (`CameraWorker`) nunca persiste datos de tracking → reportes siempre vacíos

- **Archivo:** `src/tracking/camera_worker.py` (clase completa) vs. `src/main.py:106-211`
- **Severidad:** 🔴 Bloqueante (el más grave funcionalmente)
- **Estado:** ✅ Resuelto (2026-06-25) — lógica extraída a `src/tracking/tracking_pipeline.py::TrackingPipeline`, invocada por `main.py` y `CameraWorker`. Cobertura: `tests/test_tracking_pipeline.py`

### Problema
Existen **dos pipelines paralelos e inconsistentes**:

| Pipeline | Archivo | ¿Detecta zonas? | ¿Tracking IDs? | ¿Escribe a BD? | ¿State/asistencia? |
|---|---|---|---|---|---|
| Headless | `src/main.py` | ✅ `ZoneChecker` | ✅ `PersonTracker` | ✅ `DatabaseManager` | ✅ `StateManager` |
| **GUI (producción)** | `src/tracking/camera_worker.py` | ❌ | ❌ | ❌ | ❌ |

El `CameraWorker` (lo que realmente corre cuando el cliente usa `main_ui.py`) **solo**:
1. Lee frames (`cap.read()`).
2. Corre YOLO para *dibujar* cajas (`results[0].plot()`).
3. Hace reconocimiento facial para *mostrar* el nombre en pantalla.
4. Encola el frame anotado para el display.

**Nunca** llama a `ZoneChecker`, `PersonTracker`, `StateManager` ni a ningún método de
`DatabaseManager`. No hay `insert_record`, `insert_snapshot`, `update_attendance` ni
`insert_state`.

### Escenario de fallo
El cliente instala el producto, registra empleados, deja las cámaras corriendo toda la
semana, y al ir a **"Reportes Históricos"** y exportar Excel, el archivo sale **vacío**
(0 filas) porque la tabla `tracking` nunca recibió un solo `INSERT`. La asistencia y la
eficiencia —la **razón de ser del producto**— no se miden. Es un fallo silencioso: no
hay error, simplemente no hay datos.

### Corrección
El `CameraWorker.run()` debe replicar la lógica de negocio de `main.py`. Pasos:

1. **Inyectar las dependencias** en `__init__` (no hardcodear; el worker es por-cámara
   pero `DatabaseManager`/`ZoneChecker` pueden compartirse o crearse aquí):
   ```python
   from config.config import get_db_path, get_zonas_file, get_snapshots_dir
   from src.storage.database_manager import DatabaseManager
   from src.zones.zone_checker import ZoneChecker
   from src.tracking.person_tracker import PersonTracker
   from src.analysis.state_manager import StateManager

   self.db = DatabaseManager(db_path=get_db_path())
   self.zone_checker = ZoneChecker(zones_path=get_zonas_file())
   self.tracker = PersonTracker()
   self.state_manager = StateManager(self.db)
   self.zone_state = {}            # {track_id: {zone_name: bool}}
   self.track_id_to_name = {}      # {track_id: nombre}
   ```
2. **Dentro del bucle `run()`**, después de obtener `results = self.model(frame, ...)`,
   portar el bloque de `main.py:113-211`:
   - Separar `person_detections` (class_id 0) y `phone_detections` (class_id 67) desde
     las cajas de YOLO.
   - `tracked = self.tracker.update(person_detections)`.
   - Por cada `(xyxy, track_id)`: calcular centro, reconocer cara solo si el nombre es
     `Unknown` (cachear en `self.track_id_to_name`), `self.zone_checker.check(cx, cy)`.
   - Detectar evento de **entrada a zona** (`inside and not was_inside`) → guardar
     snapshot con `cv2.imwrite` + `self.db.insert_snapshot(...)`.
   - `self.db.insert_record(track_id, cx, cy, zone, inside_zone, employee_name=...)`.
   - Acumular `track_data_for_state_manager` y llamar
     `self.state_manager.process_frame(time.time(), track_data, phones_data)`.
3. **Cuidado con la frecuencia de escritura:** `main.py` inserta en *cada* frame. A 15
   fps por cámara × N cámaras esto satura SQLite. Aplicar **throttle**: insertar a la
   BD solo cada K frames (ej. `if self.frame_counter % 15 == 0`) o cuando cambie el
   estado/zona. Documentar la cadencia elegida.
4. **Prerrequisito:** este fix depende de **CR-03** (usar `_get_connection()` con WAL)
   para que las escrituras concurrentes de múltiples `CameraWorker` no rompan la BD.

> **Nota de arquitectura (altitud):** lo correcto es **extraer la lógica de
> negocio** de `main.py` a un módulo reutilizable (ej.
> `src/tracking/tracking_pipeline.py::process_detections(frame, results, deps)`) e
> invocarlo **tanto** desde `main.py` **como** desde `CameraWorker`. Hoy la lógica está
> duplicada/divergente; corregir solo el worker re-introduce la duplicación. Generalizar
> el mecanismo evita que ambos pipelines vuelvan a desincronizarse.

### Verificación
- Con la GUI corriendo y una persona frente a la cámara dentro de una zona configurada,
  la tabla `tracking` recibe filas (`SELECT COUNT(*) FROM tracking` > 0).
- "Reportes Históricos" → Exportar Excel produce filas reales.
- Se crean snapshots en `Tenants/<ID>/snapshots/` al entrar a una zona.
- `daily_attendance` registra `arrival_time`/`departure_time` del empleado reconocido.

---

## 🔴 CR-07 — `config.ZONAS_FILE` / `config.SNAPSHOTS_DIR` no existen → rutas no tenant-aware

- **Archivo:** `src/main.py:75` y `src/main.py:101`
- **Severidad:** 🔴 Bloqueante (rompe el aislamiento Multi-Tenant — ver P1-1)
- **Estado:** ✅ Resuelto (2026-06-25) — `config.get_zonas_file()` / `config.get_snapshots_dir()` tenant-aware

### Problema
```python
# src/main.py:75
zonas_file = getattr(config, 'ZONAS_FILE', os.path.join(os.environ.get('APPDATA', ...), 'OficinaEficiencia', 'data', 'zonas', 'zonas.json'))
# src/main.py:101
snapshots_dir = getattr(config, 'SNAPSHOTS_DIR', os.path.join(os.environ.get('APPDATA', ...), 'OficinaEficiencia', 'data', 'snapshots'))
```
`config.py` expone `get_zonas_file()` y `get_snapshots_dir()` como **funciones**, no como
atributos `ZONAS_FILE`/`SNAPSHOTS_DIR`. Por tanto `getattr(config, 'ZONAS_FILE', <default>)`
**siempre** devuelve el `<default>` hardcodeado, que:
- Usa el segmento `data/` ya **prohibido** por la ruta canónica (P1-1 de
  `0_REVIEW_FINDINGS.md`).
- **No** es tenant-aware: todas las sucursales comparten la misma carpeta de zonas y
  snapshots.

### Escenario de fallo
En despliegue Multi-Tenant, "Sucursal Norte" y "Sucursal Sur" leen/escriben el **mismo**
`zonas.json` y el **mismo** directorio de snapshots, violando el aislamiento hermético
prometido (Prueba 5.1.2). Las zonas de una sucursal contaminan a otra.

### Corrección
Reemplazar los `getattr` por las funciones getter tenant-aware:
```python
# src/main.py:75  — ANTES
zonas_file = getattr(config, 'ZONAS_FILE', os.path.join(...))
# DESPUÉS
zonas_file = config.get_zonas_file()

# src/main.py:101 — ANTES
snapshots_dir = getattr(config, 'SNAPSHOTS_DIR', os.path.join(...))
# DESPUÉS
snapshots_dir = config.get_snapshots_dir()
```
(Requiere que el Tenant esté seleccionado — ver CR-01 paso 2.)

### Verificación
- Con `Tenant_A` activo, `zonas_file` apunta a
  `.../Tenants/Tenant_A/zonas/zonas_config.json` (no a `.../data/zonas/zonas.json`).
- Cambiar a `Tenant_B` produce una ruta distinta. Test sugerido: extender
  `tests/test_tenant_routing.py`.

---

## 🟠 CR-02 — Inyección SQL en la generación de reportes (fechas interpoladas)

- **Archivo:** `src/gui/views.py:301`
- **Severidad:** 🟠 Seguridad (OWASP A03) — contradice la Auditoría 5.6 #2 y la directiva anti-vibe-hacking
- **Estado:** ✅ Resuelto (2026-06-25) — query con placeholders `?` + `params`, `generate_excel_async(params=...)`, y validación `YYYY-MM-DD`. Cobertura: `tests/test_report_sql_injection.py`

### Problema
```python
# src/gui/views.py:300-301
output = os.path.join(export_dir, f"Reporte_{start}_a_{end}.xlsx")
query = f"SELECT employee_name, date(timestamp) as fecha, zone, inside_zone FROM tracking WHERE date(timestamp) BETWEEN '{start}' AND '{end}'"
```
`start` y `end` provienen **directamente** de `CTkEntry` (`start_entry.get()` /
`end_entry.get()`, líneas 297-298) **sin validar ni parametrizar**, y se interpolan por
f-string dentro del SQL. La spec (`5_REVIEW.md` §5.6 pregunta 2) exige explícitamente
que **ninguna cadena de la GUI** se interpole en SQL.

### Escenario de fallo
Un usuario (o un atacante con acceso a la terminal de la sucursal) escribe en el campo
"Fecha Fin":
```
2026-12-31' OR '1'='1
```
La cláusula `WHERE` se vuelve siempre verdadera → se exfiltra **toda** la tabla
`tracking`, no solo el rango pedido. Con `;`/subqueries el daño escala (lectura de otras
tablas vía `UNION`). Además, fechas con caracteres de ruta podrían afectar el
`output_path`.

### Corrección
1. **Parametrizar la query.** `DatabaseWorker.generate_excel_async` usa
   `pd.read_sql_query(query, conn)` (report_generator.py:61). Pandas acepta `params`.
   Modificar la firma y el cuerpo:
   ```python
   # src/analysis/report_generator.py
   def generate_excel_async(self, query: str, output_path: str,
                            on_success: Callable, on_error: Callable,
                            params: tuple = ()):
       def _worker():
           try:
               conn = self.db._get_connection()
               df = pd.read_sql_query(query, conn, params=params)   # <-- params
               ...
   ```
2. **Usar placeholders en `views.py`:**
   ```python
   # src/gui/views.py — DESPUÉS
   query = ("SELECT employee_name, date(timestamp) as fecha, zone, inside_zone "
            "FROM tracking WHERE date(timestamp) BETWEEN ? AND ?")
   worker.generate_excel_async(query, output, on_ok, on_err, params=(start, end))
   ```
3. **Validar el formato de fecha** antes de usarla (defensa en profundidad y para el
   nombre de archivo). Rechazar cualquier cosa que no sea `YYYY-MM-DD`:
   ```python
   import re
   DATE_RE = re.compile(r'^\d{4}-\d{2}-\d{2}$')
   if not DATE_RE.match(start) or not DATE_RE.match(end):
       report_status.configure(text="⚠️ Formato de fecha inválido (use YYYY-MM-DD).",
                               text_color="#E74C3C")
       return
   ```

### Verificación
- Ingresar `2026-12-31' OR '1'='1` en el campo de fecha produce un error de validación,
  **no** un volcado completo de la tabla.
- Test sugerido en `tests/`: llamar a `generate_excel_async` con `params` y verificar que
  solo se exportan filas del rango.

---

## 🟠 CR-05 — El monkey-patch de `torch.load` no se restaura si YOLO falla (fuga de seguridad)

- **Archivo:** `src/main_ui.py:80-104`
- **Severidad:** 🟠 Seguridad (deserialización insegura persistente)
- **Estado:** ✅ Resuelto (2026-06-25) — `torch.load` se restaura en `finally` (todos los caminos)

### Problema
```python
# src/main_ui.py:80-104 (resumido)
try:
    import torch
    _original_load = torch.load
    def _patched_load(*args, **kwargs):
        kwargs['weights_only'] = False        # <-- desactiva la protección
        return _original_load(*args, **kwargs)
    torch.load = _patched_load
    ...
    model = YOLO(MODEL_PATH)
    torch.load = _original_load               # <-- SOLO se restaura si NO hubo excepción
except Exception as e:
    print(...); model = None                  # <-- aquí torch.load quedó PARCHEADO
```
Si `YOLO(MODEL_PATH)` (o cualquier línea entre el parche y la restauración) lanza una
excepción, el flujo salta al `except` **sin** ejecutar `torch.load = _original_load`.
`torch.load` queda permanentemente reemplazado por la versión que fuerza
`weights_only=False` durante **toda la sesión**.

### Escenario de fallo
El modelo `yolov8n.pt` está ausente/corrupto → `YOLO()` lanza excepción → la app sigue
viva (con `model = None`) pero `torch.load` quedó inseguro. Cualquier carga posterior de
un `.pt`/checkpoint (otro subsistema, un plugin, una recarga) deserializa con
`weights_only=False`, reintroduciendo el vector de ejecución de código arbitrario que el
parámetro busca mitigar.

### Corrección
Envolver la restauración en `finally` para garantizarla en todos los caminos:
```python
import torch
_original_load = torch.load
def _patched_load(*args, **kwargs):
    kwargs['weights_only'] = False
    return _original_load(*args, **kwargs)
torch.load = _patched_load
try:
    from ultralytics import YOLO
    from ultralytics.nn.tasks import DetectionModel
    if hasattr(torch.serialization, 'add_safe_globals'):
        try:
            torch.serialization.add_safe_globals([DetectionModel])
        except Exception:
            pass
    model = YOLO(MODEL_PATH)
except Exception as e:
    print(f"[VMS] No se pudo cargar YOLO: {e}")
    import tkinter.messagebox
    tkinter.messagebox.showerror("Error Crítico de IA", f"...{e}...")
    model = None
finally:
    torch.load = _original_load   # <-- SIEMPRE se restaura
```
> Idealmente usar `add_safe_globals` como mecanismo principal y evitar el parche global
> por completo; pero como mínimo, el `finally` cierra la fuga.

### Verificación
- Renombrar temporalmente `yolov8n.pt` para forzar el fallo; tras el arranque,
  `torch.load is _original_load` debe ser `True`.

---

## 🟠 CR-06 — No se verifica `LicenseWindow.activated` tras el modal → posible bypass del DRM

- **Archivo:** `src/main_ui.py:402-408`
- **Severidad:** 🟠 Seguridad (evasión de licenciamiento)
- **Estado:** ✅ Resuelto (2026-06-25) — se verifica `lic_win.activated` + re-validación `drm.validate_license()` contra disco; si falla, `sys.exit(0)`

### Problema
```python
# src/main_ui.py:402-408
drm = DRMValidator()
if not drm.validate_license():
    lic_win = LicenseWindow(root, drm)
    root.wait_window(lic_win)
    # <-- NO se comprueba lic_win.activated; la ejecución continúa pase lo que pase
bootloader = Bootloader(root)
...
```
`LicenseWindow` expone `self.activated` (True solo si `activate_license` tuvo éxito), pero
tras `wait_window` **nadie lo verifica**. Si la ventana se cierra/destruye sin activación
exitosa (excepción interna de CTk, `self.after(1500, self.destroy)` disparándose en un
estado inesperado, o un cierre programático), el flujo continúa al `Bootloader` y a
`AppMain` **sin licencia válida**.

> Nota: `on_close()` hace `sys.exit(0)` si el usuario cierra con la X, lo cual cubre el
> caso manual. El riesgo es el cierre **no manual** (programático/excepción), donde
> `activated` queda `False` pero la app arranca igual.

### Escenario de fallo
Cualquier ruta que destruya el `Toplevel` sin pasar por `on_close` deja entrar a un
usuario sin licencia. También facilita un bypass dirigido (forzar la destrucción de la
ventana). Contradice el modelo de suscripción B2B.

### Corrección
Verificar explícitamente el estado tras el modal y abortar si no se activó:
```python
drm = DRMValidator()
if not drm.validate_license():
    lic_win = LicenseWindow(root, drm)
    root.wait_window(lic_win)
    # Re-validar contra disco (fuente de verdad), no solo el flag de la ventana:
    if not getattr(lic_win, "activated", False) and not drm.validate_license():
        import sys
        print("[VMS] Activación no completada. Cerrando.")
        sys.exit(0)
```
> Re-llamar a `drm.validate_license()` (que relee y verifica la licencia persistida) es
> más robusto que confiar en el flag `activated` en memoria.

### Verificación
- Forzar el cierre de `LicenseWindow` sin activar (sin escribir `license.key`) debe
  terminar el proceso, no abrir el `Bootloader`.

---

## 🟡 CR-03 — Todas las escrituras de `DatabaseManager` saltan WAL/`busy_timeout` (reabre P3-2)

- **Archivo:** `src/storage/database_manager.py` — métodos en líneas 107, 116, 125, 133, 142, 165, 174, 183, 192, 205, 350, 366, 388
- **Severidad:** 🟡 Concurrencia / pérdida de datos
- **Estado:** ✅ Resuelto (2026-06-25) — todos los métodos usan `self._get_connection()`; grep limpio + stress test sin `OperationalError`
- **⚠️ Corrige a `0_REVIEW_FINDINGS.md` P3-2:** ese ítem está marcado **✅ Resuelto**,
  pero la resolución es **incompleta**. WAL y `busy_timeout` se aplican en
  `_create_table()` y en `_get_connection()`, pero **ningún método de escritura usa
  `_get_connection()`**. Debe **reabrirse**.

### Problema
`_get_connection()` (líneas 21-37) aplica `journal_mode=WAL`, `synchronous=NORMAL` y
`busy_timeout=30000`. Sin embargo, **todos** los métodos de lectura/escritura abren su
propia conexión con `sqlite3.connect(self.db_path)` **directo**, sin esos PRAGMA:
```python
def insert_record(self, ...):
    conn = sqlite3.connect(self.db_path)   # <-- sin WAL, sin busy_timeout
    ...
```
(igual en `insert_snapshot`, `insert_state`, `update_attendance`, `get_all_records`,
`employee_exists`, `save_employee_profile`, `get_all_employee_names`,
`get_unique_employees`, `get_employee_snapshots`, `anonymize_employee`,
`delete_employee_profile`). El **único** consumidor de `_get_connection()` es el
`DatabaseWorker` (export Excel). La conexión por defecto de SQLite usa
`busy_timeout=0`: ante un lock, falla **de inmediato**.

### Escenario de fallo
Con CR-04 corregido, varios `CameraWorker` insertan a ~15 fps mientras el usuario exporta
un Excel (lectura larga). El export mantiene un lock; las inserciones, sin
`busy_timeout`, lanzan `sqlite3.OperationalError: database is locked` y **se pierden
registros** de asistencia/tracking. Es un corruptor silencioso de los datos de negocio.

### Corrección
1. Hacer que **todos** los métodos usen `self._get_connection()` en lugar de
   `sqlite3.connect(self.db_path)`:
   ```python
   # ANTES
   conn = sqlite3.connect(self.db_path)
   # DESPUÉS
   conn = self._get_connection()
   ```
   Aplicar el reemplazo en los ~13 métodos listados arriba.
2. Idealmente envolver cada operación en `with conn:` o `try/finally` para garantizar
   `close()` ante excepciones (varios métodos hoy no cierran si la query falla).
3. Tras aplicar, **actualizar `0_REVIEW_FINDINGS.md`**: cambiar P3-2 de
   "✅ Resuelto" a "✅ Resuelto (completo)" solo cuando se verifique lo de abajo; mientras
   tanto marcarlo "⚠️ Parcial".

### Verificación
- `grep -n "sqlite3.connect(self.db_path)" src/storage/database_manager.py` no devuelve
  resultados (todas pasan por `_get_connection`).
- Test de estrés: 2 hilos insertando + 1 hilo leyendo durante 30 s sin
  `OperationalError`.

---

## 🟡 CR-09 — `time.sleep(0.5)` en el hilo de UI congela la ventana al cambiar de cámara

- **Archivo:** `src/main_ui.py:146-151` (`_stop_local_camera`)
- **Severidad:** 🟡 UX / robustez (roza la Prueba 5.1.3 "Navegación Asíncrona Fluida")
- **Estado:** ✅ Resuelto (2026-06-25) — sin `time.sleep` en UI; reinicio vía `self.after(500, ...)` + botón "Conectar" deshabilitado durante el cambio

### Problema
```python
# src/main_ui.py:146-151
def _stop_local_camera(self):
    for w in self.camera_workers:
        w.stop()
    self.camera_workers.clear()
    import time
    time.sleep(0.5)   # <-- BLOQUEA el hilo principal de Tkinter
```
`_stop_local_camera` se llama desde `_switch_camera` (línea 249), que corre en el **hilo
de la UI**. `time.sleep(0.5)` congela CustomTkinter medio segundo: la ventana deja de
responder y Windows puede marcarla "No responde" (justo lo que la Prueba 5.1.3 prohíbe).

### Escenario de fallo
El usuario cambia de cámara → la UI se congela 500 ms. Si impaciente vuelve a hacer clic
en "Conectar" antes de que responda, `_start_local_camera` se invoca de nuevo y, como el
worker viejo aún no terminó de soltar el dispositivo, se crean **workers duplicados**
compitiendo por el mismo índice de cámara (fuga de hilos + posible `VideoCapture` doble).

### Corrección
No dormir en el hilo de UI. Opciones (de menor a mayor esfuerzo):
- **Mínima:** unir los hilos con timeout fuera del hilo de UI, o reprogramar el arranque
  con `self.after` en vez de `sleep`:
  ```python
  def _stop_local_camera(self):
      for w in self.camera_workers:
          w.stop()
      self.camera_workers.clear()
      # No bloquear: el daemon thread terminará solo; reprogramar el reinicio.
  ```
  Y en `_switch_camera`, en lugar de llamar a `_start_local_camera` inmediatamente:
  ```python
  self._stop_local_camera()
  self.camera_queues.clear()
  self.after(500, lambda: self._start_local_camera(camera_index=camera_id))
  ```
- **Robusta:** deshabilitar el botón "Conectar" mientras hay un cambio en curso
  (`self._cam_connect_btn.configure(state="disabled")`) y reactivarlo al completar, para
  impedir el doble clic que crea workers duplicados.

### Verificación
- Cambiar de cámara no congela la ventana (sigue redibujando otras cámaras).
- Hacer doble clic rápido en "Conectar" no deja más de un `CameraWorker` activo
  (`len(self.camera_workers) == 1`).

---

## ⚪ CR-08 — Clave HMAC de biometría derivada de `platform.node()` (duplica P2-2)

- **Archivo:** `src/recognition/face_recognizer.py:20-23`
- **Severidad:** ⚪ Calidad / robustez de datos
- **Estado:** ✅ Resuelto (2026-06-25) — `_get_integrity_key` deriva del `machine_id`
  del DRM (bump a `v2`), consistente con `db_crypto.py`/`crash_logger.py`. Cierra P2-2.

### Problema
```python
def _get_integrity_key() -> bytes:
    node = platform.node().encode('utf-8', errors='replace')   # <-- hostname
    return hashlib.sha256(node + b"_oe_face_integrity_v1").digest()
```
El HMAC que protege `encodings.npz` se deriva del **hostname**, no del `machine_id` (WMI)
que usa el DRM. El hostname es trivialmente modificable.

### Escenario de fallo
El cliente renombra la PC, la une a un dominio AD (cambia el nombre), o migra la carpeta
`APPDATA` a otra máquina. El HMAC deja de validar → `load_known_faces` descarta el `.npz`
e intenta **re-codificar desde las imágenes fuente**. Si solo se distribuyó el `.npz`
(sin las imágenes), la base biométrica queda **inutilizable** hasta re-registrar a todos
los empleados.

### Corrección
1. Derivar la clave del mismo `machine_id` que el DRM (consistente con `db_crypto.py` y
   `crash_logger.py`, que ya hacen esto):
   ```python
   def _get_integrity_key() -> bytes:
       try:
           from src.security.drm import DRMValidator
           machine_id = DRMValidator().machine_id
       except Exception:
           import uuid
           machine_id = f"FALLBACK_{uuid.getnode()}"
       return hashlib.sha256(machine_id.encode("utf-8") + b"_oe_face_integrity_v2").digest()
   ```
   (Nótese el bump a `v2` para no colisionar con firmas viejas.)
2. **Ligar con P2-3 (recovery):** definir una ruta de re-key cuando cambie el hardware
   (re-firmar el `.npz` tras re-validar licencia), para no dejar la biometría
   irrecuperable. Ver P2-3 en `0_REVIEW_FINDINGS.md`.

### Verificación
- Cambiar el hostname (sin cambiar hardware) **no** invalida `encodings.npz`.
- La firma sigue validando entre reinicios en la misma máquina.

---

## ⚪ CR-10 — Constantes duplicadas en `config.py` (sobrescritura silenciosa)

- **Archivo:** `config/config.py:42-48`
- **Severidad:** ⚪ Calidad / mantenibilidad
- **Estado:** ✅ Resuelto (2026-06-25) — bloque duplicado eliminado; una sola definición de cada constante

### Problema
```python
# config/config.py:42-48
FRAME_SKIP = 1
CONFIDENCE_THRESHOLD = 0.4


# Otros parámetros generales
FRAME_SKIP = 1
CONFIDENCE_THRESHOLD = 0.4
```
`FRAME_SKIP` y `CONFIDENCE_THRESHOLD` se definen **dos veces** (idénticas). La segunda
definición (líneas 47-48) sobrescribe la primera.

### Escenario de fallo
Un desarrollador ajusta `CONFIDENCE_THRESHOLD = 0.6` en la **primera** definición
(líneas 42-43) para reducir falsos positivos de detección. La **segunda** definición lo
revierte a `0.4` silenciosamente. El cambio "no tiene efecto" sin error → tiempo perdido
depurando y detección mal calibrada en producción.

### Corrección
Eliminar el bloque duplicado (líneas 46-48), dejando una sola definición:
```python
# Otros parámetros generales
FRAME_SKIP = 1
CONFIDENCE_THRESHOLD = 0.4
```

### Verificación
- `grep -c "CONFIDENCE_THRESHOLD =" config/config.py` devuelve `1`.

---

## Resumen de estado

| ID | Archivo:línea | Severidad | Estado | Relación |
|---|---|---|---|---|
| CR-01 | `src/main.py:86` | 🔴 Bloqueante | ✅ | — |
| CR-04 | `src/tracking/camera_worker.py` | 🔴 Bloqueante | ✅ | depende de CR-03 |
| CR-07 | `src/main.py:75,101` | 🔴 Bloqueante | ✅ | refuerza P1-1 |
| CR-02 | `src/gui/views.py:301` | 🟠 Seguridad | ✅ | viola §5.6 #2 |
| CR-05 | `src/main_ui.py:80-104` | 🟠 Seguridad | ✅ | — |
| CR-06 | `src/main_ui.py:402-408` | 🟠 Seguridad | ✅ | — |
| CR-03 | `src/storage/database_manager.py` | 🟡 Concurrencia | ✅ | **cierra P3-2** |
| CR-09 | `src/main_ui.py:146-151` | 🟡 UX/robustez | ✅ | roza Prueba 5.1.3 |
| CR-08 | `src/recognition/face_recognizer.py:20` | ⚪ Calidad | ✅ | **= P2-2** |
| CR-10 | `config/config.py:42-48` | ⚪ Calidad | ✅ | — |

### Orden de implementación recomendado
1. **CR-03** (WAL en escrituras) — prerrequisito de concurrencia para el resto.
2. **CR-01** y **CR-07** (getters tenant-aware en `main.py`) — fixes de 1 línea c/u.
3. **CR-04** (persistencia en `CameraWorker`) — el grande; extraer pipeline compartido.
4. **CR-02** (parametrizar SQL de reportes) — seguridad, autocontenido.
5. **CR-05**, **CR-06** (fugas de seguridad en arranque) — autocontenidos.
6. **CR-09**, **CR-08**, **CR-10** (UX y calidad).

---

**Auditor (Production Code Review):** [ _________________________ ]
**Fecha:** 2026-06-25
**Build evaluado:** rama `claude/production-code-review-vws1fs` · VERSION 1.3.0
