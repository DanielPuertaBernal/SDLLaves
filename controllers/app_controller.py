import tkinter as tk
from tkinter import messagebox
from models.schedule_model import ScheduleModel
from models.key_log_model import KeyLogModel
from views.key_delivery_view import KeyDeliveryView
from views.delivery_log_view import DeliveryLogView
from views.schedule_view import ScheduleView
import os
import pandas as pd # Necesario para pd.NaT en add_key_delivery

class AppController:
    """
    Controlador principal de la aplicación.
    Coordina la interacción entre el modelo y las vistas.
    """
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Gestión de Llaves")
        self.root.geometry("1200x700") # Tamaño inicial de la ventana

        # Inicializar Modelos
        self.schedule_model = ScheduleModel()
        self.key_log_model = KeyLogModel()

        # Inicializar Vistas
        self.views = {
            "entrega": KeyDeliveryView(self.root, self),
            "registro": DeliveryLogView(self.root, self),
            "programacion": ScheduleView(self.root, self)
        }

        # Mostrar la vista inicial
        self.current_view = None
        self.mostrar_vista("entrega")

    def mostrar_vista(self, view_name):
        """Muestra la vista especificada y oculta la actual."""
        if self.current_view:
            self.current_view.hide()
        
        view = self.views.get(view_name)
        if view:
            self.current_view = view
            self.current_view.show()
            # Cargar datos de la vista cuando se muestra (después de que los widgets estén creados)
            self.current_view.cargar_datos_vista()
        else:
            messagebox.showerror("Error", f"Vista '{view_name}' no encontrada.")

    # Métodos para interactuar con ScheduleModel
    def cargar_y_limpiar_programacion(self, file_path):
        return self.schedule_model.cargar_y_limpiar_programacion(file_path)

    def obtener_programacion_diaria(self, day):
        return self.schedule_model.obtener_programacion_diaria(day)

    def obtener_programacion_completa(self):
        return self.schedule_model.obtener_programacion_completa()

    def exportar_programacion(self, df, path):
        self.schedule_model.exportar_programacion(df, path)

    # Métodos para interactuar con KeyLogModel
    def registrar_entrega_llave(self, data):
        return self.key_log_model.registrar_entrega(data)

    def registrar_devolucion(self, nroidenti):
        return self.key_log_model.registrar_devolucion(nroidenti)

    def obtener_registro_llaves(self, filters=None, start_date=None, end_date=None):
        return self.key_log_model.obtener_registro_llaves(filters, start_date, end_date)

    def obtener_registro_llaves_por_fecha(self, date):
        return self.key_log_model.obtener_registro_llaves_por_fecha(date)

    def obtener_historial_completo(self):
        return self.key_log_model.obtener_historial_completo()

    def exportar_registro_llaves(self, df, path):
        self.key_log_model.exportar_registro_llaves(df, path)

