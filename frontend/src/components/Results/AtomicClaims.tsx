/**
 * AtomicClaims Component
 * 
 * Task 15: Implement AtomicClaims component
 * - Display list of atomic claims from API response
 * - Show claim text and verification status for each
 * - Implement expand/collapse functionality (accordion or details/summary)
 * - Show detailed verification results when expanded
 * - Show overall verdict for compound claims (when multiple atomic claims exist)
 * - Add visual indicators for claim status (icons or colors)
 * 
 * Requirements: 9.1, 9.2, 9.3, 9.4, 9.5
 */

import React, { useState } from 'react';
import { AtomicClaim, VerdictType, VerificationResult } from '../../types/verification';
import { getVerdictColorClass } from '../../utils/formatting';
import './AtomicClaims.css';

interface AtomicClaimsProps {
  atomicClaims: AtomicClaim[];
  verificationResult?: VerificationResult;
}

export const AtomicClaims: React.FC<AtomicClaimsProps> = ({
  atomicClaims,
  verificationResult,
}) => {
  const [expandedClaims, setExpandedClaims] = useState<Set<string>>(new Set());

  // Toggle expansion state for a claim
  const toggleClaim = (claimId: string) => {
    setExpandedClaims((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(claimId)) {
        newSet.delete(claimId);
      } else {
        newSet.add(claimId);
      }
      return newSet;
    });
  };

  // Get status icon based on verification status
  const getStatusIcon = (status?: VerdictType): string => {
    if (!status) return '⏳';
    switch (status) {
      case 'Supported':
        return '✓';
      case 'Refuted':
        return '✗';
      case 'Not Enough Information':
        return '?';
      default:
        return '⏳';
    }
  };

  // Get status class for styling
  const getStatusClass = (status?: VerdictType): string => {
    if (!status) return 'status-pending';
    return getVerdictColorClass(status);
  };

  // Check if this is a compound claim (multiple atomic claims)
  const isCompoundClaim = atomicClaims.length > 1;

  // Calculate overall verdict for compound claims
  const getOverallVerdict = (): VerdictType | null => {
    if (!isCompoundClaim || !verificationResult) return null;

    // Use the consensus verdict from the verification result
    return verificationResult.consensus_verdict.final_classification;
  };

  const overallVerdict = getOverallVerdict();

  if (atomicClaims.length === 0) {
    return null;
  }

  return (
    <div className="atomic-claims" role="region" aria-label="Atomic claims">
      <h3 className="atomic-claims-title">
        {isCompoundClaim ? 'Claim Breakdown' : 'Claim Analysis'}
      </h3>

      {/* Overall verdict for compound claims */}
      {isCompoundClaim && overallVerdict && (
        <div className="atomic-claims-overall">
          <div className="atomic-claims-overall-label">Overall Verdict:</div>
          <div className={`atomic-claims-overall-verdict ${getVerdictColorClass(overallVerdict)}`}>
            <span className="atomic-claims-overall-icon">{getStatusIcon(overallVerdict)}</span>
            <span className="atomic-claims-overall-text">{overallVerdict}</span>
          </div>
        </div>
      )}

      {/* List of atomic claims */}
      <div className="atomic-claims-list">
        {atomicClaims.map((claim) => {
          const isExpanded = expandedClaims.has(claim.id);
          const statusClass = getStatusClass(claim.verification_status);
          const statusIcon = getStatusIcon(claim.verification_status);

          return (
            <div key={claim.id} className="atomic-claim-item">
              {/* Claim header - always visible */}
              <button
                className="atomic-claim-header"
                onClick={() => toggleClaim(claim.id)}
                aria-expanded={isExpanded}
                aria-controls={`claim-details-${claim.id}`}
              >
                <div className="atomic-claim-header-content">
                  <span className={`atomic-claim-status-icon ${statusClass}`}>
                    {statusIcon}
                  </span>
                  <span className="atomic-claim-text">{claim.text}</span>
                  <span className={`atomic-claim-status-badge ${statusClass}`}>
                    {claim.verification_status || 'Pending'}
                  </span>
                </div>
                <span className={`atomic-claim-expand-icon ${isExpanded ? 'expanded' : ''}`}>
                  ▼
                </span>
              </button>

              {/* Claim details - shown when expanded */}
              {isExpanded && (
                <div
                  id={`claim-details-${claim.id}`}
                  className="atomic-claim-details"
                  role="region"
                  aria-label={`Details for claim ${claim.id}`}
                >
                  <div className="atomic-claim-detail-section">
                    <h4 className="atomic-claim-detail-title">Claim Information</h4>
                    <div className="atomic-claim-detail-item">
                      <span className="atomic-claim-detail-label">ID:</span>
                      <span className="atomic-claim-detail-value">{claim.id}</span>
                    </div>
                    <div className="atomic-claim-detail-item">
                      <span className="atomic-claim-detail-label">Type:</span>
                      <span className="atomic-claim-detail-value">
                        {claim.is_atomic ? 'Atomic' : 'Compound'}
                      </span>
                    </div>
                    {claim.parent_claim && (
                      <div className="atomic-claim-detail-item">
                        <span className="atomic-claim-detail-label">Parent Claim:</span>
                        <span className="atomic-claim-detail-value">{claim.parent_claim}</span>
                      </div>
                    )}
                  </div>

                  {/* Verification results */}
                  {claim.verification_status && verificationResult && (
                    <div className="atomic-claim-detail-section">
                      <h4 className="atomic-claim-detail-title">Verification Results</h4>
                      <div className="atomic-claim-detail-item">
                        <span className="atomic-claim-detail-label">Status:</span>
                        <span className={`atomic-claim-detail-value ${statusClass}`}>
                          {claim.verification_status}
                        </span>
                      </div>
                      
                      {/* Show confidence score if available */}
                      {verificationResult.confidence_score && (
                        <div className="atomic-claim-detail-item">
                          <span className="atomic-claim-detail-label">Confidence:</span>
                          <span className="atomic-claim-detail-value">
                            {(verificationResult.confidence_score.overall_score * 100).toFixed(1)}%
                          </span>
                        </div>
                      )}

                      {/* Show justification if available */}
                      {verificationResult.consensus_verdict?.consensus_justification && (
                        <div className="atomic-claim-detail-item atomic-claim-justification">
                          <span className="atomic-claim-detail-label">Justification:</span>
                          <p className="atomic-claim-detail-value">
                            {verificationResult.consensus_verdict.consensus_justification}
                          </p>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Info message for compound claims */}
      {isCompoundClaim && (
        <div className="atomic-claims-info">
          <p>
            This claim was broken down into {atomicClaims.length} atomic claims for verification.
            Click on each claim to see detailed verification results.
          </p>
        </div>
      )}
    </div>
  );
};

export default AtomicClaims;
