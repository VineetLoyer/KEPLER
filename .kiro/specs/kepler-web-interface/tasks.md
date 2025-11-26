# Implementation Plan

- [x] 1. Set up REST API backend structure
  - Create FastAPI application with CORS middleware
  - Set up project structure for API endpoints
  - Configure environment variables and settings
  - Add logging configuration
  - _Requirements: 10.1, 11.5_

- [x] 1.1 Write unit tests for API setup
  - Test CORS configuration
  - Test health endpoint
  - _Requirements: 10.1_

- [x] 2. Implement verification API endpoint
  - Create Pydantic models for request/response validation
  - Implement POST /api/verify endpoint
  - Add request validation for text, image, and selected_models
  - Integrate with existing KEPLER pipeline
  - Handle base64 image decoding
  - _Requirements: 10.2, 10.3, 10.4, 10.5_

- [x] 2.1 Write property tests for verification endpoint
  - **Property 29: API request acceptance**
  - **Property 30: Pipeline invocation**
  - **Property 31: Complete response structure**
  - **Validates: Requirements 10.2, 10.3, 10.4, 10.5**

- [x] 3. Implement API error handling
  - Add validation error handler (400 responses)
  - Add general exception handler (500 responses)
  - Add 404 handler for missing resources
  - Ensure error responses include descriptive messages
  - Add error logging for all exceptions
  - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_

- [x] 3.1 Write property tests for error handling
  - **Property 32: Invalid request error handling**
  - **Property 33: Pipeline error handling**
  - **Property 34: Error message inclusion**
  - **Property 35: Error logging**
  - **Validates: Requirements 11.1, 11.2, 11.4, 11.5**

- [x] 4. Implement models list endpoint
  - Create GET /api/models endpoint
  - Return list of available LLMs with metadata
  - Add caching for model list
  - _Requirements: 4.1, 4.2_

- [x] 5. Set up frontend project structure



  - Initialize React project with Vite
  - Set up component directory structure (components/, services/, utils/)
  - Configure build tools and development server
  - Set up CSS/styling approach (CSS modules or Tailwind)
  - Configure environment variables for API URL
  - Create basic App component shell
  - _Requirements: 1.1, 1.2_

- [x] 5.1 Write tests for initial app rendering






  - Test main interface loads
  - Test input form is displayed
  - **Validates: Requirements 1.1, 1.2**

- [x] 6. Implement ClaimInput component



  - Create textarea for claim input with placeholder text
  - Add client-side validation (non-empty, non-whitespace)
  - Display inline validation error messages
  - Handle form submission event
  - Disable input during verification (controlled by parent state)
  - Style component with appropriate spacing and focus states
  - _Requirements: 2.1, 2.2, 2.3_

- [x] 6.1 Write property tests for claim input






  - **Property 2: Input validation for empty claims**
  - **Property 3: API request on valid submission**
  - **Validates: Requirements 2.2, 2.3**

- [x] 7. Implement ImageUpload component
















  - Create file input with custom label/button styling
  - Validate file type against allowed formats (JPEG, PNG, GIF, WebP)
  - Validate file size (max 10MB) before processing
  - Display error messages for invalid files
  - Display image preview using FileReader
  - Convert image to base64 string for API transmission
  - Add remove/clear image functionality
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 7.1 Write property tests for image upload



  - **Property 6: Image file type validation**
  - **Property 7: Image file size validation**
  - **Property 8: Image preview display**
  - **Property 9: Multimodal data transmission**
  - **Validates: Requirements 3.2, 3.3, 3.4, 3.5**


- [x] 8. Implement ModelSelector component





  - Fetch available models from GET /api/models on component mount
  - Display loading state while fetching models
  - Display model list with checkboxes showing name and provider
  - Implement checkbox selection with state management
  - Enforce minimum one model selected (prevent deselecting last model)
  - Allow multiple model selection
  - Handle API fetch errors gracefully
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [x] 8.1 Write property tests for model selector




  - **Property 10: Model information display**
  - **Property 11: Minimum model selection**
  - **Property 12: Multiple model selection**
  - **Property 13: Selected models in request**
  - **Validates: Requirements 4.2, 4.3, 4.4, 4.5**

