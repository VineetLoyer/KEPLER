/**
 * ModelVerdicts Component Unit Tests
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ModelVerdicts } from './ModelVerdicts';
import { ConsensusVerdict } from '../../types/verification';

describe('ModelVerdicts Component', () => {
  const mockConsensusVerdictWithAgreement: ConsensusVerdict = {
    final_classification: 'Supported',
    consensus_justification: 'All models agree this claim is supported.',
    agreement_level: 1.0,
    individual_verdicts: [
      {
        model_id: 'gpt-4',
        classification: 'Supported',
        justification: 'The evidence strongly supports this claim.',
        confidence: 0.95,
        evidence_references: ['evidence-1', 'evidence-2'],
      },
      {
        model_id: 'claude-3',
        classification: 'Supported',
        justification: 'Multiple reliable sources confirm this claim.',
        confidence: 0.92,
        evidence_references: ['evidence-1', 'evidence-3'],
      },
    ],
  };

  const mockConsensusVerdictWithDisagreement: ConsensusVerdict = {
    final_classification: 'Supported',
    consensus_justification: 'Majority of models support this claim.',
    agreement_level: 0.67,
    individual_verdicts: [
      {
        model_id: 'gpt-4',
        classification: 'Supported',
        justification: 'The evidence strongly supports this claim.',
        confidence: 0.95,
        evidence_references: ['evidence-1', 'evidence-2'],
      },
      {
        model_id: 'claude-3',
        classification: 'Supported',
        justification: 'Multiple reliable sources confirm this claim.',
        confidence: 0.92,
        evidence_references: ['evidence-1', 'evidence-3'],
      },
      {
        model_id: 'gemini-pro',
        classification: 'Refuted',
        justification: 'Some sources contradict this claim.',
        confidence: 0.78,
        evidence_references: ['evidence-4'],
      },
    ],
  };

  it('renders the component with title', () => {
    render(<ModelVerdicts consensusVerdict={mockConsensusVerdictWithAgreement} />);
    expect(screen.getByText('Individual Model Verdicts')).toBeInTheDocument();
  });

  it('displays all individual model verdicts', () => {
    render(<ModelVerdicts consensusVerdict={mockConsensusVerdictWithAgreement} />);
    expect(screen.getByText('gpt-4')).toBeInTheDocument();
    expect(screen.getByText('claude-3')).toBeInTheDocument();
  });

  it('shows model classification for each verdict', () => {
    render(<ModelVerdicts consensusVerdict={mockConsensusVerdictWithAgreement} />);
    const supportedBadges = screen.getAllByText('Supported');
    expect(supportedBadges.length).toBeGreaterThanOrEqual(2);
  });

  it('displays justification for each model', () => {
    render(<ModelVerdicts consensusVerdict={mockConsensusVerdictWithAgreement} />);
    expect(screen.getByText('The evidence strongly supports this claim.')).toBeInTheDocument();
    expect(screen.getByText('Multiple reliable sources confirm this claim.')).toBeInTheDocument();
  });

  it('shows confidence scores for each model', () => {
    render(<ModelVerdicts consensusVerdict={mockConsensusVerdictWithAgreement} />);
    // ConfidenceBar components should be rendered
    const confidenceLabels = screen.getAllByText('Confidence');
    expect(confidenceLabels.length).toBe(2);
  });

  it('displays disagreement badge when models disagree', () => {
    render(<ModelVerdicts consensusVerdict={mockConsensusVerdictWithDisagreement} />);
    expect(screen.getByText('Disagreements Detected')).toBeInTheDocument();
  });

  it('does not display disagreement badge when all models agree', () => {
    render(<ModelVerdicts consensusVerdict={mockConsensusVerdictWithAgreement} />);
    expect(screen.queryByText('Disagreements Detected')).not.toBeInTheDocument();
  });

  it('highlights disagreeing models', () => {
    const { container } = render(
      <ModelVerdicts consensusVerdict={mockConsensusVerdictWithDisagreement} />
    );
    const disagreeingCards = container.querySelectorAll('.model-verdict-disagreeing');
    expect(disagreeingCards.length).toBe(1);
  });

  it('shows disagreement indicator on disagreeing model cards', () => {
    render(<ModelVerdicts consensusVerdict={mockConsensusVerdictWithDisagreement} />);
    expect(screen.getByText('Disagrees with consensus')).toBeInTheDocument();
  });

  it('displays agreement level', () => {
    render(<ModelVerdicts consensusVerdict={mockConsensusVerdictWithAgreement} />);
    expect(screen.getByText('Agreement Level:')).toBeInTheDocument();
    expect(screen.getByText('100%')).toBeInTheDocument();
  });

  it('displays evidence references when available', () => {
    render(<ModelVerdicts consensusVerdict={mockConsensusVerdictWithAgreement} />);
    expect(screen.getAllByText('evidence-1').length).toBeGreaterThan(0);
    expect(screen.getByText('evidence-2')).toBeInTheDocument();
  });

  it('applies correct verdict color classes', () => {
    const { container } = render(
      <ModelVerdicts consensusVerdict={mockConsensusVerdictWithDisagreement} />
    );
    const supportedBadges = container.querySelectorAll('.verdict-supported');
    const refutedBadges = container.querySelectorAll('.verdict-refuted');
    expect(supportedBadges.length).toBeGreaterThan(0);
    expect(refutedBadges.length).toBeGreaterThan(0);
  });

  it('renders with proper ARIA labels', () => {
    render(<ModelVerdicts consensusVerdict={mockConsensusVerdictWithAgreement} />);
    expect(screen.getByRole('region', { name: 'Individual model verdicts' })).toBeInTheDocument();
  });
});
