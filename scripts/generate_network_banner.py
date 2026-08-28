#!/usr/bin/env python3
"""Generate the AICA-inspired animated profile banner.

Tuning constants are grouped near the top so the animation can be adjusted
without changing the deterministic structure:
- SEED controls every procedural choice.
- FRAME_COUNT and FRAME_DURATION_MS define the GIF runtime.
- NODE_COUNT, LINK_RADIUS, and ACTIVATION_COUNT set network density.
- TEXT_RESERVED_X keeps the right-side title area quiet and legible.
"""

from __future__ import annotations

import argparse
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


WIDTH = 1584
HEIGHT = 480
SEED = 20260828

FRAME_COUNT = 96
FRAME_DURATION_MS = 90
NODE_COUNT = 76
LINK_RADIUS = 160
ACTIVATION_COUNT = 3
TEXT_RESERVED_X = 1050

BG = (5, 16, 31)
GRID_DOT = (25, 49, 73)
EDGE_BASE = (36, 117, 163)
EDGE_HOT = (93, 231, 255)
NODE_BASE = (78, 174, 219)
NODE_HOT = (210, 252, 255)
TEXT_PRIMARY = (237, 248, 255)
TEXT_SECONDARY = (137, 176, 196)


def lerp(a: int, b: int, t: float) -> int:
    return int(a + (b - a) * max(0.0, min(1.0, t)))


