import base64
import re


class SVGProcessor:
    @staticmethod
    def _escape_ampersands(svg_code: str) -> str:
        """Escape bare '&' characters in SVG text content.

        LLMs often produce SVG with unescaped '&' inside <text> elements
        (e.g. "R&D", "Q&A").  Bare '&' is invalid XML and causes parse
        failures in downstream consumers (svgelements, resvg, etc.).

        This replaces every '&' that is NOT already part of a valid XML
        entity reference (``&amp;``, ``&lt;``, ``&gt;``, ``&quot;``,
        ``&apos;``, or ``&#...;``) with ``&amp;``.
        """
        # Negative lookahead: don't touch & that is followed by a valid
        # entity name + ';' or a numeric character reference.
        return re.sub(
            r"&(?!(?:amp|lt|gt|quot|apos|#[0-9]+|#x[0-9a-fA-F]+);)",
            "&amp;",
            svg_code,
        )

    @staticmethod
    def encode_svg(svg_code: str) -> str:
        """
        Base64 encodes SVG code for safe display in an <img> tag.
        Returns a data URI string.
        """
        # Ensure it has a viewBox or width/height for better rendering
        if 'viewBox="' not in svg_code and 'width="' not in svg_code:
            # Simple fix: prepend a basic viewBox if missing
            svg_code = svg_code.replace(
                "<svg",
                '<svg viewBox="0 0 400 400" preserveAspectRatio="xMidYMid meet"',
                1,
            )

        # Ensure the XML namespace is present
        if 'xmlns="http://www.w3.org/2000/svg"' not in svg_code:
            svg_code = svg_code.replace(
                "<svg", '<svg xmlns="http://www.w3.org/2000/svg"', 1
            )

        b64 = base64.b64encode(svg_code.encode("utf-8")).decode("utf-8")
        return f"data:image/svg+xml;base64,{b64}"

    @staticmethod
    def sanitize_svg(svg_code: str) -> str:
        """
        Sanitize SVG code to prevent XSS and external resource leakage.

        Removes:
        - <script> tags
        - Event handler attributes (onload, onclick, etc.)
        - <use> elements referencing external URLs
        - href / xlink:href attributes pointing to external URLs
          (on <image>, <feImage>, <use>, <a>, and any element)
        - javascript: URIs
        - <foreignObject> elements (arbitrary HTML embedding)
        """
        s = SVGProcessor._escape_ampersands(svg_code)

        # 1. Remove <script> blocks
        s = re.sub(
            r"<script\b[^>]*>.*?</script>", "", s, flags=re.DOTALL | re.IGNORECASE
        )

        # 2. Remove <foreignObject> blocks (can embed arbitrary HTML)
        s = re.sub(
            r"<foreignObject\b[^>]*>.*?</foreignObject>",
            "",
            s,
            flags=re.DOTALL | re.IGNORECASE,
        )

        # 3. Remove event handler attributes (on*)
        s = re.sub(r'\bon\w+\s*=\s*(?:"[^"]*"|\'[^\']*\')', "", s, flags=re.IGNORECASE)

        # 4. Remove href / xlink:href attributes that reference external URLs or javascript:
        #    Matches: href="https://..." xlink:href='http://...' href="javascript:..."
        s = re.sub(
            r'(?:xlink:)?href\s*=\s*(?:"(?:https?:|javascript:|data:(?!image/(?:png|jpeg|gif|webp|svg\+xml)))[^"]*"|'
            r"\'(?:https?:|javascript:|data:(?!image/(?:png|jpeg|gif|webp|svg\+xml)))[^\']*\')",
            "",
            s,
            flags=re.IGNORECASE,
        )

        # 5. Remove <image> / <feImage> elements that still carry an external src or href
        #    (belt-and-suspenders after step 4)
        s = re.sub(
            r'<(?:image|feImage)\b[^>]*(?:href|src)\s*=\s*["\']https?://[^"\']*["\'][^>]*/?>',
            "",
            s,
            flags=re.IGNORECASE | re.DOTALL,
        )

        # 6. Remove javascript: URIs anywhere (e.g. in style attributes or custom attributes)
        s = re.sub(r"javascript\s*:", "invalid:", s, flags=re.IGNORECASE)

        return s.strip()
