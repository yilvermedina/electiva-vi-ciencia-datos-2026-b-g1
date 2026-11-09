# Semana 13 - Boceto de dashboard de ventas de Nube Coffee Lab
# Yilver Medina Urrea - Electiva VI Ciencia de Datos - CORHUILA 2026-B
#
# Calcula los 3 KPIs con los datos limpios de la semana 10 y dibuja el boceto
# del tablero (boceto_dashboard.png) con datos reales para que se vea como quedaria.

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

D10 = "../10-week/"
ventas = pd.read_csv(D10 + "datos_limpios/ventas_limpias.csv", parse_dates=["fecha"])
producto = pd.read_csv(D10 + "data/producto.csv")
insumo = pd.read_csv(D10 + "data/insumo.csv")
receta = pd.read_csv(D10 + "data/receta.csv")

# costo de insumos de cada producto segun la receta
receta = receta.merge(insumo, on="id_insumo")
receta["costo"] = receta["cantidad"] * receta["costo_unitario"]
costo_producto = receta.groupby("id_producto")["costo"].sum()
producto["costo_unit"] = producto["id_producto"].map(costo_producto)

ventas = ventas.merge(producto[["nombre", "costo_unit"]], left_on="producto", right_on="nombre")
ventas["ingreso"] = ventas["cantidad"] * ventas["precio_unitario"]
ventas["costo"] = ventas["cantidad"] * ventas["costo_unit"]

# ---------------- KPIs por semana (lunes a domingo)
semanal = ventas.set_index("fecha").resample("W-SUN").agg(
    {"ingreso": "sum", "costo": "sum", "id_venta": "nunique"})
semanal["ticket"] = semanal["ingreso"] / semanal["id_venta"]
semanal["margen"] = (1 - semanal["costo"] / semanal["ingreso"]) * 100

META_INGRESO = 12_500_000   # pesos por semana
META_TICKET = 13_500        # pesos por venta
META_MARGEN = 75            # % sobre el costo de insumos

print(semanal[["ingreso", "id_venta", "ticket", "margen"]].round(1))
ult, ant = semanal.iloc[-1], semanal.iloc[-2]

# ticket por punto y canal, margen por producto
def ticket(grupo):
    return grupo["ingreso"].sum() / grupo["id_venta"].nunique()

ticket_punto = ventas.groupby("punto").apply(ticket)
ticket_canal = ventas.groupby("canal").apply(ticket)
ticket_seg = pd.concat([ticket_punto, ticket_canal])
margen_prod = ventas.groupby("producto")[["ingreso", "costo"]].sum()
margen_prod = ((1 - margen_prod["costo"] / margen_prod["ingreso"]) * 100).sort_values()
print("\nTicket por punto y canal:\n", ticket_seg.round(0))
print("\nMargen por producto:\n", margen_prod.round(1))

# ---------------- BOCETO
def pesos(x):
    return "$" + f"{x:,.0f}".replace(",", ".")

CAFE, GRIS, ROJO, VERDE = "#6f4e37", "#c9c4bd", "#c0392b", "#2e7d32"
fig = plt.figure(figsize=(14, 9.5))
fig.patch.set_facecolor("#f4f2ef")
fig.text(0.03, 0.955, "Nübe Coffee Lab · Tablero de ventas", fontsize=18, fontweight="bold")

# filtros
filtros = ["Fecha: 3 ago - 27 sep 2026  ▾", "Punto de venta: Todos  ▾", "Categoría / producto: Todos  ▾",
           "Canal: Todos  ▾"]
x = 0.03
for f in filtros:
    ancho = 0.012 + len(f) * 0.0072
    fig.patches.append(FancyBboxPatch((x, 0.885), ancho, 0.04, boxstyle="round,pad=0.004",
                                      transform=fig.transFigure, facecolor="white", edgecolor="#999999"))
    fig.text(x + 0.008, 0.905, f, fontsize=10, va="center")
    x += ancho + 0.015

