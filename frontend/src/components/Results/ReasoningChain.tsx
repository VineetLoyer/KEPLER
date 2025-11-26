/**
 * ReasoningChain Component
 * 
 * Task 13: Implement ReasoningChain component
 * - Display reasoning steps in sequential order by step number
 * - Show step description, evidence used, and conclusion for each step
 * - Display agreements section with common assertions and strength
 * - Display conflicts section with conflicting assertions and severity
 * - Display information gaps section with missing aspects
 * - Apply distinct styling for agreements (green) and conflicts (red/yellow)
 * - Format strength/severity as percentages
 * 
 * Requirements: 7.1, 7.2, 7.3, 7.4, 7.5
 */

import React from 'react';
import { ReasoningChain as ReasoningChainType } from '../../types/verification';
import { formatPercentage } from '../../utils/formatting';
import './ReasoningChain.css';

interface ReasoningChainProps {
  reasoningChain: ReasoningChainType;
}

export const ReasoningChain: React.FC<ReasoningChainProps> = ({ reasoningChain }) => {
  // Handle empty reasoning chain
  if (!reasoningChain) {
    return (
      <div className="reasoning-chain reasoning-chain-empty">
        <p className="reasoning-empty-message">No reasoning chain available.</p>
      </div>
    );
  }

  const { steps, agreements, conflicts, gaps } = reasoningChain;

  return (
    <div className="reasoning-chain" role="region" aria-label="Reasoning process">
      <h3 className="reasoning-chain-title">Reasoning Process</h3>

      {/* Reasoning Steps Section */}
      {steps && steps.length > 0 && (
        <div className="reasoning-steps">
          {steps.map((step) => (
            <div key={step.step_number} className="reasoning-step">
              <div className="step-number">Step {step.step_number}</div>
              <div className="step-content">
                <p className="step-description">{step.description}</p>
                
                {/* Evidence Used */}
                {step.evidence_used && step.evidence_used.length > 0 && (
                  <div className="step-evidence">
                    <strong>Evidence used:</strong>
                    <ul className="step-evidence-list">
                      {step.evidence_used.map((evidenceId, i) => (
                        <li key={i} className="step-evidence-item">
                          {evidenceId}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Conclusion */}
                <p className="step-conclusion">
                  <strong>Conclusion:</strong> {step.conclusion}
                </p>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Agreements Section */}
      {agreements && agreements.length > 0 && (
        <div className="agreements-section">
          <h4 className="agreements-title">Agreements in Evidence</h4>
          <div className="agreements-list">
            {agreements.map((agreement, index) => (
              <div key={index} className="agreement-item">
                <p className="agreement-assertion">{agreement.common_assertion}</p>
                <span className="agreement-strength">
                  Strength: {formatPercentage(agreement.strength, 0)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Conflicts Section */}
      {conflicts && conflicts.length > 0 && (
        <div className="conflicts-section">
          <h4 className="conflicts-title">Conflicts in Evidence</h4>
          <div className="conflicts-list">
            {conflicts.map((conflict, index) => (
              <div key={index} className="conflict-item">
                <ul className="conflict-assertions-list">
                  {conflict.conflicting_assertions.map((assertion, i) => (
                    <li key={i} className="conflict-assertion">
                      {assertion}
                    </li>
                  ))}
                </ul>
                <span className="conflict-severity">
                  Severity: {formatPercentage(conflict.severity, 0)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Information Gaps Section */}
      {gaps && gaps.length > 0 && (
        <div className="gaps-section">
          <h4 className="gaps-title">Information Gaps</h4>
          <div className="gaps-list">
            {gaps.map((gap, index) => (
              <div key={index} className="gap-item">
                <p className="gap-aspect">{gap.missing_aspect}</p>
                <span className="gap-importance">
                  Importance: {formatPercentage(gap.importance, 0)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default ReasoningChain;
