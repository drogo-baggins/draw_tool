# Design: LLM Drawing Tool (init-llm-drawing-tool)

## System Architecture
The application is a single-page Streamlit app that coordinates between the user interface, an LLM service, and an export engine.

### Data Flow
1. **User Prompt:** The user enters a description in a Streamlit text input.
2. **LLM Generation:** A backend service (OpenAI or Llama.cpp) generates SVG code.
3. **SVG Validation & Display:**
    - The code is sanitized.
    - It's displayed using `st.html()` after base64 encoding.
4. **Code Editing:** The user fine-tunes the SVG code using `streamlit-ace`.
5. **Export Processing:**
    - User clicks the export button.
    - The SVG is converted to PNG (using `cairosvg`) for maximum PPTX compatibility.
    - `python-pptx` inserts the PNG into a new slide.
6. **Download:** The generated .pptx is provided as a Streamlit download.

## Core Components
- **UI Engine (`app.py`):** Handles the main loop, state management, and user interaction.
- **LLM Engine (`llm_client.py`):** Abstract interface for calling LLMs to generate SVG.
- **SVG Engine (`svg_processor.py`):** Manages SVG sanitization, encoding, and display logic.
- **Export Engine (`pptx_exporter.py`):** Handles the conversion and PPTX assembly.

## Trade-offs & Decisions
- **cairosvg vs. Aspose.Slides:** Aspose.Slides is powerful but commercial. `python-pptx` combined with `cairosvg` is open-source and sufficient for basic insertion.
- **Real-time Preview:** Base64 encoding for `st.html()` ensures the SVG is rendered correctly across different browsers without external file dependencies.
- **SVG Code Editor:** Using `streamlit-ace` provides syntax highlighting and a developer-friendly experience for direct manipulation.

## Technical Requirements
- Python 3.9+
- OpenAI API Key (or local Llama.cpp instance)
- Cairo library installed on the host system (required by `cairosvg`).
