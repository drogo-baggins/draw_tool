import streamlit as st
import os
import yaml
from dotenv import load_dotenv
from llm_client import LLMClient
from llm_profile_config import get_profile_by_label, normalize_config_data
from pptx_exporter import PPTXNativeExporter
from svg_processor import SVGProcessor
from vision_feedback import VisionFeedback
import base64
import io

load_dotenv()

CONFIG_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "config", "llm_configs.yaml"
)

# Mapping from display names to internal values
PURPOSE_MAP = {
    "Auto": "auto",
    "Diagram": "diagram",
    "Icon": "icon",
    "Infographic": "infographic",
    "Flat Illustration": "flat_illustration",
    "Classic": "classic",
}
GEN_MODE_MAP = {
    "Direct SVG": "direct_svg",
    "Code Generation (Higher Quality)": "code_generation",
    "Component (Pre-made Parts)": "component",
}

IMAGE_MODELS = [
    "flux-2-pro",          # 汎用高品質
    "flux-2-max",          # 汎用最高品質
    "imagineart-1.5-pro",  # 汎用イラスト
    "venice-sd35",         # SD3.5 汎用
    "hidream",             # 高品質
    "seedream-v5-lite",    # 軽量
    "seedream-v4",
    "qwen-image-2",
    "qwen-image-2-pro",
    "wan-2-7-text-to-image",
    "grok-imagine-image",
    "wai-Illustrious",     # イラスト特化
    "recraft-v4",          # サイケデリック系
    "recraft-v4-pro",
]

STYLE_PRESETS = [
    "(none)",
    "Minimalist",
    "Line Art",
    "Flat Papercut",
    "Digital Art",
    "Lowpoly",
    "Isometric Style",
    "Watercolor",
    "Anime",
    "Comic Book",
]


def load_configs():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return normalize_config_data(yaml.safe_load(f))
    return normalize_config_data(None)


def save_configs(configs_data):
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        yaml.safe_dump(configs_data, f, allow_unicode=True)


st.set_page_config(page_title="🎨 LLM Vector Illustrator", layout="wide")

# Session state initialization
if "svg_code" not in st.session_state:
    st.session_state.svg_code = '<svg width="800" height="600" viewBox="0 0 800 600" xmlns="http://www.w3.org/2000/svg"><rect x="0" y="0" width="800" height="600" fill="#f0f8ff"/><circle cx="400" cy="300" r="100" fill="#ff6347"/></svg>'
if "editor_content" not in st.session_state:
    st.session_state.editor_content = st.session_state.svg_code
if "svg-editor" not in st.session_state:
    st.session_state["svg-editor"] = st.session_state.editor_content
if "refinement_versions" not in st.session_state:
    st.session_state.refinement_versions = []
if "selected_version" not in st.session_state:
    st.session_state.selected_version = 0
if "last_result_meta" not in st.session_state:
    st.session_state.last_result_meta = {}

configs_data = load_configs()
config_labels = [c["label"] for c in configs_data["configs"]]
generation_default_index = (
    config_labels.index(configs_data["selected_generation_label"])
    if configs_data["selected_generation_label"] in config_labels
    else 0
)
vision_option_labels = ["(none)", *config_labels]
selected_vision_value = configs_data.get("selected_vision_label") or "(none)"
vision_default_index = (
    vision_option_labels.index(selected_vision_value)
    if selected_vision_value in vision_option_labels
    else 0
)

# --- App mode ---
app_mode = st.sidebar.radio(
    "App Mode",
    ["🤖 LLM → SVG", "🖼️ Image → SVG"],
    horizontal=True,
)

