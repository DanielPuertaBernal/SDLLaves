import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
from datetime import datetime
from views.base_view import BaseView # Importar la clase base
from utils.data_helpers import limpiar_numero_documento # Importar función auxiliar

class DeliveryLogView(BaseView):
    """Vista para el registro de entrega de llaves."""
    def __init__(self, parent, controller):
        # Inicializar atributos antes de llamar a super().__init__()
        self.tree = None
        self.filters = {} 
        self.start_date_entry = None
        self.end_date_entry = None
        self.current_key_log_df = pd.DataFrame() # DataFrame para el log actual
        self._sort_direction = "asc" # Dirección de ordenación inicial
        self._sort_column = None # Columna actualmente ordenada

        super().__init__(parent, controller, "Registro de Entrega de Llaves")

    def create_widgets(self):
        super().create_widgets()

        # Marco de filtros
        filter_frame = ttk.LabelFrame(self, text="Filtros de Registro")
        filter_frame.pack(pady=10, padx=10, fill="x")

        # Filtros por columna
        filter_cols = ["fecha_entrega", "fecha_devolucion", "dia", "materia", "salon", "docente", "estado"]
        for i, col in enumerate(filter_cols):
            row = i // 4
            col_pos = i % 4 * 2
            tk.Label(filter_frame, text=col.replace("_", " ").title() + ":").grid(row=row, column=col_pos, padx=5, pady=2, sticky="w")
            entry = ttk.Entry(filter_frame, width=15)
            entry.grid(row=row, column=col_pos + 1, padx=5, pady=2, sticky="ew")
            entry.bind("<KeyRelease>", self.aplicar_filtros)
            self.filters[col] = entry

        # Filtro por rango de fechas
        tk.Label(filter_frame, text="Fecha Inicio (YYYY-MM-DD):").grid(row=row + 1, column=0, padx=5, pady=2, sticky="w")
        self.start_date_entry = ttk.Entry(filter_frame, width=15)
        self.start_date_entry.grid(row=row + 1, column=1, padx=5, pady=2, sticky="ew")

        tk.Label(filter_frame, text="Fecha Fin (YYYY-MM-DD):").grid(row=row + 1, column=2, padx=5, pady=2, sticky="w")
        self.end_date_entry = ttk.Entry(filter_frame, width=15)
        self.end_date_entry.grid(row=row + 1, column=3, padx=5, pady=2, sticky="ew")

        ttk.Button(filter_frame, text="Aplicar Filtros", command=self.aplicar_filtros).grid(row=row + 2, column=0, columnspan=2, pady=5)
        ttk.Button(filter_frame, text="Limpiar Filtros", command=self.limpiar_filtros).grid(row=row + 2, column=2, columnspan=2, pady=5)

        # Marco de la tabla
        table_frame = ttk.Frame(self)
        table_frame.pack(pady=10, padx=10, fill="both", expand=True)

        columns = ("fecha_entrega", "hora_entrega", "fecha_devolucion", "hora_devolucion", "dia", "materia", "salon", "docente", "estado", "nroidenti")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        self.tree.pack(side="left", fill="both", expand=True)

        for col in columns:
            self.tree.heading(col, text=col.replace("_", " ").title(), command=lambda c=col: self.ordenar_columna(c))
            self.tree.column(col, width=100) # Ancho por defecto

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Botones de exportación
        export_frame = ttk.Frame(self)
        export_frame.pack(pady=10, padx=10, fill="x")

        ttk.Button(export_frame, text="Exportar Todo a Excel", command=lambda: self.exportar_registro("all")).pack(side=tk.LEFT, padx=5)
        ttk.Button(export_frame, text="Exportar por Rango de Fechas", command=lambda: self.exportar_registro("range")).pack(side=tk.LEFT, padx=5)
        ttk.Button(export_frame, text="Exportar por Fecha Específica", command=lambda: self.exportar_registro("specific")).pack(side=tk.LEFT, padx=5)
        ttk.Button(export_frame, text="Marcar como Devuelto", command=self.marcar_como_devuelto).pack(side=tk.RIGHT, padx=5)

    def cargar_datos_vista(self):
        """Carga y muestra el registro completo de llaves."""
        self.current_key_log_df = self.controller.obtener_historial_completo()
        self.actualizar_tabla(self.current_key_log_df)

    def actualizar_tabla(self, df):
        """Actualiza la tabla con los datos del DataFrame."""
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        if df.empty:
            return

        for index, row in df.iterrows():
            # Formatear fechas para mostrar solo la fecha si la hora es 00:00:00
            fecha_entrega_str = row['fecha_entrega'] if pd.notna(row['fecha_entrega']) else ""
            hora_entrega_str = row['hora_entrega'] if pd.notna(row['hora_entrega']) else ""
            fecha_devolucion_str = row['fecha_devolucion'] if pd.notna(row['fecha_devolucion']) else ""
            hora_devolucion_str = row['hora_devolucion'] if pd.notna(row['hora_devolucion']) else ""

            self.tree.insert("", "end", values=(
                fecha_entrega_str, hora_entrega_str, fecha_devolucion_str, hora_devolucion_str,
                row["dia"], row["materia"], row["salon"], row["docente"], row["estado"],
                row["nroidenti"]
            ), iid=index) # Usar el índice del DataFrame como iid

    def aplicar_filtros(self, event=None):
        """Aplica los filtros de columna y rango de fechas."""
        current_filters = {col: entry.get().strip() for col, entry in self.filters.items()}
        
        start_date_str = self.start_date_entry.get().strip()
        end_date_str = self.end_date_entry.get().strip()

        start_date = None
        end_date = None

        try:
            if start_date_str:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            if end_date_str:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d') + pd.Timedelta(days=1, microseconds=-1) # Incluir todo el día
        except ValueError:
            messagebox.showerror("Error de Fecha", "Formato de fecha inválido. Use YYYY-MM-DD.")
            return

        filtered_df = self.controller.obtener_registro_llaves(current_filters, start_date, end_date)
        self.actualizar_tabla(filtered_df)

    def limpiar_filtros(self):
        """Limpia todos los filtros y recarga la tabla."""
        for entry in self.filters.values():
            entry.delete(0, tk.END)
        self.start_date_entry.delete(0, tk.END)
        self.end_date_entry.delete(0, tk.END)
        self.cargar_datos_vista()

    def ordenar_columna(self, col):
        """Ordena la tabla por la columna especificada."""
        # Obtener los datos actuales de la tabla
        data = [(self.tree.set(child, col), child) for child in self.tree.get_children('')]
        
        # Determinar si es un tipo numérico o fecha para ordenar correctamente
        try:
            if 'fecha' in col:
                data.sort(key=lambda t: datetime.strptime(t[0], '%Y-%m-%d %H:%M') if t[0] else datetime.min)
            elif 'nroidenti' in col: # Asumiendo que nroidenti es numérico
                data.sort(key=lambda t: int(t[0]) if t[0].isdigit() else t[0])
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

    def exportar_registro(self, export_type):
        """Exporta el registro de llaves según el tipo especificado."""
        df_to_export = pd.DataFrame()

        if export_type == "all":
            df_to_export = self.controller.obtener_historial_completo()
        elif export_type == "range":
            start_date_str = self.start_date_entry.get().strip()
            end_date_str = self.end_date_entry.get().strip()
            start_date = None
            end_date = None
            try:
                if start_date_str:
                    start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
                if end_date_str:
                    end_date = datetime.strptime(end_date_str, '%Y-%m-%d') + pd.Timedelta(days=1, microseconds=-1)
            except ValueError:
                messagebox.showerror("Error de Fecha", "Formato de fecha inválido para el rango. Use YYYY-MM-DD.")
                return
            df_to_export = self.controller.obtener_registro_llaves(start_date=start_date, end_date=end_date)
        elif export_type == "specific":
            date_str = self.start_date_entry.get().strip() # Usar el campo de fecha inicio para fecha específica
            if not date_str:
                messagebox.showwarning("Fecha Requerida", "Por favor, ingrese una fecha en el campo 'Fecha Inicio' para exportar por fecha específica.")
                return
            try:
                specific_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                df_to_export = self.controller.obtener_registro_llaves_por_fecha(specific_date)
            except ValueError:
                messagebox.showerror("Error de Fecha", "Formato de fecha inválido. Use YYYY-MM-DD.")
                return
        
        if df_to_export.empty:
            messagebox.showinfo("Exportación", "No hay datos para exportar con los filtros aplicados.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Archivos Excel", "*.xlsx")],
            title="Guardar Registro de Entrega"
        )
        if file_path:
            self.controller.exportar_registro_llaves(df_to_export, file_path)

    def marcar_como_devuelto(self):
        """Marca la llave seleccionada como devuelta."""
        selected_item = self.tree.focus()
        if not selected_item:
            messagebox.showwarning("Selección", "Por favor, seleccione un registro de la tabla para marcar como devuelto.")
            return
        
        # Obtener el índice del DataFrame original
        selected_index = int(selected_item)
        
        # Asegurarse de que el índice es válido para el DataFrame actual
        if selected_index < len(self.current_key_log_df):
            # Obtener el registro original del DataFrame
            original_record = self.current_key_log_df.iloc[selected_index]
            
            if original_record['estado'] == 'Devuelta': # Cambiado de 'Entregado' a 'Devuelta'
                messagebox.showinfo("Estado Actual", "Esta llave ya ha sido marcada como 'Devuelta'.")
                return

            confirm = messagebox.askyesno("Confirmar Devolución", "¿Está seguro de que desea marcar esta llave como devuelta?")
            if confirm:
                # Actualizar el registro en el modelo
                # Necesitamos el nroidenti para la función de devolución
                nroidenti_docente = original_record['nroidenti']
                if self.controller.registrar_devolucion(nroidenti_docente):
                    self.cargar_datos_vista() # Recargar la tabla para reflejar el cambio
        else:
            messagebox.showerror("Error", "Índice de registro no válido. Por favor, recargue la vista.")