# tarjetas de KPI
tarjetas = [
    ("Ingreso semanal", pesos(ult["ingreso"]), f"Meta: {pesos(META_INGRESO)}",
     ult["ingreso"] >= META_INGRESO, f"{ult['ingreso'] / ant['ingreso'] - 1:+.1%} vs semana anterior"),
    ("Ticket promedio", pesos(ult["ticket"]), f"Meta: {pesos(META_TICKET)}",
     ult["ticket"] >= META_TICKET, f"{ult['ticket'] / ant['ticket'] - 1:+.1%} vs semana anterior"),
    ("Margen sobre insumos", f"{ult['margen']:.1f} %", f"Meta: {META_MARGEN} %",
     ult["margen"] >= META_MARGEN, f"{ult['margen'] - ant['margen']:+.1f} puntos vs semana anterior"),
]
for i, (nombre, valor, meta, cumple, cambio) in enumerate(tarjetas):
    x0 = 0.03 + i * 0.32
    fig.patches.append(FancyBboxPatch((x0, 0.70), 0.30, 0.15, boxstyle="round,pad=0.005",
                                      transform=fig.transFigure, facecolor="white", edgecolor="#dddddd"))
    fig.text(x0 + 0.015, 0.825, nombre + " (última semana)", fontsize=11, color="#555555")
    fig.text(x0 + 0.015, 0.765, valor.replace(".", ",") if "%" in valor else valor,
             fontsize=24, fontweight="bold")
    estado = "Cumple" if cumple else "Por debajo"
    fig.text(x0 + 0.015, 0.725, f"{meta.replace('.', ',') if '%' in meta else meta}   ·   {estado}",
             fontsize=10, color=VERDE if cumple else ROJO)
    fig.text(x0 + 0.29, 0.775, cambio.replace(".", ","), fontsize=9, color="#777777", ha="right")

# grafico 1: ingreso semanal vs meta (KPI 1)
ax1 = fig.add_axes([0.06, 0.38, 0.88, 0.25])
etiquetas = [f"{d - pd.Timedelta(days=6):%d/%m}" for d in semanal.index]
ax1.plot(etiquetas, semanal["ingreso"] / 1e6, marker="o", color=CAFE, linewidth=2.2, label="Ingreso semanal")
ax1.axhline(META_INGRESO / 1e6, color=ROJO, linestyle="--", linewidth=1.3, label="Meta")
ax1.set_ylim(0, 16)
ax1.set_ylabel("Millones COP")
ax1.set_title("1. Ingreso semanal vs. meta (las semanas del 3/08 y 17/08 tuvieron festivo)",
              loc="left", fontsize=11)
ax1.legend(loc="lower right", fontsize=9)
ax1.grid(axis="y", alpha=0.3)

# grafico 2: ticket promedio por punto y canal (KPI 2)
ax2 = fig.add_axes([0.06, 0.06, 0.40, 0.24])
ax2.bar(ticket_seg.index, ticket_seg / 1000, color=[CAFE, CAFE, GRIS, GRIS], width=0.6)
ax2.axhline(META_TICKET / 1000, color=ROJO, linestyle="--", linewidth=1.3)
ax2.set_ylim(0, 15)
ax2.set_ylabel("Miles de pesos")
ax2.set_title("2. Ticket promedio por punto (café) y por canal (gris)", loc="left", fontsize=11)
ax2.grid(axis="y", alpha=0.3)

# grafico 3: margen por producto (KPI 3)
ax3 = fig.add_axes([0.62, 0.06, 0.34, 0.24])
ax3.barh(margen_prod.index, margen_prod,
         color=[ROJO if m < META_MARGEN else GRIS for m in margen_prod])
ax3.axvline(META_MARGEN, color=ROJO, linestyle="--", linewidth=1.3)
ax3.set_xlim(0, 100)
ax3.set_xlabel("% de margen sobre insumos")
ax3.set_title("3. Margen por producto (rojo = por debajo de la meta)", loc="left", fontsize=11)
ax3.tick_params(axis="y", labelsize=9)

for ax in (ax1, ax2, ax3):
    ax.spines[["top", "right"]].set_visible(False)

plt.savefig("boceto_dashboard.png", dpi=110, facecolor=fig.get_facecolor())
print("\nGuardado boceto_dashboard.png")
