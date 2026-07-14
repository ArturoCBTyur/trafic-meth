"""Frontend Pygame ultra-moderno: tema oscuro, glassmorphism, glow y vehículos con estilo.

La lógica de simulación (motor numérico, semáforos, sostenibilidad, eventos) es idéntica
a la versión previa; solo se rediseñó por completo la capa de presentación.
"""

from __future__ import annotations

import math
import os
import random
import re
from typing import Callable

import numpy as np
import pygame

from numerical_engine import TrafficSimulationEngine, SustainabilityAnalyzer
from modulo_explicativo import ModuloExplicativo

# Dimensiones iniciales
INITIAL_WIDTH = 1400
INITIAL_HEIGHT = 900
MIN_WIDTH = 900
MIN_HEIGHT = 560

ROAD_WIDTH = 130

# Movimiento de vehículos (capa visual)
VEHICLE_SPEED = 170.0   # px/s
VEHICLE_GAP = 30.0      # separación mínima entre autos (car-following)
LANE_OFFSET = 22        # desplazamiento lateral respecto al eje de la vía

# ----------------------------------------------------------------------------
# PALETA MODERNA (dark UI + acentos neón)
# ----------------------------------------------------------------------------
BG_TOP = (17, 21, 30)
BG_BOTTOM = (9, 11, 16)

GLASS_FILL = (22, 27, 37)
GLASS_ALPHA = 205
GLASS_BORDER = (58, 66, 82)
HAIRLINE = (40, 46, 58)

TEXT_COLOR = (234, 239, 246)
TEXT_DIM = (139, 149, 165)
TEXT_FAINT = (95, 104, 120)

ACCENT = (88, 166, 255)        # azul
ACCENT_CYAN = (86, 211, 231)   # cian
ACCENT_PURPLE = (176, 132, 255)
ACCENT_ORANGE = (255, 148, 92)
SUCCESS_COLOR = (63, 201, 120)
WARN_COLOR = (240, 185, 74)
ERROR_COLOR = (248, 92, 102)

ROAD_TOP = (40, 45, 54)
ROAD_BOTTOM = (26, 29, 36)
LANE_COLOR = (206, 213, 226)
CENTER_COLOR = (245, 191, 66)

# Colores de acento por aproximación (N-S, E-O, S-N, O-E)
APPROACH_COLORS = [ACCENT, ACCENT_CYAN, ACCENT_PURPLE, ACCENT_ORANGE]

TRAFFIC_LIGHT_GREEN = (61, 214, 140)
TRAFFIC_LIGHT_RED = (248, 92, 102)

# Compat (usado por status/reporte)
PANEL_BG_COLOR = GLASS_FILL
PANEL_BORDER_COLOR = GLASS_BORDER

_gradient_cache: dict[tuple, pygame.Surface] = {}


def make_font(size: int, bold: bool = False) -> pygame.font.Font:
    """Carga una fuente moderna del sistema con fallback."""
    font = pygame.font.SysFont(
        "Segoe UI,Roboto,Helvetica Neue,DejaVu Sans,Arial", size, bold=bold
    )
    return font


def vertical_gradient(width: int, height: int, top: tuple, bottom: tuple) -> pygame.Surface:
    """Devuelve (cacheada) una superficie con degradado vertical."""
    key = (width, height, top, bottom)
    cached = _gradient_cache.get(key)
    if cached is not None:
        return cached
    surf = pygame.Surface((width, height))
    if height <= 1:
        surf.fill(top)
    else:
        for y in range(height):
            t = y / (height - 1)
            color = (
                int(top[0] + (bottom[0] - top[0]) * t),
                int(top[1] + (bottom[1] - top[1]) * t),
                int(top[2] + (bottom[2] - top[2]) * t),
            )
            pygame.draw.line(surf, color, (0, y), (width, y))
    if len(_gradient_cache) > 40:
        _gradient_cache.clear()
    _gradient_cache[key] = surf
    return surf


def draw_glow(screen: pygame.Surface, center: tuple, radius: int, color: tuple,
              layers: int = 7, max_alpha: int = 95) -> None:
    """Dibuja un halo suave (glow) alrededor de un punto."""
    radius = max(1, int(radius))
    surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    for i in range(layers, 0, -1):
        t = i / layers
        alpha = int(max_alpha * (t * t))
        r = int(radius * t)
        pygame.draw.circle(surf, (*color, alpha), (radius, radius), r)
    screen.blit(surf, (int(center[0] - radius), int(center[1] - radius)),
                special_flags=pygame.BLEND_RGBA_ADD)


def glass_panel(screen: pygame.Surface, rect: pygame.Rect, radius: int = 16,
                fill: tuple = GLASS_FILL, alpha: int = GLASS_ALPHA,
                border: tuple = GLASS_BORDER, accent: tuple | None = None) -> None:
    """Dibuja un panel translúcido estilo glassmorphism con borde fino."""
    surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(surf, (*fill, alpha), surf.get_rect(), border_radius=radius)
    pygame.draw.rect(surf, (*border, 180), surf.get_rect(), width=1, border_radius=radius)
    screen.blit(surf, rect.topleft)
    if accent is not None:
        pygame.draw.rect(screen, accent, (rect.x, rect.y + 12, 3, 22), border_radius=2)


def latex_to_display(latex: str) -> str:
    """Convierte una fórmula LaTeX a texto plano legible (solo presentación en la UI).

    No intenta un render completo de LaTeX (pygame no lo soporta): sustituye los
    comandos comunes por símbolos unicode y aplana fracciones/sub/superíndices para
    mostrar la fórmula de forma comprensible en un cuadro de texto.
    """
    s = latex
    replacements = {
        # Casos compuestos primero (contienen \, que se sustituiría luego)
        r"_{i\,impar}": " (i impar) ", r"_{i\,par}": " (i par) ",
        r"\qquad": "    ", r"\quad": "   ", r"\,": " ", r"\!": "", r"\;": " ",
        r"\left": "", r"\right": "", r"\int": "∫", r"\sum": "Σ", r"\Delta": "Δ",
        r"\approx": "≈", r"\cdot": "·", r"\times": "×", r"\tilde": "~", r"\frac": "frac",
    }
    for key, val in replacements.items():
        s = s.replace(key, val)
    s = re.sub(r"frac\{([^{}]*)\}\{([^{}]*)\}", r"(\1)/(\2)", s)
    s = re.sub(r"_\{([^{}]*)\}", r"_\1", s)
    s = re.sub(r"\^\{([^{}]*)\}", r"^\1", s)
    s = s.replace("{", "").replace("}", "").replace("\\", "")
    return re.sub(r"\s+", " ", s).strip()


def wrap_text(text: str, font: pygame.font.Font, max_width: int) -> list[str]:
    """Divide un texto en líneas que caben en max_width píxeles."""
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        trial = f"{current} {word}".strip()
        if font.size(trial)[0] <= max_width or not current:
            current = trial
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


