/**
 * EvidencePanel Component Example
 * 
 * This file demonstrates how to use the EvidencePanel component
 * with sample data.
 */

import React from 'react';
import { EvidencePanel } from './EvidencePanel';
import type { EvidencePiece } from '../../types/verification';

// Example evidence data
const exampleEvidence: EvidencePiece[] = [
  {
    id: 'ev-001',
    source: {
      url: 'https://www.nature.com/articles/example-article',
      title: 'Climate Change Impact on Global Temperatures',
      domain: 'nature.com',
      content_type: 'research',
      publish_date: '2024-01-15T10:00:00Z',
    },
    summary:
      'A comprehensive study analyzing temperature data from the past 50 years shows a consistent upward trend in global average temperatures, with the most significant increases observed in polar regions.',
    raw_content: 'Full article content...',
    credibility_score: 0.95,
    relevance_score: 0.92,
    recency_score: 0.88,
    final_rank_score: 0.92,
  },
  {
    id: 'ev-002',
    source: {
      url: 'https://www.sciencedaily.com/releases/2024/climate-study',
      title: 'New Research Confirms Accelerating Warming Trends',
      domain: 'sciencedaily.com',
      content_type: 'news',
      publish_date: '2024-02-20T14:30:00Z',
    },
    summary:
      'Recent satellite data confirms that global warming is accelerating faster than previously predicted, with ocean temperatures reaching record highs in 2023.',
    raw_content: 'Full article content...',
    credibility_score: 0.88,
    relevance_score: 0.90,
    recency_score: 0.95,
    final_rank_score: 0.91,
  },
  {
    id: 'ev-003',
    source: {
      url: 'https://climate.nasa.gov/evidence/',
      title: 'Evidence | Facts – Climate Change: Vital Signs of the Planet',
      domain: 'nasa.gov',
      content_type: 'article',
      publish_date: '2023-12-10T09:00:00Z',
    },
    summary:
      'NASA provides comprehensive evidence of climate change including rising temperatures, shrinking ice sheets, and rising sea levels based on decades of scientific observations.',
    raw_content: 'Full article content...',
    credibility_score: 0.98,
    relevance_score: 0.94,
    recency_score: 0.85,
    final_rank_score: 0.93,
  },
  {
    id: 'ev-004',
    source: {
      url: 'https://www.ipcc.ch/report/ar6/wg1/',
      title: 'IPCC Sixth Assessment Report: The Physical Science Basis',
      domain: 'ipcc.ch',
      content_type: 'research',
      publish_date: '2023-08-09T00:00:00Z',
    },
    summary:
      'The IPCC report provides unequivocal evidence that human influence has warmed the atmosphere, ocean, and land, with widespread and rapid changes occurring across the climate system.',
    raw_content: 'Full report content...',
    credibility_score: 0.99,
    relevance_score: 0.96,
    recency_score: 0.82,
    final_rank_score: 0.94,
  },
];

// Example with empty evidence
const emptyEvidence: EvidencePiece[] = [];

// Example with minimal evidence (missing optional fields)
const minimalEvidence: EvidencePiece[] = [
  {
    id: 'ev-min-001',
    source: {
      url: 'https://example.com/article',
      title: 'Example Article',
      domain: 'example.com',
      content_type: 'article',
    },
    summary: 'This is a minimal example with only required fields.',
    raw_content: 'Content...',
  },
];

/**
 * Example: Standard usage with multiple evidence pieces
 */
export const StandardExample: React.FC = () => {
  return (
    <div style={{ maxWidth: '800px', margin: '0 auto', padding: '20px' }}>
      <h2>Standard Evidence Panel</h2>
      <EvidencePanel evidence={exampleEvidence} />
    </div>
  );
};

/**
 * Example: Empty evidence list
 */
export const EmptyExample: React.FC = () => {
  return (
    <div style={{ maxWidth: '800px', margin: '0 auto', padding: '20px' }}>
      <h2>Empty Evidence Panel</h2>
      <EvidencePanel evidence={emptyEvidence} />
    </div>
  );
};

/**
 * Example: Minimal evidence (missing optional fields)
 */
export const MinimalExample: React.FC = () => {
  return (
    <div style={{ maxWidth: '800px', margin: '0 auto', padding: '20px' }}>
      <h2>Minimal Evidence Panel</h2>
      <EvidencePanel evidence={minimalEvidence} />
    </div>
  );
};

/**
 * Example: Single evidence piece
 */
export const SingleExample: React.FC = () => {
  return (
    <div style={{ maxWidth: '800px', margin: '0 auto', padding: '20px' }}>
      <h2>Single Evidence Piece</h2>
      <EvidencePanel evidence={[exampleEvidence[0]]} />
    </div>
  );
};

/**
 * Example: Evidence with varying credibility scores
 */
export const VaryingScoresExample: React.FC = () => {
  const varyingScores: EvidencePiece[] = [
    {
      ...exampleEvidence[0],
      credibility_score: 0.99,
    },
    {
      ...exampleEvidence[1],
      credibility_score: 0.75,
    },
    {
      ...exampleEvidence[2],
      credibility_score: 0.50,
    },
    {
      ...exampleEvidence[3],
      credibility_score: 0.25,
    },
  ];

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto', padding: '20px' }}>
      <h2>Evidence with Varying Credibility Scores</h2>
      <EvidencePanel evidence={varyingScores} />
    </div>
  );
};

// Default export for easy importing
export default StandardExample;
