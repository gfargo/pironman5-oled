"""Screensaver registry — each animation is a standalone class with reset() and draw(oled)."""
from .dvd_bounce import DVDBounce
from .starfield import Starfield
from .matrix_rain import MatrixRain
from .sine_wave import SineWave
from .particles import Particles
from .game_of_life import GameOfLife
from .fractal_tree import FractalTree
from .pendulum_wave import PendulumWave
from .uptime_counter import UptimeCounter
from .binary_clock import BinaryClock
from .ocean_waves import OceanWaves
from .lissajous import Lissajous
from .perlin_terrain import PerlinTerrain
from .spirograph import Spirograph
from .lorenz_attractor import LorenzAttractor
from .raindrop_ripples import RaindropRipples
from .fire_effect import FireEffect
from .maze import Maze

ALL_SCREENSAVERS = [
    DVDBounce,
    Starfield,
    MatrixRain,
    SineWave,
    Particles,
    GameOfLife,
    FractalTree,
    PendulumWave,
    UptimeCounter,
    BinaryClock,
    OceanWaves,
    Lissajous,
    PerlinTerrain,
    Spirograph,
    LorenzAttractor,
    RaindropRipples,
    FireEffect,
    Maze,
]
