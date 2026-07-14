# Simulador de Tráfico 2D - Métodos Numéricos

Un simulador dinámico de tráfico en 2D que integra tres unidades de métodos numéricos para la optimización de intersecciones viales, con un módulo de análisis de sostenibilidad ambiental que exporta reportes en Excel.

## Características

### Unidades de Métodos Numéricos Implementadas

#### 1. **UNIDAD III: Integración Numérica (Regla de Simpson 1/3)**
- **Función**: Calcula el área bajo la curva de longitud de cola q(t) para obtener **Horas-Vehículo de retraso**
- **Método**: Regla de Simpson 1/3 compuesta
- **Entrada**: Historial de colas q(t) muestreado en el tiempo
- **Comportamiento**:
  - n par → Simpson 1/3 pura (exacta para polinomios de grado ≤ 3)
  - n impar → Simpson en los primeros n-1 tramos + Trapecio en el último
  - n = 1 → Trapecio; n ≤ 0 → 0
- **API**: `composite_simpson(q_list, h)` / `engine.integrate_simpson(q_list, h)`

#### 2. **UNIDAD I: Newton-Raphson Matricial**
- **Objetivo**: Resolver el reparto óptimo de verde F(X) = 0 según la demanda de cada eje
- **Sistema**: `[λ_ns/g_ns − λ_ew/g_ew, g_ns + g_ew − g_total]`
- **Método**: Newton-Raphson matricial con Jacobiana numérica por diferencias finitas
- **Iteración**:
  - Calcular: $J(X_k) \Delta X = -F(X_k)$
  - Actualizar: $X_{k+1} = X_k + \Delta X$
- **API**: `solve_green_split(λ_ns, λ_ew, g_total, ...)` → `{solution, converged, residual_norm, iterations}`
- **Caso borde**: demanda cero → reparto equitativo

#### 3. **UNIDAD IV: Método de Euler Modificado (Heun)**
- **Problema**: Evolucionar la longitud de cola q(t) frente a semáforos rojos
- **EDO**: $\frac{dq}{dt} = T_{entrada}(t) - T_{salida}(t)$
- **Algoritmo Predictor-Corrector**:
  - Predictor: $\tilde{q}_{i+1} = q_i + h \cdot f(t_i, q_i)$
  - Corrector: $q_{i+1} = q_i + \frac{h}{2}[f(t_i, q_i) + f(t_{i+1}, \tilde{q}_{i+1})]$
- **Restricción Física**: $q(t) \geq 0$ (no colas negativas)
- **API**: `heun_queue_update(q_prev, t, h, entry, exit)`. También usado por `project_emissions()` para proyectar emisiones antes/después de optimizar.

### 4. **Componente de Sostenibilidad Ambiental**
- **Clase**: `SustainabilityAnalyzer` en `numerical_engine.py`
- **Funcionalidad**:
  - Integra q(t) con **Simpson 1/3** para calcular **Horas-Vehículo de retraso**
  - Estima **emisiones de CO2** por ralentí (tasa: 0.12 kg CO2/hora por motor)
  - Genera **reportes comparativos** entre sincronización manual (baseline) vs. optimizada
  - Calcula el porcentaje de **reducción de contaminación** tras optimización
  - Métricas equivalentes: árboles necesarios, viajes evitados, km equivalentes
- **Reporte**: Archivo **Excel (.xlsx)** con estilos y gráficas — hojas *Dashboard*, *Por Dirección*, *Serie Temporal* e *Impacto*. Se genera con la tecla `E` o el botón "Exportar Excel". Nombre con marca de tiempo automática.
- **API**: `export_to_excel(filename)`, `set_baseline()`, `set_optimized()`, `calculate_total_emissions()`

## Ejecutables (sin instalar nada)

El proyecto entrega binarios **autocontenidos** para cada sistema operativo — no
requieren Python ni dependencias, solo descargar y ejecutar.

### Descargar (recomendado)
En la pestaña **Releases** de GitHub hay un binario por plataforma (generados
automáticamente por GitHub Actions en runners nativos):

| Sistema | Archivo | Cómo correr |
|---------|---------|-------------|
| Windows | `SmartIntersection-windows.exe` | doble clic |
| macOS   | `SmartIntersection-macos` | `chmod +x` y abrir (o `./SmartIntersection-macos`) |
| Linux   | `SmartIntersection-linux` | `chmod +x` y `./SmartIntersection-linux` |

### Construir el ejecutable localmente
PyInstaller **no** hace cross-compilación: cada binario se construye en su propio SO.

- **Linux / macOS**: `./build.sh`
- **Windows**: `build.bat`

Salida: `dist/SmartIntersection` (o `.exe`). El `.spec` (`trafic_meth.spec`) es la
fuente de verdad de la configuración de empaquetado; el workflow
`.github/workflows/build.yml` compila los 3 SO y adjunta los binarios a la Release
al publicar un tag `vX.Y.Z`.

---

## Instalación (para desarrollo / desde código)

