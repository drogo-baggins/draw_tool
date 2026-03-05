# Spec: PowerPoint Export (export)

## ADDED Requirements

### Requirement: Export SVG to PPTX
The system SHALL generate a PowerPoint (.pptx) file containing the current SVG diagram.

#### Scenario: Basic Export
- **Given:** A valid SVG diagram is displayed in the preview.
- **When:** The user clicks "Export to PPTX".
- **Then:** The system converts the SVG to a PNG (using `cairosvg`) and inserts it into a new slide of a .pptx file.

### Requirement: Handle Conversion Errors
The system SHALL notify the user if the SVG cannot be converted to a PNG for PPTX insertion.

#### Scenario: Invalid SVG Code
- **Given:** The user has accidentally entered invalid XML in the editor.
- **When:** The user clicks "Export to PPTX".
- **Then:** The system displays an error message: "Failed to convert SVG to PNG. Please check the SVG code for errors."

### Requirement: Download Functionality
The user SHALL be able to download the generated .pptx file directly through the browser.

#### Scenario: Download Trigger
- **Given:** The PPTX file has been generated successfully.
- **When:** The user clicks the "Download" button.
- **Then:** The browser prompts the user to save the file.
