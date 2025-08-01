import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
from datetime import datetime
from views.base_view import BaseView # Importar la clase base
from utils.data_helpers import limpiar_numero_documento, limpiar_texto_excel # Importar función auxiliar

class ScheduleView(BaseView):
    """Vista para la gestión de la programación."""
    def __init__(self, parent, controller):
        # Inicializar atributos antes de llamar a super().__init__()
        self.tree = None
        self.filters = {}
        self.full_schedule_df = pd.DataFrame() # DataFrame original completo cargado
        self.full_schedule_df_filtered = pd.DataFrame() # DataFrame después de aplicar filtros/ordenación
        self._sort_direction = "asc" # Dirección de ordenación inicial
        self._sort_column = None # Columna actualmente ordenada
        self.filter_entries = {} # Asegurado que se inicializa aquí

        # Atributos para la paginación
        self.current_page = 1
        self.items_per_page_options = [10, 20, 50, 100, 200]
        self.items_per_page = self.items_per_page_options[1] # Default 20 items per page
        self.total_pages = 1

        super().__init__(parent, controller, "Programación Académica")

    def create_widgets(self):
        super().create_widgets()

        # Marco de carga y limpieza
        load_frame = ttk.LabelFrame(self, text="Cargar y Limpiar Programación")
        load_frame.pack(pady=10, padx=10, fill="x")

        ttk.Button(load_frame, text="Cargar y Limpiar Excel", command=self.cargar_y_limpiar_programacion).pack(side=tk.LEFT, padx=5)
        ttk.Button(load_frame, text="Exportar Programación Limpia", command=self.exportar_programacion_limpia).pack(side=tk.RIGHT, padx=5)

        # Marco de la tabla
        table_frame = ttk.Frame(self)
        table_frame.pack(pady=10, padx=10, fill="both", expand=True)

        # Columnas de la tabla (todas las del archivo de programación, ajustadas para la vista)
        columns = [
            'semestre', 'codigo_materia', 'PROGRAMA', 'materia', 'inp', 'grupo', 'nivel_grupo',
            'semanas', 'nro_horas', 'fecha_inicio', 'fecha_fin', 'nro_estudiantes_premat',
            'nro_estudiantes', 'TOTAL', 'nroidenti', 'profesor', 'dia', 'horario', 'aula', 'OBSERVACION'
        ]
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        self.tree.pack(side="left", fill="both", expand=True)

        # Configurar encabezados y ancho de columnas
        column_display_names = {
            'semestre': 'Semestre',
            'codigo_materia': 'Cód. Materia', # Nuevo nombre para el código
            'PROGRAMA': 'Programa',
            'materia': 'Materia', # Nombre descriptivo de la materia
            'inp': 'Inp',
            'grupo': 'Grupo',
            'nivel_grupo': 'Nivel Grupo',
            'semanas': 'Semanas',
            'nro_horas': 'Nro. Horas',
            'fecha_inicio': 'Fecha Inicio',
            'fecha_fin': 'Fecha Fin',
            'nro_estudiantes_premat': 'Est. Premat.',
            'nro_estudiantes': 'Estudiantes',
            'TOTAL': 'Total',
            'nroidenti': 'Nro. Identificación',
            'profesor': 'Profesor',
            'dia': 'Día',
            'horario': 'Horario',
            'aula': 'Aula',
            'OBSERVACION': 'Observación'
        }

        for col in columns:
            self.tree.heading(col, text=column_display_names.get(col, col.replace("_", " ").title()), command=lambda c=col: self.ordenar_columna(c))
            self.tree.column(col, width=100) # Ancho por defecto

        # Ajustes de ancho para algunas columnas importantes
        self.tree.column('profesor', width=150)
        self.tree.column('materia', width=200)
        self.tree.column('codigo_materia', width=100)
        self.tree.column('horario', width=120)
        self.tree.column('nroidenti', width=120)
        self.tree.column('aula', width=80)
        self.tree.column('PROGRAMA', width=200)


        scrollbar_y = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        scrollbar_y.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar_y.set)

        scrollbar_x = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        scrollbar_x.pack(side="bottom", fill="x")
        self.tree.configure(xscrollcommand=scrollbar_x.set)
        # Marco de paginación
        pagination_frame = ttk.Frame(self)
        pagination_frame.pack(pady=10, fill="x")

        ttk.Label(pagination_frame, text="Items por página:").pack(side=tk.LEFT, padx=5)
        self.items_per_page_combo = ttk.Combobox(pagination_frame, values=self.items_per_page_options,
                                                 state="readonly", width=5)
        self.items_per_page_combo.set(self.items_per_page)
        self.items_per_page_combo.bind("<<ComboboxSelected>>", self.set_items_per_page)
        self.items_per_page_combo.pack(side=tk.LEFT, padx=5)

        self.prev_page_button = ttk.Button(pagination_frame, text="< Anterior", command=self.go_to_previous_page)
        self.prev_page_button.pack(side=tk.LEFT, padx=10)

        self.page_info_label = ttk.Label(pagination_frame, text="Página 1 de 1")
        self.page_info_label.pack(side=tk.LEFT, padx=10)

        self.next_page_button = ttk.Button(pagination_frame, text="Siguiente >", command=self.go_to_next_page)
        self.next_page_button.pack(side=tk.LEFT, padx=10)


    def cargar_datos_vista(self):
        """Carga y muestra la programación limpia completa."""
        self.full_schedule_df = self.controller.obtener_programacion_completa()
        self.full_schedule_df_filtered = self.full_schedule_df.copy() # Inicializar con todos los datos
        self.current_page = 1 # Reset page on new data load
        self.actualizar_tabla(self.full_schedule_df_filtered)

    def actualizar_tabla(self, df_to_display):
        """Actualiza la tabla con los datos del DataFrame, aplicando paginación."""
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        if df_to_display.empty:
            self.total_pages = 1
            self.current_page = 1
            self.page_info_label.config(text="Página 0 de 0")
            self.prev_page_button.config(state=tk.DISABLED)
            self.next_page_button.config(state=tk.DISABLED)
            return

        # Calculate total pages based on the DataFrame being displayed
        self.total_pages = (len(df_to_display) + self.items_per_page - 1) // self.items_per_page

        # Adjust current page if it's out of bounds
        if self.current_page > self.total_pages:
            self.current_page = self.total_pages
        if self.current_page < 1:
            self.current_page = 1

        # Calculate slice for current page
        start_index = (self.current_page - 1) * self.items_per_page
        end_index = start_index + self.items_per_page
        paginated_df = df_to_display.iloc[start_index:end_index]

        # Update page info label
        self.page_info_label.config(text=f"Página {self.current_page} de {self.total_pages}")

        # Update pagination button states
        self.prev_page_button.config(state=tk.NORMAL if self.current_page > 1 else tk.DISABLED)
        self.next_page_button.config(state=tk.NORMAL if self.current_page < self.total_pages else tk.DISABLED)


        # Asegurarse de que todas las columnas esperadas existan en el DataFrame antes de insertarlas
        # y usar los nombres de columna del DataFrame (que ya hemos mapeado en el modelo)
        expected_columns_from_df = [
            'semestre', 'codigo_materia', 'PROGRAMA', 'materia', 'inp', 'grupo', 'nivel_grupo',
            'semanas', 'nro_horas', 'fecha_inicio', 'fecha_fin', 'nro_estudiantes_premat',
            'nro_estudiantes', 'TOTAL', 'nroidenti', 'profesor', 'dia', 'horario', 'aula', 'OBSERVACION'
        ]
        
        for index, row in paginated_df.iterrows(): # Use paginated_df here
            values = []
            for col in expected_columns_from_df:
                value = row.get(col, '') # Usar .get() con un valor por defecto si la columna no existe
                if 'fecha' in col and pd.notna(value):
                    values.append(value.strftime('%Y-%m-%d'))
                elif pd.isna(value):
                    values.append('') # Reemplazar NaN con cadena vacía
                else:
                    values.append(value)
            self.tree.insert("", "end", values=values)

    def set_items_per_page(self, event=None):
        """Sets the number of items to display per page."""
        try:
            new_items_per_page = int(self.items_per_page_combo.get())
            if new_items_per_page > 0:
                self.items_per_page = new_items_per_page
                self.current_page = 1 # Reset to first page when items per page changes
                self.actualizar_tabla(self.full_schedule_df_filtered) # Update table with new pagination
        except ValueError:
            messagebox.showwarning("Entrada inválida", "Por favor, ingrese un número válido para 'Items por página'.")

    def go_to_previous_page(self):
        """Navigates to the previous page."""
        if self.current_page > 1:
            self.current_page -= 1
            self.actualizar_tabla(self.full_schedule_df_filtered) # Update table with new pagination

    def go_to_next_page(self):
        """Navigates to the next page."""
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.actualizar_tabla(self.full_schedule_df_filtered) # Update table with new pagination


    def cargar_y_limpiar_programacion(self):
        """Permite al usuario seleccionar un archivo Excel, lo carga, limpia y guarda."""
        file_path = filedialog.askopenfilename(
            filetypes=[("Archivos Excel", "*.xlsx;*.xls")],
            title="Seleccionar Archivo de Programación"
        )
        if file_path:
            try:
                # Mostrar un mensaje de carga
                messagebox.showinfo("Cargando", "Cargando y limpiando programación. Esto puede tardar un momento...")
                cleaned_df = self.controller.cargar_y_limpiar_programacion(file_path)
                self.full_schedule_df = cleaned_df
                self.full_schedule_df_filtered = cleaned_df.copy() # Reset filtered DF
                self.current_page = 1 # Reset page on new data load
                self.actualizar_tabla(self.full_schedule_df_filtered)
                messagebox.showinfo("Éxito", "Programación cargada y limpia correctamente.")
            except Exception as e:
                messagebox.showerror("Error", f"Error al procesar el archivo: {e}")

    def exportar_programacion_limpia(self):
        """Exporta la programación limpia actual a un archivo Excel."""
        if self.full_schedule_df.empty:
            messagebox.showwarning("Advertencia", "No hay programación limpia para exportar. Por favor, cargue y limpie una programación primero.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Archivos Excel", "*.xlsx")],
            title="Guardar Programación Limpia"
        )
        if file_path:
            self.controller.exportar_programacion(self.full_schedule_df, file_path)

    def aplicar_filtros_columna(self, event=None):
        """Aplica los filtros por columna a la tabla."""
        filtered_df = self.full_schedule_df.copy() # Start from the full original data
        for col, entry in self.filter_entries.items(): # Usar self.filter_entries
            filter_val = entry.get().strip()
            if filter_val:
                if col in filtered_df.columns:
                    # Limpiar documento si la columna es nroidenti
                    if col == 'nroidenti':
                        filtered_df['nroidenti_limpio'] = filtered_df['nroidenti'].apply(limpiar_numero_documento)
                        filtered_df = filtered_df[filtered_df['nroidenti_limpio'].str.contains(limpiar_numero_documento(filter_val), case=False, na=False)]
                        filtered_df = filtered_df.drop(columns=['nroidenti_limpio'])
                    else:
                        filtered_df = filtered_df[filtered_df[col].astype(str).str.contains(limpiar_texto_excel(filter_val), case=False, na=False)]
        
        # Después de filtrar, actualizar el DataFrame filtrado para paginación
        self.full_schedule_df_filtered = filtered_df.copy()
        self.current_page = 1 # Reset to first page after filtering
        self.actualizar_tabla(self.full_schedule_df_filtered) # Pass the filtered DF to update table


    def limpiar_filtros(self):
        """Limpia todos los filtros y recarga la tabla."""
        for entry in self.filter_entries.values(): # Usar self.filter_entries
            entry.delete(0, tk.END)
        self.full_schedule_df_filtered = self.full_schedule_df.copy() # Reset to original full data
        self.current_page = 1 # Reset to first page
        self.actualizar_tabla(self.full_schedule_df_filtered)

    def ordenar_columna(self, col):
        """Ordena la tabla por la columna especificada."""
        # Obtener el DataFrame actualmente mostrado (filtrado o completo)
        df_to_sort = self.full_schedule_df_filtered.copy() # Always sort the currently filtered data

        if df_to_sort.empty:
            return

        # Determinar la dirección de ordenación
        if self._sort_column == col:
            self._sort_direction = "desc" if self._sort_direction == "asc" else "asc"
        else:
            self._sort_direction = "asc"
            self._sort_column = col

        # Función clave para la ordenación robusta
        def sort_key_robust(row_val):
            try:
                # Intentar convertir a float para números
                # Si es un número de documento, limpiarlo antes de intentar convertir a float
                if col == "nroidenti":
                    cleaned_value = limpiar_numero_documento(row_val)
                    return (0, float(cleaned_value))
                # Para otras columnas numéricas, intentar directamente
                return (0, float(row_val)) # 0 para que los números se ordenen antes que las cadenas
            except (ValueError, TypeError):
                # Si no es un número, tratar como cadena
                return (1, str(row_val).lower()) # 1 para que las cadenas se ordenen después de los números

        # Sort the DataFrame directly
        df_to_sort['sort_key'] = df_to_sort[col].apply(sort_key_robust)
        df_to_sort = df_to_sort.sort_values(by='sort_key', ascending=(self._sort_direction == "asc")).drop(columns='sort_key')
        
        # Update the filtered DataFrame with the sorted data
        self.full_schedule_df_filtered = df_to_sort
        self.current_page = 1 # Reset to first page after sorting
        self.actualizar_tabla(self.full_schedule_df_filtered) # Pass the sorted DF to update table

        # Actualizar el encabezado de la columna para mostrar la dirección de ordenación
        for c in self.tree["columns"]:
            text = self.tree.heading(c, "text")
            # Remove existing arrows
            text = text.replace(" ↑", "").replace(" ↓", "")
            if c == col:
                arrow = " ↑" if self._sort_direction == "asc" else " ↓"
                self.tree.heading(c, text=f"{text}{arrow}")
            else:
                self.tree.heading(c, text=text)

