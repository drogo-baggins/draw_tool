"""Vision-based feedback loop for iteratively refining SVG quality.

This module provides a feedback system that uses vision models to evaluate
SVG renderings and provide actionable improvement instructions to an LLM
for iterative refinement.
"""

import base64
from typing import Optional

import resvg_py
from openai import OpenAI


class VisionFeedback:
    """Manages vision-model feedback for SVG quality refinement.

    Uses a vision-capable model to evaluate SVG renderings and provide
    structured feedback that guides LLM-based iterative improvements.
    """

    def __init__(
        self, api_key: str, model: str = "gpt-4o", base_url: Optional[str] = None
    ):
        """Initialize with OpenAI client for vision API calls.

        Args:
            api_key: OpenAI API key
            model: Vision model to use (default: gpt-4o)
            base_url: Optional base URL for OpenAI API (for custom endpoints)
        """
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model

    def render_svg_to_png(self, svg_code: str) -> bytes:
        """Render SVG string to PNG bytes.

        Args:
            svg_code: SVG code as string

        Returns:
            PNG image as bytes

        Raises:
            ValueError: If SVG rendering fails
        """
        try:
            svg_bytes = svg_code.encode("utf-8")
            png_bytes = resvg_py.svg_to_png(svg_bytes)
            return png_bytes
        except Exception as e:
            raise ValueError(f"Failed to render SVG to PNG: {str(e)}") from e

    def evaluate(self, svg_code: str, original_prompt: str) -> str:
        """Evaluate SVG rendering using vision model.

        Args:
            svg_code: SVG code to evaluate
            original_prompt: Original prompt that generated this SVG

        Returns:
            Evaluation feedback as string with improvement instructions
        """
        # Render SVG to PNG
        png_bytes = self.render_svg_to_png(svg_code)

        # Encode PNG to base64
        b64_png = base64.b64encode(png_bytes).decode("utf-8")

        # Prepare evaluation prompt
        evaluation_prompt = (
            f"Evaluate this SVG rendering for:\n"
            f"1. Visual alignment and symmetry\n"
            f"2. Color harmony and contrast\n"
            f"3. Text readability and placement\n"
            f"4. Overall professional appearance\n"
            f'5. Adherence to the original prompt: "{original_prompt}"\n\n'
            f"Provide specific, actionable improvement instructions as a numbered list.\n"
            f"Focus on what needs to change, not what is good.\n"
            f"Be concise - each instruction should be one sentence."
        )

        # Send to vision model
        message = {
            "role": "user",
            "content": [
                {"type": "text", "text": evaluation_prompt},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{b64_png}",
                        "detail": "high",
                    },
                },
            ],
        }

        response = self.client.chat.completions.create(
            model=self.model, messages=[message], max_tokens=512
        )

        return response.choices[0].message.content

    def refine_loop(
        self,
        llm_client,
        prompt: str,
        initial_svg: str,
        max_iterations: int = 3,
        purpose: str = "classic",
        generation_mode: str = "direct_svg",
    ) -> list[dict]:
        """Run iterative refinement loop with vision feedback.

        Args:
            llm_client: LLM client instance for generating improved SVGs
            prompt: Original prompt for SVG generation
            initial_svg: Initial SVG code to refine
            max_iterations: Maximum refinement iterations (default: 3)
            purpose: Style purpose for LLM generation (default: "classic")
            generation_mode: Generation mode for LLM (default: "direct_svg")

        Returns:
            List of dicts with keys: iteration, svg, feedback
        """
        results = []
        current_svg = initial_svg

        # Add initial SVG without feedback
        results.append({"iteration": 0, "svg": current_svg, "feedback": None})

        # Refinement iterations
        for iteration in range(1, max_iterations + 1):
            # Evaluate current SVG
            feedback = self.evaluate(current_svg, prompt)

            # Generate refined SVG using feedback
            refined_prompt = (
                f"{prompt}\n\nRefinement feedback from visual evaluation:\n{feedback}"
            )

            diagram_data = llm_client.generate_diagram_data(
                prompt=refined_prompt,
                current_svg=current_svg,
                purpose=purpose,
                generation_mode=generation_mode,
            )

            current_svg = diagram_data["svg"]

            # Store result
            results.append(
                {"iteration": iteration, "svg": current_svg, "feedback": feedback}
            )

        return results
