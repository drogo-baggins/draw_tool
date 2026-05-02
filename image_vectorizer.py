"""
image_vectorizer.py

Pipeline: Venice AI image generation → image preprocessing → vtracer vectorization → SVG

Venice AI image API returns base64-encoded WebP images.
Preprocessing reduces color complexity to produce cleaner SVGs.
"""

from __future__ import annotations

import base64
import io
import requests
from PIL import Image, ImageFilter


VENICE_IMAGE_URL = "https://api.venice.ai/api/v1/image/generate"

# Default vtracer parameters tuned for illustration→SVG
DEFAULT_VTRACER_PARAMS = dict(
    colormode="color",
    hierarchical="stacked",
    mode="spline",
    filter_speckle=8,        # remove tiny details (higher = simpler)
    color_precision=6,       # number of colors (lower = simpler)
    layer_difference=32,     # color merging threshold (higher = fewer layers)
    corner_threshold=60,
    length_threshold=4.0,
    max_iterations=10,
    splice_threshold=45,
    path_precision=3,
)


def generate_image(
    prompt: str,
    api_key: str,
    model: str = "recraft-v4",
    width: int = 512,
    height: int = 512,
    style_preset: str | None = "Minimalist",
) -> Image.Image:
    """Call Venice AI image generation API and return a PIL Image."""
    payload: dict = {
        "model": model,
        "prompt": prompt,
        "width": width,
        "height": height,
    }
    if style_preset:
        payload["style_preset"] = style_preset

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    resp = requests.post(VENICE_IMAGE_URL, json=payload, headers=headers, timeout=120)
    resp.raise_for_status()
    data = resp.json()

    images = data.get("images", [])
    if not images:
        raise ValueError(f"No images in response: {data}")

    img_b64 = images[0]
    img_bytes = base64.b64decode(img_b64)
    return Image.open(io.BytesIO(img_bytes)).convert("RGBA")


def preprocess_image(
    img: Image.Image,
    num_colors: int = 8,
    blur_radius: float = 1.0,
    output_size: tuple[int, int] = (512, 512),
) -> Image.Image:
    """
    Reduce image complexity for cleaner vectorization:
    1. Resize to consistent size
    2. Slight blur to eliminate micro-details
    3. Color quantization to limit palette
    4. Convert to RGB (vtracer needs no alpha)
    """
    # Resize
    img = img.resize(output_size, Image.LANCZOS)

    # Flatten alpha onto white background
    if img.mode == "RGBA":
        background = Image.new("RGBA", img.size, (255, 255, 255, 255))
        background.paste(img, mask=img.split()[3])
        img = background.convert("RGB")
    else:
        img = img.convert("RGB")

    # Blur to suppress high-frequency detail
    if blur_radius > 0:
        img = img.filter(ImageFilter.GaussianBlur(radius=blur_radius))

    # Quantize to reduce color palette
    img_q = img.quantize(colors=num_colors, method=Image.Quantize.FASTOCTREE)
    img = img_q.convert("RGB")

    return img


