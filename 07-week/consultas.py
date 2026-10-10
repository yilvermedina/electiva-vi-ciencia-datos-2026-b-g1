"""
Semana 7 · Consultas SQL y pandas sobre Nübe Coffee Lab

Autor: Yilver Medina Urrea · Electiva VI Ciencia de Datos · CORHUILA 2026-B

1. Crea la base SQLite nube.db con el esquema de la semana 6 (esquema.sql).
2. Carga los CSV de data/ (si no existen, corre primero generar_datos.py).
3. Ejecuta 3 consultas SQL (WHERE, JOIN, GROUP BY).
4. Reproduce la consulta GROUP BY en pandas y comprueba que da lo mismo.

Uso:  python consultas.py
"""
from pathlib import Path
import sqlite3
import pandas as pd

AQUI = Path(__file__).parent
DATA = AQUI / "data"
DB = AQUI / "nube.db"

if not (DATA / "venta.csv").exists():
    import runpy
    runpy.run_path(str(AQUI / "generar_datos.py"))

# ------------------------------------------------------------ 1-2. crear y cargar
if DB.exists():
    DB.unlink()
con = sqlite3.connect(DB)
con.executescript((AQUI / "esquema.sql").read_text(encoding="utf-8"))
orden = ["punto_venta", "cliente", "producto", "insumo", "calendario_clima",
         "venta", "detalle_venta", "receta"]          # padres antes que hijos (FK)
for tabla in orden:
    df = pd.read_csv(DATA / f"{tabla}.csv")
    df.to_sql(tabla, con, if_exists="append", index=False)
    print(f"cargada {tabla:17s} {len(df):6d} filas")

pd.set_option("display.width", 120)


def correr(titulo, sql):
    print("\n" + "=" * 70 + f"\n{titulo}\n" + "=" * 70)
    print(sql.strip())
    res = pd.read_sql_query(sql, con)
    print("\nResultado:")
    print(res.to_string(index=False))
    return res


# ------------------------------------------------------------ 3. consultas SQL
q1 = correr("Consulta 1 · WHERE — domicilios en días de lluvia fuerte (>= 15 mm)", """
SELECT v.fecha, COUNT(*) AS domicilios
FROM venta v
WHERE v.canal = 'Domicilio'
  AND v.fecha IN (SELECT fecha FROM calendario_clima WHERE lluvia_mm >= 15)
GROUP BY v.fecha
ORDER BY domicilios DESC;
""")

q2 = correr("Consulta 2 · JOIN — litros de leche gastados por día (top 7)", """
SELECT v.fecha,
       c.dia_semana,
       ROUND(SUM(d.cantidad * r.cantidad), 1) AS litros_leche
FROM venta v
JOIN detalle_venta    d ON d.id_venta    = v.id_venta
JOIN receta           r ON r.id_producto = d.id_producto
JOIN insumo           i ON i.id_insumo   = r.id_insumo
JOIN calendario_clima c ON c.fecha       = v.fecha
WHERE i.nombre = 'Leche entera'
GROUP BY v.fecha, c.dia_semana
ORDER BY litros_leche DESC
LIMIT 7;
""")

q3 = correr("Consulta 3 · GROUP BY — unidades e ingresos por producto", """
SELECT p.nombre                                  AS producto,
       SUM(d.cantidad)                           AS unidades,
       SUM(d.cantidad * d.precio_unitario)       AS ingresos
FROM detalle_venta d
JOIN producto p ON p.id_producto = d.id_producto
GROUP BY p.nombre
ORDER BY unidades DESC;
""")

# ------------------------------------------------------------ 4. misma consulta en pandas
print("\n" + "=" * 70 + "\nConsulta 3 reproducida en pandas (groupby)\n" + "=" * 70)
detalle = pd.read_csv(DATA / "detalle_venta.csv")
producto = pd.read_csv(DATA / "producto.csv")

df = detalle.merge(producto, on="id_producto")           # el JOIN
df["ingreso"] = df["cantidad"] * df["precio_unitario"]
q3_pandas = (df.groupby("nombre")                          # el GROUP BY
               .agg(unidades=("cantidad", "sum"), ingresos=("ingreso", "sum"))
               .reset_index()
               .rename(columns={"nombre": "producto"})
               .sort_values("unidades", ascending=False))
print(q3_pandas.to_string(index=False))

iguales = q3.reset_index(drop=True).equals(q3_pandas.reset_index(drop=True))
print("\n¿SQL y pandas dan exactamente lo mismo?", "SÍ" if iguales else "NO")
con.close()
