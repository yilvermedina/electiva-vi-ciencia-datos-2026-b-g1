# Semana 7 · Consultas SQL y pandas: Nübe Coffee Lab

> **Asignatura:** Ciencia de Datos · Unidad 2 — Modelamiento, transformación y conexión de datos
> **Estudiante:** Yilver Medina Urrea · [@yilvermedina](https://github.com/yilvermedina)
> **Programa:** Ingeniería Mecatrónica
> **Periodo:** 2026-B · Corte 2
> **Modalidad:** Individual

---

## 1. Datos usados

Uso el **modelo que diseñé en la semana 6** ([`esquema.sql`](esquema.sql)) cargado en **SQLite**, con datos de 8 semanas de operación de Nübe Coffee Lab (3 de agosto a 27 de septiembre de 2026).

> ⚠️ Los datos son **simulados** con el script [`generar_datos.py`](generar_datos.py), con semilla fija para que siempre salgan iguales. Siguen el comportamiento del caso: dos puntos en Neiva, más ventas en fines de semana y festivos, y más bebidas calientes y domicilios cuando llueve.

| Tabla | Filas |
|---|---:|
| `venta` | 7.676 |
| `detalle_venta` | 11.896 |
| `cliente` | 300 |
| `calendario_clima` | 56 |
| `producto` / `insumo` / `receta` | 8 / 6 / 14 |
| `punto_venta` | 2 |

**Cómo ejecutarlo:**

```bash
cd 07-week
python generar_datos.py   # crea data/*.csv (ya vienen incluidos)
python consultas.py       # crea nube.db, corre las 3 consultas y el equivalente en pandas
```

---

## 2. Consulta 1 · `WHERE`

**Pregunta:** ¿cuántos domicilios hubo los días de lluvia fuerte (15 mm o más)?

```sql
SELECT v.fecha, COUNT(*) AS domicilios
FROM venta v
WHERE v.canal = 'Domicilio'
  AND v.fecha IN (SELECT fecha FROM calendario_clima WHERE lluvia_mm >= 15)
GROUP BY v.fecha
ORDER BY domicilios DESC;
```

| fecha | domicilios |
|---|---:|
| 2026-08-21 | 62 |
| 2026-09-10 | 61 |
| 2026-09-12 | 49 |
| 2026-09-15 | 29 |

**Qué responde:** el `WHERE` deja solo los pedidos por domicilio de los días con mucha lluvia. En un día seco normal hay unos 25 domicilios entre los dos puntos; con lluvia fuerte llegan hasta 60. **Sirve para decidir cuándo reforzar el turno de domicilios** viendo el pronóstico del clima.

---

## 3. Consulta 2 · `JOIN`

**Pregunta:** ¿qué días se gastó más leche?

```sql
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
```

| fecha | día | litros de leche |
|---|---|---:|
| 2026-08-08 | sábado | 32,6 |
| 2026-09-26 | sábado | 31,3 |
| 2026-08-15 | sábado | 31,1 |
| 2026-08-07 | viernes (festivo) | 29,9 |
| 2026-08-22 | sábado | 28,7 |
| 2026-08-09 | domingo | 26,7 |
| 2026-09-13 | domingo | 26,6 |

**Qué responde:** esta es **la consulta central de mi proyecto**. Une 5 tablas: la venta, sus líneas, la **receta** de cada producto, el insumo y el calendario. Así cada capuchino, latte o chocolate se convierte en litros de leche. Los días de más consumo son los **sábados** y el **festivo del 7 de agosto**, con unos 30 litros. Ese es el número que la administradora necesita para pedir la leche, en lugar de calcularla "a ojo".

---

## 4. Consulta 3 · `GROUP BY`

**Pregunta:** ¿cuántas unidades y cuánto dinero dejó cada producto en las 8 semanas?

```sql
SELECT p.nombre                            AS producto,
       SUM(d.cantidad)                     AS unidades,
       SUM(d.cantidad * d.precio_unitario) AS ingresos
FROM detalle_venta d
JOIN producto p ON p.id_producto = d.id_producto
GROUP BY p.nombre
ORDER BY unidades DESC;
```

| producto | unidades | ingresos (COP) |
|---|---:|---:|
| Croissant | 2.702 | 16.212.000 |
| Tinto | 2.543 | 7.629.000 |
| Capuchino | 2.472 | **21.012.000** |
| Latte | 1.818 | 16.362.000 |
| Americano | 1.789 | 8.945.000 |
| Croissant de almendras | 1.364 | 10.912.000 |
| Chocolate caliente | 1.080 | 8.100.000 |
| Frappé de café | 959 | 10.549.000 |

**Qué responde:** el `GROUP BY` agrupa todas las líneas de venta por producto y suma unidades e ingresos. El producto **que más se vende es el croissant**, pero el que **más plata deja es el capuchino** (21 millones). Por eso son los dos que no se pueden agotar: el croissant por volumen y el capuchino por ingreso.

---

## 5. La consulta 3 en pandas (`groupby`)

```python
import pandas as pd

detalle  = pd.read_csv("data/detalle_venta.csv")
producto = pd.read_csv("data/producto.csv")

df = detalle.merge(producto, on="id_producto")          # equivale al JOIN
df["ingreso"] = df["cantidad"] * df["precio_unitario"]

resultado = (df.groupby("nombre")                         # equivale al GROUP BY
               .agg(unidades=("cantidad", "sum"),         # SUM(cantidad)
                    ingresos=("ingreso", "sum"))          # SUM(cantidad*precio)
               .reset_index()
               .sort_values("unidades", ascending=False)) # ORDER BY unidades DESC
```

El script compara las dos tablas con `DataFrame.equals()` y la salida es:

```
¿SQL y pandas dan exactamente lo mismo? SÍ
```

### Equivalencias SQL ↔ pandas

| SQL | pandas |
|---|---|
| `FROM detalle_venta JOIN producto ON ...` | `detalle.merge(producto, on="id_producto")` |
| `GROUP BY p.nombre` | `.groupby("nombre")` |
| `SUM(d.cantidad)` | `.agg(unidades=("cantidad", "sum"))` |
| `ORDER BY unidades DESC` | `.sort_values("unidades", ascending=False)` |
| `WHERE canal = 'Domicilio'` | `df[df["canal"] == "Domicilio"]` |

---

## 6. Archivos

| Archivo | Contenido |
|---|---|
| `README.md` | Este documento |
| `consultas.py` | Crea la base, carga los datos, corre las 3 consultas y el equivalente en pandas |
| `generar_datos.py` | Genera los datos simulados del caso |
| `esquema.sql` | El modelo de la semana 6 |
| `data/*.csv` | Las 8 tablas en CSV |

---

*Entrega individual por GitHub · Fork del repositorio de la clase · CORHUILA 2026-B*
