# SDD: Distribución de Aplicación Standalone ("Zero-Dependency")

## 1. Introducción
**Objetivo:** Permitir que la aplicación de Monitoreo de Oficina Eficiencia se pueda distribuir, instalar y ejecutar en la máquina de cualquier cliente Windows sin requerir la instalación previa de Python, Conda, o dependencias externas complejas. La experiencia debe ser análoga a la instalación de un videojuego: "Instalar y usar".

## 2. Requisitos de la Especificación
- **Autonomía:** El ejecutable debe contener todo su entorno (intérprete de Python, librerías como OpenCV, PyTorch, YOLOv8, Face Recognition).
- **Gestión de Permisos:** La aplicación no debe intentar escribir en su directorio de instalación (típicamente `C:\Program Files\...`), evitando errores de permisos de escritura. Todo archivo de estado (BBDD SQLite, capturas, logs, reportes, zonas) debe persistirse en el directorio del perfil del usuario (ej. `%APPDATA%\OficinaEficiencia`).
- **Prevención de Conflictos de Librerías:** Los conflictos conocidos (como el choque de OpenMP entre NumPy y PyTorch) deben manejarse dinámicamente y silenciarse dentro del código fuente compilado.
- **Portabilidad de Modelos de IA:** Los modelos (YOLOv8, Face Recognition models) deben estar empaquetados dentro del binario y ser referenciados utilizando rutas relativas correctas en tiempo de ejecución (`sys._MEIPASS`).
- **Instalador Profesional:** El resultado de la compilación debe poder integrarse en un instalador tradicional (.exe).

## 3. Arquitectura y Estrategia de Solución

### 3.1. Empaquetado del Binario (PyInstaller)
- Se utilizará `PyInstaller` en modo `--onedir` (directorio de distribución). Esto es preferible sobre `--onefile` para aplicaciones grandes con PyTorch/YOLO porque reduce el tiempo de arranque drásticamente al no tener que descomprimir gigabytes en el directorio temporal en cada ejecución.
- El script de compilación (`compilar_exe.bat`) y la especificación (`gui_app.spec`) se encargarán de inyectar directamente las `.dll` problemáticas o esenciales (como `mkl_*.dll` de MKL y `libiomp5md.dll` de PyTorch).
- Se forzarán los hooks de empaquetado (`collect_all`, `copy_metadata`) para `ultralytics`, `supervision` y librerías que dependan de carga dinámica.

### 3.2. Gestión de Rutas en Tiempo de Ejecución (Runtime Paths)
Para que la aplicación funcione como Standalone, debe distinguir entre dos tipos de rutas:
1.  **Rutas de Solo Lectura (Recursos):** Archivos que vienen con el ejecutable (modelos, scripts, UI). En tiempo de ejecución, cuando se congela con PyInstaller, estos recursos se desempaquetan (o referencian) en un directorio local si se usa `--onedir`, o temporal apuntado por `sys._MEIPASS` si se usara `--onefile`.
2.  **Rutas de Lectura/Escritura (Datos de Usuario):** Bases de datos (`.sqlite`), archivos de zonas (`.json`), reportes (`.xlsx`).

La configuración (`config.py` y `path_utils.py`) debe implementar de forma centralizada:
- `get_resource_path(relative_path)`: Retorna la ruta al paquete de la aplicación compilada (o ruta local en modo desarrollo).
- `get_appdata_path()`: Apunta invariablemente a `os.environ.get('APPDATA')` (Windows) + `\OficinaEficiencia`. Debe asegurar que las carpetas se creen recursivamente si no existen en el primer arranque.

### 3.3. Resolución de Conflictos Críticos (OpenMP / DLLs)
- En el archivo principal de entrada de la interfaz, **antes** de importar librerías pesadas como OpenCV (`cv2`) o PyTorch (`torch`), se debe forzar:
  ```python
  import os
  os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
  ```
- El orden de importación estricto: Primero `torch`, luego `cv2`. Esto previene fallos silenciosos al cargar la aplicación compilada en máquinas cliente.

### 3.4. Generación del Instalador Final (Inno Setup)
- Una vez PyInstaller genera la carpeta `dist/gui_app/`, se utilizará Inno Setup para compilar todo ese directorio en un único archivo de instalación: `setup_oficina_eficiencia_v1.0.exe`.
- El instalador se encargará de crear el acceso directo en el Escritorio y en el Menú Inicio apuntando a `gui_app.exe`.
- Inno Setup debe copiar todo el directorio intacto sin requerir instalación adicional de variables de entorno ni Python en el sistema destino.

## 4. Criterios de Aceptación
1.  **Instalación Limpia:** Se puede instalar la aplicación usando el `.exe` generado por Inno Setup en una máquina Windows "virgen" (sin Python ni Conda instalados).
2.  **Ejecución Autónoma:** La aplicación arranca correctamente; el entorno resuelve dinámicamente todas sus dependencias.
3.  **Persistencia Segura:** El usuario puede guardar configuraciones, generar reportes y guardar datos en SQLite sin que la aplicación deba ejecutarse como Administrador. Todo dato se guarda y lee de `%APPDATA%`.
4.  **Inferencia Intacta:** El modelo YOLO detecta entidades y Face Recognition identifica empleados exitosamente utilizando los modelos empaquetados.

## 5. Pasos de Implementación Recomendados
*(Nota: Acorde a las restricciones del usuario, no se realizarán modificaciones de código en esta tarea, pero esta es la ruta a seguir)*
1. Verificar que todo acceso a archivo modificable se realice usando la ruta de `APPDATA` de `config.py`.
2. Asegurar que las llamadas a archivos `.pt` (como `yolov8n.pt`) usen la ruta del recurso dinámico y no una ruta estática.
3. Compilar usando `compilar_exe.bat`.
4. Utilizar Inno Setup para construir el empaquetado final a partir del resultado en `dist/`.
5. Probar el resultado en "Windows Sandbox" para confirmar el escenario de cero-dependencias.