import os
import shutil

src_data = r"C:\Users\PC\Desktop\ML-main\data"
dest_data = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), 'MonitoreoAsistencia', 'data')

if os.path.exists(src_data):
    print(f"Migrando datos desde {src_data} a {dest_data}...")
    try:
        shutil.copytree(src_data, dest_data, dirs_exist_ok=True)
        print("¡Migración exitosa!")
    except Exception as e:
        print(f"Error migrando datos: {e}")
else:
    print(f"Carpeta de origen {src_data} no encontrada, no hay nada que migrar.")
