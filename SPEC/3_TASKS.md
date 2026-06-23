# 3. TASKS: Backlog Técnico Ultra-Granular para el Sistema B2B Multi-Cámara

Este documento es el **Kanban Técnico Estricto**. Las IAs o desarrolladores asignados deben ejecutar y marcar estas tareas de forma atómica (una por vez) utilizando Control de Versiones (Git) para evitar regresiones.

**🚨 DIRECTIVA ESTRICTA PARA AGENTES (ANTI-VIBE HACKING PROTOCOL) 🚨**
> *Se exige cumplimiento secuencial estricto.* **NO SE PERMITE** fusionar sub-tareas (ej. implementar DRM y la Interfaz Gráfica en un mismo commit). El incumplimiento de la **Definition of Done (DoD)** de cada subtarea resultará en un "Commit Rejected". No asumas dependencias no listadas ni modifiques el comportamiento fundamental sin la aprobación de un plan previo.

---

## 3.1 Sprint 1: Concurrencia (Zero Blocking Core) - Hilos y Queues

### [x] TASK-1.1: Refactorización de la Adquisición de Video (`src/tracking/`)
*   **Sub-tarea 1.1.1:** Crear la clase `CameraWorker(threading.Thread)` en `src/tracking/camera_worker.py`. Debe instanciar un objeto `cv2.VideoCapture()`.
*   **Sub-tarea 1.1.2:** Inyectar una dependencia (modelo YOLOv8) en `CameraWorker` y ejecutar la inferencia dentro del método `run()`.
*   **Sub-tarea 1.1.3:** Limitar el framerate (FPS) artificialmente dentro del hilo (ej. 15 FPS) usando `time.sleep()` para reducir el uso de CPU en máquinas con pocos recursos (Core i3/i5 sin GPU dedicada).
*   **DoD:** El código pasa la prueba estática de no bloquear el Hilo Principal. Si se crea una UI de prueba vacía con un botón "Test", la UI sigue respondiendo mientras OpenCV lee frames en la consola.

### [x] TASK-1.2: Implementación de Colas (Queues) Anti-Memory Leaks
*   **Sub-tarea 1.2.1:** Configurar `queue.Queue(maxsize=10)` por cada cámara instanciada para almacenar los frames procesados (`numpy.ndarray`).
*   **Sub-tarea 1.2.2:** Programar el "Drop Frame Protocol": Dentro de `CameraWorker.run()`, usar `try: self.frame_queue.put_nowait(frame)` y un bloque `except queue.Full:` para saltarse frames si la UI (Consumidor) es demasiado lenta renderizando (evitando un desbordamiento de RAM).
*   **DoD:** Una prueba de estrés de 1 hora procesando un video `.mp4` en bucle no incrementa el uso de RAM por encima del punto base (~800MB - 1.2GB).

### [x] TASK-1.3: Asincronía en Generación de Reportes (Excel sin Lag)
*   **Sub-tarea 1.3.1:** Modificar la clase/función actual que genera reportes Excel (usualmente en `src/analysis/` o `src/gui_app.py`). Envolverla en una función puente que la ejecute en `threading.Thread(target=generar, daemon=True)`.
*   **Sub-tarea 1.3.2:** Integrar callbacks (funciones de retorno) en el Hilo Principal para que el Hilo de Reportes avise (usando `master.after(0, show_toast)`) que el Excel `.xlsx` se guardó correctamente.
*   **DoD:** Mientras 4 cámaras están mostrando video fluido en pantalla, presionar "Generar Reporte" no pausa, congela ni "laguea" el video ni un milisegundo.

---

## 3.2 Sprint 2: Modernización "Fluid UI" (CustomTkinter)

### [x] TASK-2.1: Bootstrap de `CustomTkinter` y Layout Principal
*   **Sub-tarea 2.1.1:** Reemplazar las importaciones base de `import tkinter as tk` por `import customtkinter as ctk` en el archivo principal (`src/gui_app.py` o su nuevo reemplazo `src/main_ui.py`).
*   **Sub-tarea 2.1.2:** Configurar el tema global (`ctk.set_appearance_mode("Dark")` y `ctk.set_default_color_theme("blue")`).
*   **Sub-tarea 2.1.3:** Estructurar el diseño en dos grandes marcos (`CTkFrame`): El "Sidebar" (izquierda, ancho fijo 250px) y el "Main Workspace" (centro-derecha, que ocupa todo el espacio restante con `fill="both", expand=True`).
*   **DoD:** La aplicación inicia con una ventana moderna, redimensionable, y un menú lateral que responde (cambia de color) al pasar el mouse por encima (Hover Effect).

