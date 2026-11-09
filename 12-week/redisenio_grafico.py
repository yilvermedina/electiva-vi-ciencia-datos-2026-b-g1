# Semana 12 - Redisenar un grafico
# Yilver Medina Urrea - Electiva VI Ciencia de Datos - CORHUILA 2026-B
#
# Datos: ventas limpias de Nube Coffee Lab (semana 10), 3 ago - 27 sep 2026
# Hace dos imagenes: antes.png (grafico mal hecho) y despues.png (rediseño)

import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("../10-week/datos_limpios/ventas_limpias.csv")
df["ingreso"] = df["cantidad"] * df["precio_unitario"]

# ingreso total por producto, de mayor a menor
por_producto = df.groupby("producto")["ingreso"].sum().sort_values(ascending=False)
porcentaje = por_producto / por_producto.sum() * 100
print(pd.DataFrame({"millones": (por_producto / 1e6).round(2), "%": porcentaje.round(1)}))
print("Top 3:", round(porcentaje.head(3).sum(), 1), "% del ingreso")

# ---------------- ANTES: torta con 8 partes, colores arcoiris y sin titulo claro
fig, ax = plt.subplots(figsize=(8, 6))
colores = plt.cm.rainbow([i / 7 for i in range(8)])
ax.pie(por_producto, labels=por_producto.index, autopct="%1.2f%%", colors=colores,
       explode=[0.08] * 8, shadow=True, startangle=20, textprops={"fontsize": 9})
ax.set_title("Ventas")
plt.savefig("antes.png", dpi=110)
plt.close()

# ---------------- DESPUES: barras horizontales ordenadas, eje desde 0 y color solo para lo importante
datos = por_producto.sort_values()                 # ascendente para que el mayor quede arriba
top3 = por_producto.head(3).index
colores = ["#6f4e37" if p in top3 else "#c9c4bd" for p in datos.index]

fig, ax = plt.subplots(figsize=(10, 5.5))
barras = ax.barh(datos.index, datos / 1e6, color=colores)
for barra, prod in zip(barras, datos.index):
    texto = f"${datos[prod] / 1e6:.1f} M  ({porcentaje[prod]:.0f} %)".replace(".", ",")
    ax.text(barra.get_width() + 0.3, barra.get_y() + barra.get_height() / 2, texto,
            va="center", fontsize=10)

ax.set_xlim(0, 26)                                  # el eje empieza en 0
ax.set_xlabel("Ingreso en millones de pesos (COP)")
ax.set_title("Capuchino, latte y croissant dejan más de la mitad del ingreso de Nübe",
             loc="left", fontsize=13, fontweight="bold", pad=26)
ax.text(0, 1.025, "Ingreso por producto, 3 ago - 27 sep 2026 (los 2 puntos de venta)",
        transform=ax.transAxes, fontsize=10, color="#555555")
ax.spines[["top", "right"]].set_visible(False)
ax.grid(axis="x", alpha=0.3)
ax.set_axisbelow(True)
plt.tight_layout()
plt.savefig("despues.png", dpi=130)
plt.close()
print("Guardados antes.png y despues.png")
