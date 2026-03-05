# Spec: SVG Preview & Editor (ui)

## ADDED Requirements

### Requirement: Real-time SVG Preview
The system SHALL display the SVG rendered on the screen immediately after it's generated or edited.

#### Scenario: Generate and Display
- **Given:** The LLM client has returned an SVG string.
- **When:** The application state is updated.
- **Then:** The SVG is displayed in a Streamlit container as an interactive preview.

### Requirement: Interactive SVG Code Editing
The user SHALL be able to modify the raw SVG code directly through a syntax-highlighted editor.

#### Scenario: Manual Adjustment
- **Given:** The generated SVG has a red circle.
- **When:** The user changes `<circle fill="red" ... />` to `<circle fill="green" ... />` in the `streamlit-ace` editor.
- **Then:** The preview is updated to show a green circle.

### Requirement: Responsive Layout
The UI SHALL provide a clean and responsive layout for different screen sizes.

#### Scenario: Split View
- **Given:** The application is running on a desktop.
- **When:** The user enters a prompt.
- **Then:** The editor and the preview should be side-by-side or stacked logically for easy interaction.
