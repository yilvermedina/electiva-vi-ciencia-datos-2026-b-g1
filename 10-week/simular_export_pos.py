"""
Crea data/export_pos_crudo.csv: la planilla tal como la exportaría el POS de
Nübe Coffee Lab, CON los errores típicos de una planilla digitada por varias
personas (duplicados, vacíos, nombres mal escritos, fechas y precios en otro
formato). Es el dataset "sucio" que se limpia en mini_proyecto.py.

Autor: Yilver Medina Urrea · Electiva VI Ciencia de Datos · CORHUILA 2026-B

Parte de los datos simulados de la semana 7 (../07-week/data). Semilla fija.
Uso:  python simular_export_pos.py
"""
from pathlib import Path
import numpy as np
import pandas as pd

rng = np.random.default_rng(10)
AQUI = Path(__file__).parent
SRC = AQUI.parent / "07-week" / "data"

venta = pd.read_csv(SRC / "venta.csv")
detalle = pd.read_csv(SRC / "detalle_venta.csv")
producto = pd.read_csv(SRC / "producto.csv")
punto = pd.read_csv(SRC / "punto_venta.csv")

df = (detalle.merge(venta, on="id_venta")
             .merge(producto[["id_producto", "nombre"]], on="id_producto")
             .merge(punto[["id_punto", "nombre"]].rename(columns={"nombre": "punto"}), on="id_punto"))
df = df.rename(columns={"nombre": "producto"})[
    ["id_venta", "fecha", "hora", "punto", "canal", "producto", "cantidad",
     "precio_unitario", "medio_pago", "id_cliente"]].astype({"cantidad": object, "precio_unitario": object})
n = len(df)


def elegir(frac):
    return rng.random(n) < frac


# 1) nombres de producto mal escritos (mayúsculas, espacios, typos)
variantes = {
    "Capuchino": ["capuchino", " Capuchino ", "CAPUCHINO", "Capuccino"],
    "Croissant": ["croissant", "Croisant", "CROISSANT "],
    "Latte": ["latte", "Late", " LATTE"],
    "Tinto": ["tinto", "TINTO", "Tinto "],
    "Chocolate caliente": ["chocolate caliente", "Chocolate  caliente"],
    "Frappé de café": ["Frappe de cafe", "frappé de café"],
    "Americano": ["americano", "AMERICANO"],
    "Croissant de almendras": ["croissant de almendras", "Croissant almendras"],
}
m = elegir(0.15)
df.loc[m, "producto"] = [rng.choice(variantes[p]) for p in df.loc[m, "producto"]]

# 2) punto de venta escrito de varias formas
m = elegir(0.10)
df.loc[m, "punto"] = [rng.choice(["centro", "NUBE CENTRO", "Nube Centro "]) if "Centro" in p
                      else rng.choice(["altico", "Nübe El Altico", "NUBE ALTICO"]) for p in df.loc[m, "punto"]]

# 3) medio de pago en mayúsculas/minúsculas y algunos vacíos
m = elegir(0.08)
df.loc[m, "medio_pago"] = df.loc[m, "medio_pago"].str.upper()
df.loc[elegir(0.02), "medio_pago"] = np.nan

# 4) fechas en formato dd/mm/aaaa (otro cajero, otro formato)
m = elegir(0.12)
df.loc[m, "fecha"] = pd.to_datetime(df.loc[m, "fecha"]).dt.strftime("%d/%m/%Y")

# 5) precios con signo $ y punto de miles, y algunos vacíos
m = elegir(0.10)
df.loc[m, "precio_unitario"] = ["$" + f"{int(v):,}".replace(",", ".") for v in df.loc[m, "precio_unitario"]]
df.loc[elegir(0.02), "precio_unitario"] = np.nan

# 6) cantidad como texto "2 und", algunos vacíos y algunos en 0 (error de digitación)
m = elegir(0.05)
df.loc[m, "cantidad"] = [f"{int(v)} und" for v in df.loc[m, "cantidad"]]
df.loc[elegir(0.01), "cantidad"] = np.nan
df.loc[elegir(0.004), "cantidad"] = 0

# 7) filas duplicadas (el cajero exportó dos veces parte del turno)
dups = df.sample(frac=0.03, random_state=7)
df = pd.concat([df, dups]).sample(frac=1, random_state=3).reset_index(drop=True)

df.to_csv(AQUI / "data" / "export_pos_crudo.csv", index=False)
print("export_pos_crudo.csv:", df.shape)