- [x] 9. Implement API service layer



  - Create axios or fetch client with base URL from environment variable
  - Implement verifyClaim function (POST /api/verify)
  - Implement getAvailableModels function (GET /api/models)
  - Implement checkHealth function (GET /api/health)
  - Add error handling for network failures
  - Add error handling for API error responses (400, 500)
  - Parse and format error messages from API responses
  - _Requirements: 2.3, 10.2, 10.3_

- [x] 9.1 Write tests for API service






  - Test API calls with mocked responses
  - Test error handling for different status codes
  - Test network failure scenarios
  - _Requirements: 2.3_

- [x] 10. Implement LoadingIndicator component



  - Create animated loading spinner (CSS or SVG)
  - Accept current stage as prop
  - Display stage-specific progress messages
  - Add "This may take a moment..." helper text
  - Style with appropriate spacing and centering
  - _Requirements: 2.4, 12.1, 12.2_

- [x] 10.1 Write property tests for loading indicator
















  - **Property 4: Loading indicator during verification**
  - **Property 36: Progress message display**
  - **Validates: Requirements 2.4, 12.1, 12.2**
-




- [x] 11. Implement VerdictDisplay component







  - Display verdict classification badge with distinct colors (green/red/yellow)
  - Show confidence score formatted as percentage (0-100%)
  - Render visual confidence indicator (progress bar or gauge)
  - Display consensus justification text in readable format
  - Show confidence factor breakdown (source reliability, model agreement, evidence recency)
  - _Requirements: 2.5, 5.1, 5.2, 5.3, 5.4, 5.5_

pe
  - _Requirements: 2.5, 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 11.1 Write property tests for verdict display




  - **Property 5: Verdict display after completion**
  - **Property 14: Distinct verdict styling**
  - **Property 15: Confidence score percentage format**
  - **Property 16: Confidence indicator presence**


  - **Property 17: Justification text display**
  - **Validates: Requirements 2.5, 5.1, 5.2, 5.3, 5.4, 5.5**

- [x] 12. Implement EvidencePanel component






  - Display list of evidence sources from API response
  - Show title, URL, and credibility score for each source
  - Make URLs clickable with target="_blank" and rel="noopener noreferrer"
  - Display evidence summary text for each piece
  - Format credibility scores as percentages
  - Add appropriate styling and spacing between items
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [x] 12.1 Write property tests for evidence panel



  - **Property 18: Evidence source completeness**
  - **Property 19: Evidence URL link behavior**
  - **Validates: Requirements 6.2, 6.3, 6.4, 6.5**

- [x] 13. Implement ReasoningChain component





  - Display reasoning steps in sequential order by step number
  - Show step description, evidence used, and conclusion for each step
  - Display agreements section with common assertions and strength
  - Display conflicts section with conflicting assertions and severity
  - Display information gaps section with missing aspects
  - Apply distinct styling for agreements (green) and conflicts (red/yellow)
  - Format strength/severity as percentages
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [x] 13.1 Write property tests for reasoning chain



  - **Property 20: Reasoning steps sequential display**
  - **Property 21: Reasoning step content completeness**
  - **Property 22: Agreement and conflict highlighting**
  - **Validates: Requirements 7.2, 7.3, 7.4, 7.5**

- [x] 14. Implement ModelVerdicts component





  - Display individual verdicts from each model in the response
  - Show model name/ID, classification, and justification for each
  - Show confidence score for each model verdict
  - Visually indicate disagreements (highlight when classifications differ)
  - Use consistent verdict styling (same colors as main verdict)
  - Add borders or badges to highlight disagreeing models
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_


- [x] 14.1 Write property tests for model verdicts







  - **Property 23: Individual verdict display completeness**
  - **Property 24: Disagreement visualization**
  - **Validates: Requirements 8.2, 8.3, 8.4, 8.5**

- [x] 15. Implement AtomicClaims component





  - Display list of atomic claims from API response
  - Show claim text and verification status for each
  - Implement expand/collapse functionality (accordion or details/summary)
  - Show detailed verification results when expanded
  - Show overall verdict for compound claims (when multiple atomic claims exist)
  - Add visual indicators for claim status (icons or colors)
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

