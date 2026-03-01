import base64
import re

class SVGProcessor:
    @staticmethod
    def encode_svg(svg_code: str) -> str:
        """
        Base64 encodes SVG code for safe display in an <img> tag.
        Returns a data URI string.
        """
        # Ensure it has a viewBox or width/height for better rendering
        if 'viewBox="' not in svg_code and 'width="' not in svg_code:
            # Simple fix: prepend a basic viewBox if missing
            svg_code = svg_code.replace('<svg', '<svg viewBox="0 0 400 400" preserveAspectRatio="xMidYMid meet"', 1)
        
        # Ensure the XML namespace is present
        if 'xmlns="http://www.w3.org/2000/svg"' not in svg_code:
            svg_code = svg_code.replace('<svg', '<svg xmlns="http://www.w3.org/2000/svg"', 1)
            
        b64 = base64.b64encode(svg_code.encode("utf-8")).decode("utf-8")
        return f"data:image/svg+xml;base64,{b64}"

    @staticmethod
    def sanitize_svg(svg_code: str) -> str:
        """
        Performs basic sanitization on the SVG code to prevent XSS.
        In a production environment, use a robust library like defusedxml or Bleach.
        """
        # Remove any <script> tags for basic safety
        sanitized = re.sub(r'<script.*?>.*?</script>', '', svg_code, flags=re.DOTALL | re.IGNORECASE)
        # Remove event handlers like onload, onclick, etc.
        sanitized = re.sub(r'\son\w+=".*?"', '', sanitized, flags=re.IGNORECASE)
        return sanitized.strip()
