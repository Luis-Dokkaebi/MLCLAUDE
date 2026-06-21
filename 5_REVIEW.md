# 5. REVIEW: Auditoría de Aceptación, Testing B2B y Pruebas de Penetración

La versión 1.0 (Enterprise/B2B) de "Oficina Eficiencia" no se considerará "Realeased" hasta que supere todas las pruebas de esta auditoría, diseñada para garantizar cero fugas de memoria, robustez anti-hacking (DRM/SQLCipher) y un rendimiento sin bloqueos (Multi-Threading en CustomTkinter).

**🚨 DIRECTIVA ESTRICTA DE AUDITORÍA PARA IAs (ANTI-VIBE HACKING PROTOCOL) 🚨**
> *La Inteligencia Artificial o el QA asignado no puede simular estas pruebas.* Cada test debe ejecutarse sobre el binario ofuscado `.exe` (Pruebas de Caja Negra) o usando el suite de `unittest` / `pytest` nativo (Pruebas de Caja Blanca). Las excepciones como `sqlite3.DatabaseError` o `queue.Full` son **CRITERIOS DE ÉXITO**, no fallos, ya que demuestran que las mitigaciones están activas (encriptación o prevenciones de memory leak). Todo reporte falso positivo de un Agente se considerará una violación del protocolo.

---

## 5.1 Criterios de Aceptación Funcional (Caja Negra)

El usuario final o equipo de QA debe validar el software interactuando con el ejecutable generado (`OficinaEficiencia_B2B.exe`) sin mirar el código fuente:

### [ ] Prueba 5.1.1: Concurrencia Extrema (Zero Blocking)
*   **Procedimiento:** Iniciar la aplicación e instanciar al menos 4 streams de video. En una PC con bajos recursos, emular estrés limitando el uso de CPU.
*   **Acción:** Hacer clic en "Generar Reporte Excel Mensual" (o equivalente que genere I/O pesado).
*   **Validación de Éxito:** Las 4 cámaras DEBEN continuar renderizando frames (sin "Laguear" la ventana ni congelar los `CTkLabel`). La aplicación no muestra "No Responde" en la barra de título de Windows en ningún momento. El reporte aparece exitosamente en la carpeta `%APPDATA%/OficinaEficiencia/Tenants/[ID]/data/reportes/`.

### [ ] Prueba 5.1.2: Aislamiento Local B2B (Multi-Tenant Test)
*   **Procedimiento:** Al iniciar el ejecutable, en la ventana modal de "Selección de Sucursal", crear "Sucursal Norte" y "Sucursal Sur".
*   **Acción:** Ingresar a "Sucursal Norte", registrar el rostro de un empleado ("Juan Perez"). Cerrar la app y volver a ingresar seleccionando "Sucursal Sur".
*   **Validación de Éxito:** Al entrar al menú "Empleados" de la "Sucursal Sur", "Juan Perez" NO debe existir. La cámara de la sucursal sur NO debe reconocerlo (devuelve `Unknown` o `Desconocido`). Los archivos `.db` en `%APPDATA%` deben estar en subcarpetas separadas físicamente.

### [ ] Prueba 5.1.3: Navegación Asíncrona Fluida (Single-Window Application)
*   **Procedimiento:** Durante el monitoreo de video (Grid View con 4 cámaras), hacer doble clic rápidamente en uno de los videos, luego presionar 5 botones diferentes del menú lateral (Sidebar) en menos de 2 segundos.
*   **Validación de Éxito:** La aplicación responde instantáneamente (<100ms) cambiando de pestaña ("Zonas", "Configuración", etc.) sin crashear. El doble clic expande (Single View) y colapsa (Grid View) el video correctamente sin detener las cámaras de fondo.

---

## 5.2 Pruebas Unitarias y de Integración Automatizadas (TDD)

El repositorio debe contener el directorio `tests/` con los siguientes scripts que se ejecutarán mediante `python -m unittest discover tests/`:

### [ ] Test de Desempeño y Control de Memoria (Thread Queues)
*   **Archivo:** `test_camera_worker_leaks.py`
*   **Objetivo:** Validar el "Drop Frame Protocol" del `CameraWorker`.
*   **Procedimiento Mock:** Instanciar un `CameraWorker` con `fps_limit=30` (Productor rápido) y asignarle una `queue.Queue(maxsize=5)`. Ejecutar el worker sin arrancar el Consumidor (UI) durante 5 segundos.
*   **Criterio de Éxito:** La prueba pasa si la cola se llena (tiene 5 elementos) y el worker no lanza una excepción no controlada (`queue.Full` debe ser silenciado por `try-except`), previniendo un memory leak. El uso de RAM debe permanecer estable.

