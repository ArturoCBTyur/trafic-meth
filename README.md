# Simulador de Tráfico 2D - Métodos Numéricos

Un simulador dinámico de tráfico en 2D que integra tres unidades de métodos numéricos para la optimización de intersecciones viales.

## Características

### Unidades de Métodos Numéricos Implementadas

#### 1. **UNIDAD III: Diferenciación Numérica**
- **Función**: Estima la derivada instantánea de la tasa de llegada de vehículos R'(t)
- **Método**: Diferencias finitas centrales
- **Entrada**: Historial discreto de conteos R(t) capturado por sensores virtuales
- **Salida**: 
  - Derivada instantánea R'(t)
  - Flag de "Estado Estacionario" (convergencia)
- **Fórmula**: $R'(t_i) \approx \frac{R(t_{i+1}) - R(t_{i-1})}{t_{i+1} - t_{i-1}}$

#### 2. **UNIDAD I: Newton-Raphson Avanzado**
- **Objetivo**: Resolver un sistema no lineal de equilibrio de flujos F(X) = 0
- **Modelo de Congestión**: Greenshields exponencial
- **Método**: Newton-Raphson matricial con Jacobiana numérica por diferencias finitas
- **Iteración**: 
  - Calcular: $J(X_k) \Delta X = -F(X_k)$
  - Actualizar: $X_{k+1} = X_k + \Delta X$
- **Jacobiana**: Aproximada numéricamente sin derivadas analíticas explícitas

#### 3. **UNIDAD IV: Método de Euler Modificado (Heun)**
- **Problema**: Evolucionar la longitud de cola q(t) frente a semáforos rojos
- **EDO**: $\frac{dq}{dt} = T_{entrada}(t) - T_{salida}(t)$
- **Algoritmo Predictor-Corrector**:
  - Predictor: $\tilde{q}_{i+1} = q_i + h \cdot f(t_i, q_i)$
  - Corrector: $q_{i+1} = q_i + \frac{h}{2}[f(t_i, q_i) + f(t_{i+1}, \tilde{q}_{i+1})]$
- **Restricción Física**: $q(t) \geq 0$ (no colas negativas)

### 4. **Componente de Sostenibilidad Ambiental**
- **Clase**: `SustainabilityAnalyzer` en backend
- **Funcionalidad**:
  - Integra q(t) en el tiempo para calcular **Horas-Vehículo de retraso**
  - Estima **emisiones de CO2** por ralentí (tasa: 0.12 kg CO2/hora por motor)
  - Genera **reportes comparativos** entre sincronización manual vs. optimizada
  - Muestra porcentaje de **reducción de contaminación** tras optimización
  - Métricas equivalentes: árboles necesarios, viajes evitados, km equivalentes
- **Activación**: Automática cuando se detecta estado estacionario (Diferenciación Numérica)
- **Reporte**: Generado en terminal al presionar `G` o hacer clic en "Generar Reporte"

## Instalación

1. **Clonar o descargar el repositorio**:
   ```bash
   cd trafico-meth
   ```

2. **Crear entorno virtual**:
   ```bash
   python -m venv .venv
   ```

3. **Activar el entorno**:
   - **Windows (PowerShell)**:
     ```powershell
     .\.venv\Scripts\Activate.ps1
     ```
   - **Windows (CMD)**:
     ```cmd
     .venv\Scripts\activate.bat
     ```
   - **Linux/macOS**:
     ```bash
     source .venv/bin/activate
     ```

4. **Instalar dependencias**:
   ```bash
   pip install numpy pygame
   ```

## Uso

### Opción 1: Ejecutar desde terminal
```bash
python frontend.py
```

### Opción 2: Doble clic en Windows
- **Con consola**: `run_simulation.bat`
- **Sin consola**: `run_simulation.pyw`

## Controles Interactivos

