/**
 * EvidencePanel Component
 * 
 * Task 12: Implement EvidencePanel component
 * - Display list of evidence sources from API response
 * - Show title, URL, and credibility score for each source
 * - Make URLs clickable with target="_blank" and rel="noopener noreferrer"
 * - Display evidence summary text for each piece
 * - Format credibility scores as percentages
 * - Add appropriate styling and spacing between items
 * 
 * Requirements: 6.1, 6.2, 6.3, 6.4, 6.5
 */

import React from 'react';
import { EvidencePiece } from '../../types/verification';
import { formatPercentage } from '../../utils/formatting';
import './EvidencePanel.css';

interface EvidencePanelProps {
  evidence: EvidencePiece[];
}

export const EvidencePanel: React.FC<EvidencePanelProps> = ({ evidence }) => {
  // Handle empty evidence list
  if (!evidence || evidence.length === 0) {
    return (
      <div className="evidence-panel evidence-panel-empty">
        <p className="evidence-empty-message">No evidence sources available.</p>
      </div>
    );
  }

  return (
    <div className="evidence-panel" role="region" aria-label="Evidence sources">
      <h3 className="evidence-panel-title">Evidence Sources</h3>
      <div className="evidence-list">
        {evidence.map((item, index) => (
          <div key={item.id || index} className="evidence-item">
            {/* Evidence Header with Title and Credibility Score */}
            <div className="evidence-header">
              <h4 className="evidence-title">{item.source.title}</h4>
              <span className="evidence-credibility-score">
                Credibility: {formatPercentage(item.credibility_score || 0, 0)}
              </span>
            </div>

            {/* Evidence Summary */}
            <p className="evidence-summary">{item.summary}</p>

            {/* Evidence Source Link */}
            <a
              href={item.source.url}
              target="_blank"
              rel="noopener noreferrer"
              className="evidence-link"
              aria-label={`View source: ${item.source.title}`}
            >
              View Source →
            </a>

            {/* Additional metadata (optional display) */}
            {item.source.domain && (
              <div className="evidence-metadata">
                <span className="evidence-domain">{item.source.domain}</span>
                {item.source.publish_date && (
                  <span className="evidence-date">
                    {new Date(item.source.publish_date).toLocaleDateString()}
                  </span>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default EvidencePanel;