def mix(c1: tuple[int, int, int], c2: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    return tuple(lerp(a, b, t) for a, b in zip(c1, c2))


def ease_pulse(v: float) -> float:
    return math.exp(-10.0 * v * v)


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    names = [
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
    ]
    for name in names:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def make_nodes() -> list[dict[str, float]]:
    rng = random.Random(SEED)
    nodes: list[dict[str, float]] = []
    while len(nodes) < NODE_COUNT:
        x = rng.uniform(56, WIDTH - 64)
        y = rng.uniform(44, HEIGHT - 44)
        if x > TEXT_RESERVED_X - 45 and 118 < y < 330:
            continue
        if x > 1210 and 92 < y < 360 and rng.random() < 0.82:
            continue
        nodes.append(
            {
                "x": x,
                "y": y,
                "phase": rng.random() * math.tau,
                # Integer frequencies make every orbit close exactly at the
                # GIF boundary, avoiding a visible final-to-first-frame jump.
                "freq_x": float(rng.choice((1, 1, 2))),
                "freq_y": float(rng.choice((1, 2))),
                "dx": rng.uniform(-4.8, 4.8),
                "dy": rng.uniform(-3.2, 3.2),
                "base": rng.uniform(1.4, 2.5),
            }
        )
    return nodes


def node_position(node: dict[str, float], t: float) -> tuple[float, float]:
    phase = node["phase"]
    return (
        node["x"] + math.sin(t * math.tau * node["freq_x"] + phase) * node["dx"],
        node["y"] + math.cos(t * math.tau * node["freq_y"] + phase * 1.7) * node["dy"],
    )


def make_edges(nodes: list[dict[str, float]]) -> list[tuple[int, int, float]]:
    edges: set[tuple[int, int]] = set()
    for i, a in enumerate(nodes):
        candidates: list[tuple[float, int]] = []
        for j, b in enumerate(nodes):
            if i == j:
                continue
            d = math.hypot(a["x"] - b["x"], a["y"] - b["y"])
            if d < LINK_RADIUS:
                candidates.append((d, j))
        for d, j in sorted(candidates)[:3]:
            if random.Random(SEED + i * 997 + j).random() < 0.74:
                edges.add((min(i, j), max(i, j)))
    return [(i, j, math.hypot(nodes[i]["x"] - nodes[j]["x"], nodes[i]["y"] - nodes[j]["y"])) for i, j in sorted(edges)]


def activation_centers(t: float) -> list[tuple[float, float, float]]:
    rng = random.Random(SEED + 404)
    centers: list[tuple[float, float, float]] = []
    for _ in range(ACTIVATION_COUNT):
        phase = rng.random()
        direction = rng.choice((-1.0, 1.0))
        amplitude_x = rng.uniform(105.0, 205.0)
        amplitude_y = rng.uniform(70.0, 125.0)
        center_x = rng.uniform(110.0 + amplitude_x, TEXT_RESERVED_X - 95.0 - amplitude_x)
        center_y = rng.uniform(54.0 + amplitude_y, HEIGHT - 54.0 - amplitude_y)
        angle = math.tau * (direction * t + phase)
        x = center_x + amplitude_x * math.sin(angle + 0.2 * math.sin(2.0 * angle))
        y = center_y + amplitude_y * math.cos(angle + phase * math.pi)
        radius_base = rng.uniform(112.0, 132.0)
        radius_swing = rng.uniform(14.0, 22.0)
        radius = radius_base + radius_swing * math.sin(angle + phase * math.tau)
        centers.append((x, y, radius))
    return centers


def activation_at(x: float, y: float, centers: list[tuple[float, float, float]]) -> float:
    value = 0.0
    for cx, cy, radius in centers:
        d = math.hypot(x - cx, y - cy)
        value = max(value, max(0.0, 1.0 - d / radius))
    return value


def draw_grid(draw: ImageDraw.ImageDraw) -> None:
    for y in range(18, HEIGHT, 24):
        for x in range(18, WIDTH, 24):
            fade = 0.45 + 0.45 * (1 - abs((x / WIDTH) - 0.47))
            color = tuple(int(c * fade) for c in GRID_DOT)
            draw.ellipse((x - 1, y - 1, x + 1, y + 1), fill=color)


def draw_text(draw: ImageDraw.ImageDraw) -> None:
    title_font = load_font(56, bold=True)
    sub_font = load_font(24)
    x = 1110
    y = 178
    draw.text((x + 2, y + 2), "Yunhong Min", font=title_font, fill=(1, 9, 18))
    draw.text((x, y), "Yunhong Min", font=title_font, fill=TEXT_PRIMARY)
    draw.text((x, y + 75), "AICA Lab · Soongsil University", font=sub_font, fill=TEXT_SECONDARY)


def render_frame(nodes: list[dict[str, float]], edges: list[tuple[int, int, float]], frame_index: int) -> Image.Image:
    t = frame_index / FRAME_COUNT
    img = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(img, "RGBA")
    draw_grid(draw)

    centers = activation_centers(t)
    positions = [node_position(node, t) for node in nodes]
    node_energy = [0.0 for _ in nodes]

    for edge_index, (i, j, _) in enumerate(edges):
        x1, y1 = positions[i]
        x2, y2 = positions[j]
        mx = (x1 + x2) * 0.5
        my = (y1 + y2) * 0.5
        energy = activation_at(mx, my, centers)
        shimmer = 0.5 + 0.5 * math.sin(math.tau * (t * 2.0 + edge_index * 0.071))
        visible = energy + 0.14 * shimmer
        if visible < 0.32:
            continue
        node_energy[i] = max(node_energy[i], energy)
        node_energy[j] = max(node_energy[j], energy)
        alpha = int(8 + 42 * min(1.0, visible))
        draw.line((x1, y1, x2, y2), fill=(*mix(EDGE_BASE, EDGE_HOT, energy), alpha), width=1)

        if energy > 0.5 and edge_index % 5 == 0:
            pulse_cycles = 2 + (edge_index % 3)
            travel = (t * pulse_cycles + edge_index * 0.137) % 1.0
            span = 0.08
            ax = x1 + (x2 - x1) * max(0.0, travel - span)
            ay = y1 + (y2 - y1) * max(0.0, travel - span)
            bx = x1 + (x2 - x1) * min(1.0, travel + span)
            by = y1 + (y2 - y1) * min(1.0, travel + span)
            glow = int(44 + 52 * energy)
            draw.line((ax, ay, bx, by), fill=(*EDGE_HOT, glow), width=1)
            node_energy[i] = max(node_energy[i], energy * ease_pulse(travel))
            node_energy[j] = max(node_energy[j], energy * ease_pulse(1.0 - travel))

    for idx, (x, y) in enumerate(positions):
        energy = max(node_energy[idx], activation_at(x, y, centers) * 0.75)
        base = nodes[idx]["base"]
        r = base + 1.4 * energy
        color = mix(NODE_BASE, NODE_HOT, energy)
        draw.ellipse((x - r * 1.7, y - r * 1.7, x + r * 1.7, y + r * 1.7), fill=(*color, int(3 + 16 * energy)))
        draw.ellipse((x - r, y - r, x + r, y + r), fill=(*color, int(65 + 55 * energy)))
        if energy > 0.72:
            draw.ellipse((x - 1.5, y - 1.5, x + 1.5, y + 1.5), fill=(*NODE_HOT, 145))

    # Subtle veil keeps the title zone calm while preserving the global grid.
    draw.rectangle((TEXT_RESERVED_X - 24, 92, WIDTH, 350), fill=(BG[0], BG[1], BG[2], 174))
    draw_text(draw)
    return img.quantize(colors=96, method=Image.Quantize.MEDIANCUT)


def generate(output: Path) -> None:
    nodes = make_nodes()
    edges = make_edges(nodes)
    frames = [render_frame(nodes, edges, i) for i in range(FRAME_COUNT)]
    output.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(
        output,
        save_all=True,
        append_images=frames[1:],
        duration=FRAME_DURATION_MS,
        loop=0,
        optimize=True,
        disposal=2,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the deterministic animated network banner GIF.")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "assets" / "banner-v5-network.gif",
        help="Output GIF path. Defaults to assets/banner-v5-network.gif beside the project root.",
    )
    args = parser.parse_args()
    generate(args.output)


if __name__ == "__main__":
    main()
