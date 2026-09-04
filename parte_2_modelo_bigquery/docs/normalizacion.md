# Normalización del modelo — TodoComponentes (3NF)

Este documento justifica que el modelo de datos de **TodoComponentes** está
normalizado hasta la **Tercera Forma Normal (3NF)** y explica las decisiones de
diseño más relevantes.

## Entidades y claves

| Tabla | PK | FKs | Clave candidata relevante |
|---|---|---|---|
| `customers` | `customer_id` | — | `email` (única) |
| `categories` | `category_id` | — | `name` (única) |
| `products` | `product_id` | `category_id` | `name` |
| `orders` | `order_id` | `customer_id` | — |
| `order_items` | `order_item_id` | `order_id`, `product_id` | `(order_id, product_id)` (única) |
| `payments` | `payment_id` | `order_id` (única) | `order_id` |
| `reviews` | `review_id` | `order_item_id`, `customer_id` | `order_item_id` (única en la práctica) |

> **Nota de diseño:** las tablas llevan además una PK sintética autoincrementada
> (p.ej. `order_item_id`, `review_id`) además de las FKs que definen la
> cardinalidad. Esto es una práctica defensiva: permite que BigQuery y las
> herramientas de carga manejen filas de forma uniforme y facilita el debug de
> la carga. La **dependencia funcional** real se analiza sobre la clave
> mínima.

---

## 1NF — Primera Forma Normal

**Regla:** todos los atributos son atómicos y no hay grupos repetidos.

| Campo | Cumple 1NF | Motivo |
|---|---|---|
| `customers.country`, `city` | ✅ | Un solo valor por fila. No hay listas de países ni de ciudades. |
| `orders.shipping_country`, `shipping_city`, `shipping_address` | ✅ | Un único destino por pedido. Si un pedido tuviera múltiples destinos, se normalizaría en `shipments`. |
| `order_items.quantity`, `unit_price` | ✅ | Atómicos. Las múltiples líneas de un pedido viven en filas distintas de `order_items`, **no** como una columna `items: [ … ]`. |
| `products.brand`, `unit_price` | ✅ | Un solo valor por producto. No hay `brands: [ … ]` ni `prices: {…}`. |
| `reviews.rating` | ✅ | Un solo entero 1-5 por línea de pedido. No "ratings: [4, 5, 3]". |

**No hay grupos repetidos:** el detalle de cada pedido está en `order_items`
(filas) y no como una columna tipo `JSON` dentro de `orders`. ✅

---

## 2NF — Segunda Forma Normal

**Regla:** cumple 1NF **y** ningún atributo no-clave depende de solo *parte*
de la clave primaria cuando la clave es compuesta.

Análisis tabla por tabla (solo las con clave compuesta o candidata compuesta
son las relevantes):

### `order_items` — clave mínima `(order_id, product_id)`

Atributos no-clave y de quién dependen:

| Atributo | Depende de | ¿Dependencia parcial? |
|---|---|---|
| `quantity` | `(order_id, product_id)` | No — hay una cantidad por (pedido, producto), no por producto solo. |
| `unit_price` (snapshot) | `(order_id, product_id)` | No — el precio pagado puede variar entre pedidos para el mismo producto. |
| `discount` | `(order_id, product_id)` | No — mismo razonamiento. |
| `line_total` | `(order_id, product_id)` | No — derivado de los anteriores. |

✅ **Cumple 2NF.** Ningún atributo depende solo de `order_id` ni solo de
`product_id`.

### `reviews` — clave mínima `(order_item_id, customer_id)`

| Atributo | Depende de | ¿Dependencia parcial? |
|---|---|---|
| `rating` | `(order_item_id, customer_id)` | No — cada cliente puede valorar la misma línea una vez, y el rating es del *par* (línea, cliente). |
| `comment` | `(order_item_id, customer_id)` | No. |
| `created_at` | `(order_item_id, customer_id)` | No. |

✅ **Cumple 2NF.** (Además, `order_item_id` identifica ya al cliente vía
`order_items → orders → customers`, así que `customer_id` queda redundante
*como dato*, pero se mantiene como FK de integridad: una revisión la emite un
cliente sobre una línea concreta.)

### Tablas con clave simple

En `customers`, `categories`, `products`, `orders`, `payments` la clave
primaria es un solo campo (`customer_id`, etc.), por lo que no existe la noción
de "parte de la clave". **Cumplen 2NF automáticamente.**

---

## 3NF — Tercera Forma Normal

**Regla:** cumple 2NF **y** ningún atributo no-clave depende de otro atributo
no-clave (no hay dependencias transitivas).

### `customers`

| Atributo | Depende de | ¿Transitiva? |
|---|---|---|
| `country`, `city`, `email`, `phone` | `customer_id` | No. |
| `acquisition_channel` | `customer_id` | No — es una propiedad del cliente, no derivada de otra columna de la tabla. |
| `created_at` | `customer_id` | No. |

✅ **Cumple 3NF.**

