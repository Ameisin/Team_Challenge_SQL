r"""
Genera el diagrama Entidad-Relación de TodoComponentes como PNG.

Uso:
    venv\Scripts\python.exe parte_2_modelo_bigquery/docs/generate_er_diagram.py

El resultado se escribe en `parte_2_modelo_bigquery/docs/er_diagram.png`.
"""
from __future__ import annotations

import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib import font_manager

# --- Definición del modelo (misma fuente de verdad que er_diagram.dbml) ---
TABLES = {
    "categories": {
        "pk": ["category_id int"],
        "cols": ["name string  (unique)", "description string"],
        "color": "#EAF3FF",
    },
    "customers": {
        "pk": ["customer_id int  PK"],
        "cols": [
            "first_name string",
            "last_name string",
            "email string  (unique)",
            "phone string",
            "country string",
            "city string",
            "acquisition_channel string",
            "created_at timestamp",
        ],
        "color": "#EAF3FF",
    },
    "products": {
        "pk": ["product_id int  PK"],
        "cols": [
            "category_id int  FK",
            "name string",
            "description string",
            "brand string",
            "unit_cost decimal",
            "unit_price decimal",
            "stock int",
            "is_active boolean",
            "created_at timestamp",
        ],
        "color": "#EAF3FF",
    },
    "orders": {
        "pk": ["order_id int  PK"],
        "cols": [
            "customer_id int  FK",
            "order_status string",
            "shipping_country string",
            "shipping_city string",
            "shipping_address string",
            "order_date timestamp",
            "shipped_date timestamp",
            "delivered_date timestamp",
        ],
        "color": "#F3EEFF",
    },
    "order_items": {
        "pk": ["order_item_id int  PK"],
        "cols": [
            "order_id int  FK",
            "product_id int  FK",
            "quantity int",
            "unit_price decimal",
            "discount decimal",
            "line_total decimal",
        ],
        "color": "#FFF6E6",
    },
    "payments": {
        "pk": ["payment_id int  PK"],
        "cols": [
            "order_id int  FK (unique)",
            "payment_method string",
            "payment_status string",
            "amount decimal",
            "paid_at timestamp",
        ],
        "color": "#EAF3FF",
    },
    "reviews": {
        "pk": ["review_id int  PK"],
        "cols": [
            "order_item_id int  FK",
            "customer_id int  FK",
            "rating int",
            "comment string",
            "created_at timestamp",
        ],
        "color": "#F3EEFF",
    },
}

# Posiciones de las tablas: (centro_x, centro_y) en coordenadas del lienzo
LAYOUT = {
    "categories":    (10,   90),
    "customers":     (10,   30),
    "products":      (30,   75),
    "orders":        (30,   25),
    "order_items":   (52,   50),
    "payments":      (30,   5),
    "reviews":       (52,   15),
}

# Aristas (relaciones) — cada una es: (src_table, dst_table, cardinality, style)
# cardinality: "1" / "N" / "M" — se dibuja en el extremo destino
EDGES = [
    ("categories", "products",    "1:N", "-"),
    ("customers",  "orders",      "1:N", "-"),
    ("orders",     "order_items", "1:N", "-"),
    ("products",   "order_items", "1:N", "-"),
    ("orders",     "payments",    "1:1", "-"),
    ("order_items","reviews",     "1:N", "-"),
    ("customers",  "reviews",     "1:N", "-"),
]


def _table_rect(ax, name: str):
    """Calcula y dibuja el rectángulo de una tabla. Devuelve (xmin, xmax, ymin, ymax)."""
    cx, cy = LAYOUT[name]
    t = TABLES[name]
    rows = len(t["cols"]) + len(t["pk"])
    row_h = 1.55
    width = 20
    height = row_h * (rows + 1) + 2
    x0 = cx - width / 2
    y0 = cy - height / 2

    # cuerpo
    body = patches.FancyBboxPatch(
        (x0, y0), width, height,
        boxstyle="round,pad=0.2,rounding_size=0.6",
        linewidth=1.4, edgecolor="#334155", facecolor=t["color"],
    )
    ax.add_patch(body)

    # header
    header_h = 2.6
    header = patches.FancyBboxPatch(
        (x0, y0 + height - header_h), width, header_h,
        boxstyle="round,pad=0.2,rounding_size=0.6",
        linewidth=1.4, edgecolor="#334155", facecolor="#334155",
    )
    ax.add_patch(header)
    ax.text(cx, y0 + height - header_h / 2, name,
            ha="center", va="center", color="white",
            fontsize=12, fontweight="bold", family="monospace")

    # rows
    top = y0 + height - header_h
    for i, col in enumerate(t["pk"] + t["cols"]):
        y = top - (i + 1) * row_h + row_h / 2
        ax.text(x0 + 1.5, y, col, ha="left", va="center",
                fontsize=9, family="monospace", color="#0f172a")

    return x0, x0 + width, y0, y0 + height


