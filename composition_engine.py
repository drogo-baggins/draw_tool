"""
Composition engine for assembling SVG assets from the component library into final SVG output.

Composes pre-designed SVG components (shapes, people, icons) into a complete SVG document
based on a JSON composition specification produced by the LLM. Handles element placement
with scaling, connection routing (straight, orthogonal, curved), arrow markers, and text elements.

Usage:
    engine = CompositionEngine()
    svg_string = engine.compose(composition_json)
"""

import json
import logging
import math
import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Default component library path relative to this file
DEFAULT_LIBRARY_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "component_library"
)

# Default anchors for components that don't define their own
DEFAULT_ANCHORS = {
    "top": {"x": 0.5, "y": 0.0},
    "right": {"x": 1.0, "y": 0.5},
    "bottom": {"x": 0.5, "y": 1.0},
    "left": {"x": 0.0, "y": 0.5},
    "center": {"x": 0.5, "y": 0.5},
}


class CompositionEngine:
    """Composes SVG assets from the component library into a final SVG document."""

    def __init__(self, library_path: Optional[str] = None):
        self._library_path = library_path or DEFAULT_LIBRARY_PATH
        self._manifest: dict = {}
        self._components: dict = {}  # id -> component metadata from manifest
        self._svg_cache: dict = {}  # component_id -> raw SVG string

        self._load_manifest()

    def compose(self, composition: dict) -> str:
        """Compose a complete SVG document from a JSON composition specification.

        Args:
            composition: Dict matching the composition JSON schema with
                         ``canvas``, ``elements``, and ``connections`` keys.

        Returns:
            A complete SVG 1.1 document string.
        """
        canvas = composition.get("canvas", {})
        width = _safe_float(canvas.get("width", 800), 800)
        height = _safe_float(canvas.get("height", 600), 600)
        background = _sanitize_attr(canvas.get("background", "#ffffff"))

        w_str = str(int(width)) if width == int(width) else str(width)
        h_str = str(int(height)) if height == int(height) else str(height)

        elements = composition.get("elements", [])
        connections = composition.get("connections", [])

        # Build element map for connection resolution
        elements_map: dict = {}
        svg_parts: list[str] = []
        defs_parts: list[str] = []

        # Place elements
        for elem in elements:
            elem_id = elem.get("id")
            if elem_id:
                elements_map[elem_id] = elem
            self._place_element(elem, svg_parts, defs_parts)

        # Route connections
        for conn in connections:
            self._route_connection(conn, elements_map, svg_parts, defs_parts)

        # Assemble final SVG
        defs_block = ""
        if defs_parts:
            defs_block = (
                "  <defs>\n"
                + "\n".join(f"    {d}" for d in defs_parts)
                + "\n  </defs>\n"
            )

        body = "\n".join(f"  {p}" for p in svg_parts)

        svg = (
            f'<svg width="{w_str}" height="{h_str}" '
            f'viewBox="0 0 {w_str} {h_str}" '
            f'xmlns="http://www.w3.org/2000/svg">\n'
            f'  <rect width="100%" height="100%" fill="{background}"/>\n'
            f"{defs_block}"
            f"{body}\n"
            f"</svg>"
        )
        return svg

    def get_component_summary(self) -> str:
        """Return a human-readable component list for LLM prompt injection."""
        lines: list[str] = []
        lines.append("Available components:")
        lines.append("")

        categories: dict[str, list[dict]] = {}
        for comp in self._manifest.get("components", []):
            cat = comp.get("category", "other")
            categories.setdefault(cat, []).append(comp)

        for cat in sorted(categories.keys()):
            lines.append(f"## {cat.upper()}")
            for comp in categories[cat]:
                anchor_names = list(comp.get("anchors", {}).keys())
                lines.append(
                    f"  - id: {comp['id']}  name: {comp['name']}  "
                    f"size: {comp.get('default_width', '?')}x{comp.get('default_height', '?')}  "
                    f"anchors: {', '.join(anchor_names)}  "
                    f"tags: {', '.join(comp.get('tags', []))}"
                )
            lines.append("")

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Manifest & SVG loading
    # ------------------------------------------------------------------

    def _load_manifest(self) -> dict:
        """Load and index the component library manifest."""
        manifest_path = os.path.join(self._library_path, "manifest.json")
        if not os.path.exists(manifest_path):
            logger.warning(
                "Component library manifest not found at %s; "
                "composition will work without pre-built components",
                manifest_path,
            )
            self._manifest = {"components": []}
            return self._manifest

        with open(manifest_path, "r", encoding="utf-8") as f:
            self._manifest = json.load(f)

        for comp in self._manifest.get("components", []):
            self._components[comp["id"]] = comp

        logger.info(
            "Loaded component library manifest: %d components",
            len(self._components),
        )
        return self._manifest

    def _load_svg_content(self, component_id: str) -> Optional[str]:
        """Load the SVG file content for a component, using a cache.

        Returns:
            The raw SVG file contents, or ``None`` if the component or file
            is not found.
        """
        if component_id in self._svg_cache:
            return self._svg_cache[component_id]

        comp = self._components.get(component_id)
        if not comp:
            logger.warning("Unknown component_id: %s", component_id)
            return None

        svg_path = os.path.join(self._library_path, comp["file"])
        if not os.path.exists(svg_path):
            logger.warning(
                "SVG file not found for component %s: %s", component_id, svg_path
            )
            return None

        with open(svg_path, "r", encoding="utf-8") as f:
            content = f.read()

        self._svg_cache[component_id] = content
        return content

    # ------------------------------------------------------------------
    # Element placement
    # ------------------------------------------------------------------

    def _place_element(self, element: dict, svg_parts: list, defs_parts: list) -> None:
        """Place a component or text element into the SVG output."""
        elem_type = element.get("type", "component")

        if elem_type == "text":
            self._place_text(element, svg_parts)
        else:
            self._place_component(element, svg_parts, defs_parts)

    def _place_component(
        self, element: dict, svg_parts: list, defs_parts: list
    ) -> None:
        """Load an SVG component and place it at the specified position and size."""
        component_id = element.get("component_id")
        if not component_id:
            logger.warning(
                "Element missing component_id, skipping: %s", element.get("id")
            )
            return

        svg_content = self._load_svg_content(component_id)
        if svg_content is None:
            return

        x = _safe_float(element.get("x", 0))
        y = _safe_float(element.get("y", 0))
        comp = self._components.get(component_id, {})
        target_w = _safe_float(
            element.get("width", comp.get("default_width", 100)), 100
        )
        target_h = _safe_float(
            element.get("height", comp.get("default_height", 100)), 100
        )

        # Parse viewBox from the SVG to determine native dimensions
        vb_w, vb_h = self._parse_viewbox(svg_content, target_w, target_h)
        scale_x = target_w / vb_w if vb_w else 1
        scale_y = target_h / vb_h if vb_h else 1

        # Extract inner content (everything between <svg ...> and </svg>)
        inner = self._extract_svg_inner(svg_content)

        # Build the placed group
        parts: list[str] = []

        # Optional fill background rect
        fill = element.get("fill")
        if fill:
            parts.append(
                f'<rect width="{vb_w}" height="{vb_h}" rx="8" ry="8" fill="{_sanitize_attr(fill)}"/>'
            )

        parts.append(inner)

        group = (
            f'<g transform="translate({x},{y}) scale({scale_x},{scale_y})">'
            + "".join(parts)
            + "</g>"
        )
        svg_parts.append(group)

        # Optional label centered on element
        label = element.get("label")
        if label:
            text_x = x + target_w / 2
            text_y = y + target_h / 2
            svg_parts.append(
                f'<text x="{text_x}" y="{text_y}" text-anchor="middle" '
                f'dominant-baseline="central" font-family="sans-serif" '
                f'font-size="14" fill="#ffffff">{_escape_xml(label)}</text>'
            )

    def _place_text(self, element: dict, svg_parts: list) -> None:
        """Create an SVG ``<text>`` element from a text specification."""
        content = element.get("content", "")
        x = _safe_float(element.get("x", 0))
        y = _safe_float(element.get("y", 0))
        font_size = _safe_float(element.get("font_size", 14), 14)
        fill = _sanitize_attr(element.get("fill", "#212121"))
        font_weight = _sanitize_attr(element.get("font_weight", "normal"))
        text_anchor = _sanitize_attr(element.get("text_anchor", "start"))

        svg_parts.append(
            f'<text x="{x}" y="{y}" font-family="sans-serif" '
            f'font-size="{font_size}" font-weight="{font_weight}" '
            f'fill="{fill}" text-anchor="{text_anchor}">'
            f"{_escape_xml(content)}</text>"
        )

    # ------------------------------------------------------------------
    # Anchor resolution
    # ------------------------------------------------------------------

    def _resolve_anchor(self, element: dict, anchor_name: str) -> tuple:
        """Convert a normalized anchor to absolute coordinates.

        Formula:
            abs_x = element.x + anchor.x * element.width
            abs_y = element.y + anchor.y * element.height
        """
        component_id = element.get("component_id")
        comp = self._components.get(component_id, {}) if component_id else {}
        anchors = comp.get("anchors", DEFAULT_ANCHORS)

        anchor = anchors.get(anchor_name)
        if not anchor:
            logger.warning(
                "Unknown anchor '%s' for element '%s', falling back to center",
                anchor_name,
                element.get("id"),
            )
            anchor = {"x": 0.5, "y": 0.5}

        ex = element.get("x", 0)
        ey = element.get("y", 0)
        ew = element.get("width", comp.get("default_width", 100))
        eh = element.get("height", comp.get("default_height", 100))

        abs_x = ex + anchor["x"] * ew
        abs_y = ey + anchor["y"] * eh
        return abs_x, abs_y

    def _get_anchor_direction(self, anchor_name: str) -> str:
        """Return the direction associated with a named anchor.

        Maps common anchor names to one of ``'top'``, ``'right'``,
        ``'bottom'``, ``'left'``.  Falls back to ``'right'`` for
        unrecognized names.
        """
        mapping = {
            "top": "top",
            "right": "right",
            "bottom": "bottom",
            "left": "left",
            "center": "right",
        }
        return mapping.get(anchor_name, "right")

    # ------------------------------------------------------------------
    # Connection routing
    # ------------------------------------------------------------------

    def _route_connection(
        self, conn: dict, elements_map: dict, svg_parts: list, defs_parts: list
    ) -> None:
        """Route a connection between two elements and append SVG output."""
        from_spec = conn.get("from", {})
        to_spec = conn.get("to", {})
        from_id = from_spec.get("element_id")
        to_id = to_spec.get("element_id")

        if not from_id or not to_id:
            logger.warning("Connection missing element_id, skipping")
            return

        from_elem = elements_map.get(from_id)
        to_elem = elements_map.get(to_id)
        if not from_elem:
            logger.warning("Connection references unknown element: %s", from_id)
            return
        if not to_elem:
            logger.warning("Connection references unknown element: %s", to_id)
            return

        from_anchor = from_spec.get("anchor", "right")
        to_anchor = to_spec.get("anchor", "left")

        sx, sy = self._resolve_anchor(from_elem, from_anchor)
        ex, ey = self._resolve_anchor(to_elem, to_anchor)

        start_dir = self._get_anchor_direction(from_anchor)
        end_dir = self._get_anchor_direction(to_anchor)

        style = conn.get("style", "orthogonal")
        stroke = _sanitize_attr(conn.get("stroke", "#607D8B"))
        stroke_width = _safe_float(conn.get("stroke_width", 2), 2)
        arrow = conn.get("arrow", "none")

        # Create arrow marker(s) if needed
        marker_attrs = ""
        if arrow in ("end", "both"):
            marker_id = f"arrow-end-{_color_to_id(stroke)}"
            defs_parts.append(self._create_arrow_marker(marker_id, stroke))
            marker_attrs += f' marker-end="url(#{marker_id})"'
        if arrow in ("start", "both"):
            marker_id = f"arrow-start-{_color_to_id(stroke)}"
            defs_parts.append(self._create_arrow_marker(marker_id, stroke))
            marker_attrs += f' marker-start="url(#{marker_id})"'

        # Route based on style
        if style == "straight":
            path_str = self._route_straight(sx, sy, ex, ey)
            svg_parts.append(
                f'<line x1="{sx}" y1="{sy}" x2="{ex}" y2="{ey}" '
                f'stroke="{stroke}" stroke-width="{stroke_width}" '
                f'fill="none"{marker_attrs}/>'
            )
        elif style == "curved":
            path_d = self._route_curved(sx, sy, start_dir, ex, ey, end_dir)
            svg_parts.append(
                f'<path d="{path_d}" stroke="{stroke}" stroke-width="{stroke_width}" '
                f'fill="none"{marker_attrs}/>'
            )
        else:
            # orthogonal (default)
            points = self._route_orthogonal(sx, sy, start_dir, ex, ey, end_dir)
            points_str = " ".join(f"{px},{py}" for px, py in points)
            svg_parts.append(
                f'<polyline points="{points_str}" stroke="{stroke}" '
                f'stroke-width="{stroke_width}" fill="none"{marker_attrs}/>'
            )

        # Optional connection label
        label = conn.get("label")
        if label:
            mid_x = (sx + ex) / 2
            mid_y = (sy + ey) / 2
            svg_parts.append(
                f'<text x="{mid_x}" y="{mid_y - 8}" text-anchor="middle" '
                f'font-family="sans-serif" font-size="12" fill="{stroke}">'
                f"{_escape_xml(label)}</text>"
            )

    def _route_straight(self, sx: float, sy: float, ex: float, ey: float) -> str:
        """Return SVG path data for a straight line between two points."""
        return f"M {sx} {sy} L {ex} {ey}"

    def _extend_from_anchor(
        self, x: float, y: float, direction: str, margin: float
    ) -> tuple:
        """Extend a point from an anchor in the given direction by *margin* pixels."""
        if direction == "top":
            return x, y - margin
        elif direction == "right":
            return x + margin, y
        elif direction == "bottom":
            return x, y + margin
        elif direction == "left":
            return x - margin, y
        return x, y

    def _route_orthogonal(
        self,
        start_x: float,
        start_y: float,
        start_dir: str,
        end_x: float,
        end_y: float,
        end_dir: str,
        margin: float = 20,
    ) -> list:
        """Manhattan routing: generate a right-angle path between two anchors.

        Returns a list of ``(x, y)`` waypoints for a polyline.
        """
        sx, sy = self._extend_from_anchor(start_x, start_y, start_dir, margin)
        ex, ey = self._extend_from_anchor(end_x, end_y, end_dir, margin)

        mid_x = (sx + ex) / 2
        mid_y = (sy + ey) / 2

        if start_dir in ("left", "right"):
            points = [
                (start_x, start_y),
                (sx, sy),
                (mid_x, sy),
                (mid_x, ey),
                (ex, ey),
                (end_x, end_y),
            ]
        else:
            points = [
                (start_x, start_y),
                (sx, sy),
                (sx, mid_y),
                (ex, mid_y),
                (ex, ey),
                (end_x, end_y),
            ]
        return points

    def _route_curved(
        self,
        sx: float,
        sy: float,
        start_dir: str,
        ex: float,
        ey: float,
        end_dir: str,
    ) -> str:
        """Return SVG cubic bezier path data with control points along anchor directions."""
        dist = math.hypot(ex - sx, ey - sy) * 0.4
        c1x, c1y = self._extend_from_anchor(sx, sy, start_dir, dist)
        c2x, c2y = self._extend_from_anchor(ex, ey, end_dir, dist)
        return f"M {sx} {sy} C {c1x} {c1y}, {c2x} {c2y}, {ex} {ey}"

    # ------------------------------------------------------------------
    # Arrow markers
    # ------------------------------------------------------------------

    def _create_arrow_marker(self, marker_id: str, color: str) -> str:
        """Return an SVG ``<marker>`` definition for an arrowhead."""
        safe_id = _sanitize_attr(marker_id)
        safe_color = _sanitize_attr(color)
        return (
            f'<marker id="{safe_id}" viewBox="0 0 10 10" refX="10" refY="5" '
            f'markerWidth="8" markerHeight="8" orient="auto-start-reverse">'
            f'<path d="M 0 0 L 10 5 L 0 10 z" fill="{safe_color}"/>'
            f"</marker>"
        )

    # ------------------------------------------------------------------
    # SVG parsing helpers
    # ------------------------------------------------------------------

    def _parse_viewbox(
        self, svg_content: str, fallback_w: float, fallback_h: float
    ) -> tuple:
        """Extract viewBox width/height from SVG content.

        Falls back to ``width``/``height`` attributes, then to the provided
        fallback dimensions.
        """
        # Try viewBox attribute
        vb_match = re.search(r'viewBox\s*=\s*["\']([^"\']+)["\']', svg_content)
        if vb_match:
            parts = vb_match.group(1).split()
            if len(parts) == 4:
                try:
                    return float(parts[2]), float(parts[3])
                except ValueError:
                    pass

        # Fallback to width/height attributes
        w_match = re.search(r'width\s*=\s*["\']([0-9.]+)', svg_content)
        h_match = re.search(r'height\s*=\s*["\']([0-9.]+)', svg_content)
        if w_match and h_match:
            try:
                return float(w_match.group(1)), float(h_match.group(1))
            except ValueError:
                pass

        return fallback_w, fallback_h

    @staticmethod
    def _extract_svg_inner(svg_content: str) -> str:
        """Extract the inner content between ``<svg ...>`` and ``</svg>``."""
        # Remove XML declaration if present
        content = re.sub(r"<\?xml[^?]*\?>", "", svg_content).strip()
        # Remove the outer <svg> wrapper
        content = re.sub(r"^<svg[^>]*>", "", content, count=1)
        content = re.sub(r"</svg>\s*$", "", content, count=1)
        return content.strip()


# ------------------------------------------------------------------
# Module-level helpers
# ------------------------------------------------------------------


def _escape_xml(text: str) -> str:
    """Escape special XML characters in text content."""
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    text = text.replace('"', "&quot;")
    return text


def _sanitize_attr(value: str) -> str:
    """Escape characters that could break out of a double-quoted SVG attribute.

    Defense-in-depth: even though ``svg_processor.sanitize_svg()`` strips
    ``on*`` handlers downstream, we sanitize at the composition layer to
    prevent attribute injection via LLM-supplied values like
    ``#fff" onload="alert(1)"``.
    """
    return (
        str(value)
        .replace("&", "&amp;")
        .replace('"', "&quot;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _safe_float(value, default: float = 0.0) -> float:
    """Coerce *value* to float, returning *default* on failure.

    Defense-in-depth: prevents string injection through numeric fields
    (e.g. ``'0" onload="alert(1)'`` for an x-coordinate).
    """
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _color_to_id(color: str) -> str:
    """Convert a color string to a safe identifier fragment."""
    return re.sub(r"[^a-zA-Z0-9]", "", color)
