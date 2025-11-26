# Requirements Document

## Introduction

The KEPLER Web Interface provides a user-friendly web application for interacting with the KEPLER fact-verification system. The interface consists of two main components: a REST API backend that exposes the verification pipeline, and a responsive web frontend that allows users to submit claims, view results, and explore the verification process in detail.

## Glossary

- **KEPLER Web Interface**: The complete web application including API and frontend
- **REST API**: The backend service that exposes KEPLER pipeline functionality via HTTP endpoints
- **Web Frontend**: The browser-based user interface for interacting with KEPLER
- **Verification Session**: A single fact-checking request and its associated results
- **Evidence Panel**: A UI component displaying retrieved evidence sources
- **Reasoning Chain Viewer**: A UI component showing step-by-step verification reasoning
- **Confidence Indicator**: A visual representation of the verification confidence score
- **LLM Selector**: A UI component for choosing which language models to use

## Requirements

### Requirement 1

**User Story:** As a user, I want to access KEPLER through a web browser, so that I can verify claims without installing software or using command-line tools.

#### Acceptance Criteria

1. WHEN a user navigates to the application URL THEN the Web Frontend SHALL load and display the main interface
2. WHEN the main interface loads THEN the Web Frontend SHALL display an input form for submitting claims
3. WHEN the main interface loads THEN the Web Frontend SHALL be responsive and functional on desktop browsers
4. WHEN the main interface loads THEN the Web Frontend SHALL be responsive and functional on mobile browsers
5. WHEN the application encounters a loading error THEN the Web Frontend SHALL display a clear error message

### Requirement 2

**User Story:** As a user, I want to submit text claims through the web interface, so that I can verify factual statements easily.

#### Acceptance Criteria

1. WHEN a user types text into the claim input field THEN the Web Frontend SHALL accept the text without character limits beyond reasonable bounds
2. WHEN a user submits a claim THEN the Web Frontend SHALL validate that the claim is not empty or whitespace-only
3. WHEN a user submits a valid claim THEN the Web Frontend SHALL send the claim to the REST API
4. WHEN the API processes the claim THEN the Web Frontend SHALL display a loading indicator
5. WHEN the API returns results THEN the Web Frontend SHALL display the verification verdict

### Requirement 3

**User Story:** As a user, I want to upload images along with text claims, so that I can verify multimodal content.

#### Acceptance Criteria

1. WHEN a user clicks the image upload button THEN the Web Frontend SHALL open a file selection dialog
2. WHEN a user selects an image file THEN the Web Frontend SHALL validate the file type is a supported image format
3. WHEN a user selects an image file THEN the Web Frontend SHALL validate the file size is within acceptable limits
4. WHEN a valid image is selected THEN the Web Frontend SHALL display a preview of the image
5. WHEN a user submits a claim with an image THEN the Web Frontend SHALL send both text and image data to the REST API

### Requirement 4

**User Story:** As a user, I want to select which language models to use for verification, so that I can customize the verification process.

#### Acceptance Criteria

1. WHEN the interface loads THEN the Web Frontend SHALL display a list of available language models
2. WHEN a user views the model list THEN the Web Frontend SHALL show model names and providers for each option
3. WHEN a user selects models THEN the Web Frontend SHALL allow selection of at least one model
4. WHEN a user selects models THEN the Web Frontend SHALL allow selection of multiple models
5. WHEN a user submits a claim THEN the Web Frontend SHALL include the selected models in the API request

### Requirement 5

**User Story:** As a user, I want to see the verification verdict clearly displayed, so that I can quickly understand if a claim is supported or refuted.

#### Acceptance Criteria

1. WHEN verification completes THEN the Web Frontend SHALL display the verdict as Supported, Refuted, or Not Enough Information
2. WHEN displaying the verdict THEN the Web Frontend SHALL use distinct visual styling for each verdict type
3. WHEN displaying the verdict THEN the Web Frontend SHALL show the confidence score as a percentage
4. WHEN displaying the verdict THEN the Web Frontend SHALL show a visual confidence indicator
5. WHEN displaying the verdict THEN the Web Frontend SHALL show the consensus justification text

### Requirement 6

**User Story:** As a user, I want to view the evidence sources used in verification, so that I can assess the quality of information used.

#### Acceptance Criteria

1. WHEN verification completes THEN the Web Frontend SHALL display a list of evidence sources
2. WHEN displaying evidence sources THEN the Web Frontend SHALL show the source title for each piece of evidence
3. WHEN displaying evidence sources THEN the Web Frontend SHALL show the source URL for each piece of evidence
4. WHEN displaying evidence sources THEN the Web Frontend SHALL show the credibility score for each piece of evidence
5. WHEN a user clicks on a source URL THEN the Web Frontend SHALL open the source in a new browser tab

### Requirement 7

**User Story:** As a user, I want to explore the reasoning chain, so that I can understand how the system arrived at its verdict.

#### Acceptance Criteria

