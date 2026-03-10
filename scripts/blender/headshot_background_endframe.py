#!/usr/bin/env python3
"""
Render headshot decorative layers with Blender (bpy).

Outputs (default names):
- headshot-bg-backdrop.png: base rectangle + blue accents (transparent outside)
- headshot-bg-overlay.png: plusses/lines/arcs/light gradient overlay (transparent)
- headshot-bg-backdrop.webm: animated backdrop layer (alpha)
- headshot-bg-overlay.webm: hold video for overlay layer (alpha)

Run:
/Applications/Blender.app/Contents/MacOS/Blender -b -P scripts/blender/headshot_background_endframe.py -- --output-dir public/generated/headshot-bg --frame-width 1000 --frame-height 1007

"""

from __future__ import annotations

import argparse
import math
import random
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple

try:
    import bpy
except ModuleNotFoundError:
    print("This script must run inside Blender (bpy unavailable).", file=sys.stderr)
    sys.exit(1)

BASE_WIDTH = 1000
BASE_HEIGHT = 1007

# Geometry measured from the target artwork at 1000x1007.
PROFILE_PHOTO_PANEL_CORNER_RADIUS = 6.0
MAIN_RECT = {"left": 24, "top": 130, "right": 914, "bottom": 964}
# Blue plate base geometry before profile-photo offset is applied.
BLUE_BACK = {"left": 24, "top": 130, "right": 928, "bottom": 974}
# Positive values move the blue square right/down in screen space.
# Defaults preserve the current rendered placement.
X_OFFSET_BLUE_SQUARE_PROFILE_PHOTO = 2.0
Y_OFFSET_BLUE_PROFILE_PHOTO = 24.0

# Profile-photo palette controls.
RED_PROFILE_PHOTO_HEX = "A20F10"        # Most saturated red (gradient right side + red quarter-circle icon)
DARK_BLUE_PROFILE_PHOTO_HEX = "0b1769"  # Plusses + lower-left striped shape
LIGHT_BLUE_PROFILE_PHOTO_HEX = "3144b3" # Blue square behind the gradient panel
# Horizontal gradient controls (0.0 = left edge, 1.0 = right edge).
RED_GRADIENT_END_COLOR_PROFILE_PHOTO_HEX = RED_PROFILE_PHOTO_HEX
RED_GRADIENT_END_STOP_PROFILE_PHOTO = 0.9

# Master animation duration. All internal checkpoints scale from this value.
# Actual frame count is computed as: round(fps * duration_seconds).
PROFILE_PHOTO_ANIMATION_FPS = 24
PROFILE_PHOTO_ANIMATION_DURATION_SECONDS = 0.5

# Hatch tuning (in screen-pixel units for the ortho camera setup).
HATCH_LINE_WIDTH_PX = 2.0
HATCH_LINE_SPACING_PX = 11.0
HATCH_LINE_ANGLE_DEG = 45.0  # Lower-left to upper-right in screen space.
HATCH_LINE_ENDPOINT_INSET_PX = HATCH_LINE_WIDTH_PX * 0.5

# Hatch cutout geometry and animation controls.
HATCH_BLOCK_LEFT = 0.0
HATCH_BLOCK_TOP = 836.0
HATCH_BLOCK_RIGHT = 450.0
HATCH_BLOCK_BOTTOM = 1007.0
HATCH_BLOCK_RADIUS_TOP_LEFT_PX = 10
HATCH_BLOCK_RADIUS_TOP_RIGHT_HEIGHT_RATIO = 0.5
HATCH_BLOCK_RADIUS_BOTTOM_RIGHT_HEIGHT_RATIO = 0.5
HATCH_BLOCK_RADIUS_BOTTOM_LEFT_PX = 70.0
HATCH_BLOCK_CORNER_SEGMENTS = 30
# Hatch animation now runs across the full master timeline.
HATCH_DRAW_START_PROGRESS = 0.0
HATCH_DRAW_END_PROGRESS = 1.0
# Integer seed controlling random start-position per line segment.
HATCH_DRAW_ORIGIN_SEED = 17
# Backward-compatible alias (used by older helpers).
HATCH_RANDOM_SEED = HATCH_DRAW_ORIGIN_SEED

# Plus draw animation controls.
# Portion of the full timeline each plus can consume (both strokes combined).
# 1.0 means all pluses must start together at frame 1 and finish at the final frame.
LIFECYCLE_OF_PLUS_ANIMATION_AS_PORTION_OF_TOTAL_ANIMATION = 0.45
# Dedicated seed for all plus randomness: start time, stroke order, and stroke origins.
PLUS_ANIMATION_RANDOM_SEED = 29

# Plus layout controls (screen-space px at 1000x1007 reference geometry).
# "Length" here is the square footprint of each plus icon (width == height).
WHITE_PLUS_SIZE_PX = 30.0
BLUE_PLUS_SIZE_PX = 29.0
WHITE_PLUS_THICKNESS_PX = 6.0
BLUE_PLUS_THICKNESS_PX = 7.0
WHITE_PLUS_COL_GAP_PX = 39.0
WHITE_PLUS_ROW_GAP_PX = 38.5
BLUE_PLUS_COL_GAP_PX = 38.5
BLUE_PLUS_ROW_GAP_PX = 38.5
# Top offsets are measured from the red panel top edge (MAIN_RECT["top"]).
WHITE_PLUS_TOP_CENTER_OFFSET_FROM_RED_PANEL_PX = 206.0
BLUE_PLUS_TOP_CENTER_OFFSET_FROM_RED_PANEL_PX = 321.5


def parse_blender_args() -> argparse.Namespace:
    raw = sys.argv
    tail = raw[raw.index("--") + 1:] if "--" in raw else []

    parser = argparse.ArgumentParser(description="Render layered headshot decorative assets.")
    parser.add_argument("--output-dir", type=Path, default=Path("public/generated/headshot-bg"))
    parser.add_argument("--frame-width", type=int, default=BASE_WIDTH)
    parser.add_argument("--frame-height", type=int, default=BASE_HEIGHT)
    parser.add_argument("--fps", type=int, default=PROFILE_PHOTO_ANIMATION_FPS)
    parser.add_argument("--duration-seconds", type=float, default=PROFILE_PHOTO_ANIMATION_DURATION_SECONDS)

    parser.add_argument("--backdrop-still-name", type=str, default="headshot-bg-backdrop.png")
    parser.add_argument("--overlay-still-name", type=str, default="headshot-bg-overlay.png")

    parser.add_argument("--backdrop-video-webm-name", type=str, default="headshot-bg-backdrop.webm")
    parser.add_argument("--overlay-video-webm-name", type=str, default="headshot-bg-overlay.webm")
    parser.add_argument("--overlay-video-mp4-name", type=str, default="headshot-bg-overlay.mp4")

    parser.add_argument(
        "--keep-frame-sequence",
        action="store_true",
        help="Keep intermediate PNG frame folders used for ffmpeg encoding.",
    )
    parser.add_argument(
        "--skip-video",
        action="store_true",
        help="Render stills only.",
    )
    return parser.parse_args(tail)


def hex_to_rgba(value: str, alpha: float = 1.0) -> Tuple[float, float, float, float]:
    value = value.strip().lstrip("#")
    if len(value) != 6:
        raise ValueError(f"Expected 6-digit hex color, got '{value}'.")
    r = int(value[0:2], 16) / 255.0
    g = int(value[2:4], 16) / 255.0
    b = int(value[4:6], 16) / 255.0
    return (r, g, b, alpha)


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    for mesh in list(bpy.data.meshes):
        if mesh.users == 0:
            bpy.data.meshes.remove(mesh)
    for material in list(bpy.data.materials):
        if material.users == 0:
            bpy.data.materials.remove(material)
    for image in list(bpy.data.images):
        if image.users == 0:
            bpy.data.images.remove(image)


