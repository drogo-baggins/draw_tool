# Spec: LLM Diagram Generation (llm)

## ADDED Requirements

### Requirement: Generate SVG from Natural Language Prompt
The system SHALL translate a user's description of a diagram into a valid, standalone SVG string.

#### Scenario: Basic Shape Request
- **Given:** The user provides the prompt "a blue circle".
- **When:** The LLM client processes the request.
- **Then:** The system returns a string containing a `<svg>` tag with a `<circle fill="blue" ... />`.

#### Scenario: Complex Diagram Request
- **Given:** The user provides the prompt "a sales funnel with three stages: Lead, Prospect, Customer".
- **When:** The LLM client processes the request.
- **Then:** The system returns a string containing a structured SVG representing the funnel with the specified labels.

### Requirement: Handle LLM API Failures Gracefully
The system SHALL detect and report errors from the LLM service to the user.

#### Scenario: API Timeout
- **Given:** The LLM service is unresponsive.
- **When:** The system attempts to generate an SVG.
- **Then:** The system displays an error message: "LLM service timed out. Please try again later."