### [x] TASK-2.2: Sistema de Navegación por Pestañas Invisibles
*   **Sub-tarea 2.2.1:** Programar un gestor de Vistas (`ViewManager`) que limpie (usando `frame.grid_forget()` o `.pack_forget()`) el contenido del "Main Workspace" y dibuje la nueva interfaz (ej. cambiar del "Dashboard de Cámaras" al "Formulario de Registro de Empleados").
*   **Sub-tarea 2.2.2:** Evitar instanciar nuevas ventanas top-level; todo ocurre dentro de la misma raíz para mantener la sensación "App nativa (VMS)".
*   **DoD:** El usuario puede alternar rápidamente entre 5 menús distintos en menos de 100ms sin que la ventana parpadee en blanco.

### [x] TASK-2.3: "Dashboard Multiplexor" (Grid de Cámaras Dinámico)
*   **Sub-tarea 2.3.1:** Crear la lógica de grilla matemática. Si hay 1 cámara: `row=0, col=0, rowspan=2, colspan=2`. Si hay 4 cámaras: Cámara 1 (`row=0, col=0`), Cámara 2 (`row=0, col=1`), etc.
*   **Sub-tarea 2.3.2:** Programar la rutina `.after(15, actualizar_frames)` en la interfaz. Esta rutina leerá la cola compartida (`queue`) de cada cámara activa, convertirá de BGR a RGB, creará una imagen `PIL`, y actualizará el atributo `image` de un `CTkLabel`.
*   **DoD:** La UI renderiza 4 cámaras falsas o reales al mismo tiempo a un mínimo de 15 FPS en una cuadrícula proporcional que se ajusta si el usuario redimensiona la ventana de Windows.

### [x] TASK-2.4: Interacción "Single View" (Doble Clic para Expandir)
*   **Sub-tarea 2.4.1:** Enlazar el evento de mouse `<Double-1>` a cada `CTkLabel` de video.
*   **Sub-tarea 2.4.2:** Al detectar el doble clic, el `ViewManager` oculta los demás labels usando `.grid_forget()`, reasigna el label clickeado para ocupar todo el marco (`row=0, column=0, sticky="nsew"`), y cambia el estado interno a `is_single_view = True`.
*   **Sub-tarea 2.4.3:** Al recibir otro doble clic en ese estado, se restauran las configuraciones `.grid()` originales de todas las cámaras.
*   **DoD:** La transición entre ver 4 cámaras pequeñas y 1 cámara en pantalla completa es instantánea y sin pérdida de frames.

---

## 3.3 Sprint 3: Aislamiento Multi-Tenant Local (Arquitectura B2B)

### [x] TASK-3.1: Pantalla de "Login / Selección de Sucursal" (Bootloader)
*   **Sub-tarea 3.1.1:** Modificar el punto de entrada para que, antes de inicializar el `CustomTkinter` principal, se lance una ventana modal que liste las carpetas dentro de `%APPDATA%/OficinaEficiencia/Tenants/`.
*   **Sub-tarea 3.1.2:** Si es la primera ejecución, mostrar un formulario para crear el primer "Tenant" (ej. "Empresa Principal").
*   **Sub-tarea 3.1.3:** AlMACENAR la elección en una variable global segura (ej. `ConfigManager.set_active_tenant(nombre_carpeta)`).
*   **DoD:** Es imposible saltarse esta ventana sin elegir un Tenant válido; la aplicación principal no carga sin un contexto definido.

### [x] TASK-3.2: Refactorización Dinámica de Rutas (`path_utils.py`)
*   **Sub-tarea 3.2.1:** Buscar todas las llamadas estáticas a `get_appdata_path('data', 'db')` o `'faces'` a lo largo de todo el código (`storage/`, `recognition/`, `zones/`).
*   **Sub-tarea 3.2.2:** Alterarlas para usar `get_appdata_path('Tenants', ConfigManager.get_active_tenant(), 'db')` o similar.
*   **DoD:** Creando 2 Tenants, el Tenant A no puede leer ni modificar la base de datos de rostros o de eventos de SQLite del Tenant B (Separación física en el disco).

