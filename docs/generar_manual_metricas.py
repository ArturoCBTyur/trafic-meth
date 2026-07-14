"""Genera un manual de LECTURA DE MÉTRICAS en PDF con diseño moderno.

Explica cada variable numérica que muestra el software (panel MÉTRICAS) y cada dato
del reporte exportado a Excel, para que el usuario interprete lo que ve.

Reutiliza el kit de diseño de generar_manual.py (mismo estilo visual).

Uso:
    python docs/generar_manual_metricas.py
    -> docs/Manual_Lectura_Metricas.pdf
"""

from __future__ import annotations

import os
import sys

import matplotlib

matplotlib.use("Agg")
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Rectangle

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from generar_manual import (  # noqa: E402  (reutiliza el kit de diseño)
    A4, AMBER, BG, BLUE, CARD, CW, CYAN, DIM, FAINT, GREEN, LINE, MX, PANEL,
    PURPLE, TXT, _badge, _card, _footer, _new_page, _text, _wrapped,
)


def _metric_card(ax, x, y, w, h, tag, tagc, desc, unit=""):
    """Tarjeta de una métrica: etiqueta con acento + descripción + unidad."""
    _card(ax, x, y - h, w, h, face=CARD, edge=LINE, lw=1.0)
    ax.add_patch(Rectangle((x, y - h + 0.006), 0.004, h - 0.012, color=tagc, zorder=2))
    _text(ax, x + 0.018, y - 0.016, tag, size=9.5, color=tagc, weight="bold")
    if unit:
        _text(ax, x + w - 0.015, y - 0.016, unit, size=8.5, color=DIM, ha="right")
    _wrapped(ax, x + 0.018, y - 0.033, desc, width=int((w / CW) * 96), size=9,
             color=TXT, leading=0.0155)


def _table(ax, x, y, rows, widths, headers, accent):
    """Tabla simple: cabecera con acento + filas alternadas."""
    rh = 0.026
    tw = sum(widths)
    # Cabecera
    _card(ax, x, y - rh, tw, rh, face=accent, edge=accent, radius=0.006)
    cx = x
    for h, w in zip(headers, widths):
        _text(ax, cx + 0.008, y - rh + 0.008, h, size=8.5, color=BG, weight="bold")
        cx += w
    yy = y - rh
    for i, row in enumerate(rows):
        face = PANEL if i % 2 else CARD
        _card(ax, x, yy - rh, tw, rh, face=face, edge=LINE, lw=0.6, radius=0.004)
        cx = x
        for j, (cell, w) in enumerate(zip(row, widths)):
            col = TXT if j == 0 else DIM
            wt = "bold" if j == 0 else "normal"
            _text(ax, cx + 0.008, yy - rh + 0.008, cell, size=8.3, color=col, weight=wt)
            cx += w
        yy -= rh
    return yy


# ------------------------------------------------------------------ Portada
def _cover(pdf):
    fig, ax = _new_page(pdf)
    import numpy as np
    grad = np.linspace(0, 1, 256).reshape(-1, 1)
    ax.imshow(grad, extent=[0, 1, 0.64, 1.0], aspect="auto",
              cmap=matplotlib.colormaps["viridis"], alpha=0.22, zorder=-5)
    ax.add_patch(Rectangle((0, 0), 1, 0.64, color=BG, zorder=-4))

    ax.plot([MX, MX + 0.16], [0.70, 0.70], color=GREEN, lw=3)
    _text(ax, MX, 0.66, "GUÍA DE INTERPRETACIÓN", size=13, color=GREEN, weight="bold")
    _text(ax, MX, 0.58, "Manual de Lectura", size=29, color=TXT, weight="bold")
    _text(ax, MX, 0.515, "de Métricas", size=29, color=TXT, weight="bold")
    _wrapped(ax, MX, 0.45,
             "Qué significa cada variable numérica que muestra el software y cada dato "
             "del reporte exportado a Excel.", width=58, size=13, color=DIM, leading=0.03)

    cards = [
        ("EN PANTALLA", "Panel MÉTRICAS en vivo", CYAN),
        ("EN EXCEL", "Reporte de sostenibilidad", GREEN),
        ("GLOSARIO", "Variables y unidades", PURPLE),
    ]
    cw = CW / 3 - 0.02
    for i, (t, d, c) in enumerate(cards):
        x = MX + i * (cw + 0.03)
        _card(ax, x, 0.29, cw, 0.09, face=CARD, edge=c, lw=1.2)
        _text(ax, x + 0.02, 0.36, t, size=8.5, color=c, weight="bold")
        _wrapped(ax, x + 0.02, 0.335, d, width=26, size=10.5, color=TXT, leading=0.02)

    _text(ax, MX, 0.06, "Generado con Claude Opus 4.8", size=8, color=FAINT)
    pdf.savefig(fig, facecolor=BG)
    plt_close(fig)


