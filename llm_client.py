"""
LLM client for SVG generation with purpose-specific prompts and multiple generation modes.

Supports:
- Purpose classification (auto or manual): diagram, icon, infographic, flat_illustration, classic
- Generation modes: direct_svg (LLM outputs SVG text), code_generation (LLM outputs Python code)
- YAML-based prompt templates loaded from prompt_templates/ directory
"""

import logging
import os
import re
import xml.etree.ElementTree as ET
import yaml
from typing import Optional
from openai import OpenAI

logger = logging.getLogger(__name__)

# Directory containing prompt template YAML files
TEMPLATES_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "prompt_templates"
)

# Valid purpose categories
VALID_PURPOSES = ["classic", "diagram", "icon", "infographic", "flat_illustration"]

# Valid generation modes
VALID_MODES = ["direct_svg", "code_generation"]


def load_template(purpose: str) -> dict:
    """Load a prompt template YAML file for the given purpose."""
    if purpose not in VALID_PURPOSES:
        purpose = "classic"
    filepath = os.path.join(TEMPLATES_DIR, f"{purpose}.yaml")
    if not os.path.exists(filepath):
        filepath = os.path.join(TEMPLATES_DIR, "classic.yaml")
    with open(filepath, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_all_templates() -> dict[str, dict]:
    """Load all prompt templates and return as {purpose: template_dict}."""
    templates = {}
    for purpose in VALID_PURPOSES:
        filepath = os.path.join(TEMPLATES_DIR, f"{purpose}.yaml")
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                templates[purpose] = yaml.safe_load(f)
    return templates


class LLMClient:
    _MAX_REPAIR_ATTEMPTS = 2

    def __init__(
        self, api_key: str, model: str = "gpt-4o", base_url: Optional[str] = None
    ):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model
        self._templates = load_all_templates()
        self._last_repair_attempts = 0

    def classify_purpose(self, prompt: str) -> str:
        """
        Auto-classify the user prompt into a purpose category.
        Uses keyword matching first, falls back to LLM classification.
        """
        prompt_lower = prompt.lower()

        # Keyword-based classification (fast, no API call)
        for purpose, template in self._templates.items():
            if purpose == "classic":
                continue
            keywords = template.get("classification_keywords", [])
            for keyword in keywords:
                if keyword.lower() in prompt_lower:
                    return purpose

        # Fallback to LLM classification
        try:
            classification_prompt = (
                "Classify the following user prompt into exactly one category:\n"
                "- diagram: flowcharts, org charts, ER diagrams, network diagrams, process flows, architecture\n"
                "- icon: single icons, symbols, logos, badges\n"
                "- infographic: data visualization, charts, statistics, dashboards, metrics\n"
                "- flat_illustration: flat design illustrations, scenes, conceptual visuals\n"
                "- classic: anything else that doesn't clearly fit the above\n\n"
                f"User prompt: {prompt}\n\n"
                "Respond with ONLY the category name (one word, lowercase)."
            )
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a prompt classifier. Respond with only the category name.",
                    },
                    {"role": "user", "content": classification_prompt},
                ],
                temperature=0.0,
                max_tokens=20,
                timeout=15.0,
            )
            result = response.choices[0].message.content.strip().lower()
            if result in VALID_PURPOSES:
                return result
        except Exception:
            pass  # Classification failure is non-critical, fall back to classic

        return "classic"

    def generate_diagram_data(
        self,
        prompt: str,
        current_svg: Optional[str] = None,
        purpose: str = "auto",
        generation_mode: str = "direct_svg",
    ) -> dict:
        """
        Generate SVG from a natural language prompt.

        Args:
            prompt: User's description of what to generate.
            current_svg: Existing SVG for refinement mode. None for new generation.
            purpose: Purpose category ('auto', 'classic', 'diagram', 'icon', 'infographic', 'flat_illustration').
            generation_mode: 'direct_svg' or 'code_generation'.

        Returns:
            dict with keys:
                - 'svg': The generated SVG string.
                - 'purpose': The resolved purpose category.
                - 'generation_mode': The generation mode used.
                - 'fallback': True if fell back to direct_svg from code_generation.
        """
        # Resolve purpose
        self._last_repair_attempts = 0
        if purpose == "auto":
            resolved_purpose = self.classify_purpose(prompt)
        elif purpose in VALID_PURPOSES:
            resolved_purpose = purpose
        else:
            resolved_purpose = "classic"

        # Load template
        template = self._templates.get(
            resolved_purpose, self._templates.get("classic", {})
        )

        # Build context data
        mode_instruction = (
            "Create a high-quality, professional SVG illustration from scratch."
        )
        context_data = ""
        if current_svg:
            mode_instruction = "Modify or refine the existing SVG based on the user's instruction. Keep the artistic style consistent."
            context_data = f"\n### Current SVG Code:\n{current_svg}"

        # Try code generation mode
        if generation_mode == "code_generation":
            try:
                svg = self._generate_via_code(
                    prompt, template, mode_instruction, context_data
                )
                return {
                    "svg": svg,
                    "purpose": resolved_purpose,
                    "generation_mode": "code_generation",
                    "fallback": False,
                    "repaired": self._last_repair_attempts > 0,
                }
            except Exception:
                # Fall back to direct SVG
                svg = self._generate_direct_svg(
                    prompt, template, mode_instruction, context_data
                )
                return {
                    "svg": svg,
                    "purpose": resolved_purpose,
                    "generation_mode": "direct_svg",
                    "fallback": True,
                    "repaired": self._last_repair_attempts > 0,
                }

        # Direct SVG mode (default)
        svg = self._generate_direct_svg(
            prompt, template, mode_instruction, context_data
        )
        return {
            "svg": svg,
            "purpose": resolved_purpose,
            "generation_mode": "direct_svg",
            "fallback": False,
            "repaired": self._last_repair_attempts > 0,
        }

    def _generate_direct_svg(
        self, prompt: str, template: dict, mode_instruction: str, context_data: str
    ) -> str:
        """Generate SVG by having the LLM output SVG code directly.

        After extracting the SVG from the LLM response, validates it as
        well-formed XML.  If parsing fails, sends the error back to the
        LLM for repair (up to ``_MAX_REPAIR_ATTEMPTS`` times).
        """
        system_prompt_template = template.get("system_prompt", "")
        system_prompt = system_prompt_template.format(
            mode_instruction=mode_instruction,
            context_data=context_data,
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Instruction: {prompt}"},
        ]

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3,
                timeout=60.0,
            )
            content = response.choices[0].message.content.strip()

            svg = self._extract_svg_tag(content)
            svg = self._sanitize_svg_text(svg)

            parse_error = self._validate_svg_xml(svg)
            if parse_error is None:
                return svg

            # Repair loop: feed parse error back to LLM
            for attempt in range(1, self._MAX_REPAIR_ATTEMPTS + 1):
                logger.warning(
                    "SVG XML invalid (attempt %d/%d): %s",
                    attempt,
                    self._MAX_REPAIR_ATTEMPTS,
                    parse_error,
                )
                svg = self._repair_svg_via_llm(svg, parse_error)
                svg = self._sanitize_svg_text(svg)
                parse_error = self._validate_svg_xml(svg)
                if parse_error is None:
                    logger.info("SVG repaired successfully on attempt %d", attempt)
                    self._last_repair_attempts = attempt
                    return svg

            logger.warning(
                "SVG repair exhausted after %d attempts, returning best-effort SVG",
                self._MAX_REPAIR_ATTEMPTS,
            )
            self._last_repair_attempts = self._MAX_REPAIR_ATTEMPTS
            return svg
        except Exception as e:
            raise Exception(f"Failed to generate SVG: {str(e)}")

    def _generate_via_code(
        self, prompt: str, template: dict, mode_instruction: str, context_data: str
    ) -> str:
        """Generate SVG by having the LLM output Python code, then executing it."""
        from code_executor import CodeExecutor

        code_prompt_template = template.get("code_generation_prompt", "")
        if not code_prompt_template:
            raise Exception("No code_generation_prompt in template")

        system_prompt = code_prompt_template.format(
            mode_instruction=mode_instruction,
            context_data=context_data,
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Create: {prompt}"},
                ],
                temperature=0.2,
                timeout=60.0,
            )
            content = response.choices[0].message.content.strip()

            # Extract Python code from response (handle markdown code blocks)
            code = self._extract_code(content)

            # Execute in sandbox
            executor = CodeExecutor()
            return executor.execute(code)
        except Exception as e:
            raise Exception(f"Code generation failed: {str(e)}")

    @staticmethod
    def _extract_code(content: str) -> str:
        """Extract Python code from LLM response, handling markdown code blocks."""
        # Try to extract from ```python ... ``` block
        code_match = re.search(r"```(?:python)?\s*\n(.*?)```", content, re.DOTALL)
        if code_match:
            return code_match.group(1).strip()

        # If no code block, assume entire content is code
        # But strip any leading/trailing non-code text
        lines = content.split("\n")
        code_lines = []
        in_code = False
        for line in lines:
            if line.strip().startswith(
                ("import ", "from ", "def ", "class ", "d =", "d=", "#")
            ):
                in_code = True
            if in_code:
                code_lines.append(line)

        if code_lines:
            return "\n".join(code_lines)

        # Last resort: return as-is
        return content

    # ------------------------------------------------------------------
    # SVG validation & repair helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_svg_tag(content: str) -> str:
        """Extract the <svg>...</svg> block from LLM output."""
        match = re.search(r"<svg.*?</svg>", content, re.DOTALL | re.IGNORECASE)
        return match.group() if match else content

    @staticmethod
    def _sanitize_svg_text(svg: str) -> str:
        """Escape bare '&' characters that would break XML parsing."""
        return re.sub(
            r"&(?!(?:amp|lt|gt|quot|apos|#[0-9]+|#x[0-9a-fA-F]+);)",
            "&amp;",
            svg,
        )

    @staticmethod
    def _validate_svg_xml(svg: str) -> Optional[str]:
        """Return ``None`` if *svg* is well-formed XML, else the error message."""
        try:
            ET.fromstring(svg)
            return None
        except ET.ParseError as e:
            return str(e)

    def _repair_svg_via_llm(self, broken_svg: str, parse_error: str) -> str:
        """Ask the LLM to fix an XML parse error in *broken_svg*."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an SVG repair assistant. "
                            "Fix the XML error in the SVG below. "
                            "Output ONLY the corrected <svg>…</svg>, no explanation."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"This SVG has an XML parse error:\n\n"
                            f"Error: {parse_error}\n\n"
                            f"SVG:\n{broken_svg}"
                        ),
                    },
                ],
                temperature=0.0,
                timeout=30.0,
            )
            content = response.choices[0].message.content.strip()
            return self._extract_svg_tag(content)
        except Exception as e:
            logger.warning("SVG repair LLM call failed: %s", e)
            return broken_svg
