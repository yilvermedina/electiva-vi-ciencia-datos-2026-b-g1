"""
Semana 14 · Corte 3 · Análisis temporal y visualización · Nübe Coffee Lab

Autor: Yilver Medina Urrea · Electiva VI Ciencia de Datos · CORHUILA 2026-B

Parte de los datos limpios del mini-proyecto de la semana 10 (ventas_limpias.csv):
  1. Arma la serie temporal del ingreso por ventas (pesos COP).
  2. La agrega por periodo con resample: por día ('D') y por semana ('W-SUN').
  3. Calcula la media móvil de 7 días (rolling) para ver la tendencia.
  4. Mide la estacionalidad semanal (índice por día de la semana).
  5. Hace las 2 gráficas: evolución (línea) y comparación (barras).

Uso:  python analisis_temporal.py
"""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

AQUI = Path(__file__).parent
DATA = AQUI / "data"
GRAF = AQUI / "graficas"
RES = AQUI / "resultados"
GRAF.mkdir(exist_ok=True)
RES.mkdir(exist_ok=True)
pd.set_option("display.width", 120)

DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]


def titulo(t):
    print("\n" + "=" * 72 + f"\n{t}\n" + "=" * 72)


def millones(x, decimales=2):
    """1773348 -> '1,77' (formato colombiano: coma decimal)."""
    return f"{x / 1e6:.{decimales}f}".replace(".", ",")


# =========================================================== 1. SERIE TEMPORAL
titulo("1. Serie temporal: ingreso por ventas")
df = pd.read_csv(DATA / "ventas_limpias.csv", parse_dates=["fecha"])
cal = pd.read_csv(DATA / "calendario_clima.csv", parse_dates=["fecha"]).set_index("fecha")

df["ingreso"] = df["cantidad"] * df["precio_unitario"]          # pesos de cada línea
ventas = df.set_index("fecha").sort_index()                     # índice de fechas -> serie temporal
print(f"{len(df):,} líneas de venta · del {ventas.index.min():%d/%m/%Y} al {ventas.index.max():%d/%m/%Y}")

# =========================================================== 2. RESAMPLE
titulo("2. Agregación por periodo con resample")
diario = pd.DataFrame({
    "ingreso": ventas["ingreso"].resample("D").sum(),           # pesos por día
    "tickets": ventas["id_venta"].resample("D").nunique(),      # ventas (tickets) por día
})
diario["ticket_promedio"] = (diario["ingreso"] / diario["tickets"]).round(0)
diario = diario.join(cal[["dia_semana", "es_festivo", "lluvia_mm"]])
print(f"Días en la serie: {len(diario)} · días sin ventas: {(diario['ingreso'] == 0).sum()}")

semanal = ventas["ingreso"].resample("W-SUN").sum().to_frame("ingreso")   # semana de lunes a domingo
semanal["festivos"] = diario["es_festivo"].resample("W-SUN").sum()
semanal["semana"] = [f"{(d - pd.Timedelta(days=6)):%d/%m} – {d:%d/%m}" for d in semanal.index]
print("\nIngreso por semana (millones COP):")
print(semanal.assign(millones=(semanal["ingreso"] / 1e6).round(2))[["semana", "millones", "festivos"]]
      .to_string(index=False))

# =========================================================== 3. MEDIA MÓVIL
titulo("3. Media móvil de 7 días (tendencia)")
# 7 días = una semana completa: cada valor promedia un lunes, un martes, ..., un domingo,
# así se cancela el efecto del día de la semana y queda la tendencia.
diario["media_movil_7d"] = diario["ingreso"].rolling(window=7).mean()   # los 6 primeros días quedan NaN
mm = diario["media_movil_7d"].dropna()
print(f"Media móvil: primer valor {millones(mm.iloc[0])} M (09/08) · último {millones(mm.iloc[-1])} M (27/09)")
print(f"Media móvil: mínimo {millones(mm.min())} M · máximo {millones(mm.max())} M")

