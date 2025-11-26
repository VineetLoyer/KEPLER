/**
 * ModelVerdicts Component Example
 * 
 * This file demonstrates the usage of the ModelVerdicts component
 * with various scenarios.
 */

import React from 'react';
import { ModelVerdicts } from './ModelVerdicts';
import { ConsensusVerdict } from '../../types/verification';

// Example 1: All models agree (Supported)
const exampleAllAgreeSupported: ConsensusVerdict = {
  final_classification: 'Supported',
  consensus_justification: 'All models unanimously agree that this claim is supported by strong evidence.',
  agreement_level: 1.0,
  individual_verdicts: [
    {
      model_id: 'gpt-4',
      classification: 'Supported',
      justification: 'Multiple credible sources confirm this claim with consistent evidence.',
      confidence: 0.95,
      evidence_references: ['evidence-1', 'evidence-2', 'evidence-3'],
    },
    {
      model_id: 'claude-3-opus',
      classification: 'Supported',
      justification: 'The evidence is comprehensive and from reliable sources.',
      confidence: 0.93,
      evidence_references: ['evidence-1', 'evidence-2', 'evidence-4'],
    },
    {
      model_id: 'gemini-pro',
      classification: 'Supported',
      justification: 'Strong corroboration across multiple independent sources.',
      confidence: 0.91,
      evidence_references: ['evidence-2', 'evidence-3', 'evidence-5'],
    },
  ],
};

// Example 2: Models disagree (Mixed verdicts)
const exampleDisagreement: ConsensusVerdict = {
  final_classification: 'Supported',
  consensus_justification: 'Majority of models support this claim, though one model found contradictory evidence.',
  agreement_level: 0.67,
  individual_verdicts: [
    {
      model_id: 'gpt-4',
      classification: 'Supported',
      justification: 'Recent studies and expert opinions strongly support this claim.',
      confidence: 0.88,
      evidence_references: ['evidence-1', 'evidence-2'],
    },
    {
      model_id: 'claude-3-opus',
      classification: 'Supported',
      justification: 'The preponderance of evidence supports this conclusion.',
      confidence: 0.85,
      evidence_references: ['evidence-1', 'evidence-3'],
    },
    {
      model_id: 'gemini-pro',
      classification: 'Refuted',
      justification: 'Found contradictory evidence from recent publications that challenge this claim.',
      confidence: 0.79,
      evidence_references: ['evidence-4', 'evidence-5'],
    },
  ],
};

// Example 3: All models agree (Refuted)
const exampleAllAgreeRefuted: ConsensusVerdict = {
  final_classification: 'Refuted',
  consensus_justification: 'All models agree that this claim is contradicted by available evidence.',
  agreement_level: 1.0,
  individual_verdicts: [
    {
      model_id: 'gpt-4',
      classification: 'Refuted',
      justification: 'Multiple authoritative sources directly contradict this claim.',
      confidence: 0.96,
      evidence_references: ['evidence-1', 'evidence-2'],
    },
    {
      model_id: 'claude-3-opus',
      classification: 'Refuted',
      justification: 'The evidence overwhelmingly refutes this assertion.',
      confidence: 0.94,
      evidence_references: ['evidence-1', 'evidence-3'],
    },
  ],
};

// Example 4: Not Enough Information with disagreement
const exampleNEIWithDisagreement: ConsensusVerdict = {
  final_classification: 'Not Enough Information',
  consensus_justification: 'Models could not reach a clear consensus due to insufficient or conflicting evidence.',
  agreement_level: 0.5,
  individual_verdicts: [
    {
      model_id: 'gpt-4',
      classification: 'Not Enough Information',
      justification: 'Available evidence is insufficient to make a determination.',
      confidence: 0.65,
      evidence_references: ['evidence-1'],
    },
    {
      model_id: 'claude-3-opus',
      classification: 'Supported',
      justification: 'Limited evidence suggests support, but more data is needed.',
      confidence: 0.58,
      evidence_references: ['evidence-1', 'evidence-2'],
    },
    {
      model_id: 'gemini-pro',
      classification: 'Refuted',
      justification: 'Some evidence contradicts the claim, but it is not conclusive.',
      confidence: 0.62,
      evidence_references: ['evidence-3'],
    },
    {
      model_id: 'llama-3',
      classification: 'Not Enough Information',
      justification: 'The evidence is too sparse to draw a reliable conclusion.',
      confidence: 0.60,
      evidence_references: [],
    },
  ],
};

export const ModelVerdictsExamples: React.FC = () => {
  return (
    <div style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '40px' }}>
      <div>
        <h2>Example 1: All Models Agree (Supported)</h2>
        <ModelVerdicts consensusVerdict={exampleAllAgreeSupported} />
      </div>

      <div>
        <h2>Example 2: Models Disagree (Mixed Verdicts)</h2>
        <ModelVerdicts consensusVerdict={exampleDisagreement} />
      </div>

      <div>
        <h2>Example 3: All Models Agree (Refuted)</h2>
        <ModelVerdicts consensusVerdict={exampleAllAgreeRefuted} />
      </div>

      <div>
        <h2>Example 4: Not Enough Information with Disagreement</h2>
        <ModelVerdicts consensusVerdict={exampleNEIWithDisagreement} />
      </div>
    </div>
  );
};

export default ModelVerdictsExamples;
