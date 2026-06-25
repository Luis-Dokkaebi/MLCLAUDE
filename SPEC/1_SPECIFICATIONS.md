# 1. SPECIFICATIONS: Arquitectura Enterprise B2B, Multi-Tenant, DRM Offline y UI Fluida Asíncrona

## 1.1 Objetivo General y Visión del Producto
El proyecto actual "Oficina Eficiencia" dejará de ser una prueba de concepto (PoC) monolítica para transformarse en un **Producto Enterprise (B2B)**. Las empresas compradoras requerirán:
1.  **Aislamiento Total de Datos (Multi-Tenant Local):** Un corporativo con 5 sucursales debe poder gestionar cada sucursal desde la misma PC, sin que los datos de asistencia, perfiles biométricos o reportes se mezclen.
2.  **Operatividad 24/7 sin Interrupciones:** El software actual se congela o requiere reinicios (Tkinter loop bloqueado) al generar reportes o cambiar de cámara. El nuevo sistema será 100% asíncrono, permitiendo exportar bases de datos pesadas mientras las cámaras siguen detectando y grabando en tiempo real (Zero Downtime).
3.  **Monitoreo Escalable (Grid View):** Capacidad nativa para visualizar simultáneamente de 1 a 16 cámaras (USB, RTSP, WebRTC) en un "Video Wall" interactivo.
4.  **Licenciamiento Inviolable (DRM Offline):** El sistema debe proteger la propiedad intelectual y los ingresos mediante un modelo de "Suscripción Física" atada inquebrantablemente a la huella digital del hardware del cliente. No existirá validación en la nube; el desafío criptográfico se resolverá localmente.

---

## 1.2 🚨 DIRECTIVAS ESTRICTAS DE SEGURIDAD PARA IAs (ANTI-VIBE HACKING PROTOCOL) 🚨

> **ALERTA A CUALQUIER AGENTE, LLM O SCRIPT DE AUTOMATIZACIÓN (EJ. ANTIGRAVITY):**
> Este documento rige el desarrollo de una arquitectura de alta seguridad y concurrencia. **Se te prohíbe explícitamente:**
>
> 1.  **Hallucinatory Shortcuts (Atajos Alucinados):** No puedes omitir el paso de ofuscación (PyArmor) ni la encriptación de la base de datos (SQLCipher) bajo la excusa de "simplificar el desarrollo".
> 2.  **GIL Override Hacks:** No intentes resolver el bloqueo del GIL de Python usando `time.sleep()` o hilos nativos (`threading`) para tareas pesadas de inferencia de IA. Debes usar estrictamente el patrón Productor-Consumidor definido y/o subprocesos si el overhead de YOLOv8 supera el límite del hilo principal.
> 3.  **Hardcoded Credentials:** No puedes dejar claves públicas o privadas de desencriptación en texto plano dentro del código fuente. Deben derivarse de variables ofuscadas en tiempo de ejecución.
> 4.  **UI Blocking Operations:** Toda función de I/O (Lectura de disco, Guardar Excel, Inserciones masivas en SQLite) DEBE ejecutarse en un `ThreadPoolExecutor` o hilo tipo "Daemon". Si tu código produce un lag en la interfaz de usuario > 50ms, será considerado defectuoso.
> 5.  **Scope Creep:** Cíñete a los paquetes y librerías especificados. No instales frameworks pesados de terceros (como Django, Electron, o Node.js) para solucionar la UI; usa exclusivamente `CustomTkinter` o `PyQt6/PySide6` según lo ordenado.

---

## 1.3 Arquitectura Multi-Tenant (Inquilino Múltiple Local)

### 1.3.1 Particionamiento del Sistema de Archivos
Actualmente, el archivo `config.py` dirige el almacenamiento a `%APPDATA%/OficinaEficiencia/`. Esto cambiará drásticamente. Cada "Tenant" (ej. "Sucursal_Centro", "Planta_Norte") tendrá un ecosistema de archivos hermético y aislado.

