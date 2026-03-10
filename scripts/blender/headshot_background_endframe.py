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
MAIN_RECT = {"left": 24, "top": 130, "right": 914, "bottom": 964, "radius": 6}
# Blue plate base geometry before profile-photo offset is applied.
BLUE_BACK = {"left": 24, "top": 130, "right": 928, "bottom": 974, "radius": 0}
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
PROFILE_PHOTO_ANIMATION_DURATION_SECONDS = 10.0 # 10 seconds requires 240 frames

# Hatch tuning (in screen-pixel units for the ortho camera setup).
HATCH_LINE_WIDTH_PX = 4.0
HATCH_LINE_SPACING_PX = 15.0


def parse_blender_args() -> argparse.Namespace:
    raw = sys.argv
    tail = raw[raw.index("--") + 1:] if "--" in raw else []

    parser = argparse.ArgumentParser(description="Render layered headshot decorative assets.")
    parser.add_argument("--output-dir", type=Path, default=Path("public/generated/headshot-bg"))
    parser.add_argument("--frame-width", type=int, default=BASE_WIDTH)
    parser.add_argument("--frame-height", type=int, default=BASE_HEIGHT)
    parser.add_argument("--fps", type=int, default=24)
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


def ensure_hatch_pattern_image(name: str, size: int = 128, line_px: int = 4, gap_px: int = 30) -> bpy.types.Image:
    existing = bpy.data.images.get(name)
    if existing and existing.size[0] == size and existing.size[1] == size:
        return existing
    if existing:
        bpy.data.images.remove(existing)

    img = bpy.data.images.new(name=name, width=size, height=size, alpha=True)
    pixels = [0.0] * (size * size * 4)
    period = max(1, line_px + gap_px)

    for y in range(size):
        for x in range(size):
            idx = (y * size + x) * 4
            # Keep stripes at a true 45deg in texture space.
            active = ((x - y) % period) < line_px
            alpha = 1.0 if active else 0.0
            pixels[idx + 0] = 1.0
            pixels[idx + 1] = 1.0
            pixels[idx + 2] = 1.0
            pixels[idx + 3] = alpha

    img.pixels.foreach_set(pixels)
    img.pack()
    return img


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


def make_hatch_material(name: str) -> bpy.types.Material:
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
    separate = nodes.new(type="ShaderNodeSeparateXYZ")
    stripe_axis = nodes.new(type="ShaderNodeMath")
    period_div = nodes.new(type="ShaderNodeMath")
    frac = nodes.new(type="ShaderNodeMath")
    stripe_mask = nodes.new(type="ShaderNodeMath")

    # Use object space to avoid UV seams and keep line direction stable.
    mapping.inputs["Scale"].default_value = (1.0, 1.0, 1.0)
    stripe_axis.operation = "SUBTRACT"  # x - y => 45deg up-right stripes.

    # Pixel-like spacing because 1 world unit == 1 screen pixel in this ortho setup.
    line_px = HATCH_LINE_WIDTH_PX
    period_px = max(line_px + 1.0, HATCH_LINE_SPACING_PX)
    period_div.operation = "DIVIDE"
    period_div.inputs[1].default_value = period_px

    frac.operation = "FRACT"
    stripe_mask.operation = "LESS_THAN"
    stripe_mask.inputs[1].default_value = line_px / period_px

    emission.inputs["Color"].default_value = hex_to_rgba(DARK_BLUE_PROFILE_PHOTO_HEX, 1.0)
    emission.inputs["Strength"].default_value = 1.0

    links.new(tex_coord.outputs["Object"], mapping.inputs["Vector"])
    links.new(mapping.outputs["Vector"], separate.inputs["Vector"])
    links.new(separate.outputs["X"], stripe_axis.inputs[0])
    links.new(separate.outputs["Y"], stripe_axis.inputs[1])
    links.new(stripe_axis.outputs["Value"], period_div.inputs[0])
    links.new(period_div.outputs["Value"], frac.inputs[0])
    links.new(frac.outputs["Value"], stripe_mask.inputs[0])
    links.new(stripe_mask.outputs["Value"], mix.inputs["Fac"])
    links.new(transparent.outputs["BSDF"], mix.inputs[1])
    links.new(emission.outputs["Emission"], mix.inputs[2])
    links.new(mix.outputs["Shader"], out.inputs["Surface"])

    return mat


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
) -> List[bpy.types.Object]:
    half = size * 0.5
    half_t = thickness * 0.5
    r = thickness * 0.5

    vert = add_rounded_rect(
        f"{name_prefix}Vert",
        cx - half_t,
        cy - half,
        cx + half_t,
        cy + half,
        r,
        z,
        frame_width,
        frame_height,
        sx,
        sy,
        material,
        collection,
        origin_screen=(cx, cy),
    )

    horz = add_rounded_rect(
        f"{name_prefix}Horz",
        cx - half,
        cy - half_t,
        cx + half,
        cy + half_t,
        r,
        z,
        frame_width,
        frame_height,
        sx,
        sy,
        material,
        collection,
        origin_screen=(cx, cy),
    )

    return [vert, horz]


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
) -> List[List[bpy.types.Object]]:
    plus_groups: List[List[bpy.types.Object]] = []
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


