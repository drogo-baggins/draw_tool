# Project Context: LLM Drawing Tool

## Purpose
A Streamlit-based graphical user interface that allows users to generate, preview, and edit SVG diagrams using natural language prompts, and export the final result into PowerPoint presentations.

## Tech Stack
- **Frontend/UI:** Streamlit
- **LLM Integration:** OpenAI SDK (Supports OpenAI-compatible APIs & custom Base URL)
- **Editor:** streamlit-ace (for direct SVG code modification)
- **Export/Conversion:** python-pptx
- **Image Processing:** cairosvg (SVG to PNG conversion for PPTX compatibility)

## Project Conventions

### Code Style
- Pythonic (PEP 8)
- Type hints for core functions
- Modular design:
    - `app.py`: UI & State Management
    - `llm_client.py`: OpenAI-compatible API client
    - `svg_processor.py`: SVG Sanitization & Encoding
    - `pptx_exporter.py`: PPTX generation & PNG conversion

### Architecture Patterns
- Single-page Streamlit application
- State-driven UI for real-time preview
- Support for custom LLM Endpoints (Local LLM, etc.) via `base_url`.

### Testing Strategy
- Unit tests for SVG generation parsing
- Export validation (check if PPTX contains the image)

## Domain Context
The tool aims to bridge the gap between AI-generated visuals and professional presentation workflows by providing a visual intermediate step.

## Important Constraints
- SVG must be valid for cairosvg conversion.
- PPTX export should handle transparency if possible.

## External Dependencies
- OpenAI API (optional local Llama.cpp fallback)
- Cairo (system dependency for cairosvg)