# --- Sidebar ---
with st.sidebar:
    st.header("Settings")

    if not config_labels:
        st.error("No LLM profiles found in config/llm_configs.yaml.")
        selected_generation_label = ""
        selected_vision_label = "(none)"
        generation_config = None
        vision_config = None
    else:
        selected_generation_label = st.selectbox(
            "Generation Profile",
            config_labels,
            index=generation_default_index,
        )
        generation_config = get_profile_by_label(
            configs_data["configs"], selected_generation_label
        )

        selected_vision_label = selected_vision_value
        vision_config = get_profile_by_label(
            configs_data["configs"],
            "" if selected_vision_label == "(none)" else selected_vision_label,
        )

    # Purpose selection
    selected_purpose = st.selectbox("Purpose", list(PURPOSE_MAP.keys()), index=0)

    # Generation mode
    selected_gen_mode = st.selectbox(
        "Generation Mode", list(GEN_MODE_MAP.keys()), index=0
    )

    # Vision refinement controls
    st.divider()
    st.subheader("Refinement")
    enable_refinement = st.checkbox("Enable Vision Refinement", value=False)
    max_iterations = 3
    if enable_refinement:
        selected_vision_label = st.selectbox(
            "Vision Profile",
            vision_option_labels,
            index=vision_default_index,
        )
        vision_config = get_profile_by_label(
            configs_data["configs"],
            "" if selected_vision_label == "(none)" else selected_vision_label,
        )
        max_iterations = st.number_input(
            "Max Iterations", min_value=1, max_value=5, value=3
        )
        if not vision_config:
            st.warning("Select a vision-capable profile to use refinement.")
        elif not vision_config.get("supports_vision"):
            st.warning(
                "The selected vision profile is not marked as vision-capable. Refinement will be blocked."
            )

    if config_labels:
        new_config_data = {
            "configs": configs_data["configs"],
            "selected_generation_label": selected_generation_label,
            "selected_vision_label": (
                "" if selected_vision_label == "(none)" else selected_vision_label
            ),
        }
        if new_config_data != configs_data:
            save_configs(new_config_data)
            configs_data = new_config_data

    st.divider()
    st.info("PowerPoint export converts SVG paths to native editable shapes.")

    # --- Image → SVG settings (shown only in that mode) ---
    if app_mode == "🖼️ Image → SVG":
        st.divider()
        st.subheader("Image → SVG Settings")

        # Venice API key: use the first Venice profile found
        venice_api_key = ""
        for c in configs_data["configs"]:
            if "venice" in c.get("base_url", "").lower():
                venice_api_key = c.get("api_key", "")
                break

        img_model = st.selectbox("Image Model", IMAGE_MODELS, index=0)
        img_style = st.selectbox("Style Preset", STYLE_PRESETS,
                                  index=STYLE_PRESETS.index("Flat Papercut"))
        img_num_colors = st.slider(
            "Color Count (simplicity)", 4, 64, 16,
            help="Fewer colors = simpler SVG. Increase if colors are disappearing."
        )
        img_blur = st.slider(
            "Blur Radius (detail suppression)", 0.0, 4.0, 0.5, 0.5,
            help="Higher = less detail before vectorization"
        )
        img_speckle = st.slider(
            "Filter Speckle (min path size)", 2, 50, 16,
            help="Remove tiny paths (higher = simpler)"
        )
        img_auto_enhance = st.checkbox(
            "Auto-enhance prompt for vectorization", value=True,
            help="Automatically append flat/vector style keywords to your prompt"
        )

        if not venice_api_key:
            st.warning("No Venice AI profile found in config. Add one to use this mode.")
    else:
        # Dummy values so Image→SVG block doesn't crash when mode is LLM
        venice_api_key = ""
        img_model = IMAGE_MODELS[0]
        img_style = "Flat Papercut"
        img_num_colors = 12
        img_blur = 0.5
        img_speckle = 16
        img_auto_enhance = False

# --- Main Layout ---
col1, col2 = st.columns([2, 3])

