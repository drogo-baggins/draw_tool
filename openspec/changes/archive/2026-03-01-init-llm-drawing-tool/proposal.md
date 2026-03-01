# Proposal: LLM Drawing Tool (init-llm-drawing-tool)

## Overview
This proposal outlines the implementation of a Streamlit-based application that enables users to generate, preview, and edit SVG diagrams via LLM prompts and export them to PowerPoint.

## Motivation
Bridging the gap between AI text generation and professional visual communication. Users can often describe a diagram but lack the tools or time to draw it manually in professional software.

## Change ID
`init-llm-drawing-tool`

## Capabilities
- **LLM Diagram Generation:** Translate natural language into valid SVG code.
- **Real-time SVG Preview:** Immediate feedback on the generated SVG.
- **Interactive SVG Editor:** Allow manual fine-tuning using `streamlit-ace`.
- **PowerPoint Integration:** Export the diagram into a .pptx file with high-fidelity conversion.

## Success Criteria
- [ ] User can input a prompt and receive an SVG.
- [ ] SVG is displayed on the screen.
- [ ] User can edit the SVG code and see the changes reflected.
- [ ] User can download a .pptx file containing the diagram.
- [ ] The .pptx file contains a PNG or SVG representation that is correctly rendered in PowerPoint.
