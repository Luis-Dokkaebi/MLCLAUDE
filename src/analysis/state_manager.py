# src/analysis/state_manager.py

import time
import numpy as np
from datetime import datetime

class StateManager:
    """
    Administra y determina los estados complejos de cada empleado basándose en 
    ventanas de tiempo, presencia, movimiento y objetos detectados.
    """
    def __init__(self, db_manager, history_size=30, movement_threshold=5.0, lunch_timeout=1800):
        self.db_manager = db_manager
        
        # history_size: Cantidad de frames o lecturas a guardar para calcular la std.
        self.history_size = history_size
        self.movement_threshold = movement_threshold
        
        # lunch_timeout: Segundos antes de considerar que salió a comer (30 mins = 1800 seg)
        self.lunch_timeout = lunch_timeout
        self.out_of_bounds_timeout = 10 # Segundos rápidos para "Tiempo fuera" normal

        # Estructura principal en memoria
        # employee_name: {
        #     "positions": [(x, y), (x, y)...],
        #     "last_seen": timestamp,
        #     "current_state": str,
        #     "last_zone": str
        # }
        self.employees = {}

    def get_color_for_state(self, state):
        colors = {
            "Activo": (0, 255, 0),         # Verde
            "Inactivo": (0, 255, 255),       # Amarillo
            "En traslado": (255, 165, 0),    # Naranja
            "En el celular": (0, 0, 255),    # Rojo
            "Tiempo fuera": (128, 128, 128), # Gris
            "Hora de comer": (255, 0, 255),  # Magenta
            "Desconocido": (255, 255, 255)   # Blanco
        }
        return colors.get(state, (255, 255, 255))

    def process_frame(self, current_time: float, track_data: list, phones_data: list):
        """
        track_data: lista de dicts [{'name': 'Juan', 'x': cx, 'y': cy, 'bbox': (x1, y1, x2, y2), 'zone': 'Zona_Juan', 'inside': bool}]
        phones_data: lista de bboxes de celulares [(x1,y1,x2,y2), ...]
        """
        seen_this_frame = set()

        # Update existents or add new
        for data in track_data:
            name = data['name']
            
            # Si el nombre es Unknown, no procedemos con estados complejos porque 
            # no sabríamos a quién asignarlo al final del día.
            if name == "Unknown":
                continue
                
            seen_this_frame.add(name)

            if name not in self.employees:
                self.employees[name] = {
                    "positions": [],
                    "last_seen": current_time,
                    "current_state": "Inicializando",
                    "last_zone": data['zone'],
                    "on_lunch": False
                }
                self.db_manager.insert_state(name, "Inicializando")
            
            emp = self.employees[name]
            
            # Registrar asistencia si es visto (esto se maneja en el Manager para actualizar su Hora de Salida constantemente)
            self.db_manager.update_attendance(name)

            # Update history
            emp["positions"].append((data['x'], data['y']))
            if len(emp["positions"]) > self.history_size:
                emp["positions"].pop(0)
                
            emp["last_seen"] = current_time
            emp["last_zone"] = data['zone']
            
            # Calculate new state
            new_state = self._determine_state(emp, data, phones_data)
            
            # Transition logic
            if new_state != emp["current_state"]:
                if emp["on_lunch"] and new_state != "Hora de comer" and new_state != "Tiempo fuera":
                    self.db_manager.insert_state(name, "Regreso a comer")
                    emp["on_lunch"] = False

                self.db_manager.insert_state(name, new_state)
                emp["current_state"] = new_state

        # Check for people not seen in this frame
        self._check_timeouts(current_time, seen_this_frame)

    def _determine_state(self, emp, data, phones_data):
        # 1. Check for Cell Phone usage (highest priority active state)
        person_bbox = data['bbox']
        has_phone = False
        for phone_bbox in phones_data:
            if self._bboxes_intersect(person_bbox, phone_bbox):
                has_phone = True
                break
                
        if has_phone:
            return "En el celular"

        # 2. Check En Traslado (Fuera de zona asignada)
        if not data['inside']:
            return "En traslado"

        # 3. Check Activo vs Inactivo
        positions = emp["positions"]
        if len(positions) < self.history_size // 2:
            return "Activo" # Default to active while gathering data

        xs = [p[0] for p in positions]
        ys = [p[1] for p in positions]
        std_x = np.std(xs)
        std_y = np.std(ys)

        total_std = std_x + std_y
        
        if total_std > self.movement_threshold:
            return "Activo"
        else:
            return "Inactivo"

    def _check_timeouts(self, current_time, seen_this_frame):
        for name, emp in self.employees.items():
            if name not in seen_this_frame:
                time_away = current_time - emp["last_seen"]
                
                new_state = emp["current_state"]
                
                if time_away > self.lunch_timeout:
                    new_state = "Hora de comer"
                    if not emp["on_lunch"]:
                        emp["on_lunch"] = True
                        self.db_manager.insert_state(name, "Salida a comer")
                elif time_away > self.out_of_bounds_timeout and emp["current_state"] != "Hora de comer":
                    new_state = "Tiempo fuera"

                if new_state != emp["current_state"]:
                    self.db_manager.insert_state(name, new_state)
                    emp["current_state"] = new_state

    def _bboxes_intersect(self, bbox1, bbox2):
        # Format: (x1, y1, x2, y2)
        x1_1, y1_1, x2_1, y2_1 = bbox1
        x1_2, y1_2, x2_2, y2_2 = bbox2
        
        # overlapping check
        if x2_1 < x1_2 or x2_2 < x1_1:
            return False
        if y2_1 < y1_2 or y2_2 < y1_1:
            return False
            
        return True

    def get_state(self, name):
        if name in self.employees:
            return self.employees[name]["current_state"]
        return "Desconocido"
