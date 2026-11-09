# Semana 14 - Análisis temporal y visualización (Corte 3)

Yilver Medina Urrea ([@yilvermedina](https://github.com/yilvermedina)) · Electiva VI Ciencia de Datos · Corte 3 · Entrega individual

Para esta entrega seguí con mi caso, Nübe Coffee Lab, y usé los datos que dejé limpios en la [semana 10](../10-week/README.md) (`ventas_limpias.csv`, copiado en `data/`). Son 11.858 líneas de venta de los dos puntos, del 3 de agosto al 27 de septiembre de 2026, o sea 8 semanas. Los datos son simulados, igual que en las semanas anteriores.

Para correr todo:

```bash
cd 14-week
pip install pandas matplotlib
python analisis_temporal.py    # serie, resample, media móvil y las 2 gráficas
python optimizacion_sql.py     # consulta antes y después en SQLite
```

## 1. Serie temporal

Como indicador usé el ingreso por ventas en pesos (cantidad × precio de cada línea). Puse la fecha como índice, agrupé con `resample` por día y por semana, y después saqué la media móvil de 7 días con `rolling`:

```python
df["ingreso"] = df["cantidad"] * df["precio_unitario"]
ventas = df.set_index("fecha").sort_index()

diario = ventas["ingreso"].resample("D").sum()          # 56 días
semanal = ventas["ingreso"].resample("W-SUN").sum()     # 8 semanas, de lunes a domingo
media_movil_7d = diario.rolling(window=7).mean()
```

Escogí 7 días porque es una semana completa: cada valor promedia un lunes, un martes, ... y un domingo, así se quita el efecto del día y queda la tendencia. Los primeros 6 días quedan vacíos (NaN) porque todavía no hay 7 días para promediar.

Total por semana, en millones de pesos:

| Semana | Ingreso | Festivo |
|---|---:|---|
| 03/08 - 09/08 | 13,32 | sí (viernes 7) |
| 10/08 - 16/08 | 11,87 | |
| 17/08 - 23/08 | 13,67 | sí (lunes 17) |
| 24/08 - 30/08 | 12,27 | |
| 31/08 - 06/09 | 12,05 | |
| 07/09 - 13/09 | 12,08 | |
| 14/09 - 20/09 | 12,05 | |
| 21/09 - 27/09 | 12,00 | |

### Tendencia

Al principio pensé que las ventas venían bajando, porque la media móvil pasa de $1,90 M por día en agosto a $1,71 M a finales de septiembre. Pero en la tabla se ve que las dos semanas más altas son justo las que tuvieron festivo. Las otras seis están casi iguales, alrededor de $12,05 M, y si les ajusto una recta la pendiente da prácticamente 0 % por semana (con las 8 semanas da −1,3 %, por culpa de los festivos). Entonces la tendencia es **plana**: el negocio no está creciendo ni cayendo, lo que pasa es que agosto tuvo dos festivos y septiembre ninguno.

### Estacionalidad

Lo que sí se nota es un patrón **semanal**. Este es el promedio por día de la semana, sin contar los 2 festivos:

| Día | Promedio (millones) | Índice |
|---|---:|---:|
| Lunes | 1,50 | 0,86 |
| Martes | 1,49 | 0,85 |
| Miércoles | 1,52 | 0,87 |
| Jueves | 1,69 | 0,96 |
| Viernes | 1,83 | 1,05 |
| Sábado | 2,25 | 1,29 |
| Domingo | 1,96 | 1,12 |

El índice es el promedio de ese día dividido entre el de un día normal ($1,75 M). De lunes a miércoles se vende entre 13 y 15 % menos de lo normal y el fin de semana más; el sábado es el mejor día y vende 51 % más que el martes. Los festivos se parecen a un sábado ($2,37 M y $2,25 M). Esto cuadra con lo de la semana 10, donde el sábado se gastaba 55 % más leche que un miércoles.

Con solo 8 semanas no se puede saber si hay una estacionalidad en el año (por ejemplo diciembre o la temporada de lluvias); para eso harían falta por lo menos 12 meses de datos.

## 2. Visualizaciones

### Evolución

![Ingreso diario y media móvil de 7 días](graficas/01_evolucion_ventas.png)

Usé una línea porque el eje x es el tiempo. El ingreso de cada día va en gris y la media móvil en azul, más gruesa, porque es lo que quiero que se vea. También marqué los dos festivos para que se entiendan los picos de agosto.

### Comparación

![Ingreso promedio por día de la semana](graficas/02_ventas_por_dia_semana.png)

Para comparar los días usé barras, en el orden normal de la semana (no de mayor a menor) para que se vea el patrón. El fin de semana va en azul y la línea punteada es el promedio de un día normal, para ver qué días quedan por encima y cuáles por debajo.

En las dos traté de aplicar lo que vimos en clase: el título dice la conclusión y no solo "ventas", el eje y empieza en $0 para no exagerar las diferencias, las unidades están en el eje (millones de pesos), uso un solo color para resaltar y gris para lo demás, no hay 3D ni doble eje, y abajo dice de dónde salen los datos.

## 3. Optimización de una consulta SQL

Escogí SQL porque el proyecto lo vengo trabajando en SQLite con el modelo de la semana 6 (`esquema.sql`). La consulta saca el ingreso y el número de ventas por día de septiembre, que es el mismo indicador de la serie.

**Antes:**

```sql
SELECT v.fecha,
       (SELECT SUM(d2.cantidad * d2.precio_unitario)
          FROM venta v2
          JOIN detalle_venta d2 ON d2.id_venta = v2.id_venta
         WHERE v2.fecha = v.fecha)                AS ingreso,
       COUNT(*)                                   AS tickets
FROM venta v
WHERE strftime('%Y-%m', v.fecha) = '2026-09'
GROUP BY v.fecha
ORDER BY v.fecha;
```

**Después:**

```sql
CREATE INDEX idx_venta_fecha ON venta(fecha);

SELECT v.fecha,
       SUM(d.cantidad * d.precio_unitario)  AS ingreso,
       COUNT(DISTINCT v.id_venta)           AS tickets
FROM venta v
JOIN detalle_venta d ON d.id_venta = v.id_venta
WHERE v.fecha >= '2026-09-01' AND v.fecha < '2026-10-01'
GROUP BY v.fecha
ORDER BY v.fecha;
```

Qué cambié y por qué:

1. Quité el `strftime()` del `WHERE` y puse un rango de fechas. Cuando se le aplica una función a la columna, SQLite tiene que calcularla fila por fila y no puede usar un índice.
2. Cambié la subconsulta correlacionada por un solo `JOIN` con `GROUP BY`. La subconsulta se repetía una vez por cada día (27 veces) y cada vez recorría toda la tabla `venta`.
3. Creé un índice en `venta(fecha)` para que SQLite vaya directo a las ventas de septiembre en vez de leer las 7.665.

Para comprobarlo usé `EXPLAIN QUERY PLAN` y medí el tiempo (mediana de 30 ejecuciones). Antes el plan decía `SCAN v` y `CORRELATED SCALAR SUBQUERY` con otro `SCAN` adentro, o sea que leía la tabla completa varias veces. Después dice `SEARCH v USING COVERING INDEX idx_venta_fecha (fecha>? AND fecha<?)`, que es ir directo a las filas que sirven.

| Versión | Tiempo | Instrucciones de SQLite |
|---|---:|---:|
| Antes | 14,35 ms | 738.075 |
| Solo reescrita (cambios 1 y 2) | 2,65 ms | 170.577 |
| Reescrita + índice | 1,68 ms | 103.294 |

La versión final es unas 8 veces más rápida (en varias corridas me dio entre 7,6 y 8,5 veces) y hace 86 % menos trabajo. El tiempo cambia un poco cada vez que se corre, por eso también conté las instrucciones que ejecuta SQLite, que siempre dan lo mismo. El script también revisa que las tres versiones devuelvan exactamente las mismas 27 filas y que coincidan con el `resample` de pandas.

## 4. Findings

The daily sales of Nübe Coffee Lab did not grow between August 3 and September 27, 2026. The 7-day moving average stays almost flat, at around 1.8 million pesos per day. August looks a little higher only because it had two holidays, on August 7 and August 17. In the six weeks without a holiday, sales were very similar, about 12 million pesos per week.

The data has a clear weekly seasonality. Saturday is the best day, with 2.25 million pesos on average, and it sells 51% more than Tuesday, the weakest day. Monday, Tuesday and Wednesday are below average, while Friday, Saturday and Sunday are above it. Holidays sell almost like a Saturday.

The first chart shows the sales of each day in gray and the 7-day moving average in blue, so it is easy to see that the trend is flat. The second chart compares the average sales for each day of the week, and the weekend bars are in blue. In both charts the y-axis starts at zero, so the differences are not exaggerated.

Finally, the optimized SQL query gives the same results about 8 times faster. Because of all this, I think Nübe should plan its purchases and its staff by day of the week, and not with the same amount every day.

## Archivos

- `analisis_temporal.py`: serie temporal, resample, media móvil, tendencia, estacionalidad y las 2 gráficas.
- `optimizacion_sql.py`: carga la base en SQLite y compara la consulta antes y después.
- `esquema.sql`: modelo de la semana 6.
- `data/`: ventas limpias de la semana 10 y los catálogos.
- `graficas/`: las 2 gráficas.
- `resultados/`: las tablas que salen de los scripts en CSV.
