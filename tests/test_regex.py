import re

svg_code = """
<svg width="100" height="100" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" style="stop-color:rgb(255,255,0);stop-opacity:1" />
      <stop offset="100%" style="stop-color:rgb(255,0,0);stop-opacity:1" />
    </linearGradient>
    <radialGradient id="grad2" cx="50%" cy="50%" r="50%" fx="50%" fy="50%">
      <stop offset="0%" style="stop-color:rgb(255,255,255);stop-opacity:0" />
      <stop offset="100%" style="stop-color:rgb(0,0,255);stop-opacity:1" />
    </radialGradient>
  </defs>
  <rect x="10" y="10" width="80" height="80" fill="url(#grad1)" />
</svg>
"""


def extract_gradient_def(svg_code, grad_id):
    pattern = rf'<(linear|radial)Gradient[^>]*id=["\']?{re.escape(grad_id)}["\']?[^>]*>.*?</\1Gradient>'
    match = re.search(pattern, svg_code, re.DOTALL)
    if match:
        return match.group(0)
    return None


print(f"Extracting grad1: {extract_gradient_def(svg_code, 'grad1')}")
print(f"Extracting grad2: {extract_gradient_def(svg_code, 'grad2')}")