def _anchor(rect, towards: str):
    """Devuelve el punto de anclaje de `rect` que mira hacia `towards`."""
    xmin, xmax, ymin, ymax = rect
    cx = (xmin + xmax) / 2
    cy = (ymin + ymax) / 2
    if towards == "left":
        return xmin, cy
    if towards == "right":
        return xmax, cy
    if towards == "top":
        return cx, ymax
    return cx, ymin


def _best_directions(a, b):
    """Elige qué lados de cada tabla usan la conexión según la geometría."""
    acx, acy = ((a[0] + a[1]) / 2, (a[2] + a[3]) / 2)
    bcx, bcy = ((b[0] + b[1]) / 2, (b[2] + b[3]) / 2)
    dx, dy = bcx - acx, bcy - acy
    if abs(dx) > abs(dy):
        return ("right" if dx > 0 else "left"), ("left" if dx > 0 else "right")
    return ("top" if dy > 0 else "bottom"), ("bottom" if dy > 0 else "top")


def draw_diagram(out_path: str):
    fig, ax = plt.subplots(figsize=(17, 11), dpi=150)
    ax.set_xlim(0, 70)
    ax.set_ylim(0, 100)
    ax.set_aspect("equal")
    ax.axis("off")

    # Título
    ax.text(35, 97, "TodoComponentes — Modelo Entidad-Relación (3NF)",
            ha="center", va="center", fontsize=16, fontweight="bold")
    ax.text(35, 94.5, "Base de datos e-commerce · BigQuery · PK/FK en monospace",
            ha="center", va="center", fontsize=10, style="italic", color="#475569")

    # Primero dibuja las aristas (detrás) para que las tablas queden encima
    for src, dst, card, style in EDGES:
        ra = _table_rect_dummy(src)
        rb = _table_rect_dummy(dst)
        d_a, d_b = _best_directions(ra, rb)
        p1 = _anchor(ra, d_a)
        p2 = _anchor(rb, d_b)
        ax.annotate("", xy=p2, xytext=p1,
                    arrowprops=dict(arrowstyle="-", lw=1.4, color="#64748B",
                                   linestyle=style))
        # etiqueta de cardinalidad
        mx = (p1[0] + p2[0]) / 2
        my = (p1[1] + p2[1]) / 2
        ax.text(mx, my + 0.7, card, fontsize=8.5, color="#334155",
                ha="center", va="center",
                bbox=dict(boxstyle="round,pad=0.25", facecolor="white",
                          edgecolor="#CBD5E1", linewidth=0.8))

    # Ahora las tablas (encima)
    for name in TABLES:
        _table_rect(ax, name)

    # Leyenda (esquina inferior izquierda, zona libre del lienzo)
    legend = [
        ("PK", "Primary Key"),
        ("FK", "Foreign Key"),
        ("1:N", "Uno a muchos"),
        ("1:1", "Uno a uno"),
    ]
    for i, (sym, txt) in enumerate(legend):
        ax.text(3, 6 - i * 2.4, f"{sym}   {txt}", fontsize=9,
                color="#334155", ha="left", va="center", family="monospace")

    fig.tight_layout()
    fig.savefig(out_path, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"OK: diagrama escrito en {out_path}")


def _table_rect_dummy(name: str):
    """Misma geometría que _table_rect pero sin dibujar (para colocar aristas)."""
    cx, cy = LAYOUT[name]
    t = TABLES[name]
    rows = len(t["cols"]) + len(t["pk"])
    row_h = 1.55
    width = 20
    height = row_h * (rows + 1) + 2
    return cx - width / 2, cx + width / 2, cy - height / 2, cy + height / 2


if __name__ == "__main__":
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "er_diagram.png")
    draw_diagram(out)