---

## 3.4 Sprint 4: SecOps - Protección DRM Offline y PyArmor

### [x] TASK-4.1: Módulo Hardware Fingerprint (`src/security/drm.py`)
*   **Sub-tarea 4.1.1:** Instalar y usar la librería nativa de Windows `wmi`.
*   **Sub-tarea 4.1.2:** Escribir métodos robustos con manejo de excepciones para obtener `Win32_BaseBoard.SerialNumber`, `Win32_Processor.ProcessorId` y `Win32_DiskDrive.SerialNumber`.
*   **Sub-tarea 4.1.3:** Concatenar y aplicar hashing criptográfico SHA-256 (con salt) para generar la cadena de Hardware (Machine ID). Unificado a SHA-256 para coincidir con `src/security/drm.py` — ver `SPEC/0_REVIEW_FINDINGS.md` P1-2.
*   **DoD:** El Hash generado debe ser idéntico al ejecutarse múltiples veces en la misma PC y debe manejar limpiamente errores de permisos WMI retornando un ID basado en MAC (`uuid.getnode()`).

### [x] TASK-4.2: Ventana de Inserción de Licencia
*   **Sub-tarea 4.2.1:** Crear un modal de UI para "Activación de Software".
*   **Sub-tarea 4.2.2:** Importar la Llave Pública (RSA/PyCryptodome) pre-compartida en código. Desencriptar el string base64 que el usuario pegue en el cuadro de texto.
*   **Sub-tarea 4.2.3:** Validar que `Licencia_Descifrada.MachineID == Hash_Local` y que la fecha de caducidad (`Epoch`) no haya sido superada.
*   **DoD:** Licencias forjadas al azar o expiradas son rechazadas. Licencias válidas se guardan en el OS (`DPAPI`) o en archivo protegido y permiten la ejecución futura sin preguntar de nuevo (hasta la expiración).

### [x] TASK-4.3: Implementar Base de Datos Cifrada (SQLCipher)
*   **Sub-tarea 4.3.1:** Cambiar la dependencia de `sqlite3` a `pysqlcipher3`.
*   **Sub-tarea 4.3.2:** Añadir la cláusula `PRAGMA key = 'Clave_Derivada_Del_Hardware';` inmediatamente después de ejecutar `.connect()` a la base de datos `local_tracking.db`.
*   **DoD:** El archivo `.db` en `%APPDATA%` aparece como "Archivo Corrupto" o encriptado si se intenta abrir con herramientas como DB Browser for SQLite, pero la aplicación lee y escribe perfectamente.
*   **✅ Implementado vía el fallback autorizado por TASK-0.1 (cifrado a nivel de aplicación AES-256-GCM), no SQLCipher nativo:** ver `src/security/db_crypto.py::EncryptedDBVault`. En reposo solo existe `local_tracking.enc_db` (blob AES-256-GCM ilegible para DB Browser → cumple Auditoría 5.3.2); el VMS lo descifra al montar el Tenant (`main_ui` bootstrap) y lo re-cifra al cerrar. Clave derivada del `Machine_Hash` (WMI) → no portable a otra PC. Adicionalmente `DatabaseManager._get_connection()` aplica `PRAGMA journal_mode=WAL` (Riesgo 4). Cobertura: `tests/test_db_encryption.py`. Resuelve `SPEC/0_REVIEW_FINDINGS.md` P0-2 y P3-2.

