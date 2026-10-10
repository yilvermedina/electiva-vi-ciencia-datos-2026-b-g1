"""
Genera los datos simulados de Nübe Coffee Lab (caso del curso).

Autor: Yilver Medina Urrea · Electiva VI Ciencia de Datos · CORHUILA 2026-B

Los datos NO son reales: se simulan con una semilla fija (siempre salen iguales)
siguiendo el comportamiento descrito en el caso: 2 puntos de venta en Neiva,
más ventas los fines de semana y festivos, y más bebidas calientes y domicilios
los días de lluvia.

Uso:  python generar_datos.py      -> crea la carpeta data/ con 8 archivos CSV
"""
from pathlib import Path
import numpy as np
import pandas as pd

rng = np.random.default_rng(2026)
OUT = Path(__file__).parent / "data"
OUT.mkdir(exist_ok=True)

# ----------------------------------------------------------------- catálogos
punto_venta = pd.DataFrame({
    "id_punto": [1, 2],
    "nombre": ["Nübe Centro", "Nübe Altico"],
    "barrio": ["Centro", "El Altico"],
})

producto = pd.DataFrame({
    "id_producto": ["P01", "P02", "P03", "P04", "P05", "P06", "P07", "P08"],
    "nombre": ["Tinto", "Americano", "Capuchino", "Latte", "Chocolate caliente",
               "Frappé de café", "Croissant", "Croissant de almendras"],
    "categoria": ["Bebida caliente"] * 5 + ["Bebida fría", "Panadería", "Panadería"],
    "precio": [3000, 5000, 8500, 9000, 7500, 11000, 6000, 8000],
})

insumo = pd.DataFrame({
    "id_insumo": ["I01", "I02", "I03", "I04", "I05", "I06"],
    "nombre": ["Leche entera", "Café en grano", "Croissant congelado",
               "Chocolate en polvo", "Hielo", "Almendra fileteada"],
    "unidad": ["L", "kg", "und", "kg", "kg", "kg"],
    "costo_unitario": [4200, 60000, 2200, 32000, 1500, 50000],
})

# receta: cuánto insumo gasta una unidad de cada producto (tabla N:M)
receta = pd.DataFrame([
    ("P01", "I02", 0.010),
    ("P02", "I02", 0.018),
    ("P03", "I02", 0.018), ("P03", "I01", 0.150),
    ("P04", "I02", 0.018), ("P04", "I01", 0.220),
    ("P05", "I04", 0.030), ("P05", "I01", 0.250),
    ("P06", "I02", 0.018), ("P06", "I01", 0.150), ("P06", "I05", 0.200),
    ("P07", "I03", 1.000),
    ("P08", "I03", 1.000), ("P08", "I06", 0.015),
], columns=["id_producto", "id_insumo", "cantidad"])

nombres = ["Laura", "Andrés", "Camila", "Julián", "Valentina", "Sebastián", "Daniela",
           "Santiago", "Paula", "Mateo", "Juliana", "Felipe", "Natalia", "Diego", "Sofía",
           "Carlos", "María", "Jorge", "Ana", "Luis"]
apellidos = ["Perdomo", "Trujillo", "Cuéllar", "Polanía", "Vargas", "Rojas", "Cabrera",
             "Ramírez", "Losada", "Charry", "Silva", "Medina", "Quintero", "Ortiz"]
n_cli = 300
cliente = pd.DataFrame({
    "id_cliente": [f"C{i:03d}" for i in range(1, n_cli + 1)],
    "nombre": [f"{rng.choice(nombres)} {rng.choice(apellidos)}" for _ in range(n_cli)],
    "telefono": [f"31{rng.integers(0, 10)}{rng.integers(1000000, 9999999)}" for _ in range(n_cli)],
    "fecha_registro": pd.to_datetime("2025-06-01")
    + pd.to_timedelta(rng.integers(0, 400, n_cli), unit="D"),
})
cliente["fecha_registro"] = cliente["fecha_registro"].dt.date