# ------------------------------------------------------------------ Panel software
def _panel_page(pdf):
    fig, ax = _new_page(pdf)
    _text(ax, MX, 0.94, "01 · El panel MÉTRICAS (en pantalla)", size=18, color=TXT, weight="bold")
    ax.plot([MX, MX + 0.10], [0.905, 0.905], color=CYAN, lw=2.5)
    _wrapped(ax, MX, 0.875,
             "A la derecha, el software muestra en tiempo real las variables de los tres "
             "métodos numéricos y del análisis ambiental. Cada tarjeta:", width=98,
             size=10, color=DIM)

    items = [
        ("FASE (centro)", AMBER,
         "Estado del semáforo: N-S, E-O o TRANSICIÓN. Las colas de un eje solo drenan "
         "cuando ese eje está en verde.", ""),
        ("UNIDAD III · Integración (Simpson 1/3)", CYAN,
         "Área bajo las colas ∫q(t)dt = retraso acumulado. Sube mientras hay congestión; "
         "es la base para el cálculo de CO2.", "veh-h"),
        ("UNIDAD IV · Colas (Heun)", PURPLE,
         "Longitud de cola ACTUAL por dirección (N-S, E-O, S-N, O-E). La barra y el número "
         "indican cuántos vehículos esperan en cada aproximación.", "vehículos"),
        ("UNIDAD I · Newton-Raphson", BLUE,
         "x = [g_NS, g_EW] son los tiempos de verde óptimos (s). |F(X)| es la norma del "
         "residuo: mide convergencia — verde si < 1e-4 (menor = mejor).", "s  /  —"),
        ("SOSTENIBILIDAD AMBIENTAL", GREEN,
         "CO2 total (kg) y Retraso (vh = veh-h) acumulados; Veh. entrada = conteo de "
         "sensores; Reduc. % aparece tras pulsar O (plan equitativo vs. optimizado).",
         "kg / vh / %"),
    ]
    y = 0.835
    h = 0.088
    for tag, c, desc, unit in items:
        _metric_card(ax, MX, y, CW, h, tag, c, desc, unit)
        y -= h + 0.014

    _footer(ax, 2)
    pdf.savefig(fig, facecolor=BG)
    plt_close(fig)


# ------------------------------------------------------------------ Excel
def _excel_page(pdf):
    fig, ax = _new_page(pdf)
    _text(ax, MX, 0.94, "02 · El reporte en Excel (tecla E)", size=18, color=TXT, weight="bold")
    ax.plot([MX, MX + 0.10], [0.905, 0.905], color=GREEN, lw=2.5)
    _wrapped(ax, MX, 0.875,
             "Al exportar, se genera un .xlsx con cuatro hojas. Estas son sus columnas y "
             "lo que representan:", width=98, size=10, color=DIM)

    sheets = [
        ("HOJA · Dashboard", GREEN,
         "KPIs: CO2 total (kg), Retraso acumulado (veh-h) y % Reducción. Tabla y gráfico "
         "Manual (reparto equitativo) vs. Optimizado (Newton)."),
        ("HOJA · Por Direccion", PURPLE,
         "Para N-S, E-O, S-N, O-E: Retraso (veh-h) y CO2 (kg). Gráfico de barras que revela "
         "qué eje concentra la congestión."),
        ("HOJA · Serie Temporal", CYAN,
         "Tiempo (s), Cola Total (vehículos) y CO2 Acumulado (kg), muestreados. Gráfico de "
         "líneas de doble eje: evolución de colas y emisiones."),
        ("HOJA · Impacto", AMBER,
         "Equivalentes ambientales: gasolina (L), CO2 por vehículo, reducción absoluta (kg), "
         "árboles, km evitados y carbón no quemado."),
    ]
    y = 0.835
    h = 0.082
    for tag, c, desc in sheets:
        _metric_card(ax, MX, y, CW, h, tag, c, desc)
        y -= h + 0.016

    # Nota
    y -= 0.005
    _card(ax, MX, y - 0.094, CW, 0.094, face=PANEL, edge=BLUE)
    _text(ax, MX + 0.02, y - 0.02, "CÓMO SE CALCULA LA REDUCCIÓN", size=9, color=BLUE, weight="bold")
    _wrapped(ax, MX + 0.02, y - 0.043,
             "La línea base es el reparto MANUAL equitativo (verde/2 a cada eje). El plan "
             "optimizado usa el reparto de Newton. Ambos se proyectan con Heun sobre el "
             "mismo horizonte y demanda → Reducción = (base − óptimo)/base × 100.",
             width=100, size=9, color=TXT, leading=0.0155)

    _footer(ax, 3)
    pdf.savefig(fig, facecolor=BG)
    plt_close(fig)


