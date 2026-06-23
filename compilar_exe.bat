@echo off
echo =========================================================
echo  OFICINA EFICIENCIA B2B - BUILD PIPELINE SECOPS
echo  PyArmor 8 (Ofuscacion) + PyInstaller (Empaquetado)
echo =========================================================
echo.

REM ---- PASO 0: Configuracion de entorno ----
set VENV=.\venv\Scripts

REM Prevenir crash OpenMP (Riesgo 1 de 2_PLANNING.md)
set KMP_DUPLICATE_LIB_OK=TRUE

echo Leyendo version desde archivo VERSION...
set /p APP_VERSION=<VERSION

echo.
echo [1/3] Ofuscando codigo fuente con PyArmor (TASK-4.4)...
echo       (Limpia build/ y dist/obfuscated/ y ofusca src/ + config/)
%VENV%\python.exe obfuscate.py
if errorlevel 1 (
    echo ERROR FATAL: La ofuscacion PyArmor fallo. Build abortado.
    pause
    exit /b 1
)

echo.
echo [2/3] Empaquetando ejecutable OFUSCADO con PyInstaller (gui_app.spec)...
REM gui_app.spec apunta a dist\obfuscated\src\main_ui.py (entry ofuscado).
%VENV%\pyinstaller gui_app.spec --clean -y
if errorlevel 1 (
    echo ERROR FATAL: PyInstaller fallo.
    pause
    exit /b 1
)

echo.
echo [3/3] Generando Instalador para version %APP_VERSION% (Inno Setup)...
"c:\Program Files (x86)\Inno Setup 6\ISCC.exe" /DMyAppVersion=%APP_VERSION% setup_oficina.iss

echo.
echo =========================================================
echo  Proceso Finalizado (Build B2B Ofuscado).
echo  Binario: dist\OficinaEficiencia_VMS\
echo  Instalador: installer_output\setup_oficina_eficiencia_v%APP_VERSION%.exe
echo =========================================================
pause
