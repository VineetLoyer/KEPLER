/**
 * ReasoningChain Component Examples
 * 
 * This file demonstrates various usage examples of the ReasoningChain component.
 */

import React from 'react';
import { ReasoningChain } from './ReasoningChain';
import type { ReasoningChain as ReasoningChainType } from '../../types/verification';

// Example 1: Complete reasoning chain with all sections
export const CompleteReasoningChainExample = () => {
  const completeChain: ReasoningChainType = {
    steps: [
      {
        step_number: 1,
        description: 'Analyzed the claim to identify key factual assertions that can be verified',
        evidence_used: ['evidence-uuid-1', 'evidence-uuid-2'],
        conclusion: 'The claim contains three verifiable assertions about dates, locations, and quantities',
      },
      {
        step_number: 2,
        description: 'Retrieved and evaluated evidence from multiple credible sources',
        evidence_used: ['evidence-uuid-1', 'evidence-uuid-2', 'evidence-uuid-3'],
        conclusion: 'Found strong evidence supporting two assertions, with conflicting information on the third',
      },
      {
        step_number: 3,
        description: 'Assessed the reliability and recency of each evidence source',
        evidence_used: ['evidence-uuid-1', 'evidence-uuid-2', 'evidence-uuid-3', 'evidence-uuid-4'],
        conclusion: 'Most sources are recent and from reputable publishers, increasing confidence',
      },
    ],
    agreements: [
      {
        evidence_ids: ['evidence-uuid-1', 'evidence-uuid-2'],
        common_assertion: 'The event occurred on January 15, 2024',
        strength: 0.92,
      },
      {
        evidence_ids: ['evidence-uuid-2', 'evidence-uuid-3', 'evidence-uuid-4'],
        common_assertion: 'The location was confirmed to be New York City',
        strength: 0.88,
      },
    ],
    conflicts: [
      {
        evidence_ids: ['evidence-uuid-2', 'evidence-uuid-3'],
        conflicting_assertions: [
          'The attendance was reported as 10,000 people',
          'The attendance was reported as 15,000 people',
        ],
        severity: 0.65,
      },
    ],
    gaps: [
      {
        missing_aspect: 'Exact time of day when the event started',
        importance: 0.35,
      },
      {
        missing_aspect: 'Official statement from the organizing committee',
        importance: 0.55,
      },
    ],
  };

  return (
    <div style={{ padding: '2rem', maxWidth: '1200px', margin: '0 auto' }}>
      <h2>Complete Reasoning Chain Example</h2>
      <ReasoningChain reasoningChain={completeChain} />
    </div>
  );
};

// Example 2: Simple reasoning chain with only steps
export const SimpleReasoningChainExample = () => {
  const simpleChain: ReasoningChainType = {
    steps: [
      {
        step_number: 1,
        description: 'Examined the claim for factual content',
        evidence_used: ['evidence-a'],
        conclusion: 'Claim is straightforward and verifiable',
      },
      {
        step_number: 2,
        description: 'Verified against primary sources',
        evidence_used: ['evidence-a', 'evidence-b'],
        conclusion: 'All facts confirmed by reliable sources',
      },
    ],
    agreements: [],
    conflicts: [],
    gaps: [],
  };

  return (
    <div style={{ padding: '2rem', maxWidth: '1200px', margin: '0 auto' }}>
      <h2>Simple Reasoning Chain (Steps Only)</h2>
      <ReasoningChain reasoningChain={simpleChain} />
    </div>
  );
};

// Example 3: Reasoning chain with strong agreements
export const AgreementsExample = () => {
  const agreementsChain: ReasoningChainType = {
    steps: [
      {
        step_number: 1,
        description: 'Collected evidence from multiple sources',
        evidence_used: ['source-1', 'source-2', 'source-3'],
        conclusion: 'All sources align on key facts',
      },
    ],
    agreements: [
      {
        evidence_ids: ['source-1', 'source-2', 'source-3'],
        common_assertion: 'The scientific consensus supports this claim',
        strength: 0.95,
      },
      {
        evidence_ids: ['source-1', 'source-2'],
        common_assertion: 'The data was published in peer-reviewed journals',
        strength: 0.90,
      },
    ],
    conflicts: [],
    gaps: [],
  };

  return (
    <div style={{ padding: '2rem', maxWidth: '1200px', margin: '0 auto' }}>
      <h2>Reasoning Chain with Strong Agreements</h2>
      <ReasoningChain reasoningChain={agreementsChain} />
    </div>
  );
};