- [x] 15.1 Write property tests for atomic claims





  - **Property 25: Atomic claims list display**
  - **Property 26: Atomic claim status display**
  - **Property 27: Atomic claim expansion**
  - **Property 28: Compound claim overall verdict**
  - **Validates: Requirements 9.1, 9.2, 9.3, 9.4, 9.5**

-

- [x] 16. Implement application state management




  - Set up state structure in main App component (input, UI, results, history)
  - Implement state update functions for input changes
  - Handle loading states (isLoading, currentStage)
  - Manage error states (error message, error type)
  - Track verification history in state
  - Implement state persistence to localStorage for history
  - Create helper functions for state transitions
  - _Requirements: 2.4, 12.1, 12.4, 12.5, 13.1_
-

- [x] 16.1 Write property tests for state management









  - **Property 37: Submit button state management**
  - **Property 38: History tracking**
  - **Validates: Requirements 12.4, 12.5, 13.1**
- [x] 17. Implement History component




- [ ] 17. Implement History component

  - Display list of past verifications from state/localStorage
  - Show claim text (truncated if long), verdict, and timestamp for each item
  - Handle history item clicks to load and display full results
  - Implement localStorage persistence for history
  - Add clear history functionality
  - Style as sidebar or collapsible panel
  - Format timestamps in human-readable format
  - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5_

 


- [x] 17.1 Write property tests for history











  - **Property 39: History item content**
  - **Property 40: History item interaction**
  - **Validates: Requirements 13.2, 13.3, 13.4, 13.5**

- [x] 18. Implement Export functionality


  - Create ExportButton component with format dropdown
  - Implement JSON export with complete verification data
  - Implement PDF export using library (jsPDF or similar)
  - Format PDF with sections for verdict, evidence, reasoning
  - Trigger file downloads with appropriate filenames
  - Handle export errors gracefully
  - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5_

- [x] 18.1 Write property tests for export



  - **Property 41: JSON export completeness**
  - **Property 42: PDF export generation**
  - **Validates: Requirements 14.3, 14.4, 14.5**

- [x] 19. Implement responsive design


  - Add CSS media queries for mobile (<768px), tablet (768-1024px), desktop (>1024px)
  - Test layout at different viewport sizes
  - Ensure touch-friendly button sizes and spacing on mobile
  - Implement collapsible/accordion sections for mobile
  - Stack components vertically on mobile
  - Adjust font sizes for readability on small screens
  - _Requirements: 1.3, 1.4_

- [x] 19.1 Write property tests for responsive design

  - **Property 1: Responsive layout rendering**
  - **Validates: Requirements 1.3, 1.4**

- [x] 20. Implement error handling UI


  - Create ErrorMessage component
  - Display validation errors inline
  - Display API errors with retry option
  - Handle network failures gracefully
  - _Requirements: 1.5, 11.1, 11.2, 11.4_

- [x] 21. Add accessibility features

  - Add ARIA labels to interactive elements
  - Ensure keyboard navigation works
  - Add focus indicators
  - Test with screen reader
  - Verify color contrast ratios
  - _Requirements: 1.3, 1.4_

- [x] 22. Integrate all components in main App


  - Wire up input components to state
  - Connect API calls to UI updates
  - Implement verification workflow
  - Handle loading and error states
  - Display results when available
  - _Requirements: All requirements_

- [x] 22.1 Write integration tests

  - Test complete verification flow
  - Test error scenarios
  - Test multimodal input
  - _Requirements: All requirements_

- [x] 23. Add styling and polish

  - Implement color scheme for verdicts
  - Add animations and transitions
  - Style loading indicators
  - Polish responsive layouts
  - Add hover states and interactions
  - _Requirements: 5.2, 7.5, 8.5_

- [x] 24. Set up deployment configuration


  - Create Dockerfile for API backend
  - Configure environment variables
  - Set up frontend build process
  - Create deployment documentation
  - _Requirements: 10.1_

- [x] 25. Final checkpoint - Ensure all tests pass

  - Run all unit tests
  - Run all property tests
  - Run integration tests
  - Fix any failing tests
  - Verify test coverage
  - _Requirements: All requirements_