### [ ] Test DRM de Hardware (WMI Fingerprint)
*   **Archivo:** `test_wmi_drm_hash.py`
*   **Objetivo:** Validar que el algoritmo de generación de Hardware ID sea inmutable y determinista.
*   **Procedimiento Mock:** Llamar a `DRMValidator.get_hardware_fingerprint()` en un bucle cerrado de 10 iteraciones separadas por 1 segundo.
*   **Criterio de Éxito:** El Hash SHA-256 devuelto DEBE ser idéntico en las 10 iteraciones. Además, simular un fallo del servicio WMI (Mock) y verificar que el bloque de contingencia (Fallback usando MAC Address) retorna un Hash válido sin crashear la aplicación.

### [ ] Test de Aislamiento de Rutas por Tenant
*   **Archivo:** `test_tenant_routing.py`
*   **Objetivo:** Asegurar que `path_utils.py` resuelva las rutas locales al Tenant activo en tiempo real.
*   **Procedimiento Mock:** Establecer `Session.active_tenant_id = 'Tenant_A'`. Llamar a `get_appdata_path('db')`. Luego cambiar a `'Tenant_B'` y llamar a la misma función.
*   **Criterio de Éxito:** Las cadenas retornadas deben ser diferentes y apuntar estrictamente a sus subdirectorios herméticos (`...\Tenants\Tenant_A\db` y `...\Tenants\Tenant_B\db`).

---

## 5.3 Pruebas de Penetración y Auditoría de Seguridad (Pen-Testing)

Para garantizar que el software está blindado contra crackers e intentos de vulnerar el modelo de suscripción:

### [ ] Auditoría 5.3.1: Resiliencia a la Decompilación (PyArmor Check)
*   **Metodología:** Extraer los archivos del `.exe` usando un decompiler de PyInstaller (ej. `pyinstxtractor`). Localizar los módulos críticos de la lógica de licencias (`src/security/drm.pyc`).
*   **Vector de Ataque:** Intentar pasar el `.pyc` extraído por un decompilador de bytecode estándar como `uncompyle6` o servicios en línea.
*   **Criterio de Aprobación B2B:** El decompilador DEBE fallar ("Invalid Magic Number" o arrojar bytecode ofuscado indescifrable C/C++ inyectado por PyArmor). Si la clave pública RSA o la lógica `if license_valid` son visibles, la ofuscación falló y el build es rechazado.

### [ ] Auditoría 5.3.2: SQLCipher y Protección de la Base de Datos Local
*   **Metodología:** Navegar a `%APPDATA%/OficinaEficiencia/Tenants/[ID]/db/`. Copiar el archivo `local_tracking.db`.
*   **Vector de Ataque:** Abrir el archivo copiado usando una herramienta de terceros como "DB Browser for SQLite".
*   **Criterio de Aprobación B2B:** La base de datos DEBE solicitar una contraseña de desencriptación (la derivada del Hardware Hash). Si el auditor puede ver las tablas de empleados, contraseñas o registros de asistencia en texto plano, la integración de `pysqlcipher3` falló y el build es rechazado.

### [ ] Auditoría 5.3.3: Inyección de Licencias Inválidas (Spoofing)
*   **Metodología:** En la pantalla de Activación de Licencia de la UI, ingresar una cadena Base64 generada con una llave privada incorrecta, o una licencia cuya fecha Epoch fue alterada manualmente para extender el vencimiento (ej. de "2024" a "2099").
*   **Criterio de Aprobación B2B:** El `DRMValidator` DEBE detectar que la firma asimétrica RSA fue corrompida y rechazar la licencia al instante, sin arrojar "Python Tracebacks" en la consola que den pistas al atacante sobre cómo evadir la validación.

## 5.4 Auditoría 5.4: Stress Test de Red (Integración RTSP Multi-Tenant)

### [ ] Prueba 5.4.1: Recuperación Ante Pérdida de Stream
*   **Procedimiento:** Conectar 4 streams RTSP en el Grid. Desconectar físicamente el cable de red de la PC o apagar la cámara remota.
*   **Validación de Éxito:** La UI no crashea con `cv2.error`. La caja que contiene la cámara desconectada debe mostrar un `CTkLabel` con el texto "Reconectando..." o una imagen negra.
*   **Recuperación:** Al reconectar la red, el `CameraWorker` (`cap = cv2.VideoCapture`) debe restaurar la señal automáticamente en el próximo ciclo de intento (~5-10 segundos) sin intervención del usuario (Self-Healing Architecture).

### [ ] Prueba 5.4.2: Límite de CPU y Thermal Throttling
*   **Procedimiento:** Correr 16 cámaras concurrentemente en una PC sin GPU dedicada. Observar el Task Manager.
*   **Validación de Éxito:** Si el CPU alcanza 100%, la arquitectura Productor-Consumidor actuará, el Dropping Frame Protocol entrará en acción, los FPS caerán, pero la aplicación NO crasheará (No Memory Leak). Las alertas de la UI se seguirán mostrando y permitiendo al usuario desactivar/eliminar cámaras.

