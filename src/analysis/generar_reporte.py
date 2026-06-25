import sqlite3
import pandas as pd
import os

# --- CONFIGURACIÓN ---
data_dir = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), 'OficinaEficiencia', 'data')
DB_PATH = os.path.join(data_dir, 'db', 'local_tracking.db')
OUTPUT_FILE = "Reporte_Eficiencia_Final.xlsx"

def generar_reporte_pro():
    if not os.path.exists(DB_PATH):
        print(f"❌ Error: No se encuentra la BD en {DB_PATH}")
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        
        # 1. Intentamos leer la tabla de registros
        try:
            query_records = "SELECT track_id, zone, timestamp, x, y FROM records WHERE inside_zone = 1"
            df_mov = pd.read_sql_query(query_records, conn)
        except:
            query_records = "SELECT track_id, zone, timestamp, x, y FROM tracking WHERE inside_zone = 1"
            df_mov = pd.read_sql_query(query_records, conn)
        
        # 2. Obtener nombres y fotos
        query_names = "SELECT track_id, employee_name, snapshot_path FROM snapshots"
        df_names = pd.read_sql_query(query_names, conn)
        
        if df_mov.empty:
            print("⚠️ No hay datos de movimiento dentro de las zonas.")
            return

        # Unimos nombres con movimientos
        df = pd.merge(df_mov, df_names.drop_duplicates('track_id'), on='track_id', how='left')
        
        # --- CORRECCIÓN DEL ERROR DE FECHA ---
        # Usamos format='mixed' para que acepte fechas con y sin milisegundos
        df['timestamp'] = pd.to_datetime(df['timestamp'], format='mixed')
        
        df['employee_name'] = df['employee_name'].fillna("Desconocido")

        reporte_final = []
        for (id_track, nombre, zona), group in df.groupby(['track_id', 'employee_name', 'zone']):
            entrada = group['timestamp'].min()
            salida = group['timestamp'].max()
            duracion = (salida - entrada).total_seconds() / 60
            
            # Movimiento de manos/cuerpo
            mov = group['x'].diff().abs().sum() + group['y'].diff().abs().sum()
            prod = min(100, (mov / (duracion + 1)) * 10) if duracion > 0.1 else 0
            
            reporte_final.append({
                "Nombre": nombre,
                "Zona": zona,
                "Entrada": entrada.strftime("%H:%M:%S"),
                "Salida": salida.strftime("%H:%M:%S"),
                "Minutos en Zona": round(duracion, 2),
                "Productividad %": round(prod, 1),
                "Estado": "Trabajando" if prod > 25 else "Inactivo",
                "Ruta Foto": group.iloc[0]['snapshot_path'] if 'snapshot_path' in group.columns else "N/A"
            })

        df_resumen = pd.DataFrame(reporte_final)

        # --- EXCEL CON GRÁFICA ---
        writer = pd.ExcelWriter(OUTPUT_FILE, engine='xlsxwriter')
        df_resumen.to_excel(writer, sheet_name='Analisis de Eficiencia', index=False)

        workbook  = writer.book
        worksheet = writer.sheets['Analisis de Eficiencia']
        chart = workbook.add_chart({'type': 'column'})
        max_row = len(df_resumen) + 1
        
        chart.add_series({
            'name':       'Productividad %',
            'categories': ['Analisis de Eficiencia', 1, 0, max_row - 1, 0],
            'values':     ['Analisis de Eficiencia', 1, 5, max_row - 1, 5],
            'data_labels': {'value': True},
            'fill':       {'color': '#1f77b4'}
        })

        chart.set_title({'name': 'Reporte de Productividad por Empleado'})
        chart.set_y_axis({'name': 'Nivel de Actividad (%)', 'max': 100})
        worksheet.insert_chart('J2', chart)

        writer.close()
        print(f"✅ Reporte generado exitosamente: {OUTPUT_FILE}")

    except Exception as e:
        print(f"❌ Error crítico al generar reporte: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    generar_reporte_pro()