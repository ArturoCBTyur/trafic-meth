"""Genera un manual de usuario (playbook) académico en PDF con diseño moderno.

Documenta los métodos numéricos aplicados en el simulador (Newton-Raphson, Euler
Modificado/Heun y Simpson 1/3). Reutiliza el contenido didáctico de ModuloExplicativo
y renderiza las fórmulas con mathtext (sin LaTeX externo).

Uso:
    python docs/generar_manual.py
    -> docs/Manual_Metodos_Numericos.pdf
"""

from __future__ import annotations

import os
import sys
import textwrap

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from modulo_explicativo import (  # noqa: E402
    EULER_MODIFICADO, NEWTON_RAPHSON, SIMPSON, ModuloExplicativo,
)

# ------------------------------------------------------------------ Paleta
BG = "#0d1117"
PANEL = "#161b22"
CARD = "#21262d"
LINE = "#30363d"
TXT = "#e6edf3"
DIM = "#8b949e"
FAINT = "#5b6470"
CYAN = "#56d3e7"
BLUE = "#58a6ff"
GREEN = "#3fb950"
PURPLE = "#b084ff"
AMBER = "#d29922"

MONO = {"family": "DejaVu Sans Mono"}
A4 = (8.27, 11.69)
MX = 0.09          # margen horizontal
CW = 1 - 2 * MX    # ancho de contenido


def _new_page(pdf: PdfPages):
    fig = plt.figure(figsize=A4, facecolor=BG)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.add_patch(Rectangle((0, 0), 1, 1, color=BG, zorder=-10))
    return fig, ax


def _card(ax, x, y, w, h, face=CARD, edge=LINE, lw=1.0, radius=0.018, z=0):
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h, boxstyle=f"round,pad=0,rounding_size={radius}",
        facecolor=face, edgecolor=edge, linewidth=lw, zorder=z,
        mutation_aspect=A4[0] / A4[1]))


def _text(ax, x, y, s, size=10.5, color=TXT, weight="normal", ha="left",
          va="top", family=None, style="normal"):
    kw = {}
    if family:
        kw["family"] = family
    ax.text(x, y, s, fontsize=size, color=color, weight=weight, ha=ha, va=va,
            style=style, transform=ax.transAxes, **kw)


def _wrapped(ax, x, y, text, width=96, size=10.5, color=TXT, leading=0.0175):
    for line in textwrap.wrap(text, width=width):
        _text(ax, x, y, line, size=size, color=color)
        y -= leading
    return y


def _footer(ax, page_no: int):
    ax.plot([MX, 1 - MX], [0.045, 0.045], color=LINE, lw=0.8,
            transform=ax.transAxes)
    _text(ax, MX, 0.032, "Simulador de Tráfico 2D · Métodos Numéricos", size=8,
          color=FAINT)
    _text(ax, 1 - MX, 0.032, f"{page_no:02d}", size=8, color=FAINT, ha="right")


def _badge(ax, x, y, text, color):
    w = 0.0099 * len(text) + 0.028
    _card(ax, x, y - 0.018, w, 0.024, face=CARD, edge=color, lw=1.0, radius=0.012)
    _text(ax, x + 0.013, y - 0.0035, text, size=8.5, color=color, weight="bold")
    return w