# ------------------------------------------------------------------ Glosario + lectura
def _glossary_page(pdf):
    fig, ax = _new_page(pdf)
    _text(ax, MX, 0.94, "03 · Glosario de variables", size=18, color=TXT, weight="bold")
    ax.plot([MX, MX + 0.10], [0.905, 0.905], color=PURPLE, lw=2.5)

    rows = [
        ("q_i", "vehículos", "Longitud de cola en la dirección i (Heun)"),
        ("∫ q(t) dt", "veh-h", "Área bajo la cola = Horas-Vehículo de retraso (Simpson)"),
        ("λ_NS, λ_EW", "veh/s", "Demanda media medida por sensores en cada eje"),
        ("g_NS, g_EW", "s", "Tiempo de verde de cada eje (solución de Newton)"),
        ("F(X), ‖F(X)‖", "—", "Residuo del sistema no lineal; norma → convergencia"),
        ("CO2", "kg", "Emisión por ralentí = retraso × r_idle"),
        ("Reducción", "%", "(base − óptimo)/base × 100; solo tras optimizar"),
        ("S", "veh/s", "Flujo de saturación: vehículos servidos en verde"),
        ("h", "s", "Paso temporal de integración (Heun / Simpson)"),
        ("r_idle", "kg CO2/h", "Tasa de emisión en ralentí (0.12 por defecto)"),
    ]
    widths = [0.16, 0.13, CW - 0.29]
    y = _table(ax, MX, 0.87, rows, widths, ["Variable", "Unidad", "Significado"], PURPLE)

    # Lectura rápida
    y -= 0.03
    _text(ax, MX, y, "LECTURA RÁPIDA · CÓMO INTERPRETAR", size=11, color=GREEN, weight="bold")
    y -= 0.03
    rules = [
        ("Retraso (veh-h) alto", "mucha congestión acumulada en el sistema."),
        ("Colas desbalanceadas", "un eje es la arteria; Newton le asignará más verde."),
        ("‖F(X)‖ ≈ 0", "Newton convergió: los tiempos de verde son fiables."),
        ("Reducción alta", "la demanda estaba desbalanceada y optimizar ayuda mucho."),
        ("Reducción ≈ 0 %", "la demanda ya está balanceada; poco que ganar (es correcto)."),
        ("Colas suben en rojo", "y bajan en verde: es la EDO de Heun respondiendo al semáforo."),
    ]
    for head, desc in rules:
        _text(ax, MX + 0.005, y, "▸", size=10, color=GREEN)
        _text(ax, MX + 0.03, y, head, size=9.6, color=TXT, weight="bold")
        y = _wrapped(ax, MX + 0.03, y - 0.019, desc, width=92, size=9.4,
                     color=DIM, leading=0.015) - 0.011

    _footer(ax, 4)
    pdf.savefig(fig, facecolor=BG)
    plt_close(fig)


def plt_close(fig):
    import matplotlib.pyplot as plt
    plt.close(fig)


def main() -> str:
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "Manual_Lectura_Metricas.pdf")
    with PdfPages(out) as pdf:
        _cover(pdf)
        _panel_page(pdf)
        _excel_page(pdf)
        _glossary_page(pdf)
    return out


if __name__ == "__main__":
    print(f"Manual generado: {main()}")