### `categories`

`name` y `description` dependen de `category_id`. No hay cadena
`category_id → name → otra_cosa`. ✅

### `products`

| Atributo | Depende de | ¿Transitiva? |
|---|---|---|
| `category_id` | `product_id` | No (es FK, no dato derivado). |
| `name`, `brand`, `unit_cost`, `unit_price`, `stock`, `is_active` | `product_id` | No. |

✅ **Cumple 3NF.** No hay atributo que dependa de `category_id` (p.ej. un
`category_name` copiado en `products`) — eso sería una dependencia transitiva
`product_id → category_id → category_name`.

### `orders`

| Atributo | Depende de | ¿Transitiva? |
|---|---|---|
| `customer_id` | `order_id` | No (FK). |
| `order_status`, `shipping_*`, `order_date`, `shipped_date`, `delivered_date` | `order_id` | No. |

⚠️ **Pregunta clave del enunciado:** si añadieramos `customer_name` a `orders`,
habría una dependencia transitiva
`order_id → customer_id → customer_name`.
Eso **violaría 3NF** y además introduciría anomalías de actualización:
si el cliente cambia su nombre habría que actualizar *todos* sus pedidos.
**Decisión:** solo se almacena `customer_id` (FK); el nombre se obtiene con
JOIN.

### `order_items`

Ya analizado en 2NF. En 3NF: `line_total` es derivado de
`quantity × unit_price × (1 − discount)`. Técnicamente es una dependencia
funcional *redundante*, pero **no es una violación de 3NF** porque:

1. Depende de la PK completa `(order_id, product_id)`, no de otro no-clave.
2. Se calcula al insertar la línea y se conserva como *snapshot inmutable*:
   si más tarde cambiamos `unit_price` en `products`, la línea ya vendida
   no debe re-calcularse.

✅ **Cumple 3NF.**

### `payments`

| Atributo | Depende de | ¿Transitiva? |
|---|---|---|
| `order_id` (FK, única) | `payment_id` | No. |
| `payment_method`, `payment_status`, `amount`, `paid_at` | `payment_id` | No. |

⚠️ **Decisión importante:** `amount` **no** se lee de
`SUM(order_items.line_total)` al momento de leerlo. Se almacena en
`payments` como el importe *transaccionado* (puede diferir del total de las
líneas por descuentos globales, impuestos, cargos de envío, reembolsos parciales,
etc.). La relación con `orders` es **1:1** (un pago por pedido) con la FK
`order_id` marcada como `UNIQUE`.

Si `amount` dependiera transitivamente de `order_id` (p.ej. se calculara en
cada consulta como `JOIN orders → SUM(order_items)`), estaríamos duplicando
lógica y perdiendo la trazabilidad del pago real. **Decisión:** `payments`
es la fuente de verdad del importe. ✅

### `reviews`

`rating`, `comment`, `created_at` dependen de `review_id`. `customer_id` es
FK, no dato derivado. ✅

---

## Decisiones clave de diseño (resumen)

| # | Decisión | Justificación |
|---|---|---|
| 1 | `orders` ↔ `products` = **N:M** resuelto con `order_items` | Un pedido puede contener N productos; un producto puede aparecer en N pedidos. Necesaria la tabla intermedia. |
| 2 | `unit_price` en `order_items` (snapshot) | El precio pagado puede diferir del precio actual en `products.price` (descuentos, cambios de precio, promociones). Conservar el histórico de ventas es requisito de negocio. |
| 3 | `customer_name` **no** en `orders` | Violaría 3NF (dependencia transitiva). Se obtiene con `JOIN customers`. |
| 4 | `country`/`city` en `customers` (no en tabla `countries`) | El análisis es por *país del cliente*, no por entidad país. Una tabla `countries` añadiría complejidad sin beneficio claro en este dominio. |
| 5 | `payments.amount` en `payments` (no derivado de `order_items`) | El importe transaccionado puede diferir del total de líneas (descuentos globales, impuestos, cargos). `payments` es fuente de verdad del pago. |
| 6 | `reviews` enlazada a `order_items` (no a `orders`) | La valoración es sobre un producto concreto dentro de un pedido, no sobre el pedido completo. |
| 7 | `payments.order_id` = `UNIQUE` (relación 1:1) | Un pedido tiene un pago. Si hubiera múltiples pagos (split payments) se re-diseñaría con una tabla `payment_methods` intermedia. |
| 8 | `is_active` en `products` (soft delete) | Permite desactivar productos sin perder histórico en `order_items`. |
| 9 | Fechas `shipped_date`, `delivered_date` nulas en `orders` | Representan estados del ciclo de vida (`pending → confirmed → shipped → delivered → returned`); no todas las fechas existen en todo momento. |

---

## ¿Cumple el modelo 3NF?

**Sí.** Todas las tablas cumplen 1NF, 2NF y 3NF según el análisis anterior.
No hay dependencias parciales (2NF) ni dependencias transitivas (3NF) sobre
atributos no-clave.