### [x] TASK-4.4: Inyección de Ofuscación PyArmor en el Build Pipeline
*   **Sub-tarea 4.4.1:** Instalar `pyarmor` (versión 8.x recomendada para compatibilidad con Python 3.10+ y PyInstaller).
*   **Sub-tarea 4.4.2:** Escribir un script pre-build `obfuscate.py` que limpie el directorio `build/` y `ofuscado/`, y luego ejecute programáticamente el comando de ofuscación (`pyarmor gen -O ofuscado --restrict 1 src/`).
*   **Sub-tarea 4.4.3:** Modificar `compilar_exe.bat` para que llame a `python obfuscate.py` antes de llamar a `pyinstaller gui_app.spec`.
*   **Sub-tarea 4.4.4:** Editar `gui_app.spec`. Cambiar la ruta base de entrada en `Analysis` de `src/main_ui.py` a `ofuscado/src/main_ui.py`.
*   **Sub-tarea 4.4.5:** Añadir rutas adicionales (hiddenimports) en el `.spec` para empaquetar librerías dinámicas de Windows (`wmi`, `win32com`, `pywintypes`) que PyArmor suele enmascarar del analizador estático de PyInstaller.
*   **DoD:** El `.exe` ofuscado resultante se ejecuta exitosamente. Una inspección manual del contenido compilado con `pyinstxtractor` y decompiladores en línea demuestra que la estructura de clases de seguridad (`drm.py`, `database_manager.py`) es ilegible e irreversible a código fuente original.

---

## 3.5 Sprint 5: Refinamiento B2B y Auditoría Final de Arquitectura (SecOps)

### [x] TASK-5.1: Manejo de Excepciones Globales Ofuscadas
*   **Sub-tarea 5.1.1:** Modificar `sys.excepthook` en el punto de entrada principal para interceptar cualquier excepción no controlada que pueda revelar trazas de código B2B ofuscado.
*   **Sub-tarea 5.1.2:** Implementar un logger encriptado que guarde el traceback localmente en `%APPDATA%/OficinaEficiencia/Config/crash_logs.dat` cifrado simétricamente (AES-256) para evitar fugas de información de la arquitectura a usuarios finales.
*   **DoD:** Forzar un crasheo (`raise Exception('Test Crash B2B')`). El usuario final solo ve un mensaje de error genérico "Contacte a Soporte B2B". El log en disco está ilegible a simple vista.

### [x] TASK-5.2: Verificación de Integridad de Modelos AI
*   **Sub-tarea 5.2.1:** Generar el hash SHA-256 del modelo distribuido `yolov8n.pt`. Guardarlo ofuscado (usando PyArmor) dentro del código en `src/models/model_verifier.py`.
*   **Sub-tarea 5.2.2:** Al inicializar `CameraWorker`, forzar la lectura binaria de `yolov8n.pt` del sistema local (`sys._MEIPASS` o ruta relativa B2B) y calcular su hash SHA-256 en memoria.
*   **Sub-tarea 5.2.3:** Validar que el hash en disco coincide exactamente con el hash ofuscado pre-aprobado. Si no coincide, abortar ejecución e inhabilitar cámara.
*   **DoD:** Intentar reemplazar `yolov8n.pt` por otro modelo falso o con backdoor detiene de inmediato el proceso de tracking y alerta de manipulación del VMS B2B.

