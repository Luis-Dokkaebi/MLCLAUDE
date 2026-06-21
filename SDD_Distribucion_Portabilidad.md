# Spec-Driven Development (SDD) - Distribución y Portabilidad del Ejecutable

## Contexto y Objetivo
El objetivo de este SDD es proporcionar a **Antigravity** (u otros agentes/desarrolladores) las instrucciones técnicas precisas para solucionar los problemas de portabilidad del proyecto. Actualmente, la aplicación no funciona al mover el ejecutable a otra computadora debido a dependencias externas (DLLs, modelos de IA), rutas absolutas *hardcodeadas* (Miniconda) y una gestión estática de las rutas de almacenamiento (guardando la BD y recursos en la misma carpeta del `.exe`).

Se busca lograr que el cliente pueda instalar y usar el programa "con un solo archivo" en cualquier PC Windows, sin perder datos, y sin necesitar configurar librerías ni variables de entorno. **El sistema debe ser 100% autónomo (Standalone); es decir, debe funcionar en el equipo del cliente sin importar si este tiene instalado Python, Conda, o cualquier otra dependencia de software (como paquetes pip de IA), ya que todas las dependencias binarias, intérpretes y librerías deben quedar pre-empaquetadas dentro de la compilación o el instalador.**

---

## 1. Análisis de Problemas Actuales

1. **Persistencia y Escritura de Datos:**
   El código usa la carpeta relativa `data/` (por ejemplo, `data/db/local_tracking.db` o `data/faces/`) para almacenar información dinámica. Si el programa se empaqueta o se instala en `C:\Archivos de Programa`, el sistema operativo denegará permisos de escritura, o en caso de un ejecutable portable temporal (`--onefile`), los datos se borrarán al cerrar la aplicación.
2. **Rutas Absolutas en el proceso de Build:**
   El archivo `gui_app.spec` tiene directorios atados a una sola computadora (ej. `C:\Users\PC\miniconda3\...`). Esto imposibilita compilar el código en otro entorno (CI/CD, otra PC).
3. **Modelos de Inteligencia Artificial:**
   Los pesos (YOLO, dlib/face_recognition) deben estar correctamente anclados en memoria para poder usarse de manera portable.
4. **Modo `--onefile` vs Instalador Nativo:**
   PyInstaller `--onefile` encapsula todo en un exe, pero al ejecutarlo descomprime gigabytes de librerías (Torch, OpenCV, CUDA) en una carpeta temporal cada vez que arranca, lo cual ralentiza severamente el inicio del programa.

---

## 2. Especificaciones de Implementación (Tareas para el Agente)

### Fase 1: Refactorización Dinámica de Rutas (Path Management)

**Objetivo:** Separar las rutas de recursos de solo lectura (modelos) de las rutas de datos del usuario (lectura y escritura).

*   **Crear módulo/función de resolución de rutas (`utils/paths.py` o dentro de `config/config.py`):**
    *   **Recursos Estáticos (`_MEIPASS`):** Implementar lógica para detectar si la aplicación está congelada (`getattr(sys, 'frozen', False)`). Si es así, resolver la ruta base hacia `sys._MEIPASS` (donde PyInstaller mapea el entorno). Si no está congelado, apuntar al directorio actual de desarrollo.
    *   **Datos de Usuario (`%APPDATA%`):** Reemplazar todas las escrituras en la ruta relativa `data/` por el directorio de itinerancia del usuario: `os.path.join(os.environ.get('APPDATA', ''), 'OficinaEficiencia')`.
*   **Modificaciones de Código:**
    *   `config/config.py`: `LOCAL_DB_PATH` y `SNAPSHOTS_DIR` deben apuntar a la nueva carpeta en `%APPDATA%`.
    *   `src/main.py` y `src/gui_app.py`: Actualizar para usar estas rutas al crear carpetas (`os.makedirs(..., exist_ok=True)`), cargar/guardar las zonas en `zonas.json`, y al almacenar los rostros.

### Fase 2: Normalización del Archivo `.spec` y Compilación

**Objetivo:** Eliminar rutas *hardcodeadas* de Conda o del usuario específico.

*   **Limpiar `gui_app.spec`:**
    *   Antigravity debe reemplazar el `.spec` por uno dinámico o actualizar el script `compilar_exe.bat` para que no dependa de un `.spec` estático pre-generado. Las rutas para encontrar `mkl_*.dll` y `libiomp5md.dll` ya están manejadas de forma dinámica en el `.bat` con comandos de Python (`python -c ...`).
    *   Asegurar que `--add-data` referencie las rutas relativas o variables del sistema que se procesen al momento del *build*, no *paths* absolutos a carpetas del usuario.

### Fase 3: Estrategia del "Ejecutable Único" Comercial

**Objetivo:** Cumplir con la expectativa comercial de entregar "un solo archivo" al cliente sin el impacto de rendimiento del modo `--onefile`.

*   **Usar `--onedir` + Inno Setup:**
    *   En lugar de compilar PyInstaller como `--onefile`, continuar usando `--onedir` para generar la carpeta `dist/gui_app`.
    *   **Tarea para Antigravity:** Crear un script de configuración de Inno Setup (`setup.iss`) que comprima toda la carpeta `dist/gui_app` en un archivo `Instalador_OficinaEficiencia_v1.exe`.
    *   El instalador debe:
        *   Copiar la carpeta al directorio `Program Files` del cliente.
        *   Crear accesos directos en el escritorio y Menú de Inicio apuntando al ejecutable `gui_app.exe`.
        *   (Obligatorio) Incluir e instalar automáticamente las librerías *Microsoft Visual C++ Redistributable* si el sistema no las tiene, ya que OpenCV y Torch dependen de ellas para correr sin Conda.
        *   (Obligatorio) Validar que el entorno empaquetado sea **Standalone**: Todas las dependencias (Python en sí mismo, Torch, NumPy, modelos de YOLO, dlib) deben ser compiladas dentro del output de PyInstaller. El cliente no debe tener que ejecutar ningún comando `pip` o instalar Python por su cuenta.

### Fase 4: Manejo Robusto de Hardware en Entornos Nuevos

**Objetivo:** Prevenir cierres abruptos cuando el programa se ejecuta en una PC con otra configuración de hardware (ej. sin cámara web).

*   **Fallback Avanzado de Cámara:**
    *   Revisar `_init_camera` en `gui_app.py` y la lógica de `start_video_stream` en `main.py`.
    *   Añadir manejo de excepciones en caso de que ninguna cámara detectada sea capaz de devolver `cap.read()`.
    *   Si hay fallos de drivers o de dispositivo, arrojar un `messagebox.showerror()` explícito indicando "Cámara no detectada o en uso por otra aplicación" antes de cerrar.

---

## 3. Criterios de Aceptación

1. El código no contiene ninguna ruta de archivo absoluta, ni siquiera en configuraciones de build.
2. Al ejecutar el instalador final, se crea la estructura de datos en `%APPDATA%\OficinaEficiencia` de forma transparente.
3. El programa es capaz de guardar rostros nuevos y conservar su base de datos local entre reinicios sin conflictos de permisos.
4. El ejecutable carga eficientemente (gracias al modelo `--onedir` embebido en el instalador) y no falla si falta la cámara, mostrando un aviso visual al usuario en su lugar.