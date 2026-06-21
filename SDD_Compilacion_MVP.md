# Spec-Driven Development (SDD) - Compilación de MVP (Ejecutable Windows)

## 1. Objetivo y Resumen
El objetivo de este desarrollo es crear un entorno de compilación robusto que empaquete la aplicación actual "Oficina Eficiencia" en un ejecutable de Windows (`.exe`) completamente funcional e independiente. Este ejecutable debe servir como MVP (Minimum Viable Product) para que el cliente pueda realizar pruebas de uso sin necesidad de instalar Python, Conda, ni configurar entornos virtuales, dependencias complejas (como YOLO o CUDA) ni variables de entorno.

El sistema actual está diseñado con Python, OpenCV, Ultralytics (YOLOv8), Supervision y Face_Recognition, con un frontend en `Tkinter` ubicado en `src/gui_app.py` que llama al monitoreo principal (`main.py`). El objetivo es que Antigravity (el agente encargado) arregle los problemas de los scripts de compilación actuales y entregue un producto listo para ejecutar.

## 2. Requerimientos

### 2.1. Funcionales
1. **Generación de Ejecutable Único o Directorio:** El resultado debe ser una carpeta o un archivo `.exe` que pueda ser ejecutado en Windows con un doble clic.
2. **Inclusión de Dependencias:** El ejecutable debe incluir todas las dependencias críticas (como `ultralytics`, `supervision`, `face_recognition`), modelos (`yolov8n.pt`, modelos de rostros) y archivos de datos (carpetas `data`, `config`, `models`).
3. **Manejo de Librerías DLL Dinámicas:** El ejecutable debe resolver los conflictos actuales de OpenMP y DLLs faltantes de PyTorch, Numpy y Face_Recognition.
4. **GUI Funcional:** El archivo principal a compilar debe ser `src/gui_app.py`, permitiendo el registro inicial a través de la interfaz de `Tkinter` y posteriormente el lanzamiento del flujo de monitoreo en la misma ventana o un subproceso adecuado.

### 2.2. No Funcionales
1. **Independencia del Entorno:** El script de compilación **no debe depender de rutas absolutas locales** (como `C:\Users\PC\miniconda3\...`), sino calcular dinámicamente dónde se encuentran las bibliotecas en el sistema que compila, o descargar/copiar los recursos de manera automatizada en el entorno de build.
2. **Sistema Operativo Objetivo:** Windows 10/11.
3. **Mantenibilidad:** El código de compilación (ya sea un `.bat`, un script en `python`, o el `.spec` de PyInstaller) debe estar limpio y documentado para futuras compilaciones.

## 3. Estado Actual y Problemas Detectados
Al revisar el repositorio, se detectaron los siguientes artefactos de compilación:
- `compilar_exe.bat`: Intenta extraer rutas dinámicas de los entornos (`CONDA_BIN`, `FACE_MODELS`, `TORCH_LIB`) e invocar PyInstaller usando un flag `--onedir`. Sin embargo, asume que el usuario tiene un entorno `miniconda3` configurado y expuesto de una manera específica.
- `gui_app.spec`: Es el archivo de configuración de PyInstaller. Actualmente, **contiene rutas absolutas completamente hardcodeadas** (por ejemplo, `C:\Users\PC\miniconda3\Lib\site-packages\...`). Esto hará que la compilación falle estrepitosamente en cualquier máquina que no sea la original del desarrollador.
- **Detección de Cámara en `gui_app.py`**: El código intenta detectar cámaras reales versus virtuales midiendo la desviación estándar.
- **Conflicto MKL/OpenMP**: Ya existe una mitigación parcial en `gui_app.py` (`os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'` e importando `torch` antes de `cv2`), lo cual debe ser preservado en la ejecución empaquetada.

## 4. Instrucciones Técnicas y Plan de Implementación para Antigravity

**Estimado Agente Antigravity**, por favor sigue estos pasos para entregar el ejecutable funcional al usuario:

