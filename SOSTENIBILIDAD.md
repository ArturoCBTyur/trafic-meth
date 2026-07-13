================================================================================
                   COMPONENTE DE SOSTENIBILIDAD AMBIENTAL
             Responsabilidad Social en Simulador de Tráfico 2D
================================================================================

DESCRIPCION GENERAL
================================================================================

El componente de Sostenibilidad Ambiental ("SustainabilityAnalyzer") integra 
análisis de impacto ambiental en el simulador de tráfico, permitiendo evaluar 
cómo las decisiones de optimización de semáforos afectan las emisiones de CO2 
y otros indicadores de sostenibilidad.

FUNDAMENTO MATEMÁTICO
================================================================================

1. CALCULO DE HORAS-VEHICULO DE RETRASO

La métrica fundamental es la integración temporal de la longitud de cola:

    Horas-Vehículo = ∫ q(t) dt   desde t=0 hasta t_final

En forma discreta (regla del trapezoides):

    VH_i = Σ [0.5 * (q(n) + q(n-1)) * Δt]

Donde:
  - q(n): Longitud de cola en el paso n (calculada con Heun)
  - Δt: Paso temporal (0.016 segundos en modo 60 FPS)
  - VH_i: Horas-Vehículo acumulado para dirección i


2. ESTIMACION DE EMISIONES DE CO2 POR RALENTI

Modelo simplificado de emisiones:

    CO2_i = VH_i * r_idle

Donde:
  - r_idle: Tasa de emisión en ralentí (0.12 kg CO2/hora por defecto)
  - Valor tipico para auto: 0.10-0.15 kg CO2/hora con motor encendido
  - Supuesto: Un vehículo por hora-vehículo de retraso


3. ANÁLISIS COMPARATIVO PRE/POST OPTIMIZACION

Criterio de parada (Diferenciación Numérica):
  - R'(t) ≈ 0 para ventana de tiempo
  - Indica estado estacionario del sistema

Flujo de análisis:
  1. Registro de línea base: sincronización manual inicial
  2. Activación de optimización Newton-Raphson
  3. Nuevo estado con tiempos optimizados
  4. Cálculo de reducción:

    Reduccion% = [CO2_baseline - CO2_optimizado] / CO2_baseline * 100


ESTRUCTURA DE LA CLASE
================================================================================

class SustainabilityAnalyzer:

    METODOS PRINCIPALES:
    
    __init__(co2_idle_rate=0.12)
        - Inicializa con tasa de emisión configurable
        - Prepara estructuras para historial de colas
        
    record_state(time, queue_state)
        - Registra estado de colas en cada frame
        - Integra automáticamente para acumular VH y CO2
        
    calculate_total_emissions() -> dict
        - Retorna:
          * total_co2: Emisiones acumuladas (kg)
          * total_veh_hours: Horas-vehículo de retraso
          * average_queue_time: Promedio por dirección
          * emissions_per_vehicle: Ratio CO2 / VH
          
    set_baseline()
        - Establece estado actual como referencia (sincronización manual)
        
    set_optimized()
        - Marca estado actual como post-optimización
        
    generate_sustainability_report() -> str
        - Genera reporte formateado con:
          * Métricas de eficiencia de tráfico
          * Desglose por dirección
          * Impacto ambiental
          * Análisis comparativo (si optimization_applied=True)
          * Equivalentes ambientales
          
    reset()
        - Limpia todos los historiales para nueva simulación


PROCESO DE ACTIVACION
================================================================================

El análisis de sostenibilidad se activa automáticamente:

1. Estado manual: Usuario spawnea vehículos, ajusta semáforos manualmente
   → Sistema comienza a registrar estados en background

2. Estado estacionario detectado (Diferenciación Numérica)
   → R'(t) ≈ 0 durante ventana de tiempo
   → LINEA BASE se establece automáticamente
   → Mensaje en terminal: "Estado estacionario detectado..."

3. Usuario presiona "Optimizar" (Newton-Raphson)
   → Sistema busca tiempos óptimos

4. Post-optimización: Sistema registra nuevos estados con tiempos óptimos

5. Usuario presiona "Generar Reporte" (G)
   → Calcula reducción = baseline - optimizado
   → Imprime reporte completo en terminal


RESULTADOS E INTERPRETACION
================================================================================

EJEMPLO DE REPORTE:

================================================================================
REPORTE DE SOSTENIBILIDAD Y RESPONSABILIDAD SOCIAL
Simulador de Tráfico 2D - Análisis Ambiental
================================================================================

MÉTRICAS DE EFICIENCIA DE TRÁFICO
--------------------------------------------------------------------------------
Tiempo total de simulación: 15.32 segundos
Total de Horas-Vehículo de retraso: 2.847 veh-h
Tiempo promedio de espera: 0.712 h/dirección

