"""Frontend mejorado con Pygame - Ventana redimensionable, responsive y sin elementos superpuestos."""

from __future__ import annotations

import random
from typing import Callable
import os

import numpy as np
import pygame

from numerical_engine import TrafficSimulationEngine, SustainabilityAnalyzer

# Dimensiones iniciales
INITIAL_WIDTH = 1400
INITIAL_HEIGHT = 900
MIN_WIDTH = 900
MIN_HEIGHT = 600

ROAD_WIDTH = 100

# Colores
BACKGROUND_COLOR = (15, 15, 15)
ROAD_COLOR = (50, 50, 50)
LANE_COLOR = (200, 200, 200)
CENTER_COLOR = (255, 215, 0)
VEHICLE_COLOR = (255, 100, 100)
VEHICLE_QUEUE_COLOR = (255, 50, 50)
TRAFFIC_LIGHT_RED = (255, 50, 50)
TRAFFIC_LIGHT_GREEN = (50, 255, 50)
TRAFFIC_LIGHT_YELLOW = (255, 255, 50)
BUTTON_COLOR = (100, 150, 255)
BUTTON_HOVER_COLOR = (120, 170, 255)
BUTTON_ACTIVE_COLOR = (80, 120, 255)
TEXT_COLOR = (255, 255, 255)
SLIDER_COLOR = (150, 150, 150)
SLIDER_TRACK_COLOR = (80, 80, 80)
PANEL_BG_COLOR = (25, 25, 35)
PANEL_BORDER_COLOR = (80, 80, 100)
SUCCESS_COLOR = (100, 255, 100)
ERROR_COLOR = (255, 100, 100)


class SimpleButton:
    """Botón interactivo en Pygame."""

    def __init__(self, x: float, y: float, width: float, height: float, text: str) -> None:
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.hovered = False
        self.active = False

    def draw(self, screen: pygame.Surface, font: pygame.font.Font) -> None:
        color = BUTTON_ACTIVE_COLOR if self.active else (BUTTON_HOVER_COLOR if self.hovered else BUTTON_COLOR)
        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, TEXT_COLOR, self.rect, 2)
        text_surf = font.render(self.text, True, TEXT_COLOR)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)

    def update(self, mouse_pos: tuple[float, float]) -> None:
        self.hovered = self.rect.collidepoint(mouse_pos)

    def is_clicked(self, mouse_pos: tuple[float, float], mouse_pressed: bool) -> bool:
        return self.hovered and mouse_pressed
    
    def reposition(self, x: float, y: float, width: float = None, height: float = None) -> None:
        """Reposiciona el botón."""
        self.rect.x = x
        self.rect.y = y
        if width is not None:
            self.rect.width = width
        if height is not None:
            self.rect.height = height


class SimpleSlider:
    """Slider horizontal para control de parámetros."""

    def __init__(self, x: float, y: float, width: float, min_val: float, max_val: float, initial: float, label: str) -> None:
        self.rect = pygame.Rect(x, y, width, 30)
        self.min_val = min_val
        self.max_val = max_val
        self.value = initial
        self.label = label
        self.dragging = False

    def draw(self, screen: pygame.Surface, font: pygame.font.Font) -> None:
        pygame.draw.rect(screen, SLIDER_TRACK_COLOR, self.rect)
        pygame.draw.rect(screen, TEXT_COLOR, self.rect, 1)

        normalized = (self.value - self.min_val) / (self.max_val - self.min_val)
        handle_x = self.rect.x + normalized * self.rect.width
        pygame.draw.circle(screen, SLIDER_COLOR, (int(handle_x), self.rect.y + 15), 8)

        label_text = font.render(f"{self.label}: {self.value:.1f}s", True, TEXT_COLOR)
        screen.blit(label_text, (self.rect.x, self.rect.y - 20))

    def update(self, mouse_pos: tuple[float, float], mouse_pressed: bool) -> None:
        if mouse_pressed and self.rect.collidepoint(mouse_pos):
            self.dragging = True
        elif not mouse_pressed:
            self.dragging = False

        if self.dragging:
            normalized = (mouse_pos[0] - self.rect.x) / self.rect.width
            normalized = max(0.0, min(1.0, normalized))
            self.value = self.min_val + normalized * (self.max_val - self.min_val)
    
    def reposition(self, x: float, y: float, width: float) -> None:
        """Reposiciona el slider."""
        self.rect.x = x
        self.rect.y = y
        self.rect.width = width


