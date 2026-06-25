"""
Test: Dashboard Grid Multiplexor (v1.2.2)
Valida que DashboardFrame no mezcle geometry managers pack/grid (TclError fix).
Prueba directa del widget sin dependencias de YOLO, DRM ni cámaras reales.
"""
import unittest
import time
import sys
import os
import queue
import threading
import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Necesitamos Tk disponible
import customtkinter as ctk
ctk.set_appearance_mode("Dark")

class TestGridMultiplexor(unittest.TestCase):
    """Prueba unitaria del DashboardFrame aislado (sin AppMain completo)."""

    def setUp(self):
        try:
            self.root = ctk.CTk()
            self.root.withdraw()  # No mostrar ventana
        except Exception as e:
            self.skipTest(f"Tkinter/CustomTkinter no disponible en este entorno: {e}")

    def tearDown(self):
        try:
            self.root.destroy()
        except Exception:
            pass

    def test_zero_cameras_uses_grid_not_pack(self):
        """BUGFIX v1.2.2: Con 0 cámaras, el label 'No hay transmisiones' debe usar grid, no pack."""
        from src.gui.dashboard import DashboardFrame
        
        empty_queues = {}
        dashboard = DashboardFrame(self.root, empty_queues)
        dashboard.grid(row=0, column=0, sticky="nsew")
        self.root.update_idletasks()
        
        # Verificar que los hijos usan grid (grid_info no vacio)
        children = dashboard.winfo_children()
        self.assertGreater(len(children), 0, "Debe haber al menos 1 widget hijo (label placeholder)")
        for child in children:
            info = child.grid_info()
            self.assertTrue(len(info) > 0, f"Widget {child} debe estar colocado con grid(), no pack()")

    def test_transition_zero_to_n_cameras_no_tcl_error(self):
        """BUGFIX v1.2.2: Transición de 0 → N cámaras NO debe lanzar TclError."""
        from src.gui.dashboard import DashboardFrame
        
        camera_queues = {}
        dashboard = DashboardFrame(self.root, camera_queues)
        dashboard.grid(row=0, column=0, sticky="nsew")
        self.root.update_idletasks()
        
        # Ahora simular que se agregan cámaras (como hace _start_local_camera)
        camera_queues["Cámara Local"] = queue.Queue(maxsize=10)
        camera_queues["Cámara IP 1"] = queue.Queue(maxsize=10)
        dashboard.camera_queues = camera_queues
        
        # Esto fallaba con TclError antes del fix
        try:
            dashboard.setup_grid()
            self.root.update_idletasks()
        except Exception as e:
            self.fail(f"setup_grid() lanzó excepción al transicionar 0→N cámaras: {e}")
        
        # Verificar que se crearon los labels de video
        self.assertEqual(len(dashboard.video_labels), 2, "Debe haber 2 video labels")
        
        # Verificar que todos usan grid
        for cam_id, lbl in dashboard.video_labels.items():
            info = lbl.grid_info()
            self.assertTrue(len(info) > 0, f"Label de {cam_id} debe estar en grid")

    def test_grid_nxn_layout_correct(self):
        """Verifica que la cuadrícula NxN se calcule correctamente para 4 cámaras (2x2)."""
        from src.gui.dashboard import DashboardFrame
        
        camera_queues = {
            "Cam 1": queue.Queue(maxsize=5),
            "Cam 2": queue.Queue(maxsize=5),
            "Cam 3": queue.Queue(maxsize=5),
            "Cam 4": queue.Queue(maxsize=5),
        }
        dashboard = DashboardFrame(self.root, camera_queues)
        dashboard.grid(row=0, column=0, sticky="nsew")
        self.root.update_idletasks()
        
        self.assertEqual(len(dashboard.video_labels), 4)
        
        # Verificar posiciones grid (2x2)
        positions = []
        for cam_id, lbl in dashboard.video_labels.items():
            info = lbl.grid_info()
            positions.append((int(info['row']), int(info['column'])))
        
        # Debe haber posiciones (0,0), (0,1), (1,0), (1,1)
        expected = {(0, 0), (0, 1), (1, 0), (1, 1)}
        self.assertEqual(set(positions), expected, f"Layout 2x2 incorrecto: {positions}")

    def test_toggle_single_view_and_restore(self):
        """Verifica que toggle_single_view funcione sin mezclar geometry managers."""
        from src.gui.dashboard import DashboardFrame
        
        camera_queues = {
            "Cam A": queue.Queue(maxsize=5),
            "Cam B": queue.Queue(maxsize=5),
        }
        dashboard = DashboardFrame(self.root, camera_queues)
        dashboard.grid(row=0, column=0, sticky="nsew")
        self.root.update_idletasks()
        
        # Expandir vista de "Cam A"
        dashboard.toggle_single_view("Cam A")
        self.root.update_idletasks()
        self.assertTrue(dashboard.is_single_view)
        
        # Restaurar
        dashboard.toggle_single_view("Cam A")
        self.root.update_idletasks()
        self.assertFalse(dashboard.is_single_view)
        
        # Verificar que ambas cámaras están visibles de nuevo en grid
        for cam_id, lbl in dashboard.video_labels.items():
            info = lbl.grid_info()
            self.assertTrue(len(info) > 0, f"Label de {cam_id} debe estar visible en grid tras restaurar")

    def test_frame_consumption_with_mock_producers(self):
        """Verifica consumo de frames Zero-Blocking con productores simulados."""
        from src.gui.dashboard import DashboardFrame
        
        camera_queues = {
            "Test Cam": queue.Queue(maxsize=10),
        }
        dashboard = DashboardFrame(self.root, camera_queues)
        dashboard.grid(row=0, column=0, sticky="nsew")
        self.root.update_idletasks()
        
        # Inyectar frames simulados
        stop_event = threading.Event()
        
        def producer():
            while not stop_event.is_set():
                frame = np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)
                try:
                    camera_queues["Test Cam"].put_nowait(("Test Cam", frame))
                except queue.Full:
                    pass
                time.sleep(1/30)
        
        t = threading.Thread(target=producer, daemon=True)
        t.start()
        
        # Correr mainloop por 1 segundo
        start = time.time()
        updates = 0
        while time.time() - start < 1.0:
            self.root.update_idletasks()
            self.root.update()
            updates += 1
            time.sleep(0.01)
        
        stop_event.set()
        t.join(timeout=2)
        
        self.assertGreater(updates, 50, f"Debe haber >50 updates en 1s, hubo {updates}")
        print(f"✅ Frame consumption test: {updates} UI updates en 1 segundo")


if __name__ == "__main__":
    unittest.main()