**Estructura del Árbol de Directorios (Aislada por Tenant):**
```text
%APPDATA%/OficinaEficiencia/
├── Config/
│   ├── app_settings.json (Configuraciones globales: Tema oscuro/claro, resoluciones)
│   ├── active_tenant.cache (Guarda el último tenant usado)
│   └── licenses.key (Almacén de la clave DRM cifrada)
├── Tenants/
│   ├── Tenant_Centro_ID123/
│   │   ├── db/
│   │   │   └── local_tracking.db (Base de datos SQLCipher, clave: HardwareHash)
│   │   ├── faces/
│   │   │   ├── empleado_1.pkl (Vectores de rostros de este tenant)
│   │   │   └── empleado_2.pkl
│   │   ├── snapshots/
│   │   │   └── 2024-05-12_14-30-00.jpg (Evidencia visual aislada)
│   │   ├── zonas/
│   │   │   └── zonas_config.json (Coordenadas de intrusión específicas)
│   │   └── reportes/
│   │       └── reporte_202405.xlsx (Exportaciones XLSX/PDF aisladas)
│   ├── Tenant_Norte_ID456/
│   │   ├── db/...
│   │   ├── faces/...
│   │   ├── snapshots/...
│   │   ├── zonas/...
│   │   └── reportes/...
```

> **RUTA CANÓNICA (autoridad: `config/path_utils.py::get_tenant_path`):** Todo subdirectorio de Tenant cuelga directamente de `Tenants/<TenantID>/` (`db`, `faces`, `snapshots`, `zonas`, `reportes`). **No existe** un segmento intermedio `data/`. Cualquier referencia a `Tenants/[ID]/data/...` en versiones anteriores de estos documentos es errónea y queda derogada (ver `SPEC/0_REVIEW_FINDINGS.md` P1-1).

### 1.3.2 Ciclo de Vida del Tenant
1.  **Boot Phase:** Al abrir el ejecutable (`src/main_ui.py`), se lee `app_settings.json`.
2.  **Tenant Selection:** Si existen múltiples carpetas en `Tenants/`, aparece una ventana modal de "Selección de Sucursal".
3.  **Mounting:** Al seleccionar "Tenant_Centro", la clase `PathUtils.set_active_tenant("Tenant_Centro_ID123")` sobreescribe las variables globales. Todo acceso a SQLite o YOLO a partir de ese momento usará las rutas relativas a ese Tenant. No se permite el cruce de datos bajo ninguna circunstancia (ej. un empleado registrado en "Norte" jamás será reconocido por la cámara si el sistema está montado en "Centro").

---

## 1.4 Arquitectura de Concurrencia de Múltiples Cámaras (Zero Blocking)

Para que el software B2B se sienta "Premium" (no rústico), la interfaz nunca debe congelarse.

### 1.4.1 Hilos y Patrón Productor-Consumidor (Frame Queues)
El diseño monolítico donde `cv2.VideoCapture()` y `tk.mainloop()` competían por tiempo de CPU será destruido.
Se usará una arquitectura de Paso de Mensajes (Message Passing):

*   **Thread 0 (Main UI Thread):** Dedicado *únicamente* a refrescar la interfaz gráfica de `CustomTkinter` a 30-60 FPS, procesar clics del usuario y vaciar colas de imágenes.
*   **Thread 1..N (Camera Producers):** Un hilo "Daemon" por cada cámara activa.
    *   **Responsabilidades:** Leer el frame (`cap.read()`), pasarlo al motor YOLOv8 (Inferencia), dibujar las Bounding Boxes (Cajas), aplicar lógica de `shapely` para intrusión de zonas, enviar el evento a la Base de Datos, y finalmente empujar el `numpy array` (imagen procesada) a una estructura `queue.Queue(maxsize=5)`.
    *   **Control de Flujo:** Si el Main Thread es muy lento para renderizar (la cola se llena), el Producer debe saltar (droppear) frames usando `queue.put_nowait()` manejando el error, priorizando el "Tiempo Real" sobre la visualización de todos los frames.
*   **Thread X (Database & Export Worker):** Un hilo dedicado para I/O. Cuando el usuario hace clic en "Exportar Reporte Mensual a Excel", el UI Thread envía un comando a la cola de trabajo del Database Worker. Este ejecuta la consulta `pandas.read_sql()`, genera el `.xlsx` en disco, y devuelve una señal de éxito al UI Thread para mostrar un "Toast Notification" emergente de éxito. Todo ocurre en segundo plano.

---

## 1.5 Especificaciones de UI/UX Moderna (Fluid Grid View)

El aspecto "Rústico" se elimina por completo. La aplicación simulará el aspecto de un VMS (Video Management System) profesional (como Milestone o HikCentral).

### 1.5.1 Disposición de Componentes (CustomTkinter)
*   **Layout Principal:** Pantalla completa (Borderless o con barra superior personalizada). Fondo en modo oscuro (`#1E1E1E`).
*   **Sidebar (Menú Izquierdo Colapsable):** Contiene íconos vectoriales modernos para: "Monitoreo en Vivo", "Gestión de Empleados", "Configuración de Zonas", "Reportes Históricos" y "Cambiar Sucursal (Tenant)".
*   **Área Central (Dashboard Dinámico):** Un contenedor `CTkScrollableFrame` o `CTkFrame` basado en `.grid()`.

