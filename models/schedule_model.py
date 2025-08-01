import pandas as pd
from datetime import datetime
import os
from tkinter import messagebox # Importar messagebox para mostrar errores
from utils.data_helpers import limpiar_numero_documento # Importar función auxiliar

class ScheduleModel:
    """
    Gestiona la carga, limpieza y almacenamiento de la programación académica.
    """
    def __init__(self, cleaned_schedule_path="data/programacion_limpia.xlsx"):
        self.cleaned_schedule_path = cleaned_schedule_path
        self._cleaned_schedule_df = self._cargar_programacion_limpia_al_inicio()

    def _cargar_programacion_limpia_al_inicio(self):
        """
        Carga la programación limpia existente al iniciar la aplicación.
        Si el archivo no existe, crea un DataFrame vacío y lo guarda.
        """
        if os.path.exists(self.cleaned_schedule_path):
            try:
                # Especificar el motor openpyxl para leer el archivo Excel
                df = pd.read_excel(self.cleaned_schedule_path, engine='openpyxl')
                # Asegurar que las columnas de hora sean objetos time
                if 'horario' in df.columns: # Verificar si la columna horario existe para extraer horas
                    # Intentar dividir el horario en hora_ini y hora_fin
                    df['hora_ini'] = ''
                    df['hora_fin'] = ''

                    # Intenta el formato "HH:MM A HH:MM", "HH:MM a HH:MM" o "HH:MM-HH:MM"
                    # Usar una función para aplicar la lógica de split de manera segura
                    def split_horario(horario_str):
                        if pd.isna(horario_str):
                            return '', ''
                        horario_str = str(horario_str).strip()
                        if ' A ' in horario_str.upper():
                            parts = horario_str.upper().split(' A ')
                            return parts[0], parts[1]
                        elif ' a ' in horario_str:
                            parts = horario_str.split(' a ')
                            return parts[0], parts[1]
                        elif '-' in horario_str:
                            parts = horario_str.split('-')
                            return parts[0], parts[1]
                        return horario_str, horario_str # Si no hay separador, usar el horario completo para ambos

                    df[['hora_ini_temp', 'hora_fin_temp']] = df['horario'].apply(lambda x: pd.Series(split_horario(x)))

                    # Convertir horas a formato time (con manejo de errores)
                    df['hora_ini'] = pd.to_datetime(df['hora_ini_temp'], format='%H:%M', errors='coerce').dt.time
                    df['hora_fin'] = pd.to_datetime(df['hora_fin_temp'], format='%H:%M', errors='coerce').dt.time
                    df = df.drop(columns=['hora_ini_temp', 'hora_fin_temp']) # Eliminar columnas temporales
                
                return df
            except Exception as e:
                print(f"Error al cargar la programación limpia existente: {e}")
                df = self._crear_df_programacion_vacio()
                self._guardar_programacion_limpia_interna(df)
                return df
        else:
            df = self._crear_df_programacion_vacio()
            self._guardar_programacion_limpia_interna(df)
            return df

    def _crear_df_programacion_vacio(self):
        """Crea un DataFrame vacío con las columnas esperadas para la programación."""
        columns = [
            'semestre', 'materia', 'PROGRAMA', 'MATERIA', 'inp', 'grupo', 'nivel_grupo',
            'semanas', 'nro_horas', 'fecha_inicio', 'fecha_fin', 'nro_estudiantes_premat',
            'nro_estudiantes', 'TOTAL', 'nroidenti', 'profesor', 'dia', 'horario', 'aula', 'OBSERVACION',
            'hora_ini', 'hora_fin' # Columnas añadidas internamente
        ]
        return pd.DataFrame(columns=columns)

    def limpiar_programacion(self, archivo_o_df):
        """
        Limpia y consolida la programación académica, unificando clases largas
        que están divididas en múltiples registros.
        
        Args:
            archivo_o_df: Puede ser una ruta de archivo Excel o un DataFrame de pandas
        
        Returns:
            DataFrame limpio y consolidado
        """
        # Verificar si es archivo o DataFrame
        if isinstance(archivo_o_df, str):
            # Es una ruta de archivo
            try:
                df = pd.read_excel(archivo_o_df, engine='openpyxl')
            except Exception as e:
                messagebox.showerror("Error de Archivo", f"Error al leer archivo: {e}")
                return pd.DataFrame()
        elif isinstance(archivo_o_df, pd.DataFrame):
            # Es un DataFrame
            df = archivo_o_df.copy()
        else:
            messagebox.showerror("Tipo de Datos", f"Tipo no soportado: {type(archivo_o_df)}")
            return pd.DataFrame()
        
        if df.empty:
            return df
        
        try:
            # Limpiar datos básicos
            if 'horario' in df.columns:
                df['horario'] = df['horario'].astype(str)
            else:
                df['horario'] = '' # Asegurar existencia de columna

            if 'profesor' in df.columns:
                df['profesor'] = df['profesor'].fillna('').str.strip()
            else:
                df['profesor'] = ''

            if 'nroidenti' in df.columns:
                df['nroidenti'] = df['nroidenti'].apply(limpiar_numero_documento)
            else:
                df['nroidenti'] = ''

            if 'dia' in df.columns:
                df['dia'] = df['dia'].str.upper().str.strip()
            else:
                df['dia'] = ''
            
            # Limpiar nombres de materias
            if 'MATERIA' in df.columns:
                df['materia'] = df['MATERIA'].fillna('').str.strip()
            elif 'materia' not in df.columns: # Si no existe 'MATERIA' ni 'materia'
                df['materia'] = ''
            else: # Si existe 'materia' pero no 'MATERIA'
                df['materia'] = df['materia'].fillna('').str.strip()


            # Separar hora inicio y fin con diferentes formatos posibles
            df['hora_ini'] = ''
            df['hora_fin'] = ''

            if 'horario' in df.columns and not df['horario'].empty:
                # Usar la función auxiliar para dividir el horario
                def split_horario_safe(horario_str):
                    if pd.isna(horario_str):
                        return '', ''
                    horario_str = str(horario_str).strip()
                    if ' A ' in horario_str.upper():
                        parts = horario_str.upper().split(' A ')
                        return parts[0], parts[1]
                    elif ' a ' in horario_str:
                        parts = horario_str.split(' a ')
                        return parts[0], parts[1]
                    elif '-' in horario_str:
                        parts = horario_str.split('-')
                        return parts[0], parts[1]
                    return horario_str, horario_str # Si no hay separador, usar el horario completo para ambos

                df[['hora_ini_temp', 'hora_fin_temp']] = df['horario'].apply(lambda x: pd.Series(split_horario_safe(x)))

                # Convertir horas a formato time (con manejo de errores)
                df['hora_ini'] = pd.to_datetime(df['hora_ini_temp'], format='%H:%M', errors='coerce').dt.time
                df['hora_fin'] = pd.to_datetime(df['hora_fin_temp'], format='%H:%M', errors='coerce').dt.time
                df = df.drop(columns=['hora_ini_temp', 'hora_fin_temp']) # Eliminar columnas temporales
            
            # Agrupar por clase con misma información para unificar franjas horarias
            columnas_agrupacion = ['nroidenti', 'profesor', 'materia', 'aula', 'dia']
            
            # Verificar que todas las columnas existan antes de agrupar
            columnas_disponibles = [col for col in columnas_agrupacion if col in df.columns]
            
            # Solo procesar si tenemos las columnas básicas para agrupar
            if len(columnas_disponibles) == len(columnas_agrupacion):
                # Preparar diccionario de agregación dinámicamente
                agg_dict = {}
                
                # Agregar columnas de hora si existen
                if 'hora_ini' in df.columns:
                    agg_dict['hora_ini'] = 'min'
                if 'hora_fin' in df.columns:
                    agg_dict['hora_fin'] = 'max'
                
                # Agregar columnas opcionales solo si existen
                for col in ['nro_estudiantes', 'grupo', 'nivel_grupo', 'semestre', 'PROGRAMA', 'semanas', 'nro_horas', 'fecha_inicio', 'fecha_fin', 'nro_estudiantes_premat', 'TOTAL', 'OBSERVACION']:
                    if col in df.columns:
                        agg_dict[col] = 'first'
                
                if agg_dict:  # Solo agrupar si tenemos algo que agregar
                    agrupado = df.groupby(columnas_disponibles).agg(agg_dict).reset_index()
                    
                    # Reconstruir columna horario si tenemos hora_ini y hora_fin
                    if 'hora_ini' in agrupado.columns and 'hora_fin' in agrupado.columns:
                        # Convertir NaT a cadena vacía y formatear a HH:MM antes de convertir a string
                        agrupado['hora_ini_str'] = agrupado['hora_ini'].apply(lambda x: x.strftime('%H:%M') if pd.notna(x) else '')
                        agrupado['hora_fin_str'] = agrupado['hora_fin'].apply(lambda x: x.strftime('%H:%M') if pd.notna(x) else '')
                        
                        # Asegurarse de que si una de las horas es vacía, el formato sea solo la otra hora o vacío
                        def format_horario_for_display(row):
                            if row['hora_ini_str'] and row['hora_fin_str']:
                                if row['hora_ini_str'] == row['hora_fin_str']: # Si son la misma hora, mostrar solo una
                                    return row['hora_ini_str']
                                return f"{row['hora_ini_str']} a {row['hora_fin_str']}"
                            elif row['hora_ini_str']:
                                return row['hora_ini_str']
                            elif row['hora_fin_str']:
                                return row['hora_fin_str']
                            return '' # Si ambas son vacías
                        
                        agrupado['horario'] = agrupado.apply(format_horario_for_display, axis=1)
                        agrupado = agrupado.drop(columns=['hora_ini_str', 'hora_fin_str']) # Limpiar columnas temporales
                    
                    return agrupado
                else:
                    return df
            else:
                # Si no podemos agrupar por las columnas clave, devolver el DataFrame limpio básico
                return df
                
        except Exception as e:
            messagebox.showerror("Error de Procesamiento", f"Error al procesar programación: {e}")
            return df  # Devolver datos básicos si falla el procesamiento avanzado

    def cargar_y_limpiar_programacion(self, file_path):
        """
        Carga un archivo de programación, lo limpia y lo guarda.
        """
        df_original = pd.read_excel(file_path, engine='openpyxl')
        df_limpio = self.limpiar_programacion(df_original)
        self._cleaned_schedule_df = df_limpio
        self._guardar_programacion_limpia_interna(df_limpio)
        return df_limpio

    def _guardar_programacion_limpia_interna(self, df_limpio):
        """
        Guarda el DataFrame de programación limpia en el archivo predefinido.
        """
        os.makedirs(os.path.dirname(self.cleaned_schedule_path), exist_ok=True)
        try:
            df_limpio.to_excel(self.cleaned_schedule_path, index=False, engine='openpyxl')
            # No mostrar messagebox aquí para evitar spam en el inicio.
            # messagebox.showinfo("Guardado", f"Programación limpia guardada en: {self.cleaned_schedule_path}")
        except Exception as e:
            messagebox.showerror("Error de Guardado", f"No se pudo guardar la programación limpia: {e}")

    def obtener_programacion_diaria(self, day):
        """
        Retorna la programación para un día específico.
        """
        if self._cleaned_schedule_df.empty:
            return pd.DataFrame()
        
        # Mapeo de nombres de días para asegurar consistencia
        day_map = {
            "LUNES": "LUNES", "MARTES": "MARTES", "MIÉRCOLES": "MIÉRCOLES",
            "JUEVES": "JUEVES", "VIERNES": "VIERNES", "SÁBADO": "SÁBADO",
            "DOMINGO": "DOMINGO"
        }
        day_upper = day_map.get(day.upper(), day.upper()) # Convertir a mayúsculas y usar mapeo

        return self._cleaned_schedule_df[self._cleaned_schedule_df['dia'] == day_upper].copy()

    def obtener_programacion_completa(self):
        """
        Retorna la programación limpia completa.
        """
        return self._cleaned_schedule_df.copy()
    
    def exportar_programacion(self, df, path):
        """
        Exporta un DataFrame a un archivo Excel.
        """
        try:
            df.to_excel(path, index=False, engine='openpyxl')
            messagebox.showinfo("Exportación Exitosa", f"Programación exportada a: {path}")
        except Exception as e:
            messagebox.showerror("Error de Exportación", f"No se pudo exportar la programación : {e}")

