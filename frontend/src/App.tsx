import { useState, useEffect, useCallback } from 'react';
import { ClaimInput, ImageUpload, ModelSelector } from './components/InputForm';
import { History } from './components/History';
import { VerdictDisplay, EvidencePanel, ReasoningChain, ModelVerdicts, AtomicClaims } from './components/Results';
import { LoadingIndicator, ErrorMessage } from './components/Common';
import { ExportButton } from './components/Export';
import { verifyClaim } from './services/api';
import type { VerificationResult } from './types/verification';
import './App.css';

/**
 * Main KEPLER Web Interface Application
 * 
 * This component serves as the root of the web interface, managing:
 * - Input state (text, image, selected models)
 * - UI state (loading, errors, current stage)
 * - Results state (verification results)
 * - History state (past verifications)
 * 
 * Requirements: 1.1, 1.2, 2.4, 12.1, 12.4, 12.5, 13.1
 */

// LocalStorage key for history persistence
const HISTORY_STORAGE_KEY = 'kepler_verification_history';

// Maximum number of history items to store
const MAX_HISTORY_ITEMS = 50;

/**
 * Input state structure
 */
interface InputState {
  text: string;
  image: string | null;
  selectedModels: string[];
}

/**
 * UI state structure
 * Requirements: 2.4, 12.1, 12.4
 */
interface UIState {
  isLoading: boolean;
  currentStage: string | null;
  error: string | null;
  errorType: 'validation' | 'network' | 'api' | 'unknown' | null;
}

/**
 * Results state structure
 */
interface ResultsState {
  sessionId: string | null;
  originalInput: unknown | null;
  atomicClaims: unknown[];
  consensusVerdict: unknown | null;
  confidenceScore: unknown | null;
  processingMetadata: unknown | null;
  traceLog: unknown[];
}

/**
 * History item structure
 * Requirements: 13.1
 */
interface HistoryItem {
  sessionId: string;
  timestamp: string;
  claimText: string;
  verdict: string;
  confidence: number;
  fullResults: VerificationResult;
}

/**
 * Verification stages for progress indication
 * Requirements: 12.1, 12.2
 */
const VERIFICATION_STAGES = {
  INITIALIZING: 'Initializing verification...',
  DECOMPOSING: 'Decomposing claim...',
  RETRIEVING: 'Retrieving evidence...',
  RERANKING: 'Ranking evidence sources...',
  VERIFYING: 'Verifying with language models...',
  AGGREGATING: 'Aggregating results...',
  FINALIZING: 'Finalizing verdict...',
} as const;