# ------------------------------------------------------------------ Portada
def _cover(pdf):
    fig, ax = _new_page(pdf)
    # Franja de gradiente superior
    import numpy as np
    grad = np.linspace(0, 1, 256).reshape(-1, 1)
    ax.imshow(grad, extent=[0, 1, 0.62, 1.0], aspect="auto",
              cmap=matplotlib.colormaps["twilight_shifted"], alpha=0.28, zorder=-5)
    ax.add_patch(Rectangle((0, 0), 1, 0.62, color=BG, zorder=-4))

    ax.plot([MX, MX + 0.16], [0.70, 0.70], color=CYAN, lw=3)
    _text(ax, MX, 0.66, "PLAYBOOK ACADÉMICO", size=13, color=CYAN, weight="bold")
    _text(ax, MX, 0.58, "Manual de", size=30, color=TXT, weight="bold")
    _text(ax, MX, 0.51, "Métodos Numéricos", size=30, color=TXT, weight="bold")
    _text(ax, MX, 0.45, "Aplicados a un Simulador de Tráfico 2D en Tiempo Real",
          size=13, color=DIM)

    # Tarjetas de las tres unidades
    units = [
        ("UNIDAD I", "Newton-Raphson", "Sistemas no lineales", BLUE),
        ("UNIDAD III", "Simpson 1/3", "Integración numérica", CYAN),
        ("UNIDAD IV", "Euler Mod. (Heun)", "EDO / colas", PURPLE),
    ]
    cw = CW / 3 - 0.02
    for i, (u, n, d, c) in enumerate(units):
        x = MX + i * (cw + 0.03)
        _card(ax, x, 0.28, cw, 0.10, face=CARD, edge=c, lw=1.2)
        _text(ax, x + 0.02, 0.36, u, size=8.5, color=c, weight="bold")
        _text(ax, x + 0.02, 0.335, n, size=11.5, color=TXT, weight="bold")
        _text(ax, x + 0.02, 0.305, d, size=8.5, color=DIM)

    _card(ax, MX, 0.10, CW, 0.10, face=PANEL, edge=LINE)
    _text(ax, MX + 0.02, 0.18, "SOBRE ESTE DOCUMENTO", size=9, color=GREEN,
          weight="bold")
    _wrapped(ax, MX + 0.02, 0.155,
             "Guía académica y operativa de los tres métodos numéricos que gobiernan "
             "el simulador: su formulación, justificación, algoritmo paso a paso, "
             "dónde viven en el código y cómo se combinan para optimizar semáforos y "
             "estimar emisiones de CO2.", width=104, size=9.5, color=TXT, leading=0.016)
    _text(ax, MX, 0.06, "Generado con Claude Opus 4.8", size=8, color=FAINT)
    pdf.savefig(fig, facecolor=BG)
    plt.close(fig)


# ------------------------------------------------------------------ Intro + pipeline
def _intro(pdf):
    fig, ax = _new_page(pdf)
    _text(ax, MX, 0.94, "01 · Arquitectura numérica", size=20, color=TXT, weight="bold")
    ax.plot([MX, MX + 0.10], [0.905, 0.905], color=CYAN, lw=2.5)
    y = _wrapped(ax, MX, 0.87,
                 "El simulador acopla tres unidades de métodos numéricos en un único "
                 "lazo en tiempo real. La demanda medida por sensores alimenta a "
                 "Newton-Raphson, que reparte el verde de los semáforos; el método de "
                 "Heun evoluciona las colas resultantes; y Simpson 1/3 integra esas "
                 "colas para obtener el retraso y las emisiones de CO2.",
                 width=98, size=10.5, color=TXT)

    # Pipeline
    _text(ax, MX, y - 0.02, "FLUJO DE DATOS", size=10, color=CYAN, weight="bold")
    stages = [
        ("Sensores", "conteos → demanda λ", DIM),
        ("Newton-Raphson", "reparto de verde", BLUE),
        ("Heun (EDO)", "evolución de colas", PURPLE),
        ("Simpson 1/3", "área → CO2", CYAN),
    ]
    top = y - 0.055
    bh = 0.075
    bw = CW / 4 - 0.025
    centers = []
    for i, (t, d, c) in enumerate(stages):
        x = MX + i * (bw + 0.033)
        _card(ax, x, top - bh, bw, bh, face=CARD, edge=c, lw=1.2)
        _text(ax, x + bw / 2, top - 0.022, t, size=9.5, color=c, weight="bold", ha="center")
        _text(ax, x + bw / 2, top - 0.045, d, size=7.8, color=DIM, ha="center")
        centers.append((x + bw, top - bh / 2, x + bw + 0.033))
    for cx_end, cy, nx in centers[:-1]:
        ax.add_patch(FancyArrowPatch((cx_end + 0.004, cy), (nx - 0.004, cy),
                     arrowstyle="-|>", mutation_scale=12, color=FAINT, lw=1.4))

    # Resultado
    ry = top - bh - 0.05
    _card(ax, MX, ry - 0.085, CW, 0.085, face=PANEL, edge=GREEN, lw=1.2)
    _text(ax, MX + 0.02, ry - 0.02, "RESULTADO", size=9, color=GREEN, weight="bold")
    _wrapped(ax, MX + 0.02, ry - 0.042,
             "Un reparto de verde adaptado a la demanda que reduce la cola agregada y, "
             "por tanto, las emisiones. La comparación plan manual (equitativo) vs. plan "
             "optimizado se exporta a Excel con gráficos.", width=104, size=9.5,
             color=TXT, leading=0.016)

    # Nota de desacople
    ny = ry - 0.085 - 0.05
    _text(ax, MX, ny, "PRINCIPIOS DE DISEÑO", size=10, color=AMBER, weight="bold")
    notes = [
        "Backend numérico puro (numerical_engine.py): solo NumPy, sin dependencias de UI.",
        "Implementaciones manuales y explícitas (sin scipy) con fines pedagógicos.",
        "Cada método es independiente y reutilizable en otros contextos.",
    ]
    yy = ny - 0.028
    for n in notes:
        _text(ax, MX + 0.01, yy, "▸", size=10, color=AMBER)
        _wrapped(ax, MX + 0.035, yy, n, width=98, size=9.8, color=TXT, leading=0.016)
        yy -= 0.032

    _footer(ax, 2)
    pdf.savefig(fig, facecolor=BG)
    plt.close(fig)


