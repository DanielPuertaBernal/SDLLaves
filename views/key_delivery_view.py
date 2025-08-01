import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
from datetime import datetime
from views.base_view import BaseView # Importar la clase base
from utils.data_helpers import limpiar_numero_documento # Importar función auxiliar

class KeyDeliveryView(BaseView):
    """Vista para la entrega de llaves."""
    def __init__(self, parent, controller):
        # Inicializar atributos antes de llamar a super().__init__()
        self.search_doc_entry = None
        self.tree = None
        self.filters = {} 
        self.current_day_schedule_df = pd.DataFrame() # DataFrame para la programación del día
        self._sort_direction = "asc" # Dirección de ordenación inicial
        self._sort_column = None # Columna actualmente ordenada

        super().__init__(parent, controller, "Entrega de Llaves")

    def create_widgets(self):
        super().create_widgets()

        # Marco de búsqueda
        search_frame = ttk.LabelFrame(self, text="Buscar Clase del Docente")
        search_frame.pack(pady=10, padx=10, fill="x")

        tk.Label(search_frame, text="Número de Documento del Docente:").pack(side=tk.LEFT, padx=5)
        self.search_doc_entry = ttk.Entry(search_frame)
        self.search_doc_entry.pack(side=tk.LEFT, padx=5, expand=True, fill="x")
        self.search_doc_entry.bind("<Return>", self.aplicar_filtro_busqueda) # Filtrar al presionar Enter
        ttk.Button(search_frame, text="Buscar", command=self.aplicar_filtro_busqueda).pack(side=tk.LEFT, padx=5)
        ttk.Button(search_frame, text="Ver Llaves Prestadas Hoy", command=self.mostrar_modal_llaves_prestadas).pack(side=tk.RIGHT, padx=5)

        # Marco de la tabla
        table_frame = ttk.Frame(self)
        table_frame.pack(pady=10, padx=10, fill="both", expand=True)

        # Columnas de la tabla
        columns = ("salón", "franja_horaria", "docente", "materia", "grupo", "día", "nroidenti")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        self.tree.pack(side="left", fill="both", expand=True)

        # Encabezados de las columnas
        self.tree.heading("salón", text="Salón", command=lambda: self.ordenar_columna("salón"))
        self.tree.heading("franja_horaria", text="Franja Horaria", command=lambda: self.ordenar_columna("franja_horaria"))
        self.tree.heading("docente", text="Docente", command=lambda: self.ordenar_columna("docente"))
        self.tree.heading("materia", text="Materia", command=lambda: self.ordenar_columna("materia"))
        self.tree.heading("grupo", text="Grupo", command=lambda: self.ordenar_columna("grupo"))
        self.tree.heading("día", text="Día", command=lambda: self.ordenar_columna("día"))
        self.tree.heading("nroidenti", text="Nro. Identificación", command=lambda: self.ordenar_columna("nroidenti"))

        # Configurar ancho de columnas
        self.tree.column("salón", width=80, anchor="center")
        self.tree.column("franja_horaria", width=120, anchor="center")
        self.tree.column("docente", width=180)
        self.tree.column("materia", width=150)
        self.tree.column("grupo", width=80, anchor="center")
        self.tree.column("día", width=80, anchor="center")
        self.tree.column("nroidenti", width=120, anchor="center")

        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Filtrado por columna
        filter_frame = ttk.Frame(self)
        filter_frame.pack(pady=5, padx=10, fill="x")

        tk.Label(filter_frame, text="Filtros por Columna:").pack(side=tk.LEFT, padx=5)
        for col in columns[:-1]: # No incluir nroidenti en los filtros de columna individuales
            tk.Label(filter_frame, text=col.replace("_", " ").title()).pack(side=tk.LEFT, padx=2)
            entry = ttk.Entry(filter_frame, width=10)
            entry.pack(side=tk.LEFT, padx=2)
            entry.bind("<KeyRelease>", self.aplicar_filtros_columna)
            self.filters[col] = entry
        
        ttk.Button(filter_frame, text="Limpiar Filtros", command=self.limpiar_todos_los_filtros).pack(side=tk.LEFT, padx=10)

        # Botón para registrar entrega de llave
        ttk.Button(self, text="Registrar Entrega de Llave", command=self.registrar_entrega_llave).pack(pady=10)

    def cargar_datos_vista(self):
        """Carga y muestra la programación del día actual."""
        today = datetime.now().strftime("%A").upper() # Obtener el día de la semana actual en español y mayúsculas
        # Mapear los nombres de los días de la semana de Python a los que esperas en tu DataFrame
        day_names_map = {
            "MONDAY": "LUNES", "TUESDAY": "MARTES", "WEDNESDAY": "MIÉRCOLES",
            "THURSDAY": "JUEVES", "FRIDAY": "VIERNES", "SATURDAY": "SÁBADO",
            "SUNDAY": "DOMINGO"
        }
        today_mapped = day_names_map.get(datetime.now().strftime("%A").upper(), datetime.now().strftime("%A").upper())

        self.current_day_schedule_df = self.controller.obtener_programacion_diaria(today_mapped)
        self.actualizar_tabla(self.current_day_schedule_df)

    def actualizar_tabla(self, df):
        """Actualiza la tabla con los datos del DataFrame."""
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        if df.empty:
            return

        # Asegurarse de que las columnas existan antes de intentar acceder a ellas
        required_cols = ["aula", "horario", "profesor", "materia", "grupo", "dia", "nroidenti"]
        for col in required_cols:
            if col not in df.columns:
                df[col] = "" # Añadir columna vacía si no existe

        for index, row in df.iterrows():
            self.tree.insert("", "end", values=(
                row["aula"], row["horario"], row["profesor"], row["materia"],
                row["grupo"], row["dia"], row["nroidenti"]
            ), iid=index) # Usar el índice del DataFrame como iid para facilitar la referencia

    def aplicar_filtro_busqueda(self, event=None):
        """Aplica el filtro por número de documento del docente."""
        doc_num = self.search_doc_entry.get().strip()
        filtered_df = self.current_day_schedule_df.copy()

        if doc_num:
            # Limpiar el número de documento para la comparación
            filtered_df['nroidenti_limpio'] = filtered_df['nroidenti'].apply(limpiar_numero_documento)
            filtered_df = filtered_df[filtered_df['nroidenti_limpio'].str.contains(limpiar_numero_documento(doc_num), case=False, na=False)]
            filtered_df = filtered_df.drop(columns=['nroidenti_limpio'])
        
        # Aplicar también los filtros de columna existentes
        for col, entry in self.filters.items():
            filter_val = entry.get().strip()
            if filter_val:
                if col in filtered_df.columns:
                    filtered_df = filtered_df[filtered_df[col].astype(str).str.contains(filter_val, case=False, na=False)]
        
        self.actualizar_tabla(filtered_df)

    def aplicar_filtros_columna(self, event=None):
        """Aplica los filtros por columna."""
        filtered_df = self.current_day_schedule_df.copy()
        
        # Aplicar filtro de búsqueda principal (docente)
        doc_num = self.search_doc_entry.get().strip()
        if doc_num:
            filtered_df['nroidenti_limpio'] = filtered_df['nroidenti'].apply(limpiar_numero_documento)
            filtered_df = filtered_df[filtered_df['nroidenti_limpio'].str.contains(limpiar_numero_documento(doc_num), case=False, na=False)]
            filtered_df = filtered_df.drop(columns=['nroidenti_limpio'])

        for col, entry in self.filters.items():
            filter_val = entry.get().strip()
            if filter_val:
                if col in filtered_df.columns: # Asegurarse de que la columna exista
                    filtered_df = filtered_df[filtered_df[col].astype(str).str.contains(filter_val, case=False, na=False)]
        self.actualizar_tabla(filtered_df)

    def limpiar_todos_los_filtros(self):
        """Limpia todos los filtros y recarga la tabla."""
        self.search_doc_entry.delete(0, tk.END)
        for entry in self.filters.values():
            entry.delete(0, tk.END)
        self.cargar_datos_vista() # Recargar la programación del día sin filtros

    def ordenar_columna(self, col):
        """Ordena la tabla por la columna especificada."""
        # Obtener los datos actuales de la tabla
        data = [(self.tree.set(child, col), child) for child in self.tree.get_children('')]
        
        # Determinar la dirección de ordenación
        if self._sort_column == col:
            self._sort_direction = "desc" if self._sort_direction == "asc" else "asc"
        else:
            self._sort_direction = "asc"
            self._sort_column = col

        # Función clave para la ordenación robusta
        def sort_key_robust(item_tuple):
            value = item_tuple[0]
            try:
                # Intentar convertir a float para números
                return (0, float(value)) # 0 para que los números se ordenen antes que las cadenas
            except (ValueError, TypeError):
                # Si no es un número, tratar como cadena
                return (1, str(value).lower()) # 1 para que las cadenas se ordenen después de los números

        # Ordenar los datos
        data.sort(key=sort_key_robust, reverse=(self._sort_direction == "desc"))

        # Reorganizar los elementos en el Treeview
        for index, (val, item) in enumerate(data):
            self.tree.move(item, '', index)

        # Actualizar el encabezado de la columna para mostrar la dirección de ordenación
        for c in self.tree["columns"]:
            text = self.tree.heading(c, "text")
            if c == col:
                arrow = " ↑" if self._sort_direction == "asc" else " ↓"
                # Eliminar flechas anteriores antes de añadir la nueva
                text = text.replace(" ↑", "").replace(" ↓", "")
                self.tree.heading(c, text=f"{text}{arrow}")
            else:
                self.tree.heading(c, text=text.replace(" ↑", "").replace(" ↓", ""))


    def mostrar_modal_llaves_prestadas(self):
        """Muestra un modal con las llaves prestadas hoy."""
        today = datetime.now().date()
        borrowed_keys_df = self.controller.obtener_registro_llaves_por_fecha(today)

        modal = tk.Toplevel(self)
        modal.title("Llaves Prestadas Hoy")
        modal.transient(self.master)
        modal.grab_set()

        if borrowed_keys_df.empty:
            tk.Label(modal, text="No hay llaves prestadas hoy.").pack(pady=20, padx=20)
        else:
            # Seleccionar y renombrar columnas para el modal
            display_cols = ['docente', 'nroidenti', 'salon', 'materia', 'horario', 'hora_entrega']
            # Asegurarse de que todas las columnas existan
            for col in display_cols:
                if col not in borrowed_keys_df.columns:
                    borrowed_keys_df[col] = ''
            
            modal_df = borrowed_keys_df[display_cols].copy()
            modal_df.rename(columns={
                'docente': 'Docente', 'nroidenti': 'Documento', 'salon': 'Salón',
                'materia': 'Materia', 'horario': 'Horario', 'hora_entrega': 'Hora Entrega'
            }, inplace=True)

            tree = ttk.Treeview(modal, columns=list(modal_df.columns), show="headings")
            tree.pack(fill="both", expand=True, padx=10, pady=10)

            for col in modal_df.columns:
                tree.heading(col, text=col)
                tree.column(col, width=100) # Ancho por defecto

            for index, row in modal_df.iterrows():
                tree.insert("", "end", values=list(row.values))

        ttk.Button(modal, text="Cerrar", command=modal.destroy).pack(pady=10)

    def registrar_entrega_llave(self):
        """Abre una ventana para registrar la entrega de una llave."""
        selected_item = self.tree.focus()
        if not selected_item:
            messagebox.showwarning("Selección", "Por favor, seleccione una clase de la tabla para registrar la entrega de llave.")
            return

        # Obtener los datos de la fila seleccionada
        # El iid del treeview es el índice del DataFrame
        selected_index = int(selected_item)
        
        if selected_index >= len(self.current_day_schedule_df):
            messagebox.showerror("Error", "Índice de fila no válido. Por favor, recargue la vista.")
            return

        selected_class = self.current_day_schedule_df.iloc[selected_index]

        # Crear una nueva ventana para el formulario de registro
        register_window = tk.Toplevel(self)
        register_window.title("Registrar Entrega de Llave")
        register_window.transient(self.master)
        register_window.grab_set()

        form_frame = ttk.Frame(register_window, padding="10")
        form_frame.pack(fill="both", expand=True)

        # Mostrar información de la clase seleccionada
        ttk.Label(form_frame, text=f"Docente: {selected_class.get('profesor', 'N/A')}").grid(row=0, column=0, columnspan=2, sticky="w", pady=2)
        ttk.Label(form_frame, text=f"Materia: {selected_class.get('materia', 'N/A')}").grid(row=1, column=0, columnspan=2, sticky="w", pady=2)
        ttk.Label(form_frame, text=f"Salón: {selected_class.get('aula', 'N/A')}").grid(row=2, column=0, columnspan=2, sticky="w", pady=2)
        ttk.Label(form_frame, text=f"Horario: {selected_class.get('horario', 'N/A')}").grid(row=3, column=0, columnspan=2, sticky="w", pady=2)
        ttk.Label(form_frame, text=f"Nro. Identificación: {selected_class.get('nroidenti', 'N/A')}").grid(row=4, column=0, columnspan=2, sticky="w", pady=2)

        # Campo para observaciones
        tk.Label(form_frame, text="Observaciones:").grid(row=5, column=0, sticky="w", pady=5)
        observations_entry = ttk.Entry(form_frame, width=40)
        observations_entry.grid(row=5, column=1, sticky="ew", pady=5)

        def save_delivery():
            delivery_data = {
                'dia': selected_class.get('dia', 'N/A'),
                'materia': selected_class.get('materia', 'N/A'),
                'salon': selected_class.get('aula', 'N/A'),
                'docente': selected_class.get('profesor', 'N/A'),
                'nroidenti': selected_class.get('nroidenti', 'N/A'),
                'horario': selected_class.get('horario', 'N/A'),
                'observaciones': observations_entry.get().strip()
            }
            if self.controller.registrar_entrega_llave(delivery_data):
                register_window.destroy()
                self.cargar_datos_vista() # Recargar la tabla principal
            

        ttk.Button(form_frame, text="Confirmar Entrega", command=save_delivery).grid(row=6, column=0, columnspan=2, pady=10)