def setup_scene(frame_width: int, frame_height: int, fps: int, duration_seconds: float) -> bpy.types.Scene:
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = frame_width
    scene.render.resolution_y = frame_height
    scene.render.resolution_percentage = 100
    scene.render.fps = fps
    scene.frame_start = 1
    scene.frame_end = max(1, int(round(fps * duration_seconds)))
    scene.frame_current = scene.frame_end

    scene.render.film_transparent = True
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.image_settings.color_depth = "8"

    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
    scene.view_settings.exposure = 0.0
    scene.view_settings.gamma = 1.0

    world = scene.world or bpy.data.worlds.new("World")
    world.use_nodes = True
    scene.world = world
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs[0].default_value = (0.0, 0.0, 0.0, 1.0)
        bg.inputs[1].default_value = 1.0

    return scene


def add_camera(frame_width: int) -> None:
    camera_data = bpy.data.cameras.new("RenderCamera")
    camera_data.type = "ORTHO"
    camera_data.sensor_fit = "HORIZONTAL"
    camera_data.ortho_scale = float(frame_width)

    camera = bpy.data.objects.new("RenderCamera", camera_data)
    camera.location = (0.0, 0.0, 12.0)
    bpy.context.scene.collection.objects.link(camera)
    bpy.context.scene.camera = camera


def ensure_collection(name: str) -> bpy.types.Collection:
    scene_coll = bpy.context.scene.collection
    existing = bpy.data.collections.get(name)
    if existing is not None:
        return existing
    coll = bpy.data.collections.new(name)
    scene_coll.children.link(coll)
    return coll


def make_flat_material(name: str, color: Tuple[float, float, float, float]) -> bpy.types.Material:
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    mat.blend_method = "BLEND"
    if hasattr(mat, "shadow_method"):
        mat.shadow_method = "NONE"

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    out = nodes.new(type="ShaderNodeOutputMaterial")
    transparent = nodes.new(type="ShaderNodeBsdfTransparent")
    emission = nodes.new(type="ShaderNodeEmission")
    mix = nodes.new(type="ShaderNodeMixShader")

    emission.inputs["Color"].default_value = (color[0], color[1], color[2], 1.0)
    emission.inputs["Strength"].default_value = 1.0
    mix.inputs["Fac"].default_value = max(0.0, min(1.0, color[3]))

    links.new(transparent.outputs["BSDF"], mix.inputs[1])
    links.new(emission.outputs["Emission"], mix.inputs[2])
    links.new(mix.outputs["Shader"], out.inputs["Surface"])
    return mat


def make_horizontal_gradient_material(name: str) -> bpy.types.Material:
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    mat.blend_method = "BLEND"
    if hasattr(mat, "shadow_method"):
        mat.shadow_method = "NONE"

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    out = nodes.new(type="ShaderNodeOutputMaterial")
    tex_coord = nodes.new(type="ShaderNodeTexCoord")
    mapping = nodes.new(type="ShaderNodeMapping")
    separate = nodes.new(type="ShaderNodeSeparateXYZ")
    ramp = nodes.new(type="ShaderNodeValToRGB")
    emission = nodes.new(type="ShaderNodeEmission")

    mapping.inputs["Scale"].default_value = (1.0, 1.0, 1.0)
    mapping.inputs["Rotation"].default_value = (0.0, 0.0, 0.0)

    cr = ramp.color_ramp
    end_pos = max(0.001, min(1.0, RED_GRADIENT_END_STOP_PROFILE_PHOTO))
    end_color = hex_to_rgba(RED_GRADIENT_END_COLOR_PROFILE_PHOTO_HEX, 1.0)

    cr.elements[0].position = 0.0
    cr.elements[0].color = hex_to_rgba("e8d3d5", 1.0)
    cr.elements[1].position = end_pos
    cr.elements[1].color = end_color

    # Keep the midpoint hue while scaling to shorter/longer red endpoints.
    if end_pos > 0.002:
        mid_pos = max(0.001, min(end_pos - 0.001, end_pos * 0.58))
        mid = cr.elements.new(mid_pos)
        mid.color = hex_to_rgba("e58f9f", 1.0)

    # CSS-like stop behavior: hold full red from end stop to the panel edge.
    if end_pos < 0.999:
        hold = cr.elements.new(1.0)
        hold.color = end_color

    links.new(tex_coord.outputs["UV"], mapping.inputs["Vector"])
    links.new(mapping.outputs["Vector"], separate.inputs["Vector"])
    links.new(separate.outputs["X"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], emission.inputs["Color"])
    links.new(emission.outputs["Emission"], out.inputs["Surface"])

    return mat


def ensure_radial_alpha_image(name: str, size: int = 384, falloff_power: float = 1.85) -> bpy.types.Image:
    existing = bpy.data.images.get(name)
    if existing and existing.size[0] == size and existing.size[1] == size:
        return existing
    if existing:
        bpy.data.images.remove(existing)

    img = bpy.data.images.new(name=name, width=size, height=size, alpha=True, float_buffer=True)
    pixels = [0.0] * (size * size * 4)
    center = (size - 1) * 0.5
    inv_radius = 1.0 / max(1.0, center)

    for y in range(size):
        dy = (y - center) * inv_radius
        for x in range(size):
            dx = (x - center) * inv_radius
            dist = math.sqrt((dx * dx) + (dy * dy))
            base = max(0.0, 1.0 - dist)
            alpha = base ** falloff_power
            idx = (y * size + x) * 4
            pixels[idx + 0] = 1.0
            pixels[idx + 1] = 1.0
            pixels[idx + 2] = 1.0
            pixels[idx + 3] = alpha

    img.pixels.foreach_set(pixels)
    img.pack()
    return img


def make_image_glow_material(
    name: str,
    color_hex: str,
    image_name: str,
    alpha_scale: float,
) -> bpy.types.Material:
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    mat.blend_method = "BLEND"
    if hasattr(mat, "shadow_method"):
        mat.shadow_method = "NONE"

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    out = nodes.new(type="ShaderNodeOutputMaterial")
    transparent = nodes.new(type="ShaderNodeBsdfTransparent")
    emission = nodes.new(type="ShaderNodeEmission")
    mix = nodes.new(type="ShaderNodeMixShader")
    tex_coord = nodes.new(type="ShaderNodeTexCoord")
    mapping = nodes.new(type="ShaderNodeMapping")
    image_tex = nodes.new(type="ShaderNodeTexImage")
    alpha_mult = nodes.new(type="ShaderNodeMath")

    mapping.inputs["Location"].default_value = (0.0, 0.0, 0.0)
    mapping.inputs["Scale"].default_value = (1.0, 1.0, 1.0)
    image_tex.image = ensure_radial_alpha_image(image_name)
    image_tex.interpolation = "Cubic"
    image_tex.extension = "CLIP"
    alpha_mult.operation = "MULTIPLY"
    alpha_mult.inputs[1].default_value = max(0.0, min(1.0, alpha_scale))

    emission.inputs["Color"].default_value = hex_to_rgba(color_hex, 1.0)
    emission.inputs["Strength"].default_value = 1.0

    links.new(tex_coord.outputs["UV"], mapping.inputs["Vector"])
    links.new(mapping.outputs["Vector"], image_tex.inputs["Vector"])
    links.new(image_tex.outputs["Alpha"], alpha_mult.inputs[0])
    links.new(alpha_mult.outputs["Value"], mix.inputs["Fac"])
    links.new(transparent.outputs["BSDF"], mix.inputs[1])
    links.new(emission.outputs["Emission"], mix.inputs[2])
    links.new(mix.outputs["Shader"], out.inputs["Surface"])

    return mat


def px_to_world(x_px: float, y_px: float, frame_width: float, frame_height: float) -> Tuple[float, float]:
    return x_px - (frame_width / 2.0), (frame_height / 2.0) - y_px


