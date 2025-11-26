/**
 * History Component
 * 
 * Task 17: Implement History component
 * - Display list of past verifications from state/localStorage
 * - Show claim text (truncated if long), verdict, and timestamp for each item
 * - Handle history item clicks to load and display full results
 * - Implement localStorage persistence for history
 * - Add clear history functionality
 * - Style as sidebar or collapsible panel
 * - Format timestamps in human-readable format
 * 
 * Requirements: 13.1, 13.2, 13.3, 13.4, 13.5
 */

import React, { useState } from 'react';
import { HistoryItem } from './HistoryItem.tsx';
import type { VerificationResult } from '../../types/verification';
import './History.css';

/**
 * History item structure
 * Requirements: 13.1
 */
export interface HistoryItemData {
  sessionId: string;
  timestamp: string;
  claimText: string;
  verdict: string;
  confidence: number;
  fullResults: VerificationResult;
}

interface HistoryProps {
  history: HistoryItemData[];
  onItemClick: (item: HistoryItemData) => void;
  onClearHistory: () => void;
}

/**
 * History Component
 * 
 * Displays a list of past verifications with the ability to:
 * - View past verification results
 * - Clear all history
 * - Collapse/expand the history panel
 * 
 * Requirements: 13.1, 13.2, 13.3, 13.4, 13.5
 */
export const History: React.FC<HistoryProps> = ({
  history,
  onItemClick,
  onClearHistory,
}) => {
  const [isCollapsed, setIsCollapsed] = useState(false);

  const handleToggleCollapse = () => {
    setIsCollapsed(!isCollapsed);
  };

  const handleClearHistory = () => {
    if (window.confirm('Are you sure you want to clear all history? This action cannot be undone.')) {
      onClearHistory();
    }
  };

  return (
    <aside 
      className={`history-panel ${isCollapsed ? 'history-panel-collapsed' : ''}`}
      role="complementary"
      aria-label="Verification history"
    >
      <div className="history-header">
        <h3 className="history-title">
          History
          {history.length > 0 && (
            <span className="history-count">({history.length})</span>
          )}
        </h3>
        <button
          className="history-toggle-button"
          onClick={handleToggleCollapse}
          aria-label={isCollapsed ? 'Expand history' : 'Collapse history'}
          aria-expanded={!isCollapsed}
        >
          {isCollapsed ? '▶' : '◀'}
        </button>
      </div>

      {!isCollapsed && (
        <div className="history-content">
          {history.length === 0 ? (
            <div className="history-empty">
              <p className="history-empty-text">No verification history yet.</p>
              <p className="history-empty-hint">
                Submit a claim to start building your history.
              </p>
            </div>
          ) : (
            <>
              <div className="history-actions">
                <button
                  className="history-clear-button"
                  onClick={handleClearHistory}
                  aria-label="Clear all history"
                >
                  Clear All
                </button>
              </div>

              <div className="history-list" role="list">
                {history.map((item) => (
                  <HistoryItem
                    key={item.sessionId}
                    item={item}
                    onClick={() => onItemClick(item)}
                  />
                ))}
              </div>
            </>
          )}
        </div>
      )}
    </aside>
  );
};

export default History;
