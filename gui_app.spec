# -*- mode: python ; coding: utf-8 -*-
# ===================================================================
# gui_app.spec — PyInstaller Spec para Oficina Eficiencia B2B
#
# TASK-4.4: Apunta al codigo ofuscado por PyArmor en dist/obfuscated/
# TASK-4.5 (SPEC 1.9): Usa sys._MEIPASS para yolov8n.pt
#
# ANTI-VIBE HACKING: No cambiar las rutas de entrada sin actualizar
# compilar_exe.bat. El orden es: PyArmor gen -> PyInstaller spec.
# ===================================================================

import os
import sys
from PyInstaller.utils.hooks import collect_all, copy_metadata, collect_data_files

# --- Prevenir crash OpenMP (Riesgo 1 — 2_PLANNING.md) ---
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

# === RECURSOS ESTATICOS (datas) ===
# El modelo YOLO y el archivo VERSION se empaquetan en la raiz del bundle.
# En runtime se acceden via sys._MEIPASS (config/path_utils.py -> get_resource_path)
datas = [
    ('yolov8n.pt', '.'),          # Modelo AI  -> sys._MEIPASS/yolov8n.pt
    ('VERSION', '.'),              # Version B2B -> sys._MEIPASS/VERSION
]

binaries = []

# === HIDDEN IMPORTS (TASK-4.4.5) ===
# Librerias que PyArmor enmascara del analizador estatico de PyInstaller.
# Sin estos, el .exe arroja "ModuleNotFoundError" en produccion.
hiddenimports = [
    # --- Infraestructura del proyecto (ofuscada) ---
    'config', 'config.config', 'config.path_utils',
    'src', 'src.gui', 'src.gui.dashboard', 'src.gui.views',
    'src.security', 'src.security.drm',
    'src.tracking', 'src.tracking.camera_worker', 'src.tracking.person_tracker',
    'src.analysis', 'src.analysis.report_generator', 'src.analysis.state_manager',
    'src.recognition', 'src.recognition.face_recognizer',
    'src.storage', 'src.storage.database_manager',
    'src.detection', 'src.detection.person_detector', 'src.detection.people_detector',
    'src.zones', 'src.zones.zone_checker',
    'src.acquisition', 'src.acquisition.video_stream', 'src.acquisition.camera_enumerator',

    # --- Dependencias de Vision (C/C++ bindings) ---
    'ultralytics', 'ultralytics.engine', 'ultralytics.engine.model',
    'ultralytics.engine.results', 'ultralytics.models',
    'supervision',
    'cv2', 'numpy', 'PIL',

    # --- Dependencias de DRM/SecOps (Sprint 4) ---
    'wmi', 'win32com', 'win32com.client', 'pywintypes', 'pythoncom',
    'Crypto', 'Crypto.PublicKey', 'Crypto.PublicKey.RSA',
    'Crypto.Signature', 'Crypto.Signature.pkcs1_15',
    'Crypto.Hash', 'Crypto.Hash.SHA256',

    # --- Dependencias de UI/Reportes ---
    'customtkinter', 'tkinter', 'tkinter.filedialog',
    'pandas', 'openpyxl', 'matplotlib', 'matplotlib.pyplot', 'seaborn', 'scipy',
    'shapely', 'shapely.geometry',
    'tkcalendar', 'babel.numbers',

    # --- Dependencias de Reconocimiento Facial ---
    'face_recognition', 'face_recognition_models', 'dlib',

    # --- Runtime de Python ---
    'sqlite3', 'json', 'hashlib', 'platform', 'uuid',
    'threading', 'queue', 'time', 'os', 'sys', 'pickle',
]

# === COLLECT AUTOMATICO de ultralytics (modelos, configs, assets) ===
datas += copy_metadata('ultralytics')
tmp_ret = collect_all('ultralytics')
datas += tmp_ret[0]
binaries += tmp_ret[1]
hiddenimports += tmp_ret[2]

# === COLLECT de supervision ===
try:
    tmp_ret = collect_all('supervision')
    datas += tmp_ret[0]
    binaries += tmp_ret[1]
    hiddenimports += tmp_ret[2]
except Exception:
    pass

# === COLLECT de shapely ===
try:
    tmp_ret = collect_all('shapely')
    datas += tmp_ret[0]
    binaries += tmp_ret[1]
    hiddenimports += tmp_ret[2]
except Exception:
    pass

# === COLLECT de tkcalendar ===
try:
    tmp_ret = collect_all('tkcalendar')
    datas += tmp_ret[0]
    binaries += tmp_ret[1]
    hiddenimports += tmp_ret[2]
except Exception:
    pass

# === COLLECT de customtkinter (themes, assets JSON) ===
try:
    tmp_ctk = collect_all('customtkinter')
    datas += tmp_ctk[0]
    binaries += tmp_ctk[1]
    hiddenimports += tmp_ctk[2]
except Exception:
    pass

# === COLLECT de face_recognition y face_recognition_models ===
try:
    tmp_ret = collect_all('face_recognition')
    datas += tmp_ret[0]
    binaries += tmp_ret[1]
    hiddenimports += tmp_ret[2]
except Exception:
    pass

try:
    tmp_ret = collect_all('face_recognition_models')
    datas += tmp_ret[0]
    binaries += tmp_ret[1]
    hiddenimports += tmp_ret[2]
except Exception:
    pass

# === COLLECT de brotlicffi ===
try:
    tmp_ret = collect_all('brotlicffi')
    datas += tmp_ret[0]
    binaries += tmp_ret[1]
    hiddenimports += tmp_ret[2]
except Exception:
    pass

# === COLLECT de pyarrow ===
try:
    tmp_ret = collect_all('pyarrow')
    datas += tmp_ret[0]
    binaries += tmp_ret[1]
    hiddenimports += tmp_ret[2]
except Exception:
    pass

# === PyArmor Runtime: Incluir las librerias .pyd generadas ===
pyarmor_runtime_dir = os.path.join('dist', 'obfuscated', 'pyarmor_runtime_000000')
if os.path.exists(pyarmor_runtime_dir):
    # Incluir todo el directorio del runtime de PyArmor como data
    datas += [(pyarmor_runtime_dir, 'pyarmor_runtime_000000')]

# ===================================================================
# ANALYSIS: Punto de entrada = codigo OFUSCADO por PyArmor
# ===================================================================
a = Analysis(
    ['dist\\obfuscated\\src\\main_ui.py'],       # Entry point ofuscado
    pathex=[
        'dist\\obfuscated',                       # Raiz de imports ofuscados
        '.',                                       # Raiz del proyecto (para recursos)
    ],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

# ===================================================================
# EXE: Configuracion del binario final
# ===================================================================
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='OficinaEficiencia_VMS',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,                          # Compresion (puede dar falsos positivos AV)
    console=True,                      # True para debug B2B, False para produccion
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# ===================================================================
# COLLECT: Empaquetado final en carpeta dist/OficinaEficiencia_VMS/
# ===================================================================
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='OficinaEficiencia_VMS',
)
