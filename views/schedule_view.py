import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
from datetime import datetime

from views.base_view import BaseView
from utils.data_helpers import limpiar_numero_documento, limpiar_texto_excel

class ScheduleView(BaseView):
    """Vista para la gestión de la programación."""

    def __init__(self, parent, controller):
        self.tree = None
        self.filters = {}
        self.full_schedule_df = pd.DataFrame()
        self.full_schedule_df_filtered = pd.DataFrame()
        self._sort_direction = "asc"
        self._sort_column = None
        self.filter_entries = {}

        self.current_page = 1
        self.items_per_page_options = [10, 20, 50, 100, 200]
        self.items_per_page = self.items_per_page_options[1]
        self.total_pages = 1

        self.columns = [
            'semestre', 'codigo_materia', 'PROGRAMA', 'materia', 'inp', 'grupo', 'nivel_grupo',
            'semanas', 'nro_horas', 'fecha_inicio', 'fecha_fin', 'nro_estudiantes_premat',
            'nro_estudiantes', 'TOTAL', 'nroidenti', 'profesor', 'dia', 'horario', 'aula', 'OBSERVACION'
        ]
        self.column_visibility = {col: True for col in self.columns}
        self.column_display_names = {
            'semestre': 'Semestre',
            'codigo_materia': 'Cód. Materia',
            'PROGRAMA': 'Programa',
            'materia': 'Materia',
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

        super().__init__(parent, controller, "Programación Académica")

    def create_widgets(self):
        super().create_widgets()

        load_frame = ttk.LabelFrame(self, text="Cargar y Limpiar Programación")
        load_frame.pack(pady=10, padx=10, fill="x")

        ttk.Button(load_frame, text="Cargar y Limpiar Excel", command=self.cargar_y_limpiar_programacion).pack(side=tk.LEFT, padx=5)
        ttk.Button(load_frame, text="Exportar Programación Limpia", command=self.exportar_programacion_limpia).pack(side=tk.RIGHT, padx=5)
        ttk.Button(load_frame, text="Seleccionar columnas visibles", command=self.mostrar_selector_columnas).pack(side=tk.LEFT, padx=5)

        table_frame = ttk.Frame(self)
        table_frame.pack(pady=10, padx=10, fill="both", expand=True)

        self.tree = ttk.Treeview(table_frame, columns=self.columns, show="headings")
        self.tree.pack(side="left", fill="both", expand=True)

        for col in self.columns:
            self.tree.heading(col, text=self.column_display_names.get(col, col), command=lambda c=col: self.ordenar_columna(c))
            self.tree.column(col, width=100)

        scrollbar_y = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        scrollbar_y.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar_y.set)

        scrollbar_x = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        scrollbar_x.pack(side="bottom", fill="x")
        self.tree.configure(xscrollcommand=scrollbar_x.set)

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

    def mostrar_selector_columnas(self):
        ventana = tk.Toplevel(self)
        ventana.title("Seleccionar columnas visibles")
        ventana.grab_set()

        for i, col in enumerate(self.columns):
            var = tk.BooleanVar(value=self.column_visibility[col])
            def toggle(c=col, v=var):
                self.column_visibility[c] = v.get()
                self.actualizar_tabla(self.full_schedule_df_filtered)

            chk = tk.Checkbutton(ventana, text=self.column_display_names[col], variable=var, command=toggle)
            chk.grid(row=i // 3, column=i % 3, sticky="w", padx=10, pady=5)

    def cargar_datos_vista(self):
        self.full_schedule_df = self.controller.obtener_programacion_completa()
        self.full_schedule_df_filtered = self.full_schedule_df.copy()
        self.actualizar_tabla(self.full_schedule_df_filtered)

    def actualizar_tabla(self, df_to_display):
        for item in self.tree.get_children():
            self.tree.delete(item)

        if df_to_display.empty:
            self.total_pages = 1
            self.current_page = 1
            self.page_info_label.config(text="Página 0 de 0")
            self.prev_page_button.config(state=tk.DISABLED)
            self.next_page_button.config(state=tk.DISABLED)
            return

        self.total_pages = (len(df_to_display) + self.items_per_page - 1) // self.items_per_page
        self.current_page = max(1, min(self.current_page, self.total_pages))

        start_index = (self.current_page - 1) * self.items_per_page
        end_index = start_index + self.items_per_page
        paginated_df = df_to_display.iloc[start_index:end_index]

        self.page_info_label.config(text=f"Página {self.current_page} de {self.total_pages}")
        self.prev_page_button.config(state=tk.NORMAL if self.current_page > 1 else tk.DISABLED)
        self.next_page_button.config(state=tk.NORMAL if self.current_page < self.total_pages else tk.DISABLED)

        for col in self.columns:
            visible = self.column_visibility.get(col, True)
            self.tree.column(col, width=100 if visible else 0, minwidth=0, stretch=visible)
            self.tree.heading(col, text=self.column_display_names.get(col, col) if visible else "")

        for _, row in paginated_df.iterrows():
            values = []
            for col in self.columns:
                if not self.column_visibility.get(col, True):
                    continue
                val = row.get(col, '')
                if 'fecha' in col and pd.notna(val):
                    values.append(val.strftime('%Y-%m-%d'))
                elif pd.isna(val):
                    values.append('')
                else:
                    values.append(val)
            self.tree.insert("", "end", values=values)

    def set_items_per_page(self, event=None):
        try:
            new_val = int(self.items_per_page_combo.get())
            if new_val > 0:
                self.items_per_page = new_val
                self.actualizar_tabla(self.full_schedule_df_filtered)
        except ValueError:
            messagebox.showwarning("Entrada inválida", "Número inválido para 'Items por página'.")

    def go_to_previous_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.actualizar_tabla(self.full_schedule_df_filtered)

    def go_to_next_page(self):
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.actualizar_tabla(self.full_schedule_df_filtered)

    def cargar_y_limpiar_programacion(self):
        file_path = filedialog.askopenfilename(filetypes=[("Archivos Excel", "*.xlsx;*.xls")], title="Seleccionar Archivo")
        if file_path:
            try:
                messagebox.showinfo("Cargando", "Cargando y limpiando programación...")
                cleaned_df = self.controller.cargar_y_limpiar_programacion(file_path)
                self.full_schedule_df = cleaned_df
                self.full_schedule_df_filtered = cleaned_df.copy()
                self.actualizar_tabla(self.full_schedule_df_filtered)
                messagebox.showinfo("Éxito", "Programación cargada correctamente.")
            except Exception as e:
                messagebox.showerror("Error", f"Error: {e}")

    def exportar_programacion_limpia(self):
        if self.full_schedule_df.empty:
            messagebox.showwarning("Advertencia", "No hay programación limpia para exportar.")
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx")], title="Guardar Programación")
        if file_path:
            self.controller.exportar_programacion(self.full_schedule_df, file_path)

    def ordenar_columna(self, col):
        df = self.full_schedule_df_filtered.copy()
        if df.empty:
            return

        if self._sort_column == col:
            self._sort_direction = "desc" if self._sort_direction == "asc" else "asc"
        else:
            self._sort_column = col
            self._sort_direction = "asc"

        def sort_key(val):
            try:
                if col == "nroidenti":
                    val = limpiar_numero_documento(val)
                return (0, float(val))
            except:
                return (1, str(val).lower())

        df['sort_key'] = df[col].apply(sort_key)
        df = df.sort_values('sort_key', ascending=(self._sort_direction == "asc")).drop(columns='sort_key')
        self.full_schedule_df_filtered = df
        self.actualizar_tabla(self.full_schedule_df_filtered)