# Pendiente de la tendencia: recta sobre los totales semanales
x = np.arange(len(semanal))
pend_todas = np.polyfit(x, semanal["ingreso"], 1)[0]
sin_fest = semanal[semanal["festivos"] == 0]
pend_sin = np.polyfit(np.arange(len(sin_fest)), sin_fest["ingreso"], 1)[0]
print(f"Pendiente semanal (8 semanas):          {pend_todas / semanal['ingreso'].mean():+.1%} por semana")
print(f"Pendiente semanal (sin las 2 con festivo): {pend_sin / sin_fest['ingreso'].mean():+.1%} por semana")
print(f"Promedio semanas con festivo: {millones(semanal.loc[semanal['festivos'] > 0, 'ingreso'].mean())} M · "
      f"sin festivo: {millones(sin_fest['ingreso'].mean())} M")

# =========================================================== 4. ESTACIONALIDAD
titulo("4. Estacionalidad semanal (sin festivos)")
normales = diario[diario["es_festivo"] == 0]                     # el festivo es otro tipo de día
por_dia = (normales.groupby(normales.index.dayofweek)["ingreso"].mean()
           .rename(index=dict(enumerate(DIAS))).to_frame("ingreso_promedio"))
promedio_dia = normales["ingreso"].mean()
por_dia["indice_estacional"] = (por_dia["ingreso_promedio"] / promedio_dia).round(2)
print(por_dia.assign(millones=(por_dia["ingreso_promedio"] / 1e6).round(2))[["millones", "indice_estacional"]])
sab, mar = por_dia.loc["sábado", "ingreso_promedio"], por_dia.loc["martes", "ingreso_promedio"]
print(f"\nSábado vs. martes: {sab / mar - 1:+.0%}")
print(f"Festivos: {', '.join(f'{d:%d/%m} ({millones(v)} M)' for d, v in diario.loc[diario['es_festivo'] == 1, 'ingreso'].items())}"
      f" · día normal promedio: {millones(promedio_dia)} M")

# Guardar resultados
diario.to_csv(RES / "serie_diaria.csv", date_format="%Y-%m-%d")
semanal.to_csv(RES / "serie_semanal.csv", date_format="%Y-%m-%d")
por_dia.to_csv(RES / "estacionalidad_dia_semana.csv")

# =========================================================== 5. GRÁFICAS
titulo("5. Gráficas")
TINTA, TINTA_2, TINTA_3 = "#0b0b0b", "#52514e", "#8a8984"
AZUL, GRIS, REJILLA = "#2a78d6", "#a8a7a2", "#e6e5e1"
plt.rcParams.update({
    "font.family": ["Inter", "DejaVu Sans"], "font.size": 11,
    "axes.edgecolor": TINTA_3, "axes.labelcolor": TINTA_2,
    "xtick.color": TINTA_2, "ytick.color": TINTA_2,
    "axes.spines.top": False, "axes.spines.right": False,
    "figure.facecolor": "white", "axes.facecolor": "white",
})
fmt_millones = FuncFormatter(lambda v, _: f"\\${v / 1e6:.1f}".replace(".", ",") + " M")   # \$ = signo $ literal en matplotlib


def encabezado(fig, titulo_, subtitulo):
    fig.text(0.012, 0.965, titulo_, fontsize=15, fontweight="bold", color=TINTA, va="top")
    fig.text(0.012, 0.905, subtitulo, fontsize=10.5, color=TINTA_2, va="top")
    fig.text(0.012, 0.02, "Fuente: POS de Nübe Coffee Lab (datos simulados, limpios en la semana 10). "
             "Ingreso = cantidad × precio, en pesos colombianos.", fontsize=8.5, color=TINTA_3)


# ---- Gráfica 1 · EVOLUCIÓN: ingreso diario + media móvil de 7 días
fig, ax = plt.subplots(figsize=(11, 5.6))
fig.subplots_adjust(left=0.085, right=0.86, top=0.80, bottom=0.13)
ax.plot(diario.index, diario["ingreso"], color=GRIS, lw=1.3, marker="o", ms=3.5, zorder=2)
ax.plot(diario.index, diario["media_movil_7d"], color=AZUL, lw=2.8, zorder=3)
ax.set_ylim(0, 2.9e6)                                            # eje desde cero: no exagera la caída
ax.yaxis.set_major_formatter(fmt_millones)
ax.set_ylabel("Ingreso por día (millones COP)")
ax.grid(axis="y", color=REJILLA, lw=0.8)
ax.set_axisbelow(True)
ax.set_xlim(diario.index.min() - pd.Timedelta(days=1), diario.index.max() + pd.Timedelta(days=1))
semanas = pd.date_range("2026-08-03", "2026-09-28", freq="W-MON")
ax.set_xticks(semanas)
ax.set_xticklabels([f"lun {d:%d}\n{d:%b}".replace("Aug", "ago").replace("Sep", "sep") for d in semanas])
# etiquetas directas (además de la leyenda)
ult = diario.index.max()
ax.annotate("Media móvil\n7 días", (ult, diario.loc[ult, "media_movil_7d"]), xytext=(10, 2),
            textcoords="offset points", color=AZUL, fontsize=10, fontweight="bold", va="center")
