import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
from datetime import datetime
from views.base_view import BaseView # Importar la clase base
from utils.data_helpers import limpiar_numero_documento # Importar función auxiliar

class ScheduleView(BaseView):
    """Vista para la gestión de la programación."""
    def __init__(self, parent, controller):
        # Inicializar atributos antes de llamar a super().__init__()
        self.tree = None
        self.filters = {}
        self.full_schedule_df = pd.DataFrame() # DataFrame para la programación completa
        self._sort_direction = "asc" # Dirección de ordenación inicial
        self._sort_column = None # Columna actualmente ordenada
        self.filter_entries = {} # <--- Asegurado que se inicializa aquí

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

        # Columnas de la tabla (todas las del archivo de programación)
        columns = [
            'semestre', 'materia', 'PROGRAMA', 'MATERIA', 'inp', 'grupo', 'nivel_grupo',
            'semanas', 'nro_horas', 'fecha_inicio', 'fecha_fin', 'nro_estudiantes_premat',
            'nro_estudiantes', 'TOTAL', 'nroidenti', 'profesor', 'dia', 'horario', 'aula', 'OBSERVACION'
        ]
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        self.tree.pack(side="left", fill="both", expand=True)

        for col in columns:
            self.tree.heading(col, text=col.replace("_", " ").title(), command=lambda c=col: self.ordenar_columna(c))
            self.tree.column(col, width=100) # Ancho por defecto

        scrollbar_y = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        scrollbar_y.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar_y.set)

        scrollbar_x = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        scrollbar_x.pack(side="bottom", fill="x")
        self.tree.configure(xscrollcommand=scrollbar_x.set)

        # Marco de filtros por columna
        filter_frame = ttk.Frame(self)
        filter_frame.pack(pady=5, padx=10, fill="x")
        
        tk.Label(filter_frame, text="Filtros por Columna:").pack(side=tk.LEFT, padx=5)
        
        # Crear los campos de filtro dinámicamente
        # Usar un subconjunto de columnas para los filtros visibles para no saturar la UI
        filterable_columns = ['profesor', 'materia', 'aula', 'dia', 'horario', 'grupo', 'nroidenti']
        for i, col in enumerate(filterable_columns):
            tk.Label(filter_frame, text=col.replace("_", " ").title()).pack(side=tk.LEFT, padx=2)
            entry = ttk.Entry(filter_frame, width=10)
            entry.pack(side=tk.LEFT, padx=2)
            entry.bind("<KeyRelease>", self.aplicar_filtros_columna)
            self.filter_entries[col] = entry # Asegurarse de que se usa self.filter_entries

        ttk.Button(filter_frame, text="Limpiar Filtros", command=self.limpiar_filtros).pack(side=tk.LEFT, padx=10)

    def cargar_datos_vista(self):
        """Carga y muestra la programación limpia completa."""
        self.full_schedule_df = self.controller.obtener_programacion_completa()
        self.actualizar_tabla(self.full_schedule_df)

    def actualizar_tabla(self, df):
        """Actualiza la tabla con los datos del DataFrame."""
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        if df.empty:
            return

        # Asegurarse de que todas las columnas esperadas existan en el DataFrame antes de insertarlas
        expected_columns = [
            'semestre', 'materia', 'PROGRAMA', 'MATERIA', 'inp', 'grupo', 'nivel_grupo',
            'semanas', 'nro_horas', 'fecha_inicio', 'fecha_fin', 'nro_estudiantes_premat',
            'nro_estudiantes', 'TOTAL', 'nroidenti', 'profesor', 'dia', 'horario', 'aula', 'OBSERVACION'
        ]
        
        for index, row in df.iterrows():
            values = []
            for col in expected_columns:
                value = row.get(col, '') # Usar .get() con un valor por defecto si la columna no existe
                if 'fecha' in col and pd.notna(value):
                    values.append(value.strftime('%Y-%m-%d'))
                elif pd.isna(value):
                    values.append('') # Reemplazar NaN con cadena vacía
                else:
                    values.append(value)
            self.tree.insert("", "end", values=values)

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
                self.actualizar_tabla(cleaned_df)
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
        filtered_df = self.full_schedule_df.copy()
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
                        filtered_df = filtered_df[filtered_df[col].astype(str).str.contains(filter_val, case=False, na=False)]
        self.actualizar_tabla(filtered_df)

    def limpiar_filtros(self):
        """Limpia todos los filtros y recarga la tabla."""
        for entry in self.filter_entries.values(): # Usar self.filter_entries
            entry.delete(0, tk.END)
        self.cargar_datos_vista()

    def ordenar_columna(self, col):
        """Ordena la tabla por la columna especificada."""
        # Obtener los datos actuales de la tabla
        data = [(self.tree.set(child, col), child) for child in self.tree.get_children('')]
        
        # Determinar si es un tipo numérico o fecha para ordenar correctamente
        try:
            if 'fecha' in col:
                data.sort(key=lambda t: datetime.strptime(t[0], '%Y-%m-%d') if t[0] else datetime.min)
            elif 'nroidenti' in col or 'nro_estudiantes' in col or 'TOTAL' in col or 'nro_horas' in col: # Asumiendo que estos son numéricos
                data.sort(key=lambda t: float(t[0]) if isinstance(t[0], str) and t[0].replace('.', '', 1).isdigit() else t[0])
            else:
                data.sort(key=lambda t: t[0])
        except ValueError:
            data.sort(key=lambda t: t[0])

        # Invertir el orden si ya estaba ordenado en esa dirección
        if hasattr(self, '_sort_direction') and self._sort_column == col and self._sort_direction == "asc":
            data.reverse()
            self._sort_direction = "desc"
        else:
            self._sort_direction = "asc"
        self._sort_column = col

        for index, (val, item) in enumerate(data):
            self.tree.move(item, '', index)

