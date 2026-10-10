"""
Semana 10 · Mini-proyecto de datos (cierre del corte 2) · Nübe Coffee Lab

Autor: Yilver Medina Urrea · Electiva VI Ciencia de Datos · CORHUILA 2026-B

Flujo completo:  EXTRAER  ->  LIMPIAR  ->  CARGAR (SQLite, modelo semana 6)  ->  ANALIZAR
  - Extraer:  export_pos_crudo.csv (planilla del POS) + catálogos y calendario-clima
  - Limpiar:  duplicados, nulos, tipos, formatos de texto y fechas (pandas)
  - Cargar:   base nube_limpia.db con el esquema de la semana 6
  - Analizar: 2 preguntas de negocio con SQL (filtro + agregación)

Uso:  python mini_proyecto.py
"""
from pathlib import Path
import re
import sqlite3
import unicodedata
import pandas as pd

AQUI = Path(__file__).parent
DATA = AQUI / "data"
SALIDA = AQUI / "datos_limpios"
SALIDA.mkdir(exist_ok=True)
pd.set_option("display.width", 120)


def titulo(t):
    print("\n" + "=" * 72 + f"\n{t}\n" + "=" * 72)


def reporte(df, nombre):
    return {
        "dataset": nombre,
        "filas": len(df),
        "nulos": int(df.drop(columns="id_cliente").isna().sum().sum()),
        "duplicados": int(df.duplicated().sum()),
        "productos_distintos": df["producto"].nunique(),
        "puntos_distintos": df["punto"].nunique(),
    }


# =========================================================== 1. EXTRAER
titulo("1. EXTRAER")
crudo = pd.read_csv(DATA / "export_pos_crudo.csv", dtype=str)
producto = pd.read_csv(DATA / "producto.csv")
print("export_pos_crudo.csv:", crudo.shape)
print(crudo.head(5).to_string(index=False))
antes = reporte(crudo, "ANTES")
print("\nNulos por columna (id_cliente vacío es normal: cliente sin tarjeta):")
print(crudo.isna().sum().to_string())

# =========================================================== 2. LIMPIAR
titulo("2. LIMPIAR")
df = crudo.copy()

# 2.1 duplicados exactos
n0 = len(df)
df = df.drop_duplicates()
print(f"2.1 Duplicados eliminados: {n0 - len(df)}")