### [ ] Prueba 5.4.3: Perfilamiento de Rendimiento (Performance Profiling)
*   **Procedimiento Técnico:** Antes de compilar, el QA debe ejecutar la aplicación desde la consola de Windows usando el perfilador de cProfile integrado: `python -m cProfile -o b2b_stats.prof src/main_ui.py`.
*   **Acción:** Monitorear 4 cámaras durante exactamente 60 segundos y luego cerrar la ventana limpiamente (cierre de Socket, liberación de memoria).
*   **Validación:** Utilizar `snakeviz b2b_stats.prof` para visualizar las métricas. El hilo principal (`MainThread`) no debe tener ninguna función bloqueante que sume más de `50ms` de `tottime` (tiempo total ejecutándose). Las llamadas de `cv2.VideoCapture.read()` y `ultralytics.YOLO.predict()` deben estar confinadas 100% dentro del hilo "CameraWorker", aisladas del flujo de CustomTkinter.

## 5.5 Reporte de Vulnerabilidades (Bug Bounty / Hotfixes B2B)

Dado el nivel corporativo (VMS/Suscripciones) del producto final, si en cualquier momento un usuario B2B logra sobrepasar el PyArmor o generar una falsa validación WMI, el pipeline de contingencia será el siguiente:
1.  **Aislamiento del Exploit:** El QA o tú mismo replicarán el vector de ataque en un Sandbox (ej. Windows Sandbox).
2.  **Parche Criptográfico (Hotfix):** El Agente Inteligente a cargo deberá actualizar el "Salt" en `DRMValidator` (ej. de `#SaltEmpresarialV1` a `V2`), revocar las llaves públicas RSA anteriores en el código fuente ofuscado, e incrementar el número de versión (ej. 1.0.1) en `VERSION` e `Inno Setup`.
3.  **Distribución Forzosa:** Todas las licencias B2B "Crackeadas" caducarán debido a la incompatibilidad asimétrica, y los clientes legítimos recibirán su nuevo instalador `OficinaEficiencia_1.0.1_B2B.exe` con una nueva clave Base64 generada por el proveedor.

## 5.6 Auditoría de "Vibe Hacking" de Agentes de IA

Si el código resultante de estos documentos ha sido generado total o parcialmente por una IA (como Antigravity), debe pasar por este escrutinio final de 3 preguntas de Sí/No. (Todas deben ser "Sí" para que el binario pueda comercializarse en el mercado B2B):

1.  **Verificación de Dependencias (No-Bloat Check):**
    *   *¿La IA implementó la UI con CustomTkinter/PyQt SIN requerir la instalación no autorizada de servidores locales como Flask/FastAPI o Node.js/Electron, manteniéndose fiel a la Arquitectura "Single Desktop VMS"?*
    *   (Sí/No)
2.  **Verificación de Parametrización (Anti-SQLi):**
    *   *¿Se auditó la totalidad del código SQL para corroborar que ninguna cadena introducida por el usuario B2B en la GUI esté siendo interpolada de manera insegura usando el operador `%s` no validado o F-strings en las sentencias de SQLCipher/SQLite?*
    *   (Sí/No)
3.  **Verificación Cryptográfica de Archivos de Clave (DPAPI):**
    *   *¿La clave de activación se almacena localmente de forma segura (`.key` encriptada) y no existe ningún vector de ataque por archivo `config.json` en texto claro con un "is_licensed=True" flagrante y expuesto al usuario de Windows?*
    *   (Sí/No)

## 5.6 Aprobación Final B2B ("The Golden Master")

Solo tras firmar manualmente este checklist (y automatizar las pruebas unitarias en el pipeline), se considerará al proyecto listo para generar la "Release Candidate 1.0.0 (Enterprise)".
1.  **Pipeline CI/CD Local:** Se ejecuta `compilar_exe.bat` (Limpieza de Builds Antiguas -> Ofuscación PyArmor en Restrict Mode -> PyInstaller Analysis -> Empaquetado EXE).
2.  **Validación Inno Setup (ISCC):** Se construye el empaquetado instalador con `setup_oficina.iss` asegurando que las dependencias visuales (`CustomTkinter` Themes/Assets) y binarias ocultas (`wmi`, `pysqlcipher3.dll`, `libiomp5md.dll` de Torch) estén copiadas en los lugares correctos para Windows x64.
3.  **Deploy Comercial y Keygen:** Se procede a la entrega del instalador a los clientes de prueba (Beta Corporativo) o Producción, usando el "Generador de Claves B2B" privado para firmar con la Llave Privada RSA los `MachineID` proporcionados por los administradores de sucursal.

---

**Firma del Auditor de Código (Antigravity/Jules):** [ _________________________ ]
**Firma del Ingeniero QA/Pruebas de Penetración:** [ _________________________ ]
**Fecha Oficial de Aprobación B2B:** [ _______________ ]