ax.annotate("Ingreso\ndiario", (ult, diario.loc[ult, "ingreso"]), xytext=(10, 20),
            textcoords="offset points", color=TINTA_2, fontsize=10, va="center")
for f, v in diario.loc[diario["es_festivo"] == 1, "ingreso"].items():   # marcar los festivos
    ax.axvline(f, color=TINTA_3, lw=0.9, ls=(0, (2, 3)), zorder=1)
    ax.scatter([f], [v], s=70, facecolor="white", edgecolor=TINTA, linewidth=1.6, zorder=4)
    ax.text(f, 2.78e6, f"Festivo {f:%d/%m}", ha="center", fontsize=9, color=TINTA_2,
            bbox=dict(facecolor="white", edgecolor="none", pad=1.5))
ax.legend(["Ingreso diario", "Media móvil 7 días"], loc="lower left", frameon=False, ncol=2, fontsize=9.5)
encabezado(fig, "Las ventas no crecen: la media móvil de 7 días se queda plana, alrededor de \\$1,8 M por día",
           "Ingreso diario de los dos puntos, 3 ago – 27 sep 2026. Los picos son sábados y festivos; "
           "la media móvil los suaviza.")
fig.savefig(GRAF / "01_evolucion_ventas.png", dpi=150)
plt.close(fig)

# ---- Gráfica 2 · COMPARACIÓN: ingreso promedio por día de la semana
fig, ax = plt.subplots(figsize=(11, 5.6))
fig.subplots_adjust(left=0.085, right=0.97, top=0.80, bottom=0.13)
colores = [AZUL if d in ("sábado", "domingo") else GRIS for d in por_dia.index]
barras = ax.bar(por_dia.index.str.capitalize(), por_dia["ingreso_promedio"], color=colores,
                width=0.62, edgecolor="white", linewidth=2, zorder=3)
ax.set_ylim(0, 2.6e6)                                            # barras: el eje SIEMPRE empieza en cero
ax.yaxis.set_major_formatter(fmt_millones)
ax.set_ylabel("Ingreso promedio por día (millones COP)")
ax.grid(axis="y", color=REJILLA, lw=0.8)
ax.set_axisbelow(True)
ax.hlines(promedio_dia, -0.45, 6.45, color=TINTA_2, lw=1.2, ls=(0, (4, 3)), zorder=2)
ax.text(6.52, promedio_dia, f"Promedio\n\\${millones(promedio_dia)} M", va="center", ha="left",
        fontsize=9, color=TINTA_2)
for b, (dia, fila) in zip(barras, por_dia.iterrows()):
    ax.text(b.get_x() + b.get_width() / 2, fila["ingreso_promedio"] + 45_000,
            f"\\${millones(fila['ingreso_promedio'])} M", ha="center", fontsize=9.5, zorder=5,
            color=TINTA, fontweight="bold" if dia in ("sábado", "martes") else "normal",
            bbox=dict(facecolor="white", edgecolor="none", pad=1.5))
ax.set_xlim(-0.6, 7.25)
encabezado(fig, f"El sábado vende {sab / mar - 1:.0%} más que el martes: la estacionalidad es semanal".replace("%", " %"),
           "Ingreso promedio por día de la semana, sin contar los 2 festivos. Azul = fin de semana; "
           "línea punteada = promedio de un día normal.")
fig.savefig(GRAF / "02_ventas_por_dia_semana.png", dpi=150)
plt.close(fig)
print("Guardadas graficas/01_evolucion_ventas.png y graficas/02_ventas_por_dia_semana.png")
