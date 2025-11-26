# Design Document

## Overview

The KEPLER Web Interface is a full-stack web application that provides user-friendly access to the KEPLER fact-verification system. The architecture consists of two main layers:

1. **REST API Backend**: A Python-based API server (using FastAPI or Flask) that exposes the KEPLER pipeline through HTTP endpoints
2. **Web Frontend**: A responsive single-page application (using React or vanilla JavaScript) that provides an intuitive interface for claim verification

The design emphasizes:
- **Separation of concerns**: Clear boundaries between API and frontend
- **Responsiveness**: Mobile-first design that works across devices
- **Real-time feedback**: Progress indicators and streaming updates during verification
- **Transparency**: Full visibility into verification process, evidence, and reasoning
- **Usability**: Intuitive interface requiring minimal learning curve

## Architecture

### High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Web Browser                             │
│  ┌────────────────────────────────────────────────────────┐ │
│  │           KEPLER Web Frontend (React/JS)               │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐ │ │
│  │  │  Input   │  │ Results  │  │  History & Export    │ │ │
│  │  │Component │  │ Display  │  │     Components       │ │ │
│  │  └──────────┘  └──────────┘  └──────────────────────┘ │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ HTTP/JSON
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              REST API Server (FastAPI/Flask)                 │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  API Endpoints  │  Request Validation  │  Error Handler│ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ Python Function Calls
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                  KEPLER Pipeline (Existing)                  │
│         (Claim Decomposition → Retrieval → ... )             │
└─────────────────────────────────────────────────────────────┘
```

### Technology Stack

**Backend (REST API)**:
- Framework: FastAPI (recommended for async support and automatic OpenAPI docs) or Flask
- CORS: Enable cross-origin requests for frontend
- Validation: Pydantic models for request/response validation
- File handling: Support for multipart/form-data for image uploads

**Frontend**:
- Framework: React (recommended) or vanilla JavaScript with modern ES6+
- HTTP Client: Axios or Fetch API
- State Management: React Context API or Redux (if using React)
- Styling: CSS3 with Flexbox/Grid, or Tailwind CSS
- Build Tool: Vite or Create React App


## Components and Interfaces

### 1. REST API Backend

#### API Endpoints

```python
# Main verification endpoint
POST /api/verify
Request:
{
    "text": str (optional),
    "image": str (base64 encoded, optional),
    "selected_models": List[str] (required, min 1)
}
Response:
{
    "session_id": str,
    "original_input": {...},
    "atomic_claims": [...],
    "consensus_verdict": {...},
    "confidence_score": {...},
    "processing_metadata": {...},
    "trace_log": [...]
}

# Health check endpoint
GET /api/health
Response:
{
    "status": "healthy",
    "version": str
}

# Available models endpoint
GET /api/models
Response:
{
    "models": [
        {
            "id": str,
            "name": str,
            "provider": str,
            "version": str
        }
    ]
}
```

#### API Server Implementation

```python
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
from typing import Optional, List
import base64

app = FastAPI(title="KEPLER API", version="1.0.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class VerificationRequest(BaseModel):
    text: Optional[str] = None
    image: Optional[str] = None  # Base64 encoded
    selected_models: List[str]
    
    @validator('selected_models')
    def validate_models(cls, v):
        if len(v) < 1:
            raise ValueError('At least one model must be selected')
        return v
    
    @validator('text', 'image')
    def validate_input(cls, v, values):
        if not values.get('text') and not v:
            raise ValueError('Either text or image must be provided')
        return v

class VerificationResponse(BaseModel):
    session_id: str
    original_input: dict
    atomic_claims: List[dict]
    consensus_verdict: dict
    confidence_score: dict
    processing_metadata: dict
    trace_log: List[dict]

@app.post("/api/verify", response_model=VerificationResponse)
async def verify_claim(request: VerificationRequest):
    """Process a fact-verification request"""
    try:
        # Decode image if provided
        image_bytes = None
        if request.image:
            image_bytes = base64.b64decode(request.image)
        
        # Invoke KEPLER pipeline
        from src.pipeline import VerificationPipeline
        from src.config import Config
        
        config = Config()
        pipeline = VerificationPipeline(config)
        
        result = pipeline.verify(
            text=request.text,
            image=image_bytes,
            selected_model_ids=request.selected_models
        )
        
        return VerificationResponse(**result.to_dict())
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "1.0.0"}

