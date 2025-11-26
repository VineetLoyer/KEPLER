/**
 * VerdictDisplay Component Example
 * 
 * This file demonstrates how to use the VerdictDisplay component
 * with sample data.
 */

import React from 'react';
import { VerdictDisplay } from './VerdictDisplay';
import type { ConsensusVerdict, ConfidenceScore } from '../../types/verification';

// Example 1: Supported verdict with high confidence
const supportedVerdict: ConsensusVerdict = {
  final_classification: 'Supported',
  consensus_justification:
    'Multiple reliable sources confirm that the Earth orbits the Sun. This is a well-established scientific fact supported by centuries of astronomical observations and measurements.',
  individual_verdicts: [],
  agreement_level: 0.95,
};

const highConfidence: ConfidenceScore = {
  overall_score: 0.92,
  source_reliability: 0.95,
  model_agreement: 0.90,
  evidence_recency: 0.88,
  structured_justification: {
    summary: 'High confidence based on multiple reliable sources',
    key_evidence: [],
    reasoning_chain: {
      steps: [],
      agreements: [],
      conflicts: [],
      gaps: [],
    },
    source_links: [],
  },
};

// Example 2: Refuted verdict with medium confidence
const refutedVerdict: ConsensusVerdict = {
  final_classification: 'Refuted',
  consensus_justification:
    'The claim that the Earth is flat has been thoroughly debunked by scientific evidence. Satellite imagery, physics, and direct observations from space all confirm the Earth is spherical.',
  individual_verdicts: [],
  agreement_level: 0.88,
};

const mediumConfidence: ConfidenceScore = {
  overall_score: 0.75,
  source_reliability: 0.80,
  model_agreement: 0.72,
  evidence_recency: 0.73,
  structured_justification: {
    summary: 'Medium confidence with some conflicting sources',
    key_evidence: [],
    reasoning_chain: {
      steps: [],
      agreements: [],
      conflicts: [],
      gaps: [],
    },
    source_links: [],
  },
};

// Example 3: Not Enough Information verdict with low confidence
const neiVerdict: ConsensusVerdict = {
  final_classification: 'Not Enough Information',
  consensus_justification:
    'There is insufficient reliable evidence to verify this claim. More research and data are needed to reach a definitive conclusion.',
  individual_verdicts: [],
  agreement_level: 0.45,
};

const lowConfidence: ConfidenceScore = {
  overall_score: 0.35,
  source_reliability: 0.40,
  model_agreement: 0.30,
  evidence_recency: 0.35,
  structured_justification: {
    summary: 'Low confidence due to lack of evidence',
    key_evidence: [],
    reasoning_chain: {
      steps: [],
      agreements: [],
      conflicts: [],
      gaps: [],
    },
    source_links: [],
  },
};

export const VerdictDisplayExamples: React.FC = () => {
  return (
    <div style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '40px' }}>
      <div>
        <h2>Example 1: Supported Verdict (High Confidence)</h2>
        <VerdictDisplay verdict={supportedVerdict} confidenceScore={highConfidence} />
      </div>

      <div>
        <h2>Example 2: Refuted Verdict (Medium Confidence)</h2>
        <VerdictDisplay verdict={refutedVerdict} confidenceScore={mediumConfidence} />
      </div>

      <div>
        <h2>Example 3: Not Enough Information (Low Confidence)</h2>
        <VerdictDisplay verdict={neiVerdict} confidenceScore={lowConfidence} />
      </div>
    </div>
  );
};

export default VerdictDisplayExamples;