### Paso 1: Configurar el Entorno de Compilación Limpio
1. Analiza las dependencias en `requirements.txt`.
2. Instala todas las dependencias incluyendo `pyinstaller` en el entorno activo, asegurándote de que `torch`, `torchvision`, `ultralytics`, `supervision`, y `face_recognition` funcionen correctamente antes de intentar compilar.
   - *Nota:* Para `face_recognition` en Windows se necesita un compilador C++ (build tools) o bien usar binarios precompilados de `dlib`. Si tienes problemas instalando `dlib` o `face_recognition`, intenta con una versión precompilada (`pip install dlib-bin` si está disponible, o configura `cmake` correctamente).

### Paso 2: Reescribir el Script de Compilación / Archivo `.spec`
1. Elimina o sobrescribe el archivo `gui_app.spec` actual. Es preferible que el script de compilación genere el `.spec` dinámicamente o que tú, Antigravity, crees un script de Python (ej. `build_exe.py`) que localice dinámicamente las rutas necesarias (modelos de `face_recognition`, dlls de `torch`/`numpy` como `libiomp5md.dll` y `mkl_*.dll`) antes de llamar a PyInstaller de manera programática o por terminal.
2. **Script de Construcción Recomendado (`build.py` o corrección en `.bat`):**
   - Usa `site.getsitepackages()` o el módulo `os`/`sys` para encontrar las rutas dinámicamente en lugar de `C:\Users\...`.
   - Asegúrate de copiar las carpetas necesarias:
     - `data/`
     - `models/`
     - `config/`
     - `src/`
     - `yolov8n.pt`
   - Agrega las inclusiones de módulos ocultos: `--hidden-import ultralytics --hidden-import supervision --hidden-import config.config`.

### Paso 3: Compilar la Aplicación
1. Ejecuta PyInstaller apuntando a `src/gui_app.py`.
2. Es muy recomendable usar el modo `--onedir` (carpeta), ya que es más rápido de ejecutar y fácil de depurar (puedes ver si los archivos copiados están allí), además de que el modo `--onefile` extrae todos los recursos a Temp en cada ejecución, ralentizando el inicio de modelos pesados de IA.
3. Asegúrate de compilar con soporte para consola (`--console` en vez de `--windowed`) en la primera etapa del MVP, ya que los logs de YOLO y los prints de la terminal son críticos para que el usuario diagnostique problemas de detección de cámaras o inicialización.

### Paso 4: Validación del MVP
1. Una vez finalizada la compilación, el artefacto se generará en `dist/gui_app`.
2. Verifica que el ejecutable `gui_app.exe` exista.
3. Verifica que la carpeta contenga la estructura correcta (la carpeta interna `data/`, los modelos de rostros, etc.).
4. Ejecuta el archivo resultante (`dist/gui_app/gui_app.exe`) (si el entorno te permite ejecutar aplicaciones de Windows o si puedes confirmarlo de manera manual) para asegurar que la interfaz `Tkinter` arranca y la importación pesada de `torch` y `ultralytics` no crashea de inmediato.

### Paso 5: Preparar Entrega para el Usuario
1. Comprime la carpeta generada en `dist/gui_app/` como un archivo `.zip` (ej. `MVP_Oficina_Eficiencia.zip`) para que el usuario pueda descargarlo y probarlo fácilmente en su entorno Windows, o bien, indica claramente los comandos que el usuario debe correr localmente en su máquina Windows para invocar tu nuevo script de compilación saneado. (Si el usuario prefiere compilar en su máquina, el script debe ser infalible y a prueba de tontos).

## 5. Criterios de Aceptación (DoD - Definition of Done)
- [ ] Se ha eliminado el hardcode de `C:\Users\...` del archivo de compilación.
- [ ] El proceso de compilación descubre las librerías DLL dinámicamente sin fallar por rutas inexistentes.
- [ ] Todos los activos necesarios (`.pt`, carpetas `data`, `models`) están siendo empaquetados correctamente con `add-data`.
- [ ] La compilación se completa sin errores utilizando PyInstaller.
- [ ] Se entrega al usuario un `.zip` del ejecutable o un script de un-clic (`compilar_nuevo.bat` o `build.py`) que garantiza el éxito en su propia computadora.