@app.get("/api/models")
async def get_available_models():
    """Get list of available LLM models"""
    from src.config import Config
    config = Config()
    return {"models": config.get_available_models()}
```


### 2. Web Frontend Architecture

#### Component Structure

```
src/
├── components/
│   ├── InputForm/
│   │   ├── ClaimInput.jsx          # Text input for claims
│   │   ├── ImageUpload.jsx         # Image upload component
│   │   └── ModelSelector.jsx       # LLM selection component
│   ├── Results/
│   │   ├── VerdictDisplay.jsx      # Main verdict with confidence
│   │   ├── EvidencePanel.jsx       # Evidence sources list
│   │   ├── ReasoningChain.jsx      # Step-by-step reasoning
│   │   ├── ModelVerdicts.jsx       # Individual model results
│   │   └── AtomicClaims.jsx        # Decomposed claims display
│   ├── Common/
│   │   ├── LoadingIndicator.jsx    # Loading spinner/progress
│   │   ├── ErrorMessage.jsx        # Error display component
│   │   └── ConfidenceBar.jsx       # Visual confidence indicator
│   ├── History/
│   │   ├── HistoryList.jsx         # Past verifications list
│   │   └── HistoryItem.jsx         # Single history entry
│   └── Export/
│       └── ExportButton.jsx        # Export functionality
├── services/
│   └── api.js                      # API client functions
├── utils/
│   ├── validation.js               # Input validation utilities
│   └── formatting.js               # Data formatting utilities
├── App.jsx                         # Main application component
└── index.js                        # Application entry point
```

#### Key Frontend Components

**ClaimInput Component**:
```javascript
// ClaimInput.jsx
import React, { useState } from 'react';

export const ClaimInput = ({ value, onChange, onSubmit, disabled }) => {
    const [error, setError] = useState('');
    
    const handleSubmit = (e) => {
        e.preventDefault();
        
        // Validate input
        if (!value || value.trim() === '') {
            setError('Claim cannot be empty or whitespace-only');
            return;
        }
        
        setError('');
        onSubmit();
    };
    
    return (
        <form onSubmit={handleSubmit}>
            <textarea
                value={value}
                onChange={(e) => onChange(e.target.value)}
                placeholder="Enter a claim to verify..."
                disabled={disabled}
                rows={4}
                className="claim-input"
            />
            {error && <div className="error-message">{error}</div>}
            <button type="submit" disabled={disabled}>
                Verify Claim
            </button>
        </form>
    );
};
```

**ImageUpload Component**:
```javascript
// ImageUpload.jsx
import React, { useState } from 'react';

const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB
const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];

export const ImageUpload = ({ onImageSelect, disabled }) => {
    const [preview, setPreview] = useState(null);
    const [error, setError] = useState('');
    
    const handleFileSelect = (e) => {
        const file = e.target.files[0];
        if (!file) return;
        
        // Validate file type
        if (!ALLOWED_TYPES.includes(file.type)) {
            setError('Invalid file type. Please upload a JPEG, PNG, GIF, or WebP image.');
            return;
        }
        
        // Validate file size
        if (file.size > MAX_FILE_SIZE) {
            setError('File size exceeds 10MB limit.');
            return;
        }
        
        setError('');
        
        // Create preview
        const reader = new FileReader();
        reader.onloadend = () => {
            setPreview(reader.result);
            onImageSelect(reader.result); // Base64 string
        };
        reader.readAsDataURL(file);
    };
    
    return (
        <div className="image-upload">
            <input
                type="file"
                accept="image/*"
                onChange={handleFileSelect}
                disabled={disabled}
                id="image-upload-input"
            />
            <label htmlFor="image-upload-input">
                Upload Image (Optional)
            </label>
            {error && <div className="error-message">{error}</div>}
            {preview && (
                <div className="image-preview">
                    <img src={preview} alt="Preview" />
                </div>
            )}
        </div>
    );
};
```

**ModelSelector Component**:
```javascript
// ModelSelector.jsx
import React, { useState, useEffect } from 'react';
import { getAvailableModels } from '../../services/api';

