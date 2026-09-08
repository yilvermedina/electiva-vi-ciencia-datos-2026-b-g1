# Semana 1 · Encuadra un proyecto de datos

> **Asignatura:** Ciencia de Datos · Unidad 1 — Fundamentos de Ciencia de Datos y Big Data
> **Estudiante:** Yilver Medina Urrea
> **Programa:** Ingeniería Mecatrónica
> **Periodo:** 2026-B · Corte 1
> **Modalidad:** Individual

---

## 1. Problema real y pregunta de negocio

**Contexto:** *Nübe Coffee Lab*, cafetería de especialidad con dos puntos de venta y ~300 clientes diarios. La administradora compra la materia prima "a ojo", guiándose por la semana anterior. Unos días sobra leche y se vence; otros días el producto estrella se agota a media mañana.

### Pregunta de negocio

> **¿Cuánta materia prima (leche, café y croissants) debe comprar Nübe Coffee Lab para cada día de la próxima semana, de modo que el desperdicio y los agotados se reduzcan al mínimo?**

**Por qué es accionable:** la respuesta es un número que se traduce directamente en una orden de compra. No es una curiosidad, es una decisión que alguien toma todas las semanas.

---

## 2. Datos necesarios y sus fuentes

| # | Dato requerido | Fuente | Formato | Frecuencia |
|:-:|---|---|---|---|
| 1 | Ventas por producto, día y hora | Sistema POS del mostrador | Tabla / CSV — **estructurado** | Diaria |
| 2 | Pedidos de domicilio (producto, cantidad, hora) | App de domicilios | `JSON` — **semiestructurado** | Diaria |
| 3 | Consumo real de insumos y mermas | Planilla de inventario del local | Hoja de cálculo — **estructurado** | Semanal |
| 4 | Calendario de festivos y fechas especiales | Calendario oficial de Colombia | Tabla de fechas — **estructurado** | Anual |
| 5 | Clima diario (lluvia y temperatura) | API meteorológica pública (IDEAM / OpenWeather) | `JSON` — **semiestructurado** | Diaria |
| 6 | Reseñas y quejas de clientes | Google Maps · Instagram | Texto libre — **no estructurado** | Continua |

**Por qué estas fuentes:** los datos 1 a 3 dicen *cuánto se vendió y cuánto se gastó realmente*; los datos 4 y 5 explican *por qué unos días se vende más que otros*; el dato 6 valida el problema desde la voz del cliente (las quejas por agotados).

---

## 3. Decisión o acción que habilita el resultado

**Decisión concreta:** cada **jueves**, la administradora emite la orden de compra al proveedor con las cantidades sugeridas por el modelo para los 7 días siguientes, en lugar de estimarlas a mano.

**Acciones derivadas:**

- Ajustar la **cantidad de leche y café** pedida al proveedor.
- Ajustar la **producción diaria de croissants** en el horno del local.
- **Reforzar el turno** de la franja 7:00–11:00 a. m. los días de alta demanda proyectada.

**Cómo se mide el éxito:**

| Indicador | Situación actual | Meta a 3 meses |
|---|---|---|
| Merma de leche | ~12 % de lo comprado | ≤ 4 % |
| Días con agotados del producto estrella | 3 de cada 7 | ≤ 1 de cada 7 |
| Quejas por agotados en reseñas | Recurrentes | Reducción del 50 % |

---

## 4. Tipo de analítica

| Etapa | Tipo de analítica | Pregunta que responde | En este proyecto |
|---|---|---|---|
| Punto de partida | **Descriptiva** | ¿Qué pasó? | Cuáles fueron los productos más vendidos por día y franja horaria en el último trimestre |
| Objetivo principal | **Predictiva** | ¿Qué va a pasar? | Cuántos litros de leche y cuántos croissants se van a necesitar cada día de la próxima semana |

**Tipo que busca este proyecto: analítica predictiva.**

Se apoya primero en un análisis descriptivo para entender el patrón histórico de demanda, y sobre esa base construye un modelo de **regresión o serie de tiempo** que proyecta la demanda futura usando como variables el historial de ventas, el día de la semana, los festivos y el clima.

> *No se busca analítica prescriptiva en esta primera fase: el modelo sugiere la cantidad, pero la decisión final de compra sigue siendo humana.*

---

## Resumen en una línea

Convertir el historial de ventas de Nübe Coffee Lab en una **orden de compra semanal calculada**, para dejar de perder dinero por leche vencida y ventas por producto agotado.
