"""Backend numérico puro para un simulador de tráfico dinámico en 2D.

Este módulo implementa tres componentes numéricos de forma manual:
1. Integración numérica (Regla de Simpson 1/3 compuesta) para el área bajo q(t) → CO2.
2. Newton-Raphson matricial para resolver un sistema no lineal de equilibrio de flujos.
3. Método de Heun (Euler modificado) para la evolución temporal de colas.
"""

from __future__ import annotations

from typing import Callable

import numpy as np


def composite_simpson(q_list: list[float], h: float) -> float:
    """Regla de Simpson 1/3 compuesta para el área bajo la curva de q(t).

    Integra un arreglo discreto de muestras (p. ej. la longitud de cola de vehículos
    q_list) espaciadas uniformemente un paso h, aproximando ∫ q dt.

    Manejo automático del número de intervalos:
      - n intervalos par  → Simpson 1/3 compuesta pura.
      - n intervalos impar → Simpson 1/3 sobre los primeros (n-1) intervalos (par) y
        Regla del Trapecio SOLO en el último tramo (evita perder ese subintervalo).
      - n == 1            → un único intervalo: Trapecio.
      - n <= 0 o h <= 0   → 0.

    Regla compuesta (m par):  h/3 · [ y0 + 4·Σ(impares) + 2·Σ(pares internos) + ym ]

    Args:
        q_list: muestras de la función a integrar (colas de vehículos).
        h: paso uniforme entre muestras (intervalo temporal).

    Returns:
        Área bajo la curva (p. ej. Horas-Vehículo si q está en veh y h en h).
    """
    y = [float(v) for v in q_list]
    n = len(y) - 1  # número de intervalos
    if n <= 0 or h <= 0:
        return 0.0
    if n == 1:
        # Un solo intervalo: no aplica Simpson → Trapecio
        return 0.5 * h * (y[0] + y[1])

    def _simpson(nodes: list[float], m: int) -> float:
        """Simpson 1/3 compuesta sobre m intervalos (m par) usando nodes[0..m]."""
        s = nodes[0] + nodes[m]
        for i in range(1, m):
            s += (4.0 if i % 2 == 1 else 2.0) * nodes[i]
        return h * s / 3.0

    if n % 2 == 1:
        # Impar: Simpson en los primeros (n-1) intervalos + Trapecio en el último tramo
        area = _simpson(y, n - 1)
        area += 0.5 * h * (y[n - 1] + y[n])
        return area

    return _simpson(y, n)