export const ModelSelector = ({ selectedModels, onSelectionChange, disabled }) => {
    const [models, setModels] = useState([]);
    const [loading, setLoading] = useState(true);
    
    useEffect(() => {
        loadModels();
    }, []);
    
    const loadModels = async () => {
        try {
            const data = await getAvailableModels();
            setModels(data.models);
        } catch (error) {
            console.error('Failed to load models:', error);
        } finally {
            setLoading(false);
        }
    };
    
    const handleToggle = (modelId) => {
        if (selectedModels.includes(modelId)) {
            // Don't allow deselecting if it's the last one
            if (selectedModels.length > 1) {
                onSelectionChange(selectedModels.filter(id => id !== modelId));
            }
        } else {
            onSelectionChange([...selectedModels, modelId]);
        }
    };
    
    if (loading) return <div>Loading models...</div>;
    
    return (
        <div className="model-selector">
            <h3>Select Language Models</h3>
            <div className="model-list">
                {models.map(model => (
                    <label key={model.id} className="model-option">
                        <input
                            type="checkbox"
                            checked={selectedModels.includes(model.id)}
                            onChange={() => handleToggle(model.id)}
                            disabled={disabled}
                        />
                        <span className="model-name">{model.name}</span>
                        <span className="model-provider">({model.provider})</span>
                    </label>
                ))}
            </div>
        </div>
    );
};
```


**VerdictDisplay Component**:
```javascript
// VerdictDisplay.jsx
import React from 'react';
import { ConfidenceBar } from '../Common/ConfidenceBar';

export const VerdictDisplay = ({ verdict, confidenceScore }) => {
    const getVerdictClass = (classification) => {
        const classMap = {
            'Supported': 'verdict-supported',
            'Refuted': 'verdict-refuted',
            'Not Enough Information': 'verdict-nei'
        };
        return classMap[classification] || 'verdict-unknown';
    };
    
    return (
        <div className="verdict-display">
            <div className={`verdict-badge ${getVerdictClass(verdict.final_classification)}`}>
                {verdict.final_classification}
            </div>
            
            <ConfidenceBar 
                score={confidenceScore.overall_score} 
                label="Confidence"
            />
            
            <div className="confidence-percentage">
                {(confidenceScore.overall_score * 100).toFixed(1)}%
            </div>
            
            <div className="consensus-justification">
                <h4>Justification</h4>
                <p>{verdict.consensus_justification}</p>
            </div>
            
            <div className="confidence-breakdown">
                <h4>Confidence Factors</h4>
                <ul>
                    <li>Source Reliability: {(confidenceScore.source_reliability * 100).toFixed(1)}%</li>
                    <li>Model Agreement: {(confidenceScore.model_agreement * 100).toFixed(1)}%</li>
                    <li>Evidence Recency: {(confidenceScore.evidence_recency * 100).toFixed(1)}%</li>
                </ul>
            </div>
        </div>
    );
};
```

**EvidencePanel Component**:
```javascript
// EvidencePanel.jsx
import React from 'react';

export const EvidencePanel = ({ evidence }) => {
    return (
        <div className="evidence-panel">
            <h3>Evidence Sources</h3>
            <div className="evidence-list">
                {evidence.map((item, index) => (
                    <div key={index} className="evidence-item">
                        <div className="evidence-header">
                            <h4>{item.source.title}</h4>
                            <span className="credibility-score">
                                Credibility: {(item.credibility_score * 100).toFixed(0)}%
                            </span>
                        </div>
                        <p className="evidence-summary">{item.summary}</p>
                        <a 
                            href={item.source.url} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="evidence-link"
                        >
                            View Source →
                        </a>
                    </div>
                ))}
            </div>
        </div>
    );
};
```

**ReasoningChain Component**:
```javascript
// ReasoningChain.jsx
import React from 'react';

