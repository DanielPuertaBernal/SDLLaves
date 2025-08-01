import pandas as pd
from tkinter import ttk

def limpiar_numero_documento(doc):
    """
    Limpia un número de documento, eliminando '.0' y '_x000D_' si existen.
    """
    doc_str = str(doc).replace('_x000D_', '').strip() # Eliminar _x000D_ primero
    if doc_str.endswith('.0'):
        return doc_str[:-2]
    return doc_str

def limpiar_texto_excel(text):
    """
    Elimina el artefacto '_x000D_' de las cadenas de texto.
    """
    if pd.isna(text):
        return ''
    return str(text).replace('_x000D_', '').strip()

def aplicar_estilo(root):
    """Aplica un estilo básico a la aplicación Tkinter."""
    style = ttk.Style(root)
    style.theme_use('clam') # Puedes probar otros: 'clam', 'alt', 'default', 'classic', 'vista', 'xpnative'

    # Colores base
    primary_color = "#4CAF50"  # Verde
    accent_color = "#FFC107"   # Ámbar
    text_color = "#333333"
    bg_color = "#f0f0f0"
    frame_bg_color = "#ffffff"

    # Configurar estilo para el frame principal
    style.configure('TFrame', background=bg_color)
    style.configure('TLabelframe', background=frame_bg_color, relief="flat", borderwidth=1,
                    font=('Segoe UI', 10, 'bold'))
    style.configure('TLabelframe.Label', foreground=primary_color)

    # Botones
    style.configure('TButton',
                    font=('Segoe UI', 10, 'bold'),
                    background=primary_color,
                    foreground='white',
                    relief="flat",
                    padding=8,
                    borderwidth=0)
    style.map('TButton',
              background=[('active', '#5cb85c'), ('pressed', '#449d44')],
              foreground=[('active', 'white'), ('pressed', 'white')])

    style.configure('Accent.TButton',
                    background=accent_color,
                    foreground='white')
    style.map('Accent.TButton',
              background=[('active', '#ffca28'), ('pressed', '#ffb300')],
              foreground=[('active', 'white'), ('pressed', 'white')])

    # Etiquetas
    style.configure('TLabel', background=frame_bg_color, foreground=text_color, font=('Segoe UI', 10))
    style.configure('Heading.TLabel', font=('Segoe UI', 18, 'bold'), foreground=primary_color, background=bg_color)

    # Entradas de texto
    style.configure('TEntry', fieldbackground='white', foreground=text_color, font=('Segoe UI', 10))

    # Combobox
    style.configure('TCombobox', fieldbackground='white', foreground=text_color, font=('Segoe UI', 10))

    # Treeview (Tablas)
    style.configure('Treeview',
                    background='white',
                    foreground=text_color,
                    fieldbackground='white',
                    font=('Segoe UI', 9))
    style.configure('Treeview.Heading',
                    font=('Segoe UI', 10, 'bold'),
                    background='#e0e0e0',
                    foreground=text_color,
                    relief="flat")
    style.map('Treeview.Heading',
              background=[('selected', primary_color)],
              foreground=[('selected', 'white')])
