# src/main.py

import cv2
import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
import sys
from datetime import datetime

# Add the project root directory to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from config import config
except ImportError:
    # Fallback if config module is not found directly
    sys.path.append(os.getcwd())
    from config import config

from detection.person_detector import PersonDetector
from tracking.person_tracker import PersonTracker
from zones.zone_checker import ZoneChecker
from storage.database_manager import DatabaseManager
from recognition.face_recognizer import FaceRecognizer
from analysis.state_manager import StateManager
import time

def get_bbox_center(xyxy):
    x1, y1, x2, y2 = xyxy
    center_x = (x1 + x2) / 2
    center_y = (y1 + y2) / 2
    return center_x, center_y

def start_video_stream():
    # Selección de fuente de video
    if config.MODE == 'local':
        video_source = config.LOCAL_CAMERA_INDEX
    else:
        video_source = config.REMOTE_CAMERA_URL

    # Use the camera index selected by the user in the GUI (passed via env var), otherwise fallback
    selected_cam = os.environ.get('SELECTED_CAMERA_INDEX')
    if selected_cam is not None:
        sources_to_try = [int(selected_cam)]
    else:
        sources_to_try = [video_source, 0, 1, 2, 3]
    
    # Remove duplicates while preserving order
    seen = set()
    unique_sources = []
    for s in sources_to_try:
        if s not in seen:
            seen.add(s)
            unique_sources.append(s)
    sources_to_try = unique_sources
    
    cap = None
    
    for src in sources_to_try:
        temp_cap = cv2.VideoCapture(src)
        if temp_cap.isOpened():
            ret, frame = temp_cap.read()
            if ret:
                print(f"✅ Cámara iniciada con éxito en el índice/ruta: {src}")
                cap = temp_cap
                break
            else:
                print(f"⚠️ Cámara en origen {src} no devolvió frame. Omitiendo...")
        temp_cap.release()

    if not cap or not cap.isOpened():
        print("❌ Error: No se pudo detectar ninguna cámara (ni local ni externa). Revisar conexiones.")
        return

    # Ensure all data directories exist before loading
    zonas_file = getattr(config, 'ZONAS_FILE', os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), 'OficinaEficiencia', 'data', 'zonas', 'zonas.json'))
    os.makedirs(os.path.dirname(zonas_file), exist_ok=True)
    if not os.path.exists(zonas_file):
        with open(zonas_file, 'w') as f:
            f.write('{}')

    # Inicializamos los módulos
    model_path = getattr(config, 'MODEL_PATH', 'yolov8n.pt')
    detector = PersonDetector(model_path=model_path, confidence_threshold=config.CONFIDENCE_THRESHOLD)
    tracker = PersonTracker()
    zone_checker = ZoneChecker(zones_path=zonas_file)
    db_manager = DatabaseManager(db_path=config.LOCAL_DB_PATH)
    
    # Initialize face recognizer
    face_recognizer = FaceRecognizer()
    
    # Initialize state manager
    state_manager = StateManager(db_manager)

    # Track state: {track_id: {zone_name: was_inside}}
    zone_state = {}
    
    # Track names: {track_id: name}
    track_id_to_name = {}

    # Ensure snapshots dir exists
    snapshots_dir = getattr(config, 'SNAPSHOTS_DIR', os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), 'OficinaEficiencia', 'data', 'snapshots'))
    os.makedirs(snapshots_dir, exist_ok=True)

    print("✅ Sistema iniciado. Presiona 'q' para salir.")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        current_time = time.time()

        # Detección y tracking
        detections = detector.detect(frame)
        
        # Separar personas de celulares
        import numpy as np
        person_detections = detections[detections.class_id == 0]
        phone_detections = detections[detections.class_id == 67]
        
        phones_data = [] # Lista de bboxes
        if len(phone_detections) > 0:
            for xyxy in phone_detections.xyxy:
                phones_data.append(tuple(map(int, xyxy)))

        tracked_detections = tracker.update(person_detections)

        track_data_for_state_manager = []

        # Procesamos cada persona detectada
        if tracked_detections.tracker_id is not None:
            for xyxy, track_id in zip(tracked_detections.xyxy, tracked_detections.tracker_id):
                track_id = int(track_id)
                x1, y1, x2, y2 = map(int, xyxy)
                cx, cy = get_bbox_center(xyxy)

                # --- LÓGICA DE RECONOCIMIENTO CONSTANTE ---
                # Si el ID es nuevo o aún es "Unknown", intentamos reconocerlo
                current_name = track_id_to_name.get(track_id, "Unknown")
                
                # Reconocimiento continuo para corregir falsos "Unknown" (podría hacerse cada X frames)
                if current_name == "Unknown":
                    recognized_name = face_recognizer.recognize_face(frame, bbox=(x1, y1, x2, y2))
                    if recognized_name != "Unknown":
                        track_id_to_name[track_id] = recognized_name
                        print(f"✅ ¡Identificado! ID: {track_id} es {recognized_name}")
                
                display_name = track_id_to_name.get(track_id, "Unknown")
                # ------------------------------------------

                results = zone_checker.check(cx, cy)
                
                # Encontramos en qué zona está (si está en alguna)
                current_zone = "Fuera de zona"
                inside_zone_flag = False
                for z_name, inside in results.items():
                    if inside:
                        current_zone = z_name
                        inside_zone_flag = True
                        break

                # Preparamos datos para StateManager
                track_data_for_state_manager.append({
                    'name': display_name,
                    'x': cx,
                    'y': cy,
                    'bbox': (x1, y1, x2, y2),
                    'zone': current_zone,
                    'inside': inside_zone_flag
                })

                if track_id not in zone_state:
                    zone_state[track_id] = {}

                for zone_name, inside in results.items():
                    inside_zone = int(inside)
                    
                    # Check for entry event (Entrada a zona)
                    was_inside = zone_state[track_id].get(zone_name, False)
                    
                    if inside_zone and not was_inside:
                        # ACABA DE ENTRAR A LA ZONA
                        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                        filename = f"{track_id}_{display_name}_{zone_name}_{timestamp_str}.jpg"
                        filepath = os.path.join(snapshots_dir, filename)

                        try:
                            # Guardamos la evidencia
                            cv2.imwrite(filepath, frame)
                            db_manager.insert_snapshot(track_id, zone_name, filepath, employee_name=display_name)
                            print(f"📸 Foto guardada: {display_name} entró a {zone_name}")
                        except Exception as e:
                            print(f"Error saving snapshot: {e}")

                    # Update state
                    zone_state[track_id][zone_name] = bool(inside_zone)

                    # Registramos posición en la base de datos
                    db_manager.insert_record(
                        track_id=track_id,
                        x=cx,
                        y=cy,
                        zone=zone_name,
                        inside_zone=inside_zone,
                        employee_name=display_name
                    )

                # El dibujo se hará después de calcular el estado general

        # Actualizamos state manager
        state_manager.process_frame(current_time, track_data_for_state_manager, phones_data)

        # Volvemos a iterar para dibujar colores basados en el nuevo estado
        if tracked_detections.tracker_id is not None:
            for xyxy, track_id in zip(tracked_detections.xyxy, tracked_detections.tracker_id):
                track_id = int(track_id)
                x1, y1, x2, y2 = map(int, xyxy)
                display_name = track_id_to_name.get(track_id, "Unknown")
                
                # Obtener estado actual
                current_state = state_manager.get_state(display_name)
                color = state_manager.get_color_for_state(current_state)
                
                # Etiqueta: Nombre - Estado
                label = f"{display_name} - {current_state}"
                
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(frame, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        cv2.imshow("Sistema de Monitoreo Completo", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    start_video_stream()