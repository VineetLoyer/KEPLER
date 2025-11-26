# Requirements Document

## Introduction

KEPLER (Knowledge Extraction Pipeline for Logical Evidence and Reasoning) is a real-time, multimodal, and interpretable fact-verification system designed to automatically verify factual claims expressed in text or images. The system combines dynamic web retrieval, multi-hop reasoning, and confidence-calibrated verdict generation through a modular pipeline of specialized agents. Each agent is responsible for a specific stage of the reasoning process, enabling traceable and explainable fact-checking from input to verdict.

## Glossary

- **KEPLER**: Knowledge Extraction Pipeline for Logical Evidence and Reasoning - the complete fact-verification system
- **Atomic Claim**: A minimal, self-contained factual statement that can be individually verified
- **Claim Decomposition Model**: An LLM responsible for extracting atomic claims from input text
- **Retriever Agent**: The component that collects relevant multimodal information from the web
- **Reranker Agent**: The component that filters and prioritizes retrieved evidence by relevance, credibility, and recency
- **Aggregator Agent**: The component that synthesizes multimodal evidence by consolidating text, images, and metadata
- **Verifier Agent**: The component that generates verdicts and justifications using multiple LLMs
- **Confidence Scorer**: The component that rates verdict certainty based on source reliability, cross-model agreement, and evidence recency
- **Multimodal Input**: Input consisting of textual statements and/or accompanying images
- **Verdict**: The final classification of a claim as Supported, Refuted, or Not Enough Information
- **Domain Credibility Factor**: A metric derived from historical elements including agreement, citation density, authorship, stability, and link authority

## Requirements

### Requirement 1

**User Story:** As a user, I want to submit multimodal inputs for fact-checking, so that I can verify claims that include both text and images.

#### Acceptance Criteria

1. WHEN a user submits an input THEN the KEPLER system SHALL accept textual statements as claims to be verified
2. WHEN a user submits an input THEN the KEPLER system SHALL accept accompanying images as potential visual evidence
3. WHEN a user submits both text and image THEN the KEPLER system SHALL process the semantic and contextual relationship between the two modalities
4. WHEN a user submits an input THEN the KEPLER system SHALL allow the user to select n LLMs from a predefined pool before processing begins
5. WHEN processing begins THEN the KEPLER system SHALL designate one user-selected LLM as the claim decomposition model

### Requirement 2

**User Story:** As a user, I want complex claims to be decomposed into atomic claims, so that each factual statement can be verified independently and precisely.

#### Acceptance Criteria

1. WHEN the claim decomposition model receives input text THEN the KEPLER system SHALL extract atomic claims from the text
2. WHEN extracting atomic claims THEN the KEPLER system SHALL ensure each atomic claim represents a minimal, self-contained factual statement
3. WHEN extracting atomic claims THEN the KEPLER system SHALL ensure each atomic claim can be individually verified
4. WHEN a compound claim is received THEN the KEPLER system SHALL decompose the claim into granular verification units
5. WHEN atomic claims are extracted THEN the KEPLER system SHALL reduce ambiguity for subsequent verification stages

### Requirement 3

**User Story:** As a user, I want the system to retrieve relevant evidence from the web, so that claims can be verified against current and authoritative information sources.

#### Acceptance Criteria

1. WHEN the Retriever Agent processes an atomic claim THEN the KEPLER system SHALL perform web searches to collect relevant textual information
2. WHEN the Retriever Agent processes visual content THEN the KEPLER system SHALL perform image searches to collect relevant visual evidence
3. WHEN the Retriever Agent processes visual content THEN the KEPLER system SHALL perform reverse image searches to find visually similar content
4. WHEN the Retriever Agent retrieves sources THEN the KEPLER system SHALL scrape and summarize the content before passing it to reasoning stages
5. WHEN the Retriever Agent searches for evidence THEN the KEPLER system SHALL limit searches to materials published before the claim date to ensure temporal consistency
6. WHEN the Retriever Agent searches for evidence THEN the KEPLER system SHALL exclude fact-checking domains to prevent evidence leakage
7. WHEN the Retriever Agent searches for evidence THEN the KEPLER system SHALL exclude restricted domains to prevent evidence leakage

### Requirement 4

**User Story:** As a user, I want retrieved evidence to be ranked by quality and relevance, so that the most credible and pertinent information is prioritized in the verification process.

#### Acceptance Criteria

1. WHEN the Reranker Agent receives retrieved evidence THEN the KEPLER system SHALL filter sources by relevance to the atomic claim
2. WHEN the Reranker Agent receives retrieved evidence THEN the KEPLER system SHALL prioritize sources by credibility level
3. WHEN the Reranker Agent receives retrieved evidence THEN the KEPLER system SHALL prioritize sources by recency
4. WHEN the Reranker Agent evaluates credibility THEN the KEPLER system SHALL rank published papers as most credible
5. WHEN the Reranker Agent evaluates credibility THEN the KEPLER system SHALL rank verified news sources such as Reuters as intermediate credible
6. WHEN the Reranker Agent evaluates credibility THEN the KEPLER system SHALL rank other internet sources such as blogs as least credible
7. WHEN the Reranker Agent calculates domain credibility THEN the KEPLER system SHALL incorporate historical elements including agreement, citation density, authorship, stability, and link authority
8. WHEN the Reranker Agent performs benchmark evaluations THEN the KEPLER system SHALL use a conservative allowlist and neutral priors for unknown domains
9. WHEN the Reranker Agent completes ranking THEN the KEPLER system SHALL pass only the strongest and most pertinent evidence to subsequent stages