1. **Clonar o descargar el repositorio**:
   ```bash
   cd trafic-meth
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
   pip install -r requirements.txt
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
| Optimizar tiempos de semáforo | `O` o botón "Optimizar" |
| Exportar reporte de sostenibilidad a Excel | `E` o botón "Exportar Excel" |
| Abrir/cerrar la ayuda didáctica numérica | `H` o botón "? Ayuda didáctica" |
| Activar/desactivar música de fondo | `M` |
| Resetear simulación | `R` |
| Salir | `ESC` o click X |

> Cada pulsación de `1`-`4` añade 2 vehículos a esa entrada.

### Ayuda didáctica (`H`)
Modal *Didáctica Numérica* que explica cada método (Newton-Raphson, Euler
Modificado/Heun, Simpson 1/3). Navega entre pestañas con `←`/`→` (o clic); cierra
con `H`/`ESC`. Contenido en `modulo_explicativo.py`.

### Sliders de Control
- **Verde N-S**: Ajusta tiempo de luz verde (5-60s)
- **Verde E-O**: Ajusta tiempo de luz verde (5-60s)

## Visualización de Métricas

La pantalla muestra en tiempo real:

1. **Colas**: Longitud de cola en cada dirección (q0, q1, q2, q3)
2. **Newton / reparto de verde**: Solución del sistema no lineal [g_ns, g_ew]
3. **Error**: Norma del residuo de convergencia ||F(X)||
4. **Conteos de entrada**: Vehículos detectados en sensores
5. **Sostenibilidad**: CO2 total, retraso en veh-h, porcentaje de reducción (baseline vs. optimizado)

## Estructura del Código

```
trafic-meth/
├── numerical_engine.py      # Motor numérico (sin pygame)
│   ├── composite_simpson()               # Integración numérica (Simpson 1/3)
│   ├── TrafficSimulationEngine
│   │   ├── integrate_simpson()           # Wrapper de Simpson
│   │   ├── heun_queue_update()           # Euler modificado (Heun)
│   │   ├── step()                        # Avance de colas con máscara de verde
│   │   ├── solve_green_split()           # Newton-Raphson (reparto de verde)
│   │   └── project_emissions()           # Proyección de CO2 vía Heun
│   └── SustainabilityAnalyzer            # Análisis y reporte de emisiones
│       └── export_to_excel()             # Reporte .xlsx con gráficas
├── frontend.py              # Interfaz con Pygame
│   ├── TrafficSimulationFrontend         # Clase principal
│   ├── HelpOverlay                       # Modal de ayuda didáctica
│   ├── SimpleButton / SimpleSlider       # Widgets de UI
├── modulo_explicativo.py    # Contenido didáctico de cada método
├── music.py                 # Música chiptune procedural (opcional)
├── test_numerical_methods.py# Pruebas de los métodos numéricos
├── test_sustainability.py   # Prueba del modelo de sostenibilidad
├── run_simulation.bat       # Lanzador para Windows (con consola)
├── run_simulation.pyw       # Lanzador para Windows (sin consola)
└── README.md                # Este archivo
```

## Detalles de Implementación

### Backend Numérico (`numerical_engine.py`)
- **Desacoplado**: No importa Pygame ni depende de UI
- **Manual**: Solo usa NumPy para operaciones matriciales; `openpyxl` solo para el reporte Excel
- **Modular**: Cada método numérico es independiente y puede ser usado en otros contextos
- **Constantes clave**: `SATURATION_FLOW = 0.9` veh/s en verde, `ARRIVAL_CAP = 0.6`, `AXIS_SATURATION = 1.6` veh/s por eje

### Frontend (`frontend.py`)
- **Sensores Virtuales**: Generan vehículos aleatoriamente en las 4 entradas
- **Control de Semáforos**: Estados dinámicos (verde, rojo, amarillo) con máscara de verde por dirección
- **Renderizado Físico**: Las colas se dibujan proporcionalmente a q(t)
- **Optimización**: El botón ejecuta `solve_green_split` (Newton-Raphson) para hallar el reparto de verde óptimo y proyecta las emisiones resultantes

## Ejemplo de Uso Pedagógico

### Para una presentación/exposición:

1. Abre el simulador
2. Presiona `1` varias veces para generar tráfico en una dirección
3. Observa cómo q(t) crece según el método de Heun
4. Presiona `O` para optimizar
5. Muestra en pantalla:
   - Newton convergiendo (residuo tendiendo a 0)
   - El reparto de verde ajustándose a la demanda
   - El overlay comparativo antes/después de emisiones
6. Presiona `E` para exportar el reporte de sostenibilidad a Excel
7. El archivo `.xlsx` incluye:
   - Horas-Vehículo de retraso por dirección
   - Emisiones totales de CO2 (baseline vs. optimizado)
   - Porcentaje de reducción de contaminación
   - Equivalentes ambientales (árboles, viajes, km) y gráficas
8. (Opcional) Presiona `H` para abrir la ayuda didáctica de cada método

## Notas Técnicas

- **Paso de tiempo**: h = 0.016s (60 FPS) en el frontend
- **Precisión de Newton**: tol ≈ 1e-8
- **Ventana**: redimensionable (responsive, se ajusta al escritorio)
- **Reporte**: Excel con marca de tiempo, p. ej. `reporte_sostenibilidad_YYYYMMDD_HHMMSS.xlsx`

## Pruebas

Las pruebas se ejecutan de forma independiente (imprimen resultados, no usan pytest):

```bash
python test_numerical_methods.py
python test_sustainability.py
```

## Requisitos

- Python 3.10+
- NumPy >= 1.20
- Pygame >= 2.5
- openpyxl >= 3.1  (reporte Excel)
- PyInstaller >= 6.0  (solo para construir ejecutables)

## Licencia

Código educativo. Libre para usar y modificar.

---

**Autor**: Generado para propósitos educativos de Métodos Numéricos.
**Fecha**: Julio 2026