def set_bezier_scale_curves(obj: bpy.types.Object) -> None:
    if not obj.animation_data or not obj.animation_data.action:
        return
    action = obj.animation_data.action
    if not hasattr(action, "fcurves"):
        return
    for fcurve in action.fcurves:
        if fcurve.data_path != "scale":
            continue
        for key in fcurve.keyframe_points:
            key.interpolation = "BEZIER"
            key.handle_left_type = "AUTO_CLAMPED"
            key.handle_right_type = "AUTO_CLAMPED"


def animate_plus_pop(
    plus_groups: Sequence[Sequence[bpy.types.Object]],
    cols: int,
    start_frame: float,
    row_delay: float,
    col_delay: float,
    pop_duration: float,
    settle_duration: float,
    overshoot: float = 1.16,
) -> None:
    hidden = 0.001
    for idx, group in enumerate(plus_groups):
        row = idx // cols
        col = idx % cols
        f0 = start_frame + (row * row_delay) + (col * col_delay)
        f1 = f0 + pop_duration
        f2 = f1 + settle_duration
        for obj in group:
            obj.scale = (hidden, hidden, 1.0)
            obj.keyframe_insert(data_path="scale", frame=1.0)
            obj.scale = (hidden, hidden, 1.0)
            obj.keyframe_insert(data_path="scale", frame=f0)
            obj.scale = (overshoot, overshoot, 1.0)
            obj.keyframe_insert(data_path="scale", frame=f1)
            obj.scale = (1.0, 1.0, 1.0)
            obj.keyframe_insert(data_path="scale", frame=f2)
            set_bezier_scale_curves(obj)


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
        if fcurve.data_path != "bevel_factor_end":
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
    span = max(0.001, end_frame - start_frame)
    total_length = sum(max(0.0, length) for _, length in curve_strokes)
    if total_length <= 1e-9:
        animate_curve_draw([obj for obj, _ in curve_strokes], start_frame, end_frame)
        return

    cursor = start_frame
    for idx, (obj, length) in enumerate(curve_strokes):
        frac = max(0.0, length) / total_length
        segment_end = end_frame if idx == (len(curve_strokes) - 1) else (cursor + (span * frac))
        animate_curve_draw([obj], cursor, max(cursor + 0.001, segment_end))
        cursor = segment_end


def plus_pop_completion_frame(
    cols: int,
    rows: int,
    start_frame: float,
    row_delay: float,
    col_delay: float,
    pop_duration: float,
    settle_duration: float,
) -> float:
    return (
        start_frame
        + ((rows - 1) * row_delay)
        + ((cols - 1) * col_delay)
        + pop_duration
        + settle_duration
    )


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
    scene.render.film_transparent = transparent
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.filepath = str(sequence_dir / prefix)
    bpy.ops.render.render(animation=True)
    return sequence_dir / f"{prefix}%04d.png"


def run_ffmpeg(cmd: Sequence[str]) -> None:
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.decode("utf-8", errors="replace")
        raise RuntimeError(f"ffmpeg encode failed:\n{stderr}") from exc


