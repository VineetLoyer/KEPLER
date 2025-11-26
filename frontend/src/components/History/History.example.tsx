/**
 * History Component Example
 * 
 * This file demonstrates the usage of the History component.
 */

import React, { useState } from 'react';
import { History } from './History';
import type { HistoryItemData } from './History';

/**
 * Example history data
 */
const exampleHistory: HistoryItemData[] = [
  {
    sessionId: 'session-1',
    timestamp: new Date('2025-11-25T10:30:00').toISOString(),
    claimText: 'The Earth is flat and surrounded by an ice wall.',
    verdict: 'Refuted',
    confidence: 0.95,
    fullResults: {
      session_id: 'session-1',
      original_input: { text: 'The Earth is flat and surrounded by an ice wall.' },
      atomic_claims: [],
      consensus_verdict: {
        final_classification: 'Refuted',
        consensus_justification: 'Scientific evidence overwhelmingly supports that Earth is spherical.',
        individual_verdicts: [],
        agreement_level: 0.95,
      },
      confidence_score: {
        overall_score: 0.95,
        source_reliability: 0.92,
        model_agreement: 0.98,
        evidence_recency: 0.95,
        structured_justification: {
          summary: 'Claim refuted by scientific consensus',
          key_evidence: [],
          reasoning_chain: { steps: [], agreements: [], conflicts: [], gaps: [] },
          source_links: [],
        },
      },
      processing_metadata: {},
      trace_log: [],
    },
  },
  {
    sessionId: 'session-2',
    timestamp: new Date('2025-11-25T09:15:00').toISOString(),
    claimText: 'Water boils at 100 degrees Celsius at sea level.',
    verdict: 'Supported',
    confidence: 0.99,
    fullResults: {
      session_id: 'session-2',
      original_input: { text: 'Water boils at 100 degrees Celsius at sea level.' },
      atomic_claims: [],
      consensus_verdict: {
        final_classification: 'Supported',
        consensus_justification: 'This is a well-established scientific fact.',
        individual_verdicts: [],
        agreement_level: 0.99,
      },
      confidence_score: {
        overall_score: 0.99,
        source_reliability: 0.98,
        model_agreement: 1.0,
        evidence_recency: 0.99,
        structured_justification: {
          summary: 'Claim supported by scientific consensus',
          key_evidence: [],
          reasoning_chain: { steps: [], agreements: [], conflicts: [], gaps: [] },
          source_links: [],
        },
      },
      processing_metadata: {},
      trace_log: [],
    },
  },
  {
    sessionId: 'session-3',
    timestamp: new Date('2025-11-25T08:00:00').toISOString(),
    claimText: 'Aliens built the pyramids in ancient Egypt.',
    verdict: 'Not Enough Information',
    confidence: 0.45,
    fullResults: {
      session_id: 'session-3',
      original_input: { text: 'Aliens built the pyramids in ancient Egypt.' },
      atomic_claims: [],
      consensus_verdict: {
        final_classification: 'Not Enough Information',
        consensus_justification: 'While there is no evidence for alien involvement, the exact construction methods remain debated.',
        individual_verdicts: [],
        agreement_level: 0.45,
      },
      confidence_score: {
        overall_score: 0.45,
        source_reliability: 0.50,
        model_agreement: 0.40,
        evidence_recency: 0.45,
        structured_justification: {
          summary: 'Insufficient evidence to make a determination',
          key_evidence: [],
          reasoning_chain: { steps: [], agreements: [], conflicts: [], gaps: [] },
          source_links: [],
        },
      },
      processing_metadata: {},
      trace_log: [],
    },
  },
];

/**
 * Example component demonstrating History usage
 */
export const HistoryExample: React.FC = () => {
  const [history, setHistory] = useState<HistoryItemData[]>(exampleHistory);
  const [selectedItem, setSelectedItem] = useState<HistoryItemData | null>(null);

  const handleItemClick = (item: HistoryItemData) => {
    setSelectedItem(item);
    console.log('Selected history item:', item);
  };

  const handleClearHistory = () => {
    setHistory([]);
    setSelectedItem(null);
    console.log('History cleared');
  };

  return (
    <div style={{ display: 'flex', height: '600px', border: '1px solid #ccc' }}>
      <div style={{ flex: 1, padding: '20px', overflowY: 'auto' }}>
        <h2>Main Content Area</h2>
        {selectedItem ? (
          <div>
            <h3>Selected Verification</h3>
            <p><strong>Claim:</strong> {selectedItem.claimText}</p>
            <p><strong>Verdict:</strong> {selectedItem.verdict}</p>
            <p><strong>Confidence:</strong> {(selectedItem.confidence * 100).toFixed(0)}%</p>
            <p><strong>Timestamp:</strong> {new Date(selectedItem.timestamp).toLocaleString()}</p>
          </div>
        ) : (
          <p>Click on a history item to view details</p>
        )}
      </div>
      
      <History
        history={history}
        onItemClick={handleItemClick}
        onClearHistory={handleClearHistory}
      />
    </div>
  );
};

export default HistoryExample;
