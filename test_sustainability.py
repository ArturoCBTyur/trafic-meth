"""Script de prueba: sostenibilidad con modelo unificado (una sola fuente de verdad).

Todas las cifras (CO2, retraso, reducción y el Excel) provienen de la MISMA proyección
engine.project_emissions() bajo la demanda medida (Heun + Simpson).
"""

from __future__ import annotations

from numerical_engine import TrafficSimulationEngine, SustainabilityAnalyzer


def test_sustainability_integration() -> None:
    print("\n" + "=" * 80)
    print("TEST: SOSTENIBILIDAD (MODELO UNIFICADO)")
    print("=" * 80 + "\n")

    engine = TrafficSimulationEngine(h=0.016)
    analyzer = SustainabilityAnalyzer(co2_idle_rate=0.12)

    # Demanda desbalanceada (arteria N-S) medida en veh/s por eje
    lambda_ns, lambda_ew = 1.1, 0.3
    g_total = 50.0
    print(f"Demanda: N-S={lambda_ns} veh/s, E-O={lambda_ew} veh/s\n")

    print("Fase 1: línea base = reparto MANUAL equitativo (verde/2 a cada eje)")
    print("-" * 80)
    base = engine.project_emissions(g_total / 2, g_total / 2, lambda_ns, lambda_ew)
    print(f"CO2 base: {base['co2']:.3f} kg  ·  retraso: {base['veh_hours']:.3f} veh-h")

    print("\nFase 2: reparto óptimo (Newton-Raphson por demanda)")
    print("-" * 80)
    result = engine.solve_green_split(lambda_ns, lambda_ew, g_total)
    g_ns, g_ew = result["solution"]
    print(f"Convergió: {result['converged']}  ·  ‖F(X)‖={result['residual_norm']:.2e}")
    print(f"Verde óptimo: N-S={g_ns:.1f}s, E-O={g_ew:.1f}s")

    print("\nFase 3: proyección del plan óptimo (misma demanda/horizonte)")
    print("-" * 80)
    opt = engine.project_emissions(g_ns, g_ew, lambda_ns, lambda_ew)
    print(f"CO2 óptimo: {opt['co2']:.3f} kg  ·  retraso: {opt['veh_hours']:.3f} veh-h")

    analyzer.set_current(opt, (lambda_ns, lambda_ew))
    analyzer.set_baseline(base["co2"])
    analyzer.set_optimized(opt["co2"])

    em = analyzer.calculate_total_emissions()
    reduction = (base["co2"] - opt["co2"]) / base["co2"] * 100
    print(f"\nKPI (fuente única): CO2={em['total_co2']:.3f} kg, "
          f"retraso={em['total_veh_hours']:.3f} veh-h")
    print(f">>> Reducción de contaminación: {reduction:.1f}% <<<")
    assert opt["co2"] <= base["co2"] + 1e-9, "el óptimo no debería emitir más que la base"

    print("\n" + "=" * 80)
    print("EXPORTACIÓN A EXCEL")
    print("=" * 80)
    filepath = analyzer.export_to_excel("reporte_sostenibilidad.xlsx")
    print(f"Reporte Excel generado: {filepath}")

    print("\n✓ PRUEBA DE INTEGRACIÓN COMPLETADA EXITOSAMENTE\n")


if __name__ == "__main__":
    test_sustainability_integration()