def arc_points_screen(
    cx: float,
    cy: float,
    radius: float,
    start_deg: float,
    end_deg: float,
    segments: int,
) -> List[Tuple[float, float]]:
    points: List[Tuple[float, float]] = []
    for i in range(segments + 1):
        t = i / segments
        deg = start_deg + ((end_deg - start_deg) * t)
        rad = math.radians(deg)
        points.append((cx + (radius * math.cos(rad)), cy + (radius * math.sin(rad))))
    return points


def rounded_rect_points_screen(
    left: float,
    top: float,
    right: float,
    bottom: float,
    radius: float,
    segments: int = 16,
) -> List[Tuple[float, float]]:
    r = max(0.0, min(radius, (right - left) * 0.5, (bottom - top) * 0.5))
    if r <= 0.001:
        return [(left, top), (right, top), (right, bottom), (left, bottom)]

    points: List[Tuple[float, float]] = []
    points.append((left + r, top))
    points.append((right - r, top))
    points.extend(arc_points_screen(right - r, top + r, r, 270.0, 360.0, segments)[1:])
    points.append((right, bottom - r))
    points.extend(arc_points_screen(right - r, bottom - r, r, 0.0, 90.0, segments)[1:])
    points.append((left + r, bottom))
    points.extend(arc_points_screen(left + r, bottom - r, r, 90.0, 180.0, segments)[1:])
    points.append((left, top + r))
    points.extend(arc_points_screen(left + r, top + r, r, 180.0, 270.0, segments)[1:])
    return points


def top_right_rounded_points_screen(
    left: float,
    top: float,
    right: float,
    bottom: float,
    radius: float,
    segments: int = 16,
) -> List[Tuple[float, float]]:
    r = max(0.0, min(radius, (right - left) * 0.5, (bottom - top) * 0.5))
    if r <= 0.001:
        return [(left, top), (right, top), (right, bottom), (left, bottom)]

    points: List[Tuple[float, float]] = []
    points.append((left, bottom))
    points.append((right, bottom))
    points.append((right, top + r))
    points.extend(arc_points_screen(right - r, top + r, r, 0.0, -90.0, segments)[1:])
    points.append((left, top))
    return points


def right_side_rounded_points_screen(
    left: float,
    top: float,
    right: float,
    bottom: float,
    radius: float,
    segments: int = 16,
) -> List[Tuple[float, float]]:
    r = max(0.0, min(radius, (right - left) * 0.5, (bottom - top) * 0.5))
    if r <= 0.001:
        return [(left, top), (right, top), (right, bottom), (left, bottom)]

    points: List[Tuple[float, float]] = []
    points.append((left, top))
    points.append((right - r, top))
    points.extend(arc_points_screen(right - r, top + r, r, 270.0, 360.0, segments)[1:])
    points.append((right, bottom - r))
    points.extend(arc_points_screen(right - r, bottom - r, r, 0.0, 90.0, segments)[1:])
    points.append((left, bottom))
    return points


def right_side_and_bottom_left_rounded_points_screen(
    left: float,
    top: float,
    right: float,
    bottom: float,
    radius: float,
    segments: int = 16,
) -> List[Tuple[float, float]]:
    r = max(0.0, min(radius, (right - left) * 0.5, (bottom - top) * 0.5))
    if r <= 0.001:
        return [(left, top), (right, top), (right, bottom), (left, bottom)]

    points: List[Tuple[float, float]] = []
    points.append((left, top))
    points.append((right - r, top))
    points.extend(arc_points_screen(right - r, top + r, r, 270.0, 360.0, segments)[1:])
    points.append((right, bottom - r))
    points.extend(arc_points_screen(right - r, bottom - r, r, 0.0, 90.0, segments)[1:])
    points.append((left + r, bottom))
    points.extend(arc_points_screen(left + r, bottom - r, r, 90.0, 180.0, segments)[1:])
    points.append((left, top))
    return points


def hatch_block_points_screen(
    left: float,
    top: float,
    right: float,
    bottom: float,
    right_radius: float,
    lower_left_radius: float,
    segments: int = 18,
) -> List[Tuple[float, float]]:
    max_radius = min((right - left) * 0.5, (bottom - top) * 0.5)
    rr = max(0.0, min(right_radius, max_radius))
    ll = max(0.0, min(lower_left_radius, max_radius))

    points: List[Tuple[float, float]] = []
    points.append((left, top))
    points.append((right - rr, top))
    points.extend(arc_points_screen(right - rr, top + rr, rr, 270.0, 360.0, segments)[1:])
    points.append((right, bottom - rr))
    points.extend(arc_points_screen(right - rr, bottom - rr, rr, 0.0, 90.0, segments)[1:])
    points.append((left + ll, bottom))
    points.extend(arc_points_screen(left + ll, bottom - ll, ll, 90.0, 180.0, segments)[1:])
    points.append((left, top))
    return points


def rounded_rect_per_corner_points_screen(
    left: float,
    top: float,
    right: float,
    bottom: float,
    radius_top_left: float,
    radius_top_right: float,
    radius_bottom_right: float,
    radius_bottom_left: float,
    segments: int = 16,
) -> List[Tuple[float, float]]:
    width = max(0.0, right - left)
    height = max(0.0, bottom - top)
    max_r = min(width * 0.5, height * 0.5)

    rtl = max(0.0, min(radius_top_left, max_r))
    rtr = max(0.0, min(radius_top_right, max_r))
    rbr = max(0.0, min(radius_bottom_right, max_r))
    rbl = max(0.0, min(radius_bottom_left, max_r))

    points: List[Tuple[float, float]] = []

    def append_unique(pt: Tuple[float, float]) -> None:
        if not points:
            points.append(pt)
            return
        dx = points[-1][0] - pt[0]
        dy = points[-1][1] - pt[1]
        if (dx * dx) + (dy * dy) > 1e-10:
            points.append(pt)

    append_unique((left + rtl, top) if rtl > 0.0 else (left, top))
    append_unique((right - rtr, top) if rtr > 0.0 else (right, top))
    if rtr > 0.0:
        for pt in arc_points_screen(right - rtr, top + rtr, rtr, 270.0, 360.0, segments)[1:]:
            append_unique(pt)

    append_unique((right, bottom - rbr) if rbr > 0.0 else (right, bottom))
    if rbr > 0.0:
        for pt in arc_points_screen(right - rbr, bottom - rbr, rbr, 0.0, 90.0, segments)[1:]:
            append_unique(pt)

    append_unique((left + rbl, bottom) if rbl > 0.0 else (left, bottom))
    if rbl > 0.0:
        for pt in arc_points_screen(left + rbl, bottom - rbl, rbl, 90.0, 180.0, segments)[1:]:
            append_unique(pt)

    append_unique((left, top + rtl) if rtl > 0.0 else (left, top))
    if rtl > 0.0:
        for pt in arc_points_screen(left + rtl, top + rtl, rtl, 180.0, 270.0, segments)[1:]:
            append_unique(pt)

    if points:
        append_unique(points[0])
    return points