function App() {
  // Input state
  const [input, setInput] = useState<InputState>({
    text: '',
    image: null,
    selectedModels: [],
  });

  // UI state
  const [ui, setUi] = useState<UIState>({
    isLoading: false,
    currentStage: null,
    error: null,
    errorType: null,
  });

  // Results state
  const [results, setResults] = useState<ResultsState>({
    sessionId: null,
    originalInput: null,
    atomicClaims: [],
    consensusVerdict: null,
    confidenceScore: null,
    processingMetadata: null,
    traceLog: [],
  });

  // History state
  const [history, setHistory] = useState<HistoryItem[]>([]);

  /**
   * Load history from localStorage on mount
   * Requirements: 13.1
   */
  useEffect(() => {
    loadHistoryFromStorage();
  }, []);

  /**
   * Save history to localStorage whenever it changes
   * Requirements: 13.1
   */
  useEffect(() => {
    saveHistoryToStorage(history);
  }, [history]);

  /**
   * Load history from localStorage
   */
  const loadHistoryFromStorage = useCallback(() => {
    try {
      const stored = localStorage.getItem(HISTORY_STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored);
        if (Array.isArray(parsed)) {
          setHistory(parsed);
        }
      }
    } catch (error) {
      console.error('Failed to load history from localStorage:', error);
    }
  }, []);

  /**
   * Save history to localStorage
   */
  const saveHistoryToStorage = useCallback((historyItems: HistoryItem[]) => {
    try {
      localStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(historyItems));
    } catch (error) {
      console.error('Failed to save history to localStorage:', error);
    }
  }, []);

  /**
   * Add a verification to history
   * Requirements: 13.1
   */
  const addToHistory = useCallback((result: VerificationResult) => {
    const historyItem: HistoryItem = {
      sessionId: result.session_id,
      timestamp: new Date().toISOString(),
      claimText: typeof result.original_input === 'object' && result.original_input !== null && 'text' in result.original_input
        ? String((result.original_input as { text?: string }).text || '')
        : '',
      verdict: result.consensus_verdict?.final_classification || 'Unknown',
      confidence: result.confidence_score?.overall_score || 0,
      fullResults: result,
    };

    setHistory(prev => {
      const updated = [historyItem, ...prev];
      // Keep only the most recent items
      return updated.slice(0, MAX_HISTORY_ITEMS);
    });
  }, []);

  /**
   * Clear all history
   * Requirements: 13.1
   */
  const clearHistory = useCallback(() => {
    setHistory([]);
    // Note: We don't remove the key, just set it to empty array
    // This is because the useEffect will save it anyway
  }, []);

  /**
   * Load a history item's results
   * Requirements: 13.5
   */
  const loadHistoryItem = useCallback((item: HistoryItem) => {
    setResults({
      sessionId: item.fullResults.session_id,
      originalInput: item.fullResults.original_input,
      atomicClaims: item.fullResults.atomic_claims,
      consensusVerdict: item.fullResults.consensus_verdict,
      confidenceScore: item.fullResults.confidence_score,
      processingMetadata: item.fullResults.processing_metadata,
      traceLog: item.fullResults.trace_log,
    });
    
    // Clear any errors
    setUi(prev => ({ ...prev, error: null, errorType: null }));
  }, []);

  /**
   * Update input text
   */
  const handleClaimChange = useCallback((text: string) => {
    setInput(prev => ({ ...prev, text }));
    // Clear validation errors when user types
    if (ui.errorType === 'validation') {
      setUi(prev => ({ ...prev, error: null, errorType: null }));
    }
  }, [ui.errorType]);

  /**
   * Update input image
   */
  const handleImageChange = useCallback((image: string | null) => {
    setInput(prev => ({ ...prev, image }));
  }, []);

  /**
   * Update selected models
   */
  const handleModelsChange = useCallback((models: string[]) => {
    setInput(prev => ({ ...prev, selectedModels: models }));
  }, []);

  /**
   * Set loading state with stage
   * Requirements: 2.4, 12.1, 12.4
   */
  const setLoadingState = useCallback((isLoading: boolean, stage: string | null = null) => {
    setUi(prev => ({
      ...prev,
      isLoading,
      currentStage: stage,
      error: isLoading ? null : prev.error, // Clear errors when starting new verification
      errorType: isLoading ? null : prev.errorType,
    }));
  }, []);

  /**
   * Set error state
   * Requirements: 11.1, 11.2, 11.4, 12.5
   */
  const setErrorState = useCallback((
    error: string,
    errorType: UIState['errorType'] = 'unknown'
  ) => {
    setUi(prev => ({
      ...prev,
      isLoading: false,
      currentStage: null,
      error,
      errorType,
    }));
  }, []);

  /**
   * Clear error state
   */
  const clearError = useCallback(() => {
    setUi(prev => ({
      ...prev,
      error: null,
      errorType: null,
    }));
  }, []);

  /**
   * Reset results state
   */
  const clearResults = useCallback(() => {
    setResults({
      sessionId: null,
      originalInput: null,
      atomicClaims: [],
      consensusVerdict: null,
      confidenceScore: null,
      processingMetadata: null,
      traceLog: [],
    });
  }, []);

  /**
   * Simulate verification stages for progress indication
   * Requirements: 12.1, 12.2
   */
  const simulateVerificationStages = useCallback(async () => {
    const stages = Object.values(VERIFICATION_STAGES);
    for (let i = 0; i < stages.length; i++) {
      await new Promise(resolve => setTimeout(resolve, 500));
      setUi(prev => ({ ...prev, currentStage: stages[i] }));
    }
  }, []);

  /**
   * Handle claim submission
   * Requirements: 2.3, 2.4, 12.1, 12.4, 12.5, 13.1
   */
  const handleClaimSubmit = useCallback(async () => {
    // Validate input
    if (!input.text?.trim() && !input.image) {
      setErrorState('Please enter a claim or upload an image', 'validation');
      return;
    }

    if (input.selectedModels.length === 0) {
      setErrorState('Please select at least one model', 'validation');
      return;
    }

    // Clear previous results and errors
    clearResults();
    clearError();

    // Set loading state
    setLoadingState(true, VERIFICATION_STAGES.INITIALIZING);

    // Start stage simulation
    const stageSimulation = simulateVerificationStages();

    try {
      // Call API
      const result = await verifyClaim(
        input.text || undefined,
        input.image,
        input.selectedModels
      );

      // Stop stage simulation
      await stageSimulation;

      // Update results
      setResults({
        sessionId: result.session_id,
        originalInput: result.original_input,
        atomicClaims: result.atomic_claims,
        consensusVerdict: result.consensus_verdict,
        confidenceScore: result.confidence_score,
        processingMetadata: result.processing_metadata,
        traceLog: result.trace_log,
      });

      // Add to history
      addToHistory(result as VerificationResult);

      // Clear loading state
      setLoadingState(false);
    } catch (error) {
      // Stop stage simulation
      await stageSimulation;

      // Handle error
      if (error instanceof Error) {
        const errorMessage = error.message;
        
        // Determine error type
        let errorType: UIState['errorType'] = 'unknown';
        if (errorMessage.includes('network') || errorMessage.includes('connection')) {
          errorType = 'network';
        } else if (errorMessage.includes('API Error')) {
          errorType = 'api';
        }

        setErrorState(errorMessage, errorType);
      } else {
        setErrorState('An unexpected error occurred', 'unknown');
      }
    }
  }, [
    input,
    setLoadingState,
    setErrorState,
    clearError,
    clearResults,
    simulateVerificationStages,
    addToHistory,
  ]);

  return (
    <div className="app">
      <header className="app-header">
        <h1>KEPLER Fact Checker</h1>
        <p>AI-Powered Fact Verification System</p>
      </header>

      <main className="app-main">
        <section className="input-section">
          <h2>Submit a Claim</h2>
          <p>Enter a claim to verify or upload an image for multimodal verification.</p>
          
          <ClaimInput
            value={input.text}
            onChange={handleClaimChange}
            onSubmit={handleClaimSubmit}
            disabled={ui.isLoading}
          />

          <ImageUpload
            onImageSelect={handleImageChange}
            disabled={ui.isLoading}
          />

          <ModelSelector
            selectedModels={input.selectedModels}
            onSelectionChange={handleModelsChange}
            disabled={ui.isLoading}
          />
        </section>

        {ui.isLoading && (
          <LoadingIndicator stage={ui.currentStage || undefined} />
        )}

        {ui.error && (
          <ErrorMessage
            message={ui.error}
            type={ui.errorType || 'general'}
            onDismiss={clearError}
            onRetry={ui.errorType === 'network' || ui.errorType === 'api' ? handleClaimSubmit : undefined}
          />
        )}

        {results.consensusVerdict && results.confidenceScore && (
          <section className="results-section">
            <h2>Verification Results</h2>
            
            <VerdictDisplay
              verdict={results.consensusVerdict as any}
              confidenceScore={results.confidenceScore as any}
            />

            {results.confidenceScore && (results.confidenceScore as any).structured_justification?.source_links?.length > 0 && (
              <EvidencePanel
                evidence={(results.confidenceScore as any).structured_justification.source_links}
              />
            )}

            {results.confidenceScore && (results.confidenceScore as any).structured_justification?.reasoning_chain && (
              <ReasoningChain
                reasoningChain={(results.confidenceScore as any).structured_justification.reasoning_chain}
              />
            )}

            {results.consensusVerdict && (results.consensusVerdict as any).individual_verdicts?.length > 0 && (
              <ModelVerdicts
                verdicts={(results.consensusVerdict as any).individual_verdicts}
              />
            )}

            {results.atomicClaims && results.atomicClaims.length > 0 && (
              <AtomicClaims
                claims={results.atomicClaims as any}
              />
            )}

            <ExportButton
              results={results as any}
            />
          </section>
        )}
      </main>

      <History
        history={history}
        onItemClick={loadHistoryItem}
        onClearHistory={clearHistory}
      />
    </div>
  );
}

export default App;
