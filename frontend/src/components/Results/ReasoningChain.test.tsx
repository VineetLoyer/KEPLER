import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ReasoningChain } from './ReasoningChain';
import type { ReasoningChain as ReasoningChainType } from '../../types/verification';

/**
 * Unit Tests for ReasoningChain Component
 * 
 * These tests verify specific examples and edge cases for the ReasoningChain component.
 */

describe('ReasoningChain Component', () => {
  const mockReasoningChain: ReasoningChainType = {
    steps: [
      {
        step_number: 1,
        description: 'Analyze the claim for factual assertions',
        evidence_used: ['evidence-1', 'evidence-2'],
        conclusion: 'The claim contains verifiable facts',
      },
      {
        step_number: 2,
        description: 'Compare evidence sources',
        evidence_used: ['evidence-1', 'evidence-3'],
        conclusion: 'Sources generally agree on key points',
      },
    ],
    agreements: [
      {
        evidence_ids: ['evidence-1', 'evidence-2'],
        common_assertion: 'The event occurred on January 15, 2024',
        strength: 0.85,
      },
    ],
    conflicts: [
      {
        evidence_ids: ['evidence-2', 'evidence-3'],
        conflicting_assertions: [
          'The number was 100',
          'The number was 150',
        ],
        severity: 0.6,
      },
    ],
    gaps: [
      {
        missing_aspect: 'Exact time of the event',
        importance: 0.4,
      },
    ],
  };

  it('should render reasoning chain title', () => {
    render(<ReasoningChain reasoningChain={mockReasoningChain} />);
    
    const title = screen.getByText(/reasoning process/i);
    expect(title).toBeInTheDocument();
  });

  it('should render all reasoning steps', () => {
    const { container } = render(<ReasoningChain reasoningChain={mockReasoningChain} />);
    
    const steps = container.querySelectorAll('.reasoning-step');
    expect(steps.length).toBe(2);
  });

  it('should display step numbers', () => {
    render(<ReasoningChain reasoningChain={mockReasoningChain} />);
    
    expect(screen.getByText('Step 1')).toBeInTheDocument();
    expect(screen.getByText('Step 2')).toBeInTheDocument();
  });

  it('should display step descriptions', () => {
    render(<ReasoningChain reasoningChain={mockReasoningChain} />);
    
    expect(screen.getByText('Analyze the claim for factual assertions')).toBeInTheDocument();
    expect(screen.getByText('Compare evidence sources')).toBeInTheDocument();
  });

  it('should display step conclusions', () => {
    render(<ReasoningChain reasoningChain={mockReasoningChain} />);
    
    expect(screen.getByText(/The claim contains verifiable facts/)).toBeInTheDocument();
    expect(screen.getByText(/Sources generally agree on key points/)).toBeInTheDocument();
  });

  it('should display evidence used in steps', () => {
    render(<ReasoningChain reasoningChain={mockReasoningChain} />);
    
    // evidence-1 appears in both steps, so use getAllByText
    const evidence1Elements = screen.getAllByText('evidence-1');
    expect(evidence1Elements.length).toBeGreaterThan(0);
    
    expect(screen.getByText('evidence-2')).toBeInTheDocument();
    expect(screen.getByText('evidence-3')).toBeInTheDocument();
  });

  it('should render agreements section when agreements exist', () => {
    render(<ReasoningChain reasoningChain={mockReasoningChain} />);
    
    const agreementsTitle = screen.getByText(/agreements in evidence/i);
    expect(agreementsTitle).toBeInTheDocument();
  });

  it('should display agreement assertions', () => {
    render(<ReasoningChain reasoningChain={mockReasoningChain} />);
    
    expect(screen.getByText('The event occurred on January 15, 2024')).toBeInTheDocument();
  });

  it('should display agreement strength as percentage', () => {
    render(<ReasoningChain reasoningChain={mockReasoningChain} />);
    
    expect(screen.getByText(/Strength: 85%/)).toBeInTheDocument();
  });

  it('should render conflicts section when conflicts exist', () => {
    render(<ReasoningChain reasoningChain={mockReasoningChain} />);
    
    const conflictsTitle = screen.getByText(/conflicts in evidence/i);
    expect(conflictsTitle).toBeInTheDocument();
  });

  it('should display conflicting assertions', () => {
    render(<ReasoningChain reasoningChain={mockReasoningChain} />);
    
    expect(screen.getByText('The number was 100')).toBeInTheDocument();
    expect(screen.getByText('The number was 150')).toBeInTheDocument();
  });

  it('should display conflict severity as percentage', () => {
    render(<ReasoningChain reasoningChain={mockReasoningChain} />);
    
    expect(screen.getByText(/Severity: 60%/)).toBeInTheDocument();
  });

  it('should render information gaps section when gaps exist', () => {
    render(<ReasoningChain reasoningChain={mockReasoningChain} />);
    
    const gapsTitle = screen.getByText(/information gaps/i);
    expect(gapsTitle).toBeInTheDocument();
  });

  it('should display missing aspects', () => {
    render(<ReasoningChain reasoningChain={mockReasoningChain} />);
    
    expect(screen.getByText('Exact time of the event')).toBeInTheDocument();
  });

  it('should display gap importance as percentage', () => {
    render(<ReasoningChain reasoningChain={mockReasoningChain} />);
    
    expect(screen.getByText(/Importance: 40%/)).toBeInTheDocument();
  });

  it('should handle empty agreements array', () => {
    const chainWithoutAgreements: ReasoningChainType = {
      ...mockReasoningChain,
      agreements: [],
    };
    
    render(<ReasoningChain reasoningChain={chainWithoutAgreements} />);
    
    const agreementsSection = document.querySelector('.agreements-section');
    expect(agreementsSection).not.toBeInTheDocument();
  });

  it('should handle empty conflicts array', () => {
    const chainWithoutConflicts: ReasoningChainType = {
      ...mockReasoningChain,
      conflicts: [],
    };
    
    render(<ReasoningChain reasoningChain={chainWithoutConflicts} />);
    
    const conflictsSection = document.querySelector('.conflicts-section');
    expect(conflictsSection).not.toBeInTheDocument();
  });

  it('should handle empty gaps array', () => {
    const chainWithoutGaps: ReasoningChainType = {
      ...mockReasoningChain,
      gaps: [],
    };
    
    render(<ReasoningChain reasoningChain={chainWithoutGaps} />);
    
    const gapsSection = document.querySelector('.gaps-section');
    expect(gapsSection).not.toBeInTheDocument();
  });

  it('should handle steps without evidence', () => {
    const chainWithNoEvidence: ReasoningChainType = {
      steps: [
        {
          step_number: 1,
          description: 'Initial analysis',
          evidence_used: [],
          conclusion: 'No evidence needed for this step',
        },
      ],
      agreements: [],
      conflicts: [],
      gaps: [],
    };
    
    const { container } = render(<ReasoningChain reasoningChain={chainWithNoEvidence} />);
    
    const evidenceSection = container.querySelector('.step-evidence');
    expect(evidenceSection).not.toBeInTheDocument();
  });

  it('should display empty message for null reasoning chain', () => {
    render(<ReasoningChain reasoningChain={null as any} />);
    
    const emptyMessage = screen.getByText(/no reasoning chain available/i);
    expect(emptyMessage).toBeInTheDocument();
  });

  it('should have proper accessibility attributes', () => {
    render(<ReasoningChain reasoningChain={mockReasoningChain} />);
    
    // Should have region role
    const region = screen.getByRole('region', { name: /reasoning process/i });
    expect(region).toBeInTheDocument();
    
    // Should have main heading
    const mainHeading = screen.getByRole('heading', { name: /reasoning process/i });
    expect(mainHeading).toBeInTheDocument();
  });

  it('should apply distinct CSS classes for agreements and conflicts', () => {
    const { container } = render(<ReasoningChain reasoningChain={mockReasoningChain} />);
    
    const agreementsSection = container.querySelector('.agreements-section');
    const conflictsSection = container.querySelector('.conflicts-section');
    
    expect(agreementsSection).toHaveClass('agreements-section');
    expect(conflictsSection).toHaveClass('conflicts-section');
    
    // Classes should be different
    expect(agreementsSection?.className).not.toBe(conflictsSection?.className);
  });
});