export const ReasoningChain = ({ reasoningChain }) => {
    return (
        <div className="reasoning-chain">
            <h3>Reasoning Process</h3>
            
            <div className="reasoning-steps">
                {reasoningChain.steps.map((step, index) => (
                    <div key={index} className="reasoning-step">
                        <div className="step-number">Step {step.step_number}</div>
                        <div className="step-content">
                            <p className="step-description">{step.description}</p>
                            <div className="step-evidence">
                                <strong>Evidence used:</strong>
                                <ul>
                                    {step.evidence_used.map((evidenceId, i) => (
                                        <li key={i}>{evidenceId}</li>
                                    ))}
                                </ul>
                            </div>
                            <p className="step-conclusion">
                                <strong>Conclusion:</strong> {step.conclusion}
                            </p>
                        </div>
                    </div>
                ))}
            </div>
            
            {reasoningChain.agreements.length > 0 && (
                <div className="agreements-section">
                    <h4>Agreements in Evidence</h4>
                    {reasoningChain.agreements.map((agreement, index) => (
                        <div key={index} className="agreement-item">
                            <p>{agreement.common_assertion}</p>
                            <span className="strength">Strength: {(agreement.strength * 100).toFixed(0)}%</span>
                        </div>
                    ))}
                </div>
            )}
            
            {reasoningChain.conflicts.length > 0 && (
                <div className="conflicts-section">
                    <h4>Conflicts in Evidence</h4>
                    {reasoningChain.conflicts.map((conflict, index) => (
                        <div key={index} className="conflict-item">
                            <ul>
                                {conflict.conflicting_assertions.map((assertion, i) => (
                                    <li key={i}>{assertion}</li>
                                ))}
                            </ul>
                            <span className="severity">Severity: {(conflict.severity * 100).toFixed(0)}%</span>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};
```


**API Service Layer**:
```javascript
// services/api.js
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

export const verifyC laim = async (text, image, selectedModels) => {
    try {
        const response = await api.post('/api/verify', {
            text,
            image, // Base64 encoded
            selected_models: selectedModels,
        });
        return response.data;
    } catch (error) {
        if (error.response) {
            // Server responded with error
            throw new Error(error.response.data.detail || 'Verification failed');
        } else if (error.request) {
            // Request made but no response
            throw new Error('No response from server. Please check your connection.');
        } else {
            // Something else happened
            throw new Error('Failed to send verification request');
        }
    }
};

export const getAvailableModels = async () => {
    try {
        const response = await api.get('/api/models');
        return response.data;
    } catch (error) {
        throw new Error('Failed to load available models');
    }
};

export const checkHealth = async () => {
    try {
        const response = await api.get('/api/health');
        return response.data;
    } catch (error) {
        throw new Error('Health check failed');
    }
};
```

### 3. State Management

**Application State Structure**:
```javascript
{
    // Input state
    input: {
        text: string,
        image: string | null,
        selectedModels: string[],
    },
    
    // UI state
    ui: {
        isLoading: boolean,
        currentStage: string | null,
        error: string | null,
    },
    
    // Results state
    results: {
        sessionId: string | null,
        originalInput: object | null,
        atomicClaims: array,
        consensusVerdict: object | null,
        confidenceScore: object | null,
        processingMetadata: object | null,
        traceLog: array,
    },
    
    // History state
    history: [
        {
            sessionId: string,
            timestamp: string,
            claimText: string,
            verdict: string,
            confidence: number,
            fullResults: object,
        }
    ],
}
```

## Data Models

### API Request/Response Models

```python
# Backend models (Pydantic)
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class VerificationRequest(BaseModel):
    text: Optional[str] = None
    image: Optional[str] = None  # Base64 encoded
    selected_models: List[str]

class ModelInfo(BaseModel):
    id: str
    name: str
    provider: str
    version: str

class VerificationResponse(BaseModel):
    session_id: str
    original_input: Dict[str, Any]
    atomic_claims: List[Dict[str, Any]]
    consensus_verdict: Dict[str, Any]
    confidence_score: Dict[str, Any]
    processing_metadata: Dict[str, Any]
    trace_log: List[Dict[str, Any]]

class ErrorResponse(BaseModel):
    error: str
    detail: str
    timestamp: datetime
```

### Frontend Data Types

```typescript
// TypeScript interfaces for frontend (if using TypeScript)
interface VerificationRequest {
    text?: string;
    image?: string;
    selected_models: string[];
}

interface VerdictType {
    final_classification: 'Supported' | 'Refuted' | 'Not Enough Information';
    consensus_justification: string;
    individual_verdicts: IndividualVerdict[];
    agreement_level: number;
}

interface ConfidenceScore {
    overall_score: number;
    source_reliability: number;
    model_agreement: number;
    evidence_recency: number;
    structured_justification: StructuredJustification;
}

interface EvidencePiece {
    id: string;
    source: Source;
    summary: string;
    relevance_score: number;
    credibility_score: number;
}

interface ReasoningChain {
    steps: ReasoningStep[];
    agreements: Agreement[];
    conflicts: Conflict[];
    gaps: InformationGap[];
}

interface HistoryItem {
    sessionId: string;
    timestamp: string;
    claimText: string;
    verdict: string;
    confidence: number;
    fullResults: VerificationResponse;
}
```


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Responsive layout rendering
*For any* viewport width (desktop or mobile), the interface should render without horizontal scrolling and maintain usability.
**Validates: Requirements 1.3, 1.4**

### Property 2: Input validation for empty claims
*For any* empty or whitespace-only text input, the frontend should reject submission and display a validation error.
**Validates: Requirements 2.2**

### Property 3: API request on valid submission
*For any* valid claim submission (non-empty text or image with selected models), the frontend should send an HTTP POST request to the API.
**Validates: Requirements 2.3**

### Property 4: Loading indicator during verification
*For any* verification request in progress, the frontend should display a loading indicator.
**Validates: Requirements 2.4, 12.1**

### Property 5: Verdict display after completion
*For any* successful API response, the frontend should display the verdict classification.
**Validates: Requirements 2.5, 5.1**

### Property 6: Image file type validation
*For any* selected file, if the file type is not a supported image format (JPEG, PNG, GIF, WebP), the frontend should reject it and display an error.
**Validates: Requirements 3.2**

### Property 7: Image file size validation
*For any* selected image file, if the file size exceeds the maximum limit, the frontend should reject it and display an error.
**Validates: Requirements 3.3**

### Property 8: Image preview display
*For any* valid image selection, the frontend should display a preview of the image.
**Validates: Requirements 3.4**

### Property 9: Multimodal data transmission
*For any* submission with both text and image, the API request should include both data types.
**Validates: Requirements 3.5**

### Property 10: Model information display
*For any* available model in the list, the frontend should display both the model name and provider.
**Validates: Requirements 4.2**

### Property 11: Minimum model selection
*For any* model selection state, at least one model should be selected.
**Validates: Requirements 4.3**

### Property 12: Multiple model selection
*For any* model selection interaction, the frontend should allow selecting more than one model simultaneously.
**Validates: Requirements 4.4**

### Property 13: Selected models in request
*For any* verification request, the API payload should include all selected model identifiers.
**Validates: Requirements 4.5**

### Property 14: Distinct verdict styling
*For any* two different verdict types (Supported vs Refuted vs Not Enough Information), the visual styling should be distinguishable.
**Validates: Requirements 5.2**

### Property 15: Confidence score percentage format
*For any* displayed confidence score, it should be formatted as a percentage (0-100%).
**Validates: Requirements 5.3**

### Property 16: Confidence indicator presence
*For any* verdict display, a visual confidence indicator should be present.
**Validates: Requirements 5.4**

### Property 17: Justification text display
*For any* verdict, the consensus justification text should be displayed.
**Validates: Requirements 5.5**

### Property 18: Evidence source completeness
*For any* displayed evidence piece, it should include title, URL, and credibility score.
**Validates: Requirements 6.2, 6.3, 6.4**

### Property 19: Evidence URL link behavior
*For any* evidence source URL click, the link should open in a new browser tab.
**Validates: Requirements 6.5**

### Property 20: Reasoning steps sequential display
*For any* reasoning chain, the steps should be displayed in sequential order by step number.
**Validates: Requirements 7.2**

### Property 21: Reasoning step content completeness
*For any* reasoning step, it should display the description and evidence references.
**Validates: Requirements 7.3, 7.4**

### Property 22: Agreement and conflict highlighting
*For any* reasoning chain with agreements or conflicts, they should have distinct visual styling.
**Validates: Requirements 7.5**

### Property 23: Individual verdict display completeness
*For any* individual model verdict, it should display model name, classification, and justification.
**Validates: Requirements 8.2, 8.3, 8.4**

### Property 24: Disagreement visualization
*For any* set of model verdicts where classifications differ, the frontend should visually indicate the disagreement.
**Validates: Requirements 8.5**

### Property 25: Atomic claims list display
*For any* compound claim that is decomposed, all atomic claims should be displayed.
**Validates: Requirements 9.1, 9.2**

### Property 26: Atomic claim status display
*For any* atomic claim, its verification status should be displayed.
**Validates: Requirements 9.3**

### Property 27: Atomic claim expansion
*For any* atomic claim, clicking or interacting with it should expand to show detailed results.
**Validates: Requirements 9.4**

### Property 28: Compound claim overall verdict
*For any* compound claim with all atomic claims verified, an overall verdict should be displayed.
**Validates: Requirements 9.5**

### Property 29: API request acceptance
*For any* valid JSON payload with required fields (text or image, and selected_models), the API should accept the request and return 200 status.
**Validates: Requirements 10.2, 10.3**

### Property 30: Pipeline invocation
*For any* valid API request, the KEPLER pipeline should be invoked with the provided inputs.
**Validates: Requirements 10.4**

### Property 31: Complete response structure
*For any* successful pipeline execution, the API response should include all required fields (session_id, atomic_claims, consensus_verdict, confidence_score, etc.).
**Validates: Requirements 10.5**

### Property 32: Invalid request error handling
*For any* invalid API request (missing required fields, invalid format), the API should return 400 status with error details.
**Validates: Requirements 11.1**

### Property 33: Pipeline error handling
*For any* pipeline execution error, the API should return 500 status with error details.
**Validates: Requirements 11.2**

### Property 34: Error message inclusion
*For any* error response, the response should include a descriptive error message.
**Validates: Requirements 11.4**

### Property 35: Error logging
*For any* error occurrence, the error details should be logged.
**Validates: Requirements 11.5**

### Property 36: Progress message display
*For any* verification in progress, the frontend should display messages indicating the current pipeline stage.
**Validates: Requirements 12.2**

### Property 37: Submit button state management
*For any* verification in progress, the submit button should be disabled; when complete or failed, it should be re-enabled.
**Validates: Requirements 12.4, 12.5**

### Property 38: History tracking
*For any* completed verification, the session should be added to the history list.
**Validates: Requirements 13.1**

### Property 39: History item content
*For any* history item, it should display claim text, verdict, and timestamp.
**Validates: Requirements 13.2, 13.3, 13.4**

### Property 40: History item interaction
*For any* history item click, the full verification results should be displayed.
**Validates: Requirements 13.5**

### Property 41: JSON export completeness
*For any* JSON export, the file should contain all verification details including evidence sources and reasoning chain.
**Validates: Requirements 14.3, 14.5**

### Property 42: PDF export generation
*For any* PDF export request, a formatted PDF file should be generated and downloaded.
**Validates: Requirements 14.4**


## Error Handling

### Frontend Error Handling

**Input Validation Errors**:
- Empty or whitespace-only text: Display inline validation message
- Invalid image format: Display error message near upload button
- Oversized image: Display error with size limit information
- No models selected: Prevent submission and highlight model selector

**API Communication Errors**:
- Network failure: Display "Connection failed" message with retry option
- Timeout: Display "Request timed out" message with retry option
- 400 Bad Request: Display validation error from API response
- 500 Internal Server Error: Display "Verification failed" with error details
- Unknown errors: Display generic error message and log to console

**Error Display Strategy**:
```javascript
// ErrorMessage.jsx
export const ErrorMessage = ({ error, onRetry, onDismiss }) => {
    if (!error) return null;
    
    return (
        <div className="error-container">
            <div className="error-icon">⚠️</div>
            <div className="error-content">
                <h4>Error</h4>
                <p>{error.message}</p>
                {error.detail && <p className="error-detail">{error.detail}</p>}
            </div>
            <div className="error-actions">
                {onRetry && <button onClick={onRetry}>Retry</button>}
                {onDismiss && <button onClick={onDismiss}>Dismiss</button>}
            </div>
        </div>
    );
};
```

### Backend Error Handling

**Request Validation**:
```python
@app.exception_handler(ValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={
            "error": "Validation Error",
            "detail": str(exc),
            "timestamp": datetime.now().isoformat()
        }
    )
```

**Pipeline Errors**:
```python
@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "detail": "An error occurred during verification",
            "timestamp": datetime.now().isoformat()
        }
    )
```

**CORS Errors**:
- Properly configure CORS middleware to allow frontend origin
- Return appropriate CORS headers in all responses including errors

## Testing Strategy

### Frontend Testing

**Unit Tests** (using Jest + React Testing Library):
- Component rendering tests
- Input validation logic
- State management functions
- Utility functions (formatting, validation)

**Integration Tests**:
- Form submission flow
- API communication with mocked responses
- Error handling scenarios
- History management

**E2E Tests** (using Cypress or Playwright):
- Complete verification workflow
- Image upload and preview
- Model selection
- Results display and navigation
- Export functionality

**Example Unit Test**:
```javascript
// ClaimInput.test.jsx
import { render, screen, fireEvent } from '@testing-library/react';
import { ClaimInput } from './ClaimInput';

describe('ClaimInput', () => {
    test('should reject empty input', () => {
        const onSubmit = jest.fn();
        render(<ClaimInput value="" onChange={() => {}} onSubmit={onSubmit} />);
        
        const button = screen.getByText('Verify Claim');
        fireEvent.click(button);
        
        expect(screen.getByText(/cannot be empty/i)).toBeInTheDocument();
        expect(onSubmit).not.toHaveBeenCalled();
    });
    
    test('should reject whitespace-only input', () => {
        const onSubmit = jest.fn();
        render(<ClaimInput value="   " onChange={() => {}} onSubmit={onSubmit} />);
        
        const button = screen.getByText('Verify Claim');
        fireEvent.click(button);
        
        expect(screen.getByText(/cannot be empty/i)).toBeInTheDocument();
        expect(onSubmit).not.toHaveBeenCalled();
    });
    
    test('should accept valid input', () => {
        const onSubmit = jest.fn();
        render(<ClaimInput value="Valid claim" onChange={() => {}} onSubmit={onSubmit} />);
        
        const button = screen.getByText('Verify Claim');
        fireEvent.click(button);
        
        expect(onSubmit).toHaveBeenCalled();
    });
});
```

### Backend Testing

**Unit Tests** (using pytest):
- Endpoint request/response handling
- Request validation
- Error handling
- Model serialization

**Integration Tests**:
- Full API workflow with mocked pipeline
- CORS configuration
- Error responses

**Example API Test**:
```python
# test_api.py
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_verify_endpoint_requires_models():
    response = client.post("/api/verify", json={
        "text": "Test claim",
        "selected_models": []
    })
    assert response.status_code == 400
    assert "at least one model" in response.json()["detail"].lower()

def test_verify_endpoint_requires_input():
    response = client.post("/api/verify", json={
        "selected_models": ["gpt-4"]
    })
    assert response.status_code == 400

def test_verify_endpoint_success(mocker):
    # Mock the pipeline
    mock_pipeline = mocker.patch('main.VerificationPipeline')
    mock_result = mocker.Mock()
    mock_result.to_dict.return_value = {
        "session_id": "test-123",
        "atomic_claims": [],
        "consensus_verdict": {},
        "confidence_score": {},
        "processing_metadata": {},
        "trace_log": []
    }
    mock_pipeline.return_value.verify.return_value = mock_result
    
    response = client.post("/api/verify", json={
        "text": "Test claim",
        "selected_models": ["gpt-4"]
    })
    
    assert response.status_code == 200
    assert "session_id" in response.json()
```

### Property-Based Testing

Property-based tests will use Hypothesis (Python) for backend and fast-check (JavaScript) for frontend.

**Configuration**: Each property-based test should run a minimum of 100 iterations.

**Tagging**: Each property-based test must include a comment referencing the correctness property using the format: `**Feature: kepler-web-interface, Property {number}: {property_text}**`

**Key Properties to Test**:

1. **Input validation properties** (Properties 2, 6, 7): Generate random inputs and verify validation
2. **API request properties** (Properties 3, 9, 13, 29): Generate random valid inputs and verify API calls
3. **Display properties** (Properties 5, 10, 14-18, 20-28, 39): Generate random data and verify rendering
4. **State management properties** (Properties 11, 37, 38): Generate random state transitions and verify correctness
5. **Error handling properties** (Properties 32-35): Generate random error scenarios and verify handling
6. **Export properties** (Properties 41-42): Generate random results and verify export completeness


## UI/UX Design Guidelines

### Visual Design Principles

**Color Scheme**:
- Supported verdict: Green (#10B981)
- Refuted verdict: Red (#EF4444)
- Not Enough Information: Yellow/Amber (#F59E0B)
- Primary action: Blue (#3B82F6)
- Background: Light gray (#F9FAFB) or white
- Text: Dark gray (#111827)

**Typography**:
- Headings: Sans-serif (e.g., Inter, Roboto)
- Body text: Sans-serif, 16px base size for readability
- Code/technical: Monospace (e.g., Fira Code, Monaco)

**Spacing**:
- Use consistent spacing scale (4px, 8px, 16px, 24px, 32px, 48px)
- Generous whitespace for readability
- Clear visual hierarchy

### Layout Structure

```
┌─────────────────────────────────────────────────────────────┐
│                        Header                                │
│                   KEPLER Fact Checker                        │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│                     Input Section                            │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Claim Input (Textarea)                                │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌──────────────┐  ┌──────────────────────────────────────┐│
│  │ Image Upload │  │  Model Selector (Checkboxes)         ││
│  └──────────────┘  └──────────────────────────────────────┘│
│                    [Verify Claim Button]                     │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│                    Results Section                           │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Verdict Display (with confidence bar)                 │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Tabs: Evidence | Reasoning | Models | Claims          │ │
│  │  [Tab Content Area]                                    │ │
│  └────────────────────────────────────────────────────────┘ │
│  [Export Button]                                             │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│                    History Sidebar                           │
│  [Past Verifications List]                                   │
└─────────────────────────────────────────────────────────────┘
```

### Responsive Design

**Desktop (>1024px)**:
- Two-column layout: Main content + History sidebar
- Full-width input section
- Tabbed results display

**Tablet (768px - 1024px)**:
- Single column layout
- Collapsible history sidebar
- Stacked input components

**Mobile (<768px)**:
- Single column, vertical stack
- Full-width components
- Accordion-style results sections
- Bottom sheet for history

### Accessibility

- Semantic HTML elements
- ARIA labels for interactive elements
- Keyboard navigation support
- Focus indicators
- Color contrast ratio ≥ 4.5:1 for text
- Alt text for images
- Screen reader friendly

### Loading States

**Stages to Display**:
1. "Decomposing claim..."
2. "Retrieving evidence..."
3. "Ranking sources..."
4. "Analyzing evidence..."
5. "Generating verdicts..."
6. "Calculating confidence..."

**Loading Indicator**:
```javascript
export const LoadingIndicator = ({ stage }) => {
    return (
        <div className="loading-container">
            <div className="spinner"></div>
            <p className="loading-stage">{stage}</p>
            <p className="loading-message">This may take a moment...</p>
        </div>
    );
};
```

## Deployment Considerations

### Backend Deployment

**Requirements**:
- Python 3.9+
- FastAPI/Flask server
- ASGI server (Uvicorn for FastAPI)
- Environment variables for configuration

**Docker Configuration**:
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Frontend Deployment

**Build Process**:
```bash
npm run build
# Generates optimized static files in build/ directory
```

**Hosting Options**:
- Static hosting: Netlify, Vercel, GitHub Pages
- CDN: CloudFlare, AWS CloudFront
- Traditional: Nginx serving static files

**Environment Configuration**:
```javascript
// .env.production
REACT_APP_API_URL=https://api.kepler.example.com
```

### Security Considerations

**API Security**:
- Rate limiting to prevent abuse
- Input sanitization
- HTTPS only in production
- CORS configuration for specific origins
- API key authentication (optional)

**Frontend Security**:
- Content Security Policy headers
- XSS protection
- Sanitize user input before display
- Secure cookie handling for session storage

## Performance Optimization

**Frontend**:
- Code splitting for faster initial load
- Lazy loading for heavy components
- Image optimization
- Caching API responses
- Debouncing input validation

**Backend**:
- Async request handling
- Connection pooling
- Response compression (gzip)
- Caching for model list endpoint
- Request timeout configuration

## Monitoring and Logging

**Frontend Monitoring**:
- Error tracking (e.g., Sentry)
- Performance metrics (Core Web Vitals)
- User analytics (optional)

**Backend Monitoring**:
- Request/response logging
- Error tracking and alerting
- Performance metrics (response time, throughput)
- Health check endpoint monitoring

**Logging Format**:
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Log all API requests
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"{request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Status: {response.status_code}")
    return response
```

