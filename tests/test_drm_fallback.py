import unittest
from unittest.mock import patch
import platform
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.security.drm import DRMValidator

class TestDRM(unittest.TestCase):
    def test_wmi_fallback(self):
        # Muteamos por completo el stack pesado de administracion WMI fingiendo una computadora de oficina capada
        with patch('wmi.WMI') as mock_wmi:
            mock_wmi.side_effect = Exception("Acceso Denegado por Políticas de Dominio GPO de Windows Server")
            
            # Encender validador
            drm = DRMValidator()
            machine_id = drm.machine_id
            
            # Output de prueba
            self.assertEqual(len(machine_id), 64, "El Fallback falló al tratar de parsear un Hash de 256 bits estable")
            
            print(f"\n[Security Audit] Sistema WMI denegado a nivel usuario.")
            print(f"[Security Audit] Fallback Resiliente Executed con la tarjeta de red Local (MAC UUID).")
            print(f"[Crypto] Machine ID Salvavidas generado: {machine_id[:16]}... (Completado: 64 char SHA256)")

if __name__ == "__main__":
    unittest.main()
