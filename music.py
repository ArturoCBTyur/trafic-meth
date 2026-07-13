"""Música de fondo chiptune: melodía de Tetris (Korobeiniki, folk rusa de dominio
público) sintetizada proceduralmente como onda cuadrada. Sin archivos externos.
"""

from __future__ import annotations

import numpy as np
import pygame

_PITCH_CLASS = {
    "C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5,
    "F#": 6, "G": 7, "G#": 8, "A": 9, "A#": 10, "B": 11,
}

# Korobeiniki (tema A de Tetris). Cada entrada: (nota, duración en tiempos).
_MELODY: list[tuple[str, float]] = [
    ("E5", 1), ("B4", .5), ("C5", .5), ("D5", 1), ("C5", .5), ("B4", .5),
    ("A4", 1), ("A4", .5), ("C5", .5), ("E5", 1), ("D5", .5), ("C5", .5),
    ("B4", 1.5), ("C5", .5), ("D5", 1), ("E5", 1),
    ("C5", 1), ("A4", 1), ("A4", 1), ("rest", 1),
    ("rest", .5), ("D5", 1), ("F5", .5), ("A5", 1), ("G5", .5), ("F5", .5),
    ("E5", 1.5), ("C5", .5), ("E5", 1), ("D5", .5), ("C5", .5),
    ("B4", 1), ("B4", .5), ("C5", .5), ("D5", 1), ("E5", 1),
    ("C5", 1), ("A4", 1), ("A4", 1), ("rest", 1),
]


def _note_freq(note: str) -> float:
    """Frecuencia (Hz) de una nota tipo 'E5'/'A4'/'rest' (A4 = 440 Hz)."""
    if note == "rest":
        return 0.0
    name, octave = note[:-1], int(note[-1])
    midi = (octave + 1) * 12 + _PITCH_CLASS[name]
    return 440.0 * (2.0 ** ((midi - 69) / 12.0))


def make_tetris_sound(volume: float = 0.22, bpm: float = 150.0) -> pygame.mixer.Sound:
    """Sintetiza la melodía completa y devuelve un pygame.Sound (para reproducir en bucle).

    Requiere el mixer inicializado; lo inicializa si hace falta. Genera onda cuadrada
    con una pequeña envolvente ataque/decaimiento y un hueco entre notas (articulación).
    """
    init = pygame.mixer.get_init()
    if init is None:
        pygame.mixer.init(frequency=44100, size=-16, channels=2)
        init = pygame.mixer.get_init()
    sample_rate, _fmt, channels = init

    beat = 60.0 / bpm
    segments: list[np.ndarray] = []
    attack = int(sample_rate * 0.005)
    release = int(sample_rate * 0.030)

    for note, beats in _MELODY:
        n = int(sample_rate * beats * beat)
        if n <= 0:
            continue
        freq = _note_freq(note)
        if freq <= 0.0:
            segments.append(np.zeros(n))
            continue
        t = np.arange(n) / sample_rate
        wave = np.sign(np.sin(2.0 * np.pi * freq * t))  # onda cuadrada
        env = np.ones(n)
        if attack > 0:
            env[:attack] = np.linspace(0.0, 1.0, attack)
        if release > 0 and release < n:
            env[-release:] = np.linspace(1.0, 0.0, release)
        wave *= env
        gap = int(n * 0.12)  # silencio final → separación entre notas
        if gap > 0:
            wave[-gap:] = 0.0
        segments.append(wave)

    buffer = np.concatenate(segments) if segments else np.zeros(1)
    buffer = np.clip(buffer * volume, -1.0, 1.0)
    pcm = (buffer * 32767).astype(np.int16)
    if channels == 2:
        pcm = np.column_stack([pcm, pcm])
    return pygame.sndarray.make_sound(np.ascontiguousarray(pcm))