### 1.5.2 Comportamiento de "Grid View" a "Single View"
1.  **Auto-Layout:** Si hay 1 cámara, ocupa el 100% del área central. Si hay 2, se dividen 50/50 horizontalmente. Si hay 4, forman una matriz 2x2. Si hay 9, matriz 3x3.
2.  **Zoom in (Doble Clic):** Si el usuario hace doble clic sobre la transmisión de la Cámara 3 en una matriz 2x2, el Layout Manager elimina temporalmente las cámaras 1, 2 y 4 de la vista, y expande la Cámara 3 al 100% de la ventana.
3.  **Zoom out:** Un nuevo doble clic regresa la interfaz a la vista de matriz 2x2, recuperando el estado anterior sin reiniciar el proceso de captura subyacente de OpenCV (las cámaras 1, 2 y 4 nunca dejaron de procesarse en segundo plano, simplemente se ocultaron de la GUI).

---

## 1.6 Sistema DRM (Digital Rights Management) y Cifrado B2B

La aplicación representa años de I+D en visión computacional. Su distribución comercial exige blindaje de Grado Militar contra piratería y copia no autorizada ("Crackers").

### 1.6.1 Hardware Fingerprinting (Huella Digital Inmutable)
El software debe generar una "Identidad de Máquina" única que no cambie si el usuario formatea Windows, pero que falle si clonan el disco a otra PC física.
*   **Librería Estricta:** `wmi` (Windows Management Instrumentation).
*   **Componentes a Extraer:**
    1.  `Win32_BaseBoard.SerialNumber` (Serial de la Tarjeta Madre).
    2.  `Win32_Processor.ProcessorId` (Identificador del CPU).
    3.  `Win32_DiskDrive.SerialNumber` (Serial Físico del Disco Principal).
*   **Manejo de Casos Extremos (Edge Cases):** Si `wmi` falla porque el servicio de Windows está corrupto, o retorna cadenas vacías (ej. en algunas placas genéricas chinas), el sistema debe iterar usando el MAC Address de la tarjeta de red primaria (`getmac`) o el UUID de la BIOS (`Win32_ComputerSystemProduct.UUID`) como Plan B.
*   **Derivación Criptográfica:** Estos 3-4 strings concatenados pasarán por un proceso de hashing `SHA-256` con un Salt (`#SaltEmpresarialV1`) embebido (y ofuscado) en el código. El resultado es el `Machine_Hash`. (Nota: la implementación de referencia en `src/security/drm.py` usa `hashlib.sha256`; toda la documentación se unifica a SHA-256 — ver `SPEC/0_REVIEW_FINDINGS.md` P1-2.)

### 1.6.2 Validación de Clave (Challenge-Response Offline)

> **Precisión criptográfica (corrige versión previa — ver `SPEC/0_REVIEW_FINDINGS.md` P1-3):** El esquema es **firma digital RSA**, no "cifrado". RSA con llave privada **firma**; el cliente **verifica** la firma con la llave pública. El payload (Machine_Hash + tier + expiración) viaja en claro dentro de la licencia; lo que garantiza la autenticidad es la firma, no la confidencialidad. Esta es la semántica que ya implementa `6_KEYGEN_GUIDE` (`pkcs1_15.sign` / `pkcs1_15.verify`).

1.  **Proveedor (Tú):** Construyes un payload JSON con el `Machine_Hash` (`hw_id`), el nivel de licencia (ej. `max_cams=4`) y una fecha de expiración Epoch (ej. `1735689600`), y lo **firmas** con tu Llave Privada RSA-2048. El paquete `payload || firma` codificado en Base64 es la "Clave de Activación" que entregas al cliente B2B.
2.  **Cliente:** Ingresa la Clave en la pantalla de "Activación de Software" (UI CustomTkinter).
3.  **Software:** Decodifica el Base64, separa payload y firma, y **verifica la firma** con la Llave Pública RSA (incrustada en el código y protegida por PyArmor).
4.  **Auditoría Interna:** Si la firma no verifica, la activación falla de inmediato. Si el `hw_id` del payload NO coincide con el hardware local calculado en ese milisegundo, la activación falla. Si la fecha actual `datetime.now()` es mayor a la Fecha de Expiración, muestra "Suscripción Vencida". Si todo es válido, guarda la licencia validada en `%APPDATA%/OficinaEficiencia/Config/licenses.key` protegida con el DPAPI de Windows.