### [x] TASK-5.3: Sanitización de Entradas en Interfaz Gráfica CustomTkinter
*   **Sub-tarea 5.3.1:** Para cada entrada de texto (`CTkEntry`) usada en formularios como "Registrar Empleado B2B" o "Cambiar Sucursal", implementar un validador Regex `^[a-zA-Z0-9_\-\s]+$`.
*   **Sub-tarea 5.3.2:** Bloquear intentos de inyección de rutas (Path Traversal) rechazando caracteres especiales (`/`, `\`, `.`, `:`, `;`, `'`, `"`).
*   **DoD:** Ingresar `../../windows/system32/` como nombre de Tenant dispara un "Toast Error" y descarta la operación, previniendo escalada de privilegios a través de los constructores dinámicos en `get_appdata_path()`.

### [x] TASK-5.4: Stress Test de Exportaciones (I/O) en B2B
*   **Sub-tarea 5.4.1:** Llenar temporalmente el Tenant B2B activo (`local_tracking.db` cifrado) con 100,000 registros ficticios de "Eventos de Zona" y marcas de tiempo (`timestamps`) variadas.
*   **Sub-tarea 5.4.2:** Mientras 4 streams de video corren simultáneamente en el Dashboard CustomTkinter, simular operaciones de lectura pesada de usuarios presionando el botón de "Generar Reporte Excel Mensual (XLSX)".
*   **Sub-tarea 5.4.3:** Si el usuario solicita cancelar la exportación en progreso, el hilo en background (`DatabaseWorker`) debe interrumpir el proceso de pandas limpiamente sin corromper el `Workbook` del disco ni provocar fallos de segmentación (Segmentation Faults) en el intérprete subyacente de C++.
*   **DoD:** El proceso de `pandas.read_sql` y escritura Excel se realiza 100% asincrónico (en su propio `ThreadPoolExecutor`). El Grid de video no decae más de un 15% en FPS durante los 15-20 segundos que toma la exportación pesada. El archivo final `.xlsx` contiene los 100k registros intactos (o la cantidad parcial si se canceló correctamente), y un "Toast Notification" en la UI reporta el éxito final del guardado con el path exacto de Windows `%APPDATA%\OficinaEficiencia\Tenants\Norte\reportes\reporte_test.xlsx` (ruta canónica, ver `SPEC/0_REVIEW_FINDINGS.md` P1-1).

---

## 3.6 Setup Inicial y Control de Dependencias (Paso Cero)

Para evitar regresiones o dependencias infladas por alucinación, la IA debe inicializar el entorno con las siguientes versiones estrictas.

### [x] TASK-0.1: Congelar `requirements.txt` (Environment Freeze)
*   **Sub-tarea 0.1.1:** Establecer el intérprete base estricto a **Python 3.10 o 3.11** (PyArmor y PyInstaller no garantizan soporte ofuscado completo B2B en 3.12+).
*   **Sub-tarea 0.1.2:** Sobrescribir `requirements.txt` obligando a las versiones estables:
    ```txt
    customtkinter==5.2.2
    ultralytics==8.1.15
    opencv-python-headless==4.9.0.80
    supervision==0.18.0
    shapely==2.0.3
    wmi==1.5.1
    pyarmor==8.4.6
    pysqlcipher3==1.2.0
    pyinstaller==6.4.0
    pandas==2.2.0
    openpyxl==3.1.2
    cryptography==42.0.5
    pycryptodome==3.20.0
    # Requeridas por el código actual en src/ (no eliminar):
    face_recognition
    numpy
    pillow
    matplotlib
    seaborn
    tkcalendar
    ```
    > **Nota (ver `SPEC/0_REVIEW_FINDINGS.md` P1-4):** `pycryptodome` es obligatorio porque `src/security/drm.py` y los scripts de keygen lo usan (`Crypto.Signature.pkcs1_15`). `face_recognition`, `matplotlib`, `seaborn` y `tkcalendar` también son importados por el código y no deben eliminarse.
*   **Nota Anti-Bloqueo B2B:** Si `pysqlcipher3==1.2.0` falla al instalar en Windows por falta de compiladores de C++ (Build Tools) y OpenSSL, el agente de IA está autorizado a usar `cryptography` (Fernet o AES-GCM) para encriptar los valores en texto plano (nombres, fechas, json) y almacenarlos en un `sqlite3` estándar con extensión segura de base de datos (`.enc_db`), delegando el cifrado a nivel de aplicación (ORM o DAO) en lugar de a nivel motor, para garantizar que el proyecto avance sin dependencias rotas en Windows.
*   **Sub-tarea 0.1.3:** Desinstalar dependencias redundantes (`tkinter` nativo si es posible o `PyQt` si CustomTkinter fue el elegido definitivo) para no inflar el ejecutable B2B. (Nota: `reportlab` y `plotly` figuraban en el `requirements.txt` legacy pero **no** son importados por `src/`; se eliminaron del freeze — ver `SPEC/0_REVIEW_FINDINGS.md` P0-1.)
*   **DoD:** Ejecutar `pip install -r requirements.txt` en un entorno virtual limpio no arroja conflictos de compatibilidad en Windows.

## 3.7 Resumen del Proyecto y Validaciones B2B

*   Total de Tareas a Ejecutar: 19 Tareas Principales
*   Total de Sub-Tareas: 53 Sub-tareas granulares y verificables.
*   Ruta Crítica: Multi-Threading (Sprint 1) -> CustomTkinter UI (Sprint 2) -> Multi-Tenant B2B (Sprint 3) -> DRM/Ofuscación (Sprint 4) -> SecOps Audit (Sprint 5).
*   Prohibición Absoluta de Mezclar los alcances de los Sprints (Anti-Vibe Hacking). Todo Pull Request que consolide los objetivos técnicos o se salte el Freeze de dependencias deberá ser rechazado bajo la matriz de pruebas de regresión.