# ----------------------------------------------------------------- calendario y clima
fechas = pd.date_range("2026-08-03", "2026-09-27", freq="D")  # 8 semanas completas
festivos = {pd.Timestamp("2026-08-07"), pd.Timestamp("2026-08-17")}
llueve = rng.random(len(fechas)) < 0.22
lluvia_mm = np.where(llueve, np.round(rng.gamma(2.0, 7.0, len(fechas)), 1), 0.0)
temp_max = np.round(rng.normal(34.5, 1.4, len(fechas)) - np.where(llueve, 2.5, 0), 1)
dias_es = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
calendario_clima = pd.DataFrame({
    "fecha": fechas.date,
    "dia_semana": [dias_es[d.weekday()] for d in fechas],
    "es_festivo": [int(d in festivos) for d in fechas],
    "temp_max_c": temp_max,
    "lluvia_mm": lluvia_mm,
})

# ----------------------------------------------------------------- ventas
factor_dia = [0.90, 0.95, 1.00, 1.00, 1.10, 1.35, 1.15]
base_punto = {1: 75, 2: 55}
horas = np.arange(6, 21)                       # abre 6 a. m., cierra 9 p. m.
peso_hora = np.array([3, 10, 12, 11, 9, 6, 5, 5, 4, 6, 7, 6, 4, 3, 2], float)
peso_hora /= peso_hora.sum()
precios = dict(zip(producto.id_producto, producto.precio))

ventas, detalle = [], []
id_venta = 1
for _, dia in calendario_clima.iterrows():
    f = pd.Timestamp(dia.fecha)
    lluvia = dia.lluvia_mm > 0
    for punto, base in base_punto.items():
        lam = base * factor_dia[f.weekday()] * (1.30 if dia.es_festivo else 1) * (0.92 if lluvia else 1)
        for _ in range(rng.poisson(lam)):
            h = rng.choice(horas, p=peso_hora)
            hora = f"{h:02d}:{rng.integers(0, 60):02d}"
            canal = "Domicilio" if rng.random() < (0.35 if lluvia else 0.18) else "Mostrador"
            pago = rng.choice(["Efectivo", "Tarjeta", "Nequi"], p=[0.35, 0.30, 0.35])
            cli = rng.choice(cliente.id_cliente) if rng.random() < 0.40 else None
            ventas.append((id_venta, dia.fecha, hora, punto, cli, canal, pago))
            # productos del ticket (1 a 3 líneas distintas)
            p = np.array([0.16, 0.12, 0.17, 0.12, 0.07, 0.10, 0.17, 0.09])
            if lluvia:
                p *= [1.2, 1.1, 1.25, 1.2, 1.8, 0.4, 1.0, 1.0]
            if h < 11:
                p *= [1.3, 1.2, 1.1, 1.1, 1.0, 0.5, 1.4, 1.2]
            p /= p.sum()
            n_lin = rng.choice([1, 2, 3], p=[0.55, 0.35, 0.10])
            for prod in rng.choice(producto.id_producto, size=n_lin, replace=False, p=p):
                cant = int(rng.choice([1, 2, 3], p=[0.80, 0.16, 0.04]))
                detalle.append((id_venta, prod, cant, precios[prod]))
            id_venta += 1

venta = pd.DataFrame(ventas, columns=["id_venta", "fecha", "hora", "id_punto",
                                      "id_cliente", "canal", "medio_pago"])
detalle_venta = pd.DataFrame(detalle, columns=["id_venta", "id_producto",
                                               "cantidad", "precio_unitario"])

for nombre, df in [("punto_venta", punto_venta), ("cliente", cliente), ("producto", producto),
                   ("insumo", insumo), ("receta", receta), ("calendario_clima", calendario_clima),
                   ("venta", venta), ("detalle_venta", detalle_venta)]:
    df.to_csv(OUT / f"{nombre}.csv", index=False)
    print(f"{nombre:18s} {len(df):6d} filas")