if app_mode == "🤖 LLM → SVG":
    with col1:
        st.subheader("Prompt")
        mode = st.radio(
            "Mode", ["✨ New Illustration", "🔄 Refine Current"], horizontal=True
        )
        prompt = st.text_area(
            "Instruction",
            placeholder="Describe a scene, character, or diagram...",
            height=150,
        )

        if st.button("🚀 Execute", use_container_width=True, type="primary"):
            generation_api_key = (
                generation_config.get("api_key") or os.getenv("OPENAI_API_KEY", "")
                if generation_config
                else ""
            )
            generation_base_url = generation_config.get("base_url") if generation_config else ""
            generation_model = generation_config.get("model") if generation_config else ""
            generation_prompt_profile = (
                generation_config.get("prompt_profile", "default")
                if generation_config
                else "default"
            )
            generation_request_timeout = (
                generation_config.get("request_timeout", 60.0)
                if generation_config
                else 60.0
            )
            generation_use_llm_classification = (
                generation_config.get("use_llm_classification", True)
                if generation_config
                else True
            )
            generation_api_style = (
                generation_config.get("api_style", "chat")
                if generation_config
                else "chat"
            )
            generation_max_output_tokens = (
                generation_config.get("max_output_tokens", 2048)
                if generation_config
                else 2048
            )
            generation_disable_svg_repair = (
                generation_config.get("disable_svg_repair", False)
                if generation_config
                else False
            )

            vision_api_key = (
                vision_config.get("api_key") or os.getenv("OPENAI_API_KEY", "")
                if vision_config
                else ""
            )

            if not generation_api_key:
                st.error("Missing API Key.")
            elif not prompt:
                st.warning("Please enter a prompt.")
            elif enable_refinement and not vision_config:
                st.error("Vision refinement requires a separate vision profile.")
            elif enable_refinement and not vision_config.get("supports_vision"):
                st.error("Selected vision profile is not vision-capable.")
            elif enable_refinement and not vision_api_key:
                st.error("Vision profile is missing an API key.")
            else:
                with st.status("LLM is crafting SVG...") as status:
                    st.session_state.last_result_meta = {
                        "purpose": PURPOSE_MAP[selected_purpose],
                        "generation_mode": GEN_MODE_MAP[selected_gen_mode],
                        "generation_profile": selected_generation_label,
                        "vision_profile": (
                            "" if selected_vision_label == "(none)" else selected_vision_label
                        ),
                        "request_timeout": generation_request_timeout,
                        "use_llm_classification": generation_use_llm_classification,
                        "api_style": generation_api_style,
                        "max_output_tokens": generation_max_output_tokens,
                        "error": None,
                    }
                    try:
                        llm = LLMClient(
                            api_key=generation_api_key,
                            model=generation_model,
                            base_url=generation_base_url,
                            prompt_profile=generation_prompt_profile,
                            request_timeout=generation_request_timeout,
                            use_llm_classification=generation_use_llm_classification,
                            api_style=generation_api_style,
                            max_output_tokens=generation_max_output_tokens,
                            disable_svg_repair=generation_disable_svg_repair,
                        )
                        current_svg = (
                            st.session_state.svg_code
                            if mode == "🔄 Refine Current"
                            else None
                        )

                        purpose_value = PURPOSE_MAP[selected_purpose]
                        gen_mode_value = GEN_MODE_MAP[selected_gen_mode]

                        result = llm.generate_diagram_data(
                            prompt,
                            current_svg=current_svg,
                            purpose=purpose_value,
                            generation_mode=gen_mode_value,
                        )

                        sanitized = SVGProcessor.sanitize_svg(result["svg"])
                        st.session_state.svg_code = sanitized
                        st.session_state.editor_content = sanitized
                        st.session_state["svg-editor"] = sanitized
                        st.session_state.refinement_versions = []
                        st.session_state.last_result_meta = {
                            "purpose": result["purpose"],
                            "generation_mode": result["generation_mode"],
                            "fallback": result["fallback"],
                            "repaired": result.get("repaired", False),
                            "generation_profile": selected_generation_label,
                            "vision_profile": (
                                "" if selected_vision_label == "(none)" else selected_vision_label
                            ),
                            "request_timeout": generation_request_timeout,
                            "use_llm_classification": generation_use_llm_classification,
                            "api_style": generation_api_style,
                            "max_output_tokens": generation_max_output_tokens,
                            "disable_svg_repair": generation_disable_svg_repair,
                            "error": None,
                        }

                        # Vision refinement loop
                        if enable_refinement:
                            status.update(
                                label="Running vision refinement...", state="running"
                            )
                            try:
                                vf = VisionFeedback(
                                    api_key=vision_api_key,
                                    model=vision_config.get("model"),
                                    base_url=vision_config.get("base_url"),
                                )
                                versions = vf.refine_loop(
                                    llm_client=llm,
                                    prompt=prompt,
                                    initial_svg=result["svg"],
                                    max_iterations=max_iterations,
                                    purpose=purpose_value,
                                    generation_mode=gen_mode_value,
                                )
                                st.session_state.refinement_versions = versions
                                st.session_state.selected_version = len(versions) - 1
                                sanitized_r = SVGProcessor.sanitize_svg(versions[-1]["svg"])
                                st.session_state.svg_code = sanitized_r
                                st.session_state.editor_content = sanitized_r
                                st.session_state["svg-editor"] = sanitized_r
                            except Exception as e:
                                st.warning(
                                    f"Refinement failed: {e}. Using initial generation."
                                )

                        status.update(label="Done!", state="complete", expanded=False)
                        st.rerun()
                    except Exception as e:
                        st.session_state.last_result_meta = {
                            **st.session_state.get("last_result_meta", {}),
                            "error": str(e),
                        }
                        st.error(f"Error: {e}")

        # Generation metadata display
        meta = st.session_state.get("last_result_meta", {})
        if meta:
            purpose_display = meta.get("purpose", "N/A")
            mode_display = meta.get("generation_mode", "N/A")
            generation_profile_display = meta.get("generation_profile", "N/A")
            vision_profile_display = meta.get("vision_profile") or "disabled"
            timeout_display = meta.get("request_timeout", "N/A")
            llm_classification_display = meta.get("use_llm_classification", True)
            api_style_display = meta.get("api_style", "chat")
            max_output_tokens_display = meta.get("max_output_tokens", "N/A")
            disable_repair_display = meta.get("disable_svg_repair", False)
            st.caption(
                f"Detected purpose: **{purpose_display}** | Mode: **{mode_display}** | Generation profile: **{generation_profile_display}** | Vision profile: **{vision_profile_display}** | API style: **{api_style_display}** | Max tokens: **{max_output_tokens_display}** | Repair disabled: **{disable_repair_display}** | Timeout: **{timeout_display}s** | LLM classification: **{llm_classification_display}**"
            )
            if meta.get("fallback"):
                st.warning("Code generation failed. Fell back to direct SVG mode.")
            if meta.get("repaired"):
                st.info("⚕️ SVG had XML errors that were auto-repaired by the LLM.")
            if meta.get("error"):
                st.caption(f"Last error: {meta['error']}")

        st.subheader("Manual Edit (SVG Code)")
        new_editor_val = st.text_area(
            label="SVG",
            key="svg-editor",
            height=300,
            label_visibility="collapsed",
        )
        # svg_code は常にエディタの現在値から同期する
        st.session_state.svg_code = SVGProcessor.sanitize_svg(new_editor_val)
        st.session_state.editor_content = new_editor_val

    with col2:
        st.subheader("Live Preview")

        # Version selector (only when refinement versions exist)
        versions = st.session_state.get("refinement_versions", [])
        if len(versions) > 1:
            version_labels = [f"V{v['iteration']}" for v in versions]
            selected_idx = st.select_slider(
                "Version",
                options=list(range(len(versions))),
                value=st.session_state.selected_version,
                format_func=lambda i: version_labels[i],
            )
            if selected_idx != st.session_state.selected_version:
                st.session_state.selected_version = selected_idx
                st.session_state.svg_code = versions[selected_idx]["svg"]
                st.session_state.editor_content = versions[selected_idx]["svg"]

            # Show feedback for selected version
            feedback = versions[selected_idx].get("feedback")
            if feedback:
                with st.expander("Vision Feedback", expanded=False):
                    st.markdown(feedback)

        # SVG preview
        try:
            b64 = base64.b64encode(st.session_state.svg_code.encode("utf-8")).decode(
                "utf-8"
            )
            st.markdown(
                f'<img src="data:image/svg+xml;base64,{b64}" style="width: 100%; border: 1px solid #ccc; background-color: white;" />',
                unsafe_allow_html=True,
            )
        except Exception as e:
            st.error(f"Render error: {e}")

        st.divider()
        if st.button("📦 Generate & Download Native PPTX", use_container_width=True):
            with st.spinner("Converting SVG paths to PowerPoint shapes..."):
                try:
                    pptx_data = PPTXNativeExporter.generate_pptx_from_data(
                        st.session_state.svg_code
                    )
                    if not pptx_data:
                        st.error(
                            "PPTX generation failed: SVG could not be parsed. Check the SVG code for invalid XML (e.g. unescaped '&')."
                        )
                    else:
                        st.download_button(
                            label="📥 Download Now",
                            data=pptx_data,
                            file_name="illustration_native.pptx",
                            mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                            use_container_width=True,
                        )
                except Exception as e:
                    st.error(f"Export failed: {e}")

