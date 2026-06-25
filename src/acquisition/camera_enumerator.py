"""
Utilidad de enumeración de cámaras para el VMS B2B.
Escanea dispositivos de video disponibles en el sistema y reporta resolución y backend.
"""
import cv2
import threading


def enumerate_cameras(max_index: int = 10, timeout: float = 3.0) -> list[dict]:
    """
    Escanea los índices de cámara de 0 a max_index y retorna una lista de diccionarios
    con info de cada cámara detectada.
    
    Retorna:
        [{"index": 0, "name": "Cámara 0", "width": 640, "height": 480, "backend": "MSMF"}, ...]
    """
    cameras = []
    
    for idx in range(max_index):
        try:
            cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
            if cap.isOpened():
                w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                backend = cap.getBackendName()
                
                # Leer un frame para verificar que realmente funciona
                try:
                    ret, frame = cap.read()
                except (ValueError, Exception):
                    ret, frame = False, None
                cap.release()
                
                if ret and frame is not None and frame.size > 0:
                    cameras.append({
                        "index": idx,
                        "name": f"Cámara {idx}",
                        "width": w,
                        "height": h,
                        "backend": backend,
                        "label": f"Cámara {idx} ({w}x{h}, {backend})"
                    })
            else:
                cap.release()
        except Exception:
            pass
    
    # También probar con MSMF si DSHOW no encontró nada
    if not cameras:
        for idx in range(max_index):
            try:
                cap = cv2.VideoCapture(idx)
                if cap.isOpened():
                    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    backend = cap.getBackendName()
                    
                    try:
                        ret, frame = cap.read()
                    except (ValueError, Exception):
                        ret, frame = False, None
                    cap.release()
                    
                    if ret and frame is not None and frame.size > 0:
                        cameras.append({
                            "index": idx,
                            "name": f"Cámara {idx}",
                            "width": w,
                            "height": h,
                            "backend": backend,
                            "label": f"Cámara {idx} ({w}x{h}, {backend})"
                        })
                else:
                    cap.release()
            except Exception:
                pass
    
    return cameras


def enumerate_cameras_async(callback, max_index: int = 10):
    """
    Versión asíncrona que ejecuta el escaneo en un hilo secundario
    y llama a `callback(cameras_list)` cuando termina.
    """
    def _scan():
        result = enumerate_cameras(max_index)
        callback(result)
    
    t = threading.Thread(target=_scan, daemon=True)
    t.start()
    return t