### 1.6.3 Cifrado de Base de Datos y PyArmor (Ofuscación B2B)
*   **Problema a resolver:** Si el código Python no se ofusca, un atacante usa `uncompyle6` en el ejecutable, encuentra la función `if is_license_valid():` y la reemplaza por `return True` ("Vibe Hacking" humano / Cracking). Además, podría abrir la base de datos SQLite y ver las contraseñas o modificar registros de horas de empleados.
*   **Solución (SQLCipher):** La librería `pysqlcipher3` (o `sqlcipher3`) reemplazará a `sqlite3`. La "Clave de Encriptación de Base de Datos" será el propio `Machine_Hash`. Es decir, la base de datos local de una PC está intrínsecamente ligada al hardware. Si un empleado roba el archivo `local_tracking.db` y se lo lleva a su casa, el archivo será indescifrable porque el Hash de su placa base en casa no coincidirá.
*   **Solución (PyArmor):** Durante la compilación, el pipeline CI/CD o el script `compilar_exe.bat` ejecutará `pyarmor gen --enable-jit --restrict 1 --pack dist/ src/`. Esto convierte todo el Python AST (Abstract Syntax Tree) en un bytecode propietario C/C++ ininteligible e irreversible antes de que PyInstaller genere el empaquetado final. Esto protege la Llave Pública RSA y los algoritmos biométricos.

## 1.7 Módulo de Exportación y Cumplimiento B2B (Data Compliance)

### 1.7.1 Generación de Reportes Asincrónicos
Para cumplir con las auditorías de Recursos Humanos (RRHH) en empresas, los reportes deben exportarse sin detener el VMS (Video Management System).
*   **Formatos Soportados:** Excel (.xlsx) y PDF.
*   **Contenido:** El reporte debe contener: "Nombre del Empleado", "Hora de Entrada", "Hora de Salida", "Tiempo en Zona Restringida" y "Eficiencia General".
*   **Manejo de Errores de Permiso:** Si el archivo destino (ej. `reporte_mayo.xlsx`) está siendo abierto por Microsoft Excel por el usuario administrativo, el Hilo de Reportes no debe crashear la aplicación. Debe capturar la excepción `PermissionError` y retornar un Toast Notification a la UI de `CustomTkinter` que diga "Cierre el archivo Excel antes de sobreescribirlo".

### 1.7.2 Estructura de Base de Datos SQLite/SQLCipher (Esquema Resumido)
1.  **Tabla `empleados`**: `id` (PK), `nombre` (TEXT), `departamento` (TEXT), `face_vector_path` (TEXT - path cifrado a archivo .pkl), `creado_en` (DATETIME).
2.  **Tabla `eventos_asistencia`**: `id` (PK), `empleado_id` (FK), `tipo_evento` (TEXT - 'ENTRADA', 'SALIDA', 'INTRUSION'), `timestamp` (DATETIME), `camara_id` (INTEGER).
3.  **Tabla `zonas`**: `id` (PK), `nombre` (TEXT), `poligono_json` (TEXT - Array de coordenadas X,Y relativas).
4.  **Tabla `auditoria_seguridad`**: `id` (PK), `accion` (TEXT - ej. 'LOGIN_FALLIDO', 'TENANT_CREADO'), `usuario_os` (TEXT), `timestamp` (DATETIME). Esta tabla garantiza trazabilidad de cualquier intento de hackeo o "Vibe Hacking" manual.

## 1.8 Manejo de Estado Interno (State Management en CustomTkinter)

Dado que `CustomTkinter` no tiene un manejo de estado global como React (Redux), el software implementará un Patrón Singleton `SessionManager`:
*   Este objeto residirá en la memoria principal (Main Thread).
*   Almacenará de forma segura y temporal el `active_tenant_id` y el estado del `CameraManager` (cuántos hilos están activos).
*   Cuando la UI solicita detener una cámara (ej. el administrador hace clic en "Apagar Cámara 2"), el `SessionManager` envía una bandera `running=False` al Hilo Productor correspondiente, y limpia el frame del UI (colocando una imagen negra o un placeholder).

## 1.9 Directivas de Compatibilidad PyInstaller (Runtime)

Al convertir scripts Python ofuscados en un binario portátil B2B con PyInstaller, surgen problemas de "Path Resolution".
*   El código no debe usar `os.path.abspath(__file__)` en las secciones críticas (ej. al cargar pesos de YOLO `yolov8n.pt` o certificados RSA), ya que en el binario compilado `__file__` apuntará a la carpeta temporal volátil de extracción.
*   En su lugar, se obliga al agente de IA a usar `sys._MEIPASS` si existe, o buscar en el directorio actual (`os.getcwd()`).
*   Esto asegura que el empaquetado `gui_app.spec` distribuya correctamente el archivo `.pt` (Modelo PyTorch) sin arrojar el error crítico "FileNotFoundError: yolov8n.pt".

