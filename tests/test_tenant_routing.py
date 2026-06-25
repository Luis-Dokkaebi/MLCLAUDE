import unittest
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config.path_utils import ConfigManager
from config.config import get_db_path, get_faces_dir, get_export_dir

class TestTenantRouting(unittest.TestCase):
    def test_isolation(self):
        # 1. Tenant A
        ConfigManager.set_active_tenant("Tenant_A_Norte")
        db_a = get_db_path()
        faces_a = get_faces_dir()
        export_a = get_export_dir()
        
        # 2. Tenant B
        ConfigManager.set_active_tenant("Tenant_B_Sur")
        db_b = get_db_path()
        faces_b = get_faces_dir()
        export_b = get_export_dir()
        
        # Validar hermetismo puro (B2B Requirement)
        self.assertNotEqual(db_a, db_b, "Las rutas de SQLite deben estar estrictamente asiladas por sucursal.")
        self.assertNotEqual(faces_a, faces_b, "Los vectores faciales PKL deben estar aislados por sucursal para cumplir la GDPR.")
        self.assertNotEqual(export_a, export_b, "Los Excels no pueden mezclarse.")
        
        self.assertIn(os.path.join("OficinaEficiencia", "Tenants", "Tenant_A_Norte", "db"), db_a)
        self.assertIn(os.path.join("OficinaEficiencia", "Tenants", "Tenant_B_Sur", "faces"), faces_b)
        
        print("\n--- PRUEBA DE HERMETISMO B2B ---")
        print(f"Ruta DB Tenant A: {db_a}")
        print(f"Ruta DB Tenant B: {db_b}")
        print(">> Aislamiento de Variables de Entorno Validado.")

if __name__ == "__main__":
    unittest.main()
