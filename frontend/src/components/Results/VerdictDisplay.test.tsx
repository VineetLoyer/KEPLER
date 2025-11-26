import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { VerdictDisplay } from './VerdictDisplay';
import type { ConsensusVerdict, ConfidenceScore } from '../../types/verification';

/**
 * Unit Tests for VerdictDisplay Component
 * 
 * These tests verify specific examples and edge cases for the VerdictDisplay component.
 */

describe('VerdictDisplay Unit Tests', () => {
  const mockConfidenceScore: ConfidenceScore = {
    overall_score: 0.85,
    source_reliability: 0.90,
    model_agreement: 0.80,
    evidence_recency: 0.85,
    structured_justification: {
      summary: 'Test summary',
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

  it('should render Supported verdict with green styling', () => {
    const verdict: ConsensusVerdict = {
      final_classification: 'Supported',
      consensus_justification: 'The claim is supported by multiple reliable sources.',
      individual_verdicts: [],
      agreement_level: 0.9,
    };

    const { container } = render(
      <VerdictDisplay verdict={verdict} confidenceScore={mockConfidenceScore} />
    );

    const badge = screen.getByText('Supported');
    expect(badge).toBeInTheDocument();

    const badgeContainer = container.querySelector('.verdict-badge');
    expect(badgeContainer).toHaveClass('verdict-supported');
  });

  it('should render Refuted verdict with red styling', () => {
    const verdict: ConsensusVerdict = {
      final_classification: 'Refuted',
      consensus_justification: 'The claim is contradicted by evidence.',
      individual_verdicts: [],
      agreement_level: 0.85,
    };

    const { container } = render(
      <VerdictDisplay verdict={verdict} confidenceScore={mockConfidenceScore} />
    );

    const badge = screen.getByText('Refuted');
    expect(badge).toBeInTheDocument();

    const badgeContainer = container.querySelector('.verdict-badge');
    expect(badgeContainer).toHaveClass('verdict-refuted');
  });

  it('should render Not Enough Information verdict with yellow styling', () => {
    const verdict: ConsensusVerdict = {
      final_classification: 'Not Enough Information',
      consensus_justification: 'Insufficient evidence to verify the claim.',
      individual_verdicts: [],
      agreement_level: 0.7,
    };

    const { container } = render(
      <VerdictDisplay verdict={verdict} confidenceScore={mockConfidenceScore} />
    );

    const badge = screen.getByText('Not Enough Information');
    expect(badge).toBeInTheDocument();

    const badgeContainer = container.querySelector('.verdict-badge');
    expect(badgeContainer).toHaveClass('verdict-nei');
  });

  it('should display confidence score as percentage', () => {
    const verdict: ConsensusVerdict = {
      final_classification: 'Supported',
      consensus_justification: 'Test justification',
      individual_verdicts: [],
      agreement_level: 0.9,
    };

    const { container } = render(
      <VerdictDisplay verdict={verdict} confidenceScore={mockConfidenceScore} />
    );

    // Check for 85.0% (overall_score = 0.85)
    const largePercentage = container.querySelector('.verdict-confidence-percentage-large');
    expect(largePercentage?.textContent).toBe('85.0%');
  });

  it('should display all confidence factors', () => {
    const verdict: ConsensusVerdict = {
      final_classification: 'Supported',
      consensus_justification: 'Test justification',
      individual_verdicts: [],
      agreement_level: 0.9,
    };

    render(<VerdictDisplay verdict={verdict} confidenceScore={mockConfidenceScore} />);

    expect(screen.getByText(/Source Reliability/i)).toBeInTheDocument();
    expect(screen.getByText(/Model Agreement/i)).toBeInTheDocument();
    expect(screen.getByText(/Evidence Recency/i)).toBeInTheDocument();
  });

  it('should display justification text', () => {
    const justificationText = 'This is a detailed justification for the verdict.';
    const verdict: ConsensusVerdict = {
      final_classification: 'Supported',
      consensus_justification: justificationText,
      individual_verdicts: [],
      agreement_level: 0.9,
    };

    render(<VerdictDisplay verdict={verdict} confidenceScore={mockConfidenceScore} />);

    expect(screen.getByText(justificationText)).toBeInTheDocument();
  });

  it('should render confidence bars with correct values', () => {
    const verdict: ConsensusVerdict = {
      final_classification: 'Supported',
      consensus_justification: 'Test justification',
      individual_verdicts: [],
      agreement_level: 0.9,
    };

    const { container } = render(
      <VerdictDisplay verdict={verdict} confidenceScore={mockConfidenceScore} />
    );

    const progressBars = container.querySelectorAll('[role="progressbar"]');
    expect(progressBars.length).toBeGreaterThan(0);

    // Check that progress bars have correct aria attributes
    progressBars.forEach((bar) => {
      expect(bar).toHaveAttribute('aria-valuenow');
      expect(bar).toHaveAttribute('aria-valuemin', '0');
      expect(bar).toHaveAttribute('aria-valuemax', '100');
    });
  });

  it('should handle edge case: 0% confidence', () => {
    const verdict: ConsensusVerdict = {
      final_classification: 'Not Enough Information',
      consensus_justification: 'No confidence in this verdict.',
      individual_verdicts: [],
      agreement_level: 0,
    };

    const lowConfidence: ConfidenceScore = {
      overall_score: 0,
      source_reliability: 0,
      model_agreement: 0,
      evidence_recency: 0,
      structured_justification: mockConfidenceScore.structured_justification,
    };

    const { container } = render(
      <VerdictDisplay verdict={verdict} confidenceScore={lowConfidence} />
    );

    const largePercentage = container.querySelector('.verdict-confidence-percentage-large');
    expect(largePercentage?.textContent).toBe('0.0%');
  });

  it('should handle edge case: 100% confidence', () => {
    const verdict: ConsensusVerdict = {
      final_classification: 'Supported',
      consensus_justification: 'Maximum confidence in this verdict.',
      individual_verdicts: [],
      agreement_level: 1,
    };

    const highConfidence: ConfidenceScore = {
      overall_score: 1,
      source_reliability: 1,
      model_agreement: 1,
      evidence_recency: 1,
      structured_justification: mockConfidenceScore.structured_justification,
    };

    const { container } = render(
      <VerdictDisplay verdict={verdict} confidenceScore={highConfidence} />
    );

    const largePercentage = container.querySelector('.verdict-confidence-percentage-large');
    expect(largePercentage?.textContent).toBe('100.0%');
  });

  it('should have proper accessibility attributes', () => {
    const verdict: ConsensusVerdict = {
      final_classification: 'Supported',
      consensus_justification: 'Test justification',
      individual_verdicts: [],
      agreement_level: 0.9,
    };

    render(<VerdictDisplay verdict={verdict} confidenceScore={mockConfidenceScore} />);

    const region = screen.getByRole('region', { name: /verification verdict/i });
    expect(region).toBeInTheDocument();
  });

  it('should render all required sections', () => {
    const verdict: ConsensusVerdict = {
      final_classification: 'Supported',
      consensus_justification: 'Test justification',
      individual_verdicts: [],
      agreement_level: 0.9,
    };

    const { container } = render(
      <VerdictDisplay verdict={verdict} confidenceScore={mockConfidenceScore} />
    );

    // Check for all main sections
    expect(container.querySelector('.verdict-badge')).toBeInTheDocument();
    expect(container.querySelector('.verdict-confidence-section')).toBeInTheDocument();
    expect(container.querySelector('.verdict-justification-section')).toBeInTheDocument();
    expect(container.querySelector('.verdict-breakdown-section')).toBeInTheDocument();
  });
});
