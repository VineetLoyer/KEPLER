/**
 * VerdictDisplay Component
 * 
 * Task 11: Implement VerdictDisplay component
 * - Display verdict classification badge with distinct colors (green/red/yellow)
 * - Show confidence score formatted as percentage (0-100%)
 * - Render visual confidence indicator (progress bar or gauge)
 * - Display consensus justification text in readable format
 * - Show confidence factor breakdown (source reliability, model agreement, evidence recency)
 * 
 * Requirements: 2.5, 5.1, 5.2, 5.3, 5.4, 5.5
 */

import React from 'react';
import type { ConsensusVerdict, ConfidenceScore } from '../../types/verification';
import { ConfidenceBar } from '../Common/ConfidenceBar';
import { formatPercentage, getVerdictColorClass } from '../../utils/formatting';
import './VerdictDisplay.css';

interface VerdictDisplayProps {
  verdict: ConsensusVerdict;
  confidenceScore: ConfidenceScore;
}

export const VerdictDisplay: React.FC<VerdictDisplayProps> = ({
  verdict,
  confidenceScore,
}) => {
  const verdictClass = getVerdictColorClass(verdict.final_classification);

  return (
    <div className="verdict-display" role="region" aria-label="Verification verdict">
      {/* Verdict Badge */}
      <div className={`verdict-badge ${verdictClass}`}>
        <span className="verdict-badge-text">{verdict.final_classification}</span>
      </div>

      {/* Overall Confidence Score */}
      <div className="verdict-confidence-section">
        <h3 className="verdict-section-title">Confidence Score</h3>
        <div className="verdict-confidence-main">
          <ConfidenceBar
            score={confidenceScore.overall_score}
            label="Overall"
            showPercentage={true}
          />
        </div>
        <div className="verdict-confidence-percentage-large">
          {formatPercentage(confidenceScore.overall_score, 1)}
        </div>
      </div>

      {/* Consensus Justification */}
      <div className="verdict-justification-section">
        <h3 className="verdict-section-title">Justification</h3>
        <p className="verdict-justification-text">
          {verdict.consensus_justification}
        </p>
      </div>

      {/* Confidence Factor Breakdown */}
      <div className="verdict-breakdown-section">
        <h3 className="verdict-section-title">Confidence Factors</h3>
        <div className="verdict-breakdown-list">
          <div className="verdict-breakdown-item">
            <ConfidenceBar
              score={confidenceScore.source_reliability}
              label="Source Reliability"
              showPercentage={true}
            />
          </div>
          <div className="verdict-breakdown-item">
            <ConfidenceBar
              score={confidenceScore.model_agreement}
              label="Model Agreement"
              showPercentage={true}
            />
          </div>
          <div className="verdict-breakdown-item">
            <ConfidenceBar
              score={confidenceScore.evidence_recency}
              label="Evidence Recency"
              showPercentage={true}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default VerdictDisplay;