| Acción | Tecla/Control |
|--------|---------------|
| Spawnear vehículos en entrada N-S (arriba-abajo) | `1` |
| Spawnear vehículos en entrada E-O (izquierda) | `2` |
| Spawnear vehículos en entrada S-N (abajo) | `3` |
| Spawnear vehículos en entrada O-E (derecha) | `4` |
| Optimizar tiempos de semáforo | `O` o click en botón |
| Generar reporte de sostenibilidad | `G` o click en botón |
| Resetear simulación | `R` |
| Salir | `ESC` o click X |

### Sliders de Control
- **Verde N-S**: Ajusta tiempo de luz verde (5-60s)
- **Verde E-O**: Ajusta tiempo de luz verde (5-60s)

## Visualización de Métricas

La pantalla muestra en tiempo real:

1. **R'(t)**: Derivada de la tasa de llegada (veh/s)
2. **Colas**: Longitud de cola en cada dirección (q0, q1, q2, q3)
3. **Newton**: Solución del sistema no lineal [x1, x2]
4. **Error**: Norma del residuo de convergencia ||F(X)||
5. **Estado Estacionario**: Indicador de convergencia
6. **Conteos de entrada**: Vehículos detectados en sensores
7. **Sostenibilidad**: CO2 total, retraso en veh-h, porcentaje de reducción

## Estructura del Código

```
trafico-meth/
├── numerical_engine.py      # Motor numérico (sin pygame)
│   ├── estimate_arrival_rate_derivative()   # Diferenciación numérica
│   ├── solve_newton_raphson()               # Newton-Raphson matricial
│   └── heun_queue_update()                  # Método de Heun
├── frontend.py              # Interfaz con Pygame
│   ├── TrafficSimulationFrontend            # Clase principal
│   ├── SimpleButton                         # Widget de botón
│   └── SimpleSlider                         # Widget de slider
├── run_simulation.bat       # Lanzador para Windows (con consola)
├── run_simulation.pyw       # Lanzador para Windows (sin consola)
└── README.md                # Este archivo
```

## Detalles de Implementación

### Backend Numérico (`numerical_engine.py`)
- **Desacoplado**: No importa Pygame ni depende de UI
- **Manual**: Solo usa NumPy para operaciones matriciales básicas
- **Modular**: Cada método numérico es independiente y puede ser usado en otros contextos

### Frontend (`frontend.py`)
- **Sensores Virtuales**: Generan vehículos aleatoriamente en las 4 entradas
- **Control de Semáforos**: Estados dinámicos (verde, rojo, amarillo)
- **Renderizado Físico**: Las colas se dibujan proporcionalmente a q(t)
- **Optimización**: El botón ejecuta Newton-Raphson para hallar tiempos óptimos

## Ejemplo de Uso Pedagógico

### Para una presentación/exposición:

1. Abre el simulador
2. Presiona `1` varias veces para generar tráfico en una dirección
3. Observa cómo q(t) crece según el método de Heun
4. Presiona `O` para optimizar
5. Muestra en pantalla:
   - La derivada R'(t) bajando (estacionario)
   - Newton convergiendo (residuo tendiendo a 0)
   - Los tiempos ajustándose automáticamente
6. Presiona `G` para generar un reporte de sostenibilidad
7. En la terminal aparecerá:
   - Horas-Vehículo de retraso por dirección
   - Emisiones totales de CO2
   - Porcentaje de reducción de contaminación
   - Equivalentes ambientales (árboles, viajes, combustible)

## Notas Técnicas

- **Paso de tiempo**: h = 0.016s (60 FPS)
- **Precisión de Newton**: tol = 1e-8
- **Ventana**: 1200x800 píxeles
- **Stationarity window**: últimos 3 conteos (configurables)

## Requisitos

- Python 3.8+
- NumPy >= 1.20
- Pygame >= 2.5.0

## Licencia

Código educativo. Libre para usar y modificar.

---

**Autor**: Generado para propósitos educativos de Métodos Numéricos.
**Fecha**: Julio 2026
