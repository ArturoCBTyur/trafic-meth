"""Script de verificación: valida que todos los componentes numéricos funcionan correctamente."""

from __future__ import annotations

from numerical_engine import TrafficSimulationEngine, composite_simpson


def test_simpson_integration() -> None:
    """Prueba la integración numérica por Regla de Simpson 1/3 compuesta."""
    print("=" * 60)
    print("TEST 1: INTEGRACIÓN NUMÉRICA - SIMPSON 1/3 (UNIDAD III)")
    print("=" * 60)

    engine = TrafficSimulationEngine(h=0.1)

    # Caso 1: integrar x^2 en [0,2], exacto = 8/3 ≈ 2.6667 (Simpson es exacto en cúbicas)
    h = 0.5
    xs = [0.0, 0.5, 1.0, 1.5, 2.0]           # 4 intervalos (par)
    ys = [x * x for x in xs]
    area_even = composite_simpson(ys, h)
    print(f"∫x² dx en [0,2] (4 intervalos, par): {area_even:.4f}  (exacto 2.6667)")

    # Caso 2: número IMPAR de intervalos (Trapecio en el último tramo)
    xs_odd = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5]  # 5 intervalos (impar)
    ys_odd = [x * x for x in xs_odd]
    area_odd = composite_simpson(ys_odd, h)
    print(f"∫x² dx en [0,2.5] (5 intervalos, impar→trapecio final): {area_odd:.4f}")

    # Caso 3: vía el motor con q(t) tipo cola de vehículos
    q_list = [0.0, 2.0, 4.0, 3.0, 1.0]
    area_q = engine.integrate_simpson(q_list, h=0.1)
    print(f"Área bajo q(t)={q_list} con h=0.1: {area_q:.4f} veh-h")
    print()


def test_newton_raphson() -> None:
    """Prueba Newton-Raphson matricial para el reparto óptimo de verde (Unidad I)."""
    print("=" * 60)
    print("TEST 2: NEWTON-RAPHSON AVANZADO (UNIDAD I)")
    print("=" * 60)

    engine = TrafficSimulationEngine(h=0.1)

    # Demanda desbalanceada (arteria N-S) → el reparto debe favorecer a N-S
    lambda_ns, lambda_ew = 1.1, 0.3
    g_total = 50.0
    print(f"Demanda: N-S={lambda_ns} veh/s, E-O={lambda_ew} veh/s, verde total={g_total}s")

    result = engine.solve_green_split(lambda_ns, lambda_ew, g_total)
    g_ns, g_ew = result["solution"]

    print(f"Verde óptimo: N-S={g_ns:.2f}s, E-O={g_ew:.2f}s")
    print(f"Norma del residuo ‖F(X)‖: {result['residual_norm']:.2e}")
    print(f"Convergido: {result['converged']}  ·  iteraciones: {result['iterations']}")

    assert result["converged"], "Newton-Raphson no convergió"
    assert g_ns > g_ew, "el eje con más demanda debería recibir más verde"
    assert abs((g_ns + g_ew) - g_total) < 1e-6, "el verde repartido debe sumar g_total"
    print()


def test_heun_method() -> None:
    """Prueba el método de Heun."""
    print("=" * 60)
    print("TEST 3: MÉTODO DE EULER MODIFICADO (UNIDAD IV)")
    print("=" * 60)

    engine = TrafficSimulationEngine(h=0.1)

    q0 = 5.0
    t0 = 0.0
    h = 0.1
    entry_rate = 2.0
    exit_rate = 1.5

    q_values = [q0]
    for i in range(10):
        q_next = engine.heun_queue_update(q_values[-1], t0 + i * h, h, entry_rate, exit_rate)
        q_values.append(q_next)

    print(f"Condición inicial q(0): {q0}")
    print(f"Tasa de entrada: {entry_rate} veh/s")
    print(f"Tasa de salida: {exit_rate} veh/s")
    print(f"Paso temporal h: {h}s")
    print(f"\nLongitudes de cola en tiempo:")
    for i, q in enumerate(q_values):
        t = i * h
        print(f"  t={t:.1f}s: q={q:.3f}")
    print()


def test_full_integration() -> None:
    """Prueba la integración completa del sistema."""
    print("=" * 60)
    print("TEST 4: INTEGRACIÓN COMPLETA")
    print("=" * 60)

    engine = TrafficSimulationEngine(h=0.016)

    print("Ejecutando 5 pasos de integración con conteos simulados...")
    for step in range(5):
        counts = [1, 2, 1, 0]
        result = engine.step(discrete_counts=counts)
        print(f"Paso {step}: Colas={[f'{q:.3f}' for q in result['queues']]}")

    print(f"\nEstado final de colas: {engine.queue_state}")
    print()


def main() -> None:
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 58 + "║")
    print("║" + " " * 10 + "VALIDACIÓN DE MÉTODOS NUMÉRICOS" + " " * 17 + "║")
    print("║" + " " * 14 + "Simulador de Tráfico 2D" + " " * 21 + "║")
    print("║" + " " * 58 + "║")
    print("╚" + "═" * 58 + "╝")
    print()

    test_simpson_integration()
    test_newton_raphson()
    test_heun_method()
    test_full_integration()

    print("=" * 60)
    print("✓ TODOS LOS TESTS COMPLETADOS EXITOSAMENTE")
    print("=" * 60)
    print()


if __name__ == "__main__":
    main()
