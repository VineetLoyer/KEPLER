/**
 * HistoryItem Component
 * 
 * Displays a single history item with:
 * - Truncated claim text
 * - Verdict badge
 * - Timestamp
 * - Confidence score
 * 
 * Requirements: 13.2, 13.3, 13.4
 */

import React from 'react';
import { formatTimestamp, truncateText, getVerdictColorClass, formatPercentage } from '../../utils/formatting';
import type { HistoryItemData } from './History';
import './HistoryItem.css';

interface HistoryItemProps {
  item: HistoryItemData;
  onClick: () => void;
}

/**
 * Maximum length for claim text display in history
 */
const MAX_CLAIM_LENGTH = 80;

/**
 * HistoryItem Component
 * 
 * Displays a single verification history entry.
 * Requirements: 13.2, 13.3, 13.4
 */
export const HistoryItem: React.FC<HistoryItemProps> = ({ item, onClick }) => {
  const verdictClass = getVerdictColorClass(item.verdict);
  const truncatedClaim = truncateText(item.claimText, MAX_CLAIM_LENGTH);
  const formattedTimestamp = formatTimestamp(item.timestamp);
  const formattedConfidence = formatPercentage(item.confidence, 0);

  return (
    <button
      className="history-item"
      onClick={onClick}
      role="listitem"
      aria-label={`View verification for: ${truncatedClaim}`}
    >
      <div className="history-item-content">
        {/* Claim Text */}
        <div className="history-item-claim">
          {truncatedClaim}
        </div>

        {/* Verdict and Confidence */}
        <div className="history-item-meta">
          <span className={`history-item-verdict ${verdictClass}`}>
            {item.verdict}
          </span>
          <span className="history-item-confidence">
            {formattedConfidence}
          </span>
        </div>

        {/* Timestamp */}
        <div className="history-item-timestamp">
          {formattedTimestamp}
        </div>
      </div>
    </button>
  );
};

export default HistoryItem;
