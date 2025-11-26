/**
 * AtomicClaims Component Unit Tests
 */

import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { AtomicClaims } from './AtomicClaims';
import { AtomicClaim, VerificationResult } from '../../types/verification';

describe('AtomicClaims Component', () => {
  const mockSingleAtomicClaim: AtomicClaim[] = [
    {
      id: 'claim-1',
      text: 'The Earth orbits the Sun.',
      is_atomic: true,
      verification_status: 'Supported',
    },
  ];

  const mockMultipleAtomicClaims: AtomicClaim[] = [
    {
      id: 'claim-1',
      text: 'The Earth orbits the Sun.',
      is_atomic: true,
      parent_claim: 'compound-claim-1',
      verification_status: 'Supported',
    },
    {
      id: 'claim-2',
      text: 'The Moon orbits the Earth.',
      is_atomic: true,
      parent_claim: 'compound-claim-1',
      verification_status: 'Supported',
    },
    {
      id: 'claim-3',
      text: 'Mars has two moons.',
      is_atomic: true,
      parent_claim: 'compound-claim-1',
      verification_status: 'Refuted',
    },
  ];

  const mockVerificationResult: VerificationResult = {
    session_id: 'session-123',
    original_input: {},
    atomic_claims: mockMultipleAtomicClaims,
    consensus_verdict: {
      final_classification: 'Supported',
      consensus_justification: 'Most claims are supported by evidence.',
      individual_verdicts: [],
      agreement_level: 0.8,
    },
    confidence_score: {
      overall_score: 0.85,
      source_reliability: 0.9,
      model_agreement: 0.8,
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
    },
    processing_metadata: {},
    trace_log: [],
  };

  it('renders nothing when no atomic claims are provided', () => {
    const { container } = render(<AtomicClaims atomicClaims={[]} />);
    expect(container.firstChild).toBeNull();
  });

  it('renders the component with title for single claim', () => {
    render(<AtomicClaims atomicClaims={mockSingleAtomicClaim} />);
    expect(screen.getByText('Claim Analysis')).toBeInTheDocument();
  });

  it('renders the component with title for compound claims', () => {
    render(<AtomicClaims atomicClaims={mockMultipleAtomicClaims} />);
    expect(screen.getByText('Claim Breakdown')).toBeInTheDocument();
  });

  it('displays all atomic claims', () => {
    render(<AtomicClaims atomicClaims={mockMultipleAtomicClaims} />);
    expect(screen.getByText('The Earth orbits the Sun.')).toBeInTheDocument();
    expect(screen.getByText('The Moon orbits the Earth.')).toBeInTheDocument();
    expect(screen.getByText('Mars has two moons.')).toBeInTheDocument();
  });

  it('shows verification status for each claim', () => {
    render(<AtomicClaims atomicClaims={mockMultipleAtomicClaims} />);
    const supportedBadges = screen.getAllByText('Supported');
    expect(supportedBadges.length).toBeGreaterThanOrEqual(2);
    expect(screen.getByText('Refuted')).toBeInTheDocument();
  });

  it('displays overall verdict for compound claims', () => {
    render(
      <AtomicClaims
        atomicClaims={mockMultipleAtomicClaims}
        verificationResult={mockVerificationResult}
      />
    );
    expect(screen.getByText('Overall Verdict:')).toBeInTheDocument();
  });

  it('does not display overall verdict for single claim', () => {
    render(
      <AtomicClaims
        atomicClaims={mockSingleAtomicClaim}
        verificationResult={mockVerificationResult}
      />
    );
    expect(screen.queryByText('Overall Verdict:')).not.toBeInTheDocument();
  });

  it('expands claim details when header is clicked', () => {
    render(<AtomicClaims atomicClaims={mockSingleAtomicClaim} />);
    
    const claimHeader = screen.getByRole('button', { expanded: false });
    expect(screen.queryByText('Claim Information')).not.toBeInTheDocument();
    
    fireEvent.click(claimHeader);
    
    expect(screen.getByText('Claim Information')).toBeInTheDocument();
  });

  it('collapses claim details when header is clicked again', () => {
    render(<AtomicClaims atomicClaims={mockSingleAtomicClaim} />);
    
    const claimHeader = screen.getByRole('button');
    
    // Expand
    fireEvent.click(claimHeader);
    expect(screen.getByText('Claim Information')).toBeInTheDocument();
    
    // Collapse
    fireEvent.click(claimHeader);
    expect(screen.queryByText('Claim Information')).not.toBeInTheDocument();
  });

  it('shows claim ID in expanded details', () => {
    render(<AtomicClaims atomicClaims={mockSingleAtomicClaim} />);
    
    const claimHeader = screen.getByRole('button');
    fireEvent.click(claimHeader);
    
    expect(screen.getByText('ID:')).toBeInTheDocument();
    expect(screen.getByText('claim-1')).toBeInTheDocument();
  });

  it('shows claim type in expanded details', () => {
    render(<AtomicClaims atomicClaims={mockSingleAtomicClaim} />);
    
    const claimHeader = screen.getByRole('button');
    fireEvent.click(claimHeader);
    
    expect(screen.getByText('Type:')).toBeInTheDocument();
    expect(screen.getByText('Atomic')).toBeInTheDocument();
  });

  it('shows parent claim when available', () => {
    render(<AtomicClaims atomicClaims={mockMultipleAtomicClaims} />);
    
    const claimHeaders = screen.getAllByRole('button');
    fireEvent.click(claimHeaders[0]);
    
    expect(screen.getByText('Parent Claim:')).toBeInTheDocument();
    expect(screen.getByText('compound-claim-1')).toBeInTheDocument();
  });

  it('shows verification results when expanded', () => {
    render(
      <AtomicClaims
        atomicClaims={mockSingleAtomicClaim}
        verificationResult={mockVerificationResult}
      />
    );
    
    const claimHeader = screen.getByRole('button');
    fireEvent.click(claimHeader);
    
    expect(screen.getByText('Verification Results')).toBeInTheDocument();
    expect(screen.getByText('Status:')).toBeInTheDocument();
  });

  it('shows confidence score in expanded details', () => {
    render(
      <AtomicClaims
        atomicClaims={mockSingleAtomicClaim}
        verificationResult={mockVerificationResult}
      />
    );
    
    const claimHeader = screen.getByRole('button');
    fireEvent.click(claimHeader);
    
    expect(screen.getByText('Confidence:')).toBeInTheDocument();
    expect(screen.getByText('85.0%')).toBeInTheDocument();
  });

  it('shows justification in expanded details', () => {
    render(
      <AtomicClaims
        atomicClaims={mockSingleAtomicClaim}
        verificationResult={mockVerificationResult}
      />
    );
    
    const claimHeader = screen.getByRole('button');
    fireEvent.click(claimHeader);
    
    expect(screen.getByText('Justification:')).toBeInTheDocument();
    expect(screen.getByText('Most claims are supported by evidence.')).toBeInTheDocument();
  });

  it('displays info message for compound claims', () => {
    render(<AtomicClaims atomicClaims={mockMultipleAtomicClaims} />);
    expect(
      screen.getByText(/This claim was broken down into 3 atomic claims/)
    ).toBeInTheDocument();
  });

  it('does not display info message for single claim', () => {
    render(<AtomicClaims atomicClaims={mockSingleAtomicClaim} />);
    expect(
      screen.queryByText(/This claim was broken down/)
    ).not.toBeInTheDocument();
  });

  it('applies correct status icon for supported claims', () => {
    const { container } = render(<AtomicClaims atomicClaims={mockSingleAtomicClaim} />);
    const statusIcons = container.querySelectorAll('.atomic-claim-status-icon');
    expect(statusIcons[0].textContent).toBe('✓');
  });

  it('applies correct status icon for refuted claims', () => {
    const refutedClaim: AtomicClaim[] = [
      {
        id: 'claim-1',
        text: 'Test claim',
        is_atomic: true,
        verification_status: 'Refuted',
      },
    ];
    const { container } = render(<AtomicClaims atomicClaims={refutedClaim} />);
    const statusIcons = container.querySelectorAll('.atomic-claim-status-icon');
    expect(statusIcons[0].textContent).toBe('✗');
  });

  it('applies correct status icon for NEI claims', () => {
    const neiClaim: AtomicClaim[] = [
      {
        id: 'claim-1',
        text: 'Test claim',
        is_atomic: true,
        verification_status: 'Not Enough Information',
      },
    ];
    const { container } = render(<AtomicClaims atomicClaims={neiClaim} />);
    const statusIcons = container.querySelectorAll('.atomic-claim-status-icon');
    expect(statusIcons[0].textContent).toBe('?');
  });

  it('applies correct status icon for pending claims', () => {
    const pendingClaim: AtomicClaim[] = [
      {
        id: 'claim-1',
        text: 'Test claim',
        is_atomic: true,
      },
    ];
    const { container } = render(<AtomicClaims atomicClaims={pendingClaim} />);
    const statusIcons = container.querySelectorAll('.atomic-claim-status-icon');
    expect(statusIcons[0].textContent).toBe('⏳');
  });

  it('renders with proper ARIA labels', () => {
    render(<AtomicClaims atomicClaims={mockSingleAtomicClaim} />);
    expect(screen.getByRole('region', { name: 'Atomic claims' })).toBeInTheDocument();
  });

  it('has proper aria-expanded attribute on claim headers', () => {
    render(<AtomicClaims atomicClaims={mockSingleAtomicClaim} />);
    const claimHeader = screen.getByRole('button');
    
    expect(claimHeader).toHaveAttribute('aria-expanded', 'false');
    
    fireEvent.click(claimHeader);
    
    expect(claimHeader).toHaveAttribute('aria-expanded', 'true');
  });

  it('has proper aria-controls attribute on claim headers', () => {
    render(<AtomicClaims atomicClaims={mockSingleAtomicClaim} />);
    const claimHeader = screen.getByRole('button');
    
    expect(claimHeader).toHaveAttribute('aria-controls', 'claim-details-claim-1');
  });
});