class TrafficSimulationEngine:
    """Motor numérico para la simulación de tráfico con métodos explícitos."""

    def __init__(self, h: float = 0.1) -> None:
        self.h = h
        self.queue_state = [0.0, 0.0, 0.0, 0.0]
        self.discrete_vehicle_counts = [0, 0, 0, 0]

        self.current_time = 0.0
        self.newton_solution: np.ndarray | None = None
        self.newton_residual_norm = float("inf")

    def integrate_simpson(self, q_list: list[float], h: float | None = None) -> float:
        """Unidad III: área bajo q(t) por Simpson 1/3 compuesta (ver composite_simpson)."""
        return composite_simpson(q_list, self.h if h is None else h)

    def queue_rhs(
        self,
        t: float,
        q: float,
        entry_rate: float | Callable[[float], float],
        exit_rate: float | Callable[[float], float],
    ) -> float:
        """Evalúa el lado derecho de la EDO de la longitud de la cola.

        La ecuación es:

        dq/dt = Tasa_Entrada(t) - Tasa_Salida(t)

        con la restricción física q(t) >= 0.
        """
        if callable(entry_rate):
            arrival = float(entry_rate(t))
        else:
            arrival = float(entry_rate)

        if callable(exit_rate):
            departure = float(exit_rate(t))
        else:
            departure = float(exit_rate)

        return arrival - departure

    def heun_queue_update(
        self,
        q_previous: float,
        t_current: float,
        h: float,
        entry_rate: float | Callable[[float], float],
        exit_rate: float | Callable[[float], float],
    ) -> float:
        """Implementa el método predictor-corrector de Heun para la cola.

        Predictor:
            q_tilde_{i+1} = q_i + h f(t_i, q_i)

        Corrector:
            q_{i+1} = q_i + (h/2) [f(t_i, q_i) + f(t_{i+1}, q_tilde_{i+1})]

        El resultado se truncará a cero para respetar la condición física de no colas
        negativas.
        """
        f0 = self.queue_rhs(t_current, q_previous, entry_rate, exit_rate)
        q_pred = q_previous + h * f0
        q_pred = max(0.0, q_pred)

        f1 = self.queue_rhs(t_current + h, q_pred, entry_rate, exit_rate)
        q_next = q_previous + 0.5 * h * (f0 + f1)
        return max(0.0, q_next)

    # Parámetros físicos del modelo de cola por dirección
    SATURATION_FLOW = 0.9      # veh/s que salen cuando el semáforo está en verde
    ARRIVAL_SCALE = 0.02       # conversión de conteo de sensor a tasa de llegada
    ARRIVAL_CAP = 0.6          # tope de tasa de llegada (evita colas ilimitadas)

    def step(
        self,
        discrete_counts: list[int] | None = None,
        dt: float | None = None,
        green_mask: list[bool] | None = None,
    ) -> dict[str, list[float]]:
        """Actualiza el estado del sistema a partir de conteos discretos y métodos numéricos.

        Args:
            green_mask: lista booleana [N-S, E-O, S-N, O-E]. Cuando una dirección tiene
                verde, sus vehículos salen (drenan la cola); en rojo solo se acumulan.
                Esto acopla el temporizador de semáforos (frontend) con la EDO de colas.
        """
        if dt is None:
            dt = self.h

        if discrete_counts is not None:
            self.discrete_vehicle_counts = [max(0, c) for c in discrete_counts]

        for index, queue_value in enumerate(self.queue_state):
            # Tasa de llegada acotada (proporcional a la demanda detectada)
            arrival_rate = min(
                self.ARRIVAL_CAP,
                self.ARRIVAL_SCALE * self.discrete_vehicle_counts[index],
            )
            # Tasa de salida: solo drena en verde (acoplada al semáforo)
            has_green = green_mask[index] if green_mask is not None else True
            departure_rate = self.SATURATION_FLOW if has_green else 0.0
            self.queue_state[index] = self.heun_queue_update(
                queue_value,
                self.current_time,
                dt,
                arrival_rate,
                departure_rate,
            )

        self.current_time += dt
        return {"queues": self.queue_state}

    # ------------------------------------------------------------------
    # OPTIMIZACIÓN DE SEMÁFOROS (acopla Unidad I + III + IV)
    # ------------------------------------------------------------------
    def green_split_residuals(
        self, x: np.ndarray | list[float],
        lambda_ns: float, lambda_ew: float, g_total: float,
    ) -> np.ndarray:
        """Sistema no lineal para el reparto óptimo de verde entre los dos ejes.

        Dado el flujo de demanda medido en cada eje (lambda_ns, lambda_ew), se busca
        el reparto de verde X=[g_ns, g_ew] que iguala el grado de saturación de ambos
        ejes (x_i = lambda_i / (s * g_i / C) → igualar lambda_i / g_i), manteniendo el
        presupuesto total de verde fijo:

            F1(X) = lambda_ns / g_ns - lambda_ew / g_ew   (igualar saturación)
            F2(X) = g_ns + g_ew - g_total                 (presupuesto de verde)
        """
        g_ns = max(1e-3, float(x[0]))
        g_ew = max(1e-3, float(x[1]))
        f1 = lambda_ns / g_ns - lambda_ew / g_ew
        f2 = g_ns + g_ew - g_total
        return np.array([f1, f2], dtype=float)

    def solve_green_split(
        self, lambda_ns: float, lambda_ew: float, g_total: float,
        initial_guess: np.ndarray | list[float] | None = None,
        tol: float = 1e-8, max_iter: int = 50,
    ) -> dict[str, object]:
        """Newton-Raphson matricial (Jacobiana numérica) para el reparto de verde.

        Resuelve green_split_residuals = 0 con J(X_k) ΔX = -F(X_k). Si no hay demanda
        en ningún eje el sistema es degenerado y se devuelve un reparto equitativo.
        """
        if lambda_ns <= 1e-9 and lambda_ew <= 1e-9:
            x = np.array([g_total / 2.0, g_total / 2.0])
            self.newton_solution = x
            self.newton_residual_norm = 0.0
            return {"solution": x, "converged": True, "residual_norm": 0.0, "iterations": 0}

        if initial_guess is None:
            initial_guess = np.array([g_total / 2.0, g_total / 2.0])
        x = np.asarray(initial_guess, dtype=float)

        converged = False
        iterations = 0
        for k in range(max_iter):
            iterations = k + 1
            f_value = self.green_split_residuals(x, lambda_ns, lambda_ew, g_total)
            if float(np.linalg.norm(f_value)) < tol:
                converged = True
                break

            jacobian = np.zeros((2, 2), dtype=float)
            for j in range(2):
                epsilon = 1e-6 * (1.0 + abs(x[j]))
                x_pert = x.copy()
                x_pert[j] += epsilon
                f_pert = self.green_split_residuals(x_pert, lambda_ns, lambda_ew, g_total)
                jacobian[:, j] = (f_pert - f_value) / epsilon

            try:
                delta_x = np.linalg.solve(jacobian, -f_value)
            except np.linalg.LinAlgError:
                break
            x = x + delta_x
            if float(np.linalg.norm(delta_x)) < tol:
                converged = True
                break

        self.newton_solution = x
        self.newton_residual_norm = float(
            np.linalg.norm(self.green_split_residuals(x, lambda_ns, lambda_ew, g_total)))
        return {
            "solution": x,
            "converged": converged,
            "residual_norm": self.newton_residual_norm,
            "iterations": iterations,
        }

    AXIS_SATURATION = 1.6  # veh/s servidos por un eje en verde (con holgura vs demanda)

    def project_emissions(
        self, g_ns: float, g_ew: float, lambda_ns: float, lambda_ew: float,
        red: float = 5.0, horizon: float = 90.0, h: float = 0.1,
        co2_idle_rate: float = 0.12, saturation: float | None = None,
    ) -> dict[str, float]:
        """Proyecta emisiones bajo un plan de semáforos usando el método de Heun.

        Simula (determinísticamente) la evolución de las colas agregadas de cada eje
        sobre un horizonte fijo, ciclando el semáforo con los tiempos dados, e integra
        q(t) por trapezoides para obtener Horas-Vehículo y CO2. Permite comparar el
        plan manual vs. el optimizado sobre las MISMAS llegadas → reducción real.
        """
        sat = self.AXIS_SATURATION if saturation is None else saturation
        period = g_ns + g_ew + 2.0 * red

        def ns_green(t: float) -> bool:
            return (t % period) < g_ns

        def ew_green(t: float) -> bool:
            phase = t % period
            return g_ns + red <= phase < g_ns + red + g_ew

        exit_ns = lambda t: sat if ns_green(t) else 0.0
        exit_ew = lambda t: sat if ew_green(t) else 0.0

        q_ns, q_ew, t = 0.0, 0.0, 0.0
        times = [0.0]
        traj_ns = [0.0]
        traj_ew = [0.0]
        n_steps = int(horizon / h)
        for _ in range(n_steps):
            q_ns = self.heun_queue_update(q_ns, t, h, lambda_ns, exit_ns)
            q_ew = self.heun_queue_update(q_ew, t, h, lambda_ew, exit_ew)
            t += h
            times.append(t)
            traj_ns.append(q_ns)
            traj_ew.append(q_ew)

        # Unidad III: el área bajo cada cola se integra con Simpson 1/3 compuesta.
        vh_ns = composite_simpson(traj_ns, h)
        vh_ew = composite_simpson(traj_ew, h)
        veh_hours = vh_ns + vh_ew

        return {
            "co2": veh_hours * co2_idle_rate,
            "veh_hours": veh_hours,
            "vh_ns": vh_ns,
            "vh_ew": vh_ew,
            "co2_ns": vh_ns * co2_idle_rate,
            "co2_ew": vh_ew * co2_idle_rate,
            "times": times,
            "q_ns": traj_ns,
            "q_ew": traj_ew,
        }