# 2.2 texto: producto -> nombre oficial del catálogo
def clave(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", s).strip().lower()


catalogo = {clave(n): n for n in producto["nombre"]}
catalogo.update({                      # errores de digitación vistos en la planilla
    "capuccino": "Capuchino", "croisant": "Croissant", "late": "Latte",
    "croissant almendras": "Croissant de almendras",
})
sin_mapa = set(df["producto"].map(clave)) - set(catalogo)
df["producto"] = df["producto"].map(clave).map(catalogo)
print(f"2.2 Productos: {crudo['producto'].nunique()} escrituras -> {df['producto'].nunique()} productos."
      f" Sin reconocer: {sin_mapa or 'ninguno'}")

# 2.3 texto: punto de venta
df["punto"] = df["punto"].map(clave).map(
    lambda s: "Nübe Centro" if "centro" in s else ("Nübe Altico" if "altico" in s else None))
print(f"2.3 Puntos: {crudo['punto'].nunique()} escrituras -> {df['punto'].nunique()} puntos")

# 2.4 texto: medio de pago (mayúsculas) y vacíos
df["medio_pago"] = df["medio_pago"].str.strip().str.capitalize().fillna("Sin dato")
print("2.4 Medios de pago:", sorted(df["medio_pago"].unique()))

# 2.5 fechas: dos formatos (aaaa-mm-dd y dd/mm/aaaa) -> datetime
iso = pd.to_datetime(df["fecha"], format="%Y-%m-%d", errors="coerce")
dmy = pd.to_datetime(df["fecha"], format="%d/%m/%Y", errors="coerce")
df["fecha"] = iso.fillna(dmy)
print(f"2.5 Fechas en dd/mm/aaaa corregidas: {int(iso.isna().sum())}. Fechas inválidas: {int(df['fecha'].isna().sum())}")

# 2.6 precio: quitar '$' y '.', pasar a número; vacíos -> precio de la carta
precio_carta = dict(zip(producto["nombre"], producto["precio"]))
df["precio_unitario"] = pd.to_numeric(df["precio_unitario"].str.replace(r"[$.\s]", "", regex=True),
                                      errors="coerce")
n_imp = int(df["precio_unitario"].isna().sum())
df["precio_unitario"] = df["precio_unitario"].fillna(df["producto"].map(precio_carta)).astype(int)
print(f"2.6 Precios con '$' convertidos; {n_imp} precios vacíos imputados con el precio de la carta")

# 2.7 cantidad: '2 und' -> 2; vacíos -> 1 (la moda); 0 -> se elimina (no es una venta)
df["cantidad"] = pd.to_numeric(df["cantidad"].str.extract(r"(\d+)")[0], errors="coerce")
moda = int(df["cantidad"].mode()[0])
n_nul = int(df["cantidad"].isna().sum())
df["cantidad"] = df["cantidad"].fillna(moda).astype(int)
n_cero = int((df["cantidad"] <= 0).sum())
df = df[df["cantidad"] > 0]
print(f"2.7 Cantidades: {n_nul} vacías imputadas con la moda ({moda}); {n_cero} filas con cantidad 0 eliminadas")

# 2.8 tipos finales
df["id_venta"] = df["id_venta"].astype(int)
df = df.sort_values(["id_venta", "producto"]).reset_index(drop=True)
print("2.8 Tipos finales:\n" + df.dtypes.to_string())

# 2.9 verificación: (id_venta, producto) debe ser único (PK de detalle_venta)
assert not df.duplicated(["id_venta", "producto"]).any(), "PK repetida en detalle"

despues = reporte(df, "DESPUÉS")
titulo("ANTES / DESPUÉS")
comp = pd.DataFrame([antes, despues]).set_index("dataset").T
print(comp.to_string())
comp.to_csv(SALIDA / "reporte_antes_despues.csv")
df.to_csv(SALIDA / "ventas_limpias.csv", index=False, date_format="%Y-%m-%d")
print("\nGuardado datos_limpios/ventas_limpias.csv")

# =========================================================== 3. CARGAR
titulo("3. CARGAR en SQLite (modelo de la semana 6)")
db = AQUI / "nube_limpia.db"
if db.exists():
    db.unlink()
con = sqlite3.connect(db)
con.executescript((AQUI / "esquema.sql").read_text(encoding="utf-8"))

id_punto = {"Nübe Centro": 1, "Nübe Altico": 2}
id_prod = dict(zip(producto["nombre"], producto["id_producto"]))
df["fecha"] = df["fecha"].dt.strftime("%Y-%m-%d")

# una venta = un ticket; el medio de pago se toma de la línea que sí lo tiene
venta = (df.assign(_sin=df["medio_pago"].eq("Sin dato"))
           .sort_values(["id_venta", "_sin"])
           .groupby("id_venta", as_index=False)
           .first()[["id_venta", "fecha", "hora", "punto", "id_cliente", "canal", "medio_pago"]])
venta["id_punto"] = venta.pop("punto").map(id_punto)
detalle = df[["id_venta", "producto", "cantidad", "precio_unitario"]].copy()
detalle["id_producto"] = detalle.pop("producto").map(id_prod)

tablas = [("punto_venta", pd.read_csv(DATA / "punto_venta.csv")),
          ("cliente", pd.read_csv(DATA / "cliente.csv")),
          ("producto", producto),
          ("insumo", pd.read_csv(DATA / "insumo.csv")),
          ("calendario_clima", pd.read_csv(DATA / "calendario_clima.csv")),
          ("venta", venta[["id_venta", "fecha", "hora", "id_punto", "id_cliente", "canal", "medio_pago"]]),
          ("detalle_venta", detalle[["id_venta", "id_producto", "cantidad", "precio_unitario"]]),
          ("receta", pd.read_csv(DATA / "receta.csv"))]
for nombre, t in tablas:
    t.to_sql(nombre, con, if_exists="append", index=False)
    print(f"cargada {nombre:17s} {len(t):6d} filas")
fk = con.execute("PRAGMA foreign_key_check").fetchall()
print("Revisión de llaves foráneas:", "sin errores" if not fk else fk[:5])

# =========================================================== 4. ANALIZAR
titulo("4. PREGUNTA 1 · ¿Cuánta leche y café hay que pedir para cada día de la semana?")
sql1 = """
WITH consumo_dia AS (                      -- consumo de cada insumo en cada fecha
    SELECT v.fecha, c.dia_semana, i.nombre AS insumo, i.unidad,
           SUM(d.cantidad * r.cantidad) AS consumo
    FROM venta v
    JOIN detalle_venta    d ON d.id_venta    = v.id_venta
    JOIN receta           r ON r.id_producto = d.id_producto
    JOIN insumo           i ON i.id_insumo   = r.id_insumo
    JOIN calendario_clima c ON c.fecha       = v.fecha
    WHERE i.nombre IN ('Leche entera', 'Café en grano')   -- filtro
      AND c.es_festivo = 0                                 -- los festivos se planean aparte
    GROUP BY v.fecha, c.dia_semana, i.nombre, i.unidad
)
SELECT dia_semana, insumo, unidad,
       ROUND(AVG(consumo), 2)          AS promedio,       -- agregación
       ROUND(MAX(consumo), 2)          AS maximo,
       ROUND(AVG(consumo) * 1.10, 1)   AS pedido_sugerido -- promedio + 10 % de seguridad
FROM consumo_dia
GROUP BY dia_semana, insumo, unidad
ORDER BY insumo DESC,
         CASE dia_semana WHEN 'lunes' THEN 1 WHEN 'martes' THEN 2 WHEN 'miércoles' THEN 3
              WHEN 'jueves' THEN 4 WHEN 'viernes' THEN 5 WHEN 'sábado' THEN 6 ELSE 7 END;
"""
r1 = pd.read_sql_query(sql1, con)
print(sql1.strip())
print("\nResultado:")
print(r1.to_string(index=False))
r1.to_csv(SALIDA / "pedido_sugerido_por_dia.csv", index=False)

titulo("4. PREGUNTA 2 · ¿La lluvia aumenta la venta de bebidas calientes?")
sql2 = """
WITH por_dia AS (
    SELECT v.fecha,
           CASE WHEN c.lluvia_mm > 0 THEN 'Con lluvia' ELSE 'Sin lluvia' END AS clima,
           SUM(CASE WHEN p.categoria = 'Bebida caliente' THEN d.cantidad ELSE 0 END) AS calientes,
           SUM(CASE WHEN p.categoria = 'Bebida fría'     THEN d.cantidad ELSE 0 END) AS frias,
           COUNT(DISTINCT CASE WHEN v.canal = 'Domicilio' THEN v.id_venta END)       AS domicilios
    FROM venta v
    JOIN detalle_venta    d ON d.id_venta    = v.id_venta
    JOIN producto         p ON p.id_producto = d.id_producto
    JOIN calendario_clima c ON c.fecha       = v.fecha
    WHERE c.es_festivo = 0                                 -- filtro
    GROUP BY v.fecha, clima
)
SELECT clima,
       COUNT(*)                   AS dias,
       ROUND(AVG(calientes), 1)   AS bebidas_calientes_dia,  -- agregación
       ROUND(AVG(frias), 1)       AS bebidas_frias_dia,
       ROUND(AVG(domicilios), 1)  AS domicilios_dia
FROM por_dia
GROUP BY clima;
"""
r2 = pd.read_sql_query(sql2, con)
print(sql2.strip())
print("\nResultado:")
print(r2.to_string(index=False))
r2.to_csv(SALIDA / "efecto_lluvia.csv", index=False)

con.close()
print("\nListo. Resultados en datos_limpios/")
