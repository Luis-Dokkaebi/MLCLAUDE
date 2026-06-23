import cv2
import queue
import threading
import time
from typing import Tuple, Any
import numpy as np
from src.recognition.face_recognizer import FaceRecognizer

class CameraWorker(threading.Thread):
    def __init__(self, camera_id: int | str, frame_queue: queue.Queue, model: Any, fps_limit: int = 15):
        super().__init__(daemon=True) # El hilo muere al cerrar la app
        self.camera_id = camera_id
        self.frame_queue = frame_queue
        self.model = model
        self.fps_limit = fps_limit
        self.running = False
        self._delay = 1.0 / self.fps_limit
        
        # FIX: Usar get_faces_dir() para garantizar la MISMA ruta que usa la UI de registro
        from config.config import get_faces_dir
        faces_dir = get_faces_dir()

        self.face_rec = FaceRecognizer(faces_dir=faces_dir)
        self.frame_counter = 0
        self.last_name = "Unknown"
        self.last_name_time = 0

        # --- TASK-5.2: Verificacion de integridad del modelo AI (Anti-Tamper) ---
        # Si el yolov8n.pt en disco fue reemplazado por un modelo falso/backdoor,
        # el hash SHA-256 no coincide y el tracking se deshabilita (SPEC 5.2 DoD).
        self.model_verified = True
        try:
            from config.config import MODEL_PATH
            from src.models.model_verifier import verify_model
            self.model_verified = verify_model(MODEL_PATH)
            if not self.model_verified:
                print(f"[VMS][SECURITY] Modelo AI manipulado en {MODEL_PATH}. "
                      f"Inferencia DESHABILITADA para cámara {self.camera_id}.")
        except FileNotFoundError as exc:
            # Modelo ausente: no podemos verificar -> deshabilitar por seguridad
            self.model_verified = False
            print(f"[VMS][SECURITY] No se pudo verificar el modelo AI: {exc}")
        print(f"[CameraWorker] FaceRecognizer cargado. faces_dir={faces_dir}, "
              f"encodings={len(self.face_rec.known_face_names)} rostro(s): {self.face_rec.known_face_names}")

    def run(self):
        # TASK-5.2 DoD: si el modelo fue manipulado, abortar el tracking de inmediato.
        if not self.model_verified:
            print(f"[VMS][SECURITY] Cámara {self.camera_id} no inicia: integridad del modelo AI inválida.")
            return
        self.running = True
        if isinstance(self.camera_id, int):
            cap = cv2.VideoCapture(self.camera_id, cv2.CAP_DSHOW)
            if not cap.isOpened():
                cap = cv2.VideoCapture(self.camera_id)
        else:
            cap = cv2.VideoCapture(self.camera_id)
        
        # Fallback de autodescubrimiento B2B
        if not cap.isOpened():
            print(f"[VMS] Cámara {self.camera_id} falló. Intentando autodescubrimiento...")
            for idx in [0, 1, 2]:
                cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
                if not cap.isOpened():
                    cap = cv2.VideoCapture(idx)
                if cap.isOpened():
                    print(f"[VMS] Cámara {idx} de respaldo conectada exitosamente.")
                    self.camera_id = idx
                    break
                    
        # Optimizacion OpenCV B2B: Forzar resolucion (opcional)
        # cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        # cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

        while self.running:
            start_time = time.time()
            ret, frame = cap.read()
            
            if not ret or frame is None or frame.size == 0:
                # Log de reconexion en entorno Enterprise (ej. RTSP perdido)
                time.sleep(2.0)
                if isinstance(self.camera_id, int):
                    cap = cv2.VideoCapture(self.camera_id, cv2.CAP_DSHOW)
                    if not cap.isOpened():
                        cap = cv2.VideoCapture(self.camera_id)
                else:
                    cap = cv2.VideoCapture(self.camera_id)
                continue

            # Inferencia YOLOv8
            results = self.model(frame, verbose=False)
            annotated_frame = results[0].plot() # numpy array (BGR)
            
            # --- FACE RECOGNITION (Optimizado para Velocidad y Precision) ---
            self.frame_counter += 1
            
            # --- HOT-RELOAD: Detectar nuevos empleados registrados cada ~60 frames (~4s) ---
            if self.frame_counter % 60 == 0:
                self.face_rec.check_reload()
            
            has_person = False
            for r in results:
                for box in r.boxes:
                    if int(box.cls[0]) == 0 and float(box.conf[0]) > 0.4:
                        has_person = True
                        break
                        
            if has_person:
                # Detectar solo cada 15 frames para mantener el video fluido
                if self.frame_counter % 15 == 0:
                    # Buscamos en todo el frame (sin recortes YOLO) para no confundir a dlib
                    self.last_name = self.face_rec.recognize_face(frame, bbox=None)
                    if self.last_name != "Unknown":
                        self.last_name_time = time.time()
                
                # Dejar el nombre visible en la pantalla por un momento
                if self.last_name != "Unknown" and (time.time() - self.last_name_time) < 3.0:
                    label = f"BIOMETRIA VMS: {self.last_name}"
                    cv2.rectangle(annotated_frame, (10, 10), (500, 60), (0, 0, 0), -1)
                    cv2.putText(annotated_frame, label, (20, 45), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 3)
            else:
                self.last_name = "Unknown"
            
            # --- DROP FRAME PROTOCOL (Anti-Memory Leak) ---
            try:
                # Intenta encolar sin bloquear. Si esta llena (UI retardada), entra al except
                self.frame_queue.put_nowait((self.camera_id, annotated_frame))
            except queue.Full:
                # Se descarta este frame para que la memoria no colapse
                pass 
                
            # Limitar FPS para ahorrar CPU (Artificial Throttle)
            elapsed_time = time.time() - start_time
            time_to_wait = self._delay - elapsed_time
            if time_to_wait > 0:
                time.sleep(time_to_wait)
                
        cap.release()

    def stop(self):
        self.running = False