class SustainabilityAnalyzer:
    """Analizador de sostenibilidad basado en UNA sola fuente de verdad.

    Todas las cifras reportadas (CO2, retraso, desglose, reducción y el reporte Excel)
    provienen de la MISMA proyección: engine.project_emissions() bajo la demanda medida,
    que corre Heun e integra con Simpson 1/3. Así el número mostrado en pantalla y el
    porcentaje de reducción son siempre coherentes entre sí.

    El estado "actual" (self.current) es la proyección del plan aplicado; baseline y
    optimized son proyecciones del reparto equitativo y del reparto Newton sobre la
    misma demanda y horizonte.
    """

    DIRECTIONS = ["N-S", "E-O", "S-N", "O-E"]

    def __init__(self, co2_idle_rate: float = 0.12) -> None:
        self.co2_idle_rate = co2_idle_rate
        self.current: dict | None = None          # proyección del plan aplicado
        self.demand: tuple[float, float] = (0.0, 0.0)
        self.baseline_emissions = 0.0
        self.optimized_emissions = 0.0
        self.optimization_applied = False

    def set_current(self, projection: dict, demand: tuple[float, float] | None = None) -> None:
        """Registra la proyección del plan actualmente aplicado (fuente de verdad)."""
        self.current = projection
        if demand is not None:
            self.demand = demand

    def _per_direction(self) -> tuple[list[float], list[float]]:
        """Reparte el veh-h/CO2 por eje a las 4 direcciones (mitad a cada aproximación)."""
        if not self.current:
            return [0.0] * 4, [0.0] * 4
        vh_ns, vh_ew = self.current["vh_ns"] / 2, self.current["vh_ew"] / 2
        vh = [vh_ns, vh_ew, vh_ns, vh_ew]                     # N-S, E-O, S-N, O-E
        co2 = [v * self.co2_idle_rate for v in vh]
        return vh, co2

    def calculate_total_emissions(self) -> dict[str, float]:
        """Métricas totales tomadas de la proyección actual (única fuente)."""
        if not self.current:
            return {"total_co2": 0.0, "total_veh_hours": 0.0,
                    "average_queue_time": 0.0, "emissions_per_vehicle": 0.0}
        total_co2 = float(self.current["co2"])
        total_vh = float(self.current["veh_hours"])
        return {
            "total_co2": total_co2,
            "total_veh_hours": total_vh,
            "average_queue_time": total_vh / 4.0,
            "emissions_per_vehicle": total_co2 / total_vh if total_vh > 0 else 0.0,
        }

    def set_baseline(self, co2_value: float) -> None:
        """Fija la línea base = proyección del plan equitativo (misma demanda/horizonte)."""
        self.baseline_emissions = float(co2_value)

    def set_optimized(self, co2_value: float) -> None:
        """Fija el plan optimizado = proyección del reparto Newton (misma base)."""
        self.optimized_emissions = float(co2_value)
        self.optimization_applied = True

    def export_to_excel(self, filename: str = "reporte_sostenibilidad.xlsx") -> str:
        """Exporta un reporte moderno en Excel (.xlsx) con dashboard y gráficos.

        Genera un libro con 4 hojas:
          - "Dashboard": KPIs con estilo tipo tarjeta + gráfico comparativo.
          - "Por Direccion": desglose de retraso/CO2 por dirección + gráfico de barras.
          - "Serie Temporal": evolución de colas y CO2 acumulado + gráfico de líneas.
          - "Impacto": equivalentes ambientales (árboles, km, gasolina, carbón).

        Único método de reporte del sistema (reemplaza al TXT/CSV legado).

        Returns:
            Ruta del archivo .xlsx guardado (con timestamp).
        """
        import os
        from datetime import datetime

        from openpyxl import Workbook
        from openpyxl.chart import BarChart, LineChart, Reference, Series
        from openpyxl.chart.label import DataLabelList
        from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
        from openpyxl.utils import get_column_letter
        from openpyxl.worksheet.properties import PageSetupProperties

        def fit_page(sheet) -> None:
            """Ajusta la hoja a una página de ancho, horizontal (para impresión/PDF)."""
            sheet.page_setup.orientation = "landscape"
            sheet.page_setup.fitToWidth = 1
            sheet.page_setup.fitToHeight = 0
            sheet.sheet_properties.pageSetUpPr = PageSetupProperties(fitToPage=True)

        base, _ = os.path.splitext(filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = f"{base}_{timestamp}.xlsx"

        em = self.calculate_total_emissions()
        directions = ["N-S", "E-O", "S-N", "O-E"]
        dir_colors = ["58A6FF", "56D3E7", "B084FF", "FF945C"]
        proj = self.current or {"times": [0.0], "q_ns": [0.0], "q_ew": [0.0]}
        vh_dir, co2_dir = self._per_direction()
        horizon = proj["times"][-1] if proj["times"] else 0.0

        # --- Paleta / estilos ---
        DARK = "0D1117"
        PANEL = "161B22"
        CARD = "21262D"
        ACCENT = "58A6FF"
        GREEN = "3FB950"
        AMBER = "D29922"
        TXT = "E6EDF3"
        MUTED = "8B949E"
        WHITE = "FFFFFF"

        def fill(hexc: str) -> PatternFill:
            return PatternFill("solid", fgColor=hexc)

        thin = Side(style="thin", color="30363D")
        box = Border(left=thin, right=thin, top=thin, bottom=thin)

        wb = Workbook()

        # ==================== HOJA 1: DASHBOARD ====================
        ws = wb.active
        ws.title = "Dashboard"
        ws.sheet_view.showGridLines = False
        ws.sheet_properties.tabColor = ACCENT
        fit_page(ws)
        for col in range(1, 10):
            ws.column_dimensions[get_column_letter(col)].width = 15

        # Banner
        ws.merge_cells("A1:I2")
        c = ws["A1"]
        c.value = "REPORTE DE SOSTENIBILIDAD  ·  Smart Intersection"
        c.font = Font(name="Segoe UI", size=20, bold=True, color=WHITE)
        c.fill = fill(DARK)
        c.alignment = Alignment(horizontal="left", vertical="center", indent=1)
        ws.merge_cells("A3:I3")
        s = ws["A3"]
        s.value = f"Simulador de Tráfico 2D — Análisis Ambiental   ·   Generado {datetime.now():%Y-%m-%d %H:%M}"
        s.font = Font(name="Segoe UI", size=10, italic=True, color=MUTED)
        s.fill = fill(PANEL)
        s.alignment = Alignment(horizontal="left", vertical="center", indent=1)
        ws.row_dimensions[1].height = 22
        ws.row_dimensions[2].height = 22
        ws.row_dimensions[3].height = 20

        reduction = self.baseline_emissions - self.optimized_emissions
        reduction_pct = (reduction / self.baseline_emissions * 100
                         if self.optimization_applied and self.baseline_emissions > 0 else 0.0)

        # KPI cards (cada tarjeta ocupa 3 columnas)
        kpis = [
            ("CO2 TOTAL", f"{em['total_co2']:.3f} kg", ACCENT),
            ("RETRASO ACUMULADO", f"{em['total_veh_hours']:.2f} veh-h", AMBER),
            ("REDUCCION CONTAMINACION", f"{reduction_pct:.1f} %", GREEN),
        ]
        start_row = 5
        for i, (label, value, color) in enumerate(kpis):
            col0 = 1 + i * 3
            l = get_column_letter(col0)
            r = get_column_letter(col0 + 2)
            ws.merge_cells(f"{l}{start_row}:{r}{start_row}")
            ws.merge_cells(f"{l}{start_row + 1}:{r}{start_row + 2}")
            lc = ws[f"{l}{start_row}"]
            lc.value = label
            lc.font = Font(name="Segoe UI", size=9, bold=True, color=MUTED)
            lc.fill = fill(CARD)
            lc.alignment = Alignment(horizontal="left", vertical="center", indent=1)
            vc = ws[f"{l}{start_row + 1}"]
            vc.value = value
            vc.font = Font(name="Segoe UI", size=22, bold=True, color=color)
            vc.fill = fill(CARD)
            vc.alignment = Alignment(horizontal="left", vertical="center", indent=1)
            for rr in range(start_row, start_row + 3):
                for cc in range(col0, col0 + 3):
                    ws.cell(row=rr, column=cc).fill = fill(CARD)
        ws.row_dimensions[start_row].height = 18
        ws.row_dimensions[start_row + 1].height = 24
        ws.row_dimensions[start_row + 2].height = 18

        # Tabla comparativa (datos para gráfico) — filas 10+
        hdr_row = 10
        ws.cell(row=hdr_row, column=1, value="Escenario").font = Font(bold=True, color=TXT)
        ws.cell(row=hdr_row, column=2, value="CO2 (kg)").font = Font(bold=True, color=TXT)
        for cc in (1, 2):
            ws.cell(row=hdr_row, column=cc).fill = fill("1F6FEB")
            ws.cell(row=hdr_row, column=cc).border = box
        comp = [
            ("Manual (base)", self.baseline_emissions if self.optimization_applied else em["total_co2"]),
            ("Optimizado", self.optimized_emissions if self.optimization_applied else em["total_co2"]),
        ]
        for i, (name, val) in enumerate(comp):
            ws.cell(row=hdr_row + 1 + i, column=1, value=name).border = box
            vcell = ws.cell(row=hdr_row + 1 + i, column=2, value=round(val, 4))
            vcell.number_format = "0.000"
            vcell.border = box

        chart = BarChart()
        chart.type = "col"
        chart.title = "Emisiones: Manual vs Optimizado"
        chart.height = 7.5
        chart.width = 13
        chart.y_axis.title = "kg CO2"
        chart.legend = None
        data = Reference(ws, min_col=2, min_row=hdr_row, max_row=hdr_row + 2)
        cats = Reference(ws, min_col=1, min_row=hdr_row + 1, max_row=hdr_row + 2)
        chart.add_data(data, titles_from_data=True)
        chart.set_categories(cats)
        chart.dLbls = DataLabelList()
        chart.dLbls.showVal = True
        chart.dLbls.showSerName = False
        chart.dLbls.showCatName = False
        chart.dLbls.showLegendKey = False
        ws.add_chart(chart, "A15")

        # ==================== HOJA 2: POR DIRECCION ====================
        wd = wb.create_sheet("Por Direccion")
        wd.sheet_view.showGridLines = False
        wd.sheet_properties.tabColor = "B084FF"
        fit_page(wd)
        headers = ["Direccion", "Retraso (veh-h)", "CO2 (kg)"]
        for j, h in enumerate(headers, start=1):
            cell = wd.cell(row=1, column=j, value=h)
            cell.font = Font(bold=True, color=WHITE)
            cell.fill = fill("1F6FEB")
            cell.alignment = Alignment(horizontal="center")
            cell.border = box
        for i, d in enumerate(directions):
            wd.cell(row=2 + i, column=1, value=d).border = box
            a = wd.cell(row=2 + i, column=2, value=round(vh_dir[i], 4))
            a.number_format = "0.000"
            a.border = box
            b = wd.cell(row=2 + i, column=3, value=round(co2_dir[i], 4))
            b.number_format = "0.000"
            b.border = box
        wd.column_dimensions["A"].width = 14
        wd.column_dimensions["B"].width = 16
        wd.column_dimensions["C"].width = 14

        dchart = BarChart()
        dchart.type = "col"
        dchart.title = "Retraso y CO2 por Direccion"
        dchart.height = 8
        dchart.width = 15
        d_data = Reference(wd, min_col=2, max_col=3, min_row=1, max_row=5)
        d_cats = Reference(wd, min_col=1, min_row=2, max_row=5)
        dchart.add_data(d_data, titles_from_data=True)
        dchart.set_categories(d_cats)
        wd.add_chart(dchart, "E2")

        # ==================== HOJA 3: SERIE TEMPORAL ====================
        wt = wb.create_sheet("Serie Temporal")
        wt.sheet_view.showGridLines = False
        wt.sheet_properties.tabColor = "56D3E7"
        fit_page(wt)
        for j, h in enumerate(["Tiempo (s)", "Cola Total", "CO2 Acumulado (kg)"], start=1):
            cell = wt.cell(row=1, column=j, value=h)
            cell.font = Font(bold=True, color=WHITE)
            cell.fill = fill("1F6FEB")
            cell.border = box
        wt.column_dimensions["A"].width = 12
        wt.column_dimensions["B"].width = 12
        wt.column_dimensions["C"].width = 18

        # Trayectoria PROYECTADA del plan actual (misma fuente que los KPIs)
        p_times, p_ns, p_ew = proj["times"], proj["q_ns"], proj["q_ew"]
        n = len(p_times)
        stride = max(1, n // 250)  # downsample a ~250 puntos
        co2_acc = 0.0
        prev_q = None
        prev_t = None
        row = 2
        for k in range(n):
            t = p_times[k]
            q_total = float(p_ns[k] + p_ew[k])
            if prev_t is not None:
                dt = t - prev_t
                co2_acc += 0.5 * (q_total + prev_q) * dt * self.co2_idle_rate
            prev_q, prev_t = q_total, t
            if k % stride == 0 or k == n - 1:
                wt.cell(row=row, column=1, value=round(t, 3)).number_format = "0.00"
                wt.cell(row=row, column=2, value=round(q_total, 3)).number_format = "0.00"
                wt.cell(row=row, column=3, value=round(co2_acc, 4)).number_format = "0.0000"
                row += 1

        if row > 3:
            lchart = LineChart()
            lchart.title = "Evolucion de Colas y CO2"
            lchart.height = 9
            lchart.width = 18
            lchart.y_axis.title = "Cola total (veh)"
            q_ref = Reference(wt, min_col=2, min_row=1, max_row=row - 1)
            lchart.add_data(q_ref, titles_from_data=True)
            co2_ref = Reference(wt, min_col=3, min_row=1, max_row=row - 1)
            lchart2 = LineChart()
            lchart2.add_data(co2_ref, titles_from_data=True)
            lchart2.y_axis.axId = 200
            lchart2.y_axis.title = "CO2 acumulado (kg)"
            lchart2.y_axis.crosses = "max"
            lchart += lchart2
            t_cats = Reference(wt, min_col=1, min_row=2, max_row=row - 1)
            lchart.set_categories(t_cats)
            wt.add_chart(lchart, "E2")

        # ==================== HOJA 4: IMPACTO ====================
        wi = wb.create_sheet("Impacto")
        wi.sheet_view.showGridLines = False
        wi.sheet_properties.tabColor = GREEN
        fit_page(wi)
        wi.column_dimensions["A"].width = 40
        wi.column_dimensions["B"].width = 20
        wi.merge_cells("A1:B1")
        t = wi["A1"]
        t.value = "EQUIVALENTES AMBIENTALES"
        t.font = Font(size=14, bold=True, color=WHITE)
        t.fill = fill(DARK)
        t.alignment = Alignment(horizontal="left", vertical="center", indent=1)
        wi.row_dimensions[1].height = 24

        rows = [
            ("Gasolina equivalente (litros)", em["total_co2"] / 2.31),
            ("CO2 por vehiculo en cola (kg)", em["emissions_per_vehicle"]),
            ("Horizonte de proyeccion (s)", horizon),
        ]
        if self.optimization_applied and self.baseline_emissions > 0:
            rows += [
                ("Reduccion absoluta (kg CO2)", reduction),
                ("Arboles para absorber diferencia", reduction / 21),
                ("Viajes evitados (km, auto tipico)", reduction / 0.25),
                ("Carbon no quemado (kg)", reduction / 0.4),
            ]
        for i, (label, val) in enumerate(rows, start=3):
            lc = wi.cell(row=i, column=1, value=label)
            lc.font = Font(color=TXT)
            lc.fill = fill(CARD if i % 2 else PANEL)
            lc.border = box
            vc = wi.cell(row=i, column=2, value=round(float(val), 3))
            vc.number_format = "0.000"
            vc.font = Font(bold=True, color=GREEN)
            vc.fill = fill(CARD if i % 2 else PANEL)
            vc.border = box
            vc.alignment = Alignment(horizontal="right")

        wb.save(filepath)
        return filepath

    def reset(self) -> None:
        """Reinicia el analizador de sostenibilidad."""
        self.current = None
        self.demand = (0.0, 0.0)
        self.baseline_emissions = 0.0
        self.optimized_emissions = 0.0
        self.optimization_applied = False
