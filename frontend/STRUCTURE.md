# Frontend Project Structure

This document describes the organization of the KEPLER Web Interface frontend.

## Directory Structure

```
frontend/
├── src/
│   ├── components/          # React components
│   │   ├── InputForm/       # Input-related components
│   │   │   ├── ClaimInput.tsx
│   │   │   ├── ImageUpload.tsx
│   │   │   └── ModelSelector.tsx
│   │   ├── Results/         # Results display components
│   │   │   ├── VerdictDisplay.tsx
│   │   │   ├── EvidencePanel.tsx
│   │   │   ├── ReasoningChain.tsx
│   │   │   ├── ModelVerdicts.tsx
│   │   │   └── AtomicClaims.tsx
│   │   ├── Common/          # Shared/reusable components
│   │   │   ├── LoadingIndicator.tsx
│   │   │   ├── ErrorMessage.tsx
│   │   │   └── ConfidenceBar.tsx
│   │   ├── History/         # History-related components
│   │   │   ├── HistoryList.tsx
│   │   │   └── HistoryItem.tsx
│   │   ├── Export/          # Export functionality
│   │   │   └── ExportButton.tsx
│   │   └── index.ts         # Component exports
│   ├── services/            # API and external services
│   │   └── api.ts           # REST API client
│   ├── utils/               # Utility functions
│   │   ├── validation.ts    # Input validation
│   │   └── formatting.ts    # Data formatting
│   ├── App.tsx              # Main application component
│   ├── App.css              # Application styles
│   ├── main.tsx             # Application entry point
│   └── index.css            # Global styles
├── public/                  # Static assets
├── .env                     # Environment variables (not in git)
├── .env.example             # Environment variables template
├── package.json             # Dependencies and scripts
├── tsconfig.json            # TypeScript configuration
├── vite.config.ts           # Vite configuration
└── README.md                # Project documentation
```

## Component Organization

### InputForm Components
Components for accepting user input:
- **ClaimInput**: Text input for claims
- **ImageUpload**: Image file upload with preview
- **ModelSelector**: LLM model selection checkboxes

### Results Components
Components for displaying verification results:
- **VerdictDisplay**: Main verdict with confidence score
- **EvidencePanel**: List of evidence sources
- **ReasoningChain**: Step-by-step reasoning display
- **ModelVerdicts**: Individual model verdicts
- **AtomicClaims**: Decomposed claims display

### Common Components
Reusable components used throughout the app:
- **LoadingIndicator**: Loading spinner with stage info
- **ErrorMessage**: Error display with retry option
- **ConfidenceBar**: Visual confidence indicator

### History Components
Components for verification history:
- **HistoryList**: List of past verifications
- **HistoryItem**: Single history entry

### Export Components
Components for exporting results:
- **ExportButton**: Export to JSON/PDF

## State Management

The main App component manages application state:

```typescript
{
  // Input state
  input: {
    text: string;
    image: string | null;
    selectedModels: string[];
  },
  
  // UI state
  ui: {
    isLoading: boolean;
    currentStage: string | null;
    error: string | null;
  },
  
  // Results state
  results: {
    sessionId: string | null;
    originalInput: any | null;
    atomicClaims: any[];
    consensusVerdict: any | null;
    confidenceScore: any | null;
    processingMetadata: any | null;
    traceLog: any[];
  },
  
  // History state
  history: HistoryItem[];
}
```

## Services

### API Service (`services/api.ts`)
Handles all communication with the KEPLER REST API:
- `verifyClaim()` - Submit verification request
- `getAvailableModels()` - Fetch available LLM models
- `checkHealth()` - Check API health status

## Utilities

### Validation (`utils/validation.ts`)
Input validation functions:
- `isValidText()` - Validate non-empty text
- `isValidImageType()` - Validate image file type
- `isValidImageSize()` - Validate image file size
- `hasMinimumModels()` - Validate model selection
- `fileToBase64()` - Convert file to base64

### Formatting (`utils/formatting.ts`)
Data formatting functions:
- `formatPercentage()` - Format scores as percentages
- `formatTimestamp()` - Format dates/times
- `truncateText()` - Truncate long text
- `getVerdictColorClass()` - Get CSS class for verdict
- `formatFileSize()` - Format file sizes

## Styling

### CSS Organization
- `index.css` - Global styles and resets
- `App.css` - Main application layout and theme
- Component-specific styles can be co-located with components

### CSS Variables
Defined in `App.css`:
- Colors: `--color-supported`, `--color-refuted`, `--color-nei`, etc.
- Spacing: `--spacing-xs` through `--spacing-2xl`
- Border radius: `--radius-sm`, `--radius-md`, `--radius-lg`
- Shadows: `--shadow-sm`, `--shadow-md`, `--shadow-lg`

## Environment Variables

Configured in `.env`:
- `VITE_API_URL` - Base URL for the KEPLER API
- `VITE_ENVIRONMENT` - Environment (development/production)

## Development Workflow

1. Start the dev server: `npm run dev`
2. Make changes to components
3. Hot reload updates automatically
4. Build for production: `npm run build`
5. Preview production build: `npm run preview`

## Next Steps

The following components need to be implemented:
1. Input components (ClaimInput, ImageUpload, ModelSelector)
2. Results components (VerdictDisplay, EvidencePanel, etc.)
3. Common components (LoadingIndicator, ErrorMessage, etc.)
4. History and Export components
5. Integration and testing
