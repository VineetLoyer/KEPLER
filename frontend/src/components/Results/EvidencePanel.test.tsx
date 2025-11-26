import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { EvidencePanel } from './EvidencePanel';
import type { EvidencePiece } from '../../types/verification';

/**
 * Unit Tests for EvidencePanel Component
 * 
 * These tests verify specific examples and edge cases for the EvidencePanel component.
 */

describe('EvidencePanel Unit Tests', () => {
  const mockEvidence: EvidencePiece[] = [
    {
      id: 'evidence-1',
      source: {
        url: 'https://example.com/article1',
        title: 'Test Article 1',
        domain: 'example.com',
        content_type: 'article',
        publish_date: '2024-01-15T10:00:00Z',
      },
      summary: 'This is a test summary for the first evidence piece.',
      raw_content: 'Full content here...',
      credibility_score: 0.85,
      relevance_score: 0.9,
    },
    {
      id: 'evidence-2',
      source: {
        url: 'https://test.org/research',
        title: 'Research Paper',
        domain: 'test.org',
        content_type: 'research',
      },
      summary: 'This is a test summary for the second evidence piece.',
      raw_content: 'Full research content...',
      credibility_score: 0.95,
    },
  ];

  it('should render evidence panel with title', () => {
    render(<EvidencePanel evidence={mockEvidence} />);
    
    const title = screen.getByText('Evidence Sources');
    expect(title).toBeInTheDocument();
  });

  it('should render all evidence items', () => {
    const { container } = render(<EvidencePanel evidence={mockEvidence} />);
    
    const items = container.querySelectorAll('.evidence-item');
    expect(items.length).toBe(2);
  });

  it('should display evidence titles', () => {
    render(<EvidencePanel evidence={mockEvidence} />);
    
    expect(screen.getByText('Test Article 1')).toBeInTheDocument();
    expect(screen.getByText('Research Paper')).toBeInTheDocument();
  });

  it('should display credibility scores as percentages', () => {
    render(<EvidencePanel evidence={mockEvidence} />);
    
    expect(screen.getByText('Credibility: 85%')).toBeInTheDocument();
    expect(screen.getByText('Credibility: 95%')).toBeInTheDocument();
  });

  it('should display evidence summaries', () => {
    render(<EvidencePanel evidence={mockEvidence} />);
    
    expect(screen.getByText('This is a test summary for the first evidence piece.')).toBeInTheDocument();
    expect(screen.getByText('This is a test summary for the second evidence piece.')).toBeInTheDocument();
  });

  it('should render clickable links with correct attributes', () => {
    render(<EvidencePanel evidence={mockEvidence} />);
    
    const links = screen.getAllByRole('link');
    expect(links.length).toBe(2);
    
    // First link
    expect(links[0]).toHaveAttribute('href', 'https://example.com/article1');
    expect(links[0]).toHaveAttribute('target', '_blank');
    expect(links[0]).toHaveAttribute('rel', 'noopener noreferrer');
    
    // Second link
    expect(links[1]).toHaveAttribute('href', 'https://test.org/research');
    expect(links[1]).toHaveAttribute('target', '_blank');
    expect(links[1]).toHaveAttribute('rel', 'noopener noreferrer');
  });

  it('should display empty message when no evidence provided', () => {
    render(<EvidencePanel evidence={[]} />);
    
    expect(screen.getByText('No evidence sources available.')).toBeInTheDocument();
  });

  it('should handle undefined credibility score', () => {
    const evidenceWithoutScore: EvidencePiece[] = [
      {
        id: 'evidence-3',
        source: {
          url: 'https://example.com/article',
          title: 'Article Without Score',
          domain: 'example.com',
          content_type: 'article',
        },
        summary: 'Summary text',
        raw_content: 'Content',
      },
    ];
    
    render(<EvidencePanel evidence={evidenceWithoutScore} />);
    
    // Should default to 0%
    expect(screen.getByText('Credibility: 0%')).toBeInTheDocument();
  });

  it('should display domain metadata when available', () => {
    render(<EvidencePanel evidence={mockEvidence} />);
    
    expect(screen.getByText('example.com')).toBeInTheDocument();
    expect(screen.getByText('test.org')).toBeInTheDocument();
  });

  it('should display publish date when available', () => {
    render(<EvidencePanel evidence={mockEvidence} />);
    
    // Date should be formatted (locale-independent check)
    const dateElements = screen.getAllByText(/\d+\/\d+\/\d+/);
    expect(dateElements.length).toBeGreaterThan(0);
    
    // Check that the date contains the year 2024
    const dateElement = screen.getByText(/2024/);
    expect(dateElement).toBeInTheDocument();
  });

  it('should have proper accessibility attributes', () => {
    render(<EvidencePanel evidence={mockEvidence} />);
    
    // Should have region role
    const panel = screen.getByRole('region', { name: /evidence sources/i });
    expect(panel).toBeInTheDocument();
    
    // Links should have aria-labels
    const links = screen.getAllByRole('link');
    links.forEach((link) => {
      expect(link).toHaveAttribute('aria-label');
    });
  });

  it('should render with proper CSS classes', () => {
    const { container } = render(<EvidencePanel evidence={mockEvidence} />);
    
    expect(container.querySelector('.evidence-panel')).toBeInTheDocument();
    expect(container.querySelector('.evidence-list')).toBeInTheDocument();
    expect(container.querySelectorAll('.evidence-item').length).toBe(2);
  });

  it('should handle single evidence item', () => {
    const singleEvidence = [mockEvidence[0]];
    const { container } = render(<EvidencePanel evidence={singleEvidence} />);
    
    const items = container.querySelectorAll('.evidence-item');
    expect(items.length).toBe(1);
  });

  it('should display link text correctly', () => {
    render(<EvidencePanel evidence={mockEvidence} />);
    
    const links = screen.getAllByText(/View Source/);
    expect(links.length).toBe(2);
    
    links.forEach((link) => {
      expect(link.textContent).toContain('→');
    });
  });
});
