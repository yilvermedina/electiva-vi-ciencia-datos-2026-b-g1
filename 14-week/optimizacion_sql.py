"""
Semana 14 · Corte 3 · Optimización de una consulta SQL · Nübe Coffee Lab

Autor: Yilver Medina Urrea · Electiva VI Ciencia de Datos · CORHUILA 2026-B

La consulta saca el indicador de la serie temporal: ingreso y tickets por día de un mes.
Se compara la versión original (lenta) con la optimizada:
  A. Original:   función sobre la columna en el WHERE + subconsulta correlacionada.
  B. Reescrita:  un solo JOIN + GROUP BY y filtro por rango de fechas.
  C. Optimizada: B + índice sobre venta(fecha).
Para cada una se muestra el plan (EXPLAIN QUERY PLAN), el tiempo y se verifica que
las tres devuelven exactamente lo mismo, y que coinciden con el resample de pandas.

Uso:  python optimizacion_sql.py
"""
from pathlib import Path
import sqlite3
import statistics
import time
import pandas as pd

AQUI = Path(__file__).parent
DATA = AQUI / "data"
RES = AQUI / "resultados"
RES.mkdir(exist_ok=True)
REPETICIONES = 30


def titulo(t):
    print("\n" + "=" * 72 + f"\n{t}\n" + "=" * 72)


# =========================================================== 1. CARGAR la base (modelo semana 6)
titulo("1. Cargar ventas_limpias.csv en SQLite con el esquema de la semana 6")
db = AQUI / "nube.db"
if db.exists():
    db.unlink()
con = sqlite3.connect(db)
con.executescript((AQUI / "esquema.sql").read_text(encoding="utf-8"))

df = pd.read_csv(DATA / "ventas_limpias.csv")
producto = pd.read_csv(DATA / "producto.csv")
id_punto = {"Nübe Centro": 1, "Nübe Altico": 2}
id_prod = dict(zip(producto["nombre"], producto["id_producto"]))

# una venta = un ticket; el medio de pago se toma de la línea que sí lo tiene (igual que en la semana 10)
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
con.execute("ANALYZE")                      # estadísticas para que el optimizador decida bien

# =========================================================== 2. LAS CONSULTAS
SQL_A = """
SELECT v.fecha,
       (SELECT SUM(d2.cantidad * d2.precio_unitario)          -- subconsulta correlacionada:
          FROM venta v2                                         -- se repite para cada fecha
          JOIN detalle_venta d2 ON d2.id_venta = v2.id_venta
         WHERE v2.fecha = v.fecha)                AS ingreso,
       COUNT(*)                                   AS tickets
FROM venta v
WHERE strftime('%Y-%m', v.fecha) = '2026-09'      -- función sobre la columna: no puede usar índice
GROUP BY v.fecha
ORDER BY v.fecha;
"""

SQL_B = """
SELECT v.fecha,
       SUM(d.cantidad * d.precio_unitario)  AS ingreso,     -- se suma en una sola pasada
       COUNT(DISTINCT v.id_venta)           AS tickets
FROM venta v
JOIN detalle_venta d ON d.id_venta = v.id_venta
WHERE v.fecha >= '2026-09-01' AND v.fecha < '2026-10-01' -- rango sobre la columna "tal cual"
GROUP BY v.fecha
ORDER BY v.fecha;
"""

INDICE = "CREATE INDEX idx_venta_fecha ON venta(fecha);"


def plan(sql):
    return [fila[3] for fila in con.execute("EXPLAIN QUERY PLAN " + sql)]


def medir(sql):
    con.execute(sql).fetchall()                               # calentar caché
    tiempos = []
    for _ in range(REPETICIONES):
        t0 = time.perf_counter()
        filas = con.execute(sql).fetchall()
        tiempos.append((time.perf_counter() - t0) * 1000)
    return filas, statistics.median(tiempos)


def filas_leidas(sql):
    """Cuántas filas recorre SQLite (pasos de la máquina virtual) -> no depende del PC."""
    pasos = 0

    def contar():
        nonlocal pasos
        pasos += 1
        return 0                                              # 0 = seguir ejecutando
    con.set_progress_handler(contar, 1)
    con.execute(sql).fetchall()
    con.set_progress_handler(None, 1)
    return pasos


resultados = []
for nombre, sql, crear_indice in [("A · Original", SQL_A, False),
                                  ("B · Reescrita (JOIN + rango)", SQL_B, False),
                                  ("C · Reescrita + índice", SQL_B, True)]:
    if crear_indice:
        con.execute(INDICE)
        con.execute("ANALYZE")
    titulo(f"2. Consulta {nombre}")
    p = plan(sql)
    print("Plan:"); [print("   ", paso) for paso in p]
    filas, ms = medir(sql)
    pasos = filas_leidas(sql)
    print(f"Filas devueltas: {len(filas)} · tiempo (mediana de {REPETICIONES}): {ms:.2f} ms · "
          f"instrucciones VM: {pasos:,}")
    resultados.append({"version": nombre, "tiempo_ms": round(ms, 2), "instrucciones_vm": pasos,
                       "plan": " | ".join(p), "filas": filas})

# =========================================================== 3. VERIFICAR
titulo("3. Verificación: mismas respuestas")
iguales = resultados[0]["filas"] == resultados[1]["filas"] == resultados[2]["filas"]
print("A, B y C devuelven exactamente lo mismo:", "✅ sí" if iguales else "❌ NO")

# contra pandas (resample del análisis temporal)
dfp = pd.read_csv(DATA / "ventas_limpias.csv", parse_dates=["fecha"])
dfp["ingreso"] = dfp["cantidad"] * dfp["precio_unitario"]
sep = dfp[dfp["fecha"].dt.month == 9].set_index("fecha")
pd_ingreso = sep["ingreso"].resample("D").sum()
pd_tickets = sep["id_venta"].resample("D").nunique()
sql_df = pd.DataFrame(resultados[2]["filas"], columns=["fecha", "ingreso", "tickets"])
coincide = (list(sql_df["ingreso"]) == list(pd_ingreso) and list(sql_df["tickets"]) == list(pd_tickets))
print("SQL coincide con el resample de pandas:", "✅ sí" if coincide else "❌ NO")
assert iguales and coincide

# =========================================================== 4. RESUMEN
titulo("4. Resumen")
base = resultados[0]
for r in resultados:
    print(f"{r['version']:32s} {r['tiempo_ms']:9.2f} ms  ({base['tiempo_ms'] / r['tiempo_ms']:6.1f}x)  "
          f"{r['instrucciones_vm']:>12,} instrucciones")
resumen = pd.DataFrame([{k: v for k, v in r.items() if k != "filas"} for r in resultados])
resumen["veces_mas_rapida"] = (base["tiempo_ms"] / resumen["tiempo_ms"]).round(1)
resumen.to_csv(RES / "optimizacion_sql.csv", index=False)
sql_df.to_csv(RES / "ingreso_diario_septiembre_sql.csv", index=False)
print("\nGuardado resultados/optimizacion_sql.csv")
con.close()
