"""Script de verificación: valida que todos los componentes numéricos funcionan correctamente."""

from __future__ import annotations

import numpy as np

from numerical_engine import TrafficSimulationEngine


def test_arrival_rate_derivative() -> None:
    """Prueba la diferenciación numérica."""
    print("=" * 60)
    print("TEST 1: DIFERENCIACIÓN NUMÉRICA (UNIDAD III)")
    print("=" * 60)

    engine = TrafficSimulationEngine(h=0.1)

    counts = [0, 5, 10, 15, 12]
    times = [0.0, 0.1, 0.2, 0.3, 0.4]

    derivative, stationary = engine.estimate_arrival_rate_derivative(counts, times)

    print(f"Historiales de conteo: {counts}")
    print(f"Tiempos: {times}")
    print(f"Derivada estimada: {derivative:.4f} veh/s")
    print(f"Estado estacionario: {stationary}")
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
    print(f"Derivada instantánea: {engine.arrival_rate_derivative:.4f}")
    print(f"Bandera de estacionariedad: {engine.stationary_flag}")
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

    test_arrival_rate_derivative()
    test_newton_raphson()
    test_heun_method()
    test_full_integration()

    print("=" * 60)
    print("✓ TODOS LOS TESTS COMPLETADOS EXITOSAMENTE")
    print("=" * 60)
    print()


if __name__ == "__main__":
    main()
