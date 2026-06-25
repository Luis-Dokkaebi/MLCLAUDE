import unittest
from unittest.mock import MagicMock, patch
import os
import threading
import time

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.analysis.report_generator import DatabaseWorker
import pandas as pd

class TestDatabaseWorker(unittest.TestCase):
    def test_permission_error_on_locked_file(self):
        # Mocking DB Manager
        mock_db = MagicMock()
        mock_conn = MagicMock()
        mock_db._get_connection.return_value = mock_conn
        
        worker = DatabaseWorker(mock_db)
        
        # Eventos para sincronizar callbacks del hilo en el Unit Test
        error_event = threading.Event()
        success_event = threading.Event()
        
        error_msg = {"msg": ""}
        
        def mock_on_success(path, count):
            success_event.set()
            
        def mock_on_error(msg):
            error_msg["msg"] = msg
            error_event.set()

        output_path = "locked_mock.xlsx"
        
        # Bloquear artificialmente simulando MS Excel lock
        with patch('pandas.read_sql_query') as mock_read_sql:
            mock_read_sql.return_value = pd.DataFrame({"col": [1]})
            
            with patch('os.path.exists') as mock_exists:
                mock_exists.return_value = True
                
                with patch('os.rename') as mock_rename:
                    mock_rename.side_effect = PermissionError("Locked by Excel")
                    
                    worker.generate_excel_async("SELECT 1", output_path, mock_on_success, mock_on_error)
                    
                    # Esperar la confirmacion del Callback
                    error_event.wait(timeout=3)
                    
                    self.assertTrue(error_event.is_set(), "El callback de error asincrono debio llamarse de vuelta.")
                    self.assertIn("Cierre el archivo", error_msg["msg"], "Debe manejar el error indicando al usuario que debe cerrar el MS Excel.")
                    self.assertFalse(success_event.is_set(), "No debio llamarse a success.")

if __name__ == '__main__':
    unittest.main()
