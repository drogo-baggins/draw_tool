import io
import logging
from pptx_exporter import PPTXNativeExporter
from svgelements import SVG

# Configure logging
logging.basicConfig(level=logging.INFO)

svg_content = """
<svg width="400" height="300" xmlns="http://www.w3.org/2000/svg">
  <!-- Red Rectangle -->
  <rect x="50" y="50" width="100" height="80" fill="#FF0000" stroke="black" stroke-width="2"/>
  
  <!-- Blue Circle -->
  <circle cx="250" cy="90" r="40" fill="#0000FF" stroke="none"/>
  
  <!-- Green Path (Triangle) -->
  <path d="M 50 200 L 150 200 L 100 100 Z" fill="#00FF00" stroke="black"/>
</svg>
"""

if __name__ == "__main__":
    try:
        print("Generating PPTX...")
        pptx_bytes = PPTXNativeExporter.generate_pptx_from_data(svg_content)
        print(f"Generated {len(pptx_bytes)} bytes.")

        with open("debug_output_fixed.pptx", "wb") as f:
            f.write(pptx_bytes)
        print("Saved to debug_output_fixed.pptx")

    except Exception as e:
        print(f"Fatal Error: {e}")
