import tkinter as tk
import os
from controllers.app_controller import AppController
from utils.data_helpers import aplicar_estilo # Importar la función de estilo

if __name__ == "__main__":
    # Crear el directorio 'data' si no existe
    if not os.path.exists("data"):
        os.makedirs("data")
    
    # Crear el directorio 'utils' si no existe (para data_helpers.py)
    if not os.path.exists("utils"):
        os.makedirs("utils")

    root = tk.Tk()
    aplicar_estilo(root) # Aplicar el estilo al root
    app = AppController(root)
    root.mainloop()
