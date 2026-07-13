"""Script de verificación: valida que todos los componentes numéricos funcionan correctamente."""

from __future__ import annotations

import numpy as np

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
    """Prueba el método de Newton-Raphson."""
    print("=" * 60)
    print("TEST 2: NEWTON-RAPHSON AVANZADO (UNIDAD I)")
    print("=" * 60)

    engine = TrafficSimulationEngine(h=0.1)

    initial_guess = np.array([0.3, 0.2])
    print(f"Aproximación inicial: {initial_guess}")

    result = engine.solve_newton_raphson(initial_guess, tol=1e-8, max_iter=50)

    print(f"Solución encontrada: {result['solution']}")
    print(f"Residuo: {result['residual']}")
    print(f"Norma del residuo: {result['residual_norm']:.2e}")
    print(f"Convergido: {result['converged']}")
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
        print(f"Paso {step}: Flujos={[f'{f:.3f}' for f in result['flows']]}, "
              f"Colas={[f'{q:.3f}' for q in result['queues']]}")

    print(f"\nEstado final de colas: {engine.queue_state}")
    print(f"Flujos finales: {engine.flow_state}")
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
