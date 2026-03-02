## MODIFIED Requirements

### Requirement: Generate SVG from Natural Language Prompt

The system SHALL translate a user's description of a diagram into a valid, standalone SVG string, using a generation pipeline selected based on the content purpose and generation mode.

The system SHALL support the following generation modes:

- **Direct SVG (Classic)**: LLM outputs SVG code directly as text (existing behavior, preserved as default fallback).
- **Code Generation**: LLM outputs Python code using `drawsvg` library, which is executed in a sandboxed environment to produce SVG.

The system SHALL support the following purpose classifications:

- `diagram`: Flowcharts, org charts, ER diagrams, network diagrams
- `icon`: Single icons, symbols, logos
- `infographic`: Data visualization, statistics display
- `flat_illustration`: Flat design scene illustrations
- `classic`: General SVG requests (backward-compatible default)

#### Scenario: Basic Shape Request

- **GIVEN** the user provides the prompt "a blue circle".
- **WHEN** the LLM client processes the request.
- **THEN** the system returns a string containing a `<svg>` tag with a `<circle fill="blue" ... />`.

#### Scenario: Complex Diagram Request

- **GIVEN** the user provides the prompt "a sales funnel with three stages: Lead, Prospect, Customer".
- **WHEN** the LLM client processes the request.
- **THEN** the system returns a string containing a structured SVG representing the funnel with the specified labels.

#### Scenario: Purpose Auto-Classification

- **GIVEN** the user provides the prompt "organizational chart of a marketing team with 5 members".
- **WHEN** the system processes the request.
- **THEN** the system classifies the purpose as `diagram` and applies the diagram-specific prompt template.

#### Scenario: Code Generation Mode

- **GIVEN** the user selects "Code Generation" mode and provides the prompt "a radial bar chart showing quarterly sales".
- **WHEN** the LLM client processes the request.
- **THEN** the system generates Python code using `drawsvg`, executes it in a sandbox, and returns the resulting SVG string.

#### Scenario: Code Generation Fallback

- **GIVEN** code generation mode is selected but the generated code fails to execute.
- **WHEN** the sandbox returns an error (syntax error, timeout, or invalid output).
- **THEN** the system falls back to direct SVG generation and notifies the user of the fallback.

### Requirement: Handle LLM API Failures Gracefully

The system SHALL detect and report errors from the LLM service to the user.

#### Scenario: API Timeout

- **GIVEN** the LLM service is unresponsive.
- **WHEN** the system attempts to generate an SVG.
- **THEN** the system displays an error message: "LLM service timed out. Please try again later."

#### Scenario: Code Execution Timeout

- **GIVEN** the LLM generated Python code that exceeds the execution time limit (10 seconds).
- **WHEN** the sandbox terminates the process.
- **THEN** the system displays an error message indicating the code took too long and suggests trying direct SVG mode.

## ADDED Requirements

### Requirement: Purpose-Specific Prompt Templates

The system SHALL maintain a library of purpose-specific system prompts as YAML template files, each containing design rules, color palettes, layout guidelines, and example patterns optimized for the target purpose.

The system SHALL load prompt templates from `prompt_templates/` directory and select the appropriate template based on purpose classification.

#### Scenario: Diagram Template Application

- **GIVEN** the purpose is classified as `diagram`.
- **WHEN** the system prepares the LLM request.
- **THEN** the system applies the diagram template containing grid-aligned layout rules, professional color palette (#2196F3 primary, #FF9800 accent), and connector styling guidelines.

#### Scenario: Template Fallback to Classic

- **GIVEN** no purpose-specific template matches or classification fails.
- **WHEN** the system prepares the LLM request.
- **THEN** the system applies the `classic.yaml` template (equivalent to current behavior).

### Requirement: Sandboxed Code Execution

The system SHALL execute LLM-generated Python code in a sandboxed subprocess environment with security constraints.

The sandbox MUST enforce:

- Import whitelist: only `drawsvg`, `math`, `colorsys`, `random` are permitted
- Execution timeout: 10 seconds maximum
- File system isolation: execution in a temporary directory
- No network access

#### Scenario: Valid Code Execution

- **GIVEN** the LLM generates valid Python code that imports `drawsvg` and `math`.
- **WHEN** the sandbox executes the code.
- **THEN** the system captures the SVG output from stdout and returns it as a valid SVG string.

#### Scenario: Blocked Import Attempt

- **GIVEN** the LLM generates code containing `import os` or `import subprocess`.
- **WHEN** the system performs static analysis before execution.
- **THEN** the system rejects the code and returns an error indicating the import is not allowed.

#### Scenario: Infinite Loop Protection

- **GIVEN** the LLM generates code containing an infinite loop.
- **WHEN** the sandbox reaches the 10-second timeout.
- **THEN** the subprocess is terminated and an error is returned to the user.

### Requirement: Vision Feedback Loop

The system SHALL optionally refine generated SVGs through a vision-model evaluation loop.

The refinement loop:

1. Renders the SVG to PNG (using resvg-py)
2. Sends the PNG to a vision-capable model (e.g., GPT-4V) for quality evaluation
3. Feeds the evaluation back to the generating LLM for improvement
4. Repeats up to a configurable maximum (default: 3 iterations)

The refinement loop MUST be opt-in (default: disabled).

#### Scenario: Refinement Improves Quality

- **GIVEN** the user enables the refinement loop and generates an SVG.
- **WHEN** the vision model identifies misaligned elements in iteration 1.
- **THEN** the system feeds the alignment feedback to the LLM, which generates an improved SVG in iteration 2.

#### Scenario: Refinement Respects Maximum Iterations

- **GIVEN** the refinement loop is set to maximum 3 iterations.
- **WHEN** all 3 iterations complete.
- **THEN** the system stops refinement and presents the final version, regardless of remaining improvement potential.

#### Scenario: User Selects Intermediate Version

- **GIVEN** the refinement loop produces 3 versions of the SVG.
- **WHEN** the user reviews the versions.
- **THEN** the user can select any of the 3 versions (not just the final one) as the active SVG.

### Requirement: Component Library Composition

The system SHALL provide a component-based SVG generation mode where the LLM selects and arranges pre-built SVG components via JSON instructions, and a composition engine assembles the final SVG deterministically.

The component library MUST:

- Contain only MIT or CC0 licensed SVG assets
- Be managed via a `manifest.json` with metadata (id, name, category, tags, dimensions, license)
- Support categories: icons, shapes, decorations
- Be extensible (add new components without code changes)

#### Scenario: Component-Based Diagram

- **GIVEN** the user requests "a simple workflow: idea → design → build" in component mode.
- **WHEN** the LLM outputs a JSON composition specifying components and positions.
- **THEN** the composition engine assembles an SVG using pre-built components for boxes, arrows, and text labels.

#### Scenario: Unknown Component Reference

- **GIVEN** the LLM references a component ID not present in the manifest.
- **WHEN** the composition engine processes the JSON.
- **THEN** the system skips the unknown component and logs a warning, producing a partial result rather than failing entirely.
