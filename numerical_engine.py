"""Backend numérico puro para un simulador de tráfico dinámico en 2D.

Este módulo implementa tres componentes numéricos de forma manual:
1. Diferenciación numérica para estimar la tasa de llegada de vehículos.
2. Newton-Raphson matricial para resolver un sistema no lineal de equilibrio de flujos.
3. Método de Heun (Euler modificado) para la evolución temporal de colas.
"""

from __future__ import annotations

from typing import Callable

import numpy as np


class TrafficSimulationEngine:
    """Motor numérico para la simulación de tráfico con métodos explícitos."""

    def __init__(self, h: float = 0.1) -> None:
        self.h = h
        self.flow_state = [0.0, 0.0, 0.0, 0.0]
        self.queue_state = [0.0, 0.0, 0.0, 0.0]
        self.discrete_vehicle_counts = [0, 0, 0, 0]

        self.current_time = 0.0
        self.count_history: list[float] = []
        self.time_history: list[float] = []
        self.arrival_rate_derivative = 0.0
        self.stationary_flag = False
        self.newton_solution: np.ndarray | None = None
        self.newton_residual_norm = float("inf")

    def estimate_arrival_rate_derivative(
        self,
        counts_history: list[float],
        times_history: list[float],
        stationarity_window: int = 3,
        stationarity_threshold: float = 1e-6,
    ) -> tuple[float, bool]:
        """Estima la derivada instantánea de la tasa de llegada mediante diferencias finitas.

        Matemáticamente, si R(t) representa el conteo discreto de vehículos observado en
        tiempos t_i, entonces la derivada numérica se aproxima como:

        R'(t_i) ≈ (R(t_{i+1}) - R(t_{i-1})) / (t_{i+1} - t_{i-1})

        para puntos interiores. En los extremos se usan fórmulas unilaterales para evitar
        depender de datos inexistentes. El flag de estado estacionario se activa cuando la
        magnitud de las derivadas recientes permanece suficientemente cercana a cero durante
        una ventana de tiempo.
        """
        if len(counts_history) != len(times_history):
            raise ValueError("Los historiales de conteo y tiempos deben tener la misma longitud.")

        if len(counts_history) < 2:
            self.arrival_rate_derivative = 0.0
            self.stationary_flag = True
            return 0.0, True

        counts = np.asarray(counts_history, dtype=float)
        times = np.asarray(times_history, dtype=float)

        if np.any(np.diff(times) <= 0):
            raise ValueError("Los tiempos deben crecer estrictamente de forma monótona.")

        derivatives = np.zeros_like(counts, dtype=float)
        n = len(counts)

        for i in range(n):
            if i == 0:
                derivatives[i] = (counts[1] - counts[0]) / (times[1] - times[0])
            elif i == n - 1:
                derivatives[i] = (counts[-1] - counts[-2]) / (times[-1] - times[-2])
            else:
                derivatives[i] = (counts[i + 1] - counts[i - 1]) / (times[i + 1] - times[i - 1])

        latest_derivative = float(derivatives[-1])
        window = max(1, min(stationarity_window, n))
        stationary_flag = bool(np.all(np.abs(derivatives[-window:]) <= stationarity_threshold))

        self.arrival_rate_derivative = latest_derivative
        self.stationary_flag = stationary_flag
        return latest_derivative, stationary_flag

    def nonlinear_flow_residuals(
        self,
        x: np.ndarray | list[float],
        parameters: tuple[float, float, float, float] | None = None,
    ) -> np.ndarray:
        """Modelo de equilibrio de flujos concurrentes mediante saturación no lineal.

        Se considera un vector de incógnitas X = [x1, x2], donde x1 representa el flujo
        dominante de una dirección y x2 el flujo concurrente de la perpendicular. Para modelar
        la congestión se utiliza una forma exponencial tipo Greenshields en la que el flujo
        crece hacia una saturación asintótica cuando el conflicto aumenta.

        Las ecuaciones no lineales son:

        F1(X) = x1 - a(1 - e^{-x2 / c}) - b1
        F2(X) = x2 - d(1 - e^{-x1 / e}) - b2

        donde los términos de saturación capturan el efecto de choque entre flujos.
        """
        x_array = np.asarray(x, dtype=float)
        if x_array.shape != (2,):
            raise ValueError("El vector de incógnitas debe tener exactamente dos componentes.")

        if parameters is None:
            a, b1, d, b2 = 0.85, 0.15, 0.75, 0.10
            c, e = 2.0, 3.0
        else:
            a, b1, d, b2, c, e = (*parameters, 2.0, 3.0)

        x1, x2 = x_array
        f1 = x1 - a * (1.0 - np.exp(-x2 / c)) - b1
        f2 = x2 - d * (1.0 - np.exp(-x1 / e)) - b2
        return np.array([f1, f2], dtype=float)

    def solve_newton_raphson(
        self,
        initial_guess: np.ndarray | list[float],
        tol: float = 1e-8,
        max_iter: int = 50,
        parameters: tuple[float, float, float, float] | None = None,
    ) -> dict[str, object]:
        """Resuelve F(X)=0 mediante Newton-Raphson con Jacobiana numérica.

        El método iterativo sigue la forma:

        J(X_k) ΔX = -F(X_k)
        X_{k+1} = X_k + ΔX

        donde la matriz Jacobiana se aproxima numéricamente por diferencias finitas hacia
        adelante para cada variable del sistema, sin requerir derivadas analíticas explícitas.
        """
        x = np.asarray(initial_guess, dtype=float)
        if x.shape != (2,):
            raise ValueError("La aproximación inicial debe ser un vector de dos componentes.")

        converged = False
        for k in range(max_iter):
            f_value = self.nonlinear_flow_residuals(x, parameters)
            residual_norm = float(np.linalg.norm(f_value))
            if residual_norm < tol:
                converged = True
                break

            jacobian = np.zeros((2, 2), dtype=float)
            for j in range(2):
                epsilon = 1e-6 * (1.0 + abs(x[j]))
                x_perturbed = x.copy()
                x_perturbed[j] += epsilon
                f_perturbed = self.nonlinear_flow_residuals(x_perturbed, parameters)
                jacobian[:, j] = (f_perturbed - f_value) / epsilon

            delta_x = np.linalg.solve(jacobian, -f_value)
            x = x + delta_x

            if np.linalg.norm(delta_x) < tol:
                converged = True
                break

        self.newton_solution = x
        self.newton_residual_norm = float(np.linalg.norm(self.nonlinear_flow_residuals(x, parameters)))
        return {
            "solution": x,
            "residual": self.nonlinear_flow_residuals(x, parameters),
            "residual_norm": self.newton_residual_norm,
            "converged": converged,
        }

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

    def integrate_queue(
        self,
        q0: float,
        total_time: float,
        h: float,
        entry_rate: float | Callable[[float], float],
        exit_rate: float | Callable[[float], float],
    ) -> tuple[list[float], list[float]]:
        """Integra la EDO de la cola sobre un intervalo de tiempo usando Heun."""
        n_steps = int(total_time / h)
        times = [i * h for i in range(n_steps + 1)]
        q_values = [float(q0)]

        for i in range(n_steps):
            q_next = self.heun_queue_update(q_values[-1], times[i], h, entry_rate, exit_rate)
            q_values.append(float(q_next))

        return times, q_values

    def step(
        self,
        discrete_counts: list[int] | None = None,
        dt: float | None = None,
    ) -> dict[str, list[float]]:
        """Actualiza el estado del sistema a partir de conteos discretos y métodos numéricos."""
        if dt is None:
            dt = self.h

        if discrete_counts is not None:
            self.discrete_vehicle_counts = [max(0, c) for c in discrete_counts]

        self.count_history.append(float(sum(self.discrete_vehicle_counts)))
        self.time_history.append(self.current_time)
        if len(self.count_history) > 20:
            self.count_history = self.count_history[-20:]
            self.time_history = self.time_history[-20:]

        self.estimate_arrival_rate_derivative(self.count_history, self.time_history)

        self.flow_state = [
            max(0.0, flow + 0.01 * count + 0.001 * self.arrival_rate_derivative)
            for flow, count in zip(self.flow_state, self.discrete_vehicle_counts)
        ]

        for index, queue_value in enumerate(self.queue_state):
            arrival_rate = 0.05 * self.discrete_vehicle_counts[index] + 0.01 * self.flow_state[index]
            departure_rate = 0.02 + 0.005 * max(0.0, queue_value)
            self.queue_state[index] = self.heun_queue_update(
                queue_value,
                self.current_time,
                dt,
                arrival_rate,
                departure_rate,
            )

        self.current_time += dt
        return {"flows": self.flow_state, "queues": self.queue_state}


