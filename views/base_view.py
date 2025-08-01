import tkinter as tk
from tkinter import ttk

class BaseView(tk.Frame):
    """Clase base para las vistas."""
    def __init__(self, parent, controller, title):
        super().__init__(parent)
        self.controller = controller
        self.title = title
        self.create_widgets()

    def create_widgets(self):
        # Título de la vista
        tk.Label(self, text=self.title, font=("Helvetica", 16, "bold")).pack(pady=10)

        # Contenedor para botones de navegación
        nav_frame = ttk.Frame(self)
        nav_frame.pack(pady=5)

        ttk.Button(nav_frame, text="Entrega de Llaves", command=lambda: self.controller.mostrar_vista("entrega")).pack(side=tk.LEFT, padx=5)
        ttk.Button(nav_frame, text="Registro de Entrega", command=lambda: self.controller.mostrar_vista("registro")).pack(side=tk.LEFT, padx=5)
        ttk.Button(nav_frame, text="Programación", command=lambda: self.controller.mostrar_vista("programacion")).pack(side=tk.LEFT, padx=5)

    def show(self):
        self.pack(fill="both", expand=True)

    def hide(self):
        self.pack_forget()

    # Métodos placeholder para ser implementados por las subclases si necesitan recargar datos al mostrarse
    def cargar_datos_vista(self):
        pass

