import streamlit as st
import os
import yaml
import json
from dotenv import load_dotenv
from streamlit_ace import st_ace
from llm_client import LLMClient
from pptx_exporter import PPTXNativeExporter
import base64

load_dotenv()

CONFIG_FILE = "config/llm_configs.yaml"

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

# State management: SVG String instead of JSON
if "svg_code" not in st.session_state:
    st.session_state.svg_code = '<svg width="800" height="600" viewBox="0 0 800 600" xmlns="http://www.w3.org/2000/svg"><rect x="0" y="0" width="800" height="600" fill="#f0f8ff"/><circle cx="400" cy="300" r="100" fill="#ff6347"/></svg>'
if "editor_content" not in st.session_state:
    st.session_state.editor_content = st.session_state.svg_code

configs_data = load_configs()
config_labels = [c["label"] for c in configs_data["configs"]]
default_index = config_labels.index(configs_data["selected_label"]) if configs_data["selected_label"] in config_labels else 0

with st.sidebar:
    st.header("Settings")
    selected_label = st.selectbox("LLM Profile", config_labels, index=default_index)
    current_config = next((c for c in configs_data["configs"] if c["label"] == selected_label), None)
    if current_config:
        api_key = current_config.get("api_key") or os.getenv("OPENAI_API_KEY", "")
        base_url, model = current_config.get("base_url"), current_config.get("model")
    else: api_key, base_url, model = "", "", ""
    st.info("PowerPoint export converts SVG paths to native editable shapes.")

col1, col2 = st.columns([2, 3])

with col1:
    st.subheader("Prompt")
    mode = st.radio("Mode", ["✨ New Illustration", "🔄 Refine Current"], horizontal=True)
    prompt = st.text_area("Instruction", placeholder="Describe a scene, character, or diagram...", height=150)
    
    if st.button("🚀 Execute", use_container_width=True, type="primary"):
        if not api_key:
            st.error("Missing API Key.")
        elif not prompt:
            st.warning("Please enter a prompt.")
        else:
            with st.status("LLM is crafting SVG...") as status:
                try:
                    llm = LLMClient(api_key=api_key, model=model, base_url=base_url)
                    current_svg = st.session_state.svg_code if mode == "🔄 Refine Current" else None
                    
                    new_svg = llm.generate_diagram_data(prompt, current_svg=current_svg)
                    
                    # Update state
                    st.session_state.svg_code = new_svg
                    st.session_state.editor_content = new_svg
                    
                    status.update(label="Done!", state="complete", expanded=False)
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

    st.subheader("Manual Edit (SVG Code)")
    # ACE Editor for SVG
    new_editor_val = st_ace(
        value=st.session_state.editor_content,
        language="xml", # SVG is XML
        theme="monokai",
        height=300,
        key="ace-editor"
    )
    if new_editor_val != st.session_state.editor_content:
        st.session_state.svg_code = new_editor_val
        st.session_state.editor_content = new_editor_val

with col2:
    st.subheader("Live Preview")
    try:
        # SVGを直接プレビュー
        b64 = base64.b64encode(st.session_state.svg_code.encode('utf-8')).decode('utf-8')
        st.markdown(f'<img src="data:image/svg+xml;base64,{b64}" style="width: 100%; border: 1px solid #ccc; background-color: white;" />', unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Render error: {e}")
    
    st.divider()
    if st.button("📦 Generate & Download Native PPTX", use_container_width=True):
        with st.spinner("Converting SVG paths to PowerPoint shapes..."):
            try:
                pptx_data = PPTXNativeExporter.generate_pptx_from_data(st.session_state.svg_code)
                st.download_button(
                    label="📥 Download Now",
                    data=pptx_data,
                    file_name="illustration_native.pptx",
                    mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"Export failed: {e}")
