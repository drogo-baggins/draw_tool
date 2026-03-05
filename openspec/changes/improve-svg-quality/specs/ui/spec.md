## ADDED Requirements

### Requirement: Purpose Selection Control

The system SHALL provide a dropdown control in the UI for selecting the SVG generation purpose.

The dropdown MUST include the following options:

- **Auto** (default): LLM auto-classifies the purpose from the prompt
- **Diagram**: Flowcharts, org charts, ER diagrams
- **Icon**: Single icons, symbols, logos
- **Infographic**: Data visualization, statistics
- **Flat Illustration**: Flat design scene illustrations
- **Classic**: Direct SVG generation (backward-compatible)

The selected purpose MUST be displayed alongside the generation result for transparency.

#### Scenario: Auto-Classification Display

- **GIVEN** the user leaves the purpose dropdown on "Auto" and enters a prompt.
- **WHEN** the SVG is generated.
- **THEN** the UI displays the auto-detected purpose (e.g., "Detected: Diagram") near the result.

#### Scenario: Manual Purpose Override

- **GIVEN** the user selects "Icon" from the purpose dropdown.
- **WHEN** the SVG is generated.
- **THEN** the system uses the icon-specific prompt template regardless of the prompt content.

### Requirement: Generation Mode Selection

The system SHALL provide a control in the UI for selecting the SVG generation mode.

The options MUST include:

- **Direct SVG** (default): LLM outputs SVG text directly
- **Code Generation**: LLM outputs Python code executed in a sandbox to produce SVG

#### Scenario: Mode Selection Persists

- **GIVEN** the user selects "Code Generation" mode.
- **WHEN** the user generates multiple SVGs in the same session.
- **THEN** the selected mode persists across generations until changed.

#### Scenario: Mode Fallback Notification

- **GIVEN** the user selected "Code Generation" but the code execution fails.
- **WHEN** the system falls back to direct SVG generation.
- **THEN** the UI displays a notification: "Code generation failed. Fell back to direct SVG mode."

### Requirement: Vision Refinement Controls

The system SHALL provide UI controls for the optional vision feedback refinement loop.

The controls MUST include:

- A checkbox to enable/disable refinement (default: disabled)
- A numeric input for maximum iterations (range: 1-5, default: 3)

When refinement is active, the UI MUST display:

- Progress indicator for each iteration ("Refining 1/3...", "Refining 2/3...")
- A version selector allowing the user to pick any intermediate version

#### Scenario: Enable Refinement

- **GIVEN** the user checks "Enable Refinement" and sets max iterations to 3.
- **WHEN** the SVG is generated.
- **THEN** the system runs up to 3 refinement iterations, showing progress for each.

#### Scenario: Version Selection After Refinement

- **GIVEN** the refinement loop produced 3 versions.
- **WHEN** the user views the results.
- **THEN** the UI provides a version slider or tabs (V1, V2, V3) to compare and select any version.

#### Scenario: Refinement Disabled by Default

- **GIVEN** a new user opens the application.
- **WHEN** the UI loads.
- **THEN** the "Enable Refinement" checkbox is unchecked and refinement controls are collapsed/hidden.

### Requirement: Component Mode Selection

The system SHALL provide a UI mode for component-based SVG generation.

When component mode is selected, the system generates SVGs by composing pre-built SVG components (including professional-quality people/face assets and anchor-equipped shapes) via LLM JSON instructions, with automatic connection routing by the composition engine.

#### Scenario: Component Mode Generation

- **GIVEN** the user selects "Component" generation mode.
- **WHEN** the user enters a prompt and generates.
- **THEN** the system uses the component library composition pipeline (LLM JSON → composition engine with anchor-based connection routing) instead of direct LLM SVG generation.

#### Scenario: Component Mode People Rendering

- **GIVEN** the user selects "Component" mode and enters a prompt involving people (e.g., "team meeting").
- **WHEN** the SVG is generated.
- **THEN** the result contains professional-quality pre-built people SVGs rather than LLM-generated human figures.
