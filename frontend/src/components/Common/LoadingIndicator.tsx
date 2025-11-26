/**
 * LoadingIndicator Component
 * 
 * Task 10: Implement LoadingIndicator component
 * - Create animated loading spinner (CSS or SVG)
 * - Accept current stage as prop
 * - Display stage-specific progress messages
 * - Add "This may take a moment..." helper text
 * - Style with appropriate spacing and centering
 * 
 * Requirements: 2.4, 12.1, 12.2
 */

import React from 'react';
import './LoadingIndicator.css';

export type VerificationStage =
  | 'initializing'
  | 'decomposing'
  | 'retrieving'
  | 'reranking'
  | 'verifying'
  | 'aggregating'
  | 'scoring'
  | 'finalizing';

interface LoadingIndicatorProps {
  currentStage?: VerificationStage;
}

const stageMessages: Record<VerificationStage, string> = {
  initializing: 'Initializing verification process...',
  decomposing: 'Breaking down claim into atomic components...',
  retrieving: 'Retrieving evidence from sources...',
  reranking: 'Ranking evidence by relevance...',
  verifying: 'Verifying claim against evidence...',
  aggregating: 'Aggregating results from multiple models...',
  scoring: 'Calculating confidence scores...',
  finalizing: 'Finalizing verification results...',
};

export const LoadingIndicator: React.FC<LoadingIndicatorProps> = ({
  currentStage = 'initializing',
}) => {
  const message = stageMessages[currentStage];

  return (
    <div className="loading-indicator" role="status" aria-live="polite">
      <div className="loading-spinner-container">
        <svg
          className="loading-spinner"
          viewBox="0 0 50 50"
          aria-hidden="true"
        >
          <circle
            className="loading-spinner-track"
            cx="25"
            cy="25"
            r="20"
            fill="none"
            strokeWidth="4"
          />
          <circle
            className="loading-spinner-path"
            cx="25"
            cy="25"
            r="20"
            fill="none"
            strokeWidth="4"
            strokeLinecap="round"
          />
        </svg>
      </div>

      <div className="loading-content">
        <p className="loading-stage-message">{message}</p>
        <p className="loading-helper-text">This may take a moment...</p>
      </div>

      <span className="sr-only">
        Loading: {message}
      </span>
    </div>
  );
};

export default LoadingIndicator;
