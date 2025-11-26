/**
 * AtomicClaims Component Example
 * 
 * This file demonstrates the usage of the AtomicClaims component
 * with various scenarios.
 */

import React from 'react';
import { AtomicClaims } from './AtomicClaims';
import { AtomicClaim, VerificationResult } from '../../types/verification';

// Example 1: Single atomic claim
const singleClaimExample: AtomicClaim[] = [
  {
    id: 'claim-001',
    text: 'The Earth orbits the Sun.',
    is_atomic: true,
    verification_status: 'Supported',
  },
];

// Example 2: Multiple atomic claims (compound claim breakdown)
const compoundClaimExample: AtomicClaim[] = [
  {
    id: 'claim-001',
    text: 'The Earth orbits the Sun.',
    is_atomic: true,
    parent_claim: 'compound-claim-solar-system',
    verification_status: 'Supported',
  },
  {
    id: 'claim-002',
    text: 'The Moon orbits the Earth.',
    is_atomic: true,
    parent_claim: 'compound-claim-solar-system',
    verification_status: 'Supported',
  },
  {
    id: 'claim-003',
    text: 'Mars has two moons named Phobos and Deimos.',
    is_atomic: true,
    parent_claim: 'compound-claim-solar-system',
    verification_status: 'Supported',
  },
];

// Example 3: Claims with mixed verdicts
const mixedVerdictsExample: AtomicClaim[] = [
  {
    id: 'claim-001',
    text: 'Water boils at 100 degrees Celsius at sea level.',
    is_atomic: true,
    parent_claim: 'compound-claim-water',
    verification_status: 'Supported',
  },
  {
    id: 'claim-002',
    text: 'Water freezes at 0 degrees Celsius.',
    is_atomic: true,
    parent_claim: 'compound-claim-water',
    verification_status: 'Supported',
  },
  {
    id: 'claim-003',
    text: 'Water is heavier than ice.',
    is_atomic: true,
    parent_claim: 'compound-claim-water',
    verification_status: 'Refuted',
  },
];

// Example 4: Claims with pending status
const pendingClaimsExample: AtomicClaim[] = [
  {
    id: 'claim-001',
    text: 'The claim is being verified.',
    is_atomic: true,
  },
  {
    id: 'claim-002',
    text: 'Another claim pending verification.',
    is_atomic: true,
  },
];

// Example 5: Claims with Not Enough Information status
const neiClaimsExample: AtomicClaim[] = [
  {
    id: 'claim-001',
    text: 'A specific event happened on a specific date.',
    is_atomic: true,
    verification_status: 'Not Enough Information',
  },
];

// Mock verification result for examples with full details
const mockVerificationResult: VerificationResult = {
  session_id: 'session-example-123',
  original_input: {
    text: 'The Earth orbits the Sun and the Moon orbits the Earth.',
  },
  atomic_claims: compoundClaimExample,
  consensus_verdict: {
    final_classification: 'Supported',
    consensus_justification:
      'All atomic claims are supported by scientific evidence and consensus.',
    individual_verdicts: [
      {
        model_id: 'gpt-4',
        classification: 'Supported',
        justification: 'Well-established astronomical facts.',
        confidence: 0.98,
        evidence_references: ['evidence-1', 'evidence-2'],
      },
      {
        model_id: 'claude-3',
        classification: 'Supported',
        justification: 'Confirmed by multiple reliable sources.',
        confidence: 0.96,
        evidence_references: ['evidence-1', 'evidence-3'],
      },
    ],
    agreement_level: 1.0,
  },
  confidence_score: {
    overall_score: 0.97,
    source_reliability: 0.98,
    model_agreement: 1.0,
    evidence_recency: 0.95,
    structured_justification: {
      summary: 'High confidence based on scientific consensus.',
      key_evidence: [],
      reasoning_chain: {
        steps: [],
        agreements: [],
        conflicts: [],
        gaps: [],
      },
      source_links: [],
    },
  },
  processing_metadata: {},
  trace_log: [],
};

// Example components for demonstration
export const SingleClaimExample: React.FC = () => (
  <div style={{ padding: '20px', maxWidth: '800px' }}>
    <h2>Example 1: Single Atomic Claim</h2>
    <AtomicClaims
      atomicClaims={singleClaimExample}
      verificationResult={mockVerificationResult}
    />
  </div>
);

export const CompoundClaimExample: React.FC = () => (
  <div style={{ padding: '20px', maxWidth: '800px' }}>
    <h2>Example 2: Compound Claim Breakdown</h2>
    <AtomicClaims
      atomicClaims={compoundClaimExample}
      verificationResult={mockVerificationResult}
    />
  </div>
);

export const MixedVerdictsExample: React.FC = () => (
  <div style={{ padding: '20px', maxWidth: '800px' }}>
    <h2>Example 3: Mixed Verdicts</h2>
    <AtomicClaims
      atomicClaims={mixedVerdictsExample}
      verificationResult={{
        ...mockVerificationResult,
        atomic_claims: mixedVerdictsExample,
        consensus_verdict: {
          ...mockVerificationResult.consensus_verdict,
          final_classification: 'Refuted',
          consensus_justification: 'One of the claims is refuted by evidence.',
        },
      }}
    />
  </div>
);

export const PendingClaimsExample: React.FC = () => (
  <div style={{ padding: '20px', maxWidth: '800px' }}>
    <h2>Example 4: Pending Claims</h2>
    <AtomicClaims atomicClaims={pendingClaimsExample} />
  </div>
);

export const NEIClaimsExample: React.FC = () => (
  <div style={{ padding: '20px', maxWidth: '800px' }}>
    <h2>Example 5: Not Enough Information</h2>
    <AtomicClaims
      atomicClaims={neiClaimsExample}
      verificationResult={{
        ...mockVerificationResult,
        atomic_claims: neiClaimsExample,
        consensus_verdict: {
          ...mockVerificationResult.consensus_verdict,
          final_classification: 'Not Enough Information',
          consensus_justification: 'Insufficient evidence to verify this claim.',
        },
      }}
    />
  </div>
);

// Combined example showing all scenarios
export const AllExamples: React.FC = () => (
  <div style={{ padding: '20px' }}>
    <h1>AtomicClaims Component Examples</h1>
    <SingleClaimExample />
    <hr style={{ margin: '40px 0' }} />
    <CompoundClaimExample />
    <hr style={{ margin: '40px 0' }} />
    <MixedVerdictsExample />
    <hr style={{ margin: '40px 0' }} />
    <PendingClaimsExample />
    <hr style={{ margin: '40px 0' }} />
    <NEIClaimsExample />
  </div>
);

export default AllExamples;
