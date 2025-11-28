/**
 * Type definitions for verification data structures
 * 
 * These types match the Python data models from the backend.
 */

export type VerdictType = 'Supported' | 'Refuted' | 'Not Enough Information';

export interface Verdict {
  model_id: string;
  classification: VerdictType;
  justification: string;
  confidence: number;
  evidence_references: string[];
}

export interface ConsensusVerdict {
  final_classification: VerdictType;
  consensus_justification: string;
  individual_verdicts: Verdict[];
  agreement_level: number;
}

export interface Source {
  url: string;
  title: string;
  publish_date?: string;
  domain: string;
  content_type: string;
}

export interface EvidencePiece {
  id: string;
  source: Source;
  summary: string;
  raw_content: string;
  relevance_score?: number;
  credibility_score?: number;
  recency_score?: number;
  final_rank_score?: number;
}

export interface ReasoningStep {
  step_number: number;
  description: string;
  evidence_used: string[];
  conclusion: string;
}

export interface Agreement {
  evidence_ids: string[];
  common_assertion: string;
  strength: number;
}

export interface Conflict {
  evidence_ids: string[];
  conflicting_assertions: string[];
  severity: number;
}

export interface InformationGap {
  missing_aspect: string;
  importance: number;
}

export interface ReasoningChain {
  steps: ReasoningStep[];
  agreements: Agreement[];
  conflicts: Conflict[];
  gaps: InformationGap[];
}

export interface StructuredJustification {
  summary: string;
  key_evidence: EvidencePiece[];
  reasoning_chain: ReasoningChain;
  source_links: string[];
}

export interface ConfidenceScore {
  overall_score: number;
  source_reliability: number;
  model_agreement: number;
  evidence_recency: number;
  structured_justification: StructuredJustification;
}

export interface AtomicClaim {
  id: string;
  text: string;
  is_atomic: boolean;
  parent_claim?: string;
  verification_status?: VerdictType;
  confidence_score?: ConfidenceScore;
  consensus_verdict?: ConsensusVerdict;
}

export interface VerificationResult {
  session_id: string;
  original_input: unknown;
  atomic_claims: AtomicClaim[];
  consensus_verdict: ConsensusVerdict;
  confidence_score: ConfidenceScore;
  processing_metadata: unknown;
  trace_log: unknown[];
}
