"""
Semana 8 · Paso EXTRAER del pipeline: consumir una API pública con requests

Autor: Yilver Medina Urrea · Electiva VI Ciencia de Datos · CORHUILA 2026-B

Trae el pronóstico del clima de Neiva desde Open-Meteo (API pública, gratis y
sin API key) y muestra 3 registros. Es la fuente "clima" del pipeline ETL de
Nübe Coffee Lab: la lluvia y la temperatura cambian la demanda de bebidas
calientes y de domicilios.

Uso:
    pip install requests pandas
    python api_clima.py
"""
import requests
import pandas as pd

URL = "https://api.open-meteo.com/v1/forecast"
PARAMS = {
    "latitude": 2.9273,          # Neiva, Huila
    "longitude": -75.2819,
    "daily": "temperature_2m_max,precipitation_sum",
    "timezone": "America/Bogota",
    "forecast_days": 7,
}

# ---------------------------------------------------------------- EXTRAER
resp = requests.get(URL, params=PARAMS, timeout=15)
resp.raise_for_status()                  # si la API falla, se detiene con el error
datos = resp.json()
print("Código HTTP:", resp.status_code)
print("Claves del JSON:", list(datos.keys()))

# ---------------------------------------------------------------- TRANSFORMAR (mínimo)
diario = datos["daily"]                  # el JSON trae listas paralelas por campo
clima = pd.DataFrame({
    "fecha": diario["time"],
    "temp_max_c": diario["temperature_2m_max"],
    "lluvia_mm": diario["precipitation_sum"],
})
clima["llueve"] = clima["lluvia_mm"] > 0

print("\n3 registros del pronóstico para Neiva:")
print(clima.head(3).to_string(index=False))

# ---------------------------------------------------------------- CARGAR (staging)
clima.to_csv("clima_neiva_pronostico.csv", index=False)
print("\nGuardado en clima_neiva_pronostico.csv")