else:  # 🖼️ Image → SVG
    from image_vectorizer import generate_image, preprocess_image, vectorize_image

    # --- Session state init for 2-stage flow ---
    if "img_stage" not in st.session_state:
        st.session_state.img_stage = "generate"  # "generate" | "vectorize"
    if "img_locked_bytes" not in st.session_state:
        st.session_state.img_locked_bytes = None  # PNG bytes of locked image
    if "img_locked_prompt" not in st.session_state:
        st.session_state.img_locked_prompt = ""
    if "img_locked_effective_prompt" not in st.session_state:
        st.session_state.img_locked_effective_prompt = ""

    # ── STAGE 1: Image Generation ──────────────────────────────────────────
    if st.session_state.img_stage == "generate":
        with col1:
            st.subheader("Step 1 — Generate Image")

            img_prompt = st.text_area(
                "Illustration description",
                value=st.session_state.img_locked_prompt,
                placeholder="例: 緊迫した会議風景、フラットイラスト",
                height=150,
            )

            gen_col1, gen_col2 = st.columns(2)
            with gen_col1:
                gen_btn = st.button("🎨 Generate", use_container_width=True, type="primary")
            with gen_col2:
                use_btn = st.button(
                    "➡️ Use this image",
                    use_container_width=True,
                    disabled=st.session_state.img_locked_bytes is None,
                )

            if gen_btn:
                if not venice_api_key:
                    st.error("No Venice AI profile found. Add one to config/llm_configs.yaml.")
                elif not img_prompt:
                    st.warning("Please enter a prompt.")
                else:
                    with st.spinner("Generating image via Venice AI..."):
                        try:
                            # Build effective prompt
                            if img_auto_enhance:
                                effective_prompt = (
                                    img_prompt
                                    + ", flat vector illustration, bold solid-color areas, "
                                    "thick clean outlines, minimal detail, geometric shapes, "
                                    "limited palette, white background"
                                )
                            else:
                                effective_prompt = img_prompt

                            pil_img = generate_image(
                                prompt=effective_prompt,
                                model=img_model,
                                api_key=venice_api_key,
                                style_preset=None if img_style == "(none)" else img_style,
                            )
                            buf = io.BytesIO()
                            pil_img.save(buf, format="PNG")
                            st.session_state.img_locked_bytes = buf.getvalue()
                            st.session_state.img_locked_prompt = img_prompt
                            st.session_state.img_locked_effective_prompt = effective_prompt
                            st.rerun()
                        except Exception as e:
                            st.error(f"Image generation failed: {e}")

            if use_btn:
                st.session_state.img_stage = "vectorize"
                st.rerun()

        with col2:
            st.subheader("Generated Image")
            if st.session_state.img_locked_bytes:
                ep = st.session_state.img_locked_effective_prompt
                if ep:
                    st.caption(f"**Prompt sent to Venice AI:** {ep}")
                st.image(st.session_state.img_locked_bytes, use_container_width=True)
                st.caption("✅ Image ready. Click **➡️ Use this image** to proceed to vectorization.")
            else:
                st.info("Generate an image to see the preview here.")

    # ── STAGE 2: Vectorization ─────────────────────────────────────────────
    else:
        with col1:
            st.subheader("Step 2 — Vectorize")

            # Back button
            if st.button("← Back to image generation"):
                st.session_state.img_stage = "generate"
                st.rerun()

            st.caption(f"**Image prompt:** {st.session_state.img_locked_prompt}")

            st.divider()
            st.subheader("Vectorization Parameters")

            v_num_colors = st.slider(
                "Color Count", 4, 64, img_num_colors,
                help="Increase to recover colors that were disappearing."
            )
            v_blur = st.slider(
                "Blur Radius", 0.0, 4.0, img_blur, 0.5,
                help="Higher = less detail before vectorization"
            )
            v_speckle = st.slider(
                "Filter Speckle (min path size)", 2, 50, img_speckle,
                help="Remove tiny paths (higher = simpler)"
            )

            if st.button("⚡ Vectorize", use_container_width=True, type="primary"):
                with st.spinner("Vectorizing..."):
                    try:
                        from PIL import Image as PILImage
                        pil_img = PILImage.open(io.BytesIO(st.session_state.img_locked_bytes))
                        # preprocess with blur only; color quantization is done inside vectorize_image via k-means
                        processed = preprocess_image(pil_img, blur_radius=v_blur, num_colors=v_num_colors)
                        svg = vectorize_image(
                            processed,
                            vtracer_params={
                                "filter_speckle": v_speckle,
                                "color_precision": v_num_colors,  # use same color count for k-means
                            },
                        )
                        sanitized = SVGProcessor.sanitize_svg(svg)
                        st.session_state.svg_code = sanitized
                        st.session_state.editor_content = sanitized
                        st.session_state["svg-editor-img"] = sanitized  # text_area key を明示更新

                        # Store processed image bytes for preview
                        proc_buf = io.BytesIO()
                        processed.save(proc_buf, format="PNG")
                        st.session_state["img_processed_bytes"] = proc_buf.getvalue()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Vectorization failed: {e}")

            st.divider()
            st.subheader("SVG Code")
            # key のみ指定 — value は session_state["svg-editor-img"] から自動で反映される
            if "svg-editor-img" not in st.session_state:
                st.session_state["svg-editor-img"] = st.session_state.get("editor_content", "")
            new_editor_val_img = st.text_area(
                label="SVG",
                key="svg-editor-img",
                height=200,
                label_visibility="collapsed",
            )
            st.session_state.svg_code = SVGProcessor.sanitize_svg(new_editor_val_img)
            st.session_state.editor_content = new_editor_val_img

        with col2:
            # Show source image + preprocessed side by side
            img_col, proc_col = st.columns(2)
            with img_col:
                st.caption("🖼️ Source image")
                if st.session_state.img_locked_bytes:
                    st.image(st.session_state.img_locked_bytes, use_container_width=True)
            with proc_col:
                st.caption("🎨 After preprocessing")
                proc_bytes = st.session_state.get("img_processed_bytes")
                if proc_bytes:
                    st.image(proc_bytes, use_container_width=True)
                else:
                    st.info("Run vectorization to see preprocessed image.")

            st.subheader("SVG Preview")
            try:
                b64 = base64.b64encode(st.session_state.svg_code.encode("utf-8")).decode("utf-8")
                st.markdown(
                    f'<img src="data:image/svg+xml;base64,{b64}" style="width: 100%; border: 1px solid #ccc; background-color: white;" />',
                    unsafe_allow_html=True,
                )
            except Exception as e:
                st.error(f"Render error: {e}")

            st.divider()
            if st.button("📦 Generate & Download Native PPTX", use_container_width=True, key="pptx_img"):
                with st.spinner("Converting SVG paths to PowerPoint shapes..."):
                    try:
                        pptx_data = PPTXNativeExporter.generate_pptx_from_data(
                            st.session_state.svg_code
                        )
                        if not pptx_data:
                            st.error("PPTX generation failed.")
                        else:
                            st.download_button(
                                label="📥 Download Now",
                                data=pptx_data,
                                file_name="illustration_native.pptx",
                                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                                use_container_width=True,
                                key="dl_pptx_img",
                            )
                    except Exception as e:
                        st.error(f"Export failed: {e}")