# ------------------------------------------------------------------ Página de método
def _method_page(pdf, leccion, formulas, codigo, accent, page_no, extra=None):
    fig, ax = _new_page(pdf)
    _badge(ax, MX, 0.95, leccion.unidad.upper(), accent)
    _text(ax, MX, 0.915, leccion.nombre, size=20, color=TXT, weight="bold")
    ax.plot([MX, MX + 0.10], [0.882, 0.882], color=accent, lw=2.5)

    # Caja de fórmula
    fh = 0.10 if len(formulas) == 1 else 0.135
    fy = 0.87 - fh
    _card(ax, MX, fy, CW, fh, face="#0f1720", edge=accent, lw=1.2)
    _text(ax, MX + 0.02, 0.855, "FÓRMULA", size=8.5, color=accent, weight="bold")
    fyy = fy + fh - 0.045
    for f in formulas:
        ax.text(0.5, fyy, f, fontsize=15, color=TXT, ha="center", va="center",
                transform=ax.transAxes)
        fyy -= 0.05

    y = fy - 0.04

    def block(title, text, color, y0):
        _text(ax, MX, y0, title, size=10.5, color=color, weight="bold")
        return _wrapped(ax, MX, y0 - 0.025, text, width=100, size=10, color=TXT,
                        leading=0.017) - 0.012

    y = block("OBJETIVO EN EL SIMULADOR", leccion.objetivo, GREEN, y)
    y = block("JUSTIFICACIÓN ACADÉMICA", leccion.justificacion, AMBER, y)

    # Paso a paso
    _text(ax, MX, y, "ALGORITMO PASO A PASO", size=10.5, color=PURPLE, weight="bold")
    y -= 0.026
    for paso in leccion.pasos:
        y = _wrapped(ax, MX + 0.005, y, paso, width=98, size=9.8, color=TXT,
                     leading=0.016) - 0.006

    # En el código
    y -= 0.012
    ch = 0.032 + 0.017 * len(codigo)
    _card(ax, MX, y - ch, CW, ch, face=PANEL, edge=CYAN, lw=1.0)
    _text(ax, MX + 0.02, y - 0.009, "EN EL CÓDIGO", size=8.5, color=CYAN, weight="bold")
    cy = y - 0.034
    for c in codigo:
        _text(ax, MX + 0.02, cy, c, size=8.8, color=DIM, family="DejaVu Sans Mono")
        cy -= 0.017

    _footer(ax, page_no)
    pdf.savefig(fig, facecolor=BG)
    plt.close(fig)


