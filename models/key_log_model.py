import pandas as pd
from datetime import datetime
import os
from tkinter import messagebox # Importar messagebox para mostrar errores
from utils.data_helpers import limpiar_numero_documento # Importar función auxiliar

class KeyLogModel:
    """
    Gestiona el registro de entrega y devolución de llaves.
    """
    def __init__(self, key_log_path="data/registro_entrega.xlsx"):
        self.key_log_path = key_log_path
        self._key_log_df = self._cargar_registro_llaves_al_inicio()

    def _cargar_registro_llaves_al_inicio(self):
        """
        Carga el registro de llaves existente al iniciar la aplicación.
        Si el archivo no existe, crea un DataFrame vacío y lo guarda.
        """
        if os.path.exists(self.key_log_path):
            try:
                df = pd.read_excel(self.key_log_path, engine='openpyxl')
                # Asegurar que las columnas de fecha/hora son datetime objects
                for col in ['fecha_entrega', 'fecha_devolucion']:
                    if col in df.columns:
                        df[col] = pd.to_datetime(df[col], errors='coerce')
                return df
            except Exception as e:
                print(f"Error al cargar el registro de llaves existente: {e}")
                df = self._crear_df_registro_vacio()
                self._guardar_registro_llaves_interna(df) # Intenta guardar un DataFrame vacío
                return df
        else:
            # Si el archivo no existe, crear un DataFrame vacío y guardarlo
            df = self._crear_df_registro_vacio()
            self._guardar_registro_llaves_interna(df) # Guardar para crear el archivo
            return df

    def _crear_df_registro_vacio(self):
        """
        Crea un DataFrame vacío para el registro de llaves con las columnas necesarias.
        """
        columns = [
            'fecha_entrega', 'hora_entrega', 'fecha_devolucion', 'hora_devolucion',
            'dia', 'materia', 'salon', 'docente', 'nroidenti', 'horario',
            'estado', 'observaciones'
        ]
        return pd.DataFrame(columns=columns)

    def _guardar_registro_llaves_interna(self, df_to_save):
        """
        Guarda el DataFrame del registro de llaves en el archivo predefinido.
        """
        os.makedirs(os.path.dirname(self.key_log_path), exist_ok=True)
        try:
            df_to_save.to_excel(self.key_log_path, index=False, engine='openpyxl')
            # No mostrar messagebox aquí para evitar spam en el inicio.
        except Exception as e:
            messagebox.showerror("Error de Guardado", f"No se pudo guardar el registro de llaves: {e}")

    def registrar_entrega(self, data):
        """
        Añade un nuevo registro de entrega de llave.
        Data should be a dictionary with keys matching DataFrame columns.
        """
        # Asegurarse de que el documento esté limpio
        data['nroidenti'] = limpiar_numero_documento(data['nroidenti'])

        # Verificar si ya hay una llave pendiente para este docente
        llaves_pendientes = self.obtener_llaves_pendientes()
        if not llaves_pendientes.empty and data['nroidenti'] in llaves_pendientes['nroidenti'].values:
            messagebox.showwarning("Advertencia", f"El docente {data.get('docente', 'N/A')} ({data['nroidenti']}) ya tiene una llave pendiente de devolución.")
            return False

        # Añadir fecha y hora de entrega
        now = datetime.now()
        data['fecha_entrega'] = now.strftime('%Y-%m-%d')
        data['hora_entrega'] = now.strftime('%H:%M:%S')
        data['fecha_devolucion'] = pd.NaT # Not a Time, para indicar que aún no se ha devuelto
        data['hora_devolucion'] = ''
        data['estado'] = 'Entregada' # Estado inicial

        new_record_df = pd.DataFrame([data])
        self._key_log_df = pd.concat([self._key_log_df, new_record_df], ignore_index=True)
        self._guardar_registro_llaves_interna(self._key_log_df)
        messagebox.showinfo("Registro Exitoso", "Llave registrada correctamente.")
        return True

    def registrar_devolucion(self, nroidenti):
        """
        Actualiza un registro de llave con la fecha de devolución y estado.
        Busca la llave por nroidenti que esté en estado 'Entregada'.
        """
        nroidenti_limpio = limpiar_numero_documento(nroidenti)
        
        # Buscar la llave pendiente para este nroidenti
        # Se asume que un docente solo puede tener una llave prestada a la vez
        idx_to_update = self._key_log_df[
            (self._key_log_df['nroidenti'] == nroidenti_limpio) &
            (self._key_log_df['estado'] == 'Entregada')
        ].index

        if not idx_to_update.empty:
            now = datetime.now()
            self._key_log_df.loc[idx_to_update, 'fecha_devolucion'] = now.strftime('%Y-%m-%d')
            self._key_log_df.loc[idx_to_update, 'hora_devolucion'] = now.strftime('%H:%M:%S')
            self._key_log_df.loc[idx_to_update, 'estado'] = 'Devuelta'
            self._guardar_registro_llaves_interna(self._key_log_df)
            messagebox.showinfo("Actualización Exitosa", "Llave devuelta registrada correctamente.")
            return True
        else:
            messagebox.showerror("Error", "No se encontró una llave pendiente para este documento.")
            return False

    def obtener_registro_llaves(self, filters=None, start_date=None, end_date=None):
        """
        Retorna el registro de llaves, aplicando filtros si se proporcionan.
        """
        df = self._key_log_df.copy()

        if filters:
            for col, value in filters.items():
                if value:
                    # Convertir a string para la búsqueda de subcadenas, ignorando caso
                    df = df[df[col].astype(str).str.contains(value, case=False, na=False)]
        
        # Filtrado por rango de fechas de entrega
        if start_date and end_date:
            # Asegurarse de que la columna sea datetime para la comparación
            df['fecha_entrega_dt'] = pd.to_datetime(df['fecha_entrega'], errors='coerce')
            df = df[(df['fecha_entrega_dt'] >= start_date) & (df['fecha_entrega_dt'] <= end_date)]
            df = df.drop(columns=['fecha_entrega_dt'])
        elif start_date:
            df['fecha_entrega_dt'] = pd.to_datetime(df['fecha_entrega'], errors='coerce')
            df = df[df['fecha_entrega_dt'] >= start_date]
            df = df.drop(columns=['fecha_entrega_dt'])
        elif end_date:
            df['fecha_entrega_dt'] = pd.to_datetime(df['fecha_entrega'], errors='coerce')
            df = df[df['fecha_entrega_dt'] <= end_date]
            df = df.drop(columns=['fecha_entrega_dt'])
            
        return df

    def obtener_llaves_pendientes(self):
        """
        Retorna las llaves que están en estado 'Entregada' (no devueltas).
        """
        if self._key_log_df.empty:
            return pd.DataFrame()
        return self._key_log_df[self._key_log_df['estado'] == 'Entregada'].copy()

    def obtener_registro_llaves_por_fecha(self, date):
        """
        Retorna el registro de llaves para un día específico.
        """
        if self._key_log_df.empty:
            return pd.DataFrame()
        
        # Convertir la columna 'fecha_entrega' a solo fecha para comparar
        df_temp = self._key_log_df.copy()
        df_temp['fecha_entrega_date'] = pd.to_datetime(df_temp['fecha_entrega'], errors='coerce').dt.date
        filtered_df = df_temp[df_temp['fecha_entrega_date'] == date].copy()
        filtered_df.drop(columns=['fecha_entrega_date'], inplace=True) # Eliminar columna temporal
        return filtered_df

    def obtener_historial_completo(self):
        """
        Retorna el DataFrame completo del registro de llaves.
        """
        return self._key_log_df.copy()

    def exportar_registro_llaves(self, df, path):
        """
        Exporta un DataFrame a un archivo Excel.
        """
        try:
            df.to_excel(path, index=False, engine='openpyxl')
            messagebox.showinfo("Exportación Exitosa", f"Registro exportado a: {path}")
        except Exception as e:
            messagebox.showerror("Error de Exportación", f"No se pudo exportar el registro: {e}")