class HelpOverlay:
    """Modal de 'Didáctica Numérica': consume ModuloExplicativo y lo muestra en pantalla."""

    SHORT = {
        "newton_raphson": "Newton-Raphson",
        "euler_modificado": "Euler Mod. (Heun)",
        "simpson": "Simpson 1/3",
    }

    def __init__(self, modulo: ModuloExplicativo) -> None:
        self.modulo = modulo
        self.ids = modulo.metodos_disponibles()
        self.index = 0
        self.visible = False
        self.tab_rects: list[tuple[pygame.Rect, int]] = []
        self.close_rect: pygame.Rect | None = None

    def toggle(self) -> None:
        self.visible = not self.visible

    def switch(self, i: int) -> None:
        self.index = i % len(self.ids)

    def next(self) -> None:
        self.index = (self.index + 1) % len(self.ids)

    def prev(self) -> None:
        self.index = (self.index - 1) % len(self.ids)

    def handle_click(self, pos: tuple[int, int]) -> bool:
        """Procesa un clic dentro del modal. Devuelve True si consumió el evento."""
        if not self.visible:
            return False
        if self.close_rect and self.close_rect.collidepoint(pos):
            self.visible = False
            return True
        for rect, i in self.tab_rects:
            if rect.collidepoint(pos):
                self.index = i
                return True
        return True  # modal: absorbe todos los clics mientras está abierto

    def draw(self, screen: pygame.Surface, fonts: dict, width: int, height: int) -> None:
        if not self.visible:
            return
        f_title = fonts["title"]
        f_sec = fonts["section"]
        f_body = fonts["body"]
        f_mono = fonts["mono"]
        f_tiny = fonts["tiny"]

        # Fondo oscurecido (scrim)
        scrim = pygame.Surface((width, height), pygame.SRCALPHA)
        scrim.fill((0, 0, 0, 150))
        screen.blit(scrim, (0, 0))

        w = min(780, width - 80)
        h = min(600, height - 80)
        modal = pygame.Rect(0, 0, w, h)
        modal.center = (width // 2, height // 2)
        glass_panel(screen, modal, radius=18, alpha=248, accent=ACCENT_CYAN)

        leccion = self.modulo.obtener_informacion(self.ids[self.index])
        pad = 24
        x = modal.x + pad
        content_w = modal.width - 2 * pad
        y = modal.y + 18

        # Encabezado
        header = f_tiny.render("DIDÁCTICA NUMÉRICA", True, ACCENT_CYAN)
        screen.blit(header, (x, y))
        # Botón cerrar
        self.close_rect = pygame.Rect(modal.right - 40, modal.y + 14, 26, 26)
        pygame.draw.rect(screen, (48, 40, 46), self.close_rect, border_radius=8)
        cx = f_sec.render("X", True, (230, 160, 160))
        screen.blit(cx, cx.get_rect(center=self.close_rect.center))
        y += 22
        screen.blit(f_title.render(leccion.nombre, True, TEXT_COLOR), (x, y))
        y += 30
        screen.blit(f_tiny.render(leccion.unidad, True, TEXT_DIM), (x, y))
        y += 26

        # Pestañas de método
        self.tab_rects = []
        tx = x
        for i, mid in enumerate(self.ids):
            label = self.SHORT.get(mid, mid)
            tw = f_tiny.size(label)[0] + 24
            tab = pygame.Rect(tx, y, tw, 26)
            active = (i == self.index)
            pygame.draw.rect(screen, ACCENT if active else (36, 42, 54), tab, border_radius=8)
            pygame.draw.rect(screen, ACCENT if active else HAIRLINE, tab, width=1, border_radius=8)
            ts = f_tiny.render(label, True, (255, 255, 255) if active else TEXT_DIM)
            screen.blit(ts, ts.get_rect(center=tab.center))
            self.tab_rects.append((tab, i))
            tx += tw + 8
        y += 40

        # Caja de fórmula
        formula = latex_to_display(leccion.formula_latex)
        fbox = pygame.Rect(x, y, content_w, 46)
        pygame.draw.rect(screen, (18, 26, 32), fbox, border_radius=10)
        pygame.draw.rect(screen, (40, 70, 80), fbox, width=1, border_radius=10)
        flabel = f_tiny.render("FÓRMULA", True, ACCENT_CYAN)
        screen.blit(flabel, (fbox.x + 12, fbox.y + 6))
        fsurf = f_mono.render(formula, True, (210, 230, 240))
        if fsurf.get_width() > content_w - 24:  # reescalar si no cabe
            scale = (content_w - 24) / fsurf.get_width()
            fsurf = pygame.transform.smoothscale(
                fsurf, (int(fsurf.get_width() * scale), int(fsurf.get_height() * scale)))
        screen.blit(fsurf, (fbox.x + 12, fbox.y + 22))
        y += 58

        def section(title: str, text: str, y0: int, color: tuple) -> int:
            screen.blit(f_sec.render(title, True, color), (x, y0))
            y0 += 22
            for line in wrap_text(text, f_body, content_w):
                screen.blit(f_body.render(line, True, (206, 214, 226)), (x, y0))
                y0 += 20
            return y0 + 8

        y = section("OBJETIVO EN EL SIMULADOR", leccion.objetivo, y, SUCCESS_COLOR)
        y = section("JUSTIFICACIÓN ACADÉMICA", leccion.justificacion, y, WARN_COLOR)

        # Paso a paso
        screen.blit(f_sec.render("PASO A PASO", True, ACCENT_PURPLE), (x, y))
        y += 22
        for paso in leccion.pasos:
            for k, line in enumerate(wrap_text(paso, f_body, content_w - 12)):
                screen.blit(f_body.render(line, True, (206, 214, 226)), (x + (0 if k == 0 else 14), y))
                y += 19
            y += 2

        hint = f_tiny.render("← → cambiar método   ·   H / ESC cerrar", True, TEXT_FAINT)
        screen.blit(hint, (modal.centerx - hint.get_width() // 2, modal.bottom - 24))


class SimpleButton:
    """Botón moderno con degradado, hover glow y estado presionado."""

    def __init__(self, x: float, y: float, width: float, height: float, text: str,
                 accent: tuple = ACCENT, icon: str = "") -> None:
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.icon = icon
        self.accent = accent
        self.hovered = False
        self.active = False
        self._t = 0.0  # animación hover 0..1

    def draw(self, screen: pygame.Surface, font: pygame.font.Font) -> None:
        target = 1.0 if self.hovered else 0.0
        self._t += (target - self._t) * 0.25
        r = self.rect

        # Sombra
        shadow = pygame.Surface((r.width + 16, r.height + 16), pygame.SRCALPHA)
        pygame.draw.rect(shadow, (0, 0, 0, 90), shadow.get_rect(), border_radius=14)
        screen.blit(shadow, (r.x - 8, r.y - 4))

        # Glow al hacer hover
        if self._t > 0.02:
            glow = pygame.Surface((r.width + 30, r.height + 30), pygame.SRCALPHA)
            pygame.draw.rect(glow, (*self.accent, int(70 * self._t)),
                             glow.get_rect(), border_radius=18)
            screen.blit(glow, (r.x - 15, r.y - 15), special_flags=pygame.BLEND_RGBA_ADD)

        # Cuerpo con degradado
        top = tuple(min(255, int(c + 28 + 22 * self._t)) for c in self.accent)
        bottom = tuple(max(0, int(c - 30)) for c in self.accent)
        if self.active:
            top, bottom = bottom, tuple(max(0, c - 20) for c in bottom)
        grad = vertical_gradient(r.width, r.height, top, bottom)
        mask = pygame.Surface((r.width, r.height), pygame.SRCALPHA)
        pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(), border_radius=12)
        body = grad.copy()
        body.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        screen.blit(body, r.topleft)

        # Brillo superior
        gloss = pygame.Surface((r.width - 6, r.height // 2), pygame.SRCALPHA)
        pygame.draw.rect(gloss, (255, 255, 255, 30), gloss.get_rect(),
                         border_top_left_radius=12, border_top_right_radius=12)
        screen.blit(gloss, (r.x + 3, r.y + 2))
        pygame.draw.rect(screen, (255, 255, 255, 40), r, width=1, border_radius=12)

        label = f"{self.icon}  {self.text}" if self.icon else self.text
        text_surf = font.render(label, True, (255, 255, 255))
        screen.blit(text_surf, text_surf.get_rect(center=r.center))

    def update(self, mouse_pos: tuple[float, float]) -> None:
        self.hovered = self.rect.collidepoint(mouse_pos)

    def is_clicked(self, mouse_pos: tuple[float, float], mouse_pressed: bool) -> bool:
        return self.hovered and mouse_pressed

    def reposition(self, x: float, y: float, width: float = None, height: float = None) -> None:
        self.rect.x = x
        self.rect.y = y
        if width is not None:
            self.rect.width = width
        if height is not None:
            self.rect.height = height


class SimpleSlider:
    """Slider moderno: pista redondeada, relleno de acento y handle con glow."""

    def __init__(self, x: float, y: float, width: float, min_val: float, max_val: float,
                 initial: float, label: str, accent: tuple = ACCENT) -> None:
        self.rect = pygame.Rect(x, y, width, 26)
        self.min_val = min_val
        self.max_val = max_val
        self.value = initial
        self.label = label
        self.accent = accent
        self.dragging = False

    def _handle_x(self) -> float:
        normalized = (self.value - self.min_val) / (self.max_val - self.min_val)
        return self.rect.x + normalized * self.rect.width

    def draw(self, screen: pygame.Surface, font: pygame.font.Font) -> None:
        cy = self.rect.y + self.rect.height // 2

        # Etiqueta + valor
        label_surf = font.render(self.label.upper(), True, TEXT_DIM)
        screen.blit(label_surf, (self.rect.x, self.rect.y - 20))
        val_surf = font.render(f"{self.value:.0f}s", True, self.accent)
        screen.blit(val_surf, (self.rect.right - val_surf.get_width(), self.rect.y - 20))

        # Pista base
        track = pygame.Rect(self.rect.x, cy - 3, self.rect.width, 6)
        pygame.draw.rect(screen, (46, 52, 64), track, border_radius=3)

        # Relleno
        handle_x = self._handle_x()
        fill_w = max(0, int(handle_x - self.rect.x))
        if fill_w > 0:
            fill = pygame.Rect(self.rect.x, cy - 3, fill_w, 6)
            pygame.draw.rect(screen, self.accent, fill, border_radius=3)

        # Handle con glow
        draw_glow(screen, (handle_x, cy), 16, self.accent, layers=5, max_alpha=70)
        pygame.draw.circle(screen, (245, 248, 252), (int(handle_x), cy), 9)
        pygame.draw.circle(screen, self.accent, (int(handle_x), cy), 9, 3)

    def update(self, mouse_pos: tuple[float, float], mouse_pressed: bool) -> None:
        hit = pygame.Rect(self.rect.x - 6, self.rect.y - 6,
                          self.rect.width + 12, self.rect.height + 12)
        if mouse_pressed and hit.collidepoint(mouse_pos):
            self.dragging = True
        elif not mouse_pressed:
            self.dragging = False

        if self.dragging:
            normalized = (mouse_pos[0] - self.rect.x) / self.rect.width
            normalized = max(0.0, min(1.0, normalized))
            self.value = self.min_val + normalized * (self.max_val - self.min_val)

    def reposition(self, x: float, y: float, width: float) -> None:
        self.rect.x = x
        self.rect.y = y
        self.rect.width = width


class TrafficSimulationFrontend:
    """Frontend interactivo, responsive y moderno con panel de control y métricas."""

    @staticmethod
    def _fit_to_desktop(width: int, height: int) -> tuple[int, int]:
        """Reduce el tamaño solicitado para que quepa en el escritorio (deja margen).

        Evita que la ventana inicial sea más grande que la pantalla en laptops chicas.
        """
        try:
            desktop = pygame.display.get_desktop_sizes()[0]
            dw, dh = int(desktop[0]), int(desktop[1])
        except Exception:  # noqa: BLE001
            info = pygame.display.Info()
            dw, dh = info.current_w, info.current_h
        if dw > 0 and dh > 0:
            width = min(width, int(dw * 0.92))
            height = min(height, int(dh * 0.90))
        # No bajar del mínimo salvo que la propia pantalla sea más pequeña
        width = max(min(MIN_WIDTH, dw or MIN_WIDTH), width) if width < MIN_WIDTH else width
        height = max(min(MIN_HEIGHT, dh or MIN_HEIGHT), height) if height < MIN_HEIGHT else height
        return width, height

    def __init__(self, width: int = INITIAL_WIDTH, height: int = INITIAL_HEIGHT) -> None:
        pygame.init()
        width, height = self._fit_to_desktop(width, height)
        self.screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
        pygame.display.set_caption("Smart Intersection · Simulador de Tráfico 2D")
        self.clock = pygame.time.Clock()
        self.font_tiny = make_font(14)
        self.font_small = make_font(16)
        self.font_mono = pygame.font.SysFont("Consolas,DejaVu Sans Mono,monospace", 14)
        self.font_medium = make_font(19)
        self.font_semibold = make_font(17, bold=True)
        self.font_large = make_font(26, bold=True)
        self.font_metric = make_font(24, bold=True)

        self.width = width
        self.height = height
        self.engine = TrafficSimulationEngine(h=0.016)
        self.sustainability_analyzer = SustainabilityAnalyzer(co2_idle_rate=0.12)

        self.discrete_counts = [0, 0, 0, 0]
        self.spawn_timers = [0.0, 0.0, 0.0, 0.0]
        # Demanda ambiental ASIMÉTRICA (arteria vs calle secundaria), aleatoria por
        # sesión. Un eje es "arteria" (alta) y el otro "secundaria" (baja) → la demanda
        # está naturalmente desbalanceada, por lo que la optimización SÍ reduce CO2.
        self.spawn_probabilities = self._make_traffic_pattern()
        self.spawn_probability = max(self.spawn_probabilities)  # para el gate del timer

        # Vehículos animados por aproximación. Cada auto es {'p': posición sobre el
        # eje de viaje, negativa = acercándose, positiva = ya cruzó}.
        self.vehicles: list[list[dict]] = [[], [], [], []]
        self.pending_spawns = [0, 0, 0, 0]
        self.proj_timer = 0.0  # temporizador para refrescar la proyección de emisiones
        # Muestras (t, conteos) para medir la demanda como TASA reciente (ventana móvil)
        self.count_samples: list[tuple[float, tuple[int, ...]]] = []
        self.DEMAND_WINDOW = 8.0  # s

        self.green_time_ns = 25.0
        self.green_time_ew = 25.0
        self.red_time = 5.0
        self.traffic_light_timer = 0.0
        self.light_state = "green_ns"

        # Crear elementos UI
        self.optimize_button = SimpleButton(0, 0, 180, 44, "Optimizar", ACCENT)
        self.export_button = SimpleButton(0, 0, 180, 44, "Exportar Excel", SUCCESS_COLOR)
        self.help_button = SimpleButton(0, 0, 180, 40, "? Ayuda didáctica", ACCENT_PURPLE)

        # Capa de Didáctica Numérica (consume ModuloExplicativo)
        self.modulo_explicativo = ModuloExplicativo()
        self.help_overlay = HelpOverlay(self.modulo_explicativo)
        self.green_ns_slider = SimpleSlider(0, 0, 200, 5.0, 60.0, 25.0, "Verde N-S", ACCENT)
        self.green_ew_slider = SimpleSlider(0, 0, 200, 5.0, 60.0, 25.0, "Verde E-O", ACCENT_CYAN)

        self.newton_iterations = 0
        self.newton_converged = False
        self.last_optimization_time = 0.0
        self.baseline_set = False

        # Toast de estado
        self.status_message = ""
        self.status_timer = 0.0
        self.status_color = SUCCESS_COLOR

        # Comparativa "antes/después" (momento pedagógico tras optimizar).
        # dict con base_co2, opt_co2, base_ns/ew, opt_ns/ew, pct, timer.
        self.comparison = None

        # Música de fondo (Tetris / Korobeiniki sintetizada). Falla en silencio si no
        # hay dispositivo de audio (p. ej. headless).
        self.music = None
        self.music_on = False
        try:
            if pygame.mixer.get_init() is None:
                pygame.mixer.init()
            from music import make_tetris_sound
            self.music = make_tetris_sound()
            self.music.play(loops=-1)
            self.music_on = True
        except Exception as exc:  # noqa: BLE001
            print(f"[WARN] Audio no disponible, sin música: {exc}")

        self.running = True
        self.update_layout()

    def update_layout(self) -> None:
        """Recalcula el layout de los elementos según el tamaño de la ventana."""
        self.margin = 12 if self.width < 1200 else 16
        # Paneles laterales escalables (más angostos en ventanas chicas)
        self.left_panel_width = int(min(268, max(210, self.width * 0.19)))
        self.right_panel_width = int(min(316, max(250, self.width * 0.22)))
        self.left_panel_rect = pygame.Rect(
            self.margin, self.margin, self.left_panel_width, self.height - 2 * self.margin)
        self.right_panel_rect = pygame.Rect(
            self.width - self.right_panel_width - self.margin, self.margin,
            self.right_panel_width, self.height - 2 * self.margin)

        self.center_start_x = self.left_panel_rect.right + self.margin
        self.center_width = max(
            320, self.right_panel_rect.left - self.center_start_x - self.margin)

        # Botones
        button_x = self.left_panel_rect.x + 20
        button_width = self.left_panel_width - 40
        self.optimize_button.reposition(button_x, self.left_panel_rect.y + 70, button_width, 44)
        self.export_button.reposition(button_x, self.left_panel_rect.y + 124, button_width, 44)
        self.help_button.reposition(button_x, self.left_panel_rect.y + 178, button_width, 40)

        # Sliders
        self.green_ns_slider.reposition(button_x, self.left_panel_rect.y + 268, button_width)
        self.green_ew_slider.reposition(button_x, self.left_panel_rect.y + 336, button_width)

    def _make_traffic_pattern(self) -> list[float]:
        """Genera un patrón de demanda asimétrico realista (arteria vs secundaria).

        Elige al azar qué eje es la arteria (alta demanda) y cuál la calle secundaria
        (baja), con jitter por carril. Así la demanda ambiental está desbalanceada y la
        optimización de semáforos produce una reducción de CO2 no trivial.
        """
        hi = random.uniform(0.22, 0.34)   # arteria
        lo = random.uniform(0.05, 0.12)   # secundaria
        jitter = lambda p: max(0.03, p * random.uniform(0.8, 1.2))
        if random.random() < 0.5:         # N-S arteria
            return [jitter(hi), jitter(lo), jitter(hi), jitter(lo)]
        return [jitter(lo), jitter(hi), jitter(lo), jitter(hi)]  # E-O arteria

    def spawn_vehicles(self, dt: float) -> None:
        """Genera vehículos aleatoriamente en las entradas (tasa por carril)."""
        for i in range(4):
            prob = self.spawn_probabilities[i]
            self.spawn_timers[i] += dt
            if self.spawn_timers[i] > (1.0 / max(0.1, prob)):
                if random.random() < prob:
                    self.discrete_counts[i] += 1
                    self.pending_spawns[i] += 1
                    self.spawn_timers[i] = 0.0

    def _lane_pmax(self, idx: int) -> float:
        """Distancia (px) desde el centro hasta el borde de salida de la vía."""
        if idx in (0, 2):  # ejes verticales (N-S / S-N)
            return self.height / 2 - self.margin + 24
        return self.center_width / 2 + 24  # ejes horizontales (E-O / O-E)

    def _lane_to_screen(self, idx: int, cx: float, cy: float, p: float) -> tuple[float, float]:
        """Convierte la posición de eje 'p' a coordenadas de pantalla."""
        if idx == 0:      # N-S: entra arriba, baja
            return cx - LANE_OFFSET, cy + p
        elif idx == 2:    # S-N: entra abajo, sube
            return cx + LANE_OFFSET, cy - p
        elif idx == 1:    # E-O: entra izquierda, va a la derecha
            return cx + p, cy + LANE_OFFSET
        else:             # O-E: entra derecha, va a la izquierda
            return cx - p, cy - LANE_OFFSET

    def _lane_lead(self, idx: int) -> tuple[int, int]:
        """Vector de avance (para orientar faros)."""
        return {0: (0, 1), 2: (0, -1), 1: (1, 0), 3: (-1, 0)}[idx]

    def _entrance_free(self, idx: int) -> bool:
        """True si hay espacio en la boca de entrada para un nuevo auto."""
        start = -self._lane_pmax(idx)
        cars = self.vehicles[idx]
        if not cars:
            return True
        rear = min(c["p"] for c in cars)
        return rear > start + VEHICLE_GAP

    def update_vehicles(self, dt: float) -> None:
        """Mueve los autos: avanzan, frenan tras el de adelante o en el semáforo rojo."""
        # Drenar spawns pendientes cuando la entrada está libre
        for idx in range(4):
            if self.pending_spawns[idx] > 0 and self._entrance_free(idx):
                self.vehicles[idx].append({"p": -self._lane_pmax(idx)})
                self.pending_spawns[idx] -= 1

        stop_line = -(ROAD_WIDTH // 2 + 12)
        for idx in range(4):
            green = (self.light_state == "green_ns" if idx in (0, 2)
                     else self.light_state == "green_ew")
            pmax = self._lane_pmax(idx)
            cars = self.vehicles[idx]
            cars.sort(key=lambda c: c["p"], reverse=True)  # frente primero

            for i, car in enumerate(cars):
                desired = car["p"] + VEHICLE_SPEED * dt
                # Frenar en la línea de pare si el semáforo está rojo (solo si aún no cruzó)
                if not green and car["p"] <= stop_line:
                    desired = min(desired, stop_line)
                # Car-following: no invadir al auto de adelante
                if i > 0:
                    desired = min(desired, cars[i - 1]["p"] - VEHICLE_GAP)
                car["p"] = desired

            # Despawn de los que ya salieron del área
            self.vehicles[idx] = [c for c in cars if c["p"] <= pmax]

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

    def measure_demand(self) -> tuple[float, float]:
        """Estima la tasa de llegada (veh/s) por eje sobre una VENTANA móvil reciente.

        lambda_eje = (conteo_ahora − conteo_hace_W_segundos) / W. Al usar una ventana
        (no el acumulado total), la demanda refleja el tráfico reciente y no se dispara
        por ráfagas de teclas antiguas. Preserva el desbalance N-S vs E-O.
        """
        now = self.engine.current_time
        # Buscar la muestra más antigua dentro de la ventana
        oldest = None
        for t, counts in self.count_samples:
            if now - t <= self.DEMAND_WINDOW:
                oldest = (t, counts)
                break
        if oldest is None or now - oldest[0] < 0.5:
            # Sin ventana suficiente: cae a la tasa media desde el inicio
            elapsed = max(1.0, now)
            lambda_ns = (self.discrete_counts[0] + self.discrete_counts[2]) / elapsed
            lambda_ew = (self.discrete_counts[1] + self.discrete_counts[3]) / elapsed
            return lambda_ns, lambda_ew
        t0, c0 = oldest
        span = now - t0
        lambda_ns = ((self.discrete_counts[0] - c0[0]) + (self.discrete_counts[2] - c0[2])) / span
        lambda_ew = ((self.discrete_counts[1] - c0[1]) + (self.discrete_counts[3] - c0[3])) / span
        return max(0.0, lambda_ns), max(0.0, lambda_ew)

    def refresh_projection(self) -> None:
        """Recalcula la proyección del plan ACTUAL (fuente única de CO2/retraso).

        Usa la demanda medida y los tiempos de verde vigentes; corre Heun + Simpson vía
        engine.project_emissions. Mantiene coherentes el número mostrado y la reducción.
        """
        lambda_ns, lambda_ew = self.measure_demand()
        proj = self.engine.project_emissions(
            self.green_time_ns, self.green_time_ew, lambda_ns, lambda_ew, self.red_time)
        self.sustainability_analyzer.set_current(proj, (lambda_ns, lambda_ew))

    def optimize_traffic_signals(self) -> None:
        """Optimiza el reparto de verde acoplando las 3 unidades numéricas.

        1. Unidad III: mide la demanda (lambda) por eje desde los sensores.
        2. Unidad I: Newton-Raphson resuelve el reparto de verde que iguala saturación.
        3. Unidad IV: Heun proyecta emisiones del plan manual vs. optimizado → reducción.
        """
        lambda_ns, lambda_ew = self.measure_demand()
        if lambda_ns <= 1e-9 and lambda_ew <= 1e-9:
            self.set_status("Sin demanda medida — spawnea tráfico antes de optimizar", WARN_COLOR)
            return

        g_total = self.green_time_ns + self.green_time_ew

        # Línea base = sincronización MANUAL ingenua (reparto equitativo del mismo
        # presupuesto de verde). Es la referencia justa contra la que se mide Newton.
        base = self.engine.project_emissions(
            g_total / 2.0, g_total / 2.0, lambda_ns, lambda_ew, self.red_time)

        # Newton-Raphson: reparto de verde óptimo dado el flujo medido
        result = self.engine.solve_green_split(lambda_ns, lambda_ew, g_total)
        self.newton_converged = bool(result["converged"])
        self.newton_iterations = int(result["iterations"])
        sol = result["solution"]
        opt_ns = float(max(5.0, min(60.0, sol[0])))
        opt_ew = float(max(5.0, min(60.0, sol[1])))

        # Proyección del plan OPTIMIZADO — mismo horizonte y llegadas
        opt = self.engine.project_emissions(
            opt_ns, opt_ew, lambda_ns, lambda_ew, self.red_time)

        # Aplicar tiempos y registrar comparación proyectada (misma fuente que el KPI)
        self.green_time_ns = opt_ns
        self.green_time_ew = opt_ew
        self.green_ns_slider.value = opt_ns
        self.green_ew_slider.value = opt_ew
        self.sustainability_analyzer.set_baseline(base["co2"])
        self.sustainability_analyzer.set_optimized(opt["co2"])
        self.sustainability_analyzer.set_current(opt, (lambda_ns, lambda_ew))

        pct = (base["co2"] - opt["co2"]) / base["co2"] * 100 if base["co2"] > 1e-9 else 0.0
        self.set_status(
            f"Optimizado  NS={opt_ns:.0f}s  EO={opt_ew:.0f}s  ·  -{pct:.1f}% CO2",
            SUCCESS_COLOR)

        # Comparativa visual antes/después — el "ajá" pedagógico
        self.comparison = {
            "base_co2": base["co2"], "opt_co2": opt["co2"],
            "base_ns": g_total / 2.0, "base_ew": g_total / 2.0,
            "opt_ns": opt_ns, "opt_ew": opt_ew,
            "pct": pct, "timer": 8.0,
        }

    # ------------------------------------------------------------------
    # Helpers de dibujo
    # ------------------------------------------------------------------
    def _draw_background(self) -> None:
        self.screen.blit(vertical_gradient(self.width, self.height, BG_TOP, BG_BOTTOM), (0, 0))
        # Rejilla sutil de puntos
        dot = (28, 33, 44)
        for y in range(40, self.height, 44):
            for x in range(40, self.width, 44):
                self.screen.set_at((x, y), dot)

    def _section_label(self, text: str, x: int, y: int, color: tuple = TEXT_FAINT) -> None:
        surf = self.font_tiny.render(text.upper(), True, color)
        self.screen.blit(surf, (x, y))

    def draw_left_panel(self) -> None:
        """Panel de control izquierdo (glass)."""
        r = self.left_panel_rect
        glass_panel(self.screen, r, radius=18)

        title = self.font_large.render("CONTROL", True, TEXT_COLOR)
        self.screen.blit(title, (r.x + 20, r.y + 20))
        sub = self.font_tiny.render("INTERSECCIÓN INTELIGENTE", True, ACCENT)
        self.screen.blit(sub, (r.x + 22, r.y + 50))

        self.optimize_button.draw(self.screen, self.font_semibold)
        self.export_button.draw(self.screen, self.font_semibold)
        self.help_button.draw(self.screen, self.font_semibold)

        self._section_label("Tiempos de verde", r.x + 20, r.y + 240, TEXT_DIM)
        self.green_ns_slider.draw(self.screen, self.font_tiny)
        self.green_ew_slider.draw(self.screen, self.font_tiny)

        # Chips de atajos
        self._section_label("Atajos", r.x + 20, r.y + 384, TEXT_DIM)
        shortcuts = [
            ("1-4", "Spawnear"), ("O", "Optimizar"), ("E", "Exportar Excel"),
            ("H", "Ayuda"), ("M", "Música"), ("R", "Reset"), ("ESC", "Salir"),
        ]
        y = r.y + 406
        for key, desc in shortcuts:
            kw = self.font_tiny.size(key)[0] + 14
            chip = pygame.Rect(r.x + 20, y, kw, 20)
            pygame.draw.rect(self.screen, (36, 42, 54), chip, border_radius=6)
            pygame.draw.rect(self.screen, HAIRLINE, chip, width=1, border_radius=6)
            ks = self.font_tiny.render(key, True, ACCENT_CYAN)
            self.screen.blit(ks, ks.get_rect(center=chip.center))
            ds = self.font_tiny.render(desc, True, TEXT_DIM)
            self.screen.blit(ds, (chip.right + 10, y + 3))
            y += 26

    def _metric_row(self, x: int, y: int, w: int, label: str, value: str,
                    color: tuple = TEXT_COLOR, mono: bool = True) -> None:
        ls = self.font_tiny.render(label, True, TEXT_DIM)
        self.screen.blit(ls, (x, y))
        font = self.font_mono if mono else self.font_small
        vs = font.render(value, True, color)
        self.screen.blit(vs, (x + w - vs.get_width(), y - 1))

    def draw_right_panel(self) -> None:
        """Panel de métricas derecho (glass) con tarjetas."""
        r = self.right_panel_rect
        glass_panel(self.screen, r, radius=18)
        inner_x = r.x + 20
        inner_w = r.width - 40

        title = self.font_large.render("MÉTRICAS", True, TEXT_COLOR)
        self.screen.blit(title, (inner_x, r.y + 20))

        # Integración por Simpson 1/3 (reutilizada en varias tarjetas)
        emissions = self.sustainability_analyzer.calculate_total_emissions()

        y = r.y + 66

        # --- Tarjeta: Integración numérica (Simpson 1/3) ---
        card = pygame.Rect(inner_x, y, inner_w, 62)
        pygame.draw.rect(self.screen, (30, 35, 46), card, border_radius=12)
        pygame.draw.rect(self.screen, HAIRLINE, card, width=1, border_radius=12)
        self._section_label("UNIDAD III · Integración (Simpson 1/3)", card.x + 14, card.y + 10, ACCENT_CYAN)
        area = emissions["total_veh_hours"]
        big = self.font_metric.render(f"{area:.2f}", True, TEXT_COLOR)
        self.screen.blit(big, (card.x + 14, card.y + 26))
        unit = self.font_tiny.render("∫ q(t) dt  veh-h", True, TEXT_DIM)
        self.screen.blit(unit, (card.right - unit.get_width() - 14, card.y + 38))
        y += 74

        # --- Colas por dirección (barras) ---
        self._section_label("UNIDAD IV · Colas (Heun)", inner_x, y, ACCENT_PURPLE)
        y += 20
        names = ["N-S", "E-O", "S-N", "O-E"]
        max_q = max(1.0, max(self.engine.queue_state))
        for i, q in enumerate(self.engine.queue_state):
            self.screen.blit(self.font_tiny.render(names[i], True, TEXT_DIM), (inner_x, y))
            bar_bg = pygame.Rect(inner_x + 40, y + 2, inner_w - 90, 9)
            pygame.draw.rect(self.screen, (38, 43, 54), bar_bg, border_radius=4)
            fill_w = int((q / max_q) * bar_bg.width)
            if fill_w > 0:
                pygame.draw.rect(self.screen, APPROACH_COLORS[i],
                                 (bar_bg.x, bar_bg.y, fill_w, 9), border_radius=4)
            vs = self.font_mono.render(f"{q:5.2f}", True, TEXT_COLOR)
            self.screen.blit(vs, (bar_bg.right + 8, y - 1))
            y += 22
        y += 10

        # --- Tarjeta: Newton-Raphson ---
        card = pygame.Rect(inner_x, y, inner_w, 76)
        pygame.draw.rect(self.screen, (30, 35, 46), card, border_radius=12)
        pygame.draw.rect(self.screen, HAIRLINE, card, width=1, border_radius=12)
        self._section_label("UNIDAD I · Newton-Raphson", card.x + 14, card.y + 10, ACCENT)
        if self.engine.newton_solution is not None:
            sol = self.engine.newton_solution
            self._metric_row(card.x + 14, card.y + 30, inner_w - 28, "x",
                             f"[{sol[0]:.4f}, {sol[1]:.4f}]", TEXT_COLOR)
        err = self.engine.newton_residual_norm
        err_color = SUCCESS_COLOR if err < 1e-4 else WARN_COLOR
        self._metric_row(card.x + 14, card.y + 52, inner_w - 28, "|F(X)|",
                         f"{err:.2e}", err_color)
        y += 88

        # --- Tarjeta: Sostenibilidad ---
        card = pygame.Rect(inner_x, y, inner_w, self.right_panel_rect.bottom - y - 20)
        card.height = max(100, card.height)
        pygame.draw.rect(self.screen, (28, 38, 33), card, border_radius=12)
        pygame.draw.rect(self.screen, (46, 66, 54), card, width=1, border_radius=12)
        self._section_label("Sostenibilidad Ambiental", card.x + 14, card.y + 10, SUCCESS_COLOR)
        cy = card.y + 30
        self._metric_row(card.x + 14, cy, inner_w - 28, "CO2 total",
                         f"{emissions['total_co2']:.3f} kg", TEXT_COLOR)
        cy += 22
        self._metric_row(card.x + 14, cy, inner_w - 28, "Retraso",
                         f"{emissions['total_veh_hours']:.3f} vh", TEXT_COLOR)
        cy += 22
        self._metric_row(card.x + 14, cy, inner_w - 28, "Veh. entrada",
                         f"{sum(self.discrete_counts)}", ACCENT_CYAN)
        cy += 26
        if (self.sustainability_analyzer.optimization_applied
                and self.sustainability_analyzer.baseline_emissions > 1e-9):
            reduction_pct = (
                (self.sustainability_analyzer.baseline_emissions
                 - self.sustainability_analyzer.optimized_emissions)
                / self.sustainability_analyzer.baseline_emissions * 100)
            color = SUCCESS_COLOR if reduction_pct > 0 else ERROR_COLOR
            rt = self.font_large.render(f"-{abs(reduction_pct):.1f}%", True, color)
            self.screen.blit(rt, (card.x + 14, cy))
            self.screen.blit(self.font_tiny.render("reducción de", True, TEXT_DIM),
                             (card.x + 20 + rt.get_width(), cy + 2))
            self.screen.blit(self.font_tiny.render("contaminación", True, TEXT_DIM),
                             (card.x + 20 + rt.get_width(), cy + 16))

    def draw_intersection(self) -> None:
        """Dibuja la intersección vial moderna en el área central."""
        cx = self.center_start_x + self.center_width // 2
        cy = self.height // 2
        vis_rect = pygame.Rect(self.center_start_x, self.margin,
                               self.center_width, self.height - 2 * self.margin)

        # Panel base de la escena
        glass_panel(self.screen, vis_rect, radius=18, fill=(12, 15, 21), alpha=255)
        self.screen.set_clip(vis_rect.inflate(-2, -2))

        half = ROAD_WIDTH // 2
        # Asfalto horizontal y vertical con degradado
        h_road = vertical_gradient(vis_rect.width, ROAD_WIDTH, ROAD_TOP, ROAD_BOTTOM)
        self.screen.blit(h_road, (vis_rect.x, cy - half))
        v_road = vertical_gradient(ROAD_WIDTH, vis_rect.height, ROAD_TOP, ROAD_BOTTOM)
        self.screen.blit(v_road, (cx - half, vis_rect.y))

        # Bordes de carril (líneas continuas)
        for edge in (cy - half, cy + half):
            pygame.draw.line(self.screen, (70, 76, 88), (vis_rect.x, edge), (vis_rect.right, edge), 2)
        for edge in (cx - half, cx + half):
            pygame.draw.line(self.screen, (70, 76, 88), (edge, vis_rect.y), (edge, vis_rect.bottom), 2)

        # Líneas divisorias centrales discontinuas (evitando el cruce)
        for x in range(vis_rect.x, vis_rect.right, 46):
            if x < cx - half - 10 or x > cx + half:
                pygame.draw.rect(self.screen, LANE_COLOR, (x, cy - 2, 24, 4), border_radius=2)
        for y in range(vis_rect.y, vis_rect.bottom, 46):
            if y < cy - half - 10 or y > cy + half:
                pygame.draw.rect(self.screen, LANE_COLOR, (cx - 2, y, 4, 24), border_radius=2)

        # Cruces peatonales (stripes) en las 4 bocas
        stripe = (150, 158, 172)
        for i in range(-half + 8, half - 6, 14):
            pygame.draw.rect(self.screen, stripe, (cx + i, cy - half - 22, 8, 16), border_radius=2)
            pygame.draw.rect(self.screen, stripe, (cx + i, cy + half + 6, 8, 16), border_radius=2)
            pygame.draw.rect(self.screen, stripe, (cx - half - 22, cy + i, 16, 8), border_radius=2)
            pygame.draw.rect(self.screen, stripe, (cx + half + 6, cy + i, 16, 8), border_radius=2)

        # Núcleo central con glow
        draw_glow(self.screen, (cx, cy), 70, CENTER_COLOR, layers=6, max_alpha=45)
        core = pygame.Rect(cx - 34, cy - 34, 68, 68)
        pygame.draw.rect(self.screen, CENTER_COLOR, core, border_radius=14)
        pygame.draw.rect(self.screen, (255, 226, 150), core, width=2, border_radius=14)
        pygame.draw.circle(self.screen, (60, 45, 10), core.center, 9, 3)

        self.screen.set_clip(None)

        # Título flotante de la escena
        scene_title = self.font_semibold.render("SMART INTERSECTION", True, TEXT_DIM)
        self.screen.blit(scene_title, (vis_rect.x + 20, vis_rect.y + 16))
        light_lbl = "N-S VERDE" if self.light_state.startswith("green_ns") or self.light_state == "red_ew" else "E-O VERDE"
        # fase activa
        phase = "N-S" if self.light_state in ("green_ns",) else ("E-O" if self.light_state == "green_ew" else "TRANSICIÓN")
        pc = SUCCESS_COLOR if self.light_state.startswith("green") else WARN_COLOR
        ps = self.font_tiny.render(f"FASE: {phase}", True, pc)
        self.screen.blit(ps, (vis_rect.right - ps.get_width() - 20, vis_rect.y + 18))

    def draw_traffic_lights(self) -> None:
        """Dibuja los semáforos modernos con housing y glow."""
        cx = self.center_start_x + self.center_width // 2
        cy = self.height // 2
        pulse = 0.5 + 0.5 * math.sin(pygame.time.get_ticks() * 0.006)

        light_positions = [
            (cx + 92, cy - 96),
            (cx - 96, cy - 92),
            (cx - 92, cy + 96),
            (cx + 96, cy + 92),
        ]

        for idx, (x, y) in enumerate(light_positions):
            if idx in (0, 2):
                is_green = self.light_state in ("green_ns", "yellow_ns")
            else:
                is_green = self.light_state in ("green_ew", "yellow_ew")

            color = TRAFFIC_LIGHT_GREEN if is_green else TRAFFIC_LIGHT_RED

            # Housing
            housing = pygame.Rect(0, 0, 26, 26)
            housing.center = (int(x), int(y))
            pygame.draw.rect(self.screen, (18, 20, 26), housing, border_radius=8)
            pygame.draw.rect(self.screen, (60, 66, 78), housing, width=1, border_radius=8)

            # Lámpara con glow pulsante
            glow_r = 20 + int(6 * pulse)
            draw_glow(self.screen, (x, y), glow_r, color, layers=6, max_alpha=110)
            pygame.draw.circle(self.screen, color, (int(x), int(y)), 9)
            pygame.draw.circle(self.screen, (255, 255, 255), (int(x - 2), int(y - 2)), 2)

    def _draw_vehicle(self, cx: float, cy: float, horizontal: bool, color: tuple,
                      lead: tuple) -> None:
        """Dibuja un vehículo estilizado (rounded, gradient, faros)."""
        if horizontal:
            w, h = 28, 17
        else:
            w, h = 17, 28
        rect = pygame.Rect(0, 0, w, h)
        rect.center = (int(cx), int(cy))

        # Sombra
        shadow = pygame.Surface((w + 6, h + 6), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 90), shadow.get_rect())
        self.screen.blit(shadow, (rect.x - 3, rect.y + 2))

        # Cuerpo con degradado
        top = tuple(min(255, c + 45) for c in color)
        bottom = tuple(max(0, c - 35) for c in color)
        grad = vertical_gradient(w, h, top, bottom)
        mask = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(), border_radius=5)
        body = grad.copy()
        body.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        self.screen.blit(body, rect.topleft)
        pygame.draw.rect(self.screen, (255, 255, 255, 60), rect, width=1, border_radius=5)

        # Parabrisas (franja translúcida)
        if horizontal:
            wind = pygame.Rect(rect.centerx - 3, rect.y + 3, 6, h - 6)
        else:
            wind = pygame.Rect(rect.x + 3, rect.centery - 3, w - 6, 6)
        ws = pygame.Surface((wind.width, wind.height), pygame.SRCALPHA)
        pygame.draw.rect(ws, (200, 230, 255, 90), ws.get_rect(), border_radius=3)
        self.screen.blit(ws, wind.topleft)

        # Faros en el borde delantero (hacia el centro)
        ldx, ldy = lead
        fx = rect.centerx + ldx * (w // 2 - 2)
        fy = rect.centery + ldy * (h // 2 - 2)
        if horizontal:
            offsets = [(0, -4), (0, 4)]
        else:
            offsets = [(-4, 0), (4, 0)]
        for ox, oy in offsets:
            pygame.draw.circle(self.screen, (255, 240, 190), (int(fx + ox), int(fy + oy)), 2)

    def draw_vehicle_queues(self) -> None:
        """Dibuja los vehículos animados en sus posiciones actuales."""
        cx = self.center_start_x + self.center_width // 2
        cy = self.height // 2
        vis_rect = pygame.Rect(self.center_start_x, self.margin,
                               self.center_width, self.height - 2 * self.margin)
        self.screen.set_clip(vis_rect.inflate(-2, -2))

        for idx, cars in enumerate(self.vehicles):
            horizontal = idx in (1, 3)
            lead = self._lane_lead(idx)
            for car in cars:
                x, y = self._lane_to_screen(idx, cx, cy, car["p"])
                self._draw_vehicle(x, y, horizontal, APPROACH_COLORS[idx], lead)
        self.screen.set_clip(None)

    def handle_events(self) -> None:
        """Maneja eventos de entrada del usuario."""
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()[0]

        self.optimize_button.update(mouse_pos)
        self.export_button.update(mouse_pos)
        self.help_button.update(mouse_pos)
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
            # --- Modal de ayuda: intercepta eventos mientras está visible ---
            elif self.help_overlay.visible and event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_h):
                    self.help_overlay.visible = False
                elif event.key in (pygame.K_RIGHT, pygame.K_DOWN):
                    self.help_overlay.next()
                elif event.key in (pygame.K_LEFT, pygame.K_UP):
                    self.help_overlay.prev()
            elif self.help_overlay.visible and event.type == pygame.MOUSEBUTTONDOWN:
                self.help_overlay.handle_click(mouse_pos)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_h:
                    self.help_overlay.toggle()
                elif event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4):
                    lane = event.key - pygame.K_1
                    self.discrete_counts[lane] += 2
                    self.pending_spawns[lane] += 2
                elif event.key == pygame.K_r:
                    self.discrete_counts = [0, 0, 0, 0]
                    self.engine = TrafficSimulationEngine(h=0.016)
                    self.sustainability_analyzer.reset()
                    self.vehicles = [[], [], [], []]
                    self.pending_spawns = [0, 0, 0, 0]
                    self.spawn_timers = [0.0, 0.0, 0.0, 0.0]
                    self.count_samples = []
                    self.proj_timer = 0.0
                    self.spawn_probabilities = self._make_traffic_pattern()
                    self.spawn_probability = max(self.spawn_probabilities)
                    self.baseline_set = False
                    self.set_status("Simulación reiniciada", ACCENT_CYAN)
                elif event.key == pygame.K_o:
                    self.optimize_traffic_signals()
                elif event.key == pygame.K_e:
                    self.export_excel()
                elif event.key == pygame.K_m:
                    if self.music is not None:
                        if self.music_on:
                            self.music.stop()
                        else:
                            self.music.play(loops=-1)
                        self.music_on = not self.music_on
                        self.set_status(
                            f"Música: {'ON' if self.music_on else 'OFF'}", ACCENT_CYAN)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if self.optimize_button.is_clicked(mouse_pos, True):
                    self.optimize_traffic_signals()
                    self.optimize_button.active = True
                elif self.export_button.is_clicked(mouse_pos, True):
                    self.export_excel()
                    self.export_button.active = True
                elif self.help_button.is_clicked(mouse_pos, True):
                    self.help_overlay.toggle()
                    self.help_button.active = True
            elif event.type == pygame.MOUSEBUTTONUP:
                self.optimize_button.active = False
                self.export_button.active = False
                self.help_button.active = False

        self.green_time_ns = self.green_ns_slider.value
        self.green_time_ew = self.green_ew_slider.value

    def set_status(self, message: str, color: tuple[int, int, int] = SUCCESS_COLOR) -> None:
        """Muestra un mensaje de estado temporal en pantalla."""
        self.status_message = message
        self.status_color = color
        self.status_timer = 3.0

    def export_excel(self) -> None:
        """Exporta el reporte de sostenibilidad a un archivo Excel (.xlsx) con gráficos."""
        self.refresh_projection()  # asegura una proyección al día
        if not self.sustainability_analyzer.current:
            self.set_status("Sin datos aún — spawnea tráfico primero", WARN_COLOR)
            return
        try:
            filepath = self.sustainability_analyzer.export_to_excel()
            print(f"[INFO] Excel generado: {filepath}")
            self.set_status(f"Excel exportado: {os.path.basename(filepath)}", SUCCESS_COLOR)
        except Exception as exc:
            import traceback
            traceback.print_exc()
            self.set_status("Error al exportar Excel", ERROR_COLOR)

    def draw_status_message(self) -> None:
        """Dibuja un toast de estado temporal en la parte inferior central."""
        if self.status_timer <= 0 or not self.status_message:
            return
        alpha = min(1.0, self.status_timer / 0.6)
        text_surf = self.font_small.render(self.status_message, True, self.status_color)
        pad_x, pad_y = 18, 10
        w = text_surf.get_width() + 2 * pad_x + 16
        h = text_surf.get_height() + 2 * pad_y
        toast = pygame.Rect(0, 0, w, h)
        toast.centerx = self.center_start_x + self.center_width // 2
        toast.bottom = self.height - 30
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(surf, (18, 22, 30, int(235 * alpha)), surf.get_rect(), border_radius=12)
        pygame.draw.rect(surf, (*self.status_color, int(200 * alpha)), surf.get_rect(),
                         width=1, border_radius=12)
        surf.set_alpha(int(255 * alpha))
        self.screen.blit(surf, toast.topleft)
        pygame.draw.circle(self.screen, self.status_color,
                           (toast.x + pad_x, toast.centery), 4)
        self.screen.blit(text_surf, (toast.x + pad_x + 12, toast.y + pad_y))

    def draw_comparison_overlay(self) -> None:
        """Tarjeta flotante 'antes → después' tras optimizar (momento pedagógico).

        Compara el plan MANUAL (reparto equitativo) contra el ÓPTIMO de Newton
        mostrando dos barras de CO2 proyectado y el reparto de verde de cada plan.
        """
        c = self.comparison
        if not c or c["timer"] <= 0:
            return
        # Fade-in rápido (0.4s) y fade-out en el último 1.2s
        alpha = min(1.0, (8.0 - c["timer"]) / 0.4, c["timer"] / 1.2)
        alpha = max(0.0, alpha)

        w = int(min(self.center_width - 24, 380))
        h = 196
        card = pygame.Rect(0, 0, w, h)
        card.centerx = self.center_start_x + self.center_width // 2
        card.top = self.margin + 20

        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(surf, (16, 20, 28, int(244 * alpha)), surf.get_rect(), border_radius=16)
        pygame.draw.rect(surf, (*SUCCESS_COLOR, int(150 * alpha)), surf.get_rect(),
                         width=1, border_radius=16)

        def bl(font, text, color, x, y):
            t = font.render(text, True, color)
            t.set_alpha(int(255 * alpha))
            surf.blit(t, (x, y))

        pad = 18
        bl(self.font_semibold, "OPTIMIZACIÓN  ·  ANTES → DESPUÉS", TEXT_COLOR, pad, 14)
        bl(self.font_tiny, "CO2 proyectado sobre el mismo horizonte", TEXT_DIM, pad, 38)

        # Barras de CO2 (base vs óptimo), escaladas al mayor
        base_co2, opt_co2 = c["base_co2"], c["opt_co2"]
        max_co2 = max(base_co2, opt_co2, 1e-9)
        bar_x = pad + 66
        bar_w = w - bar_x - pad - 60
        rows = [
            ("Manual", base_co2, ERROR_COLOR, f'{c["base_ns"]:.0f}/{c["base_ew"]:.0f}s'),
            ("Óptimo", opt_co2, SUCCESS_COLOR, f'{c["opt_ns"]:.0f}/{c["opt_ew"]:.0f}s'),
        ]
        ry = 62
        for label, val, color, split in rows:
            bl(self.font_tiny, label, TEXT_DIM, pad, ry + 1)
            track = pygame.Rect(bar_x, ry, bar_w, 14)
            pygame.draw.rect(surf, (38, 43, 54, int(255 * alpha)), track, border_radius=7)
            fw = int((val / max_co2) * bar_w)
            if fw > 0:
                pygame.draw.rect(surf, (*color, int(255 * alpha)),
                                 (bar_x, ry, fw, 14), border_radius=7)
            bl(self.font_mono, f"{val:.1f}kg", TEXT_COLOR, bar_x + bar_w + 8, ry - 1)
            bl(self.font_tiny, f"verde {split}", TEXT_FAINT, bar_x, ry + 18)
            ry += 44

        # Cifra grande de reducción
        pct = c["pct"]
        pcol = SUCCESS_COLOR if pct > 0 else ERROR_COLOR
        big = self.font_large.render(f"-{abs(pct):.1f}%", True, pcol)
        big.set_alpha(int(255 * alpha))
        surf.blit(big, (pad, h - 42))
        bl(self.font_tiny, "menos contaminación", TEXT_DIM, pad + big.get_width() + 10, h - 34)

        self.screen.blit(surf, card.topleft)

    def run(self) -> None:
        """Bucle principal de la simulación."""
        dt = 0.016

        while self.running:
            self.handle_events()
            self.spawn_vehicles(dt)
            self.update_traffic_light(dt)
            self.update_vehicles(dt)

            # Máscara de verde por dirección [N-S, E-O, S-N, O-E] — acopla semáforo y colas
            green_mask = [
                self.light_state == "green_ns",
                self.light_state == "green_ew",
                self.light_state == "green_ns",
                self.light_state == "green_ew",
            ]
            self.engine.step(discrete_counts=self.discrete_counts, green_mask=green_mask)

            # Muestrea conteos para la demanda por ventana (~5 Hz) y poda lo viejo
            now = self.engine.current_time
            if not self.count_samples or now - self.count_samples[-1][0] >= 0.2:
                self.count_samples.append((now, tuple(self.discrete_counts)))
            self.count_samples = [s for s in self.count_samples
                                  if now - s[0] <= self.DEMAND_WINDOW + 0.5]

            # Refresca la proyección (fuente única de CO2/retraso) ~1 vez por segundo.
            # No cada frame: project_emissions corre cientos de pasos de Heun.
            self.proj_timer += dt
            if self.proj_timer >= 1.0:
                self.proj_timer = 0.0
                self.refresh_projection()

            if self.status_timer > 0:
                self.status_timer -= dt
            if self.comparison and self.comparison["timer"] > 0:
                self.comparison["timer"] -= dt

            # Dibujar todo
            self._draw_background()
            self.draw_intersection()
            self.draw_traffic_lights()
            self.draw_vehicle_queues()
            self.draw_left_panel()
            self.draw_right_panel()
            self.draw_comparison_overlay()
            self.draw_status_message()
            self.help_overlay.draw(self.screen, {
                "title": self.font_large, "section": self.font_semibold,
                "body": self.font_small, "mono": self.font_mono, "tiny": self.font_tiny,
            }, self.width, self.height)

            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()


def main() -> None:
    frontend = TrafficSimulationFrontend()
    frontend.run()


if __name__ == "__main__":
    main()