1. WHEN verification completes THEN the Web Frontend SHALL display the reasoning chain
2. WHEN displaying the reasoning chain THEN the Web Frontend SHALL show each reasoning step in sequence
3. WHEN displaying a reasoning step THEN the Web Frontend SHALL show the step description
4. WHEN displaying a reasoning step THEN the Web Frontend SHALL show which evidence was used in that step
5. WHEN displaying the reasoning chain THEN the Web Frontend SHALL highlight agreements and conflicts in the evidence

### Requirement 8

**User Story:** As a user, I want to see individual model verdicts, so that I can understand the consensus process and any disagreements.

#### Acceptance Criteria

1. WHEN verification uses multiple models THEN the Web Frontend SHALL display individual verdicts from each model
2. WHEN displaying individual verdicts THEN the Web Frontend SHALL show the model name for each verdict
3. WHEN displaying individual verdicts THEN the Web Frontend SHALL show the classification for each verdict
4. WHEN displaying individual verdicts THEN the Web Frontend SHALL show the justification for each verdict
5. WHEN models disagree THEN the Web Frontend SHALL visually indicate the disagreement

### Requirement 9

**User Story:** As a user, I want to view atomic claims when compound claims are decomposed, so that I can see how my claim was broken down for verification.

#### Acceptance Criteria

1. WHEN a compound claim is decomposed THEN the Web Frontend SHALL display the list of atomic claims
2. WHEN displaying atomic claims THEN the Web Frontend SHALL show each atomic claim text
3. WHEN displaying atomic claims THEN the Web Frontend SHALL show the verification status for each atomic claim
4. WHEN displaying atomic claims THEN the Web Frontend SHALL allow expanding each claim to see its individual verification results
5. WHEN all atomic claims are verified THEN the Web Frontend SHALL show an overall verdict for the compound claim

### Requirement 10

**User Story:** As a developer, I want a REST API that exposes KEPLER functionality, so that the web frontend and other clients can interact with the verification system.

#### Acceptance Criteria

1. WHEN the API server starts THEN the REST API SHALL listen for HTTP requests on a configured port
2. WHEN a client sends a verification request THEN the REST API SHALL accept JSON payloads with claim text and optional image data
3. WHEN a client sends a verification request THEN the REST API SHALL accept a list of selected model identifiers
4. WHEN the API receives a valid request THEN the REST API SHALL invoke the KEPLER pipeline with the provided inputs
5. WHEN the pipeline completes THEN the REST API SHALL return a JSON response with the complete verification results

### Requirement 11

**User Story:** As a developer, I want the API to handle errors gracefully, so that clients receive meaningful error messages.

#### Acceptance Criteria

1. WHEN the API receives an invalid request THEN the REST API SHALL return a 400 Bad Request status with error details
2. WHEN the pipeline encounters an error THEN the REST API SHALL return a 500 Internal Server Error status with error details
3. WHEN a requested resource is not found THEN the REST API SHALL return a 404 Not Found status
4. WHEN the API returns an error THEN the REST API SHALL include a descriptive error message in the response
5. WHEN the API returns an error THEN the REST API SHALL log the error details for debugging

### Requirement 12

**User Story:** As a user, I want the interface to handle long-running verifications gracefully, so that I know the system is working and can wait for results.

#### Acceptance Criteria

1. WHEN verification is in progress THEN the Web Frontend SHALL display a loading indicator
2. WHEN verification is in progress THEN the Web Frontend SHALL display progress messages indicating the current stage
3. WHEN verification takes longer than expected THEN the Web Frontend SHALL continue showing progress without timing out
4. WHEN verification is in progress THEN the Web Frontend SHALL disable the submit button to prevent duplicate requests
5. WHEN verification completes or fails THEN the Web Frontend SHALL re-enable the submit button

### Requirement 13

**User Story:** As a user, I want to see my verification history, so that I can review past fact-checks.

#### Acceptance Criteria

1. WHEN a user completes a verification THEN the Web Frontend SHALL add the session to a history list
2. WHEN displaying the history THEN the Web Frontend SHALL show the claim text for each past verification
3. WHEN displaying the history THEN the Web Frontend SHALL show the verdict for each past verification
4. WHEN displaying the history THEN the Web Frontend SHALL show the timestamp for each past verification
5. WHEN a user clicks on a history item THEN the Web Frontend SHALL display the full results for that verification

### Requirement 14

**User Story:** As a user, I want to export verification results, so that I can save or share the fact-check findings.

#### Acceptance Criteria

1. WHEN viewing verification results THEN the Web Frontend SHALL display an export button
2. WHEN a user clicks the export button THEN the Web Frontend SHALL offer export format options
3. WHEN a user selects JSON export THEN the Web Frontend SHALL download the complete results as a JSON file
4. WHEN a user selects PDF export THEN the Web Frontend SHALL download a formatted report as a PDF file
5. WHEN exporting results THEN the Web Frontend SHALL include all verification details including evidence sources and reasoning chain