def encode_mp4(sequence_pattern: Path, fps: int, output_path: Path) -> None:
    ffmpeg_bin = shutil.which("ffmpeg")
    if not ffmpeg_bin:
        raise RuntimeError("ffmpeg not found on PATH.")

    cmd = [
        ffmpeg_bin,
        "-y",
        "-framerate",
        str(fps),
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

    cmd = [
        ffmpeg_bin,
        "-y",
        "-framerate",
        str(fps),
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
    hatch_mat = make_hatch_material("HatchMat")
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
        MAIN_RECT["radius"],
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
        BLUE_BACK["radius"],
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
        top_center_y=336.0,
        cols=2,
        rows=7,
        col_gap=39.0,
        row_gap=38.5,
        size=26,
        thickness=6,
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
        top_center_y=451.5,
        cols=2,
        rows=7,
        col_gap=38.5,
        row_gap=38.5,
        size=29,
        thickness=7,
        z=-0.05,
        frame_width=frame_width,
        frame_height=frame_height,
        sx=sx,
        sy=sy,
        material=blue_foreground_mat,
        collection=overlay_coll,
    )

    base_white_plus_pop = {
        "cols": 2,
        "rows": 7,
        "start_frame": 2.0,
        "row_delay": 0.84,
        "col_delay": 0.22,
        "pop_duration": 4.6,
        "settle_duration": 2.5,
        "overshoot": 1.16,
    }
    base_blue_plus_pop = {
        "cols": 2,
        "rows": 7,
        "start_frame": 3.1,
        "row_delay": 0.84,
        "col_delay": 0.22,
        "pop_duration": 4.6,
        "settle_duration": 2.5,
        "overshoot": 1.14,
    }

    base_plus_end_frame = max(
        plus_pop_completion_frame(
            cols=base_white_plus_pop["cols"],
            rows=base_white_plus_pop["rows"],
            start_frame=base_white_plus_pop["start_frame"],
            row_delay=base_white_plus_pop["row_delay"],
            col_delay=base_white_plus_pop["col_delay"],
            pop_duration=base_white_plus_pop["pop_duration"],
            settle_duration=base_white_plus_pop["settle_duration"],
        ),
        plus_pop_completion_frame(
            cols=base_blue_plus_pop["cols"],
            rows=base_blue_plus_pop["rows"],
            start_frame=base_blue_plus_pop["start_frame"],
            row_delay=base_blue_plus_pop["row_delay"],
            col_delay=base_blue_plus_pop["col_delay"],
            pop_duration=base_blue_plus_pop["pop_duration"],
            settle_duration=base_blue_plus_pop["settle_duration"],
        ),
    )
    time_scale = animation_total_frames / max(1e-6, base_plus_end_frame)

    white_plus_pop = {
        "cols": base_white_plus_pop["cols"],
        "rows": base_white_plus_pop["rows"],
        "start_frame": base_white_plus_pop["start_frame"] * time_scale,
        "row_delay": base_white_plus_pop["row_delay"] * time_scale,
        "col_delay": base_white_plus_pop["col_delay"] * time_scale,
        "pop_duration": base_white_plus_pop["pop_duration"] * time_scale,
        "settle_duration": base_white_plus_pop["settle_duration"] * time_scale,
        "overshoot": base_white_plus_pop["overshoot"],
    }
    blue_plus_pop = {
        "cols": base_blue_plus_pop["cols"],
        "rows": base_blue_plus_pop["rows"],
        "start_frame": base_blue_plus_pop["start_frame"] * time_scale,
        "row_delay": base_blue_plus_pop["row_delay"] * time_scale,
        "col_delay": base_blue_plus_pop["col_delay"] * time_scale,
        "pop_duration": base_blue_plus_pop["pop_duration"] * time_scale,
        "settle_duration": base_blue_plus_pop["settle_duration"] * time_scale,
        "overshoot": base_blue_plus_pop["overshoot"],
    }

    animate_plus_pop(
        white_pluses,
        cols=white_plus_pop["cols"],
        start_frame=white_plus_pop["start_frame"],
        row_delay=white_plus_pop["row_delay"],
        col_delay=white_plus_pop["col_delay"],
        pop_duration=white_plus_pop["pop_duration"],
        settle_duration=white_plus_pop["settle_duration"],
        overshoot=white_plus_pop["overshoot"],
    )
    animate_plus_pop(
        blue_pluses,
        cols=blue_plus_pop["cols"],
        start_frame=blue_plus_pop["start_frame"],
        row_delay=blue_plus_pop["row_delay"],
        col_delay=blue_plus_pop["col_delay"],
        pop_duration=blue_plus_pop["pop_duration"],
        settle_duration=blue_plus_pop["settle_duration"],
        overshoot=blue_plus_pop["overshoot"],
    )

    plus_end_frame = max(
        plus_pop_completion_frame(
            cols=white_plus_pop["cols"],
            rows=white_plus_pop["rows"],
            start_frame=white_plus_pop["start_frame"],
            row_delay=white_plus_pop["row_delay"],
            col_delay=white_plus_pop["col_delay"],
            pop_duration=white_plus_pop["pop_duration"],
            settle_duration=white_plus_pop["settle_duration"],
        ),
        plus_pop_completion_frame(
            cols=blue_plus_pop["cols"],
            rows=blue_plus_pop["rows"],
            start_frame=blue_plus_pop["start_frame"],
            row_delay=blue_plus_pop["row_delay"],
            col_delay=blue_plus_pop["col_delay"],
            pop_duration=blue_plus_pop["pop_duration"],
            settle_duration=blue_plus_pop["settle_duration"],
        ),
    )

    curve_draw_start_frame = 1.0 * time_scale
    animate_curve_draw_sequential(top_left_strokes, start_frame=curve_draw_start_frame, end_frame=plus_end_frame)
    animate_curve_draw_sequential(bottom_right_strokes, start_frame=curve_draw_start_frame, end_frame=plus_end_frame)

    # Hatch block: right corners are 50% (capsule end), lower-left stays smaller.
    hatch_top = 836
    hatch_bottom = 1007
    hatch_height = hatch_bottom - hatch_top
    hatch_shape = hatch_block_points_screen(
        0,
        hatch_top,
        450,
        hatch_bottom,
        right_radius=hatch_height * 0.5,
        lower_left_radius=70,
        segments=30,
    )
    add_polygon_object(
        "BottomLeftHatch",
        hatch_shape,
        -0.05,
        frame_width,
        frame_height,
        sx,
        sy,
        hatch_mat,
        overlay_coll,
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
    return plus_end_frame



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
