# Tasks: LLM Drawing Tool (init-llm-drawing-tool)

## Implementation Phases

### Phase 1: Environment Setup & Scaffold
- [x] Initialize Python virtual environment and install dependencies (`streamlit`, `streamlit-ace`, `cairosvg`, `python-pptx`, `openai`).
- [x] Create basic `app.py` structure.

### Phase 2: LLM Integration
- [x] Implement `llm_client.py` for OpenAI API calls.
- [x] Implement SVG code generation prompt.
- [x] **Validation:** Run a script that inputs a prompt and prints generated SVG code. (Verified manually via UI integration)

### Phase 3: SVG Preview & Editor
- [x] Implement `svg_processor.py` for sanitization and base64 encoding.
- [x] Integrate `st.html()` and `streamlit-ace` in `app.py`.
- [x] **Validation:** Verify that changes in `streamlit-ace` update the preview in real-time. (Verified manually)

### Phase 4: PowerPoint Export
- [x] Implement `pptx_exporter.py` using `python-pptx` and `cairosvg`.
- [x] Add export button and download functionality to `app.py`.
- [x] **Validation:** Generate a .pptx file and confirm it opens correctly with the diagram in PowerPoint. (Verified manually, depends on system Cairo)

### Phase 5: Polishing & Refinement
- [x] Add error handling for invalid SVG code and API failures.
- [x] Refine the UI (sidebar for settings, layout adjustments).
- [x] **Validation:** Conduct end-to-end testing from prompt to .pptx download. (Verified manually)

## Dependencies
- LLM service (OpenAI or local Llama.cpp)
- Cairo system dependency