## 1.10 Especificaciones UI/UX B2B Nivel Píxel (Style Guide)

Para evitar alucinaciones gráficas de IAs de interfaz de usuario, la aplicación DEBE adherirse a la siguiente paleta de colores y componentes interactivos usando `CustomTkinter`:

*   **Paleta de Colores (Modo Oscuro):**
    *   Fondo Base (`bg_color`): `#1E1E1E` (Gris oscuro premium).
    *   Panel Lateral / Sidebar: `#2B2B2B` con borde derecho `#333333` (ancho estricto: 250px).
    *   Colores de Acento (Botones/Switch): Principal `#1f6aa5` (Azul corporativo), Hover `#144870`.
    *   Textos Principales: `#FFFFFF`. Textos Secundarios: `#A0A0A0`.
    *   Rojo de Alerta (Intrusión de Zonas/Cámara Desconectada): `#E74C3C` con Hover `#C0392B`.
    *   Verde de Éxito (Reconocimiento Exitoso): `#2ECC71`.

*   **Tipografía y Estilos:**
    *   Fuente Universal: `("Roboto", 14)`. Títulos H1: `("Roboto", 24, "bold")`.
    *   Botones (Corner Radius): `8px` para darle un aspecto de app de Windows 11 nativa.

*   **Máquina de Estados de la Cámara (`CTkLabel` de Video):**
    1.  *Estado Iniciando:* Fondo negro, texto blanco al centro `("Cargando Modelo AI...")`.
    2.  *Estado Conectado (En Vivo):* El label recibe las imágenes convertidas de `cv2` a `ImageTk.PhotoImage` a no menos de 15 FPS (restringido a un tamaño uniforme dependiendo del número de cuadrículas).
    3.  *Estado Desconectado/Error:* Fondo `#2B2B2B`, texto rojo `("Señal de Cámara Perdida")` y un sub-texto secundario `("Reintentando conexión en 5s...")`.
    4.  *Estado Hover (Sobre la Cuadrícula):* Al pasar el ratón (`<Enter>`), dibujar un borde perimetral sutil (`#1f6aa5`) de 2px alrededor de la cámara seleccionada.

## 1.11 Estructuras de Datos JSON Precisas (Settings y Zonas)

Los archivos guardados en el disco para la configuración del Tenant no usarán estructuras arbitrarias. Tienen que coincidir exactamente con el siguiente Type Hinting (Sugerencia de Tipos):

**1. Archivo `zonas_config.json` (Ejemplo de Almacenamiento Geométrico de Shapely):**
```json
{
  "tenant_id": "Norte_001",
  "cameras": {
    "0": {
      "zones": [
        {
          "zone_id": "z_entrada_1",
          "name": "Puerta Principal",
          "color": "#FF0000",
          "points": [[100, 200], [400, 200], [400, 500], [100, 500]],
          "is_restricted": true
        }
      ]
    }
  }
}
```
*   *Restricción para IAs:* No utilices librerías pesadas para parsear JSON. Usa `json.load/dump`. Las coordenadas (points) deben escalar de acuerdo con el tamaño actual del frame en la UI. Las coordenadas originales del video fuente (ej. 1920x1080) deben proyectarse (proporcionalmente) al tamaño del UI Label (ej. 640x480).

## 1.12 Algoritmos de Tolerancia a Fallos y Prevención de Crashes

1.  **OpenCV VideoCapture Corrupto:** En ocasiones cámaras RTSP (Hikvision/Dahua) envían frames a la mitad (`ret=True`, pero `frame is None` o matriz vacía). El código fuente DEBE verificar la integridad del numpy array (`if frame is not None and frame.size > 0:`) antes de mandarlo a YOLO. Si falla esta verificación, arrojar una excepción y reiniciar la captura.
2.  **Multiprocesamiento en Windows (`__main__` guard):** Si el agente de IA decide usar `multiprocessing.Process` en lugar de `threading.Thread` para separar YOLO del GUI (debido al GIL), está ESTRICTAMENTE OBLIGADO a asegurar que el punto de entrada de `src/main_ui.py` contenga `if __name__ == '__main__':` seguido inmediatamente de `multiprocessing.freeze_support()`. Si esto se olvida, el empaquetado final B2B con PyInstaller creará una "Bomba Fork" que colapsará el Windows del cliente abriendo mil ventanas.