# ------------------------------------------------------------------ Guía de uso
def _guide(pdf):
    fig, ax = _new_page(pdf)
    _text(ax, MX, 0.94, "05 · Guía de uso", size=20, color=TXT, weight="bold")
    ax.plot([MX, MX + 0.10], [0.905, 0.905], color=GREEN, lw=2.5)

    _text(ax, MX, 0.87, "CONTROLES", size=10.5, color=CYAN, weight="bold")
    controls = [
        ("1 – 4", "Inyectar vehículos en cada entrada (N-S, E-O, S-N, O-E)."),
        ("O", "Optimizar: mide demanda, resuelve Newton, proyecta y aplica el reparto."),
        ("E", "Exportar el reporte de sostenibilidad a Excel con gráficos."),
        ("H", "Ayuda didáctica: overlay con fórmula, objetivo y pasos de cada método."),
        ("M", "Activar / silenciar la música de fondo."),
        ("R", "Reiniciar la simulación (nuevo patrón de demanda)."),
        ("ESC", "Salir."),
    ]
    y = 0.845
    for k, d in controls:
        _card(ax, MX, y - 0.019, 0.075, 0.026, face=CARD, edge=LINE, radius=0.01)
        _text(ax, MX + 0.0375, y - 0.006, k, size=9, color=CYAN, weight="bold", ha="center")
        _wrapped(ax, MX + 0.095, y, d, width=88, size=9.8, color=TXT, leading=0.016)
        y -= 0.034

    y -= 0.02
    _text(ax, MX, y, "FLUJO RECOMENDADO", size=10.5, color=BLUE, weight="bold")
    y -= 0.028
    steps = [
        "Deja correr unos segundos: la demanda ambiental es asimétrica (arteria vs. secundaria).",
        "Observa las colas crecer en rojo y drenar en verde (método de Heun).",
        "Pulsa O para optimizar; el reparto de verde se adapta a la demanda medida.",
        "Compara el % de reducción de CO2 en el panel de métricas.",
        "Pulsa E para exportar el reporte Excel con el análisis comparativo.",
    ]
    for i, s in enumerate(steps, 1):
        _text(ax, MX + 0.005, y, f"{i}.", size=10, color=BLUE, weight="bold")
        y = _wrapped(ax, MX + 0.03, y, s, width=96, size=9.8, color=TXT, leading=0.016) - 0.008

    y -= 0.015
    _card(ax, MX, y - 0.11, CW, 0.11, face=PANEL, edge=GREEN)
    _text(ax, MX + 0.02, y - 0.02, "SALIDA: REPORTE EXCEL", size=9, color=GREEN, weight="bold")
    _wrapped(ax, MX + 0.02, y - 0.042,
             "El .xlsx incluye Dashboard con KPIs (CO2, retraso, % reducción), desglose "
             "por dirección, serie temporal de colas y CO2 acumulado, y equivalentes "
             "ambientales (árboles, km, gasolina). Las colas se integran con Simpson 1/3.",
             width=100, size=9.5, color=TXT, leading=0.016)

    _footer(ax, 6)
    pdf.savefig(fig, facecolor=BG)
    plt.close(fig)


def main() -> str:
    modulo = ModuloExplicativo()
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "Manual_Metodos_Numericos.pdf")

    formulas = {
        NEWTON_RAPHSON: [r"$J(X_k)\,\Delta X = -F(X_k) \quad\Rightarrow\quad "
                         r"X_{k+1} = X_k + \Delta X$"],
        EULER_MODIFICADO: [
            r"$\tilde{q}_{i+1} = q_i + h\,f(t_i, q_i)$",
            r"$q_{i+1} = q_i + \frac{h}{2}\left[f(t_i,q_i) + "
            r"f(t_{i+1}, \tilde{q}_{i+1})\right]$"],
        SIMPSON: [r"$\int_{a}^{b} q(t)\,dt \approx \frac{h}{3}\left[q_0 + "
                  r"4\sum q_{impar} + 2\sum q_{par} + q_n\right]$"],
    }
    codigo = {
        NEWTON_RAPHSON: [
            "numerical_engine.py → solve_green_split(), green_split_residuals()",
            "frontend.py → optimize_traffic_signals()  (usa la demanda medida)"],
        EULER_MODIFICADO: [
            "numerical_engine.py → heun_queue_update(), queue_rhs()",
            "step() y project_emissions() integran las colas con Heun"],
        SIMPSON: [
            "numerical_engine.py → composite_simpson(), integrate_simpson()",
            "SustainabilityAnalyzer.calculate_total_emissions() → área → CO2"],
    }
    accents = {NEWTON_RAPHSON: BLUE, EULER_MODIFICADO: PURPLE, SIMPSON: CYAN}
    order = [NEWTON_RAPHSON, SIMPSON, EULER_MODIFICADO]

    with PdfPages(out) as pdf:
        _cover(pdf)
        _intro(pdf)
        for i, mid in enumerate(order, start=3):
            _method_page(pdf, modulo.obtener_informacion(mid), formulas[mid],
                         codigo[mid], accents[mid], i)
        _guide(pdf)

    return out


if __name__ == "__main__":
    path = main()
    print(f"Manual generado: {path}")
