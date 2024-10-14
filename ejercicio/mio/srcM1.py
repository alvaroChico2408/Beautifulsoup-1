'''
Created on 3 oct 2024

@author: alvaro
'''

# encoding:utf-8

from bs4 import BeautifulSoup
import urllib.request
from tkinter import *
from tkinter import messagebox
import sqlite3
import lxml
from datetime import datetime
# lineas para evitar error SSL
import os, ssl
if (not os.environ.get('PYTHONHTTPSVERIFY', '') and
getattr(ssl, '_create_unverified_context', None)):
    ssl._create_default_https_context = ssl._create_unverified_context


def ventana_principal():
  
    raiz = Tk()

    menu = Menu(raiz)

    # DATOS
    menudatos = Menu(menu, tearoff=0)
    menudatos.add_command(label="Cargar", command=cargar)
    menudatos.add_command(label="Listar", command=listar_vinos_completo)
    menudatos.add_command(label="Salir", command=raiz.quit)
    menu.add_cascade(label="Datos", menu=menudatos)

    # BUSCAR
    menubuscar = Menu(menu, tearoff=0)
    menubuscar.add_command(label="Denominación", command=buscar_denominacion)
    menubuscar.add_command(label="Fecha", command=raiz.quit)
    menubuscar.add_command(label="Géneros", command=raiz.quit)
    menu.add_cascade(label="Buscar", menu=menubuscar)

    raiz.config(menu=menu)

    raiz.mainloop()


def cargar():
    respuesta = messagebox.askyesno(title="Confirmar", message="Esta seguro que quiere recargar los datos. \nEsta operación puede ser lenta")
    if respuesta:
        almacenar_bd()


def obtener_vinos_páginas():
    lista = []
    
    for pag in range(0, 3):
        url = f'https://www.vinissimus.com/es/vinos/tinto/?cursor={pag*36}' 
        f = urllib.request.urlopen(url)
        vinos = BeautifulSoup(f, "lxml")
        lista_una_pagina = vinos.find_all("div", class_="product-list-item")
        lista.extend(lista_una_pagina)
    
    return lista
       

def almacenar_bd():

    conn = sqlite3.connect('vinos.db')
    conn.text_factory = str
    conn.execute("DROP TABLE IF EXISTS VINO")
    conn.execute("DROP TABLE IF EXISTS UVAS")
    conn.execute('''CREATE TABLE VINO
       (NOMBRE            TEXT NOT NULL,
        PRECIO        REAL        ,
        DENOMINACION      TEXT,
        BODEGA            TEXT,          
        UVAS         TEXT);''')
    conn.execute('''CREATE TABLE UVAS
       (NOMBRE            TEXT NOT NULL);''')
    
    tipos_uva = set()
    lista_vinos = obtener_vinos_páginas()
    for vino in lista_vinos:
        datos = vino.find("div", class_="details")
        nombre = datos.find("h2", class_="title heading").string.strip()
        precio = vino.find("p", class_="dto small")
        if precio is not None:
            precio = list(precio.stripped_strings)[0]
        else:
            precio = list(vino.find("p", class_="price uniq small").stripped_strings)[0]
        denominacion = datos.find("div", class_="region").string.strip()
        bodega = datos.find("div", class_="cellar-name").string.strip()
        uvas = "".join(datos.find("div", class_=["tags"]).stripped_strings)
        for uva in uvas.split("/"):
            tipos_uva.add(uva.strip())
        
        conn.execute("""INSERT INTO VINO (NOMBRE, PRECIO, DENOMINACION, BODEGA, UVAS) VALUES (?,?,?,?,?)""",
                     (nombre, float(precio.replace(',', '.')), denominacion, bodega, uvas))
    conn.commit()
    
    for u in list(tipos_uva):
        conn.execute("""INSERT INTO UVAS (NOMBRE) VALUES (?)""",
                     (u,))
    conn.commit()
    
    cursor = conn.execute("SELECT COUNT(*) FROM VINO")
    cursor1 = conn.execute("SELECT COUNT(*) FROM UVAS")
    messagebox.showinfo("Base Datos",
                        "Base de datos creada correctamente \nHay " + str(cursor.fetchone()[0]) + " vinos y "
                        +str(cursor1.fetchone()[0]) + " tipos de uvas")
    conn.close()


def listar_vinos_completo():
            conn = sqlite3.connect('vinos.db')
            conn.text_factory = str
            cursor = conn.execute("SELECT NOMBRE, PRECIO, BODEGA, DENOMINACION FROM VINO")
            conn.close
            formato_vinos(cursor)

            
def formato_vinos(cursor): 
    v = Toplevel()
    sc = Scrollbar(v)
    sc.pack(side=RIGHT, fill=Y)
    lb = Listbox(v, width=150, yscrollcommand=sc.set)
    for row in cursor:
        s = 'VINO: ' + row[0]
        lb.insert(END, s)
        lb.insert(END, "------------------------------------------------------------------------")
        s = "     PRECIO: " + str(row[1]) + ' | BODEGA: ' + row[2] + ' | DENOMINACION: ' + str(row[3])
        lb.insert(END, s)
        lb.insert(END, "\n\n")
    lb.pack(side=LEFT, fill=BOTH)
    sc.config(command=lb.yview)
    
    
    
def buscar_denominacion():

    def lista(event):
            conn = sqlite3.connect('vinos.db')
            conn.text_factory = str
            cursor = conn.execute("SELECT NOMBRE, PRECIO, BODEGA, DENOMINACION FROM VINO WHERE DENOMINACION = '" + sb.get() + "'")
            conn.close
            formato_vinos(cursor)
    
    conn = sqlite3.connect('vinos.db')
    conn.text_factory = str
    cursor = conn.execute("SELECT DISTINCT DENOMINACION FROM VINO")
    
    denominaciones = [i[0] for i in cursor]
        
    v = Toplevel()
    sb = Spinbox(v, values=denominaciones)
    sb.bind("<Return>", lista)
    sb.pack()
    
    conn.close()
  

if __name__ == '__main__':
    ventana_principal()
