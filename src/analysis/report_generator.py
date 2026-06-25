# src/analysis/report_generator.py

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import threading
from typing import Callable
import time
import os

class ReportGenerator:
    def __init__(self, results_df):
        self.df = results_df

    def generate_table(self):
        print("\n===== TABLA DE EFICIENCIA =====\n")
        print(self.df)

    def generate_bar_plot(self, save_path=None):
        plt.figure(figsize=(10, 6))
        
        # Determine X axis label
        if 'employee_name' in self.df.columns:
            # Create a combined label
            self.df['label'] = self.df.apply(lambda row: f"{row['track_id']} - {row['employee_name']}" if row['employee_name'] and row['employee_name'] != 'Unknown' else str(row['track_id']), axis=1)
            x_col = 'label'
            xlabel = "Empleado / ID"
        else:
            x_col = 'track_id'
            xlabel = "ID de Persona"

        # Si hay múltiples visitas, esto mostrará el promedio. Podríamos cambiar estimator=sum para total.
        sns.barplot(data=self.df, x=x_col, y="duration_sec", hue="zone", palette="viridis")
        plt.title("Duración Promedio de Estancia por Persona")
        plt.xlabel(xlabel)
        plt.ylabel("Duración (segundos)")
        plt.legend(title="Zona", bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        if save_path:
            plt.savefig(save_path)
        plt.show()

    def export_to_excel(self, file_path="data/reporting/eficiencia.xlsx"):
        self.df.to_excel(file_path, index=False)
        print(f"Reporte exportado a: {file_path}")

class DatabaseWorker:
    def __init__(self, db_manager):
        """Inicializa el worker con la conexión a la base de datos (ej. SQLCipher)"""
        self.db = db_manager

    def generate_excel_async(self, query: str, output_path: str, on_success: Callable, on_error: Callable):
        """Ejecuta un volcado a Excel asincrónicamente usando hilos para Zero-Blocking UI."""
        
        def _worker():
            try:
                # 1. Simular carga inicial conectando al db
                conn = self.db._get_connection()
                
                # 2. Cargar en Pandas (puede demorar, de ah de que este en background)
                df = pd.read_sql_query(query, conn)
                
                # 3. Validar si el archivo esta en uso por Excel.exe (PermissionError local)
                if os.path.exists(output_path):
                    try:
                        # Test rapido intentando renombrar el archivo sobre si mismo 
                        # Si está bloqueado por Excel arroja OSError
                        os.rename(output_path, output_path)
                    except OSError:
                        raise PermissionError(f"Cierre el archivo {output_path} en Microsoft Excel antes de sobrescribir.")

                # 4. Exportar a XLSX (Operación bloqueante de I/O)
                df.to_excel(output_path, index=False, engine='openpyxl')
                
                # 5. Invocar Callback Exitoso en el Hilo Principal (o que este lo enrute)
                if on_success:
                    on_success(output_path, len(df))
            
            except Exception as e:
                # 6. Invocar Callback de Error
                if on_error:
                    on_error(str(e))
            finally:
                if 'conn' in locals() and hasattr(conn, 'close'):
                    conn.close()

        # Iniciar y desatar el hilo
        t = threading.Thread(target=_worker, daemon=True, name="DB_Excel_Export")
        t.start()
