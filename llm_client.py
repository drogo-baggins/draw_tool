import re
from openai import OpenAI

class LLMClient:
    def __init__(self, api_key: str, model: str = "gpt-4o", base_url: str = None):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model

    def generate_diagram_data(self, prompt: str, current_svg: str = None) -> str:
        """
        プロンプトから高品質なSVGコードを生成、または既存のSVGを修正する。
        """
        mode_instruction = "Create a high-quality, professional SVG illustration from scratch."
        context_data = ""
        
        if current_svg:
            mode_instruction = "Modify or refine the existing SVG based on the user's instruction. Keep the artistic style consistent."
            # SVGが長すぎる場合は要約するか、あるいはそのまま渡すがトークン数に注意
            # ここではシンプルに全文を渡す（長大な場合はカットが必要）
            context_data = f"\n### Current SVG Code:\n{current_svg}"

        system_prompt = (
            "You are a master vector illustrator akin to Adobe Illustrator. "
            f"{mode_instruction} "
            "Respond ONLY with the SVG code string. Do not include markdown code blocks. "
            "Requirements for PowerPoint Compatibility: "
            "- Use standard SVG 1.1 features. "
            "- Focus on <path>, <rect>, <circle>, <ellipse>, <line>, <polyline>, <polygon>. "
            "- Avoid complex filters, clips, or masks as they are hard to convert to native shapes. "
            "- Use 'fill' and 'stroke' attributes directly on elements (or groups). "
            "- Dimensions should be roughly 800x600. "
            "- For illustrations (e.g., scenes, characters), use many detailed <path> elements with distinct fill colors. "
            "- Ensure all paths are closed if they are filled shapes. "
            f"{context_data}"
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Instruction: {prompt}"},
                ],
                temperature=0.3, # 少し創造性を上げる
                timeout=60.0
            )
            content = response.choices[0].message.content.strip()
            
            # SVGタグの抽出
            svg_match = re.search(r'<svg.*?</svg>', content, re.DOTALL | re.IGNORECASE)
            if svg_match:
                return svg_match.group()
            else:
                # タグが見つからない場合、全テキストを返す（修正が必要かもしれない）
                return content
        except Exception as e:
            raise Exception(f"Failed to generate SVG: {str(e)}")
