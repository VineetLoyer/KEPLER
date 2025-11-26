/**
 * ModelVerdicts Component
 * 
 * Task 14: Implement ModelVerdicts component
 * - Display individual verdicts from each model in the response
 * - Show model name/ID, classification, and justification for each
 * - Show confidence score for each model verdict
 * - Visually indicate disagreements (highlight when classifications differ)
 * - Use consistent verdict styling (same colors as main verdict)
 * - Add borders or badges to highlight disagreeing models
 * 
 * Requirements: 8.1, 8.2, 8.3, 8.4, 8.5
 */

import React from 'react';
import { ConsensusVerdict, Verdict } from '../../types/verification';
import { ConfidenceBar } from '../Common/ConfidenceBar';
import { formatPercentage, getVerdictColorClass } from '../../utils/formatting';
import './ModelVerdicts.css';

interface ModelVerdictsProps {
  consensusVerdict: ConsensusVerdict;
}

export const ModelVerdicts: React.FC<ModelVerdictsProps> = ({
  consensusVerdict,
}) => {
  const { individual_verdicts, final_classification } = consensusVerdict;

  // Check if there are any disagreements
  const hasDisagreements = individual_verdicts.some(
    (verdict) => verdict.classification !== final_classification
  );

  // Helper function to check if a specific verdict disagrees with consensus
  const isDisagreeing = (verdict: Verdict): boolean => {
    return verdict.classification !== final_classification;
  };

  return (
    <div className="model-verdicts" role="region" aria-label="Individual model verdicts">
      <div className="model-verdicts-header">
        <h3 className="model-verdicts-title">Individual Model Verdicts</h3>
        {hasDisagreements && (
          <span className="model-verdicts-disagreement-badge">
            Disagreements Detected
          </span>
        )}
      </div>

      <div className="model-verdicts-list">
        {individual_verdicts.map((verdict, index) => {
          const verdictClass = getVerdictColorClass(verdict.classification);
          const disagreeing = isDisagreeing(verdict);

          return (
            <div
              key={`${verdict.model_id}-${index}`}
              className={`model-verdict-card ${disagreeing ? 'model-verdict-disagreeing' : ''}`}
            >
              {/* Model Header */}
              <div className="model-verdict-header">
                <div className="model-verdict-model-info">
                  <h4 className="model-verdict-model-name">{verdict.model_id}</h4>
                  {disagreeing && (
                    <span className="model-verdict-disagreement-indicator">
                      Disagrees with consensus
                    </span>
                  )}
                </div>
                <div className={`model-verdict-badge ${verdictClass}`}>
                  {verdict.classification}
                </div>
              </div>

              {/* Confidence Score */}
              <div className="model-verdict-confidence">
                <ConfidenceBar
                  score={verdict.confidence}
                  label="Confidence"
                  showPercentage={true}
                />
              </div>

              {/* Justification */}
              <div className="model-verdict-justification">
                <h5 className="model-verdict-justification-title">Justification</h5>
                <p className="model-verdict-justification-text">
                  {verdict.justification}
                </p>
              </div>

              {/* Evidence References (if available) */}
              {verdict.evidence_references && verdict.evidence_references.length > 0 && (
                <div className="model-verdict-evidence">
                  <h5 className="model-verdict-evidence-title">Evidence Used</h5>
                  <ul className="model-verdict-evidence-list">
                    {verdict.evidence_references.map((ref, refIndex) => (
                      <li key={refIndex} className="model-verdict-evidence-item">
                        {ref}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Agreement Level Summary */}
      <div className="model-verdicts-summary">
        <div className="model-verdicts-agreement">
          <span className="model-verdicts-agreement-label">Agreement Level:</span>
          <span className="model-verdicts-agreement-value">
            {formatPercentage(consensusVerdict.agreement_level, 0)}
          </span>
        </div>
      </div>
    </div>
  );
};

export default ModelVerdicts;