def hatch_segments_in_polygon_screen(
    polygon_points: Sequence[Tuple[float, float]],
    spacing_px: float,
    line_angle_deg: float = HATCH_LINE_ANGLE_DEG,
    endpoint_inset_px: float = 0.0,
) -> List[Tuple[Tuple[float, float], Tuple[float, float], float]]:
    if len(polygon_points) < 3:
        return []

    polygon = list(polygon_points)
    if len(polygon) >= 2:
        dx = polygon[0][0] - polygon[-1][0]
        dy = polygon[0][1] - polygon[-1][1]
        if (dx * dx) + (dy * dy) <= 1e-10:
            polygon = polygon[:-1]
    if len(polygon) < 3:
        return []

    angle_rad = math.radians(float(line_angle_deg))
    dir_x = math.cos(angle_rad)
    dir_y = -math.sin(angle_rad)  # Screen space uses +Y downward.
    normal_x = -dir_y
    normal_y = dir_x

    dir_len = math.hypot(dir_x, dir_y)
    if dir_len <= 1e-9:
        return []
    dir_x /= dir_len
    dir_y /= dir_len

    normal_len = math.hypot(normal_x, normal_y)
    if normal_len <= 1e-9:
        return []
    normal_x /= normal_len
    normal_y /= normal_len

    def dot_normal(pt: Tuple[float, float]) -> float:
        return (pt[0] * normal_x) + (pt[1] * normal_y)

    def dot_direction(pt: Tuple[float, float]) -> float:
        return (pt[0] * dir_x) + (pt[1] * dir_y)

    def intersect_edge(
        p0: Tuple[float, float],
        p1: Tuple[float, float],
        c_value: float,
    ) -> Optional[Tuple[float, float]]:
        x0, y0 = p0
        x1, y1 = p1
        dx = x1 - x0
        dy = y1 - y0
        denom = (dx * normal_x) + (dy * normal_y)
        if abs(denom) < 1e-9:
            return None
        t = (c_value - dot_normal(p0)) / denom
        if t < -1e-9 or t > 1.0 + 1e-9:
            return None
        t = max(0.0, min(1.0, t))
        return (x0 + (t * dx), y0 + (t * dy))

    spacing = max(1.0, float(spacing_px))
    endpoint_inset = max(0.0, float(endpoint_inset_px))
    c_values = [dot_normal(pt) for pt in polygon]
    c_min = min(c_values)
    c_max = max(c_values)

    c = math.floor((c_min - spacing) / spacing) * spacing
    c_end = math.ceil((c_max + spacing) / spacing) * spacing

    segments: List[Tuple[Tuple[float, float], Tuple[float, float], float]] = []
    while c <= (c_end + 1e-6):
        intersections: List[Tuple[float, float]] = []
        for idx in range(len(polygon)):
            p0 = polygon[idx]
            p1 = polygon[(idx + 1) % len(polygon)]
            hit = intersect_edge(p0, p1, c)
            if hit is None:
                continue
            duplicate = False
            for qx, qy in intersections:
                dx = hit[0] - qx
                dy = hit[1] - qy
                if (dx * dx) + (dy * dy) <= 1e-6:
                    duplicate = True
                    break
            if not duplicate:
                intersections.append(hit)

        if len(intersections) >= 2:
            intersections.sort(key=dot_direction)
            p_start = intersections[0]
            p_end = intersections[-1]
            seg_len = math.hypot(p_end[0] - p_start[0], p_end[1] - p_start[1])
            if seg_len <= max(1.0, HATCH_LINE_WIDTH_PX):
                c += spacing
                continue

            if endpoint_inset > 0.0:
                if seg_len <= (endpoint_inset * 2.0) + 1e-6:
                    c += spacing
                    continue
                ux = (p_end[0] - p_start[0]) / seg_len
                uy = (p_end[1] - p_start[1]) / seg_len
                p_start = (p_start[0] + (ux * endpoint_inset), p_start[1] + (uy * endpoint_inset))
                p_end = (p_end[0] - (ux * endpoint_inset), p_end[1] - (uy * endpoint_inset))
                seg_len = max(0.0, seg_len - (endpoint_inset * 2.0))

            if seg_len > max(1.0, HATCH_LINE_WIDTH_PX * 0.5):
                segments.append((p_start, p_end, seg_len))
        c += spacing

    return segments


def annulus_sector_points_screen(
    cx: float,
    cy: float,
    inner_radius: float,
    outer_radius: float,
    start_deg: float,
    end_deg: float,
    segments: int = 64,
) -> List[Tuple[float, float]]:
    outer = arc_points_screen(cx, cy, outer_radius, start_deg, end_deg, segments)
    inner = arc_points_screen(cx, cy, inner_radius, end_deg, start_deg, segments)
    return outer + inner


def add_polyline_stroke_curve(
    name: str,
    points_screen: Sequence[Tuple[float, float]],
    stroke_width: float,
    z: float,
    frame_width: int,
    frame_height: int,
    sx: float,
    sy: float,
    segments: int,
    material: bpy.types.Material,
    collection: bpy.types.Collection,
) -> bpy.types.Object:
    curve_data = bpy.data.curves.new(name=f"{name}Curve", type="CURVE")
    curve_data.dimensions = "3D"
    # Blender enum names differ by version; keep a no-fill-like mode when available.
    try:
        curve_data.fill_mode = "NONE"
    except TypeError:
        curve_data.fill_mode = "FULL"
    if hasattr(curve_data, "bevel_mode"):
        try:
            curve_data.bevel_mode = "ROUND"
        except (TypeError, ValueError):
            pass
    curve_data.bevel_depth = (max(1.0, stroke_width) * 0.5) * ((sx + sy) * 0.5)
    curve_data.bevel_resolution = 10
    curve_data.resolution_u = 24
    curve_data.use_fill_caps = True

    spline = curve_data.splines.new(type="POLY")
    spline.points.add(len(points_screen) - 1)
    for idx, (x, y) in enumerate(points_screen):
        wx, wy = px_to_world(x * sx, y * sy, frame_width, frame_height)
        spline.points[idx].co = (wx, wy, 0.0, 1.0)

    obj = bpy.data.objects.new(name, curve_data)
    obj.location = (0.0, 0.0, z)
    obj.data.materials.append(material)
    collection.objects.link(obj)
    return obj


def add_arc_stroke_curve(
    name: str,
    cx: float,
    cy: float,
    radius: float,
    start_deg: float,
    end_deg: float,
    stroke_width: float,
    z: float,
    frame_width: int,
    frame_height: int,
    sx: float,
    sy: float,
    segments: int,
    material: bpy.types.Material,
    collection: bpy.types.Collection,
) -> bpy.types.Object:
    return add_polyline_stroke_curve(
        name=name,
        points_screen=arc_points_screen(cx, cy, radius, start_deg, end_deg, segments),
        stroke_width=stroke_width,
        z=z,
        frame_width=frame_width,
        frame_height=frame_height,
        sx=sx,
        sy=sy,
        segments=segments,
        material=material,
        collection=collection,
    )