class ReportPanel:
    """Panel para mostrar el reporte de sostenibilidad con scroll."""

    def __init__(self, x: float, y: float, width: float, height: float) -> None:
        self.rect = pygame.Rect(x, y, width, height)
        self.text_lines = []
        self.scroll_offset = 0
        self.line_height = 16
        self.visible = False

    def set_report(self, report_text: str) -> None:
        """Establece el texto del reporte."""
        self.text_lines = report_text.split('\n')
        self.scroll_offset = 0

    def handle_scroll(self, mouse_wheel_y: int) -> None:
        """Maneja el scroll del mouse."""
        self.scroll_offset -= mouse_wheel_y * 3
        max_scroll = max(0, len(self.text_lines) * self.line_height - self.rect.height)
        self.scroll_offset = max(0, min(self.scroll_offset, max_scroll))

    def draw(self, screen: pygame.Surface, font: pygame.font.Font) -> None:
        """Dibuja el panel del reporte."""
        if not self.visible:
            return

        # Fondo
        pygame.draw.rect(screen, PANEL_BG_COLOR, self.rect)
        pygame.draw.rect(screen, PANEL_BORDER_COLOR, self.rect, 2)

        # Crear surface de clipping
        clip_rect = self.rect.copy()
        screen.set_clip(clip_rect)

        # Dibujar líneas
        y_pos = self.rect.y - self.scroll_offset
        for line in self.text_lines:
            if y_pos > self.rect.bottom:
                break
            if y_pos + self.line_height > self.rect.y:
                text_surf = font.render(line, True, TEXT_COLOR)
                screen.blit(text_surf, (self.rect.x + 10, y_pos))
            y_pos += self.line_height

        screen.set_clip(None)