def vectorize_image(
    img: Image.Image,
    vtracer_params: dict | None = None,
) -> str:
    """Convert a PIL Image to SVG string using opencv contour tracing.

    Uses per-color-layer contour detection to produce clean flat SVG paths.
    This replaces vtracer which has Python 3.14 compatibility issues.
    """
    import cv2
    import numpy as np

    params = {**DEFAULT_VTRACER_PARAMS, **(vtracer_params or {})}
    filter_speckle = params.get("filter_speckle", 8)
    color_precision = params.get("color_precision", 6)
    # Minimum contour area to include
    min_area = max(filter_speckle * 4, 16)

    img_rgb = img.convert("RGB")
    width, height = img_rgb.size
    img_np = np.array(img_rgb, dtype=np.uint8)

    # ── Re-quantize with OpenCV k-means to guarantee exact color_precision colors ──
    # PIL quantize can produce slight edge artifacts; k-means on float data is cleaner.
    pixels = img_np.reshape(-1, 3).astype(np.float32)
    k = int(color_precision)
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
    _, labels, centers = cv2.kmeans(
        pixels, k, None, criteria, 5, cv2.KMEANS_PP_CENTERS
    )
    centers = np.round(centers).astype(np.uint8)
    quantized = centers[labels.flatten()].reshape(img_np.shape)

    # ── Detect background cluster from corner pixels ──────────────────────────
    # Sample the 4 corners of the quantized image to find which cluster is background.
    # Only that cluster is skipped (not all near-white colors) so colors that happen
    # to be light do not disappear.
    label_grid = labels.reshape(height, width)
    corner_labels = [
        int(label_grid[0, 0]),
        int(label_grid[0, width - 1]),
        int(label_grid[height - 1, 0]),
        int(label_grid[height - 1, width - 1]),
    ]
    from collections import Counter as _Counter
    bg_idx = _Counter(corner_labels).most_common(1)[0][0]
    bg_color = centers[bg_idx]
    bg_hex = f"#{int(bg_color[0]):02x}{int(bg_color[1]):02x}{int(bg_color[2]):02x}"

    paths_svg: list[str] = []

    for idx in range(k):
        # Skip only the detected background cluster
        if idx == bg_idx:
            continue

        color = centers[idx]
        r_val, g_val, b_val = int(color[0]), int(color[1]), int(color[2])
        hex_color = f"#{r_val:02x}{g_val:02x}{b_val:02x}"

        # Create exact mask for this cluster label
        mask = (labels.reshape(height, width) == idx).astype(np.uint8) * 255

        # Morphological closing to fill small holes
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        # Find contours
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_TC89_KCOS)

        for contour in contours:
            area = cv2.contourArea(contour)
            if area < min_area:
                continue

            # Simplify contour
            epsilon = 0.01 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)

            if len(approx) < 3:
                continue

            # Build SVG path
            pts = approx.reshape(-1, 2)
            d = f"M {pts[0][0]} {pts[0][1]}"
            for pt in pts[1:]:
                d += f" L {pt[0]} {pt[1]}"
            d += " Z"

            paths_svg.append(f'  <path d="{d}" fill="{hex_color}" />')

    svg_lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        f'  <rect width="{width}" height="{height}" fill="{bg_hex}"/>',
        *paths_svg,
        "</svg>",
    ]
    return "\n".join(svg_lines)


VECTOR_PROMPT_SUFFIX = (
    ", flat vector illustration, bold solid-color areas, "
    "thick clean outlines, minimal shading, geometric shapes, "
    "limited color palette, SVG-friendly style"
)


def enhance_prompt_for_vectorization(prompt: str) -> str:
    """Append vectorization-friendly keywords unless the prompt already has them."""
    keywords = ["vector", "flat", "outline", "geometric", "minimal"]
    lower = prompt.lower()
    if any(k in lower for k in keywords):
        return prompt
    return prompt + VECTOR_PROMPT_SUFFIX


def run_pipeline(
    prompt: str,
    api_key: str,
    model: str = "recraft-v4",
    width: int = 512,
    height: int = 512,
    style_preset: str | None = "Flat Papercut",
    num_colors: int = 12,
    blur_radius: float = 0.5,
    vtracer_params: dict | None = None,
    progress_callback=None,
    auto_enhance_prompt: bool = True,
) -> dict:
    """
    Full pipeline: generate → preprocess → vectorize.

    Returns dict with keys: svg, intermediate_image (PIL), params_used
    """

    def _step(msg):
        if progress_callback:
            progress_callback(msg)

    effective_prompt = enhance_prompt_for_vectorization(prompt) if auto_enhance_prompt else prompt

    _step("🎨 Generating image with Venice AI...")
    img_original = generate_image(
        prompt=effective_prompt,
        api_key=api_key,
        model=model,
        width=width,
        height=height,
        style_preset=style_preset,
    )

    _step("🔧 Preprocessing image (color reduction)...")
    img_processed = preprocess_image(
        img_original,
        num_colors=num_colors,
        blur_radius=blur_radius,
    )

    _step("📐 Vectorizing to SVG...")
    svg = vectorize_image(img_processed, vtracer_params=vtracer_params)

    return {
        "svg": svg,
        "original_image": img_original,
        "processed_image": img_processed,
        "effective_prompt": effective_prompt,
        "params": {
            "model": model,
            "style_preset": style_preset,
            "num_colors": num_colors,
            "blur_radius": blur_radius,
            "vtracer": {**DEFAULT_VTRACER_PARAMS, **(vtracer_params or {})},
        },
    }