DESGLOSE POR DIRECCIÓN
--------------------------------------------------------------------------------
N-S (Arriba)    | Retraso: 0.912 veh-h | CO2: 0.109 kg
E-O (Izq)       | Retraso: 0.635 veh-h | CO2: 0.076 kg
S-N (Abajo)     | Retraso: 0.912 veh-h | CO2: 0.109 kg
O-E (Der)       | Retraso: 0.388 veh-h | CO2: 0.047 kg

IMPACTO AMBIENTAL
--------------------------------------------------------------------------------
Emisiones totales de CO2: 0.341 kg
Equivalente a combustión de: 0.15 litros de gasolina
Emisiones por vehículo en cola: 0.1200 kg CO2

ANÁLISIS COMPARATIVO
--------------------------------------------------------------------------------
Emisiones (Sincronización Manual):      0.341 kg CO2
Emisiones (Sincronización Óptima):      0.268 kg CO2
Reducción absoluta:                     0.073 kg CO2

>>> REDUCCIÓN DE CONTAMINACION:  21.4% <<<

Equivalente ambiental:
  • Árboles necesarios para absorber diferencia: 0.3 árboles
  • Viajes evitados (auto típico): 292 km
  • CO2 equivalente a: 0.2 kg de carbón no quemado

================================================================================

INTERPRETACION:
  - Sincronizar semáforos con Newton-Raphson redujo contaminación 21.4%
  - Equivale a plantar ~0.3 árboles o ahorrar ~292 km de tráfico
  - Beneficio sostenible: Menos congestion = Menos emisiones


VENTAJAS PEDAGOGICAS
================================================================================

1. CONEXION CON ODS
   - Objetivo de Desarrollo Sostenible #11: Ciudades sostenibles
   - Objetivo #13: Acción por el clima
   - Muestra relación directa: Optimización ↔ Reducción emisiones

2. MOTIVACION PARA ALGORITMOS
   - Los estudiantes ven aplicación real de Newton-Raphson
   - No solo es "resolver una ecuación" sino "salvar el planeta"
   - Integración de ciencias: Matemática + Ambiental

3. METRICAS COMPRENSIBLES
   - Árboles plantados: Familiar para todos
   - Viajes evitados: Relatable
   - Combustible ahorrado: Económico/ambiental

4. PARAMETRIZACION FLEXIBLE
   - co2_idle_rate: Cambiar para diferentes tipos de vehículos
   - Tasa europeos: 0.10 kg CO2/h
   - Tasa americanos: 0.15-0.20 kg CO2/h
   - Cambiar rate → Cambiar reducción% → Discusión pedagógica


CASOS DE USO
================================================================================

1. CLASE DE METODOS NUMERICOS
   - "Ustedes acaban de reducir 21% de contaminación con Newton-Raphson"
   - Motiva a estudiantes

2. CLASE DE SOSTENIBILIDAD AMBIENTAL
   - Demuestra impacto de ingeniería en ambiente
   - Pensamiento sistémico: Decisiones → Mediciones → Impacto

3. PROYECTO INTERDISCIPLINARIO
   - Matemáticas + Ingeniería + Ambiental
   - Simulación → Análisis → Reportes

4. PROPUESTA DE CIUDAD INTELIGENTE
   - Mostrar a municipalidades
   - "Podemos reducir 21% de emisiones sin costo"


LIMITACIONES Y MEJORAS FUTURAS
================================================================================

LIMITACIONES ACTUALES:
  - Modelo lineal de emisiones (solo ralentí)
  - No incluye: aceleración, frenado, tipos de vehículos
  - Supone: 1 vehículo/hora de espera (sin multiplicidad)
  - Tasa fija de CO2 (no varía por motor)

MEJORAS POSIBLES:
  - Modelo no lineal: Velocidad → Emisiones
  - Ciclos de conducción reales (NEDC, WLTP)
  - Diferentes tipos de vehículos
  - Predictibilidad: ¿Y si optimizamos más agresivamente?
  - Impacto en NOx, PM2.5, otros contaminantes


ARCHIVOS RELACIONADOS
================================================================================

numerical_engine.py
  └─ class SustainabilityAnalyzer (líneas ~285-390)
  
frontend.py
  └─ Integración en TrafficSimulationFrontend
  └─ draw_sustainability_metrics()
  └─ generate_sustainability_report()
  └─ Botón "Generar Reporte" (tecla G)
  
test_sustainability.py
  └─ Validación completa del componente


================================================================================
Componente de Sostenibilidad Ambiental - Versión 1.0
Responsabilidad Social integrada en Métodos Numéricos
================================================================================