class TrafficSimulationFrontend:
    """Frontend interactivo redimensionable con sensores, control de semáforos y visualización de métricas."""

    def __init__(self, width: int = INITIAL_WIDTH, height: int = INITIAL_HEIGHT) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
        pygame.display.set_caption("Simulador de Tráfico 2D - Métodos Numéricos")
        self.clock = pygame.time.Clock()
        self.font_tiny = pygame.font.SysFont(None, 14)
        self.font_small = pygame.font.SysFont(None, 16)
        self.font_medium = pygame.font.SysFont(None, 20)
        self.font_large = pygame.font.SysFont(None, 28)

        self.width = width
        self.height = height
        self.engine = TrafficSimulationEngine(h=0.016)
        self.sustainability_analyzer = SustainabilityAnalyzer(co2_idle_rate=0.12)

        self.discrete_counts = [0, 0, 0, 0]
        self.spawn_timers = [0.0, 0.0, 0.0, 0.0]
        self.spawn_probability = 0.15

        self.green_time_ns = 25.0
        self.green_time_ew = 25.0
        self.red_time = 5.0
        self.traffic_light_timer = 0.0
        self.light_state = "green_ns"

        # Crear elementos UI
        self.optimize_button = SimpleButton(0, 0, 180, 40, "Optimizar")
        self.report_button = SimpleButton(0, 0, 180, 40, "Gen. Reporte")
        self.green_ns_slider = SimpleSlider(0, 0, 200, 5.0, 60.0, 25.0, "Verde N-S")
        self.green_ew_slider = SimpleSlider(0, 0, 200, 5.0, 60.0, 25.0, "Verde E-O")

        self.newton_iterations = 0
        self.newton_converged = False
        self.last_optimization_time = 0.0
        self.baseline_set = False
        self.report_generated = False
        
        # Panel de reporte y status
        self.report_panel = ReportPanel(0, 0, 400, 300)
        self.status_message = ""
        self.status_timer = 0.0
        self.status_color = SUCCESS_COLOR
        self.show_report = False

        self.running = True
        self.update_layout()

    def update_layout(self) -> None:
        """Recalcula el layout de los elementos según el tamaño de la ventana."""
        # Paneles: Izquierda (controles), Centro (visualización), Derecha (métricas)
        self.left_panel_width = 250
        self.right_panel_width = 300
        self.center_start_x = self.left_panel_width + 10
        self.center_width = max(300, self.width - self.left_panel_width - self.right_panel_width - 20)
        
        # Posiciones de botones
        button_x = 20
        button_width = self.left_panel_width - 40
        self.optimize_button.reposition(button_x, 20, button_width, 40)
        self.report_button.reposition(button_x, 70, button_width, 40)
        
        # Posiciones de sliders
        slider_x = 20
        slider_width = self.left_panel_width - 40
        self.green_ns_slider.reposition(slider_x, 140, slider_width)
        self.green_ew_slider.reposition(slider_x, 220, slider_width)
        
        # Posición del panel de reporte
        report_panel_x = self.center_start_x
        report_panel_y = self.height - 250
        report_panel_width = self.center_width
        report_panel_height = 240
        self.report_panel.rect.x = report_panel_x
        self.report_panel.rect.y = report_panel_y
        self.report_panel.rect.width = report_panel_width
        self.report_panel.rect.height = report_panel_height

    def spawn_vehicles(self, dt: float) -> None:
        """Genera vehículos aleatoriamente en las entradas de la intersección."""
        for i in range(4):
            self.spawn_timers[i] += dt
            if self.spawn_timers[i] > (1.0 / max(0.1, self.spawn_probability)):
                if random.random() < self.spawn_probability:
                    self.discrete_counts[i] += 1
                    self.spawn_timers[i] = 0.0

    def update_traffic_light(self, dt: float) -> None:
        """Actualiza el estado del semáforo basándose en temporizadores."""
        self.traffic_light_timer += dt

        if self.light_state == "green_ns":
            if self.traffic_light_timer >= self.green_time_ns:
                self.light_state = "red_ns"
                self.traffic_light_timer = 0.0
        elif self.light_state == "red_ns":
            if self.traffic_light_timer >= self.red_time:
                self.light_state = "green_ew"
                self.traffic_light_timer = 0.0
        elif self.light_state == "green_ew":
            if self.traffic_light_timer >= self.green_time_ew:
                self.light_state = "red_ew"
                self.traffic_light_timer = 0.0
        elif self.light_state == "red_ew":
            if self.traffic_light_timer >= self.red_time:
                self.light_state = "green_ns"
                self.traffic_light_timer = 0.0

    def optimize_traffic_signals(self) -> None:
        """Ejecuta Newton-Raphson para optimizar tiempos de semáforo."""
        initial_guess = np.array([self.green_time_ns / 30.0, self.green_time_ew / 30.0])
        result = self.engine.solve_newton_raphson(initial_guess, tol=1e-6, max_iter=20)

        self.newton_converged = result["converged"]
        self.newton_iterations = 20 if not self.newton_converged else 10

        if self.newton_converged:
            solution = result["solution"]
            self.green_time_ns = max(5.0, min(60.0, solution[0] * 30.0))
            self.green_time_ew = max(5.0, min(60.0, solution[1] * 30.0))
            self.sustainability_analyzer.set_optimized()
            self.green_ns_slider.value = self.green_time_ns
            self.green_ew_slider.value = self.green_time_ew

    def draw_left_panel(self) -> None:
        """Dibuja el panel de control izquierdo."""
        panel_rect = pygame.Rect(0, 0, self.left_panel_width, self.height)
        pygame.draw.rect(self.screen, PANEL_BG_COLOR, panel_rect)
        pygame.draw.line(self.screen, PANEL_BORDER_COLOR, (self.left_panel_width, 0), 
                        (self.left_panel_width, self.height), 2)
        
        # Título
        title = self.font_medium.render("CONTROLES", True, (100, 200, 100))
        self.screen.blit(title, (20, 5))
        
        # Botones
        self.optimize_button.draw(self.screen, self.font_small)
        self.report_button.draw(self.screen, self.font_small)
        
        # Sliders
        self.green_ns_slider.draw(self.screen, self.font_tiny)
        self.green_ew_slider.draw(self.screen, self.font_tiny)
        
        # Instrucciones
        instructions = [
            "Teclas:",
            "1-4: Spawnear",
            "O: Optimizar",
            "G: Reporte",
            "R: Resetear",
            "ESC: Salir"
        ]
        y_pos = 310
        for instr in instructions:
            text = self.font_tiny.render(instr, True, (150, 150, 150))
            self.screen.blit(text, (20, y_pos))
            y_pos += 22

    def draw_right_panel(self) -> None:
        """Dibuja el panel de métricas derecho."""
        panel_x = self.width - self.right_panel_width
        panel_rect = pygame.Rect(panel_x, 0, self.right_panel_width, self.height)
        pygame.draw.rect(self.screen, PANEL_BG_COLOR, panel_rect)
        pygame.draw.line(self.screen, PANEL_BORDER_COLOR, (panel_x, 0), (panel_x, self.height), 2)
        
        # Título
        title = self.font_medium.render("MÉTRICAS", True, (100, 150, 255))
        self.screen.blit(title, (panel_x + 20, 5))
        
        y_pos = 40
        margin = 15
        
        # Derivada
        arrival_derivative = self.engine.arrival_rate_derivative
        text = self.font_tiny.render(f"R'(t): {arrival_derivative:.4f} v/s", True, TEXT_COLOR)
        self.screen.blit(text, (panel_x + margin, y_pos))
        y_pos += 22
        
        # Colas
        queue_text = "Colas:"
        text = self.font_tiny.render(queue_text, True, TEXT_COLOR)
        self.screen.blit(text, (panel_x + margin, y_pos))
        y_pos += 18
        for i, q in enumerate(self.engine.queue_state):
            text = self.font_tiny.render(f"  q{i}: {q:.2f}", True, (200, 200, 200))
            self.screen.blit(text, (panel_x + margin, y_pos))
            y_pos += 18
        
        # Newton
        y_pos += 5
        text = self.font_tiny.render("Newton-Raphson:", True, (100, 200, 100))
        self.screen.blit(text, (panel_x + margin, y_pos))
        y_pos += 18
        
        if self.engine.newton_solution is not None:
            sol = self.engine.newton_solution
            text = self.font_tiny.render(f"x=[{sol[0]:.4f},{sol[1]:.4f}]", True, TEXT_COLOR)
            self.screen.blit(text, (panel_x + margin, y_pos))
            y_pos += 18
        
        text = self.font_tiny.render(f"Error: {self.engine.newton_residual_norm:.2e}", True, TEXT_COLOR)
        self.screen.blit(text, (panel_x + margin, y_pos))
        y_pos += 22
        
        # Estado estacionario
        color = (100, 255, 100) if self.engine.stationary_flag else (255, 100, 100)
        status = "Sí" if self.engine.stationary_flag else "No"
        text = self.font_tiny.render(f"Estac.: {status}", True, color)
        self.screen.blit(text, (panel_x + margin, y_pos))
        y_pos += 22
        
        # Vehículos
        text = self.font_tiny.render(f"Veh. entrada: {sum(self.discrete_counts)}", True, TEXT_COLOR)
        self.screen.blit(text, (panel_x + margin, y_pos))
        y_pos += 25
        
        # Sostenibilidad
        text = self.font_small.render("SOSTENIBILIDAD", True, (100, 200, 100))
        self.screen.blit(text, (panel_x + margin, y_pos))
        y_pos += 22
        
        emissions = self.sustainability_analyzer.calculate_total_emissions()
        text = self.font_tiny.render(f"CO2: {emissions['total_co2']:.3f} kg", True, TEXT_COLOR)
        self.screen.blit(text, (panel_x + margin, y_pos))
        y_pos += 18
        
        text = self.font_tiny.render(f"Retraso: {emissions['total_veh_hours']:.3f} vh", True, TEXT_COLOR)
        self.screen.blit(text, (panel_x + margin, y_pos))
        y_pos += 18
        
        if self.sustainability_analyzer.optimization_applied and self.sustainability_analyzer.baseline_emissions > 1e-9:
            reduction_pct = (
                (self.sustainability_analyzer.baseline_emissions - self.sustainability_analyzer.optimized_emissions)
                / self.sustainability_analyzer.baseline_emissions
                * 100
            )
            color = (50, 200, 50) if reduction_pct > 0 else (255, 100, 100)
            text = self.font_small.render(f"Reduc: {reduction_pct:.1f}%", True, color)
            self.screen.blit(text, (panel_x + margin, y_pos))

    def draw_intersection(self) -> None:
        """Dibuja la intersección vial en el área central."""
        center_start_y = 0
        center_end_x = self.width - self.right_panel_width
        
        # Fondo
        pygame.draw.rect(self.screen, BACKGROUND_COLOR, 
                        (self.center_start_x, center_start_y, self.center_width, self.height))
        
        # Calcular centro del área de visualización
        center_x = self.center_start_x + self.center_width // 2
        center_y = self.height // 2
        
        # Carreteras
        pygame.draw.rect(
            self.screen,
            ROAD_COLOR,
            (self.center_start_x, center_y - ROAD_WIDTH // 2, self.center_width, ROAD_WIDTH),
        )

        pygame.draw.rect(
            self.screen,
            ROAD_COLOR,
            (center_x - ROAD_WIDTH // 2, center_start_y, ROAD_WIDTH, self.height),
        )

        # Líneas divisorias
        for x in range(int(self.center_start_x), int(center_end_x), 120):
            pygame.draw.rect(self.screen, LANE_COLOR, (x, center_y - 4, 60, 8))

        for y in range(0, self.height, 120):
            pygame.draw.rect(self.screen, LANE_COLOR, (center_x - 4, y, 8, 60))

        # Centro
        pygame.draw.rect(
            self.screen,
            CENTER_COLOR,
            (center_x - 30, center_y - 30, 60, 60),
        )

    def draw_traffic_lights(self) -> None:
        """Dibuja los semáforos."""
        center_x = self.center_start_x + self.center_width // 2
        center_y = self.height // 2
        
        light_positions = [
            (center_x + 80, center_y - 150),
            (center_x - 150, center_y - 80),
            (center_x - 80, center_y + 150),
            (center_x + 150, center_y + 80),
        ]

        for idx, (x, y) in enumerate(light_positions):
            if idx in (0, 2):
                is_green = self.light_state in ("green_ns", "yellow_ns")
            else:
                is_green = self.light_state in ("green_ew", "yellow_ew")

            color = TRAFFIC_LIGHT_GREEN if is_green else TRAFFIC_LIGHT_RED
            pygame.draw.circle(self.screen, color, (int(x), int(y)), 15)
            pygame.draw.circle(self.screen, TEXT_COLOR, (int(x), int(y)), 15, 2)

    def draw_vehicle_queues(self) -> None:
        """Dibuja vehículos en fila."""
        center_x = self.center_start_x + self.center_width // 2
        center_y = self.height // 2
        
        queue_start_positions = [
            (center_x + 50, center_y - 120, 0, -1),
            (center_x - 120, center_y - 50, -1, 0),
            (center_x - 50, center_y + 120, 0, 1),
            (center_x + 120, center_y + 50, 1, 0),
        ]

        for idx, (x, y, dx, dy) in enumerate(queue_start_positions):
            queue_length = int(self.engine.queue_state[idx])
            for vehicle_idx in range(queue_length):
                vehicle_x = x + dx * vehicle_idx * 30
                vehicle_y = y + dy * vehicle_idx * 30
                pygame.draw.rect(
                    self.screen,
                    VEHICLE_QUEUE_COLOR,
                    (int(vehicle_x) - 12, int(vehicle_y) - 8, 24, 16),
                )

    def handle_events(self) -> None:
        """Maneja eventos de entrada del usuario."""
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()[0]

        self.optimize_button.update(mouse_pos)
        self.report_button.update(mouse_pos)
        self.green_ns_slider.update(mouse_pos, mouse_pressed)
        self.green_ew_slider.update(mouse_pos, mouse_pressed)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.VIDEORESIZE:
                self.width = max(MIN_WIDTH, event.size[0])
                self.height = max(MIN_HEIGHT, event.size[1])
                self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
                self.update_layout()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_1:
                    self.discrete_counts[0] += 2
                elif event.key == pygame.K_2:
                    self.discrete_counts[1] += 2
                elif event.key == pygame.K_3:
                    self.discrete_counts[2] += 2
                elif event.key == pygame.K_4:
                    self.discrete_counts[3] += 2
                elif event.key == pygame.K_r:
                    self.discrete_counts = [0, 0, 0, 0]
                    self.engine = TrafficSimulationEngine(h=0.016)
                    self.sustainability_analyzer.reset()
                    self.baseline_set = False
                    self.report_generated = False
                elif event.key == pygame.K_o:
                    self.optimize_traffic_signals()
                elif event.key == pygame.K_g:
                    self.generate_sustainability_report()
                elif event.key == pygame.K_s:
                    self.save_report()
                elif event.key == pygame.K_e:
                    self.export_csv()
                elif event.key == pygame.K_SPACE:
                    self.show_report = not self.show_report
                    if self.show_report:
                        self.set_status("Reporte mostrado (ESPACIO para ocultar)", SUCCESS_COLOR)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if self.optimize_button.is_clicked(mouse_pos, True):
                    self.optimize_traffic_signals()
                    self.optimize_button.active = True
                elif self.report_button.is_clicked(mouse_pos, True):
                    self.generate_sustainability_report()
                    self.report_button.active = True
            elif event.type == pygame.MOUSEBUTTONUP:
                self.optimize_button.active = False
                self.report_button.active = False

        self.green_time_ns = self.green_ns_slider.value
        self.green_time_ew = self.green_ew_slider.value

    def generate_sustainability_report(self) -> None:
        """Genera un reporte de sostenibilidad ambiental en la terminal."""
        if not self.report_generated:
            report = self.sustainability_analyzer.generate_sustainability_report()
            print(report)
            self.report_generated = True

    def run(self) -> None:
        """Bucle principal de la simulación."""
        dt = 0.016

        while self.running:
            self.handle_events()
            self.spawn_vehicles(dt)
            self.update_traffic_light(dt)

            self.engine.step(discrete_counts=self.discrete_counts)

            self.sustainability_analyzer.record_state(self.engine.current_time, self.engine.queue_state)

            if self.engine.stationary_flag and not self.baseline_set:
                self.sustainability_analyzer.set_baseline()
                self.baseline_set = True
                print("\n[INFO] Estado estacionario detectado. Línea base establecida para análisis de sostenibilidad.\n")

            # Dibujar todo
            self.draw_intersection()
            self.draw_traffic_lights()
            self.draw_vehicle_queues()
            self.draw_left_panel()
            self.draw_right_panel()

            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()


def main() -> None:
    frontend = TrafficSimulationFrontend()
    frontend.run()


if __name__ == "__main__":
    main()
