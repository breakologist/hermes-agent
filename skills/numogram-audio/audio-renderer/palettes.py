"""Color palettes & visual constants for numogram audiovisual output.

Palettes sourced from:
- CCRU orbital visualizer (lumpenspace/ccru) — ZONE_CLR mapping
- Wiki asset SVGs — baseline dark theme + accent set
- SunVox / tracker aesthetic conventions
"""

import os

# ── Canonical zone colors (CCRU ZONE_CLR) ────────────────────────────────────
# Source: lumpenspace/ccru app/data/zones.ts
ZONE_COLOR = {
    0: '#aaaaaa',  # Plex  — grey
    1: '#ee44ee',  # Torque — magenta
    2: '#4488ff',  # Torque — blue
    3: '#44cc77',  # Warp  — green
    4: '#ee4444',  # Torque — red
    5: '#ee8833',  # Torque — orange
    6: '#ddcc33',  # Warp  — yellow
    7: '#7755cc',  # Torque — purple
    8: '#9944ee',  # Torque — violet
    9: '#666666',  # Plex  — dark grey
}

# Syzygy pair colors
SYZYGY_PAIRS = [(4, 5), (3, 6), (2, 7), (1, 8), (0, 9)]
SYZYGY_COLORS = {
    (4, 5): '#ff4444',
    (3, 6): '#44cc77',
    (2, 7): '#4488ff',
    (1, 8): '#ee44ee',
    (0, 9): '#aaaaaa',
}

# ── Theme palettes ───────────────────────────────────────────────────────────
PALETTES = {
    'ccru': {
        'bg':      '#0f172a',
        'fg':      '#e2e8f0',
        'zone':    list(ZONE_COLOR.values()),
        'accent':  '#fbbf24',
        'syzygy':  '#22d3ee',
        'current': '#34d399',
    },
    'amber': {
        'bg':      '#0a0a0a',
        'fg':      '#FFD700',
        'zone':    ['#FFD700', '#FF8C00', '#FFA500', '#FFCC00', '#E6B800'],
        'accent':  '#FF8C00',
        'syzygy':  '#FF4500',
        'current': '#FFD700',
    },
    'sunvox': {
        'bg':      '#000000',
        'fg':      '#ffffff',
        'zone':    ['#00ffff', '#ff00ff', '#ffff00', '#00ff00', '#ff0000',
                    '#0000ff', '#ff8800', '#8800ff', '#00ff80'],
        'accent':  '#00ffff',
        'syzygy':  '#ff00ff',
        'current': '#ffff00',
    },
    'cult-garden': {
        'bg':      '#08080c',
        'fg':      '#FFD700',
        'zone':    ['#FFD700', '#FF8C00', '#FF00FF', '#00FFFF', '#00FF00', '#0080FF', '#FF3333'],
        'accent':  '#FFD700',
        'syzygy':  '#FF00FF',
        'current': '#00FFFF',
    },
}

FFMPEG_COLORMAPS = ['viridis', 'magma', 'plasma', 'cool']

# TouchDesigner MCP connection settings
TD_MCP_HOST = '127.0.0.1'
TD_MCP_PORT = 40404
TD_PROJECT_PATH = os.path.expanduser('~/.hermes/assets/numogram-viz.toe')
TD_AUDIO_DROP = '/project1/audio_drop'   # within TD network — configurable via MCP


# Terminal ANSI-256 foreground colors (bright variants)
ANSI_FG = {
    0: "\033[38;5;238m",  # void — dark grey
    1: "\033[38;5;226m",  # surge — yellow
    2: "\033[38;5;214m",  # double — orange
    3: "\033[38;5;201m",  # trap — pink / magenta
    4: "\033[38;5;51m",   # wall — bright cyan
    5: "\033[38;5;46m",   # hidden — green
    6: "\033[38;5;39m",   # rotation — teal
    7: "\033[38;5;124m",  # cut — red
    8: "\033[38;5;147m",  # mirror — lavender
    9: "\033[38;5;93m",   # plex — purple
}

# Zone → ComfyUI prompt fragment (from wallpaper script)
ZONE_PROMPTS = {
    0: {"positive": "abstract void, pure black background, faint geometric lattice emerging from darkness, mathematical grid, negative space, minimalist, dark aesthetic, high contrast, 8k wallpaper"},
    1: {"positive": "electric blue fractals radiating outward, first movement, surge of energy, lightning patterns, fibonacci spirals, dynamic motion, sci-fi aesthetic, dark background, 8k wallpaper"},
    2: {"positive": "doubling spirals, amber and gold tones, recursive patterns, infinite regression, mirror symmetry, warm light, mathematical art, dark background, 8k wallpaper"},
    3: {"positive": "triangular traps, green and ochre geometry, overlapping triangles, tessellation, sacred geometry, earth tones, mathematical precision, dark background, 8k wallpaper"},
    4: {"positive": "walls within walls, grey brutalist architecture, impossible rooms, escher-like structure, concrete textures, perspective tricks, cold tones, 8k wallpaper"},
    5: {"positive": "hidden center, concentric rings, deep purple and silver, ripples in still water, mandala, focal point, meditative, cosmic, dark background, 8k wallpaper"},
    6: {"positive": "rotational symmetry, violet and teal vortex, hinge mechanism, gears and spirals, bifurcation, quantum aesthetic, dark background, 8k wallpaper"},
    7: {"positive": "clean geometric cuts, red and black division, sharp lines, bisection, surgical precision, high contrast, minimalist, dark background, 8k wallpaper"},
    8: {"positive": "mirror inversion, lavender and rose quartz, reflected symmetry, kaleidoscope, delicate balance, soft contrast, dark background, 8k wallpaper"},
    9: {"positive": "full plex, prismatic white light, all colors unified, radiant glow, synthesis, over-determined, hyperstitional, bright background, 8k wallpaper"},
}
