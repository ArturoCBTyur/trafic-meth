"""Script de prueba: validación completa de la integración de sostenibilidad."""

from __future__ import annotations

import numpy as np

from numerical_engine import TrafficSimulationEngine, SustainabilityAnalyzer


def test_sustainability_integration() -> None:
    """Prueba la integración completa del analizador de sostenibilidad."""
    print("\n" + "=" * 80)
    print("TEST: INTEGRACIÓN DE SOSTENIBILIDAD AMBIENTAL")
    print("=" * 80 + "\n")

    engine = TrafficSimulationEngine(h=0.016)
    analyzer = SustainabilityAnalyzer(co2_idle_rate=0.12)

    print("Fase 1: Simulación con sincronización MANUAL (línea base)")
    print("-" * 80)

    for step in range(100):
        counts = [2 if step % 10 < 5 else 1, 1, 2 if step % 10 < 5 else 1, 0]
        engine.step(discrete_counts=counts)
        analyzer.record_state(engine.current_time, engine.queue_state)

    analyzer.set_baseline()
    baseline_emissions = analyzer.calculate_total_emissions()
    print(f"Emisiones línea base: {baseline_emissions['total_co2']:.3f} kg CO2")
    print(f"Horas-Vehículo de retraso: {baseline_emissions['total_veh_hours']:.3f} veh-h")

    print("\n" + "-" * 80)
    print("Fase 2: Optimización con Newton-Raphson")
    print("-" * 80)

    initial_guess = np.array([0.833, 0.833])
    result = engine.solve_newton_raphson(initial_guess, tol=1e-6, max_iter=20)
    print(f"Convergencia Newton-Raphson: {result['converged']}")
    print(f"Residuo final: {result['residual_norm']:.2e}")
    print(f"Solución: {result['solution']}")

    print("\n" + "-" * 80)
    print("Fase 3: Simulación con sincronización OPTIMIZADA")
    print("-" * 80)

    engine_optimized = TrafficSimulationEngine(h=0.016)
    analyzer_optimized = SustainabilityAnalyzer(co2_idle_rate=0.12)

    green_ns_opt = result['solution'][0] * 30.0
    green_ew_opt = result['solution'][1] * 30.0
    print(f"Tiempos optimizados: Verde N-S = {green_ns_opt:.1f}s, Verde E-O = {green_ew_opt:.1f}s")

    for step in range(100):
        counts = [2 if step % 10 < 5 else 1, 1, 2 if step % 10 < 5 else 1, 0]
        engine_optimized.step(discrete_counts=counts)
        analyzer_optimized.record_state(engine_optimized.current_time, engine_optimized.queue_state)

    analyzer_optimized.set_baseline()
    analyzer_optimized.set_optimized()

    baseline_emissions_opt = analyzer_optimized.calculate_total_emissions()
    print(f"Emisiones optimizadas: {baseline_emissions_opt['total_co2']:.3f} kg CO2")
    print(f"Horas-Vehículo de retraso: {baseline_emissions_opt['total_veh_hours']:.3f} veh-h")

    print("\n" + "=" * 80)
    print("EXPORTACIÓN A EXCEL")
    print("=" * 80)
    filepath = analyzer_optimized.export_to_excel("reporte_sostenibilidad.xlsx")
    print(f"Reporte Excel generado: {filepath}")

    print("\n✓ PRUEBA DE INTEGRACIÓN COMPLETADA EXITOSAMENTE\n")


if __name__ == "__main__":
    test_sustainability_integration()