def add_corner_outline_icon(
    name_prefix: str,
    cx: float,
    cy: float,
    inner_radius: float,
    outer_radius: float,
    stroke_width: float,
    segments: int,
    z: float,
    frame_width: int,
    frame_height: int,
    sx: float,
    sy: float,
    material: bpy.types.Material,
    collection: bpy.types.Collection,
) -> List[Tuple[bpy.types.Object, float]]:
    stroke = max(1.0, stroke_width)
    half_stroke = stroke * 0.5
    radial_start = inner_radius + half_stroke
    radial_end = outer_radius - half_stroke
    if radial_end < radial_start:
        radial_start, radial_end = radial_end, radial_start

    top_connector = add_polyline_stroke_curve(
        f"{name_prefix}ConnectorTop",
        [
            (cx + radial_start, cy),
            (cx + radial_end, cy),
        ],
        stroke,
        z,
        frame_width,
        frame_height,
        sx,
        sy,
        max(2, segments // 8),
        material,
        collection,
    )
    outer_arc = add_arc_stroke_curve(
        f"{name_prefix}Outer",
        cx,
        cy,
        outer_radius,
        0.0,
        90.0,
        stroke,
        z,
        frame_width,
        frame_height,
        sx,
        sy,
        segments,
        material,
        collection,
    )
    left_connector = add_polyline_stroke_curve(
        f"{name_prefix}ConnectorLeft",
        [
            (cx, cy + radial_end),
            (cx, cy + radial_start),
        ],
        stroke,
        z,
        frame_width,
        frame_height,
        sx,
        sy,
        max(2, segments // 8),
        material,
        collection,
    )
    inner_arc = add_arc_stroke_curve(
        f"{name_prefix}Inner",
        cx,
        cy,
        inner_radius,
        90.0,
        0.0,
        stroke,
        z,
        frame_width,
        frame_height,
        sx,
        sy,
        segments,
        material,
        collection,
    )

    # Continuous draw order: top connector -> outer arc -> left connector -> inner arc.
    return [
        (top_connector, max(1e-6, radial_end - radial_start)),
        (outer_arc, max(1e-6, (math.pi * 0.5) * outer_radius)),
        (left_connector, max(1e-6, radial_end - radial_start)),
        (inner_arc, max(1e-6, (math.pi * 0.5) * inner_radius)),
    ]


def ellipse_points_screen(
    cx: float,
    cy: float,
    rx: float,
    ry: float,
    segments: int = 84,
) -> List[Tuple[float, float]]:
    points: List[Tuple[float, float]] = []
    for idx in range(segments):
        angle = (2.0 * math.pi * idx) / segments
        points.append((cx + (math.cos(angle) * rx), cy + (math.sin(angle) * ry)))
    return points


def add_polygon_object(
    name: str,
    points_screen: Sequence[Tuple[float, float]],
    z: float,
    frame_width: int,
    frame_height: int,
    sx: float,
    sy: float,
    material: bpy.types.Material,
    collection: bpy.types.Collection,
    origin_screen: Optional[Tuple[float, float]] = None,
) -> bpy.types.Object:
    verts = []
    min_x = min(point[0] for point in points_screen)
    max_x = max(point[0] for point in points_screen)
    min_y = min(point[1] for point in points_screen)
    max_y = max(point[1] for point in points_screen)
    span_x = max(1e-6, max_x - min_x)
    span_y = max(1e-6, max_y - min_y)

    origin_wx = 0.0
    origin_wy = 0.0
    if origin_screen is not None:
        origin_wx, origin_wy = px_to_world(origin_screen[0] * sx, origin_screen[1] * sy, frame_width, frame_height)

    for x, y in points_screen:
        wx, wy = px_to_world(x * sx, y * sy, frame_width, frame_height)
        if origin_screen is not None:
            verts.append((wx - origin_wx, wy - origin_wy, 0.0))
        else:
            verts.append((wx, wy, 0.0))

    mesh = bpy.data.meshes.new(f"{name}Mesh")
    mesh.from_pydata(verts, [], [tuple(range(len(verts)))])
    mesh.update()

    # Assign simple UVs for effects that need predictable 0..1 local coordinates.
    uv_layer = mesh.uv_layers.new(name="UVMap")
    for poly in mesh.polygons:
        for loop_idx in poly.loop_indices:
            vert_idx = mesh.loops[loop_idx].vertex_index
            x, y = points_screen[vert_idx]
            u = (x - min_x) / span_x
            v = 1.0 - ((y - min_y) / span_y)
            uv_layer.data[loop_idx].uv = (u, v)

    obj = bpy.data.objects.new(name, mesh)
    obj.location = (origin_wx, origin_wy, z)
    obj.data.materials.append(material)
    collection.objects.link(obj)
    return obj


def add_ellipse_glow(
    name: str,
    cx: float,
    cy: float,
    rx: float,
    ry: float,
    z: float,
    frame_width: int,
    frame_height: int,
    sx: float,
    sy: float,
    material: bpy.types.Material,
    collection: bpy.types.Collection,
) -> bpy.types.Object:
    return add_polygon_object(
        name,
        ellipse_points_screen(cx, cy, rx, ry),
        z,
        frame_width,
        frame_height,
        sx,
        sy,
        material,
        collection,
    )


def add_rounded_rect(
    name: str,
    left: float,
    top: float,
    right: float,
    bottom: float,
    radius: float,
    z: float,
    frame_width: int,
    frame_height: int,
    sx: float,
    sy: float,
    material: bpy.types.Material,
    collection: bpy.types.Collection,
    origin_screen: Optional[Tuple[float, float]] = None,
) -> bpy.types.Object:
    return add_polygon_object(
        name,
        rounded_rect_points_screen(left, top, right, bottom, radius, segments=16),
        z,
        frame_width,
        frame_height,
        sx,
        sy,
        material,
        collection,
        origin_screen=origin_screen,
    )


def add_rect_outline(
    name_prefix: str,
    left: float,
    top: float,
    right: float,
    bottom: float,
    stroke: float,
    z: float,
    frame_width: int,
    frame_height: int,
    sx: float,
    sy: float,
    material: bpy.types.Material,
    collection: bpy.types.Collection,
) -> None:
    s = max(1.0, stroke)
    add_rounded_rect(
        f"{name_prefix}Top",
        left,
        top,
        right,
        top + s,
        0.0,
        z,
        frame_width,
        frame_height,
        sx,
        sy,
        material,
        collection,
    )
    add_rounded_rect(
        f"{name_prefix}Bottom",
        left,
        bottom - s,
        right,
        bottom,
        0.0,
        z,
        frame_width,
        frame_height,
        sx,
        sy,
        material,
        collection,
    )
    add_rounded_rect(
        f"{name_prefix}Left",
        left,
        top,
        left + s,
        bottom,
        0.0,
        z,
        frame_width,
        frame_height,
        sx,
        sy,
        material,
        collection,
    )
    add_rounded_rect(
        f"{name_prefix}Right",
        right - s,
        top,
        right,
        bottom,
        0.0,
        z,
        frame_width,
        frame_height,
        sx,
        sy,
        material,
        collection,
    )


def add_plus(
    name_prefix: str,
    cx: float,
    cy: float,
    size: float,
    thickness: float,
    z: float,
    frame_width: int,
    frame_height: int,
    sx: float,
    sy: float,
    material: bpy.types.Material,
    collection: bpy.types.Collection,
) -> List[Tuple[bpy.types.Object, float, float]]:
    # Use true stroked curves so draw-on animation keeps rounded caps at every step.
    centerline_length = max(0.001, size - thickness)
    half_line = centerline_length * 0.5

    vert = add_polyline_stroke_curve(
        f"{name_prefix}Vert",
        points_screen=[(cx, cy - half_line), (cx, cy + half_line)],
        stroke_width=thickness,
        z=z,
        frame_width=frame_width,
        frame_height=frame_height,
        sx=sx,
        sy=sy,
        segments=2,
        material=material,
        collection=collection,
    )

    horz = add_polyline_stroke_curve(
        f"{name_prefix}Horz",
        points_screen=[(cx - half_line, cy), (cx + half_line, cy)],
        stroke_width=thickness,
        z=z,
        frame_width=frame_width,
        frame_height=frame_height,
        sx=sx,
        sy=sy,
        segments=2,
        material=material,
        collection=collection,
    )

    return [
        (vert, centerline_length, thickness),
        (horz, centerline_length, thickness),
    ]


def add_plus_grid(
    name_prefix: str,
    left_center_x: float,
    top_center_y: float,
    cols: int,
    rows: int,
    col_gap: float,
    row_gap: float,
    size: float,
    thickness: float,
    z: float,
    frame_width: int,
    frame_height: int,
    sx: float,
    sy: float,
    material: bpy.types.Material,
    collection: bpy.types.Collection,
) -> List[List[Tuple[bpy.types.Object, float, float]]]:
    plus_groups: List[List[Tuple[bpy.types.Object, float, float]]] = []
    for r in range(rows):
        for c in range(cols):
            cx = left_center_x + (c * col_gap)
            cy = top_center_y + (r * row_gap)
            plus_groups.append(add_plus(
                f"{name_prefix}_{r}_{c}",
                cx,
                cy,
                size,
                thickness,
                z,
                frame_width,
                frame_height,
                sx,
                sy,
                material,
                collection,
            ))
    return plus_groups


def animate_plus_draw_lifecycle(
    plus_groups: Sequence[Sequence[Tuple[bpy.types.Object, float, float]]],
    total_frames: float,
    lifecycle_portion: float,
    seed: int,
) -> float:
    if not plus_groups:
        return 1.0

    start_frame = 1.0
    end_frame = max(start_frame + 0.001, float(total_frames))
    total_span = end_frame - start_frame
    clamped_lifecycle = max(1e-4, min(1.0, lifecycle_portion))
    per_plus_span = max(0.001, total_span * clamped_lifecycle)

    max_plus_start = max(start_frame, end_frame - per_plus_span)
    start_jitter_span = max(0.0, max_plus_start - start_frame)

    rng = random.Random(seed)
    latest_end = start_frame

    for group in plus_groups:
        if len(group) < 2:
            continue

        plus_start = start_frame if start_jitter_span <= 1e-6 else (start_frame + (rng.random() * start_jitter_span))
        first_stroke_idx = 0 if rng.random() < 0.5 else 1
        second_stroke_idx = 1 - first_stroke_idx

        first_obj, first_length, first_width = group[first_stroke_idx]
        second_obj, second_length, second_width = group[second_stroke_idx]

        first_start = plus_start
        first_end = plus_start + (per_plus_span * 0.5)
        second_start = first_end
        second_end = plus_start + per_plus_span

        animate_object_visible_at(first_obj, first_start)
        animate_object_visible_at(second_obj, second_start)

        animate_curve_draw_center_out_with_origin(
            obj=first_obj,
            line_length=first_length,
            start_frame=first_start,
            end_frame=first_end,
            origin_factor=rng.random(),
            initial_segment_px=max(0.001, first_width * 0.02),
        )
        animate_curve_draw_center_out_with_origin(
            obj=second_obj,
            line_length=second_length,
            start_frame=second_start,
            end_frame=second_end,
            origin_factor=rng.random(),
            initial_segment_px=max(0.001, second_width * 0.02),
        )

        latest_end = max(latest_end, second_end)

    return min(end_frame, latest_end)


def set_curve_draw_linear(obj: bpy.types.Object) -> None:
    curve_data = obj.data
    if not isinstance(curve_data, bpy.types.Curve):
        return
    if not curve_data.animation_data or not curve_data.animation_data.action:
        return
    action = curve_data.animation_data.action
    if not hasattr(action, "fcurves"):
        return
    for fcurve in action.fcurves:
        if fcurve.data_path not in {"bevel_factor_start", "bevel_factor_end"}:
            continue
        for key in fcurve.keyframe_points:
            key.interpolation = "LINEAR"


def animate_curve_draw(
    curve_objects: Sequence[bpy.types.Object],
    start_frame: float,
    end_frame: float,
) -> None:
    draw_end = max(start_frame + 0.001, end_frame)
    for obj in curve_objects:
        curve_data = obj.data
        if not isinstance(curve_data, bpy.types.Curve):
            continue
        curve_data.bevel_factor_mapping_end = "SPLINE"
        curve_data.bevel_factor_start = 0.0
        curve_data.bevel_factor_end = 0.0
        curve_data.keyframe_insert(data_path="bevel_factor_end", frame=start_frame)
        curve_data.bevel_factor_end = 1.0
        curve_data.keyframe_insert(data_path="bevel_factor_end", frame=draw_end)
        set_curve_draw_linear(obj)


def animate_curve_draw_sequential(
    curve_strokes: Sequence[Tuple[bpy.types.Object, float]],
    start_frame: float,
    end_frame: float,
) -> None:
    for obj, seg_start, seg_end in curve_draw_windows(curve_strokes, start_frame, end_frame):
        animate_curve_draw([obj], seg_start, seg_end)


def curve_draw_windows(
    curve_strokes: Sequence[Tuple[bpy.types.Object, float]],
    start_frame: float,
    end_frame: float,
) -> List[Tuple[bpy.types.Object, float, float]]:
    windows: List[Tuple[bpy.types.Object, float, float]] = []
    span = max(0.001, end_frame - start_frame)
    total_length = sum(max(0.0, length) for _, length in curve_strokes)
    if total_length <= 1e-9:
        for obj, _ in curve_strokes:
            windows.append((obj, start_frame, max(start_frame + 0.001, end_frame)))
        return windows

    cursor = start_frame
    for idx, (obj, length) in enumerate(curve_strokes):
        frac = max(0.0, length) / total_length
        segment_end = end_frame if idx == (len(curve_strokes) - 1) else (cursor + (span * frac))
        windows.append((obj, cursor, max(cursor + 0.001, segment_end)))
        cursor = segment_end
    return windows


def animate_curve_draw_randomized(
    curve_strokes: Sequence[Tuple[bpy.types.Object, float]],
    start_frame: float,
    end_frame: float,
    seed: int,
) -> None:
    if not curve_strokes:
        return
    shuffled = list(curve_strokes)
    rng = random.Random(seed)
    rng.shuffle(shuffled)
    animate_curve_draw_sequential(shuffled, start_frame, end_frame)


def animate_curve_draw_center_out_with_origin(
    obj: bpy.types.Object,
    line_length: float,
    start_frame: float,
    end_frame: float,
    origin_factor: float,
    initial_segment_px: float,
) -> None:
    curve_data = obj.data
    if not isinstance(curve_data, bpy.types.Curve):
        return

    draw_end = max(start_frame + 0.001, end_frame)
    center = max(0.0, min(1.0, origin_factor))
    dot_half_span = 0.0
    if line_length > 1e-6:
        # Tiny visible capsule at start approximates a circular dot.
        dot_half_span = min(0.49, max(1e-6, (initial_segment_px * 0.5) / line_length))

    start_factor = max(0.0, center - dot_half_span)
    end_factor = min(1.0, center + dot_half_span)
    left_span = center
    right_span = 1.0 - center
    max_span = max(left_span, right_span)
    min_span = min(left_span, right_span)

    # Animate both bevel factors so growth always exposes two rounded tips.
    curve_data.bevel_factor_mapping_start = "SPLINE"
    curve_data.bevel_factor_mapping_end = "SPLINE"
    curve_data.bevel_factor_start = start_factor
    curve_data.bevel_factor_end = end_factor
    curve_data.keyframe_insert(data_path="bevel_factor_start", frame=start_frame)
    curve_data.keyframe_insert(data_path="bevel_factor_end", frame=start_frame)

    if max_span > 1e-6 and min_span > 1e-6 and (min_span / max_span) < 0.999:
        hit_progress = min_span / max_span
        hit_frame = start_frame + ((draw_end - start_frame) * hit_progress)
        if left_span <= right_span:
            curve_data.bevel_factor_start = 0.0
            curve_data.bevel_factor_end = min(1.0, center + min_span)
        else:
            curve_data.bevel_factor_start = max(0.0, center - min_span)
            curve_data.bevel_factor_end = 1.0
        curve_data.keyframe_insert(data_path="bevel_factor_start", frame=hit_frame)
        curve_data.keyframe_insert(data_path="bevel_factor_end", frame=hit_frame)

    curve_data.bevel_factor_start = 0.0
    curve_data.bevel_factor_end = 1.0
    curve_data.keyframe_insert(data_path="bevel_factor_start", frame=draw_end)
    curve_data.keyframe_insert(data_path="bevel_factor_end", frame=draw_end)
    set_curve_draw_linear(obj)


def animate_curve_draw_center_out_random_origin(
    curve_strokes: Sequence[Tuple[bpy.types.Object, float]],
    start_frame: float,
    end_frame: float,
    seed: int,
) -> None:
    if not curve_strokes:
        return

    rng = random.Random(seed)
    for obj, line_length in curve_strokes:
        animate_curve_draw_center_out_with_origin(
            obj=obj,
            line_length=line_length,
            start_frame=start_frame,
            end_frame=end_frame,
            origin_factor=rng.random(),
            initial_segment_px=max(0.001, HATCH_LINE_WIDTH_PX * 0.02),
        )


def animate_object_visible_at(obj: bpy.types.Object, visible_frame: float) -> None:
    frame_show = max(1.0, float(visible_frame))
    frame_hidden = max(1.0, frame_show - 0.001)

    obj.hide_render = True
    obj.keyframe_insert(data_path="hide_render", frame=1.0)
    obj.keyframe_insert(data_path="hide_render", frame=frame_hidden)
    obj.hide_render = False
    obj.keyframe_insert(data_path="hide_render", frame=frame_show)

    if obj.animation_data and obj.animation_data.action and hasattr(obj.animation_data.action, "fcurves"):
        for fcurve in obj.animation_data.action.fcurves:
            if fcurve.data_path != "hide_render":
                continue
            for key in fcurve.keyframe_points:
                key.interpolation = "CONSTANT"


def frame_from_progress(total_frames: float, progress: float) -> float:
    clamped = max(0.0, min(1.0, progress))
    span = max(1.0, total_frames) - 1.0
    return 1.0 + (span * clamped)


def set_layer_visibility(background_coll: bpy.types.Collection, overlay_coll: bpy.types.Collection, *,
                         show_background: bool, show_overlay: bool) -> None:
    background_coll.hide_render = not show_background
    overlay_coll.hide_render = not show_overlay


def render_still(scene: bpy.types.Scene, output_path: Path, transparent: bool = True) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    scene.render.film_transparent = transparent
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.filepath = str(output_path)
    bpy.ops.render.render(write_still=True)


def render_sequence(
    scene: bpy.types.Scene,
    sequence_dir: Path,
    prefix: str,
    transparent: bool,
) -> Path:
    sequence_dir.mkdir(parents=True, exist_ok=True)
    for stale_frame in sequence_dir.glob(f"{prefix}*.png"):
        stale_frame.unlink()
    scene.render.film_transparent = transparent
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.use_overwrite = True
    scene.render.filepath = str(sequence_dir / prefix)
    bpy.ops.render.render(animation=True)
    return sequence_dir / f"{prefix}%04d.png"


def run_ffmpeg(cmd: Sequence[str]) -> None:
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.decode("utf-8", errors="replace")
        raise RuntimeError(f"ffmpeg encode failed:\n{stderr}") from exc


def detect_sequence_start_number(sequence_pattern: Path) -> int:
    prefix = sequence_pattern.name.split("%", 1)[0]
    candidates: List[int] = []
    frame_re = re.compile(r"^(\d+)$")
    for candidate in sequence_pattern.parent.glob(f"{prefix}*.png"):
        suffix = candidate.stem[len(prefix):]
        if not frame_re.match(suffix):
            continue
        candidates.append(int(suffix))
    if not candidates:
        raise RuntimeError(f"No image sequence frames found for pattern '{sequence_pattern}'.")
    return min(candidates)


def encode_mp4(sequence_pattern: Path, fps: int, output_path: Path) -> None:
    ffmpeg_bin = shutil.which("ffmpeg")
    if not ffmpeg_bin:
        raise RuntimeError("ffmpeg not found on PATH.")

    start_number = detect_sequence_start_number(sequence_pattern)
    cmd = [
        ffmpeg_bin,
        "-y",
        "-framerate",
        str(fps),
        "-start_number",
        str(start_number),
        "-i",
        str(sequence_pattern),
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv444p",
        str(output_path),
    ]
    run_ffmpeg(cmd)


def encode_webm_alpha(sequence_pattern: Path, fps: int, output_path: Path) -> None:
    ffmpeg_bin = shutil.which("ffmpeg")
    if not ffmpeg_bin:
        raise RuntimeError("ffmpeg not found on PATH.")

    start_number = detect_sequence_start_number(sequence_pattern)
    cmd = [
        ffmpeg_bin,
        "-y",
        "-framerate",
        str(fps),
        "-start_number",
        str(start_number),
        "-i",
        str(sequence_pattern),
        "-c:v",
        "libvpx-vp9",
        "-pix_fmt",
        "yuva420p",
        "-auto-alt-ref",
        "0",
        str(output_path),
    ]
    run_ffmpeg(cmd)


def build_layers(
    frame_width: int,
    frame_height: int,
    sx: float,
    sy: float,
    background_coll: bpy.types.Collection,
    overlay_coll: bpy.types.Collection,
    animation_total_frames: float,
) -> float:
    blue_back_mat = make_flat_material("BlueBackMat", hex_to_rgba(LIGHT_BLUE_PROFILE_PHOTO_HEX, 0.17))
    blue_foreground_mat = make_flat_material("BlueForegroundMat", hex_to_rgba(DARK_BLUE_PROFILE_PHOTO_HEX, 1.0))
    white_mat = make_flat_material("WhiteMat", hex_to_rgba("ffffff", 1.0))
    red_mat = make_flat_material("RedMat", hex_to_rgba(RED_PROFILE_PHOTO_HEX, 1.0))
    main_gradient_mat = make_horizontal_gradient_material("MainGradientMat")
    warm_glow_mat = make_image_glow_material(
        "WarmGlowMat",
        color_hex="c14d63",
        image_name="HeadshotWarmGlow",
        alpha_scale=0.09,
    )
    dark_glow_mat = make_image_glow_material(
        "DarkGlowMat",
        color_hex="1d2038",
        image_name="HeadshotDarkGlow",
        alpha_scale=0.11,
    )

    # Backdrop layer (pure card/background accents, no front decoration).
    add_rounded_rect(
        "MainPanel",
        MAIN_RECT["left"],
        MAIN_RECT["top"],
        MAIN_RECT["right"],
        MAIN_RECT["bottom"],
        PROFILE_PHOTO_PANEL_CORNER_RADIUS,
        -0.20,
        frame_width,
        frame_height,
        sx,
        sy,
        main_gradient_mat,
        background_coll,
    )

    add_rounded_rect(
        "BlueBackPlate",
        BLUE_BACK["left"] + X_OFFSET_BLUE_SQUARE_PROFILE_PHOTO,
        BLUE_BACK["top"] + Y_OFFSET_BLUE_PROFILE_PHOTO,
        BLUE_BACK["right"] + X_OFFSET_BLUE_SQUARE_PROFILE_PHOTO,
        BLUE_BACK["bottom"] + Y_OFFSET_BLUE_PROFILE_PHOTO,
        PROFILE_PHOTO_PANEL_CORNER_RADIUS,
        -0.24,
        frame_width,
        frame_height,
        sx,
        sy,
        blue_back_mat,
        background_coll,
    )

    # Top-left icon (outline corner family).
    top_left_strokes = add_corner_outline_icon(
        "TopLeftIcon",
        cx=39,
        cy=141,
        inner_radius=73,
        outer_radius=111,
        stroke_width=3,
        segments=64,
        z=-0.05,
        frame_width=frame_width,
        frame_height=frame_height,
        sx=sx,
        sy=sy,
        material=white_mat,
        collection=overlay_coll,
    )

    # Bottom-right icon: same family, scaled larger; behind red panel, above blue backplate.
    bottom_right_strokes = add_corner_outline_icon(
        "BottomRightIcon",
        cx=887,
        cy=832,
        inner_radius=73,
        outer_radius=111,
        stroke_width=3,
        segments=72,
        z=-0.22,
        frame_width=frame_width,
        frame_height=frame_height,
        sx=sx,
        sy=sy,
        material=red_mat,
        collection=background_coll,
    )

    # Plus grids.
    white_pluses = add_plus_grid(
        "WhitePlus",
        left_center_x=839.5,
        top_center_y=MAIN_RECT["top"] + WHITE_PLUS_TOP_CENTER_OFFSET_FROM_RED_PANEL_PX,
        cols=2,
        rows=7,
        col_gap=WHITE_PLUS_COL_GAP_PX,
        row_gap=WHITE_PLUS_ROW_GAP_PX,
        size=WHITE_PLUS_SIZE_PX,
        thickness=WHITE_PLUS_THICKNESS_PX,
        z=-0.05,
        frame_width=frame_width,
        frame_height=frame_height,
        sx=sx,
        sy=sy,
        material=white_mat,
        collection=overlay_coll,
    )

    blue_pluses = add_plus_grid(
        "BluePlus",
        left_center_x=947.0,
        top_center_y=MAIN_RECT["top"] + BLUE_PLUS_TOP_CENTER_OFFSET_FROM_RED_PANEL_PX,
        cols=2,
        rows=7,
        col_gap=BLUE_PLUS_COL_GAP_PX,
        row_gap=BLUE_PLUS_ROW_GAP_PX,
        size=BLUE_PLUS_SIZE_PX,
        thickness=BLUE_PLUS_THICKNESS_PX,
        z=-0.05,
        frame_width=frame_width,
        frame_height=frame_height,
        sx=sx,
        sy=sy,
        material=blue_foreground_mat,
        collection=overlay_coll,
    )

    all_pluses = white_pluses + blue_pluses
    animate_plus_draw_lifecycle(
        all_pluses,
        total_frames=animation_total_frames,
        lifecycle_portion=LIFECYCLE_OF_PLUS_ANIMATION_AS_PORTION_OF_TOTAL_ANIMATION,
        seed=PLUS_ANIMATION_RANDOM_SEED,
    )

    curve_draw_start_frame = 1.0
    curve_draw_end_frame = max(1.001, animation_total_frames)
    animate_curve_draw_sequential(top_left_strokes, start_frame=curve_draw_start_frame, end_frame=curve_draw_end_frame)
    animate_curve_draw_sequential(bottom_right_strokes, start_frame=curve_draw_start_frame, end_frame=curve_draw_end_frame)

    # Hatch line-segment block with per-corner radii and rounded line caps.
    hatch_height = HATCH_BLOCK_BOTTOM - HATCH_BLOCK_TOP
    hatch_shape = rounded_rect_per_corner_points_screen(
        HATCH_BLOCK_LEFT,
        HATCH_BLOCK_TOP,
        HATCH_BLOCK_RIGHT,
        HATCH_BLOCK_BOTTOM,
        radius_top_left=HATCH_BLOCK_RADIUS_TOP_LEFT_PX,
        radius_top_right=hatch_height * HATCH_BLOCK_RADIUS_TOP_RIGHT_HEIGHT_RATIO,
        radius_bottom_right=hatch_height * HATCH_BLOCK_RADIUS_BOTTOM_RIGHT_HEIGHT_RATIO,
        radius_bottom_left=HATCH_BLOCK_RADIUS_BOTTOM_LEFT_PX,
        segments=HATCH_BLOCK_CORNER_SEGMENTS,
    )

    hatch_segments = hatch_segments_in_polygon_screen(
        hatch_shape,
        spacing_px=HATCH_LINE_SPACING_PX,
        line_angle_deg=HATCH_LINE_ANGLE_DEG,
        endpoint_inset_px=HATCH_LINE_ENDPOINT_INSET_PX,
    )
    hatch_strokes: List[Tuple[bpy.types.Object, float]] = []
    for idx, (seg_start, seg_end, seg_len) in enumerate(hatch_segments):
        if seg_len <= max(1.0, HATCH_LINE_WIDTH_PX):
            continue

        line_obj = add_polyline_stroke_curve(
            name=f"BottomLeftHatchLine_{idx:03d}",
            points_screen=[seg_start, seg_end],
            stroke_width=HATCH_LINE_WIDTH_PX,
            z=-0.05,
            frame_width=frame_width,
            frame_height=frame_height,
            sx=sx,
            sy=sy,
            segments=2,
            material=blue_foreground_mat,
            collection=overlay_coll,
        )
        hatch_strokes.append((line_obj, seg_len))

    hatch_start_frame = frame_from_progress(animation_total_frames, HATCH_DRAW_START_PROGRESS)
    hatch_end_frame = frame_from_progress(animation_total_frames, HATCH_DRAW_END_PROGRESS)
    animate_curve_draw_center_out_random_origin(
        hatch_strokes,
        start_frame=hatch_start_frame,
        end_frame=hatch_end_frame,
        seed=HATCH_DRAW_ORIGIN_SEED,
    )

    # Subject lighting overlays on top layer.
    add_ellipse_glow(
        "WarmGlow",
        cx=180,
        cy=804,
        rx=292,
        ry=250,
        z=-0.056,
        frame_width=frame_width,
        frame_height=frame_height,
        sx=sx,
        sy=sy,
        material=warm_glow_mat,
        collection=overlay_coll,
    )
    add_ellipse_glow(
        "DarkGlow",
        cx=628,
        cy=726,
        rx=312,
        ry=268,
        z=-0.055,
        frame_width=frame_width,
        frame_height=frame_height,
        sx=sx,
        sy=sy,
        material=dark_glow_mat,
        collection=overlay_coll,
    )
    return animation_total_frames



def main() -> None:
    args = parse_blender_args()
    clear_scene()
    scene = setup_scene(args.frame_width, args.frame_height, args.fps, args.duration_seconds)
    add_camera(args.frame_width)

    sx = args.frame_width / BASE_WIDTH
    sy = args.frame_height / BASE_HEIGHT
    animation_total_frames = float(max(1, int(round(args.fps * args.duration_seconds))))

    bg_coll = ensure_collection("HeadshotBackdrop")
    fg_coll = ensure_collection("HeadshotOverlay")
    build_layers(args.frame_width, args.frame_height, sx, sy, bg_coll, fg_coll, animation_total_frames)
    scene.frame_end = int(animation_total_frames)
    scene.frame_current = scene.frame_end

    out_dir = args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    # Backdrop still.
    set_layer_visibility(bg_coll, fg_coll, show_background=True, show_overlay=False)
    backdrop_still_path = out_dir / args.backdrop_still_name
    render_still(scene, backdrop_still_path, transparent=True)

    # Overlay still.
    set_layer_visibility(bg_coll, fg_coll, show_background=False, show_overlay=True)
    overlay_still_path = out_dir / args.overlay_still_name
    render_still(scene, overlay_still_path, transparent=True)

    if not args.skip_video:
        # Backdrop video (alpha).
        set_layer_visibility(bg_coll, fg_coll, show_background=True, show_overlay=False)
        backdrop_seq_dir = out_dir / "headshot-bg-backdrop_frames"
        backdrop_pattern = render_sequence(scene, backdrop_seq_dir, "frame_", transparent=True)
        encode_webm_alpha(backdrop_pattern, args.fps, out_dir / args.backdrop_video_webm_name)

        # Overlay video (alpha + mp4 fallback).
        set_layer_visibility(bg_coll, fg_coll, show_background=False, show_overlay=True)
        overlay_seq_dir = out_dir / "headshot-bg-overlay_frames"
        overlay_pattern = render_sequence(scene, overlay_seq_dir, "frame_", transparent=True)
        encode_webm_alpha(overlay_pattern, args.fps, out_dir / args.overlay_video_webm_name)
        encode_mp4(overlay_pattern, args.fps, out_dir / args.overlay_video_mp4_name)

        if not args.keep_frame_sequence:
            shutil.rmtree(backdrop_seq_dir, ignore_errors=True)
            shutil.rmtree(overlay_seq_dir, ignore_errors=True)

    print(f"Rendered backdrop still: {backdrop_still_path.resolve()}")
    print(f"Rendered overlay still: {overlay_still_path.resolve()}")
    if not args.skip_video:
        print(f"Rendered backdrop webm: {(out_dir / args.backdrop_video_webm_name).resolve()}")
        print(f"Rendered overlay webm: {(out_dir / args.overlay_video_webm_name).resolve()}")
        print(f"Rendered overlay mp4: {(out_dir / args.overlay_video_mp4_name).resolve()}")


if __name__ == "__main__":
    main()