// Example 4: Reasoning chain with conflicts
export const ConflictsExample = () => {
  const conflictsChain: ReasoningChainType = {
    steps: [
      {
        step_number: 1,
        description: 'Analyzed conflicting reports from different sources',
        evidence_used: ['report-1', 'report-2', 'report-3'],
        conclusion: 'Significant disagreement found on key details',
      },
    ],
    agreements: [],
    conflicts: [
      {
        evidence_ids: ['report-1', 'report-2'],
        conflicting_assertions: [
          'The study included 500 participants',
          'The study included 750 participants',
        ],
        severity: 0.75,
      },
      {
        evidence_ids: ['report-2', 'report-3'],
        conflicting_assertions: [
          'Results showed a 20% improvement',
          'Results showed a 35% improvement',
          'Results showed no significant improvement',
        ],
        severity: 0.85,
      },
    ],
    gaps: [],
  };

  return (
    <div style={{ padding: '2rem', maxWidth: '1200px', margin: '0 auto' }}>
      <h2>Reasoning Chain with Conflicts</h2>
      <ReasoningChain reasoningChain={conflictsChain} />
    </div>
  );
};

// Example 5: Reasoning chain with information gaps
export const InformationGapsExample = () => {
  const gapsChain: ReasoningChainType = {
    steps: [
      {
        step_number: 1,
        description: 'Searched for comprehensive evidence',
        evidence_used: ['source-1', 'source-2'],
        conclusion: 'Some aspects of the claim lack sufficient evidence',
      },
    ],
    agreements: [],
    conflicts: [],
    gaps: [
      {
        missing_aspect: 'Independent verification from third-party sources',
        importance: 0.80,
      },
      {
        missing_aspect: 'Historical context and background information',
        importance: 0.45,
      },
      {
        missing_aspect: 'Expert commentary or analysis',
        importance: 0.60,
      },
    ],
  };

  return (
    <div style={{ padding: '2rem', maxWidth: '1200px', margin: '0 auto' }}>
      <h2>Reasoning Chain with Information Gaps</h2>
      <ReasoningChain reasoningChain={gapsChain} />
    </div>
  );
};

// Example 6: Empty reasoning chain
export const EmptyReasoningChainExample = () => {
  return (
    <div style={{ padding: '2rem', maxWidth: '1200px', margin: '0 auto' }}>
      <h2>Empty Reasoning Chain</h2>
      <ReasoningChain reasoningChain={null as any} />
    </div>
  );
};

// Example 7: Complex reasoning chain with all elements
export const ComplexReasoningChainExample = () => {
  const complexChain: ReasoningChainType = {
    steps: [
      {
        step_number: 1,
        description: 'Initial claim decomposition and analysis',
        evidence_used: [],
        conclusion: 'Claim contains multiple sub-assertions requiring separate verification',
      },
      {
        step_number: 2,
        description: 'Evidence retrieval from academic databases',
        evidence_used: ['academic-1', 'academic-2', 'academic-3'],
        conclusion: 'Found relevant peer-reviewed research',
      },
      {
        step_number: 3,
        description: 'Cross-reference with news sources',
        evidence_used: ['news-1', 'news-2'],
        conclusion: 'News reports generally align with academic findings',
      },
      {
        step_number: 4,
        description: 'Evaluate source credibility and recency',
        evidence_used: ['academic-1', 'academic-2', 'academic-3', 'news-1', 'news-2'],
        conclusion: 'Most sources are recent and highly credible',
      },
      {
        step_number: 5,
        description: 'Synthesize findings and identify consensus',
        evidence_used: ['academic-1', 'academic-2', 'academic-3', 'news-1', 'news-2'],
        conclusion: 'Strong consensus on main points, minor disagreements on details',
      },
    ],
    agreements: [
      {
        evidence_ids: ['academic-1', 'academic-2', 'academic-3'],
        common_assertion: 'The underlying mechanism is well-established',
        strength: 0.94,
      },
      {
        evidence_ids: ['news-1', 'news-2'],
        common_assertion: 'Recent developments support the claim',
        strength: 0.82,
      },
    ],
    conflicts: [
      {
        evidence_ids: ['academic-2', 'news-1'],
        conflicting_assertions: [
          'The effect size is moderate',
          'The effect size is large',
        ],
        severity: 0.45,
      },
    ],
    gaps: [
      {
        missing_aspect: 'Long-term follow-up data',
        importance: 0.70,
      },
      {
        missing_aspect: 'Replication studies from independent labs',
        importance: 0.65,
      },
    ],
  };

  return (
    <div style={{ padding: '2rem', maxWidth: '1200px', margin: '0 auto' }}>
      <h2>Complex Reasoning Chain</h2>
      <ReasoningChain reasoningChain={complexChain} />
    </div>
  );
};

// Export all examples
export default {
  CompleteReasoningChainExample,
  SimpleReasoningChainExample,
  AgreementsExample,
  ConflictsExample,
  InformationGapsExample,
  EmptyReasoningChainExample,
  ComplexReasoningChainExample,
};