### Requirement 5

**User Story:** As a user, I want multimodal evidence to be synthesized coherently, so that I can understand how different pieces of information relate to the claim being verified.

#### Acceptance Criteria

1. WHEN the Aggregator Agent receives ranked evidence THEN the KEPLER system SHALL consolidate textual evidence into a unified representation
2. WHEN the Aggregator Agent receives ranked evidence THEN the KEPLER system SHALL consolidate visual evidence into a unified representation
3. WHEN the Aggregator Agent receives ranked evidence THEN the KEPLER system SHALL consolidate metadata into a unified representation
4. WHEN the Aggregator Agent synthesizes evidence THEN the KEPLER system SHALL apply chain-of-thought reasoning to the consolidated information
5. WHEN the Aggregator Agent synthesizes evidence THEN the KEPLER system SHALL highlight agreements among evidence sources
6. WHEN the Aggregator Agent synthesizes evidence THEN the KEPLER system SHALL highlight conflicts among evidence sources
7. WHEN the Aggregator Agent synthesizes evidence THEN the KEPLER system SHALL highlight missing information relevant to the claim

### Requirement 6

**User Story:** As a user, I want multiple LLMs to independently verify claims, so that the verdict benefits from diverse reasoning approaches and reduces single-model bias.

#### Acceptance Criteria

1. WHEN the Verifier Agent begins verification THEN the KEPLER system SHALL engage all user-selected LLMs independently
2. WHEN the Verifier Agent provides context to LLMs THEN the KEPLER system SHALL supply the atomic claim to each model
3. WHEN the Verifier Agent provides context to LLMs THEN the KEPLER system SHALL supply retrieved textual evidence to each model
4. WHEN the Verifier Agent provides context to LLMs THEN the KEPLER system SHALL supply retrieved visual evidence to each model
5. WHEN the Verifier Agent provides context to LLMs THEN the KEPLER system SHALL supply relevant metadata to each model
6. WHEN the Verifier Agent operates LLMs THEN the KEPLER system SHALL execute models in parallel
7. WHEN each LLM completes verification THEN the KEPLER system SHALL generate an individual verdict classified as Supported, Refuted, or Not Enough Information
8. WHEN each LLM completes verification THEN the KEPLER system SHALL generate an individual justification for the verdict

### Requirement 7

**User Story:** As a user, I want individual model outputs to be aggregated into a consensus verdict, so that I receive a single, reliable answer supported by multiple reasoning perspectives.

#### Acceptance Criteria

1. WHEN the Weighted Multi-Model Output component receives individual verdicts THEN the KEPLER system SHALL aggregate results using a majority poll
2. WHEN individual justifications are textual THEN the KEPLER system SHALL use a lightweight summarization model to aggregate the justifications
3. WHEN aggregating justifications THEN the KEPLER system SHALL produce a concise, human-readable consensus justification
4. WHEN producing consensus justification THEN the KEPLER system SHALL reflect the dominant reasoning across the ensemble of models
5. WHEN the aggregation is complete THEN the KEPLER system SHALL output a final verdict classified as Supported, Refuted, or Not Enough Information

### Requirement 8

**User Story:** As a user, I want to receive a confidence score with the verdict, so that I can assess the reliability and certainty of the fact-checking result.

#### Acceptance Criteria

1. WHEN the Confidence Scorer evaluates the verdict THEN the KEPLER system SHALL consider source reliability in the confidence calculation
2. WHEN the Confidence Scorer evaluates the verdict THEN the KEPLER system SHALL consider cross-model agreement in the confidence calculation
3. WHEN the Confidence Scorer evaluates the verdict THEN the KEPLER system SHALL consider evidence recency in the confidence calculation
4. WHEN the Confidence Scorer completes evaluation THEN the KEPLER system SHALL present a confidence score with the verdict
5. WHEN the Confidence Scorer completes evaluation THEN the KEPLER system SHALL present structured, source-linked justifications with the verdict

### Requirement 9

**User Story:** As a user, I want the fact-checking process to be transparent and traceable, so that I can understand how the system arrived at its verdict and evaluate the reasoning myself.

#### Acceptance Criteria

1. WHEN the KEPLER system processes a claim THEN the system SHALL maintain a traceable record of each pipeline stage from input to verdict
2. WHEN the KEPLER system generates a verdict THEN the system SHALL provide explainable justifications that reference specific evidence sources
3. WHEN the KEPLER system presents results THEN the system SHALL link justifications to the original retrieved sources
4. WHEN the KEPLER system operates THEN the system SHALL enable users to inspect the reasoning process at each modular agent stage
