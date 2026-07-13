"""Capa de Didáctica Numérica: motor de lecciones para la UI.

`ModuloExplicativo` es una FUENTE DE INFORMACIÓN pura. No realiza cálculos ni importa
la lógica matemática real (numerical_engine); solo almacena, para cada método numérico,
su fórmula (LaTeX), su objetivo dentro del simulador, una justificación académica y un
paso a paso. La interfaz gráfica lo consulta al presionar un botón de ayuda.

Desacoplamiento intencional: este módulo puede evolucionar (más idiomas, más detalle)
sin tocar el motor numérico, y el motor puede cambiar sin tocar las lecciones.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

# Identificadores estables de método (usar estas constantes desde la UI)
NEWTON_RAPHSON = "newton_raphson"
EULER_MODIFICADO = "euler_modificado"
SIMPSON = "simpson"


@dataclass(frozen=True)
class LeccionMetodo:
    """Objeto estructurado con la información didáctica de un método numérico."""

    metodo_id: str
    nombre: str
    unidad: str
    formula_latex: str
    objetivo: str
    justificacion: str
    pasos: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Representación serializable (útil para la UI o para exportar)."""
        return asdict(self)


class ModuloExplicativo:
    """Motor de lecciones: expone la información didáctica de cada método.

    No ejecuta matemáticas; solo entrega texto/fórmulas para mostrar en pantalla.
    """

    def __init__(self) -> None:
        self._lecciones: dict[str, LeccionMetodo] = {
            NEWTON_RAPHSON: LeccionMetodo(
                metodo_id=NEWTON_RAPHSON,
                nombre="Newton-Raphson (matricial)",
                unidad="Unidad I · Sistemas no lineales",
                formula_latex=(
                    r"J(X_k)\,\Delta X = -F(X_k)\qquad X_{k+1} = X_k + \Delta X"
                ),
                objetivo=(
                    "Resolver el sistema no lineal del reparto de verde F(X)=0: hallar "
                    "los tiempos de verde [g_NS, g_EW] que igualan el grado de saturación "
                    "de ambos ejes según la demanda medida en los sensores."
                ),
                justificacion=(
                    "Convergencia cuadrática cerca de la raíz. Se usa una Jacobiana "
                    "numérica (diferencias finitas hacia adelante), evitando derivar "
                    "analíticamente el modelo y manteniendo el método general."
                ),
                pasos=[
                    "1. Partir de una aproximación inicial X_0 (reparto equitativo).",
                    "2. Evaluar el residuo F(X_k) del sistema de equilibrio de flujos.",
                    "3. Aproximar la Jacobiana J(X_k) por diferencias finitas.",
                    "4. Resolver el sistema lineal J·ΔX = -F para el paso ΔX.",
                    "5. Actualizar X_{k+1} = X_k + ΔX.",
                    "6. Repetir hasta que ||F(X)|| < tol o ||ΔX|| < tol.",
                ],
            ),
            EULER_MODIFICADO: LeccionMetodo(
                metodo_id=EULER_MODIFICADO,
                nombre="Euler Modificado (Heun) · Predictor-Corrector",
                unidad="Unidad IV · Ecuaciones diferenciales ordinarias",
                formula_latex=(
                    r"\tilde{q}_{i+1} = q_i + h\,f(t_i, q_i)\qquad "
                    r"q_{i+1} = q_i + \frac{h}{2}\left[f(t_i, q_i) + "
                    r"f(t_{i+1}, \tilde{q}_{i+1})\right]"
                ),
                objetivo=(
                    "Evolucionar en el tiempo la longitud de cola q(t) frente al semáforo, "
                    "resolviendo la EDO dq/dt = T_entrada(t) - T_salida(t) con la "
                    "restricción física q(t) ≥ 0."
                ),
                justificacion=(
                    "Como método de segundo orden, su error local es O(h^3) y el global "
                    "O(h^2): más preciso que Euler simple a igual paso. El corrector "
                    "promedia la pendiente en los extremos, estabilizando la integración."
                ),
                pasos=[
                    "1. Evaluar la pendiente inicial f(t_i, q_i).",
                    "2. Predictor: estimar q̃_{i+1} con un paso de Euler.",
                    "3. Evaluar la pendiente en el extremo f(t_{i+1}, q̃_{i+1}).",
                    "4. Corrector: promediar ambas pendientes para q_{i+1}.",
                    "5. Truncar a q_{i+1} = max(0, q_{i+1}) (no hay colas negativas).",
                ],
            ),
            SIMPSON: LeccionMetodo(
                metodo_id=SIMPSON,
                nombre="Regla de Simpson 1/3 compuesta",
                unidad="Unidad III · Integración numérica",
                formula_latex=(
                    r"\int_{a}^{b} q(t)\,dt \approx \frac{h}{3}\left[q_0 + "
                    r"4\!\!\sum_{i\,impar}\!\!q_i + 2\!\!\sum_{i\,par}\!\!q_i + q_n\right]"
                ),
                objetivo=(
                    "Integrar el área bajo la curva de cola q(t) para obtener las "
                    "Horas-Vehículo de retraso y, a partir de ellas, la emisión total "
                    "de CO2 del sistema."
                ),
                justificacion=(
                    "Aproxima la función por parábolas: es exacta para polinomios hasta "
                    "grado 3, con error O(h^4), superior al trapecio. Si el número de "
                    "intervalos es impar, se aplica el trapecio solo en el último tramo."
                ),
                pasos=[
                    "1. Tomar las muestras q_0..q_n de la cola espaciadas un paso h.",
                    "2. Si n (intervalos) es impar, reservar el último tramo para trapecio.",
                    "3. Ponderar: extremos ×1, nodos impares ×4, nodos pares internos ×2.",
                    "4. Multiplicar la suma ponderada por h/3.",
                    "5. Sumar el trapecio del último tramo si aplica → área total.",
                ],
            ),
        }

    def obtener_informacion(self, metodo_id: str) -> LeccionMetodo:
        """Devuelve la lección estructurada del método indicado.

        Args:
            metodo_id: uno de NEWTON_RAPHSON, EULER_MODIFICADO, SIMPSON.

        Returns:
            LeccionMetodo (objeto estructurado, inmutable).

        Raises:
            KeyError: si el método no existe (usar metodos_disponibles() para listar).
        """
        try:
            return self._lecciones[metodo_id]
        except KeyError:
            disponibles = ", ".join(self._lecciones)
            raise KeyError(
                f"Método desconocido: {metodo_id!r}. Disponibles: {disponibles}"
            ) from None

    def metodos_disponibles(self) -> list[str]:
        """Lista de identificadores de método disponibles."""
        return list(self._lecciones)

    def todas_las_lecciones(self) -> list[LeccionMetodo]:
        """Todas las lecciones (p. ej. para poblar un menú de ayuda)."""
        return list(self._lecciones.values())


__all__ = [
    "ModuloExplicativo",
    "LeccionMetodo",
    "NEWTON_RAPHSON",
    "EULER_MODIFICADO",
    "SIMPSON",
]
