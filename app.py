import streamlit as st
import os
import yaml
from dotenv import load_dotenv
from llm_client import LLMClient
from pptx_exporter import PPTXNativeExporter
from svg_processor import SVGProcessor
from vision_feedback import VisionFeedback
import base64

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
}


def load_configs():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    return {"configs": [], "selected_label": ""}


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
default_index = (
    config_labels.index(configs_data["selected_label"])
    if configs_data["selected_label"] in config_labels
    else 0
)

# --- Sidebar ---
with st.sidebar:
    st.header("Settings")

    # LLM Profile (unchanged)
    selected_label = st.selectbox("LLM Profile", config_labels, index=default_index)
    current_config = next(
        (c for c in configs_data["configs"] if c["label"] == selected_label), None
    )
    if current_config:
        api_key = current_config.get("api_key") or os.getenv("OPENAI_API_KEY", "")
        base_url, model = current_config.get("base_url"), current_config.get("model")
    else:
        api_key, base_url, model = "", "", ""

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
        max_iterations = st.number_input(
            "Max Iterations", min_value=1, max_value=5, value=3
        )

    st.divider()
    st.info("PowerPoint export converts SVG paths to native editable shapes.")

# --- Main Layout ---
col1, col2 = st.columns([2, 3])

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
        if not api_key:
            st.error("Missing API Key.")
        elif not prompt:
            st.warning("Please enter a prompt.")
        else:
            with st.status("LLM is crafting SVG...") as status:
                try:
                    llm = LLMClient(api_key=api_key, model=model, base_url=base_url)
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
                    }

                    # Vision refinement loop
                    if enable_refinement:
                        status.update(
                            label="Running vision refinement...", state="running"
                        )
                        try:
                            vf = VisionFeedback(
                                api_key=api_key, model=model, base_url=base_url
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
                    st.error(f"Error: {e}")

    # Generation metadata display
    meta = st.session_state.get("last_result_meta", {})
    if meta:
        purpose_display = meta.get("purpose", "N/A")
        mode_display = meta.get("generation_mode", "N/A")
        st.caption(
            f"Detected purpose: **{purpose_display}** | Mode: **{mode_display}**"
        )
        if meta.get("fallback"):
            st.warning("Code generation failed. Fell back to direct SVG mode.")
        if meta.get("repaired"):
            st.info("⚕️ SVG had XML errors that were auto-repaired by the LLM.")

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