class SustainabilityAnalyzer:
    """Analizador de Responsabilidad Social y Sostenibilidad Ambiental.

    Esta clase evalúa el impacto ambiental del tráfico en la intersección mediante:
    1. Integración temporal de colas para obtener Horas-Vehículo de retraso.
    2. Estimación de emisiones de CO2 por ralentí vehicular.
    3. Generación de reportes comparativos pre/post-optimización.
    """

    def __init__(self, co2_idle_rate: float = 0.12) -> None:
        """Inicializa el analizador de sostenibilidad.

        Args:
            co2_idle_rate: Tasa de emisión de CO2 en kg/hora cuando el motor está encendido
                          en ralentí. Valor típico para autos: 0.12 kg CO2/hora.
        """
        self.co2_idle_rate = co2_idle_rate

        self.time_history: list[float] = []
        self.queue_history: list[list[float]] = []
        self.vehicle_hours_delay: list[float] = [0.0, 0.0, 0.0, 0.0]
        self.cumulative_co2_emissions: list[float] = [0.0, 0.0, 0.0, 0.0]

        self.baseline_emissions = 0.0
        self.optimized_emissions = 0.0
        self.optimization_applied = False

    def record_state(self, time: float, queue_state: list[float]) -> None:
        """Registra el estado de las colas en un instante de tiempo.

        Matemáticamente, integra cada valor de cola q_i(t) mediante trapezoides
        para obtener el acumulado de Horas-Vehículo de retraso.
        """
        self.time_history.append(float(time))
        self.queue_history.append([float(q) for q in queue_state])

        if len(self.time_history) >= 2:
            dt = self.time_history[-1] - self.time_history[-2]
            for i in range(4):
                q_current = queue_state[i]
                q_previous = self.queue_history[-2][i] if len(self.queue_history) > 1 else 0.0
                vehicle_hours = 0.5 * (q_current + q_previous) * dt
                self.vehicle_hours_delay[i] += float(vehicle_hours)
                self.cumulative_co2_emissions[i] += float(vehicle_hours * self.co2_idle_rate)

    def calculate_total_emissions(self) -> dict[str, float]:
        """Calcula las emisiones totales y métricas de sostenibilidad.

        Retorna un diccionario con:
        - total_co2: Emisiones totales de CO2 (kg)
        - total_veh_hours: Total de Horas-Vehículo de retraso
        - average_queue_time: Tiempo promedio de espera
        - emissions_per_vehicle: Emisiones promedio por vehículo
        """
        total_co2 = float(sum(self.cumulative_co2_emissions))
        total_veh_hours = float(sum(self.vehicle_hours_delay))
        total_vehicles = total_veh_hours if total_veh_hours > 0 else 1
        emissions_per_vehicle = total_co2 / total_vehicles if total_vehicles > 0 else 0.0

        return {
            "total_co2": total_co2,
            "total_veh_hours": total_veh_hours,
            "average_queue_time": float(np.mean(self.vehicle_hours_delay)) if len(self.vehicle_hours_delay) > 0 else 0.0,
            "emissions_per_vehicle": emissions_per_vehicle,
        }

    def set_baseline(self) -> None:
        """Establece el estado actual como línea base (sincronización manual)."""
        emissions = self.calculate_total_emissions()
        self.baseline_emissions = float(emissions["total_co2"])

    def set_optimized(self) -> None:
        """Registra el estado actual como post-optimización (Newton-Raphson)."""
        emissions = self.calculate_total_emissions()
        self.optimized_emissions = float(emissions["total_co2"])
        self.optimization_applied = True

    def generate_sustainability_report(self) -> str:
        """Genera un reporte completo de sostenibilidad ambiental.

        Retorna un reporte formateado en texto que incluye:
        - Horas-Vehículo de retraso por dirección
        - Emisiones totales de CO2
        - Comparación pre/post-optimización
        - Porcentaje de reducción de contaminación
        - Estimaciones de impacto ambiental
        """
        emissions = self.calculate_total_emissions()

        report = "\n"
        report += "=" * 80 + "\n"
        report += "REPORTE DE SOSTENIBILIDAD Y RESPONSABILIDAD SOCIAL\n"
        report += "Simulador de Tráfico 2D - Análisis Ambiental\n"
        report += "=" * 80 + "\n\n"

        report += "MÉTRICAS DE EFICIENCIA DE TRÁFICO\n"
        report += "-" * 80 + "\n"
        report += f"Tiempo total de simulación: {self.time_history[-1]:.2f} segundos\n"
        report += f"Total de Horas-Vehículo de retraso: {emissions['total_veh_hours']:.3f} veh-h\n"
        report += f"Tiempo promedio de espera: {emissions['average_queue_time']:.3f} h/dirección\n\n"

        report += "DESGLOSE POR DIRECCIÓN (Norte-Sur, Este-Oeste, Sur-Norte, Oeste-Este)\n"
        report += "-" * 80 + "\n"
        directions = ["N-S (Arriba)", "E-O (Izq)", "S-N (Abajo)", "O-E (Der)"]
        for i, direction in enumerate(directions):
            report += f"{direction:15} | Retraso: {self.vehicle_hours_delay[i]:7.3f} veh-h | "
            report += f"CO2: {self.cumulative_co2_emissions[i]:7.3f} kg\n"
        report += "\n"

        report += "IMPACTO AMBIENTAL\n"
        report += "-" * 80 + "\n"
        report += f"Emisiones totales de CO2: {emissions['total_co2']:.3f} kg\n"
        report += f"Equivalente a combustión de: {emissions['total_co2'] / 2.31:.1f} litros de gasolina\n"
        report += f"Emisiones por vehículo en cola: {emissions['emissions_per_vehicle']:.4f} kg CO2\n\n"

        if self.optimization_applied and self.baseline_emissions > 0:
            reduction = self.baseline_emissions - self.optimized_emissions
            reduction_percentage = (reduction / self.baseline_emissions) * 100
            trees_equivalent = reduction / 21  # 1 árbol absorbe ~21 kg CO2/año

            report += "ANÁLISIS COMPARATIVO: SINCRONIZACIÓN MANUAL vs. OPTIMIZADA\n"
            report += "-" * 80 + "\n"
            report += f"Emisiones (Sincronización Manual):   {self.baseline_emissions:8.3f} kg CO2\n"
            report += f"Emisiones (Sincronización Óptima):   {self.optimized_emissions:8.3f} kg CO2\n"
            report += f"Reducción absoluta:                  {reduction:8.3f} kg CO2\n"
            report += f"\n>>> REDUCCIÓN DE CONTAMINACIÓN: {reduction_percentage:6.2f}% <<<\n\n"
            report += f"Equivalente ambiental:\n"
            report += f"  • Árboles necesarios para absorber diferencia: {trees_equivalent:.1f} árboles\n"
            report += f"  • Viajes evitados (auto típico): {reduction / 0.25:.0f} km\n"
            report += f"  • CO2 equivalente a: {reduction / 0.4:.1f} kg de carbón no quemado\n"

        report += "\n" + "=" * 80 + "\n"
        return report

    def save_report_to_file(self, filename: str = "reporte_sostenibilidad.txt") -> str:
        """Guarda el reporte de sostenibilidad a un archivo .txt.
        
        Args:
            filename: Nombre del archivo a guardar (default: reporte_sostenibilidad.txt)
            
        Returns:
            Ruta del archivo guardado
        """
        import os
        from datetime import datetime
        
        # Crear nombre con timestamp
        base, ext = os.path.splitext(filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = f"{base}_{timestamp}{ext}"
        
        report = self.generate_sustainability_report()
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report)
        
        return filepath

    def export_to_csv(self, filename: str = "datos_trafico.csv") -> str:
        """Exporta datos de la simulación a CSV.
        
        Args:
            filename: Nombre del archivo CSV (default: datos_trafico.csv)
            
        Returns:
            Ruta del archivo guardado
        """
        import csv
        import os
        from datetime import datetime
        
        # Crear nombre con timestamp
        base, ext = os.path.splitext(filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = f"{base}_{timestamp}{ext}"
        
        emissions = self.calculate_total_emissions()
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Encabezados
            writer.writerow(["DATOS DE SIMULACIÓN DE TRÁFICO"])
            writer.writerow([])
            
            # Métricas generales
            writer.writerow(["MÉTRICAS GENERALES"])
            writer.writerow(["Tiempo simulación (s)", self.time_history[-1] if self.time_history else 0])
            writer.writerow(["Total Horas-Vehículo", emissions['total_veh_hours']])
            writer.writerow(["Emisiones CO2 Total (kg)", emissions['total_co2']])
            writer.writerow([])
            
            # Por dirección
            writer.writerow(["DESGLOSE POR DIRECCIÓN"])
            writer.writerow(["Dirección", "Horas-Vehículo", "CO2 (kg)"])
            directions = ["N-S (Arriba)", "E-O (Izq)", "S-N (Abajo)", "O-E (Der)"]
            for i, direction in enumerate(directions):
                writer.writerow([direction, self.vehicle_hours_delay[i], self.cumulative_co2_emissions[i]])
            writer.writerow([])
            
            # Análisis comparativo si existe
            if self.optimization_applied and self.baseline_emissions > 0:
                writer.writerow(["ANÁLISIS COMPARATIVO"])
                writer.writerow(["Emisiones Baseline (kg)", self.baseline_emissions])
                writer.writerow(["Emisiones Optimizadas (kg)", self.optimized_emissions])
                reduction = self.baseline_emissions - self.optimized_emissions
                reduction_pct = (reduction / self.baseline_emissions) * 100
                writer.writerow(["Reducción Absoluta (kg)", reduction])
                writer.writerow(["Reducción Porcentual (%)", reduction_pct])
                writer.writerow(["Árboles Equivalentes", reduction / 21])
        
        return filepath

    def reset(self) -> None:
        """Reinicia el analizador de sostenibilidad."""
        self.time_history = []
        self.queue_history = []
        self.vehicle_hours_delay = [0.0, 0.0, 0.0, 0.0]
        self.cumulative_co2_emissions = [0.0, 0.0, 0.0, 0.0]
        self.baseline_emissions = 0.0
        self.optimized_emissions = 0.0
        self.optimization_applied = False
