# Semana 11 - Analisis de una serie de tiempo
# Yilver Medina Urrea - Electiva VI Ciencia de Datos - CORHUILA 2026-B
#
# Serie: temperatura minima diaria de Melbourne (1981-1990)
# Fuente: https://raw.githubusercontent.com/jbrownlee/Datasets/master/daily-min-temperatures.csv
# (datos del Australian Bureau of Meteorology)

import pandas as pd
import matplotlib.pyplot as plt

# 1. Cargar los datos con la fecha como indice
df = pd.read_csv("data/temperaturas_melbourne.csv", parse_dates=["Date"])
df = df.rename(columns={"Date": "fecha", "Temp": "temp_min"})
df = df.set_index("fecha")

print("Registros diarios:", len(df))
print("Desde", df.index.min().date(), "hasta", df.index.max().date())
print(df.head())

# 2. Agrupar por mes con resample (promedio de cada mes)
mensual = df["temp_min"].resample("ME").mean()
print("\nMeses:", len(mensual))
print(mensual.head(12).round(1))

# media movil de 12 meses: cada punto es el promedio del ultimo año,
# asi se quita el efecto de la estacion y se ve si hay tendencia
media_movil = mensual.rolling(window=12).mean()
print("\nMedia movil 12 meses (min / max):", round(media_movil.min(), 1), "/", round(media_movil.max(), 1))

# 3. Datos para la interpretacion
anual = df["temp_min"].resample("YE").mean()
print("\nPromedio por año:")
print(anual.round(2))

por_mes = mensual.groupby(mensual.index.month).mean()
print("\nPromedio de cada mes del año (todos los años):")
print(por_mes.round(1))
print("Mes mas caliente:", por_mes.idxmax(), "->", round(por_mes.max(), 1), "°C")
print("Mes mas frio:", por_mes.idxmin(), "->", round(por_mes.min(), 1), "°C")

# 4. Grafico de la serie con su media movil
fig, ax = plt.subplots(figsize=(11, 5))
ax.plot(mensual.index, mensual, color="#9db8d6", marker="o", markersize=3, linewidth=1.2,
        label="Promedio mensual")
ax.plot(media_movil.index, media_movil, color="#c0392b", linewidth=2.5,
        label="Media móvil 12 meses")
ax.set_title("La temperatura mínima sube y baja cada año, pero no tiene tendencia (Melbourne 1981-1990)",
             fontsize=12, loc="left")
ax.set_ylabel("Temperatura mínima (°C)")
ax.set_xlabel("Año")
ax.set_ylim(0, 20)
ax.grid(alpha=0.3)
ax.legend(loc="lower right")
plt.tight_layout()
plt.savefig("grafico_serie.png", dpi=130)
print("\nGrafico guardado: grafico_serie.png")
